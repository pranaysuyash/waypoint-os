#!/usr/bin/env node
import { execSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';

const root = process.cwd();
const nextDir = path.join(root, '.next');

function run(cmd) {
  try {
    return execSync(cmd, { stdio: ['ignore', 'pipe', 'pipe'] }).toString().trim();
  } catch {
    return '';
  }
}

console.log('Resetting frontend dev runtime...');

const pidsRaw = run('lsof -ti tcp:3000');
const pids = pidsRaw ? pidsRaw.split('\n').map((s) => s.trim()).filter(Boolean) : [];

if (pids.length > 0) {
  console.log(`Stopping ${pids.length} process(es) on :3000: ${pids.join(', ')}`);
  for (const pid of pids) {
    run(`kill ${pid}`);
  }
} else {
  console.log('No process found on :3000');
}

if (fs.existsSync(nextDir)) {
  fs.rmSync(nextDir, { recursive: true, force: true });
  console.log('Removed .next cache directory');
} else {
  console.log('No .next directory found');
}

console.log('✅ Reset complete. Start fresh with: npm run dev');
