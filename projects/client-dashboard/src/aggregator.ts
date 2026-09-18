import {
  DashboardData,
  WeeklyOverview,
  ClientWeeklyData,
  KeyDate,
  CalendarEvent,
  NotionTask,
  FathomMeeting,
  RankingData
} from './types';
import { clients, matchClient } from './config/clients';
import { GoogleIntegration } from './integrations/google';
import { NotionIntegration } from './integrations/notion';
import { SiteCheckerIntegration } from './integrations/sitechecker';

export class DataAggregator {
  private google: GoogleIntegration;
  private notion: NotionIntegration;
  private sitechecker: SiteCheckerIntegration;

  constructor() {
    this.google = new GoogleIntegration();
    this.notion = new NotionIntegration();
    this.sitechecker = new SiteCheckerIntegration();
  }

  /**
   * Initialize Google auth (must be called before fetching data)
   */
  async initGoogleAuth(): Promise<boolean> {
    return this.google.loadSavedTokens();
  }

  /**
   * Get Google auth URL for initial setup
   */
  getGoogleAuthUrl(): string {
    return this.google.getAuthUrl();
  }

  /**
   * Complete Google OAuth flow
   */
  async completeGoogleAuth(code: string): Promise<void> {
    await this.google.authenticate(code);
  }

  /**
   * Fetch all data from all sources
   */
  async fetchAllData(): Promise<DashboardData> {
    console.log('Fetching data from all sources...');

    // Fetch in parallel where possible
    const [calendarEvents, fathomMeetings, tasks, rankings] = await Promise.all([
      this.google.getCalendarEvents(14).catch(err => {
        console.error('Error fetching calendar:', err);
        return [] as CalendarEvent[];
      }),
      this.google.getFathomEmails(30).catch(err => {
        console.error('Error fetching Fathom emails:', err);
        return [] as FathomMeeting[];
      }),
      this.notion.getAllClientTasks().catch(err => {
        console.error('Error fetching Notion tasks:', err);
        return [] as NotionTask[];
      }),
      this.sitechecker.getAllClientRankings().catch(err => {
        console.error('Error fetching rankings:', err);
        return [] as RankingData[];
      })
    ]);

    console.log(`Fetched: ${calendarEvents.length} events, ${fathomMeetings.length} meetings, ${tasks.length} tasks, ${rankings.length} ranking reports`);

    // Generate weekly overview
    const weeklyOverview = this.generateWeeklyOverview(
      calendarEvents,
      tasks,
      fathomMeetings,
      rankings
    );

    return {
      lastUpdated: new Date(),
      weeklyOverview,
      allTasks: tasks,
      allMeetings: calendarEvents,
      allFathomSummaries: fathomMeetings,
      allRankings: rankings
    };
  }

  /**
   * Generate a weekly overview grouped by client
   */
  private generateWeeklyOverview(
    events: CalendarEvent[],
    tasks: NotionTask[],
    fathomMeetings: FathomMeeting[],
    rankings: RankingData[]
  ): WeeklyOverview {
    const now = new Date();
    const weekStart = this.getStartOfWeek(now);
    const weekEnd = new Date(weekStart);
    weekEnd.setDate(weekEnd.getDate() + 7);

    const clientData: ClientWeeklyData[] = [];

    for (const client of clients) {
      // Filter data for this client
      const clientEvents = events.filter(e =>
        e.client === client.name ||
        this.matchesClient(e.title, client.name, client.aliases)
      );

      const clientTasks = tasks.filter(t =>
        t.client === client.name ||
        this.matchesClient(t.title, client.name, client.aliases)
      );

      const clientFathom = fathomMeetings.filter(m =>
        m.client === client.name ||
        this.matchesClient(m.title, client.name, client.aliases)
      );

      const clientRanking = rankings.find(r => r.client === client.name);

      // Calculate due dates
      const tasksDue = clientTasks.filter(t =>
        t.dueDate &&
        t.dueDate >= weekStart &&
        t.dueDate <= weekEnd &&
        t.status !== 'Completed'
      );

      const tasksOverdue = clientTasks.filter(t =>
        t.dueDate &&
        t.dueDate < now &&
        t.status !== 'Completed'
      );

      // Upcoming meetings this week
      const upcomingMeetings = clientEvents.filter(e =>
        e.start >= now && e.start <= weekEnd
      );

      // Recent Fathom summaries (last 7 days)
      const sevenDaysAgo = new Date();
      sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);
      const recentMeetings = clientFathom.filter(m =>
        m.date >= sevenDaysAgo
      );

      // Key dates
      const keyDates = this.extractKeyDates(
        client.name,
        upcomingMeetings,
        tasksDue,
        tasksOverdue
      );

      clientData.push({
        client,
        upcomingMeetings,
        tasksDue,
        tasksOverdue,
        recentMeetings,
        rankingSnapshot: clientRanking || null,
        keyDates
      });
    }

    // Also include unmatched items (no client assigned)
    const unmatchedEvents = events.filter(e => !e.client);
    const unmatchedTasks = tasks.filter(t => !t.client);

    if (unmatchedEvents.length > 0 || unmatchedTasks.length > 0) {
      clientData.push({
        client: {
          id: 'unassigned',
          name: 'Unassigned',
          aliases: []
        },
        upcomingMeetings: unmatchedEvents.filter(e => e.start >= now && e.start <= weekEnd),
        tasksDue: unmatchedTasks.filter(t => t.dueDate && t.dueDate >= weekStart && t.dueDate <= weekEnd),
        tasksOverdue: unmatchedTasks.filter(t => t.dueDate && t.dueDate < now),
        recentMeetings: [],
        rankingSnapshot: null,
        keyDates: []
      });
    }

    return {
      weekStart,
      weekEnd,
      clients: clientData,
      generatedAt: new Date()
    };
  }

  /**
   * Check if text matches a client
   */
  private matchesClient(text: string, clientName: string, aliases: string[]): boolean {
    const lowerText = text.toLowerCase();
    if (lowerText.includes(clientName.toLowerCase())) return true;
    return aliases.some(alias => lowerText.includes(alias.toLowerCase()));
  }

  /**
   * Extract key dates from various sources
   */
  private extractKeyDates(
    clientName: string,
    meetings: CalendarEvent[],
    tasksDue: NotionTask[],
    tasksOverdue: NotionTask[]
  ): KeyDate[] {
    const keyDates: KeyDate[] = [];

    // Add meetings
    for (const meeting of meetings) {
      keyDates.push({
        date: meeting.start,
        type: 'meeting',
        title: meeting.title,
        client: clientName,
        source: 'calendar'
      });
    }

    // Add due tasks
    for (const task of tasksDue) {
      if (task.dueDate) {
        const type = task.qspQuarter ? 'qsp_review' : 'task_due';
        keyDates.push({
          date: task.dueDate,
          type,
          title: task.title,
          client: clientName,
          source: 'notion'
        });
      }
    }

    // Add overdue tasks (marked as urgent)
    for (const task of tasksOverdue) {
      if (task.dueDate) {
        keyDates.push({
          date: task.dueDate,
          type: 'task_due',
          title: `⚠️ OVERDUE: ${task.title}`,
          client: clientName,
          source: 'notion'
        });
      }
    }

    // Sort by date
    keyDates.sort((a, b) => a.date.getTime() - b.date.getTime());

    return keyDates;
  }

  /**
   * Get start of current week (Monday)
   */
  private getStartOfWeek(date: Date): Date {
    const d = new Date(date);
    const day = d.getDay();
    const diff = d.getDate() - day + (day === 0 ? -6 : 1);
    d.setDate(diff);
    d.setHours(0, 0, 0, 0);
    return d;
  }
}
