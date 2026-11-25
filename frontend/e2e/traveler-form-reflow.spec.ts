import { expect, test } from '@playwright/test';
import path from 'node:path';

const demo = process.env.OVERVIEW_DEMO_URL;
const capture = process.env.TRAVELER_FORM_CAPTURE;
const widths = [320, 390, 639, 640, 767, 768, 854, 1024, 1280, 1440, 1920];
test.use({ channel: process.env.OVERVIEW_BROWSER_CHANNEL });

test('group deposit preserves payment instructions and traveler entries through resize', async ({ page }) => {
  test.skip(!demo, 'Requires an isolated local preview.');
  const endpoint = '**/api/v1/group/token/responsive-fixture';
  const reference = 'WAYPOINT-BOOKING-COLLECTION-2027-00012345';
  await page.route(endpoint, route => route.fulfill({ json: {
    ok: true, trip_id: 'synthetic-trip', destination: 'Kyoto and Osaka', passenger_id: 'synthetic-passenger',
    passenger_name: 'Fictional Traveler', deposit_share_cents: 125000, status: 'PENDING',
    agency_payment_url: 'https://example.test/fixture-payment',
    payment_instructions: 'Use this reference: ' + reference,
    schedule: [{ label: 'Initial deposit installment', amount_cents: 125000, status: 'pending' }],
  } }));
  let notification: unknown;
  await page.route(endpoint + '/pay-share', route => {
    notification = route.request().postDataJSON();
    return route.fulfill({ json: { ok: true } });
  });
  await page.setViewportSize({ width: 320, height: 900 });
  await page.goto(new URL('/g/responsive-fixture', demo).href);
  const dietary = page.getByPlaceholder('e.g. Vegetarian, Gluten-free, Nut allergy');
  await dietary.fill('Vegetarian');
  const failures: number[] = [];
  for (const width of widths) {
    await page.setViewportSize({ width, height: 900 });
    await expect(dietary).toHaveValue('Vegetarian');
    await expect(page.getByText(reference, { exact: false })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Pay Deposit Share via External Link' })).toHaveAttribute('href', 'https://example.test/fixture-payment');
    await expect(page.getByRole('button', { name: 'Notify Advisor & Save Preferences' })).toBeEnabled();
    if (await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1)) failures.push(width);
    if (capture && [320, 768, 1440].includes(width)) await page.screenshot({ path: path.join(capture, 'group-' + width + '.png'), fullPage: true, animations: 'disabled' });
  }
  expect(failures).toEqual([]);
  await page.setViewportSize({ width: 320, height: 900 });
  await expect(page.getByRole('textbox', { name: 'Dietary Requirements' })).toHaveValue('Vegetarian');
  await page.getByRole('button', { name: 'Notify Advisor & Save Preferences' }).click();
  await expect(page.getByText(/Advisor Notified!/)).toBeVisible();
  expect(notification).toMatchObject({ dietary_requirements: 'Vegetarian' });
});

test('booking collection loads and keeps editable fields usable through resize', async ({ page }) => {
  test.skip(!demo, 'Requires an isolated local preview.');
  const endpoint = '**/api/public/booking-collection/fixture-agency/responsive-fixture';
  await page.route(endpoint, route => route.fulfill({ json: {
    valid: true, agency_name: 'Fixture Agency',
    trip_summary: { destination: 'Kyoto and Osaka', date_window: 'November 2027', traveler_count: 1 },
  } }));
  await page.route(endpoint + '/**', route => route.abort('blockedbyclient'));
  let booking: unknown;
  await page.route(endpoint + '/submit', route => {
    booking = route.request().postDataJSON();
    return route.fulfill({ json: { ok: true, message: 'Synthetic receipt' } });
  });
  await page.setViewportSize({ width: 320, height: 900 });
  await page.goto(new URL('/booking-collection/fixture-agency/responsive-fixture', demo).href);
  const traveler = page.getByRole('textbox', { name: 'Full name *', exact: true });
  try {
    await expect(traveler).toBeVisible({ timeout: 8000 });
  } finally {
    if (capture) await page.screenshot({ path: path.join(capture, 'collection-load-320.png'), fullPage: true, animations: 'disabled' });
  }
  await traveler.fill('Fictional Traveler');
  await page.getByLabel('Traveler name or reference *', { exact: true }).fill('Traveler A');
  await page.getByLabel('Date of birth *', { exact: true }).fill('1990-01-01');
  for (const width of widths) {
    await page.setViewportSize({ width, height: 900 });
    await expect(traveler).toHaveValue('Fictional Traveler');
    await expect(page.getByRole('button', { name: 'Submit Booking Details' })).toBeVisible();
    const box = await traveler.boundingBox();
    expect(box!.width).toBeGreaterThanOrEqual(150);
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width + 1);
    if (capture && [320, 768, 1440].includes(width)) await page.screenshot({ path: path.join(capture, 'collection-' + width + '.png'), fullPage: true, animations: 'disabled' });
  }
  await page.setViewportSize({ width: 320, height: 900 });
  await page.getByRole('button', { name: 'Submit Booking Details' }).click();
  await expect(page.getByTestId('collection-success')).toBeVisible();
  expect(booking).toMatchObject({
    booking_data: {
      travelers: [{ traveler_id: 'Traveler A', full_name: 'Fictional Traveler', date_of_birth: '1990-01-01' }],
    },
  });
});

test('traveler questions and entered answers survive resize', async ({ page }) => {
  test.skip(!demo, 'Requires an isolated local preview.');
  const endpoint = '**/api/public/asks/responsive-fixture';
  const question = 'Which arrival station will you use for the morning transfer?';
  await page.route(endpoint, route => route.fulfill({ json: {
    token: 'responsive-fixture', trip_id: 'synthetic-trip', destination: 'Kyoto and Osaka',
    status: 'open', questions: [{ field_name: 'arrival_station', question, priority: 'high' }], asked_count: 1,
  } }));
  let response: unknown;
  await page.route(endpoint + '/answers', route => {
    response = route.request().postDataJSON();
    return route.fulfill({ json: { ok: true } });
  });
  await page.setViewportSize({ width: 320, height: 900 });
  await page.goto(new URL('/a/responsive-fixture', demo).href);
  const answer = page.getByRole('textbox', { name: question });
  await answer.fill('Kyoto Station');
  for (const width of widths) {
    await page.setViewportSize({ width, height: 900 });
    await expect(answer).toHaveValue('Kyoto Station');
    await expect(page.getByRole('button', { name: 'Send answers' })).toBeEnabled();
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width + 1);
  }
  await page.setViewportSize({ width: 320, height: 900 });
  await page.getByRole('button', { name: 'Send answers' }).click();
  await expect(page.getByRole('heading', { name: 'Thank you!' })).toBeVisible();
  expect(response).toMatchObject({ answers: [{ field_name: 'arrival_station', answer: 'Kyoto Station' }] });
});
