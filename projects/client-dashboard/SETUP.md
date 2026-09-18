# Client Dashboard - Setup Guide

A unified dashboard that aggregates Google Calendar, Notion tasks, Fathom meeting summaries, and SiteChecker rankings.

## Prerequisites

- Node.js 18+
- npm or yarn
- Google Cloud account (for API access)
- Notion account with API integration
- SiteChecker account with API access

## Quick Start

```bash
cd client-dashboard
npm install
cp .env.example .env
# Edit .env with your credentials
npm run build
npm run dashboard
```

Then open http://localhost:3000 in your browser.

---

## Step 1: Google Cloud Setup

### Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing)
3. Enable these APIs:
   - Google Calendar API
   - Gmail API

### Create OAuth Credentials

1. Go to **APIs & Services > Credentials**
2. Click **Create Credentials > OAuth client ID**
3. Choose **Web application**
4. Add authorized redirect URI: `http://localhost:3000/auth/google/callback`
5. Copy the **Client ID** and **Client Secret**

### Configure OAuth Consent Screen

1. Go to **APIs & Services > OAuth consent screen**
2. Choose **External** (or Internal if G Suite)
3. Add your email as a test user
4. Add scopes:
   - `https://www.googleapis.com/auth/calendar.readonly`
   - `https://www.googleapis.com/auth/gmail.readonly`

---

## Step 2: Notion Setup

### Create an Integration

1. Go to [Notion Integrations](https://www.notion.so/my-integrations)
2. Click **New integration**
3. Name it (e.g., "Client Dashboard")
4. Select your workspace
5. Copy the **Internal Integration Token**

### Connect to Your Database

1. Open your QSP/Tasks database in Notion
2. Click **...** menu > **Add connections**
3. Select your integration
4. Copy the database ID from the URL:
   ```
   https://notion.so/workspace/DATABASE_ID?v=...
   ```

### Expected Database Structure

Your Notion database should have these properties (names are flexible):

| Property | Type | Notes |
|----------|------|-------|
| Name/Title | Title | Task name |
| Status | Status | Not Started, In Progress, Completed, Blocked |
| Due Date | Date | When task is due |
| Priority | Select | High, Medium, Low |
| Client | Select | Client name |
| Quarter | Select | Q1 2024, Q2 2024, etc. (optional) |

---

## Step 3: SiteChecker Setup

1. Log in to [SiteChecker](https://sitechecker.pro)
2. Go to **Account > API**
3. Generate an API key
4. Note your project IDs from the URL when viewing each project

---

## Step 4: Claude AI Setup (for AI Assistant)

The dashboard includes a Claude AI assistant that can analyse your data, summarise your week, and answer questions about clients.

1. Go to [Anthropic Console](https://console.anthropic.com/)
2. Create an account or sign in
3. Go to **API Keys**
4. Create a new API key
5. Copy the key (starts with `sk-ant-`)

Add to your `.env`:
```env
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx
```

### What Claude Can Do

- **Weekly summaries**: "What's my week looking like?"
- **Priority analysis**: "What should I focus on today?"
- **Client deep-dives**: "Tell me about Client X"
- **Meeting insights**: "Summarise my last meeting with Client Y"
- **QSP analysis**: "How is Client X tracking on their QSP?"
- **SEO insights**: "Which clients have improving rankings?"

---

## Step 5: Configure Clients

Edit `src/config/clients.ts` to add your clients:

```typescript
export const clients: Client[] = [
  {
    id: 'acme',
    name: 'Acme Corporation',
    aliases: ['Acme', 'Acme Corp', 'ACME'],
    notionDatabaseId: 'abc123...', // Optional: client-specific database
    sitecheckerProjectId: '12345'
  },
  {
    id: 'globex',
    name: 'Globex Industries',
    aliases: ['Globex', 'GI'],
    sitecheckerProjectId: '67890'
  }
];
```

The `aliases` array helps match clients across systems. For example:
- Calendar event: "Weekly call with Acme Corp"
- Notion task: "ACME website redesign"
- Both will be matched to "Acme Corporation"

---

## Step 6: Configure Environment

Create `.env` from the example:

```bash
cp .env.example .env
```

Fill in your credentials:

```env
# Google API
GOOGLE_CLIENT_ID=your_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_secret
GOOGLE_REDIRECT_URI=http://localhost:3000/auth/google/callback

# Notion API
NOTION_API_KEY=secret_xxx
NOTION_QSP_DATABASE_ID=abc123...

# SiteChecker API
SITECHECKER_API_KEY=your_api_key

# Claude AI
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx

# Dashboard
DASHBOARD_PORT=3000
```

---

## Running the Dashboard

### Development Mode

```bash
npm run dev
```

### Production Mode

```bash
npm run build
npm run dashboard
```

### Commands

| Command | Description |
|---------|-------------|
| `npm run dashboard` | Start the web dashboard server |
| `npm run fetch` | Manually fetch data from all sources |
| `npm run schedule` | Start the daily scheduler (7am) |
| `npm run schedule -- --run-now` | Start scheduler and run immediately |

---

## First Run - Google Authentication

1. Start the dashboard: `npm run dashboard`
2. Open http://localhost:3000
3. Click "Refresh Data"
4. You'll be redirected to Google OAuth
5. Grant permissions for Calendar and Gmail
6. You'll be redirected back to the dashboard
7. Data will be fetched automatically

The authentication token is saved to `data/google-token.json` for future runs.

---

## Running as a Background Service (Windows)

To run the scheduler automatically on startup:

### Option 1: Task Scheduler

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger: "When the computer starts" or "Daily at 7:00 AM"
4. Action: Start a program
   - Program: `node`
   - Arguments: `C:\Projects\client-dashboard\dist\scheduler.js`
   - Start in: `C:\Projects\client-dashboard`

### Option 2: PM2 (recommended)

```bash
npm install -g pm2
pm2 start dist/scheduler.js --name client-dashboard
pm2 save
pm2 startup
```

---

## Troubleshooting

### "Google auth required"

Run the dashboard and complete the OAuth flow:
```bash
npm run dashboard
# Open http://localhost:3000 and click Refresh Data
```

### "Notion API error"

- Ensure your integration is connected to the database
- Check database ID is correct
- Verify API key is valid

### "No data for client X"

- Check client name/aliases in `src/config/clients.ts`
- Ensure text matches how the client appears in each system

### Fathom emails not found

- Verify Fathom sends emails to your Gmail account
- Check if emails are from `fathom.video` domain
- Look at spam folder

---

## Architecture

```
client-dashboard/
├── src/
│   ├── types/          # TypeScript interfaces
│   ├── config/         # Client configuration
│   ├── integrations/   # API integrations
│   │   ├── google.ts   # Calendar + Gmail
│   │   ├── notion.ts   # Notion API
│   │   └── sitechecker.ts
│   ├── services/
│   │   └── claude-assistant.ts  # AI assistant
│   ├── aggregator.ts   # Data aggregation
│   ├── server.ts       # Express server + chat API
│   ├── fetch-all.ts    # CLI fetch script
│   └── scheduler.ts    # Daily scheduler
├── public/
│   └── index.html      # Dashboard UI with chat panel
├── data/               # Cached data (gitignored)
└── .env                # Configuration
```

---

## Using the Claude Assistant

Click the chat button (bottom right) to open the AI assistant panel.

### Quick Actions

Use the preset buttons for common queries:
- **Weekly Summary** - Overview of your week
- **Top Priorities** - What to focus on today
- **Overdue Items** - Tasks needing attention
- **Client Health** - Status across all clients

### Example Questions

```
"What meetings do I have with Acme this week?"
"Summarise my last call with Globex"
"Which clients have overdue tasks?"
"What are the action items from my meeting yesterday?"
"How is Acme's SEO performing?"
"What QSP tasks are due for Client X this quarter?"
"Give me a status update for all my clients"
```

### API Endpoints

The chat is powered by these endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/chat` | POST | Send a message to Claude |
| `/api/insights/:type` | GET | Get quick insights (weekly-summary, priorities, overdue, client-health) |
| `/api/analyse/client/:name` | GET | Deep-dive on a specific client |
| `/api/analyse/qsp/:name` | GET | QSP analysis for a client |
| `/api/analyse/meeting?title=...` | GET | Summarise a specific meeting |
| `/api/chat/history` | GET | Get conversation history |
| `/api/chat/clear` | POST | Clear conversation history |
