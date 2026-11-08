#!/usr/bin/env node
// tools/verify_departure_board_handoff.mjs
//
// Live E2E walk of the departure-board → auth → workbench handoff lifecycle
// (canonical module: frontend/src/lib/departure-board-handoff.ts).
//
// Verifies, in one run:
//   T1  departure-board landing renders with a "Create workspace" CTA
//   T2  CTA click writes the sessionStorage handoff and lands on /signup
//   T3  /signup shows the Case Queue handoff banner (case title + IATA pill)
//   T4  signup succeeds → redirect to /workbench?source=departure-board&case=…&iata=…&prefill=…
//   T5  workbench intake consumes the handoff prefill into the note textarea
//   T6  the handoff key is CLEARED after auth success (stale-banner regression)
//   T7  revisiting /signup in the same tab shows NO stale banner
//   T8  /login shows NO stale banner either
//
// Usage:
//   node tools/verify_departure_board_handoff.mjs \
//     [--base http://127.0.0.1:3006] [--headed] [--email you@example.com]
//
// Prereqs:
//   - backend:   uv run uvicorn spine_api.server:app --port 8000
//   - frontend:  NEXT_PUBLIC_LANDING_VARIANT=departure-board npm run dev -- -p 3006
//   - browser:   cd frontend && npx playwright install chromium-headless-shell
//
// Evidence: Docs/sims/assets/handoff_walk/t*.png + console-error report on stdout.

import { chromium } from 'file:///Users/pranay/Projects/travel_agency_agent/frontend/node_modules/playwright/index.mjs';
import { mkdirSync, writeFileSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const REPO_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const SHOT_DIR = resolve(REPO_ROOT, 'Docs/sims/assets/handoff_walk');

// ── args ─────────────────────────────────────────────────────────────────────
const arg = (name, fallback) => {
  const i = process.argv.indexOf(name);
  return i > -1 && process.argv[i + 1] ? process.argv[i + 1] : fallback;
};
const BASE = arg('--base', 'http://127.0.0.1:3006');
const HEADED = process.argv.includes('--headed');
const EMAIL = arg('--email', `handoff-walk-${Date.now()}@test.com`);
const PASSWORD = 'HandoffWalk2026!';

const HANDOFF_KEY = 'waypoint_departure_board_handoff';
const results = [];
const consoleErrors = [];

const record = (id, pass, detail) => {
  results.push({ id, pass, detail });
  console.log(`${pass ? 'PASS' : 'FAIL'}  ${id}  ${detail}`);
};
const shot = (page, name) => {
  const path = resolve(SHOT_DIR, `${name}.png`);
  return page.screenshot({ path, scale: 'css' }).then(() => path);
};

mkdirSync(SHOT_DIR, { recursive: true });

const browser = await chromium.launch({ headless: !HEADED });
const context = await browser.newContext({ viewport: { width: 1600, height: 900 } });
const page = await context.newPage();
page.on('console', (m) => {
  if (m.type() === 'error') consoleErrors.push({ where: page.url(), text: m.text().slice(0, 300) });
});
page.on('pageerror', (e) => consoleErrors.push({ where: page.url(), text: String(e).slice(0, 300) }));

const readHandoff = () =>
  page.evaluate((key) => window.sessionStorage.getItem(key), HANDOFF_KEY);

try {
  // ── T1: board landing renders with the CTA ────────────────────────────────
  await page.goto(`${BASE}/`, { waitUntil: 'domcontentloaded' });
  const cta = page.getByRole('link', { name: /Create workspace/ });
  await cta.first().waitFor({ state: 'visible', timeout: 20_000 });
  const ctaCount = await cta.count();
  const handoffBefore = await readHandoff();
  record('T1 board landing + CTA', ctaCount > 0 && handoffBefore === null,
    `${ctaCount} CTA(s); initial handoff=${handoffBefore === null ? 'null (clean)' : handoffBefore}`);
  await shot(page, 't1_board_landing');

  // ── T2: CTA writes handoff + navigates to /signup ─────────────────────────
  await cta.first().click();
  await page.waitForURL(/\/signup/, { timeout: 15_000 });
  await page.waitForLoadState('domcontentloaded');
  const raw = await readHandoff();
  let handoff = null;
  try { handoff = raw ? JSON.parse(raw) : null; } catch { /* malformed */ }
  const wrote = Boolean(handoff && (handoff.caseSlug || handoff.caseTitle));
  record('T2 CTA writes handoff → /signup', wrote,
    wrote ? `caseSlug=${handoff.caseSlug} iata=${handoff.iataCode}` : `storage raw=${raw}`);
  await shot(page, 't2_signup_after_cta');

  // ── T3: signup shows the Case Queue handoff banner ────────────────────────
  const banner = page.getByTestId('signup-departure-board-context');
  const bannerVisible = await banner
    .waitFor({ state: 'visible', timeout: 20_000 })
    .then(() => true)
    .catch(() => false);
  const bannerText = bannerVisible ? (await banner.innerText()).replace(/\s+/g, ' ').slice(0, 160) : '(absent)';
  record('T3 signup handoff banner', bannerVisible, bannerText);
  await shot(page, 't3_signup_banner');

  // ── T4: signup success → workbench redirect with handoff params ──────────
  await page.getByLabel('Full name').fill('Handoff Walk Tester');
  await page.getByLabel('Work email').fill(EMAIL);
  await page.getByLabel('Password', { exact: true }).fill(PASSWORD);
  await page.getByLabel('Confirm password').fill(PASSWORD);
  await page.getByRole('checkbox').check();
  await page.getByRole('button', { name: /Create workspace/ }).click();
  await page.waitForURL(/\/workbench\?source=departure-board/, { timeout: 45_000 });
  await page.waitForLoadState('domcontentloaded');
  const url = new URL(page.url());
  const paramsOk =
    url.searchParams.get('source') === 'departure-board' &&
    Boolean(url.searchParams.get('case')) &&
    Boolean(url.searchParams.get('prefill'));
  record('T4 signup → workbench handoff redirect', paramsOk, page.url());
  await shot(page, 't4_workbench_redirect');

  // ── T5: intake consumes the prefill ───────────────────────────────────────
  const expectedPrefill = decodeURIComponent(url.searchParams.get('prefill'));
  const matched = await page
    .waitForFunction(
      (needle) =>
        Array.from(document.querySelectorAll('textarea')).some((t) =>
          (t.value || '').includes(needle.slice(0, 40)),
        ),
      expectedPrefill,
      { timeout: 15_000 },
    )
    .then(() => true)
    .catch(() => false);
  record('T5 intake prefill consumed', matched,
    matched ? `textarea contains "${expectedPrefill.slice(0, 60)}…"` : 'no textarea carries the prefill');
  await shot(page, 't5_intake_prefill');

  // ── T6: handoff cleared after auth success ────────────────────────────────
  const afterAuth = await readHandoff();
  record('T6 handoff cleared post-auth', afterAuth === null,
    afterAuth === null ? 'sessionStorage key removed' : `STALE: ${afterAuth}`);

  // ── T7: /signup revisit shows NO stale banner (same tab) ─────────────────
  await page.goto(`${BASE}/signup`, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(1_000); // allow any handoff-state effects to settle
  const staleSignup = await page.getByTestId('signup-departure-board-context').count();
  record('T7 signup revisit: no stale banner', staleSignup === 0,
    staleSignup === 0 ? 'banner absent' : `banner rendered ${staleSignup}×`);
  await shot(page, 't6_signup_no_stale_banner');

  // ── T8: /login shows NO stale banner ──────────────────────────────────────
  await page.goto(`${BASE}/login`, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(1_000);
  const staleLogin = await page.locator('.auth-handoff-banner').count();
  record('T8 login: no stale banner', staleLogin === 0,
    staleLogin === 0 ? 'banner absent' : `banner rendered ${staleLogin}×`);
  await shot(page, 't7_login_no_stale_banner');

  // ── T9: fresh-agency overview loads without 4xx/5xx ──────────────────────
  // (the board funnel lands brand-new agencies here; broken dashboards here
  //  break the entire acquisition path — caught live 2026-11-08)
  const overviewFailures = [];
  const onResponse = (r) => {
    if (r.status() >= 400) {
      overviewFailures.push({ status: r.status(), url: r.url() });
    }
  };
  page.on('response', onResponse);
  await page.goto(`${BASE}/overview`, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(8_000);
  page.off('response', onResponse);
  record('T9 fresh-agency overview clean', overviewFailures.length === 0,
    overviewFailures.length === 0
      ? 'no 4xx/5xx during overview load'
      : overviewFailures.slice(0, 4).map((f) => `[${f.status}] ${f.url.replace(BASE, '')}`).join(' | '));
  await shot(page, 't8_overview');
} catch (err) {
  const failedAt = page.url();
  console.error(`WALK ABORTED at ${failedAt}:`, err.message ?? err);
  await shot(page, 'tx_abort_state').catch(() => {});
  results.push({ id: 'WALK', pass: false, detail: `aborted at ${failedAt}: ${err.message ?? err}` });
} finally {
  const passed = results.filter((r) => r.pass).length;
  console.log('\n════════ SUMMARY ════════');
  console.log(`${passed}/${results.length} test points passed`);
  if (consoleErrors.length) {
    console.log(`\nConsole/page errors captured (${consoleErrors.length}):`);
    for (const e of consoleErrors.slice(0, 20)) console.log(`  [${e.where}] ${e.text}`);
  } else {
    console.log('Console: no error-level messages captured');
  }
  writeFileSync(resolve(SHOT_DIR, 'walk_results.json'), JSON.stringify({ results, consoleErrors, email: EMAIL }, null, 2));
  await browser.close();
  process.exit(results.every((r) => r.pass) ? 0 : 1);
}
