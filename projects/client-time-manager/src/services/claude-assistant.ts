import Anthropic from '@anthropic-ai/sdk';
import { DashboardData, MeetingActionItems } from '../types';
import { clients } from '../config/clients';

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface AssistantContext {
  dashboardData: DashboardData | null;
  selectedClient?: string;
}

export class ClaudeAssistant {
  private client: Anthropic;
  private conversationHistory: ChatMessage[] = [];

  constructor() {
    this.client = new Anthropic({
      apiKey: process.env.ANTHROPIC_API_KEY
    });
  }

  /**
   * Build system prompt with current dashboard context
   */
  private buildSystemPrompt(context: AssistantContext): string {
    const today = new Date().toLocaleDateString('en-GB', {
      weekday: 'long',
      day: 'numeric',
      month: 'long',
      year: 'numeric'
    });

    let systemPrompt = `You are an intelligent assistant for a client management dashboard. Today is ${today}.

Your role is to help the user:
- Understand their weekly workload across all clients
- Summarise meetings, tasks, and action items
- Provide insights on priorities and potential issues
- Answer questions about specific clients, tasks, or meetings
- Suggest what to focus on based on due dates and urgency
- Extract action items from meeting transcripts
- Help create tasks from meeting notes

Be concise but thorough. Use bullet points for lists. Highlight urgent items.
When discussing dates, use relative terms like "tomorrow", "next Monday", etc.
If asked about something not in the data, say so clearly.

`;

    if (!context.dashboardData) {
      systemPrompt += `\nNOTE: No dashboard data is currently loaded. Ask the user to refresh the data first.`;
      return systemPrompt;
    }

    const data = context.dashboardData;

    systemPrompt += `\n## CURRENT DATA (Last updated: ${new Date(data.lastUpdated).toLocaleString('en-GB')})

### Clients Being Managed
${clients.map(c => `- ${c.name} (aliases: ${c.aliases.join(', ')})`).join('\n')}

### Weekly Overview (${this.formatDateRange(data.weeklyOverview.weekStart, data.weeklyOverview.weekEnd)})

`;

    // Add per-client summaries
    for (const clientData of data.weeklyOverview.clients) {
      systemPrompt += this.buildClientContext(clientData);
    }

    // Add all tasks
    systemPrompt += `\n### All Active Tasks\n`;
    for (const task of data.allTasks) {
      const dueStr = task.dueDate ? ` (Due: ${this.formatDate(task.dueDate)})` : '';
      const priorityStr = task.priority ? ` [${task.priority}]` : '';
      systemPrompt += `- [${task.client || 'Unassigned'}] ${task.title}${priorityStr}${dueStr} - Status: ${task.status}\n`;
    }

    // Add upcoming calendar
    systemPrompt += `\n### Upcoming Calendar Events\n`;
    for (const event of data.allMeetings.slice(0, 20)) {
      systemPrompt += `- ${this.formatDateTime(event.start)}: ${event.title}${event.client ? ` (${event.client})` : ''}\n`;
    }

    // Add Fathom meetings
    if (data.allFathomSummaries.length > 0) {
      systemPrompt += `\n### Recent Meeting Summaries (from Fathom)\n`;
      for (const meeting of data.allFathomSummaries.slice(0, 10)) {
        systemPrompt += `\n**${meeting.title}** (${this.formatDate(meeting.date)})${meeting.client ? ` - ${meeting.client}` : ''}
Summary: ${meeting.summary.substring(0, 300)}${meeting.summary.length > 300 ? '...' : ''}
${meeting.actionItems.length > 0 ? `Action Items:\n${meeting.actionItems.map(a => `  - ${a}`).join('\n')}` : ''}
`;
      }
    }

    // Add ranking summaries
    if (data.allRankings.length > 0) {
      systemPrompt += `\n### SEO Ranking Summaries\n`;
      for (const ranking of data.allRankings) {
        const { improved, declined, unchanged } = ranking.positionChanges;
        systemPrompt += `- ${ranking.client}: Avg position ${ranking.averagePosition.toFixed(1)} | ↑${improved} improved, ↓${declined} declined, ${unchanged} unchanged\n`;

        const topKeywords = ranking.keywords.filter(k => k.position <= 10).slice(0, 5);
        if (topKeywords.length > 0) {
          systemPrompt += `  Top 10 keywords: ${topKeywords.map(k => `"${k.keyword}" (#${k.position})`).join(', ')}\n`;
        }
      }
    }

    return systemPrompt;
  }

  /**
   * Build context for a single client
   */
  private buildClientContext(clientData: any): string {
    const { client, upcomingMeetings, tasksDue, tasksOverdue, recentMeetings, rankingSnapshot } = clientData;

    let context = `\n#### ${client.name}\n`;

    if (tasksOverdue.length > 0) {
      context += `⚠️ OVERDUE TASKS (${tasksOverdue.length}):\n`;
      for (const task of tasksOverdue) {
        context += `  - ${task.title} (was due ${this.formatDate(task.dueDate)})\n`;
      }
    }

    if (tasksDue.length > 0) {
      context += `📋 Tasks due this week (${tasksDue.length}):\n`;
      for (const task of tasksDue) {
        context += `  - ${task.title} (due ${this.formatDate(task.dueDate)})\n`;
      }
    }

    if (upcomingMeetings.length > 0) {
      context += `📅 Upcoming meetings (${upcomingMeetings.length}):\n`;
      for (const meeting of upcomingMeetings) {
        context += `  - ${this.formatDateTime(meeting.start)}: ${meeting.title}\n`;
      }
    }

    if (recentMeetings.length > 0) {
      context += `🎥 Recent meeting notes available: ${recentMeetings.map(m => m.title).join(', ')}\n`;
    }

    if (rankingSnapshot) {
      const { improved, declined } = rankingSnapshot.positionChanges;
      context += `📈 SEO: ${improved} keywords improved, ${declined} declined (avg pos: ${rankingSnapshot.averagePosition.toFixed(1)})\n`;
    }

    if (tasksOverdue.length === 0 && tasksDue.length === 0 && upcomingMeetings.length === 0) {
      context += `  No urgent items this week.\n`;
    }

    return context;
  }

  /**
   * Chat with the assistant
   */
  async chat(userMessage: string, context: AssistantContext): Promise<string> {
    const systemPrompt = this.buildSystemPrompt(context);

    this.conversationHistory.push({
      role: 'user',
      content: userMessage
    });

    if (this.conversationHistory.length > 20) {
      this.conversationHistory = this.conversationHistory.slice(-20);
    }

    try {
      const response = await this.client.messages.create({
        model: 'claude-sonnet-4-20250514',
        max_tokens: 2048,
        system: systemPrompt,
        messages: this.conversationHistory.map(msg => ({
          role: msg.role,
          content: msg.content
        }))
      });

      const assistantMessage = response.content[0].type === 'text'
        ? response.content[0].text
        : '';

      this.conversationHistory.push({
        role: 'assistant',
        content: assistantMessage
      });

      return assistantMessage;
    } catch (error) {
      console.error('Claude API error:', error);
      throw new Error('Failed to get response from Claude');
    }
  }

  /**
   * Quick insights - predefined analysis queries
   */
  async getQuickInsight(type: 'weekly-summary' | 'priorities' | 'overdue' | 'client-health', context: AssistantContext): Promise<string> {
    const prompts: Record<string, string> = {
      'weekly-summary': `Give me a concise summary of my week ahead. What meetings do I have? What tasks are due? Any urgent items I should know about? Format as a brief executive summary.`,

      'priorities': `Based on due dates, priorities, and overdue items, what should I focus on today and this week? List the top 5 priorities across all clients with brief reasoning.`,

      'overdue': `List all overdue tasks and items that need immediate attention. For each one, suggest what action I should take. Be direct and actionable.`,

      'client-health': `Give me a health check across all my clients. Which clients need more attention? Which are in good shape? Any red flags I should be aware of? Consider tasks, meetings, and SEO performance.`
    };

    return this.chat(prompts[type], context);
  }

  /**
   * Analyse a specific client
   */
  async analyseClient(clientName: string, context: AssistantContext): Promise<string> {
    return this.chat(
      `Give me a detailed analysis of ${clientName}:
1. Current status - what's happening with them?
2. Outstanding tasks and their priorities
3. Recent meetings and key action items from those meetings
4. SEO performance if available
5. What should I focus on for this client this week?`,
      context
    );
  }

  /**
   * Summarise a meeting
   */
  async summariseMeeting(meetingTitle: string, context: AssistantContext): Promise<string> {
    return this.chat(
      `Find the meeting "${meetingTitle}" in the Fathom summaries and give me:
1. A brief summary of what was discussed
2. All action items, clearly listed
3. Any deadlines or commitments mentioned
4. Suggested follow-up tasks I should create`,
      context
    );
  }

  /**
   * QSP Analysis
   */
  async analyseQSP(clientName: string, context: AssistantContext): Promise<string> {
    return this.chat(
      `Analyse the QSP (Quarterly Success Plan) tasks for ${clientName}:
1. What QSP tasks are in progress or pending?
2. Are we on track for the quarter?
3. What's at risk of not being completed?
4. Recommendations for getting back on track if needed`,
      context
    );
  }

  /**
   * Extract action items from a meeting and format as potential tasks
   */
  async extractActionItems(meetingTitle: string, context: AssistantContext): Promise<MeetingActionItems> {
    const prompt = `Analyse the meeting "${meetingTitle}" from the Fathom summaries and extract ALL action items.

For each action item, determine:
1. A clear, actionable task title (start with a verb)
2. Who owns this action (me/us, the client, or unclear)
3. Priority level based on urgency mentioned
4. Suggested due date if mentioned or implied
5. Any relevant context/notes

Return your response in this EXACT JSON format (no markdown, just JSON):
{
  "meetingTitle": "the meeting title",
  "meetingDate": "the meeting date",
  "client": "client name or null",
  "actionItems": [
    {
      "title": "Send proposal document",
      "owner": "me",
      "priority": "High",
      "suggestedDueDate": "2024-01-20",
      "notes": "Client wants to review before next meeting"
    }
  ]
}

Only include action items where owner is "me" or "unknown" - skip items that are purely the client's responsibility.
If no action items found, return an empty actionItems array.`;

    const response = await this.chat(prompt, context);

    try {
      const jsonMatch = response.match(/\{[\s\S]*\}/);
      if (jsonMatch) {
        return JSON.parse(jsonMatch[0]);
      }
    } catch (e) {
      console.error('Failed to parse action items JSON:', e);
    }

    return {
      meetingTitle,
      meetingDate: '',
      client: null,
      actionItems: []
    };
  }

  /**
   * Extract action items from ALL recent meetings
   */
  async extractAllPendingActions(context: AssistantContext): Promise<{
    meetings: Array<{
      title: string;
      date: string;
      client: string | null;
      actionItems: Array<{
        title: string;
        priority: 'High' | 'Medium' | 'Low';
        suggestedDueDate?: string;
        notes?: string;
      }>;
    }>;
    summary: string;
  }> {
    const prompt = `Review ALL the Fathom meeting summaries and identify action items that may not have been converted to tasks yet.

For each meeting with pending action items, list:
1. The meeting details
2. Action items that appear to be MY responsibility (not the client's)
3. Whether these might already exist as tasks in Notion

Return as JSON:
{
  "meetings": [
    {
      "title": "Meeting title",
      "date": "Meeting date",
      "client": "Client name",
      "actionItems": [
        {
          "title": "Clear task title",
          "priority": "High",
          "suggestedDueDate": "YYYY-MM-DD",
          "notes": "Context"
        }
      ]
    }
  ],
  "summary": "Brief summary of total pending actions across all meetings"
}

Cross-reference with existing Notion tasks - if an action item seems to already exist as a task, don't include it.`;

    const response = await this.chat(prompt, context);

    try {
      const jsonMatch = response.match(/\{[\s\S]*\}/);
      if (jsonMatch) {
        return JSON.parse(jsonMatch[0]);
      }
    } catch (e) {
      console.error('Failed to parse pending actions JSON:', e);
    }

    return {
      meetings: [],
      summary: 'Unable to extract action items'
    };
  }

  /**
   * Clear conversation history
   */
  clearHistory(): void {
    this.conversationHistory = [];
  }

  /**
   * Get conversation history
   */
  getHistory(): ChatMessage[] {
    return [...this.conversationHistory];
  }

  // Helper formatters
  private formatDate(date: Date | string): string {
    const d = new Date(date);
    const today = new Date();
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);

    if (d.toDateString() === today.toDateString()) return 'today';
    if (d.toDateString() === tomorrow.toDateString()) return 'tomorrow';

    return d.toLocaleDateString('en-GB', { weekday: 'short', day: 'numeric', month: 'short' });
  }

  private formatDateTime(date: Date | string): string {
    const d = new Date(date);
    return `${this.formatDate(d)} at ${d.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })}`;
  }

  private formatDateRange(start: Date | string, end: Date | string): string {
    const s = new Date(start);
    const e = new Date(end);
    return `${s.toLocaleDateString('en-GB', { day: 'numeric', month: 'short' })} - ${e.toLocaleDateString('en-GB', { day: 'numeric', month: 'short' })}`;
  }
}
