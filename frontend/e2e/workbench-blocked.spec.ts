import { expect, test } from '@playwright/test';
import path from 'node:path';
import { installBlockedRailFixture } from './fixtures/blocked-rail.cjs';

test.use({ channel: process.env.WORKBENCH_BROWSER_CHANNEL });

const draftId = 'draft_blocked_layout';
const inquiry = 'A family with a five-year-old proposes Baga, Dudhsagar and Old Goa in one day';
const summary = 'Trip details are incomplete';
const capture = process.env.WORKBENCH_CAPTURE;

for (const width of [1440, 390]) {
  test(`blocked inquiry stays readable and repairable at ${width}px`, async ({ page, baseURL }) => {
    await page.setViewportSize({ width, height: 1000 });
    await page.addInitScript(() => localStorage.setItem('waypoint:welcome-seen:v1', '1'));
    await page.route('**/api/auth/me', (route) => route.fulfill({ json: {
      ok: true,
      user: { id: 'visual-user', name: 'Test Advisor', email: 'advisor@example.com' },
      agency: { id: 'visual-agency', name: 'Waypoint HQ', slug: 'waypoint-hq' },
      membership: { role: 'agency_admin', isPrimary: true },
    } }));
    if (baseURL === process.env.OVERVIEW_DEMO_URL) {
      await page.goto('/api/demo-session');
    } else {
      await page.context().addCookies([{ name: 'access_token', value: 'test-fixture', url: baseURL }]);
    }
    await page.route('**/api/triage/message', route => route.fulfill({ json: {} }));
    let blocked = false;
    await page.route(`**/api/drafts/${draftId}`, (route) => route.fulfill({ json: {
      draft_id: draftId, name: inquiry, customer_message: inquiry,
      version: blocked ? 2 : 1, status: blocked ? 'blocked' : 'open',
    } }));
    await page.route('**/api/spine/run', (route) => route.fulfill({ json: {
      run_id: 'run_blocked_layout', state: 'queued',
    } }));
    await page.route('**/api/runs/run_blocked_layout', (route) => {
      blocked = true;
      return route.fulfill({ json: {
        run_id: 'run_blocked_layout', state: 'blocked', trip_id: null, stage: 'discovery',
        steps_completed: ['packet'], events: [], validation: {
          status: 'ESCALATED', gate: 'NB01', reasons: ['Structural validation failed'],
        },
        block_reason: `${summary}. Please add the missing information and try again.`,
      } });
    });

    await page.goto(`/inquiries/new?draft=${draftId}&tab=intake`);
    const title = page.getByRole('heading', { name: inquiry, exact: true });
    await expect(title).toBeVisible();
    await page.getByRole('button', { name: 'Process inquiry' }).click();
    await expect(page.getByRole('button', { name: 'Open Trip Details', exact: true })).toBeVisible();
    await page.getByRole('tab', { name: 'Risk Review' }).click();
    await expect(page.getByRole('tab', { name: 'Risk Review' })).toHaveAttribute('aria-selected', 'true');

    if (capture) {
      await page.evaluate(() => document.fonts.ready);
      await page.screenshot({
        path: path.join(capture, `blocked-${width}.png`),
        fullPage: true,
        animations: 'disabled',
      });
    }

    expect(await title.evaluate((node) => node.getBoundingClientRect().width)).toBeGreaterThan(250);
    await expect(page.getByText('Trip Details Need Your Input', { exact: true })).toHaveCount(1);
    await expect(page.getByText(summary, { exact: true })).toHaveCount(1);
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
    const showDetails = page.getByRole('button', { name: 'Show run details' });
    await expect(showDetails).toHaveAttribute('aria-expanded', 'false');
    await showDetails.click();
    await expect(page.getByRole('button', { name: 'Hide run details' })).toHaveAttribute('aria-expanded', 'true');
    await expect(page.getByText(/^Run: run_bloc/)).toBeVisible();
    await page.getByRole('button', { name: 'Open Trip Details', exact: true }).click();
    await expect(page.getByRole('tab', { name: 'Trip Details' })).toHaveAttribute('aria-selected', 'true');
  });
}

test('rail Risk Review preserves feasibility and every intake question through resize', async ({ page }) => {
  const demo = process.env.OVERVIEW_DEMO_URL;
  test.skip(!demo, 'Requires the isolated authenticated demo.');
  await page.addInitScript(() => localStorage.setItem('waypoint:welcome-seen:v1', '1'));
  await page.goto(new URL('/api/demo-session', demo).href);
  const { rail, intakeQuestions, route } = await installBlockedRailFixture(page);
  await page.setViewportSize({ width: 1440, height: 970 });
  await page.goto(new URL(route, demo).href);
  await page.getByRole('button', { name: 'Process inquiry', exact: true }).click();
  await expect(page.getByText('Blocked', { exact: true }).first()).toBeVisible();
  const risk = page.getByRole('tab', { name: 'Risk Review' });
  await risk.click();
  const feasibility = page.getByRole('region', { name: 'Itinerary feasibility' });
  const questions = page.getByText('Additional intake questions', { exact: true }).locator('..').getByRole('listitem');
  for (const width of [1440, 1024, 854, 768, 640, 390, 320, 1440]) {
    await page.setViewportSize({ width, height: 970 });
    await expect(risk).toHaveAttribute('aria-selected', 'true');
    const tablist = page.getByRole('tablist');
    const hiddenTabs = await tablist.evaluate(el => {
      const bounds = el.getBoundingClientRect();
      return Array.from(el.querySelectorAll('[role="tab"]')).filter(tab => {
        const box = tab.getBoundingClientRect();
        return box.left < bounds.left - 1 || box.right > bounds.right + 1;
      }).map(tab => tab.textContent?.trim());
    });
    expect(hiddenTabs, 'Clipped Workbench tabs at ' + width + 'px').toEqual([]);
    await expect(feasibility.getByText(rail.packet.itinerary_feasibility_context, { exact: true })).toBeVisible();
    await expect(feasibility.getByText(rail.packet.itinerary_feasibility_question, { exact: true })).toBeVisible();
    await expect(questions).toHaveText(intakeQuestions.map(({ question }) => question));
    for (const question of await questions.all()) await expect(question).toBeVisible();
    expect(await page.locator('#main-content').evaluate(el => el.scrollWidth - el.clientWidth)).toBeLessThanOrEqual(2);
    if (capture && [320, 390, 768, 1440].includes(width)) {
      await feasibility.scrollIntoViewIfNeeded();
      await page.screenshot({ path: path.join(capture, 'rail-risk-' + width + '.png'), fullPage: true, animations: 'disabled' });
    }
  }
  const tripDetails = page.getByRole('tab', { name: 'Trip Details' });
  await tripDetails.click();
  await expect(tripDetails).toHaveAttribute('aria-selected', 'true');
});
