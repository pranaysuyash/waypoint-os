const { chromium } = require('playwright');
const { expect } = require('@playwright/test');
const path = require('node:path');
const fixture = require('./fixture.json');
const intakeQuestions = [
  { field_name: 'origin_city', question: 'Which city will you be departing from?' },
  { field_name: 'date_window', question: 'When are you planning to travel? Are the dates fixed or flexible?' },
  { field_name: 'party_size', question: 'How many people will be traveling?' },
  { field_name: 'budget', question: "What's your approximate budget for this trip?" },
  { field_name: 'trip_purpose', question: "What's the main purpose of this trip? (leisure, business, pilgrimage, etc.)" },
];
const previousCopy = process.env.RAIL_CAPTURE_PREVIOUS_COPY === '1';
const packet = {
  ...fixture.packet,
  itinerary_feasibility_context: previousCopy
    ? 'Overnight train · Confirmed status reported · Separate morning transfer'
    : fixture.packet.itinerary_feasibility_context,
};

async function capture() {
  const browser = await chromium.launch({ channel: 'chrome' });
  try {
    for (const width of [1440, 390]) {
      const page = await browser.newPage({ viewport: { width, height: 970 } });
      const base = 'http://localhost:3005';
      const draft = 'draft_rail_visual';
      let blocked = false;
      await page.context().addCookies([{ name: 'access_token', value: 'test-fixture', url: base }]);
      await page.addInitScript(() => localStorage.setItem('waypoint:welcome-seen:v1', '1'));
      await page.route('**/api/auth/me', (route) => route.fulfill({ json: {
        ok: true,
        user: { id: 'visual-user', name: 'Test Advisor', email: 'advisor@example.com' },
        agency: { id: 'visual-agency', name: 'Waypoint HQ', slug: 'waypoint-hq' },
        membership: { role: 'agency_admin', isPrimary: true },
      } }));
      await page.route('**/api/drafts/' + draft, (route) => route.fulfill({ json: {
        draft_id: draft, name: 'An overnight train is waitlisted in the traveler’s note. …',
        customer_message: fixture.note + ' Correction from the traveler or operator: ' + fixture.update,
        version: blocked ? 2 : 1, status: blocked ? 'blocked' : 'open',
      } }));
      await page.route('**/api/spine/run', (route) => route.fulfill({ json: {
        run_id: 'run_rail_visual', state: 'queued',
      } }));
      await page.route('**/api/runs/run_rail_visual', (route) => {
        blocked = true;
        return route.fulfill({ json: {
          run_id: 'run_rail_visual', state: 'blocked', trip_id: null, stage: 'discovery',
          validation: { status: 'ESCALATED', gate: 'NB01', reasons: ['Structural validation failed'] },
          block_reason: 'Trip details are incomplete',
          packet, decision_state: 'STOP_NEEDS_REVIEW', follow_up_questions: intakeQuestions,
          hard_blockers: ['extraction_quality'], steps_completed: ['packet'], events: [],
        } });
      });
      const response = await page.goto(base + '/inquiries/new?draft=' + draft + '&tab=intake');
      expect(response.ok()).toBe(true);
      await expect(page.getByRole('heading', { name: /overnight train is waitlisted/i })).toBeVisible();
      await page.getByRole('button', { name: 'Process inquiry', exact: true }).click();
      const tripDetails = page.getByRole('tab', { name: 'Trip Details' });
      await expect(page.getByText('Blocked', { exact: true }).first()).toBeVisible({ timeout: 15000 });
      await expect(tripDetails).toBeVisible();
      await page.getByRole('tab', { name: 'Risk Review' }).click();
      const evidence = page.getByRole('region', { name: 'Itinerary feasibility' });
      await expect(evidence.getByText(packet.itinerary_feasibility_context, { exact: true })).toBeVisible();
      await expect(evidence.getByText(fixture.packet.itinerary_feasibility_question, { exact: true })).toBeVisible();
      const intakeList = page.getByText('Additional intake questions', { exact: true }).locator('..').getByRole('listitem');
      await expect(intakeList).toHaveText(intakeQuestions.map(({ question }) => question));
      await expect(page.getByText('Confidence unavailable', { exact: true })).toBeVisible();
      await expect(page.getByText(/draft below before sending/i)).toHaveCount(0);
      expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
      const captureName = previousCopy ? 'previous-copy' : 'after';
      await page.screenshot({ path: path.join(__dirname, captureName + '-' + width + '.png'), animations: 'disabled', fullPage: true });
      await tripDetails.click();
      await expect(tripDetails).toHaveAttribute('aria-selected', 'true');
      await page.close();
      console.log(width + 'px Risk Review and Trip Details passed');
    }
  } finally {
    await browser.close();
  }
}

capture().catch((error) => { console.error(error); process.exitCode = 1; });
