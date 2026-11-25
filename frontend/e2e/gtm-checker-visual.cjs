// Run against an already-running local Next.js server. All checker calls use synthetic responses.
const { chromium, expect } = require('@playwright/test');
const { mkdir, rename } = require('node:fs/promises');
const path = require('node:path');

const evidence = process.env.GTM_CHECKER_EVIDENCE || path.resolve(__dirname, '../../Docs/evidence/gtm-checker-2026-11-21');
const baseUrl = process.env.GTM_CHECKER_BASE_URL || 'http://127.0.0.1:3005';
const note = 'London to Rome via Paris, 50 minute transfer on separate tickets.';
const finding = 'Confirm baggage transfer with the airline before booking the 50-minute connection.';
const report = {
  run_id: 'fixture-run',
  trip_id: 'fixture-trip',
  access_token: 'fixture-report-token',
  state: 'completed',
  decision_state: 'STOP_NEEDS_REVIEW',
  hard_blockers: [finding],
  soft_blockers: [],
  follow_up_questions: [{ question: 'Are your bags checked through to Rome?' }],
  packet: {
    facts: {
      destination: { value: 'Rome' },
    },
    public_checker_live_checks: {
      destination: 'Rome',
      hard_blockers: [finding],
    },
  },
};

async function capture(browser, name, viewport) {
  const context = await browser.newContext({
    viewport,
    isMobile: name === 'mobile',
    hasTouch: name === 'mobile',
    reducedMotion: 'reduce',
    recordVideo: { dir: evidence, size: viewport },
  });
  try {
    const page = await context.newPage();
    const video = page.video();
    let nextResponse = { status: 503, json: { detail: 'Fixture unavailable' } };
    let posts = 0;
    let expectedNote = note;
    const events = [];
    let agencyAvailable = false;
    await page.addInitScript(() => {
      Object.defineProperty(navigator, 'share', { value: () => Promise.reject(new DOMException('Cancelled', 'AbortError')) });
    });
    await page.route('**/api/public-checker/**', async (route) => {
      const pathname = new URL(route.request().url()).pathname;
      if (pathname.endsWith('/run')) {
        expect(route.request().postDataJSON().raw_note).toBe(expectedNote);
        posts += 1;
        return route.fulfill(nextResponse);
      }
      if (pathname.endsWith('/events')) {
        events.push(route.request().postDataJSON().event_name);
      }
      if (pathname.includes('/trip/')) {
        expect(route.request().headers().authorization).toBe('Bearer fixture-report-token');
        return route.fulfill({ json: { ok: true, report: {} } });
      }
      if (pathname.endsWith('/matches')) {
        return route.fulfill({ json: { matches: agencyAvailable ? [
          { agency_id: 'fixture-agency', display_name: 'Sample Advisor Agency', match_reasons: ['Covers Rome'] },
        ] : [] } });
      }
      if (pathname.endsWith('/route-request')) {
        expect(route.request().postDataJSON()).toMatchObject({ agency_id: 'fixture-agency', consent: true });
        return route.fulfill({ json: { ok: true, lead_id: 'fixture-lead', status: 'routed' } });
      }
      return route.fulfill({ json: { ok: true } });
    });
    await page.goto(baseUrl + '/itinerary-checker');
    const draft = page.getByRole('textbox', { name: 'Your itinerary' });
    const submit = page.getByRole('button', { name: 'Check my itinerary', exact: true }).first();
    const screenshot = (state) => page.screenshot({ path: path.join(evidence, name + '-' + state + '.png') });
    await draft.fill(note);
    await screenshot('after-intake');
    await page.waitForTimeout(2200);
    await submit.click();
    await expect(page.getByRole('alert').filter({ hasText: 'Itinerary check unavailable' })).toContainText('Itinerary check unavailable');
    await expect(draft).toHaveValue(note);
    await expect(page.getByText('Checked against live sources', { exact: false })).toHaveCount(0);
    await expect(page.getByText('Share findings summary', { exact: true })).toHaveCount(0);
    await expect(page.getByRole('alert').filter({ hasText: 'Itinerary check unavailable' })).toBeInViewport();
    await screenshot('after-failure');
    await page.waitForTimeout(2600);

    nextResponse = { json: { run_id: 'broken', state: 'completed', packet: {} } };
    await submit.click();
    await expect.poll(() => posts).toBe(2);
    await expect(page.getByRole('alert').filter({ hasText: 'Itinerary check unavailable' })).toContainText('Itinerary check unavailable');
    await expect(draft).toHaveValue(note);

    nextResponse = { json: report };
    await submit.click();
    const heading = page.getByRole('heading', { name: 'Review these findings before booking' });
    await expect(heading).toBeFocused();
    await expect(page.getByText(finding, { exact: true }).first()).toBeInViewport();
    await expect(page.getByText('$640', { exact: false })).toHaveCount(0);
    await expect(page.getByText('/100', { exact: false })).toHaveCount(0);
    for (const width of [320, 390, 639, 640, 767, 768, 854, 1024, 1440, viewport.width]) {
      await page.setViewportSize({ width, height: viewport.height });
      await expect(heading).toBeVisible();
      await expect(page.getByText(finding, { exact: true }).first()).toBeVisible();
      expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width + 1);
    }
    await screenshot('after-report');
    await page.waitForTimeout(2800);

    await page.getByRole('button', { name: 'Check advisor availability' }).click();
    await expect(page.getByText('No matching advisor is available', { exact: false })).toBeVisible();
    await expect(page.getByRole('textbox', { name: 'Email or phone' })).toHaveCount(0);
    await screenshot('after-no-match');
    await page.getByText('Share findings summary', { exact: true }).click();
    await expect(page.getByText('Waypoint itinerary findings', { exact: false })).toBeVisible();
    await screenshot('after-share-preview');
    await page.getByRole('button', { name: 'Share this summary' }).click();
    await page.waitForTimeout(2600);
    expect(events).not.toContain('action_packet_shared');
    const download = page.waitForEvent('download');
    await page.getByRole('button', { name: 'Download my saved report' }).click();
    expect((await download).suggestedFilename()).toBe('waypoint-checker-fixture-trip.json');
    expect(events).not.toContain('finding_evidence_opened');

    await page.getByRole('button', { name: /edit itinerary/i }).click();
    await expect(draft).toHaveValue(note);
    nextResponse = { json: { ...report, state: 'blocked', decision_state: 'ASK_FOLLOWUP', hard_blockers: [], packet: { facts: {}, unknowns: [{ field_name: 'date_window' }] } } };
    await submit.click();
    await expect(page.getByRole('heading', { name: 'Your check needs more details' })).toBeFocused();
    await expect(page.getByText('No issues were flagged', { exact: false })).toHaveCount(0);
    await screenshot('after-partial');
    await page.waitForTimeout(2800);

    await expect(page.getByRole('heading', { name: 'Your check needs more details' })).toBeInViewport();
    await expect(page.getByText('Add travel dates.', { exact: true }).first()).toBeInViewport();
    await page.getByRole('button', { name: 'Correct or add trip details' }).click();
    const editor = page.getByRole('textbox', { name: 'Your submitted itinerary' });
    await expect(editor).toBeFocused();
    await expect(editor).toHaveValue(note);
    const recheck = page.getByRole('button', { name: 'Recheck my itinerary' });
    await expect(recheck).toBeDisabled();
    expectedNote = note + ' Traveling November 27–30, 2026.';
    await editor.fill(expectedNote);
    nextResponse = { status: 503, json: { detail: 'Fixture unavailable' } };
    await recheck.click();
    await expect(page.getByText('The report below is from your previous check.', { exact: false })).toBeVisible();
    await expect(editor).toHaveValue(expectedNote);
    await screenshot('after-recheck-retry');
    await page.waitForTimeout(1400);
    nextResponse = { json: { ...report, run_id: 'fixture-revised', decision_state: 'PROCEED_TRAVELER_SAFE', hard_blockers: [], follow_up_questions: [],
      packet: { facts: { date_window: { value: 'November 27–30, 2026' } } } } };
    await recheck.click();
    await expect(page.getByRole('heading', { name: 'Your itinerary check' })).toBeFocused();
    await expect(page.getByRole('term').filter({ hasText: 'Travel window' })).toBeInViewport();
    await expect(page.getByRole('textbox', { name: 'Your submitted itinerary' })).toHaveCount(0);
    await screenshot('after-recheck');
    await page.waitForTimeout(2000);
    expectedNote = note;

    await page.getByRole('button', { name: /check another itinerary/i }).click();
    await draft.fill(note);
    nextResponse = { json: { ...report, decision_state: 'PROCEED_TRAVELER_SAFE', hard_blockers: [], follow_up_questions: [], packet: { facts: {}, public_checker_entity_checks: [{ name: 'Fixture Hotel', status: 'verified', message: 'Fixture Hotel appears in the property listing.' }] } } };
    await submit.click();
    await expect(page.getByRole('heading', { name: 'Findings to review' })).toBeVisible();
    await expect(page.getByText('Fixture Hotel appears in the property listing.')).toBeVisible();
    await expect(page.getByText('$640', { exact: false })).toHaveCount(0);
    await screenshot('after-advisory-only');
    await page.waitForTimeout(2800);

    agencyAvailable = true;
    await page.getByRole('button', { name: 'Check advisor availability' }).click();
    await page.getByRole('button', { name: /Sample Advisor Agency/ }).click();
    await page.getByRole('textbox', { name: 'Email or phone' }).fill('traveler@example.test');
    const requestAdvisor = page.getByRole('button', { name: 'Request advisor follow-up' });
    await expect(requestAdvisor).toBeDisabled();
    await page.getByRole('checkbox', { name: /Send my brief and contact to Sample Advisor Agency/ }).check();
    await screenshot('after-advisor-consent');
    await page.waitForTimeout(2800);
    await requestAdvisor.click();
    await expect(page.getByText('Request recorded for the selected agency. Delivery has not been confirmed.')).toBeVisible();
    await screenshot('after-advisor-receipt');
    await page.waitForTimeout(2800);
    await context.close();
    await rename(await video.path(), path.join(evidence, name + '-walkthrough.webm'));
    console.log(name + ': failed and malformed reports, retry, findings, no match, partial, advisory-only, and advisor receipt verified');
  } finally {
    await context.close();
  }
}

(async () => {
  await mkdir(evidence, { recursive: true });
  const executablePath = process.env.GTM_CHECKER_BROWSER;
  const browser = await chromium.launch({ executablePath, channel: process.env.GTM_CHECKER_CHANNEL });
  try {
    await Promise.all([
      capture(browser, 'desktop', { width: 1440, height: 900 }),
      capture(browser, 'mobile', { width: 390, height: 844 }),
      capture(browser, 'tablet', { width: 768, height: 1024 }),
    ]);
  } finally {
    await browser.close();
  }
})().catch((error) => { console.error(error); process.exitCode = 1; });
