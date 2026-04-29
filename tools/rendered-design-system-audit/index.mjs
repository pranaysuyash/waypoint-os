#!/usr/bin/env node

/**
 * rendered-design-system-audit
 *
 * Systematic visual audit of a rendered frontend.
 * Extracts actual design tokens from the DOM and compares against DESIGN.md.
 * Uses Playwright for browser screenshotting + DOM inspection.
 *
 * Usage:
 *   node tools/rendered-design-system-audit/index.mjs
 *
 * Options:
 *   --url       Base URL (default: http://localhost:3000)
 *   --out       Output directory (default: ./tools/rendered-design-system-audit/audit-output)
 *   --pages     Comma-separated page paths to audit (default: all)
 *   --serve     Start dev server first
 *   --cdp       Connect to existing Chrome via CDP (default: launch headless).
 *              Usage: --cdp http://localhost:9222 (or just --cdp for default)
 *              Launch Chrome with: /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port=9222
 *   --wait      Wait strategy: load (default), domcontentloaded, networkidle
 */

import { chromium } from 'playwright';
import { existsSync, mkdirSync, writeFileSync, readFileSync } from 'fs';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';
import { spawn } from 'child_process';

const __dirname = dirname(fileURLToPath(import.meta.url));
const DESIGN_MD_PATH = resolve(__dirname, '../../frontend/DESIGN.md');

// ── Configuration ──────────────────────────────────────────────────────────

const CONFIG = {
  baseUrl: process.argv.includes('--url')
    ? process.argv[process.argv.indexOf('--url') + 1]
    : 'http://localhost:3000',
  outDir: process.argv.includes('--out')
    ? process.argv[process.argv.indexOf('--out') + 1]
    : resolve(__dirname, 'audit-output'),
  pages: process.argv.includes('--pages')
    ? process.argv[process.argv.indexOf('--pages') + 1].split(',')
    : ['/', '/login', '/inbox', '/workspace', '/settings', '/itinerary-checker'],
  serve: process.argv.includes('--serve'),
  cdp: process.argv.includes('--cdp')
    ? (process.argv[process.argv.indexOf('--cdp') + 1] || 'http://localhost:9222')
    : null,
  waitUntil: process.argv.includes('--wait')
    ? process.argv[process.argv.indexOf('--wait') + 1]
    : 'load',
};

const PAGES = {
  '/': { label: 'Marketing Landing', type: 'public' },
  '/login': { label: 'Login', type: 'auth' },
  '/inbox': { label: 'Inbox', type: 'app' },
  '/workspace': { label: 'Workspace', type: 'app' },
  '/settings': { label: 'Settings', type: 'app' },
  '/itinerary-checker': { label: 'Itinerary Checker', type: 'public' },
};

// Design tokens expected per DESIGN.md (Docs/DESIGN.md — v2.0 for this project)
const EXPECTED_TOKENS = {
  backgrounds: {
    '--bg-canvas': '#080a0c',
    '--bg-surface': '#0f1115',
    '--bg-elevated': '#161b22',
    '--bg-highlight': '#1c2128',
    '--bg-input': '#111318',
  },
  text: {
    '--text-primary': '#e6edf3',
    '--text-secondary': '#8b949e',
    '--text-tertiary': '#6e7681',
    '--text-muted': '#484f58',
    '--text-accent': '#58a6ff',
  },
  accents: {
    '--accent-green': '#3fb950',
    '--accent-amber': '#d29922',
    '--accent-red': '#f85149',
    '--accent-blue': '#58a6ff',
    '--accent-purple': '#a371f7',
    '--accent-cyan': '#39d0d8',
    '--accent-orange': '#ff9248',
  },
  geo: {
    '--geo-land': '#1c2128',
    '--geo-water': '#0d2137',
    '--geo-route': '#39d0d8',
    '--geo-waypoint': '#d29922',
    '--geo-destination': '#3fb950',
  },
  borders: {
    '--border-default': '#30363d',
    '--border-hover': '#8b949e',
    '--border-active': '#58a6ff',
    '--border-route': 'rgba(57, 208, 216, 0.3)',
  },
  spacing: {
    '--space-1': '4px',
    '--space-2': '8px',
    '--space-3': '12px',
    '--space-4': '16px',
    '--space-5': '20px',
    '--space-6': '24px',
    '--space-8': '32px',
    '--space-10': '40px',
    '--space-12': '48px',
  },
};

// ── Helpers ────────────────────────────────────────────────────────────────

function normalizeColor(val) {
  const s = String(val).trim().toLowerCase();
  if (s.startsWith('#')) return s.slice(0, 7);
  if (s.startsWith('rgb')) {
    const m = s.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/);
    if (m) {
      return `#${[m[1], m[2], m[3]].map(v => parseInt(v).toString(16).padStart(2, '0')).join('')}`;
    }
  }
  return s;
}

function tolerance(a, b) {
  const na = normalizeColor(a);
  const nb = normalizeColor(b);
  return na === nb ? 'exact' : na.toLowerCase() === nb.toLowerCase() ? 'case' : 'mismatch';
}

// ── Server Management ──────────────────────────────────────────────────────

let serverProcess = null;

async function startServer() {
  return new Promise((resolve, reject) => {
    console.log('Starting frontend dev server...');
    serverProcess = spawn('npm', ['run', 'dev'], {
      cwd: resolve(__dirname, '../../frontend'),
      stdio: ['ignore', 'pipe', 'pipe'],
      env: { ...process.env, PORT: '3000' },
    });

    let started = false;
    const timeout = setTimeout(() => {
      if (!started) reject(new Error('Server startup timeout'));
    }, 60000);

    serverProcess.stdout.on('data', (data) => {
      const text = data.toString();
      if (text.includes('Local:') || text.includes('ready') || text.includes('3000')) {
        started = true;
        clearTimeout(timeout);
        setTimeout(() => resolve(), 2000);
      }
    });

    serverProcess.stderr.on('data', (data) => {
      const text = data.toString();
      if (text.includes('at http://localhost') || text.includes('ready') || text.includes('3000')) {
        started = true;
        clearTimeout(timeout);
        setTimeout(() => resolve(), 2000);
      }
    });

    serverProcess.on('error', reject);
  });
}

function stopServer() {
  if (serverProcess) {
    serverProcess.kill('SIGTERM');
    serverProcess = null;
  }
}

// ── DOM Extraction ─────────────────────────────────────────────────────────

async function extractCSSVariables(page) {
  return page.evaluate(() => {
    const root = document.documentElement;
    const style = getComputedStyle(root);
    const vars = {};
    for (let i = 0; i < style.length; i++) {
      const prop = style[i];
      if (prop.startsWith('--')) {
        vars[prop] = style.getPropertyValue(prop).trim();
      }
    }
    return vars;
  });
}

async function extractPageTokens(page, selector = 'body') {
  return page.evaluate((sel) => {
    const el = document.querySelector(sel);
    if (!el) return null;
    const s = getComputedStyle(el);
    const rect = el.getBoundingClientRect();
    return {
      tag: el.tagName,
      classes: el.className,
      dimensions: { width: Math.round(rect.width), height: Math.round(rect.height) },
      colors: {
        background: s.backgroundColor,
        color: s.color,
        borderColor: s.borderColor,
        borderTopColor: s.borderTopColor,
      },
      typography: {
        fontFamily: s.fontFamily,
        fontSize: s.fontSize,
        fontWeight: s.fontWeight,
        lineHeight: s.lineHeight,
        letterSpacing: s.letterSpacing,
        textTransform: s.textTransform,
      },
      spacing: {
        padding: {
          top: s.paddingTop, right: s.paddingRight,
          bottom: s.paddingBottom, left: s.paddingLeft,
        },
        margin: {
          top: s.marginTop, right: s.marginRight,
          bottom: s.marginBottom, left: s.marginLeft,
        },
        gap: s.gap,
      },
      borders: {
        radius: s.borderRadius,
        width: s.borderWidth,
        style: s.borderStyle,
      },
      effects: {
        boxShadow: s.boxShadow,
        opacity: s.opacity,
        backdropFilter: s.backdropFilter,
      },
      layout: {
        display: s.display,
        position: s.position,
        flexDirection: s.flexDirection,
        alignItems: s.alignItems,
        justifyContent: s.justifyContent,
        gridTemplateColumns: s.gridTemplateColumns,
        gap: s.gap,
      },
    };
  }, selector);
}

async function extractAllCards(page, cardSelector) {
  return page.evaluate((sel) => {
    const cards = document.querySelectorAll(sel);
    return Array.from(cards).slice(0, 5).map((c, i) => {
      const s = getComputedStyle(c);
      const r = c.getBoundingClientRect();
      return {
        index: i,
        tag: c.tagName,
        classes: c.className.slice(0, 200),
        dimensions: { w: Math.round(r.width), h: Math.round(r.height) },
        background: s.backgroundColor,
        borderColor: s.borderColor,
        borderRadius: s.borderRadius,
        boxShadow: s.boxShadow,
        padding: `${s.paddingTop} ${s.paddingRight} ${s.paddingBottom} ${s.paddingLeft}`,
      };
    });
  }, cardSelector);
}

async function extractButtons(page) {
  return page.evaluate(() => {
    const btns = document.querySelectorAll('button, a[role="button"], [class*="btn-"], [class*="button"]');
    return Array.from(btns).slice(0, 10).map((b) => {
      const s = getComputedStyle(b);
      const r = b.getBoundingClientRect();
      return {
        text: b.textContent.trim().slice(0, 60),
        tag: b.tagName,
        classes: b.className.slice(0, 200),
        dimensions: { w: Math.round(r.width), h: Math.round(r.height) },
        background: s.backgroundColor,
        color: s.color,
        borderColor: s.borderColor,
        borderRadius: s.borderRadius,
        fontFamily: s.fontFamily,
        fontSize: s.fontSize,
        fontWeight: s.fontWeight,
        boxShadow: s.boxShadow,
      };
    });
  });
}

async function extractInputs(page) {
  return page.evaluate(() => {
    const inputs = document.querySelectorAll('input, textarea, select, [class*="input"]');
    return Array.from(inputs).slice(0, 10).map((i) => {
      const s = getComputedStyle(i);
      const r = i.getBoundingClientRect();
      return {
        type: i.tagName,
        placeholder: i.placeholder || '',
        classes: i.className.slice(0, 200),
        dimensions: { w: Math.round(r.width), h: Math.round(r.height) },
        background: s.backgroundColor,
        color: s.color,
        borderColor: s.borderColor,
        borderRadius: s.borderRadius,
        fontFamily: s.fontFamily,
        fontSize: s.fontSize,
        padding: `${s.paddingTop} ${s.paddingRight} ${s.paddingBottom} ${s.paddingLeft}`,
      };
    });
  });
}

async function extractBadges(page) {
  return page.evaluate(() => {
    const badges = document.querySelectorAll('[class*="badge"], [class*="Badge"], [class*="state-badge"]');
    return Array.from(badges).slice(0, 10).map((b) => {
      const s = getComputedStyle(b);
      return {
        text: b.textContent.trim().slice(0, 60),
        classes: b.className.slice(0, 200),
        background: s.backgroundColor,
        color: s.color,
        borderColor: s.borderColor,
        borderRadius: s.borderRadius,
        fontFamily: s.fontFamily,
        fontSize: s.fontSize,
        fontWeight: s.fontWeight,
        textTransform: s.textTransform,
        letterSpacing: s.letterSpacing,
      };
    });
  });
}

// ── DESIGN.md Comparison ────────────────────────────────────────────────────

function compareTokens(extracted, expected, label) {
  const results = [];
  for (const [token, expectedValue] of Object.entries(expected)) {
    const actual = extracted[token];
    if (actual === undefined) {
      results.push({ token, expected: expectedValue, actual: null, match: 'missing', severity: 'error' });
      continue;
    }
    const match = tolerance(actual, expectedValue);
    results.push({
      token,
      expected: expectedValue,
      actual,
      match,
      severity: match === 'mismatch' ? 'warn' : 'pass',
    });
  }
  return { label, results, passCount: results.filter(r => r.severity === 'pass').length, total: results.length };
}

function generateReport(perPage, cssVarResults, allIssues) {
  const lines = [];

  lines.push('# Rendered Design System Audit Report');
  lines.push('');
  lines.push(`**Date:** ${new Date().toISOString().split('T')[0]}`);
  lines.push(`**Base URL:** ${CONFIG.baseUrl}`);
  lines.push(`**Pages Audited:** ${CONFIG.pages.join(', ')}`);
  lines.push('');

  // ── CSS Variable Audit ──
  lines.push('## 1. CSS Custom Property Audit (vs DESIGN.md)');
  lines.push('');
  lines.push(`| Variable | Expected | Actual | Match |`);
  lines.push(`|---|---|---|---|`);
  for (const group of cssVarResults) {
    lines.push(`| **${group.label}** | | | |`);
    for (const r of group.results) {
      const icon = r.severity === 'pass' ? '✅' : r.severity === 'warn' ? '⚠️' : '❌';
      lines.push(`| \`${r.token}\` | \`${r.expected}\` | \`${r.actual || 'MISSING'}\` | ${icon} ${r.match} |`);
    }
  }
  lines.push('');

  const totalCSS = cssVarResults.reduce((s, g) => s + g.total, 0);
  const passCSS = cssVarResults.reduce((s, g) => s + g.passCount, 0);
  lines.push(`**CSS Token Compliance:** ${passCSS}/${totalCSS} (${Math.round(passCSS / totalCSS * 100)}%)`);
  lines.push('');

  // ── Page-by-Page Audit ──
  lines.push('## 2. Page-Level Visual Audit');
  lines.push('');
  for (const [path, data] of Object.entries(perPage)) {
    const cfg = PAGES[path] || { label: path, type: 'unknown' };
    lines.push(`### ${cfg.label} (\`${path}\`)`);
    lines.push('');
    if (data.error) {
      lines.push(`⚠️ **Error:** ${data.error}`);
      lines.push('');
      continue;
    }
    lines.push(`Screenshot: \`${data.screenshot}\``);
    lines.push('');

    // Body-level tokens
    if (data.bodyTokens) {
      lines.push('#### Body Defaults');
      lines.push('| Property | Value |');
      lines.push('|---|---|');
      const bt = data.bodyTokens;
      lines.push(`| Background | \`${bt.colors.background}\` |`);
      lines.push(`| Text Color | \`${bt.colors.color}\` |`);
      lines.push(`| Font Family | ${bt.typography.fontFamily} |`);
      lines.push(`| Font Size | ${bt.typography.fontSize} |`);
      lines.push(`| Font Weight | ${bt.typography.fontWeight} |`);
      lines.push(`| Line Height | ${bt.typography.lineHeight} |`);
      lines.push('');
    }

    // Cards
    if (data.cards && data.cards.length > 0) {
      lines.push('#### Cards');
      lines.push('| # | Background | Border | Radius | Shadow |');
      lines.push('|---|---|---|---|---|');
      for (const c of data.cards) {
        lines.push(`| ${c.index} | \`${c.background}\` | \`${c.borderColor}\` | \`${c.borderRadius}\` | ${c.boxShadow === 'none' ? 'none' : 'yes'} |`);
      }
      lines.push('');
    }

    // Buttons
    if (data.buttons && data.buttons.length > 0) {
      lines.push('#### Buttons');
      lines.push('| Text | Bg | Color | Border | Radius | Font |');
      lines.push('|---|---|---|---|---|---|');
      for (const b of data.buttons) {
        lines.push(`| ${b.text.slice(0, 40)} | \`${b.background}\` | \`${b.color}\` | \`${b.borderColor}\` | \`${b.borderRadius}\` | ${b.fontSize} ${b.fontWeight} |`);
      }
      lines.push('');
    }

    // Inputs
    if (data.inputs && data.inputs.length > 0) {
      lines.push('#### Inputs');
      lines.push('| Type | Bg | Color | Border | Radius | Padding |');
      lines.push('|---|---|---|---|---|---|');
      for (const i of data.inputs) {
        lines.push(`| ${i.type}${i.placeholder ? ` (${i.placeholder})` : ''} | \`${i.background}\` | \`${i.color}\` | \`${i.borderColor}\` | \`${i.borderRadius}\` | ${i.padding} |`);
      }
      lines.push('');
    }

    // Badges
    if (data.badges && data.badges.length > 0) {
      lines.push('#### Badges');
      lines.push('| Text | Bg | Color | Border | Radius | Font |');
      lines.push('|---|---|---|---|---|---|');
      for (const b of data.badges) {
        lines.push(`| ${b.text.slice(0, 40)} | \`${b.background}\` | \`${b.color}\` | \`${b.borderColor}\` | \`${b.borderRadius}\` | ${b.fontSize} ${b.fontWeight} ${b.textTransform} |`);
      }
      lines.push('');
    }
  }

  // ── Discrepancies Summary ──
  lines.push('## 3. Discrepancies & Issues');
  lines.push('');
  if (allIssues.length === 0) {
    lines.push('✅ No discrepancies found. Design tokens match DESIGN.md specifications.');
  } else {
    lines.push(`| Severity | Category | Detail |`);
    lines.push('|---|---|---|');
    for (const issue of allIssues) {
      const icon = issue.severity === 'error' ? '❌' : issue.severity === 'warn' ? '⚠️' : '💡';
      lines.push(`| ${icon} ${issue.severity} | ${issue.category} | ${issue.detail} |`);
    }
  }
  lines.push('');

  // ── Recommendations ──
  lines.push('## 4. Recommendations');
  lines.push('');
  const warnIssues = allIssues.filter(i => i.severity === 'warn' || i.severity === 'error');
  if (warnIssues.length === 0) {
    lines.push('No action required — design system is rendering as specified.');
  } else {
    lines.push('| Priority | Action |');
    lines.push('|---|---|');
    for (const issue of warnIssues) {
      lines.push(`| ${issue.severity === 'error' ? '🔴 High' : '🟡 Medium'} | ${issue.detail} |`);
    }
  }
  lines.push('');

  return lines.join('\n');
}

// ── Main Audit ─────────────────────────────────────────────────────────────

async function runAudit() {
  console.log('');
  console.log('╔══════════════════════════════════════════════╗');
  console.log('║    Rendered Design System Audit              ║');
  console.log('╚══════════════════════════════════════════════╝');
  console.log('');

  // Start server if needed
  if (CONFIG.serve) {
    try {
      await startServer();
      console.log('✓ Server started');
    } catch (e) {
      console.error('✗ Failed to start server:', e.message);
      process.exit(1);
    }
  }

  // Prepare output directory
  mkdirSync(CONFIG.outDir, { recursive: true });
  const screenshotsDir = resolve(CONFIG.outDir, 'screenshots');
  mkdirSync(screenshotsDir, { recursive: true });

  // Launch or connect to browser
  let browser;
  if (CONFIG.cdp) {
    console.log(`Connecting to Chrome via CDP at ${CONFIG.cdp}...`);
    browser = await chromium.connectOverCDP(CONFIG.cdp);
  } else {
    console.log('Launching headless browser...');
    browser = await chromium.launch({ headless: true });
  }
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    deviceScaleFactor: 2,
  });

  const perPage = {};
  const allIssues = [];
  let extractedVars = null;

  for (const path of CONFIG.pages) {
    const url = `${CONFIG.baseUrl}${path}`;
    const cfg = PAGES[path] || { label: path, type: 'unknown' };
    console.log(`\n  ── ${cfg.label} (${url}) ──`);

    const page = await context.newPage();

    try {
      // Navigate with configurable wait strategy
      await page.goto(url, { waitUntil: CONFIG.waitUntil, timeout: 15000 }).catch(() =>
        page.waitForTimeout(2000) // continue even if timeout
      );
      await page.waitForTimeout(1000);

      // Screenshot
      const screenshotName = `${path.replace(/\//g, '_') || 'root'}.png`;
      const screenshotPath = resolve(screenshotsDir, screenshotName);
      await page.screenshot({ path: screenshotPath, fullPage: true });
      console.log(`  ✓ Screenshot: ${screenshotName}`);

      // Extract CSS variables from :root
      const vars = await extractCSSVariables(page);
      if (!extractedVars) extractedVars = vars;

      // Extract body-level tokens
      const bodyTokens = await extractPageTokens(page, 'body');

      // Extract cards
      const cardSelectors = ['[class*="card"]', '[class*="Card"]', '[class*="trip-card"]', '[class*="TripCard"]'];
      let cards = [];
      for (const sel of cardSelectors) {
        const c = await extractAllCards(page, sel);
        if (c.length > 0) { cards = c; break; }
      }

      // Extract buttons
      const buttons = await extractButtons(page);

      // Extract inputs (auth pages, settings)
      const inputs = await extractInputs(page);

      // Extract badges
      const badges = await extractBadges(page);

      perPage[path] = {
        screenshot: `screenshots/${screenshotName}`,
        bodyTokens,
        cards,
        buttons,
        inputs,
        badges,
      };

      console.log(`  ✓ Body: bg=${bodyTokens?.colors?.background || 'N/A'}, text=${bodyTokens?.colors?.color || 'N/A'}`);
      console.log(`  ✓ ${cards.length} cards, ${buttons.length} buttons, ${inputs.length} inputs, ${badges.length} badges`);

    } catch (err) {
      console.log(`  ✗ Error: ${err.message}`);
      perPage[path] = { error: err.message };
    } finally {
      await page.close();
    }
  }

  await browser.close();
  console.log('\nBrowser closed.');

  // ── CSS Variable Comparison ──
  console.log('\nComparing against DESIGN.md...');
  const cssVarResults = [];
  if (extractedVars) {
    for (const [group, tokens] of Object.entries(EXPECTED_TOKENS)) {
      const result = compareTokens(extractedVars, tokens, group);
      cssVarResults.push(result);
      for (const r of result.results) {
        if (r.severity === 'warn') {
          allIssues.push({
            severity: 'warn',
            category: `CSS Variable: ${group}`,
            detail: `\`${r.token}\` expected \`${r.expected}\` but found \`${r.actual}\``,
          });
        } else if (r.severity === 'error') {
          allIssues.push({
            severity: 'error',
            category: `CSS Variable: ${group}`,
            detail: `\`${r.token}\` is MISSING from rendered CSS (expected \`${r.expected}\`)`,
          });
        }
      }
    }
  }

  // Check for DESIGN.md vs globals.css discrepancies
  // DESIGN.md Docs/DESIGN.md says --text-secondary: #8b949e but globals.css uses #a8b3c1
  if (extractedVars && extractedVars['--text-secondary']) {
    const designtextSecondary = '#8b949e';
    if (normalizeColor(extractedVars['--text-secondary']) !== normalizeColor(designtextSecondary)) {
      allIssues.push({
        severity: 'info',
        category: 'DESIGN.md vs globals.css',
        detail: `Docs/DESIGN.md specifies --text-secondary as #8b949e, but globals.css uses ${extractedVars['--text-secondary']}. The globals.css has a note: "Lightened from #8b949e for AA compliance". Docs/DESIGN.md may need updating to match.`,
      });
    }
  }

  if (extractedVars && extractedVars['--text-tertiary']) {
    const designTextTertiary = '#6e7681';
    if (normalizeColor(extractedVars['--text-tertiary']) !== normalizeColor(designTextTertiary)) {
      allIssues.push({
        severity: 'info',
        category: 'DESIGN.md vs globals.css',
        detail: `Docs/DESIGN.md specifies --text-tertiary as #6e7681, but globals.css uses ${extractedVars['--text-tertiary']}. globals.css comment: "Lighter tertiary for better readability (~4.5:1)". Docs/DESIGN.md should be updated.`,
      });
    }
  }

  // Check font differences
  if (extractedVars && extractedVars['--font-display']) {
    if (!extractedVars['--font-display'].includes('sora') && !extractedVars['--font-display'].includes('Sora')) {
      allIssues.push({
        severity: 'info',
        category: 'Font Family',
        detail: `Docs/DESIGN.md specifies --font-display: "Inter", but globals.css uses ${extractedVars['--font-display']}. The actual code uses Sora via next/font. Docs need updating.`,
      });
    }
  }

  // Check frontend/DESIGN.md vs Docs/DESIGN.md consistency
  allIssues.push({
    severity: 'info',
    category: 'DESIGN.md Duplication',
    detail: 'Two DESIGN.md files exist: frontend/DESIGN.md (1112 lines, "Waypoint OS") and Docs/DESIGN.md (1185 lines, "Travel Agency Agent"). These have diverged significantly. Recommend consolidating to a single source of truth.',
  });

  // ── Generate Report ──
  console.log('Generating report...');
  const report = generateReport(perPage, cssVarResults, allIssues);
  const reportPath = resolve(CONFIG.outDir, 'DESIGN_AUDIT_REPORT.md');
  writeFileSync(reportPath, report, 'utf-8');

  // Also copy screenshots index
  const screenshotIndex = Object.entries(perPage).map(([path, data]) => {
    const cfg = PAGES[path] || { label: path };
    return `| [${cfg.label}](${path}) | ${data.error ? '⚠️ Error' : '✅ OK'} | ${data.screenshot ? `![](${data.screenshot})` : 'N/A'} |`;
  }).join('\n');

  const summaryPath = resolve(CONFIG.outDir, 'SUMMARY.md');
  writeFileSync(summaryPath, [
    '# Audit Summary',
    '',
    `**Passed:** ${cssVarResults.reduce((s, g) => s + g.passCount, 0)}/${cssVarResults.reduce((s, g) => s + g.total, 0)} CSS token checks`,
    `**Issues:** ${allIssues.filter(i => i.severity === 'warn' || i.severity === 'error').length} warnings/errors`,
    `**Info:** ${allIssues.filter(i => i.severity === 'info').length} informational items`,
    '',
    `Full report: [DESIGN_AUDIT_REPORT.md](DESIGN_AUDIT_REPORT.md)`,
    '',
    '## Screenshots',
    '| Page | Status | Screenshot |',
    '|---|---|---|',
    screenshotIndex,
    '',
  ].join('\n'), 'utf-8');

  // ── Summary ──
  const totalChecks = cssVarResults.reduce((s, g) => s + g.total, 0);
  const passedChecks = cssVarResults.reduce((s, g) => s + g.passCount, 0);
  const errors = allIssues.filter(i => i.severity === 'error').length;
  const warnings = allIssues.filter(i => i.severity === 'warn').length;

  console.log('\n╔══════════════════════════════════════════════╗');
  console.log('║    Audit Complete                            ║');
  console.log('╠══════════════════════════════════════════════╣');
  console.log(`║  Pages Screenshot: ${CONFIG.pages.length}                    ║`);
  console.log(`║  CSS Token Checks: ${totalChecks}                          ║`);
  console.log(`║  Passed:           ${passedChecks}                          ║`);
  console.log(`║  Warnings:         ${warnings}                          ║`);
  console.log(`║  Errors:           ${errors}                          ║`);
  console.log('╠══════════════════════════════════════════════╣');
  console.log(`║  Report: ${reportPath.slice(0, 50)}...  ║`);
  console.log(`║  Screenshots: ${screenshotsDir.slice(0, 50)}... ║`);
  console.log('╚══════════════════════════════════════════════╝');
  console.log('');

  // Cleanup
  if (CONFIG.serve) stopServer();
  process.exit(0);
}

runAudit().catch((err) => {
  console.error('Audit failed:', err);
  if (CONFIG.serve) stopServer();
  process.exit(1);
});
