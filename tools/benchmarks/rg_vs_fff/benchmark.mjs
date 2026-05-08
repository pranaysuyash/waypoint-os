import { spawnSync } from 'node:child_process';
import { performance } from 'node:perf_hooks';
import fs from 'node:fs';
import path from 'node:path';
import { FileFinder } from '@ff-labs/fff-node';

const REPO_ROOT = path.resolve(process.cwd(), '../../..');
const NON_EXISTENT_QUERY = `__RG_FFF_BENCH_${Date.now()}_${Math.random().toString(36).slice(2)}__`;

const QUERIES = [
  'TODO',
  'FastAPI',
  'Trip',
  'confidence',
  NON_EXISTENT_QUERY,
];

function runCommand(cmd, args, opts = {}) {
  const started = performance.now();
  const res = spawnSync(cmd, args, {
    cwd: REPO_ROOT,
    encoding: 'utf8',
    maxBuffer: 1024 * 1024 * 1024,
    ...opts,
  });
  const ended = performance.now();
  return { ...res, durationMs: ended - started };
}

function parseRssBytesFromTimeOutput(text) {
  const m = text.match(/^\s*(\d+)\s+maximum resident set size\s*$/m);
  if (!m) return null;
  return Number(m[1]);
}

function parseRgLines(stdout) {
  const lines = stdout.split('\n').filter(Boolean);
  const keys = new Set();
  const files = new Set();

  for (const line of lines) {
    const m = line.match(/^(.*?):(\d+):(.*)$/);
    if (!m) continue;
    const file = m[1].replace(/^\.\//, '');
    const lineNo = m[2];
    files.add(file);
    keys.add(`${file}:${lineNo}`);
  }

  return { totalMatched: keys.size, uniqueFiles: files.size, keys };
}

function getRgMemoryForQuery(query) {
  const escaped = query.replace(/'/g, `'\\''`);
  const cmd = `/usr/bin/time -l rg --no-heading --line-number --color never --smart-case --max-filesize 10M '${escaped}' . > /dev/null`;
  const res = runCommand('/bin/bash', ['-lc', cmd]);
  const rssBytes = parseRssBytesFromTimeOutput(res.stderr || '');
  return {
    exitCode: res.status,
    rssBytes,
  };
}

function runRgQuery(query) {
  const args = [
    '--no-heading',
    '--line-number',
    '--color',
    'never',
    '--smart-case',
    '--max-filesize',
    '10M',
    query,
    '.',
  ];

  const result = runCommand('rg', args);
  if (![0, 1].includes(result.status ?? 1)) {
    return {
      ok: false,
      error: result.stderr || `rg failed with code ${result.status}`,
    };
  }

  const parsed = parseRgLines(result.stdout || '');
  const mem = getRgMemoryForQuery(query);

  return {
    ok: true,
    totalMatched: parsed.totalMatched,
    uniqueFiles: parsed.uniqueFiles,
    keys: parsed.keys,
    durationMs: result.durationMs,
    rssBytes: mem.rssBytes,
  };
}

async function createFffFinder() {
  const initStart = performance.now();
  const init = FileFinder.create({
    basePath: REPO_ROOT,
    disableWatch: true,
    aiMode: true,
  });
  if (!init.ok) {
    return { ok: false, error: init.error };
  }

  const finder = init.value;
  const scanWait = await finder.waitForScan(120000);
  const initEnd = performance.now();

  if (!scanWait.ok) {
    finder.destroy();
    return { ok: false, error: scanWait.error };
  }

  if (!scanWait.value) {
    finder.destroy();
    return { ok: false, error: 'FFF scan timed out after 120s' };
  }

  const progress = finder.getScanProgress();
  const mem = process.memoryUsage();

  return {
    ok: true,
    finder,
    initAndScanMs: initEnd - initStart,
    scanProgress: progress.ok ? progress.value : null,
    processRssBytesAfterScan: mem.rss,
  };
}

function runFffQuery(finder, query) {
  const start = performance.now();
  let cursor = null;
  let totalMatched = 0;
  const files = new Set();
  const keys = new Set();

  while (true) {
    const res = finder.grep(query, {
      mode: 'plain',
      smartCase: true,
      maxFileSize: 10 * 1024 * 1024,
      maxMatchesPerFile: 0,
      cursor,
      timeBudgetMs: 0,
    });

    if (!res.ok) {
      return { ok: false, error: res.error };
    }

    for (const item of res.value.items) {
      totalMatched += 1;
      files.add(item.relativePath);
      keys.add(`${item.relativePath}:${item.lineNumber}`);
    }

    if (!res.value.nextCursor) break;
    cursor = res.value.nextCursor;
  }

  const end = performance.now();

  return {
    ok: true,
    totalMatched,
    uniqueFiles: files.size,
    keys,
    durationMs: end - start,
  };
}

async function main() {
  const report = {
    generatedAt: new Date().toISOString(),
    repoRoot: REPO_ROOT,
    environment: {
      nodeVersion: process.version,
      platform: process.platform,
      arch: process.arch,
    },
    queries: QUERIES,
    rg: {
      version: null,
      perQuery: {},
    },
    fff: {
      initAndScanMs: null,
      processRssBytesAfterScan: null,
      scanProgress: null,
      perQuery: {},
    },
    comparison: {},
  };

  const rgVer = runCommand('rg', ['--version']);
  report.rg.version = (rgVer.stdout || '').split('\n')[0] || 'unknown';

  const fffFinderResult = await createFffFinder();
  if (!fffFinderResult.ok) {
    report.fff.error = fffFinderResult.error;
    const outPath = path.join(REPO_ROOT, 'tools/benchmarks/rg_vs_fff/benchmark_results.json');
    fs.writeFileSync(outPath, JSON.stringify(report, null, 2));
    console.error('FFF initialization failed:', fffFinderResult.error);
    process.exit(1);
  }

  const finder = fffFinderResult.finder;
  report.fff.initAndScanMs = Number(fffFinderResult.initAndScanMs.toFixed(3));
  report.fff.processRssBytesAfterScan = fffFinderResult.processRssBytesAfterScan;
  report.fff.scanProgress = fffFinderResult.scanProgress;

  for (const query of QUERIES) {
    const rg = runRgQuery(query);
    if (!rg.ok) {
      report.rg.perQuery[query] = { error: rg.error };
      continue;
    }

    const fff = runFffQuery(finder, query);
    if (!fff.ok) {
      report.fff.perQuery[query] = { error: fff.error };
      continue;
    }

    report.rg.perQuery[query] = {
      totalMatched: rg.totalMatched,
      uniqueFiles: rg.uniqueFiles,
      durationMs: Number(rg.durationMs.toFixed(3)),
      rssBytes: rg.rssBytes,
    };

    report.fff.perQuery[query] = {
      totalMatched: fff.totalMatched,
      uniqueFiles: fff.uniqueFiles,
      durationMs: Number(fff.durationMs.toFixed(3)),
      processRssBytesCurrent: process.memoryUsage().rss,
    };

    const onlyRg = [...rg.keys].filter((k) => !fff.keys.has(k));
    const onlyFff = [...fff.keys].filter((k) => !rg.keys.has(k));

    report.comparison[query] = {
      rgOnlyCount: onlyRg.length,
      fffOnlyCount: onlyFff.length,
      sampleRgOnly: onlyRg.slice(0, 5),
      sampleFffOnly: onlyFff.slice(0, 5),
      speedupFffVsRg:
        rg.durationMs > 0 ? Number((rg.durationMs / fff.durationMs).toFixed(3)) : null,
    };
  }

  finder.destroy();

  const outPath = path.join(REPO_ROOT, 'tools/benchmarks/rg_vs_fff/benchmark_results.json');
  fs.writeFileSync(outPath, JSON.stringify(report, null, 2));
  console.log(outPath);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
