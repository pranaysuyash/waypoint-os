import { chromium } from 'playwright';
import { mkdirSync, writeFileSync, existsSync } from 'node:fs';
import { resolve, join } from 'node:path';

const BASE_URL = process.env.SIM_BASE_URL || 'http://localhost:3005';
const OUTPUT_DIR = process.env.SIM_OUTPUT_DIR || resolve('docs/audits/visual-evidence/2026-10-21-persona-simulation');
const AXE_PATH = resolve('frontend/node_modules/axe-core/axe.min.js');

mkdirSync(OUTPUT_DIR, { recursive: true });

const PERSONAS = [
  {
    id: 'P3-JUNIOR-01',
    name: 'Marcus Chen',
    title: 'Junior Travel Associate & New Hire',
    bucket: 'project_local',
    mandate: 'Evaluate guided onboarding, intake flow clarity, mistake prevention, guardrails against unvetted quotes or margin leakage.',
    routes: ['landing', 'login', 'workbench', 'inbox', 'itinerary-checker']
  },
  {
    id: 'P2-OWNER-01',
    name: 'Elena Rostova',
    title: 'Luxury Agency Owner & Managing Director',
    bucket: 'project_local',
    mandate: 'Review executive command, margin controls, luxury aesthetic fidelity, quote review gates, agency liability shield.',
    routes: ['landing', 'workbench', 'trips', 'settings']
  },
  {
    id: 'P4-CORP-01',
    name: 'Rachel Vance',
    title: 'Corporate Travel Coordinator & Policy Gatekeeper',
    bucket: 'project_local',
    mandate: 'Enforce corporate policy rules, fast multi-city itinerary review, exception handling, cost-center tracking.',
    routes: ['workbench', 'trips', 'itinerary-checker']
  },
  {
    id: 'P12-SECURITY-01',
    name: 'Major Devlin Vance',
    title: 'VP Global Security & Tactical Duty-of-Care Operations',
    bucket: 'project_local',
    mandate: 'Crisis detection, emergency extraction routing, risk sentinel warnings, resilient failover.',
    routes: ['workbench', 'inbox', 'itinerary-checker']
  },
  {
    id: 'P13-LEGAL-01',
    name: 'Clara Sterling',
    title: 'Chief Legal, Regulatory Compliance & A11y Officer',
    bucket: 'project_local',
    mandate: 'Audit WCAG compliance, contrast, semantic HTML, ARIA tags, legal terms/privacy, contractual liability.',
    routes: ['landing', 'login', 'workbench', 'settings', 'itinerary-checker']
  }
];

const ROUTE_CONFIG = {
  landing: { name: 'landing', path: '/' },
  login: { name: 'login', path: '/login' },
  workbench: { name: 'workbench', path: '/workbench' },
  trips: { name: 'trips', path: '/trips' },
  inbox: { name: 'inbox', path: '/inbox' },
  'itinerary-checker': { name: 'itinerary-checker', path: '/itinerary-checker' },
  settings: { name: 'settings', path: '/settings' },
};

const VIEWPORTS = [
  { name: 'desktop', width: 1440, height: 900 },
  { name: 'mobile', width: 390, height: 844 },
];

async function run() {
  console.log(`Starting Persona Simulation on ${BASE_URL}...`);
  console.log(`Output Directory: ${OUTPUT_DIR}`);
  console.log(`Axe Core Path: ${AXE_PATH} (exists: ${existsSync(AXE_PATH)})`);

  let browser;
  try {
    browser = await chromium.launch({ headless: true });
  } catch (err) {
    console.log('Falling back to system chrome channel...');
    browser = await chromium.launch({ channel: 'chrome', headless: true });
  }

  const masterReport = {
    app: 'Waypoint OS (Travel Agency Agent)',
    baseUrl: BASE_URL,
    date: new Date().toISOString(),
    outputDir: OUTPUT_DIR,
    personas: PERSONAS.map(p => ({ id: p.id, name: p.name, title: p.title })),
    surfaces: [],
    issueRegistry: [],
    scorecard: {}
  };

  for (const persona of PERSONAS) {
    console.log(`\n======================================================`);
    console.log(`[Persona: ${persona.name} (${persona.id})] - ${persona.title}`);
    console.log(`Mandate: ${persona.mandate}`);
    console.log(`======================================================`);

    for (const routeKey of persona.routes) {
      const route = ROUTE_CONFIG[routeKey];
      if (!route) continue;

      for (const vp of VIEWPORTS) {
        const safeName = `${persona.id.toLowerCase()}--${route.name}--${vp.name}`;
        const screenshotPath = join(OUTPUT_DIR, `${safeName}.png`);
        console.log(`  -> Capturing ${safeName} (${vp.width}x${vp.height})...`);

        const context = await browser.newContext({
          viewport: { width: vp.width, height: vp.height },
          userAgent: vp.name === 'mobile'
            ? 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1'
            : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
        });

        // Pre-hydrate cookies/localStorage
        await context.addInitScript(() => {
          try {
            localStorage.setItem('hasSeenWelcome', 'true');
            localStorage.setItem('waypoint_onboarding_dismissed', 'true');
          } catch (e) {}
        });

        const page = await context.newPage();
        const consoleErrors = [];
        page.on('console', msg => {
          if (msg.type() === 'error') {
            consoleErrors.push(msg.text().slice(0, 300));
          }
        });
        page.on('pageerror', err => {
          consoleErrors.push(`Uncaught: ${err.message?.slice(0, 300)}`);
        });

        const targetUrl = `${BASE_URL}${route.path}`;
        try {
          await page.goto(targetUrl, { waitUntil: 'networkidle', timeout: 30000 });
        } catch (e) {
          try {
            await page.goto(targetUrl, { waitUntil: 'domcontentloaded', timeout: 15000 });
          } catch (err2) {
            consoleErrors.push(`Navigation error: ${err2.message}`);
          }
        }

        // Wait for UI stabilization
        await page.waitForTimeout(2000);

        // Gather metrics
        const metrics = await page.evaluate(() => {
          return {
            title: document.title,
            url: location.href,
            buttonCount: document.querySelectorAll('button').length,
            linkCount: document.querySelectorAll('a').length,
            inputCount: document.querySelectorAll('input, select, textarea').length,
            headingTexts: Array.from(document.querySelectorAll('h1, h2, h3')).slice(0, 6).map(h => h.innerText?.trim()?.slice(0, 60)),
            scrollHeight: document.documentElement.scrollHeight,
            scrollWidth: document.documentElement.scrollWidth,
            hasHorizontalOverflow: document.documentElement.scrollWidth > window.innerWidth
          };
        }).catch(() => ({ title: 'Error', buttonCount: 0 }));

        // Run axe accessibility audit if script available
        let violations = [];
        let axePassCount = 0;
        if (existsSync(AXE_PATH)) {
          try {
            await page.addScriptTag({ path: AXE_PATH });
            const axeResult = await page.evaluate(async () => {
              if (window.axe) {
                return await window.axe.run({
                  runOnly: {
                    type: 'tag',
                    values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa']
                  }
                });
              }
              return null;
            });
            if (axeResult) {
              violations = axeResult.violations.map(v => ({
                id: v.id,
                impact: v.impact,
                description: v.description,
                help: v.help,
                helpUrl: v.helpUrl,
                tags: v.tags,
                nodes: v.nodes.slice(0, 3).map(n => ({
                  target: n.target,
                  html: n.html?.slice(0, 150),
                  failureSummary: n.failureSummary?.slice(0, 200)
                }))
              }));
              axePassCount = axeResult.passes?.length || 0;
            }
          } catch (axeErr) {
            console.warn(`    ! Axe run error: ${axeErr.message}`);
          }
        }

        // Take screenshot
        await page.screenshot({ path: screenshotPath, fullPage: false }).catch(err => {
          console.warn(`    ! Screenshot error: ${err.message}`);
        });

        const surfaceRecord = {
          personaId: persona.id,
          personaName: persona.name,
          route: route.name,
          path: route.path,
          viewport: vp.name,
          viewportDimensions: { width: vp.width, height: vp.height },
          screenshotPath,
          screenshotRel: `${safeName}.png`,
          metrics,
          violations,
          criticalViolations: violations.filter(v => v.impact === 'critical').length,
          seriousViolations: violations.filter(v => v.impact === 'serious').length,
          moderateViolations: violations.filter(v => v.impact === 'moderate').length,
          minorViolations: violations.filter(v => v.impact === 'minor').length,
          axePasses: axePassCount,
          consoleErrors,
          timestamp: new Date().toISOString()
        };

        masterReport.surfaces.push(surfaceRecord);
        console.log(`    ✓ Saved screenshot: ${safeName}.png | Title: "${metrics.title}" | Axe: ${violations.length} violations (Crit: ${surfaceRecord.criticalViolations}, Ser: ${surfaceRecord.seriousViolations}) | Errors: ${consoleErrors.length}`);

        await context.close();
      }
    }
  }

  await browser.close();

  const reportFile = join(OUTPUT_DIR, 'simulation-report.json');
  writeFileSync(reportFile, JSON.stringify(masterReport, null, 2), 'utf8');
  console.log(`\nSimulation complete! Report written to ${reportFile}`);
}

run().catch(err => {
  console.error('Simulation harness failed:', err);
  process.exit(1);
});
