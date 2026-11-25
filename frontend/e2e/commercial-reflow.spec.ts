import { expect, test } from '@playwright/test';
import path from 'node:path';

const demo = process.env.OVERVIEW_DEMO_URL;
const capture = process.env.COMMERCIAL_CAPTURE;
const widths = [320, 390, 639, 640, 767, 768, 854, 1024, 1280, 1440, 1920];
const tripId = 'trip-responsive-fixture';
const title = 'Kyoto and Osaka Multi-Generational Family Journey';
const option = {
  id: 'transfer', category: 'Ground transportation', name: 'Private airport transfer',
  description: 'Dedicated transport for the traveling party and their luggage.',
  price_delta_usd: 520, selected: false, is_default: false,
};
const proposal = {
  token: 'responsive-fixture', title, destination: 'Japan',
  duration_days: 7, traveler_name: 'Fictional Family',
  base_price_usd: 4100, selected_total_price_usd: 4100, currency: 'USD',
  status: 'sent', days: [{ day_number: 1, title: 'Arrive in Kyoto', location: 'Kyoto',
    description: 'Meet your guide at the hotel.', highlights: ['Private welcome briefing'], options: [] }],
  available_options: [option],
};
test.use({ channel: process.env.OVERVIEW_BROWSER_CHANNEL });

test('traveler proposal keeps pricing, add-on selection and acceptance controls reachable', async ({ page }) => {
  test.skip(!demo, 'Requires an isolated local preview.');
  let selection: string[] = [];
  const endpoint = '**/api/public/proposals/responsive-fixture';
  await page.route(endpoint, route => route.fulfill({ json: proposal }));
  await page.route(endpoint + '/calculate', route => {
    selection = route.request().postDataJSON().selected_option_ids;
    return route.fulfill({ json: { ...proposal, selected_total_price_usd: selection.length ? 4620 : 4100 } });
  });
  await page.route(endpoint + '/accept', route => route.abort('blockedbyclient'));
  await page.goto(new URL('/p/responsive-fixture', demo).href);
  const range = page.getByText(option.name, { exact: true });
  await expect(range).toBeVisible();
  const spills: string[] = [];
  for (const width of widths) {
    await page.setViewportSize({ width, height: 900 });
    await expect(page.getByText('Total Package', { exact: true })).toBeVisible();
    await expect(page.getByText('Private welcome briefing')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Confirm & E-Sign Proposal' })).toBeDisabled();
    const scrollWidth = await page.evaluate(() => document.documentElement.scrollWidth);
    if (scrollWidth > width + 1) spills.push(width + 'px: ' + scrollWidth);
    if (capture && [320, 768, 1440].includes(width)) {
      await page.screenshot({ path: path.join(capture, 'proposal-' + width + '.png'), fullPage: true, animations: 'disabled' });
    }
  }
  expect(spills).toEqual([]);
  await page.setViewportSize({ width: 320, height: 900 });
  const addon = page.getByRole('button', { name: /Private airport transfer/ });
  await addon.focus({ timeout: 2500 });
  await addon.press('Enter');
  await expect.poll(() => selection).toEqual(['transfer']);
  await expect(addon).toHaveAttribute('aria-pressed', 'true');
  await expect(page.getByText('$4,620', { exact: true }).first()).toBeVisible();
  const name = page.getByRole('textbox', { name: 'Full Legal Name' });
  const email = page.getByRole('textbox', { name: 'Email Address' });
  await name.fill('Synthetic Traveler');
  await email.fill('traveler@example.test');
  await page.setViewportSize({ width: 854, height: 900 });
  await expect(addon).toHaveAttribute('aria-pressed', 'true');
  await expect(name).toHaveValue('Synthetic Traveler');
  await expect(email).toHaveValue('traveler@example.test');
  await expect(page.getByRole('button', { name: 'Confirm & E-Sign Proposal' })).toBeDisabled();
});

test('populated Quotes keeps amounts, provenance and links visible at all widths', async ({ page }) => {
  test.skip(!demo, 'Requires an isolated local preview.');
  await page.addInitScript(() => localStorage.setItem('waypoint:welcome-seen:v1', '1'));
  await page.goto(new URL('/api/demo-session', demo).href);
  await page.route(/\/api\/trips(?:\?|$)/, route => route.fulfill({ json: { items: [
    { id: tripId, destination: 'Kyoto and Osaka', origin: 'London', type: 'family', party: 6, dateWindow: 'November 2027' },
  ], total: 1 } }));
  await page.route('**/api/v1/trips/' + tripId + '/quotes', route => route.fulfill({ json: {
    trip_id: tripId, quote_ready: true, branches: [{ label: 'Alternative hotel', priced: false }], missing: [],
    quotes: [{ trip_id: tripId, title, currency: 'USD', net_cost: 4200, net_cost_basis: 'persisted_modeled_cost',
      margin_percent: 18.42, margin_basis: 'policy_preview', margin_provenance: { applied_rule_id: 'fixture_policy' },
      tax_percent: null, rack_price: 4938, rack_price_basis: 'computed_preview', status: 'approved',
      updated_at: '2026-11-20T12:00:00Z', highlights: ['Boutique hotel'], summary: 'Example commercial quote.' }],
  } }));
  await page.goto(new URL('/quotes?tripId=' + tripId, demo).href);
  await expect(page.getByTestId('quote-title')).toHaveText(title);
  for (const width of widths) {
    await page.setViewportSize({ width, height: 900 });
    await expect(page.getByTestId('quote-rack-price')).toHaveText('$4,938');
    await expect(page.getByTestId('quote-net-cost')).toHaveText('$4,200');
    await expect(page.getByText('fixture_policy')).toBeVisible();
    await expect(page.getByRole('link', { name: 'Quote Review Queue' })).toHaveAttribute('href', '/reviews');
    await expect(page.getByRole('link', { name: 'Generate Output Artifacts' })).toHaveAttribute('href', '/trips/' + tripId + '/output');
    expect(await page.locator('#main-content').evaluate(el => el.scrollWidth - el.clientWidth)).toBeLessThanOrEqual(2);
    if (capture && [320, 768, 1440].includes(width)) {
      await page.screenshot({ path: path.join(capture, 'quotes-' + width + '.png'), fullPage: true, animations: 'disabled' });
    }
  }
});

test('native-currency add-on and consent agree with the recalculated proposal total', async ({ page }) => {
  test.skip(!demo, 'Requires an isolated local preview.');
  const native = {
    ...proposal, currency: 'INR',
    base_price_usd: 125000, selected_total_price_usd: 125000, selected_total_price: 125000,
    available_options: [{ ...option, price_delta_usd: 5200 }],
  };
  const endpoint = '**/api/public/proposals/responsive-fixture';
  await page.route(endpoint, route => route.fulfill({ json: native }));
  await page.route(endpoint + '/calculate', route => route.fulfill({ json: {
    ...native, selected_total_price_usd: 130200, selected_total_price: 130200,
  } }));
  await page.route(endpoint + '/accept', route => route.abort('blockedbyclient'));
  await page.setViewportSize({ width: 320, height: 900 });
  await page.goto(new URL('/p/responsive-fixture', demo).href);
  const addon = page.getByRole('button', { name: /Private airport transfer/ });
  await addon.click();
  await expect(page.getByText('₹1,30,200', { exact: true }).first()).toBeVisible();
  if (capture) {
    await page.screenshot({ path: path.join(capture, 'proposal-customize-320.png'), fullPage: true, animations: 'disabled' });
  }
  for (const width of [320, 768, 1440]) {
    await page.setViewportSize({ width, height: 900 });
    await expect(addon).toContainText('+₹5,200');
    if (width === 320) {
      const heading = await page.getByRole('heading', { name: 'Customize Your Experience' }).boundingBox();
      const instructions = await page.getByText('Select options to update your price in real-time').boundingBox();
      expect(instructions!.y).toBeGreaterThanOrEqual(heading!.y + heading!.height);
    }
    await expect(page.getByRole('checkbox')).toHaveAccessibleName(/₹1,30,200/);
    await expect(page.getByRole('button', { name: 'Confirm & E-Sign Proposal' })).toBeDisabled();
  }
});

test('proposal waits for confirmed pricing and renewed consent after an add-on change', async ({ page }) => {
  test.skip(!demo, 'Requires an isolated local preview.');
  let release!: () => void;
  const pending = new Promise<void>(resolve => { release = resolve; });
  const endpoint = '**/api/public/proposals/responsive-fixture';
  await page.route(endpoint, route => route.fulfill({ json: proposal }));
  await page.route(endpoint + '/accept', route => route.abort('blockedbyclient'));
  await page.route(endpoint + '/calculate', async route => {
    await pending;
    await route.fulfill({ json: { ...proposal, selected_total_price_usd: 4620 } });
  });
  await page.setViewportSize({ width: 320, height: 900 });
  await page.goto(new URL('/p/responsive-fixture', demo).href);
  const consent = page.getByRole('checkbox');
  const sign = page.getByRole('button', { name: 'Confirm & E-Sign Proposal' });
  await page.getByRole('textbox', { name: 'Full Legal Name' }).fill('Fictional Traveler');
  await page.getByRole('textbox', { name: 'Email Address' }).fill('traveler@example.test');
  await consent.check();
  await expect(sign).toBeEnabled();
  const addon = page.getByRole('button', { name: /Private airport transfer/ });
  await addon.click();
  try {
    if (capture) {
      await sign.scrollIntoViewIfNeeded();
      await page.screenshot({ path: path.join(capture, 'proposal-pending-320.png'), animations: 'disabled' });
    }
    await expect(sign).toBeDisabled({ timeout: 1500 });
    await expect(addon).toBeDisabled();
    await expect(consent).not.toBeChecked();
  } finally {
    release();
  }
  await expect(consent).toHaveAccessibleName(/\$4,620/);
  await expect(addon).toBeEnabled();
  await expect(sign).toBeDisabled();
  await consent.check();
  await expect(sign).toBeEnabled();

  await page.route(endpoint + '/calculate', route => route.fulfill({ status: 503 }));
  await addon.click();
  await expect(page.getByRole('alert').filter({ hasText: 'Your previous options are still selected' })).toBeVisible();
  await expect(addon).toHaveAttribute('aria-pressed', 'true');
  await expect(consent).toHaveAccessibleName(/\$4,620/);
  await expect(sign).toBeDisabled();
});

test('revision conflict preserves signer details and requires consent to the updated total', async ({ page }) => {
  test.skip(!demo, 'Requires an isolated local preview.');
  const endpoint = '**/api/public/proposals/responsive-fixture';
  let revision = 'first-revision';
  let refreshFails = false;
  await page.route(endpoint, route => refreshFails ? route.fulfill({ status: 503 }) : route.fulfill({ json: {
    ...proposal, revision_id: revision,
    selected_total_price_usd: revision === 'first-revision' ? 4100 : 4400,
  } }));
  await page.route(endpoint + '/accept', route => route.fulfill({ status: 409, json: {
    detail: 'This proposal changed. Review the latest version before accepting.',
  } }));
  await page.setViewportSize({ width: 320, height: 900 });
  await page.goto(new URL('/p/responsive-fixture', demo).href);
  const name = page.getByRole('textbox', { name: 'Full Legal Name' });
  const email = page.getByRole('textbox', { name: 'Email Address' });
  const consent = page.getByRole('checkbox');
  const sign = page.getByRole('button', { name: 'Confirm & E-Sign Proposal' });
  await name.fill('Fictional Traveler');
  await email.fill('traveler@example.test');
  await consent.check();
  await sign.click();
  const review = page.getByRole('button', { name: 'Review latest proposal' });
  await expect(review).toBeVisible();
  await expect(sign).toBeDisabled();
  refreshFails = true;
  await review.click();
  await expect(page.getByTestId('acceptance-error')).toContainText('This proposal could not be loaded right now.');
  await expect(review).toBeEnabled();
  await expect(name).toHaveValue('Fictional Traveler');
  await expect(sign).toBeDisabled();
  refreshFails = false;
  revision = 'next-revision';
  await review.click();
  await expect(consent).toHaveAccessibleName(/\$4,400/);
  if (capture) {
    await sign.scrollIntoViewIfNeeded();
    await page.screenshot({ path: path.join(capture, 'proposal-revision-320.png'), animations: 'disabled' });
  }
  for (const width of [320, 768, 1440]) {
    await page.setViewportSize({ width, height: 900 });
    await expect(name).toHaveValue('Fictional Traveler');
    await expect(email).toHaveValue('traveler@example.test');
    await expect(consent).not.toBeChecked();
    await expect(sign).toBeDisabled();
  }
  await consent.check();
  await expect(sign).toBeEnabled();
});
