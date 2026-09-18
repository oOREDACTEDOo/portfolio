import * as fs from 'fs';
import * as path from 'path';
import dotenv from 'dotenv';
import { DataAggregator } from './aggregator';

dotenv.config();

const DATA_FILE = path.join(__dirname, '../data/dashboard-data.json');

async function main() {
  console.log('='.repeat(50));
  console.log('Client Time Manager - Data Fetch');
  console.log(`Started at: ${new Date().toISOString()}`);
  console.log('='.repeat(50));

  const aggregator = new DataAggregator();

  const hasGoogleAuth = await aggregator.initGoogleAuth();
  if (!hasGoogleAuth) {
    console.error('\nGoogle authentication required!');
    console.log('\nTo authenticate:');
    console.log('1. Run: npm run dashboard');
    console.log('2. Open http://localhost:3000');
    console.log('3. Click "Refresh Data" to trigger OAuth');
    process.exit(1);
  }

  console.log('\nGoogle auth loaded');

  try {
    console.log('\nFetching data from all sources...\n');

    const data = await aggregator.fetchAllData();

    const dataDir = path.dirname(DATA_FILE);
    if (!fs.existsSync(dataDir)) {
      fs.mkdirSync(dataDir, { recursive: true });
    }
    fs.writeFileSync(DATA_FILE, JSON.stringify(data, null, 2));

    console.log('\n' + '='.repeat(50));
    console.log('FETCH COMPLETE');
    console.log('='.repeat(50));

    console.log(`\nCalendar Events: ${data.allMeetings.length}`);
    console.log(`Notion Tasks: ${data.allTasks.length}`);
    console.log(`Fathom Meetings: ${data.allFathomSummaries.length}`);
    console.log(`Ranking Reports: ${data.allRankings.length}`);

    const { weeklyOverview } = data;
    console.log('\n--- WEEKLY OVERVIEW ---');

    let totalOverdue = 0;
    let totalDue = 0;

    for (const clientData of weeklyOverview.clients) {
      const overdueCount = clientData.tasksOverdue.length;
      const dueCount = clientData.tasksDue.length;
      const meetingsCount = clientData.upcomingMeetings.length;

      totalOverdue += overdueCount;
      totalDue += dueCount;

      if (overdueCount > 0 || dueCount > 0 || meetingsCount > 0) {
        console.log(`\n${clientData.client.name}:`);
        if (overdueCount > 0) console.log(`  ${overdueCount} overdue tasks`);
        if (dueCount > 0) console.log(`  ${dueCount} tasks due this week`);
        if (meetingsCount > 0) console.log(`  ${meetingsCount} upcoming meetings`);
      }
    }

    if (totalOverdue > 0) {
      console.log(`\nATTENTION: ${totalOverdue} total overdue tasks!`);
    }

    console.log(`\nData saved to: ${DATA_FILE}`);

  } catch (error) {
    console.error('\nError fetching data:', error);
    process.exit(1);
  }
}

main();
