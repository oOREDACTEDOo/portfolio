import cron from 'node-cron';
import { DataAggregator } from './aggregator';
import * as fs from 'fs';
import * as path from 'path';
import dotenv from 'dotenv';

dotenv.config();

const DATA_FILE = path.join(__dirname, '../data/dashboard-data.json');

class DataScheduler {
  private aggregator: DataAggregator;
  private isRunning: boolean = false;

  constructor() {
    this.aggregator = new DataAggregator();
  }

  async initialize(): Promise<boolean> {
    console.log('Initializing scheduler...');

    const hasGoogleAuth = await this.aggregator.initGoogleAuth();
    if (!hasGoogleAuth) {
      console.error('Google authentication required before scheduler can run.');
      console.log('Please authenticate via the dashboard first.');
      return false;
    }

    console.log('Google auth loaded successfully');
    return true;
  }

  async fetchAndSave(): Promise<void> {
    if (this.isRunning) {
      console.log('Fetch already in progress, skipping...');
      return;
    }

    this.isRunning = true;
    const startTime = Date.now();

    try {
      console.log(`\n[${new Date().toISOString()}] Starting scheduled data fetch...`);

      const data = await this.aggregator.fetchAllData();

      // Ensure data directory exists
      const dataDir = path.dirname(DATA_FILE);
      if (!fs.existsSync(dataDir)) {
        fs.mkdirSync(dataDir, { recursive: true });
      }

      // Save data
      fs.writeFileSync(DATA_FILE, JSON.stringify(data, null, 2));

      const duration = ((Date.now() - startTime) / 1000).toFixed(1);
      console.log(`[${new Date().toISOString()}] Fetch complete in ${duration}s`);
      console.log(`  - Calendar Events: ${data.allMeetings.length}`);
      console.log(`  - Notion Tasks: ${data.allTasks.length}`);
      console.log(`  - Fathom Meetings: ${data.allFathomSummaries.length}`);
      console.log(`  - Ranking Reports: ${data.allRankings.length}`);

      // Log any overdue tasks
      let totalOverdue = 0;
      for (const client of data.weeklyOverview.clients) {
        totalOverdue += client.tasksOverdue.length;
      }

      if (totalOverdue > 0) {
        console.log(`  ⚠ ${totalOverdue} overdue tasks`);
      }

    } catch (error) {
      console.error(`[${new Date().toISOString()}] Fetch error:`, error);
    } finally {
      this.isRunning = false;
    }
  }

  start(cronExpression: string = '0 7 * * *'): void {
    console.log(`\nScheduler started with cron: ${cronExpression}`);
    console.log('(Default: Daily at 7:00 AM)');

    // Run immediately on start
    this.fetchAndSave();

    // Schedule recurring fetches
    cron.schedule(cronExpression, () => {
      this.fetchAndSave();
    });

    console.log('\nScheduler is running. Press Ctrl+C to stop.');
  }
}

async function main() {
  console.log('='.repeat(50));
  console.log('Client Time Manager - Data Scheduler');
  console.log(`Started at: ${new Date().toISOString()}`);
  console.log('='.repeat(50));

  const scheduler = new DataScheduler();

  const initialized = await scheduler.initialize();
  if (!initialized) {
    console.log('\nTo authenticate:');
    console.log('1. Run: npm run dashboard');
    console.log('2. Open http://localhost:3000');
    console.log('3. Click "Refresh Data" to trigger OAuth');
    console.log('4. Then run this scheduler again');
    process.exit(1);
  }

  // Get cron expression from env or use default (7am daily)
  const cronExpression = process.env.FETCH_SCHEDULE || '0 7 * * *';

  scheduler.start(cronExpression);
}

main();
