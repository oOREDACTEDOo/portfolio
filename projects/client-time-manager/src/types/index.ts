// Core types for the client time manager

export interface Client {
  id: string;
  name: string;
  aliases: string[]; // Alternative names used in different systems
  notionDatabaseId?: string;
  sitecheckerProjectId?: string;
}

export interface CalendarEvent {
  id: string;
  title: string;
  description?: string;
  start: Date;
  end: Date;
  client?: string;
  attendees: string[];
  meetingLink?: string;
}

export interface NotionTask {
  id: string;
  title: string;
  status: 'Not Started' | 'In Progress' | 'Completed' | 'Blocked';
  dueDate?: Date;
  priority?: 'High' | 'Medium' | 'Low';
  client: string;
  qspQuarter?: string;
  notes?: string;
  url: string;
}

export interface FathomMeeting {
  id: string;
  title: string;
  date: Date;
  client?: string;
  summary: string;
  actionItems: string[];
  transcriptLink: string;
  videoLink?: string;
  attendees: string[];
}

export interface RankingData {
  client: string;
  projectId: string;
  keywords: KeywordRanking[];
  lastUpdated: Date;
  averagePosition: number;
  positionChanges: {
    improved: number;
    declined: number;
    unchanged: number;
  };
}

export interface KeywordRanking {
  keyword: string;
  position: number;
  previousPosition?: number;
  change: number;
  url: string;
  searchVolume?: number;
}

export interface WeeklyOverview {
  weekStart: Date;
  weekEnd: Date;
  clients: ClientWeeklyData[];
  generatedAt: Date;
}

export interface ClientWeeklyData {
  client: Client;
  upcomingMeetings: CalendarEvent[];
  tasksDue: NotionTask[];
  tasksOverdue: NotionTask[];
  recentMeetings: FathomMeeting[];
  rankingSnapshot: RankingData | null;
  keyDates: KeyDate[];
}

export interface KeyDate {
  date: Date;
  type: 'meeting' | 'task_due' | 'qsp_review' | 'report_due' | 'custom';
  title: string;
  client: string;
  source: 'calendar' | 'notion' | 'fathom';
}

export interface DashboardData {
  lastUpdated: Date;
  weeklyOverview: WeeklyOverview;
  allTasks: NotionTask[];
  allMeetings: CalendarEvent[];
  allFathomSummaries: FathomMeeting[];
  allRankings: RankingData[];
}

// Task creation types
export interface TaskToCreate {
  title: string;
  client?: string;
  dueDate?: Date;
  priority?: 'High' | 'Medium' | 'Low';
  notes?: string;
  source?: string;
}

export interface ExtractedActionItem {
  title: string;
  suggestedDueDate?: string;
  priority: 'High' | 'Medium' | 'Low';
  owner: 'me' | 'client' | 'unknown';
  notes?: string;
}

export interface MeetingActionItems {
  meetingTitle: string;
  meetingDate: string;
  client: string | null;
  actionItems: ExtractedActionItem[];
}
