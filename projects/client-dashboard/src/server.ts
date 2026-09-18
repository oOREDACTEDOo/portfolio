import express from 'express';
import cors from 'cors';
import * as fs from 'fs';
import * as path from 'path';
import { DataAggregator } from './aggregator';
import { DashboardData } from './types';
import { ClaudeAssistant } from './services/claude-assistant';
import { NotionIntegration } from './integrations/notion';
import dotenv from 'dotenv';

dotenv.config();

const app = express();
const PORT = process.env.DASHBOARD_PORT || 3000;
const DATA_FILE = path.join(__dirname, '../data/dashboard-data.json');

app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, '../public')));

const aggregator = new DataAggregator();
const assistant = new ClaudeAssistant();
const notion = new NotionIntegration();

// Load cached data
function loadCachedData(): DashboardData | null {
  if (fs.existsSync(DATA_FILE)) {
    const data = JSON.parse(fs.readFileSync(DATA_FILE, 'utf-8'));
    // Convert date strings back to Date objects
    return {
      ...data,
      lastUpdated: new Date(data.lastUpdated),
      weeklyOverview: {
        ...data.weeklyOverview,
        weekStart: new Date(data.weeklyOverview.weekStart),
        weekEnd: new Date(data.weeklyOverview.weekEnd),
        generatedAt: new Date(data.weeklyOverview.generatedAt)
      }
    };
  }
  return null;
}

// Save data to cache
function saveData(data: DashboardData): void {
  const dataDir = path.dirname(DATA_FILE);
  if (!fs.existsSync(dataDir)) {
    fs.mkdirSync(dataDir, { recursive: true });
  }
  fs.writeFileSync(DATA_FILE, JSON.stringify(data, null, 2));
}

// API Routes

// Get dashboard data
app.get('/api/data', (req, res) => {
  const data = loadCachedData();
  if (data) {
    res.json(data);
  } else {
    res.status(404).json({ error: 'No data available. Run fetch first.' });
  }
});

// Refresh data from all sources
app.post('/api/refresh', async (req, res) => {
  try {
    const hasAuth = await aggregator.initGoogleAuth();
    if (!hasAuth) {
      return res.status(401).json({
        error: 'Google auth required',
        authUrl: aggregator.getGoogleAuthUrl()
      });
    }

    const data = await aggregator.fetchAllData();
    saveData(data);
    res.json(data);
  } catch (error) {
    console.error('Error refreshing data:', error);
    res.status(500).json({ error: 'Failed to refresh data' });
  }
});

// Google OAuth callback
app.get('/auth/google/callback', async (req, res) => {
  const code = req.query.code as string;
  if (!code) {
    return res.status(400).send('Missing authorization code');
  }

  try {
    await aggregator.completeGoogleAuth(code);
    res.redirect('/?auth=success');
  } catch (error) {
    console.error('Auth error:', error);
    res.status(500).send('Authentication failed');
  }
});

// Get auth status
app.get('/api/auth/status', async (req, res) => {
  const hasAuth = await aggregator.initGoogleAuth();
  res.json({
    googleAuth: hasAuth,
    authUrl: hasAuth ? null : aggregator.getGoogleAuthUrl()
  });
});

// ============ CLAUDE AI CHAT ENDPOINTS ============

// Chat with Claude
app.post('/api/chat', async (req, res) => {
  const { message } = req.body;

  if (!message) {
    return res.status(400).json({ error: 'Message is required' });
  }

  if (!process.env.ANTHROPIC_API_KEY) {
    return res.status(500).json({ error: 'Claude API key not configured. Add ANTHROPIC_API_KEY to .env' });
  }

  try {
    const dashboardData = loadCachedData();
    const response = await assistant.chat(message, { dashboardData });
    res.json({ response, history: assistant.getHistory() });
  } catch (error) {
    console.error('Chat error:', error);
    res.status(500).json({ error: 'Failed to get response from Claude' });
  }
});

// Quick insights
app.get('/api/insights/:type', async (req, res) => {
  const { type } = req.params;
  const validTypes = ['weekly-summary', 'priorities', 'overdue', 'client-health'];

  if (!validTypes.includes(type)) {
    return res.status(400).json({ error: `Invalid type. Must be one of: ${validTypes.join(', ')}` });
  }

  if (!process.env.ANTHROPIC_API_KEY) {
    return res.status(500).json({ error: 'Claude API key not configured' });
  }

  try {
    const dashboardData = loadCachedData();
    const response = await assistant.getQuickInsight(
      type as 'weekly-summary' | 'priorities' | 'overdue' | 'client-health',
      { dashboardData }
    );
    res.json({ response });
  } catch (error) {
    console.error('Insight error:', error);
    res.status(500).json({ error: 'Failed to generate insight' });
  }
});

// Analyse specific client
app.get('/api/analyse/client/:name', async (req, res) => {
  const { name } = req.params;

  if (!process.env.ANTHROPIC_API_KEY) {
    return res.status(500).json({ error: 'Claude API key not configured' });
  }

  try {
    const dashboardData = loadCachedData();
    const response = await assistant.analyseClient(name, { dashboardData });
    res.json({ response });
  } catch (error) {
    console.error('Analysis error:', error);
    res.status(500).json({ error: 'Failed to analyse client' });
  }
});

// Analyse QSP for client
app.get('/api/analyse/qsp/:clientName', async (req, res) => {
  const { clientName } = req.params;

  if (!process.env.ANTHROPIC_API_KEY) {
    return res.status(500).json({ error: 'Claude API key not configured' });
  }

  try {
    const dashboardData = loadCachedData();
    const response = await assistant.analyseQSP(clientName, { dashboardData });
    res.json({ response });
  } catch (error) {
    console.error('QSP analysis error:', error);
    res.status(500).json({ error: 'Failed to analyse QSP' });
  }
});

// Summarise a meeting
app.get('/api/analyse/meeting', async (req, res) => {
  const { title } = req.query;

  if (!title) {
    return res.status(400).json({ error: 'Meeting title is required' });
  }

  if (!process.env.ANTHROPIC_API_KEY) {
    return res.status(500).json({ error: 'Claude API key not configured' });
  }

  try {
    const dashboardData = loadCachedData();
    const response = await assistant.summariseMeeting(title as string, { dashboardData });
    res.json({ response });
  } catch (error) {
    console.error('Meeting summary error:', error);
    res.status(500).json({ error: 'Failed to summarise meeting' });
  }
});

// Clear chat history
app.post('/api/chat/clear', (req, res) => {
  assistant.clearHistory();
  res.json({ success: true });
});

// Get chat history
app.get('/api/chat/history', (req, res) => {
  res.json({ history: assistant.getHistory() });
});

// ============ TASK CREATION ENDPOINTS ============

// Extract action items from a specific meeting
app.get('/api/actions/meeting', async (req, res) => {
  const { title } = req.query;

  if (!title) {
    return res.status(400).json({ error: 'Meeting title is required' });
  }

  if (!process.env.ANTHROPIC_API_KEY) {
    return res.status(500).json({ error: 'Claude API key not configured' });
  }

  try {
    const dashboardData = loadCachedData();
    const result = await assistant.extractActionItems(title as string, { dashboardData });
    res.json(result);
  } catch (error) {
    console.error('Action extraction error:', error);
    res.status(500).json({ error: 'Failed to extract action items' });
  }
});

// Extract all pending action items from recent meetings
app.get('/api/actions/pending', async (req, res) => {
  if (!process.env.ANTHROPIC_API_KEY) {
    return res.status(500).json({ error: 'Claude API key not configured' });
  }

  try {
    const dashboardData = loadCachedData();
    const result = await assistant.extractAllPendingActions({ dashboardData });
    res.json(result);
  } catch (error) {
    console.error('Pending actions error:', error);
    res.status(500).json({ error: 'Failed to extract pending actions' });
  }
});

// Create a single task in Notion
app.post('/api/tasks', async (req, res) => {
  const { title, client, dueDate, priority, notes, source } = req.body;

  if (!title) {
    return res.status(400).json({ error: 'Task title is required' });
  }

  if (!process.env.NOTION_API_KEY || !process.env.NOTION_QSP_DATABASE_ID) {
    return res.status(500).json({ error: 'Notion not configured' });
  }

  try {
    const result = await notion.createTask({
      title,
      client,
      dueDate: dueDate ? new Date(dueDate) : undefined,
      priority,
      notes,
      source
    });
    res.json({ success: true, task: result });
  } catch (error) {
    console.error('Task creation error:', error);
    res.status(500).json({ error: 'Failed to create task' });
  }
});

// Create multiple tasks at once
app.post('/api/tasks/bulk', async (req, res) => {
  const { tasks } = req.body;

  if (!tasks || !Array.isArray(tasks) || tasks.length === 0) {
    return res.status(400).json({ error: 'Tasks array is required' });
  }

  if (!process.env.NOTION_API_KEY || !process.env.NOTION_QSP_DATABASE_ID) {
    return res.status(500).json({ error: 'Notion not configured' });
  }

  try {
    const tasksToCreate = tasks.map((t: any) => ({
      title: t.title,
      client: t.client,
      dueDate: t.dueDate ? new Date(t.dueDate) : undefined,
      priority: t.priority,
      notes: t.notes,
      source: t.source
    }));

    const results = await notion.createTasks(tasksToCreate);
    res.json({
      success: true,
      created: results.length,
      tasks: results
    });
  } catch (error) {
    console.error('Bulk task creation error:', error);
    res.status(500).json({ error: 'Failed to create tasks' });
  }
});

// Extract action items from meeting AND create tasks in one step
app.post('/api/actions/create-from-meeting', async (req, res) => {
  const { meetingTitle } = req.body;

  if (!meetingTitle) {
    return res.status(400).json({ error: 'Meeting title is required' });
  }

  if (!process.env.ANTHROPIC_API_KEY) {
    return res.status(500).json({ error: 'Claude API key not configured' });
  }

  if (!process.env.NOTION_API_KEY || !process.env.NOTION_QSP_DATABASE_ID) {
    return res.status(500).json({ error: 'Notion not configured' });
  }

  try {
    // First extract action items
    const dashboardData = loadCachedData();
    const extracted = await assistant.extractActionItems(meetingTitle, { dashboardData });

    if (extracted.actionItems.length === 0) {
      return res.json({
        success: true,
        message: 'No action items found in this meeting',
        created: 0,
        tasks: []
      });
    }

    // Create tasks from action items
    const tasksToCreate = extracted.actionItems
      .filter(item => item.owner !== 'client') // Only create tasks for items we own
      .map(item => ({
        title: item.title,
        client: extracted.client || undefined,
        dueDate: item.suggestedDueDate ? new Date(item.suggestedDueDate) : undefined,
        priority: item.priority,
        notes: item.notes,
        source: `Fathom meeting: ${extracted.meetingTitle} (${extracted.meetingDate})`
      }));

    const results = await notion.createTasks(tasksToCreate);

    res.json({
      success: true,
      meeting: extracted.meetingTitle,
      extracted: extracted.actionItems.length,
      created: results.length,
      tasks: results
    });
  } catch (error) {
    console.error('Create from meeting error:', error);
    res.status(500).json({ error: 'Failed to create tasks from meeting' });
  }
});

// Start server
app.listen(PORT, () => {
  console.log(`Dashboard server running at http://localhost:${PORT}`);
});
