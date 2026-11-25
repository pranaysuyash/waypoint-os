import { expect, test } from '@playwright/test';
import path from 'node:path';

const demo = process.env.OVERVIEW_DEMO_URL;
const capture = process.env.PAYMENTS_CAPTURE;
test.use({ channel: process.env.OVERVIEW_BROWSER_CHANNEL });

test('populated payment table scrolls locally and keeps filters and workspace links usable', async ({ page, browserName }) => {
  test.skip(!demo, 'Requires an isolated local preview.');
  await page.addInitScript(() => localStorage.setItem('waypoint:welcome-seen:v1', '1'));
  await page.goto(new URL('/api/demo-session', demo).href);
  await page.route(/\/api\/payments(?:\?|$)/, route => route.fulfill({ json: {
    summary: { total: 1, by_queue_status: { overdue: 1 }, overdue_count: 1, due_soon_count: 0,
      not_configured_count: 0, paid_complete_count: 0, refund_in_progress_count: 0,
      due_within_7_days_count: 0 },
    pagination: { limit: 25, offset: 0, returned: 1, total: 1, has_more: false },
    items: [{ trip_id: 'fixture-payment-trip', trip_name: 'Kyoto Family Journey', destination: 'Japan',
      status: 'assigned', queue_status: 'overdue', payment_status: 'partially_paid',
      refund_status: 'not_applicable', agreed_amount: 4200, amount_paid: 1200, balance_due: 3000,
      currency: 'USD', final_payment_due: '2026-11-15',
      payment_reference_present: true, payment_proof_url_present: true, refund_paid_by_agency: false }],
  } }));
  await page.setViewportSize({ width: 320, height: 900 });
  await page.goto(new URL('/payments', demo).href);
  const table = page.getByRole('table').filter({ hasText: 'Kyoto Family Journey' });
  await expect(table).toBeVisible();
  const search = page.getByRole('searchbox', { name: 'Search payments by trip name, destination, or reference' });
  await search.fill('Kyoto');
  await expect(page).toHaveURL(/q=Kyoto/);
  for (const width of [320, 390, 639, 640, 767, 768, 854, 1024, 1280, 1440, 1920]) {
    await page.setViewportSize({ width, height: 900 });
    await expect(search).toHaveValue('Kyoto');
    await expect(table.getByRole('columnheader')).toHaveCount(9);
    await expect(table.getByText('Proof attached')).toBeVisible();
    await expect(table.getByText('$3,000.00', { exact: true })).toBeVisible();
    await expect(table.getByRole('link', { name: 'Open trip' })).toHaveAttribute('href', '/trips/fixture-payment-trip/ops');
    expect(await page.locator('#main-content').evaluate(el => el.scrollWidth - el.clientWidth)).toBeLessThanOrEqual(2);
    if (capture && [320, 768, 1440].includes(width)) {
      await page.getByRole('columnheader', { name: 'Trip', exact: true }).scrollIntoViewIfNeeded();
      await page.screenshot({ path: path.join(capture, 'payments-' + width + '.png'), animations: 'disabled' });
    }
  }
  await page.setViewportSize({ width: 320, height: 900 });
  const scroller = page.getByRole('region', { name: 'Payment queue table' });
  await scroller.focus({ timeout: 3000 });
  await expect(scroller).toBeFocused();
  expect(await scroller.evaluate(el => el.scrollWidth > el.clientWidth)).toBe(true);
  await page.keyboard.press('ArrowRight');
  await expect.poll(() => scroller.evaluate(el => el.scrollLeft)).toBeGreaterThan(0);
  await page.keyboard.press(browserName === 'webkit' ? 'Alt+Tab' : 'Tab');
  await expect(table.getByRole('link', { name: 'Open trip' })).toBeFocused();
  await expect(table.getByRole('link', { name: 'Open trip' })).toBeInViewport();
  const link = table.getByRole('link', { name: 'Open trip' });
  const keyWasAllowed = await link.evaluate(el => el.dispatchEvent(new KeyboardEvent('keydown', {
    key: 'ArrowLeft', bubbles: true, cancelable: true,
  })));
  expect(keyWasAllowed).toBe(true);
  await expect(link).toBeFocused();
  if (capture) {
    await page.screenshot({ path: path.join(capture, 'payments-320-workspace-focus.png'), animations: 'disabled' });
  }
});
