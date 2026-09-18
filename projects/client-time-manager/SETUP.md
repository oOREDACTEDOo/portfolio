# Client Time Manager - Setup Guide

A unified dashboard for managing client work across Google Calendar, Notion, Fathom meetings, and SiteChecker rankings, with Claude AI assistant for insights.

## Prerequisites

- Node.js 18+
- npm
- Google Cloud Console access
- Notion account with API access
- SiteChecker account (optional)
- Anthropic API key

---

## 1. Install Dependencies

```bash
cd c:\Projects\client-time-manager
npm install
```

---

## 2. Google Cloud Setup

### Create Project & Enable APIs

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select existing
3. Enable these APIs:
   - Google Calendar API
   - Gmail API

### Create OAuth Credentials

1. Go to **APIs & Services > Credentials**
2. Click **Create Credentials > OAuth client ID**
3. Application type: **Web application**
4. Name: `Client Time Manager`
5. Authorized redirect URIs: `http://localhost:3000/auth/callback`
6. Download the credentials JSON

### Configure OAuth Consent Screen

1. Go to **APIs & Services > OAuth consent screen**
2. User type: External (or Internal if using Google Workspace)
3. Add app name and support email
4. Add scopes:
   - `https://www.googleapis.com/auth/calendar.readonly`
   - `https://www.googleapis.com/auth/gmail.readonly`
5. Add your email as a test user

---

## 3. Notion Setup

### Create Integration

1. Go to [Notion Integrations](https://www.notion.so/my-integrations)
2. Click **New integration**
3. Name: `Client Time Manager`
4. Select your workspace
5. Copy the **Internal Integration Token**

### Connect to Databases

1. Open each Notion database you want to connect
2. Click **...** menu > **Connections** > **Connect to** > Select your integration
3. Copy the database ID from the URL:
   - URL: `notion.so/workspace/abc123def456...`
   - Database ID: `abc123def456`

### Expected Database Properties

Your Notion task database should have:
- **Title**: Task name (title property)
- **Status**: Select with options: Not Started, In Progress, Completed, Blocked
- **Due Date**: Date property
- **Priority**: Select with options: High, Medium, Low
- **Client**: Select or text property
- **QSP Quarter**: Text (e.g., "Q1 2024")
- **Notes**: Text property
- **Source**: Text (for tracking where tasks came from)

---

## 4. SiteChecker Setup (Optional)

1. Log in to [SiteChecker](https://sitechecker.pro)
2. Go to **Settings > API**
3. Generate or copy your API key
4. Note the project IDs for each client

---

## 5. Claude AI Setup

1. Go to [Anthropic Console](https://console.anthropic.com)
2. Create an API key
3. Copy the key for your .env file

---

## 6. Environment Configuration

Create `.env` file in project root:

```env
# Server
PORT=3000

# Google OAuth (from downloaded credentials JSON)
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://localhost:3000/auth/callback

# Notion
NOTION_API_KEY=secret_xxxxxxxxxxxxx

# SiteChecker (optional)
SITECHECKER_API_KEY=your-sitechecker-api-key

# Claude AI
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxx

# Scheduler (optional - cron expression, default: 7am daily)
FETCH_SCHEDULE=0 7 * * *
```

---

## 7. Configure Clients

Edit `src/config/clients.ts` to add your clients:

```typescript
export const clients: Client[] = [
  {
    id: 'client-1',
    name: 'Client Name',
    aliases: ['Client', 'client.com', 'Client Ltd'],  // For matching across systems
    notionDatabaseId: 'abc123...',  // Optional
    sitecheckerProjectId: '12345'    // Optional
  },
  // Add more clients...
];
```

**Aliases**: The system uses these to match clients across different platforms. Include variations like:
- Company name
- Domain name
- Email domain
- Calendar event naming patterns

---

## 8. Build & Run

### Build TypeScript

```bash
npm run build
```

### Run Dashboard (Development)

```bash
npm run dashboard
```

Open http://localhost:3000

### First-Time Google Auth

1. Start the dashboard
2. Click **Refresh Data**
3. Complete the OAuth flow in your browser
4. Tokens are saved to `data/google-tokens.json`

---

## 9. Running in Production

### Using PM2

```bash
# Install PM2 globally
npm install -g pm2

# Start dashboard
pm2 start dist/index.js --name "client-dashboard"

# Start scheduler (for daily fetches)
pm2 start dist/scheduler.js --name "client-scheduler"

# Save PM2 configuration
pm2 save

# Enable startup on boot
pm2 startup
```

### PM2 Commands

```bash
pm2 list              # Show running processes
pm2 logs              # View logs
pm2 restart all       # Restart all processes
pm2 stop all          # Stop all processes
```

---

## 10. Manual Data Fetch

To fetch data manually without the scheduler:

```bash
npm run fetch
```

---

## Available Scripts

| Command | Description |
|---------|-------------|
| `npm run build` | Compile TypeScript |
| `npm run dashboard` | Start dashboard server |
| `npm run fetch` | Manual data fetch |
| `npm run scheduler` | Start scheduled fetcher |
| `npm run dev` | Development with auto-reload |

---

## API Endpoints

### Dashboard
- `GET /api/data` - Get all dashboard data
- `GET /api/refresh` - Refresh data from sources
- `GET /api/auth/status` - Check Google auth status

### Claude AI
- `POST /api/chat` - Chat with Claude assistant
- `GET /api/insights/:type` - Get specific insights (weekly-summary, priorities, overdue)
- `GET /api/analyse/client/:name` - Analyze specific client
- `GET /api/analyse/qsp/:clientName` - Analyze client's QSP progress

### Tasks & Actions
- `GET /api/actions/meeting?title=...` - Extract actions from meeting
- `GET /api/actions/pending` - Get uncaptured actions from all meetings
- `POST /api/tasks` - Create single task in Notion
- `POST /api/tasks/bulk` - Create multiple tasks
- `POST /api/actions/create-from-meeting` - Extract + create tasks from meeting

---

## Troubleshooting

### Google Auth Errors

- **Invalid redirect URI**: Ensure `GOOGLE_REDIRECT_URI` matches exactly in Cloud Console
- **Access denied**: Add your email as test user in OAuth consent screen
- **Token expired**: Delete `data/google-tokens.json` and re-authenticate

### Notion Errors

- **Unauthorized**: Ensure database is connected to your integration
- **Property not found**: Check database has required properties

### No Data Loading

- Check `.env` file exists with correct values
- Ensure `data/` directory exists
- Check console for API errors

---

## VPS Deployment (Ubuntu)

```bash
# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Clone/upload project
cd /var/www
git clone [your-repo] client-time-manager
cd client-time-manager

# Install dependencies
npm install

# Create .env with production values
nano .env

# Build
npm run build

# Setup PM2
npm install -g pm2
pm2 start dist/index.js --name "client-dashboard"
pm2 start dist/scheduler.js --name "client-scheduler"
pm2 save
pm2 startup

# Optional: Nginx reverse proxy
sudo apt install nginx
```

### Nginx Configuration

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

---

## Security Notes

- Keep `.env` file secure and never commit to git
- For production, consider:
  - Adding authentication to the dashboard
  - Using HTTPS (Let's Encrypt)
  - Restricting access by IP
  - Storing tokens securely
