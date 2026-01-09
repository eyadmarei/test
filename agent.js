#!/usr/bin/env node

/**
 * Simple wrapper to run the testing agent
 * Usage: node agent.js <url> <scenario>
 */

import { spawn } from 'child_process';

const args = process.argv.slice(2);

if (args.length < 2) {
  console.log('');
  console.log('🤖 Web Testing Agent');
  console.log('');
  console.log('Usage:');
  console.log('  node agent.js <URL> <SCENARIO>');
  console.log('');
  console.log('Examples:');
  console.log('  node agent.js https://github.com "Click on Explore"');
  console.log('  node agent.js https://google.com "Search for playwright"');
  console.log('');
  console.log('With JSON file:');
  console.log('  npm run dev test -- --file examples/example-google-search.json');
  console.log('');
  console.log('Options:');
  console.log('  --headless false    Show browser window');
  console.log('  --timeout 60000     Set timeout to 60 seconds');
  console.log('');
  process.exit(1);
}

const url = args[0];
const scenario = args.slice(1).join(' ');

// Run the agent
const child = spawn('npm', ['run', 'dev', 'test', '--', '--url', url, '--scenario', scenario], {
  stdio: 'inherit',
  shell: true
});

child.on('exit', (code) => {
  process.exit(code);
});
