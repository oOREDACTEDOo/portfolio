import * as fs from 'fs';
import * as path from 'path';
import dotenv from 'dotenv';
import { DataAggregator } from './aggregator';

dotenv.config();

const DATA_FILE = path.join(__dirname, '../data/dashboard-data.json');

async function main() {
  console.log('='.repeat(50));
  console.log('Client Dashboard - Data Fetch');
  console.log(`Started at: ${new Date().toISOString()}`);
  console.log('='.repeat(50));

  const aggregator = new DataAggregator();

  // Check Google auth
  const hasGoogleAuth = await aggregator.initGoogleAuth();
  if (!hasGoogleAuth) {
    console.error('\n❌ Google authentication required!');
    console.log('\nTo authenticate:');
    console.log('1. Run: npm run dashboard');
    console.log('2. Open http://localhost:3000 in your browser');
    console.log('3. Click "Refresh Data" to trigger OAuth flow');
    console.log('\nOr visit this URL directly:');
    console.log(aggregator.getGoogleAuthUrl());
    process.exit(1);
  }

  console.log('\n✅ Google authentication loaded');

  try {
    console.log('\n📊 Fetching data from all sources...\n');

    const data = await aggregator.fetchAllData();

    // Save to file
    const dataDir = path.dirname(DATA_FILE);
    if (!fs.existsSync(dataDir)) {
      fs.mkdirSync(dataDir, { recursive: true });
    }
    fs.writeFileSync(DATA_FILE, JSON.stringify(data, null, 2));

    // Print summary
    console.log('\n' + '='.repeat(50));
    console.log('FETCH COMPLETE');
    console.log('='.repeat(50));

    console.log(`\n📅 Calendar Events: ${data.allMeetings.length}`);
    console.log(`📝 Notion Tasks: ${data.allTasks.length}`);
    console.log(`🎥 Fathom Meetings: ${data.allFathomSummaries.length}`);
    console.log(`📈 Ranking Reports: ${data.allRankings.length}`);

    // Weekly summary
    const { weeklyOverview } = data;
    console.log('\n--- WEEKLY OVERVIEW ---');
    console.log(`Week: ${weeklyOverview.weekStart.toDateString()} - ${weeklyOverview.weekEnd.toDateString()}`);

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
        if (overdueCount > 0) console.log(`  ⚠️  ${overdueCount} overdue tasks`);
        if (dueCount > 0) console.log(`  📋 ${dueCount} tasks due this week`);
        if (meetingsCount > 0) console.log(`  📅 ${meetingsCount} upcoming meetings`);

        if (clientData.rankingSnapshot) {
          const { positionChanges, averagePosition } = clientData.rankingSnapshot;
          console.log(`  📈 Rankings: ↑${positionChanges.improved} ↓${positionChanges.declined} (avg: ${averagePosition.toFixed(1)})`);
        }
      }
    }

    if (totalOverdue > 0) {
      console.log(`\n⚠️  ATTENTION: ${totalOverdue} total overdue tasks!`);
    }

    console.log(`\n✅ Data saved to: ${DATA_FILE}`);
    console.log(`\nView dashboard at: http://localhost:${process.env.DASHBOARD_PORT || 3000}`);

  } catch (error) {
    console.error('\n❌ Error fetching data:', error);
    process.exit(1);
  }
}

main();
