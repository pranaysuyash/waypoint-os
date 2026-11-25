import { expect, test } from '@playwright/test';
import path from 'node:path';

const demo = process.env.OVERVIEW_DEMO_URL;
const capture = process.env.BOOKINGS_CAPTURE;
test.use({ channel: process.env.OVERVIEW_BROWSER_CHANNEL });

test('populated booking dossier keeps collection and traveler details available on resize', async ({ page }) => {
  test.skip(!demo, 'Requires an isolated local preview.');
  await page.addInitScript(() => localStorage.setItem('waypoint:welcome-seen:v1', '1'));
  await page.goto(new URL('/api/demo-session', demo).href);
  const trip = { id: 'fixture-booking', destination: 'Kyoto and Osaka', type: 'family', origin: 'London', stage: 'booking' };
  const endpoint = '**/api/trips/' + trip.id;
  await page.route(/\/api\/trips(?:\?|$)/, route => route.fulfill({ json: { items: [trip], total: 1 } }));
  await page.route(endpoint, route => route.fulfill({ json: trip }));
  await page.route(endpoint + '/booking-data', route => route.fulfill({ json: {
    trip_id: trip.id, stage: 'booking', readiness: {},
    booking_data: {
      travelers: [{ traveler_id: 'synthetic-traveler', full_name: 'Fictional Traveler', date_of_birth: '1990-01-01', passport_number: 'SYNTHETIC123', passport_expiry: '2032-01-01', nationality: 'British' }],
      payment_tracking: { agreed_amount: 4200, currency: 'USD', amount_paid: 1200, balance_due: 3000, payment_status: 'partially_paid' },
    },
  } }));
  await page.route(endpoint + '/pending-booking-data', route => route.fulfill({ json: {
    trip_id: trip.id, pending_booking_data: { travelers: [{ traveler_id: 'fixture-pending', full_name: 'Pending Traveler', date_of_birth: '1990-01-01' }] },
  } }));
  await page.route(endpoint + '/collection-link', route => route.request().method() === 'GET' ? route.fulfill({ json: {
    has_active_token: true, has_pending_submission: true, token_id: 'fixture-token',
    collection_url: 'https://example.test/booking-collection/fixture-agency/fixture-token-long-reference',
    expires_at: '2026-12-01T00:00:00Z', status: 'active',
  } }) : route.abort('blockedbyclient'));
  await page.setViewportSize({ width: 320, height: 900 });
  await page.goto(new URL('/bookings?tripId=' + trip.id, demo).href);
  const table = page.getByRole('table').filter({ hasText: 'Fictional Traveler' });
  await expect(table).toBeVisible();
  const spills: string[] = [];
  for (const width of [320, 390, 639, 640, 767, 768, 854, 1024, 1280, 1440, 1920]) {
    await page.setViewportSize({ width, height: 900 });
    await expect(table.getByRole('columnheader')).toHaveCount(5);
    await expect(table.getByText('SYNTHETIC123')).toBeVisible();
    await expect(page.getByTestId('pending-submission')).toContainText('Pending Traveler');
    await expect(page.getByTestId('collection-url')).toContainText('fixture-token-long-reference');
    await expect(page.getByRole('button', { name: 'Revoke', exact: true })).toBeEnabled();
    await expect(page.getByRole('button', { name: 'Accept into dossier' })).toBeEnabled();
    await expect(page.getByRole('button', { name: 'Reject', exact: true })).toBeEnabled();
    const overflow = await page.locator('#main-content').evaluate(el => el.scrollWidth - el.clientWidth);
    if (overflow > 2) spills.push(width + 'px: ' + overflow);
    if (capture && [320, 768, 1440].includes(width)) {
      await page.screenshot({ path: path.join(capture, 'bookings-' + width + '.png'), animations: 'disabled' });
    }
  }
  expect(spills).toEqual([]);
  await page.setViewportSize({ width: 320, height: 900 });
  const scroller = page.getByRole('region', { name: 'Traveler details table' });
  await scroller.focus();
  await expect(scroller).toBeFocused();
  await page.keyboard.press('ArrowRight');
  await expect.poll(() => scroller.evaluate(el => el.scrollLeft)).toBeGreaterThan(0);
});
