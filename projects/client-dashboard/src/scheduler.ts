import cron from 'node-cron';
import { spawn } from 'child_process';
import * as path from 'path';
import dotenv from 'dotenv';

dotenv.config();

const FETCH_SCRIPT = path.join(__dirname, 'fetch-all.js');

// Schedule: Run at 7am every day (adjust as needed)
const SCHEDULE = '0 7 * * *';

console.log('='.repeat(50));
console.log('Client Dashboard - Scheduler');
console.log('='.repeat(50));
console.log(`\nSchedule: ${SCHEDULE} (7:00 AM daily)`);
console.log('Waiting for next scheduled run...\n');
console.log('Press Ctrl+C to stop\n');

// Run the fetch script
function runFetch() {
  console.log(`\n[${new Date().toISOString()}] Starting scheduled fetch...`);

  const process = spawn('node', [FETCH_SCRIPT], {
    stdio: 'inherit',
    shell: true
  });

  process.on('close', (code) => {
    if (code === 0) {
      console.log(`[${new Date().toISOString()}] Fetch completed successfully`);
    } else {
      console.error(`[${new Date().toISOString()}] Fetch failed with code ${code}`);
    }
    console.log('\nWaiting for next scheduled run...');
  });
}

// Schedule the task
cron.schedule(SCHEDULE, () => {
  runFetch();
});

// Option to run immediately on startup
const args = process.argv.slice(2);
if (args.includes('--run-now')) {
  console.log('Running initial fetch...');
  runFetch();
}

console.log('Scheduler started. Commands:');
console.log('  --run-now  Run fetch immediately on start\n');
