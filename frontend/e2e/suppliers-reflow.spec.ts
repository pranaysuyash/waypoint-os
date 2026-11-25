import { expect, test } from '@playwright/test';
import path from 'node:path';

const demo = process.env.OVERVIEW_DEMO_URL;
const capture = process.env.SUPPLIERS_CAPTURE;
test.use({ channel: process.env.OVERVIEW_BROWSER_CHANNEL });

test('active supplier holds and the reservation dialog reflow on phones', async ({ page }) => {
  test.skip(!demo, 'Requires an isolated local preview.');
  await page.addInitScript(() => localStorage.setItem('waypoint:welcome-seen:v1', '1'));
  await page.route(/\/supplier\/(contracts|inventory\/holds)(?:\?|$)/, route => {
    const items = new URL(route.request().url()).pathname.endsWith('/contracts')
      ? [{
        contract_id: 'fixture-contract', supplier_name: 'Amalfi Luxury DMC',
        destination: 'Amalfi Coast', currency: 'EUR', status: 'ACTIVE',
        uploaded_at: '2026-11-11T00:00:00Z',
        rate_table: [{ room_type: 'Sea View Terrace Suite', net_rate_per_night: 450, rack_rate_per_night: 650 }],
      }]
      : [{
        hold_id: 'fixture-hold', contract_id: 'fixture-contract', supplier_name: 'Amalfi Luxury DMC',
        room_type: 'Sea View Terrace Suite', guest_name: 'Fictional Traveler',
        check_in: '2026-12-10', check_out: '2026-12-14', net_rate_total: 1800,
        estimated_agency_margin: 800, expires_at: '2026-12-01T15:00:00Z',
      }];
    return route.fulfill({ json: { items } });
  });
  await page.setViewportSize({ width: 320, height: 900 });
  await page.goto(new URL('/api/demo-session?page=suppliers', demo).href);
  const table = page.getByRole('table').filter({ hasText: 'Fictional Traveler' });
  await expect(table).toBeVisible();
  for (const width of [320, 390, 639, 640, 767, 768, 854, 1024, 1280, 1440, 1920]) {
    await page.setViewportSize({ width, height: 900 });
    await expect(table.getByRole('columnheader')).toHaveCount(6);
    await expect(table.getByText('Fictional Traveler')).toBeVisible();
    const reserve = page.getByRole('button', { name: /Reserve 48h Hold/i });
    await expect(reserve).toBeVisible();
    if (width === 320) {
      const supplierName = page.getByText('Amalfi Luxury DMC', { exact: true }).filter({ visible: true }).first();
      const supplierBounds = await supplierName.boundingBox();
      const reserveBounds = await reserve.boundingBox();
      expect(reserveBounds!.y).toBeGreaterThan(supplierBounds!.y + supplierBounds!.height);
    }
    expect(await page.locator('#main-content').evaluate(el => el.scrollWidth - el.clientWidth)).toBeLessThanOrEqual(2);
    if (capture && [320, 768, 1440].includes(width)) {
      await page.getByRole('heading', { name: /Active 48h Soft-Holds/i }).scrollIntoViewIfNeeded();
      await page.screenshot({ path: path.join(capture, 'suppliers-' + width + '.png'), animations: 'disabled' });
    }
  }
  await page.setViewportSize({ width: 320, height: 900 });
  const scroller = page.getByRole('region', { name: /Active 48h Soft-Holds/i });
  await scroller.focus({ timeout: 3000 });
  await expect(scroller).toBeFocused();
  await page.keyboard.press('ArrowRight');
  await expect.poll(() => scroller.evaluate(el => el.scrollLeft)).toBeGreaterThan(0);
  await page.route('**/api/v1/supplier/inventory/soft-hold', route => route.abort('blockedbyclient'));
  const reserve = page.getByRole('button', { name: 'Reserve 48h Hold' });
  await reserve.click();
  const dialog = page.getByRole('dialog', { name: /Reserve 48h Soft-Hold/i });
  const checkIn = dialog.getByLabel('Check-in');
  const checkOut = dialog.getByLabel('Check-out');
  const guest = dialog.getByLabel('Lead traveler name');
  await checkIn.fill('2026-12-10');
  await checkOut.fill('2026-12-14');
  await guest.fill('Fictional Traveler');
  const clippedWidths: number[] = [];
  for (const width of [320, 390, 639, 640, 768, 1024, 1440, 1920]) {
    await page.setViewportSize({ width, height: width < 640 ? 320 : 900 });
    await expect(checkIn).toHaveValue('2026-12-10');
    await expect(checkOut).toHaveValue('2026-12-14');
    await expect(guest).toHaveValue('Fictional Traveler');
    await expect(dialog.getByLabel('Room tier')).toHaveValue('Sea View Terrace Suite');
    const title = dialog.getByRole('heading');
    await title.scrollIntoViewIfNeeded();
    const titleBox = await title.boundingBox();
    const dateBox = await checkOut.boundingBox();
    const panelFits = await title.evaluate(el => {
      const panel = el.parentElement!.parentElement!.getBoundingClientRect();
      return panel.top >= 0 && panel.bottom <= window.innerHeight;
    });
    if (!panelFits || titleBox!.y < 0 || dateBox!.x + dateBox!.width > width - 16) clippedWidths.push(width);
    if (capture && [320, 768, 1440].includes(width)) {
      await page.screenshot({ path: path.join(capture, 'supplier-hold-' + width + '.png'), animations: 'disabled' });
    }
  }
  expect(clippedWidths).toEqual([]);
  await page.setViewportSize({ width: 320, height: 320 });
  const confirm = dialog.getByRole('button', { name: 'Confirm 48h Soft-Hold' });
  await confirm.scrollIntoViewIfNeeded();
  await expect(confirm).toBeInViewport();
  if (capture) {
    await page.screenshot({ path: path.join(capture, 'supplier-hold-320-footer.png'), animations: 'disabled' });
  }
  await dialog.getByRole('button', { name: 'Cancel', exact: true }).click();
  await expect(dialog).toHaveCount(0);
});

test('rate-sheet editor keeps draft tiers readable across viewport changes', async ({ page }) => {
  test.skip(!demo, 'Requires an isolated local preview.');
  await page.addInitScript(() => localStorage.setItem('waypoint:welcome-seen:v1', '1'));
  await page.route('**/api/v1/supplier/contracts/upload', route => route.abort('blockedbyclient'));
  await page.setViewportSize({ width: 320, height: 640 });
  await page.goto(new URL('/api/demo-session?page=suppliers', demo).href);
  await page.getByTestId('open-upload-contract-btn').click();
  const editor = page.getByRole('dialog', { name: 'Record Supplier Rate Sheet' });
  const room = editor.getByRole('textbox', { name: 'Room tier 1' });
  const net = editor.getByRole('spinbutton', { name: 'Net rate 1' });
  const rack = editor.getByRole('spinbutton', { name: 'Rack rate 1' });
  await room.fill('Sea View Terrace Suite');
  await net.fill('450');
  await rack.fill('650');
  await editor.getByRole('button', { name: 'Add tier' }).click();
  const second = editor.getByRole('textbox', { name: 'Room tier 2' });
  await second.fill('Courtyard Suite');

  const narrowFields: string[] = [];
  for (const width of [320, 390, 639, 640, 767, 768, 854, 1024, 1280, 1440, 1920]) {
    await page.setViewportSize({ width, height: width < 640 ? 640 : 900 });
    await expect(room).toHaveValue('Sea View Terrace Suite');
    await expect(net).toHaveValue('450');
    await expect(rack).toHaveValue('650');
    await expect(second).toHaveValue('Courtyard Suite');
    await expect(editor.getByRole('button', { name: 'Save Rate Sheet' })).toBeEnabled();
    for (const field of [net, rack]) {
      const size = await field.boundingBox();
      if (size!.width < 72) narrowFields.push(width + 'px: ' + Math.round(size!.width));
    }
    if (capture && [320, 768, 1440].includes(width)) {
      await room.scrollIntoViewIfNeeded();
      await page.screenshot({ path: path.join(capture, 'rate-sheet-' + width + '.png'), animations: 'disabled' });
    }
  }
  expect(narrowFields).toEqual([]);
  await page.setViewportSize({ width: 320, height: 640 });
  await editor.getByRole('button', { name: 'Remove tier 2' }).click();
  await expect(second).toHaveCount(0);
  await expect(net).toHaveValue('450');
  await editor.getByRole('button', { name: 'Cancel', exact: true }).click();
  await expect(editor).toHaveCount(0);
});
