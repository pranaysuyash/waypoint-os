import { expect, test } from '@playwright/test';
import path from 'node:path';

const demo = process.env.OVERVIEW_DEMO_URL;
const capture = process.env.PLANNING_CAPTURE;
test.use({ channel: process.env.OVERVIEW_BROWSER_CHANNEL });
const reference = 'FIXTURE-' + '1234567890'.repeat(9);
const trip = {
  id: 'fixture-planning-reflow', destination: 'Kyoto', origin: 'London',
  budget: 'GBP 6000', dateWindow: '16 to 20 April 2027', party: 4, tripPurpose: 'Leisure',
  stage: 'proposal', status: 'assigned',
  strategy: { session_goal: 'Review the proposed transfer', suggested_opening: 'Proposed transfer ' + reference,
    priority_sequence: ['Confirm pickup'], assumptions: ['Supplier reference ' + reference] },
  internal_bundle: { user_message: 'Internal supplier reference ' + reference },
  traveler_bundle: { user_message: 'Your transfer reference is ' + reference,
    follow_up_sequence: [{ field_name: 'pickup', question: 'Where should we meet you?' }] },
};

for (const [stage, heading, content] of [
  ['strategy', 'Suggested Opening', 'Proposed transfer ' + reference],
  ['output', 'Outgoing Deliverables', 'Your transfer reference is ' + reference],
] as const) {
  test(stage + ' retains populated planning content during resize', async ({ page }) => {
    test.skip(!demo, 'Requires an isolated authenticated preview.');
    await page.addInitScript(() => localStorage.setItem('waypoint:welcome-seen:v1', '1'));
    await page.goto(new URL('/api/demo-session', demo).href);
    await page.route('**/api/trips/' + trip.id, route => route.fulfill({ json: trip }));
    await page.setViewportSize({ width: 320, height: 900 });
    await page.goto(new URL('/trips/' + trip.id + '/' + stage, demo).href);
    await expect(page.getByRole('heading', { name: heading })).toBeVisible();
    const text = page.getByText(content, { exact: stage === 'output' });
    await expect(text).toBeVisible();
    const clippedWidths: number[] = [];
    for (const width of [320, 390, 639, 768, 854, 1024, 1440, 1920, 320]) {
      await page.setViewportSize({ width, height: 900 });
      await expect(text).toBeVisible();
      const spill = await page.locator('#main-content').evaluate(el => el.scrollWidth - el.clientWidth);
      if (spill > 2 || await text.evaluate(el => el.scrollWidth - el.clientWidth > 2)) clippedWidths.push(width);
      if (stage === 'output') {
        await expect(page.getByText('Where should we meet you?')).toBeVisible();
        await expect(page.getByRole('button', { name: 'Copy Customer Draft' })).toBeVisible();
      } else {
        await expect(page.getByText('Confirm pickup')).toBeVisible();
        await expect(page.getByRole('heading', { name: 'Assumptions' })).toBeVisible();
      }
      if (capture && width === 320) {
        await text.scrollIntoViewIfNeeded();
        await page.screenshot({ path: path.join(capture, 'trip-' + stage + '-320.png'), animations: 'disabled' });
      }
    }
    expect(clippedWidths).toEqual([]);
  });
}
