#!/usr/bin/env node
import { execSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';

const root = process.cwd();
const shellPath = path.join(root, 'src/components/layouts/Shell.tsx');
const packageJsonPath = path.join(root, 'package.json');

function run(cmd) {
  try {
    return execSync(cmd, { stdio: ['ignore', 'pipe', 'pipe'] }).toString().trim();
  } catch {
    return '';
  }
}

function section(title) {
  console.log(`\n=== ${title} ===`);
}

console.log('Frontend Dev Doctor (Next.js runtime consistency check)');

section('Source sanity');
if (!fs.existsSync(shellPath)) {
  console.log(`❌ Missing file: ${shellPath}`);
  process.exit(1);
}
const shell = fs.readFileSync(shellPath, 'utf8');
const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
const sourceChecks = [
  { label: 'Shell uses runtime version hook', ok: shell.includes('useRuntimeVersion') },
  { label: 'Inbox nav item', ok: shell.includes("label: 'Inbox'") },
  { label: 'Workspaces nav item', ok: shell.includes("label: 'Workspaces'") },
  { label: 'TOOLS section', ok: shell.includes("label: 'TOOLS'") },
];
for (const c of sourceChecks) {
  console.log(`${c.ok ? '✅' : '❌'} ${c.label}`);
}

section('Port 3000 listeners');
const listenersRaw = run("lsof -nP -iTCP:3000 -sTCP:LISTEN | tail -n +2");
if (!listenersRaw) {
  console.log('⚠️ No process listening on :3000');
} else {
  const rows = listenersRaw.split('\n').filter(Boolean);
  console.log(`Found ${rows.length} listener(s) on :3000`);
  for (const row of rows) {
    const cols = row.trim().split(/\s+/);
    const pid = cols[1];
    const cmd = cols[0];
    const cwd = run(`lsof -a -p ${pid} -d cwd -Fn | tail -n 1 | sed 's/^n//'`);
    console.log(`- PID ${pid} (${cmd}) cwd=${cwd || 'unknown'}`);
  }
}

section('Runtime response check');
const html = run('curl -s http://localhost:3000');
if (!html) {
  console.log('⚠️ Could not fetch http://localhost:3000');
  console.log('   Start frontend with: npm run dev');
  process.exit(0);
}

const versionRaw = run('curl -s http://localhost:3000/api/version');
let versionPayload = null;
try {
  versionPayload = versionRaw ? JSON.parse(versionRaw) : null;
} catch {
  versionPayload = null;
}

const runtimeChecks = [
  {
    label: 'Runtime /api/version reachable',
    ok: Boolean(versionPayload && versionPayload.version),
  },
  {
    label: 'Runtime version matches package.json',
    ok: Boolean(versionPayload && versionPayload.version === packageJson.version),
  },
  { label: 'Runtime HTML has Waypoint brand', ok: html.includes('Waypoint') },
  { label: 'Runtime has Inbox', ok: html.includes('Inbox') },
  { label: 'Runtime has Workspaces', ok: html.includes('Workspaces') },
  { label: 'Runtime missing legacy New Leads', ok: !html.includes('New Leads') },
  { label: 'Runtime missing legacy Trip Pipeline', ok: !html.includes('Trip Pipeline') },
];
for (const c of runtimeChecks) {
  console.log(`${c.ok ? '✅' : '❌'} ${c.label}`);
}

const failed = [...sourceChecks, ...runtimeChecks].some((c) => !c.ok);

section('Recommendation');
if (failed) {
  console.log('⚠️ Detected mismatch or stale runtime.');
  console.log('Run: npm run dev:reset');
  console.log('Then: npm run dev');
} else {
  console.log('✅ Source and runtime look consistent.');
}
