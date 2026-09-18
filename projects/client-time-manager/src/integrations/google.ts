import { google } from 'googleapis';
import { OAuth2Client } from 'google-auth-library';
import * as fs from 'fs';
import * as path from 'path';
import { CalendarEvent, FathomMeeting } from '../types';
import { matchClient } from '../config/clients';

const SCOPES = [
  'https://www.googleapis.com/auth/calendar.readonly',
  'https://www.googleapis.com/auth/gmail.readonly'
];

const TOKEN_PATH = path.join(__dirname, '../../data/google-token.json');

export class GoogleIntegration {
  private oauth2Client: OAuth2Client;

  constructor() {
    this.oauth2Client = new google.auth.OAuth2(
      process.env.GOOGLE_CLIENT_ID,
      process.env.GOOGLE_CLIENT_SECRET,
      process.env.GOOGLE_REDIRECT_URI
    );
  }

  /**
   * Get the authorization URL for initial OAuth setup
   */
  getAuthUrl(): string {
    return this.oauth2Client.generateAuthUrl({
      access_type: 'offline',
      scope: SCOPES
    });
  }

  /**
   * Exchange authorization code for tokens
   */
  async authenticate(code: string): Promise<void> {
    const { tokens } = await this.oauth2Client.getToken(code);
    this.oauth2Client.setCredentials(tokens);

    // Save tokens for future use
    const dataDir = path.dirname(TOKEN_PATH);
    if (!fs.existsSync(dataDir)) {
      fs.mkdirSync(dataDir, { recursive: true });
    }
    fs.writeFileSync(TOKEN_PATH, JSON.stringify(tokens));
  }

  /**
   * Load saved tokens
   */
  loadSavedTokens(): boolean {
    if (fs.existsSync(TOKEN_PATH)) {
      const tokens = JSON.parse(fs.readFileSync(TOKEN_PATH, 'utf-8'));
      this.oauth2Client.setCredentials(tokens);
      return true;
    }
    return false;
  }

  /**
   * Fetch calendar events for the specified period
   */
  async getCalendarEvents(daysAhead: number = 14): Promise<CalendarEvent[]> {
    const calendar = google.calendar({ version: 'v3', auth: this.oauth2Client });

    const now = new Date();
    const future = new Date();
    future.setDate(future.getDate() + daysAhead);

    const response = await calendar.events.list({
      calendarId: 'primary',
      timeMin: now.toISOString(),
      timeMax: future.toISOString(),
      singleEvents: true,
      orderBy: 'startTime'
    });

    const events: CalendarEvent[] = [];

    for (const event of response.data.items || []) {
      const title = event.summary || 'Untitled';
      const matchedClient = matchClient(title);

      events.push({
        id: event.id || '',
        title,
        description: event.description || undefined,
        start: new Date(event.start?.dateTime || event.start?.date || ''),
        end: new Date(event.end?.dateTime || event.end?.date || ''),
        client: matchedClient?.name,
        attendees: (event.attendees || []).map(a => a.email || ''),
        meetingLink: event.hangoutLink || undefined
      });
    }

    return events;
  }

  /**
   * Fetch and parse Fathom meeting emails
   * Fathom sends emails with subject like "Meeting summary: [Meeting Title]"
   */
  async getFathomEmails(daysBack: number = 30): Promise<FathomMeeting[]> {
    const gmail = google.gmail({ version: 'v1', auth: this.oauth2Client });

    const afterDate = new Date();
    afterDate.setDate(afterDate.getDate() - daysBack);
    const afterTimestamp = Math.floor(afterDate.getTime() / 1000);

    // Search for Fathom emails
    const response = await gmail.users.messages.list({
      userId: 'me',
      q: `from:fathom.video after:${afterTimestamp}`,
      maxResults: 100
    });

    const meetings: FathomMeeting[] = [];

    for (const message of response.data.messages || []) {
      try {
        const fullMessage = await gmail.users.messages.get({
          userId: 'me',
          id: message.id || '',
          format: 'full'
        });

        const fathomMeeting = this.parseFathomEmail(fullMessage.data);
        if (fathomMeeting) {
          meetings.push(fathomMeeting);
        }
      } catch (error) {
        console.error(`Error fetching email ${message.id}:`, error);
      }
    }

    return meetings;
  }

  /**
   * Parse a Fathom email into structured data
   */
  private parseFathomEmail(message: any): FathomMeeting | null {
    const headers = message.payload?.headers || [];
    const subject = headers.find((h: any) => h.name === 'Subject')?.value || '';
    const date = headers.find((h: any) => h.name === 'Date')?.value || '';

    // Extract meeting title from subject
    const titleMatch = subject.match(/Meeting summary: (.+)/i);
    const title = titleMatch ? titleMatch[1] : subject;

    // Get email body
    let body = '';
    if (message.payload?.body?.data) {
      body = Buffer.from(message.payload.body.data, 'base64').toString('utf-8');
    } else if (message.payload?.parts) {
      for (const part of message.payload.parts) {
        if (part.mimeType === 'text/plain' && part.body?.data) {
          body = Buffer.from(part.body.data, 'base64').toString('utf-8');
          break;
        }
      }
    }

    // Parse the body for summary and action items
    const summary = this.extractSection(body, 'Summary', 'Action Items') ||
      this.extractSection(body, 'Key Points', 'Action Items') ||
      body.substring(0, 500);

    const actionItemsSection = this.extractSection(body, 'Action Items', 'Transcript') || '';
    const actionItems = actionItemsSection
      .split('\n')
      .filter(line => line.trim().startsWith('-') || line.trim().startsWith('•'))
      .map(line => line.replace(/^[-•]\s*/, '').trim())
      .filter(Boolean);

    // Extract links
    const transcriptLinkMatch = body.match(/https:\/\/[^\s]*fathom[^\s]*transcript[^\s]*/i) ||
      body.match(/https:\/\/[^\s]*fathom\.video[^\s]*/i);
    const videoLinkMatch = body.match(/https:\/\/[^\s]*fathom[^\s]*video[^\s]*/i);

    const matchedClient = matchClient(title);

    return {
      id: message.id || '',
      title,
      date: new Date(date),
      client: matchedClient?.name,
      summary: summary.trim(),
      actionItems,
      transcriptLink: transcriptLinkMatch ? transcriptLinkMatch[0] : '',
      videoLink: videoLinkMatch ? videoLinkMatch[0] : undefined,
      attendees: []
    };
  }

  /**
   * Extract a section from text between two headers
   */
  private extractSection(text: string, startHeader: string, endHeader: string): string | null {
    const startRegex = new RegExp(`${startHeader}[:\\s]*`, 'i');
    const endRegex = new RegExp(`${endHeader}[:\\s]*`, 'i');

    const startMatch = text.match(startRegex);
    if (!startMatch) return null;

    const startIndex = startMatch.index! + startMatch[0].length;
    const endMatch = text.substring(startIndex).match(endRegex);

    if (endMatch) {
      return text.substring(startIndex, startIndex + endMatch.index!);
    }

    return text.substring(startIndex);
  }
}
