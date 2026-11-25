import { expect, test } from '@playwright/test';
import path from 'node:path';

const demo = process.env.OVERVIEW_DEMO_URL;
const capture = process.env.DOCUMENTS_CAPTURE;
test.use({ channel: process.env.OVERVIEW_BROWSER_CHANNEL });

for (const entryPoint of ['documents', 'trip-ops'] as const) {
  test(entryPoint + ' document review reflows while retaining selections', async ({ page }) => {
    test.skip(!demo, 'Requires an isolated local preview.');
    const trip = { id: 'fixture-documents', destination: 'Kyoto and Osaka', stage: 'booking', type: 'family' };
    const endpoint = '/api/trips/' + trip.id;
    await page.addInitScript(() => localStorage.setItem('waypoint:welcome-seen:v1', '1'));
    await page.goto(new URL('/api/demo-session', demo).href);
    await page.route(/\/api\/trips(?:\?|$)/, route => route.fulfill({ json: { items: [trip], total: 1 } }));
    await page.route('**' + endpoint, route => route.fulfill({ json: trip }));
    const supplierReference = 'FIXTURE-' + '1234567890'.repeat(8);
    const changeNotes = 'Fictional hotel reported a room mismatch. Keep the original transfer and request an accessible replacement room.';
    if (entryPoint === 'trip-ops') {
      await page.route('**/api/v1/trips/' + trip.id, route => route.fulfill({ json: {
        active_disruption: { disruption_type: 'delay', flight_number: 'ZZ-471', severity: 'high',
          status: 'ACTIVE', source: 'operator_reported', delay_minutes: 185 },
      } }));
      await page.route('**/api/v1/disruptions/' + trip.id + '/**', route => route.abort('blockedbyclient'));
      await page.route('**/api/v1/trips/' + trip.id + '/booking-changes**', route => {
        if (route.request().method() !== 'GET') return route.abort('blockedbyclient');
        return route.fulfill({ json: { active: [{
          change_id: 'fixture-change', supplier: 'hotel', change_kind: 'overbook',
          supplier_ref: supplierReference, notes: changeNotes,
        }] } });
      });
    }
    await page.route('**' + endpoint + '/documents**', route => {
      const pathname = new URL(route.request().url()).pathname;
      if (pathname === endpoint + '/documents' && route.request().method() === 'GET') {
        return route.fulfill({ json: { trip_id: trip.id, documents: [{
          id: 'fixture-passport', trip_id: trip.id, document_type: 'passport', status: 'pending_review',
          filename_ext: '.pdf', size_bytes: 123456, uploaded_by_type: 'customer',
        }] } });
      }
      if (pathname === endpoint + '/documents/fixture-passport/extract') {
        return route.fulfill({ json: {
          id: 'fixture-extraction', status: 'pending_review', overall_confidence: 0.85, field_count: 1,
          fields: [{ field_name: 'full_name', value: 'Fictional Traveler With a Long Name', present: true, confidence: 0.85 }],
        } });
      }
      return route.abort('blockedbyclient');
    });
    await page.setViewportSize({ width: 1440, height: 900 });
    const route = entryPoint === 'documents' ? '/documents?tripId=' + trip.id : '/trips/' + trip.id + '/ops';
    await page.goto(new URL(route, demo).href);
    const row = page.getByTestId('ops-document-fixture-passport');
    const type = page.getByRole('combobox', { name: 'Document type' });
    await type.selectOption('hotel_confirmation');
    await row.getByRole('button', { name: 'Extract', exact: true }).click();
    const extraction = row.getByTestId('ops-extraction-fixture-passport');
    await expect(extraction).toContainText('Fictional Traveler With a Long Name');

    const change = page.getByRole('listitem').filter({ hasText: supplierReference });
    if (entryPoint === 'trip-ops') await expect(change).toContainText(changeNotes);
    const disruption = page.getByTestId('irrops-section');
    const draft = 'Carrier advised of a delay. Keep the accessible transfer on hold while the traveler confirms the new arrival.';
    const notes = disruption.getByRole('textbox', { name: 'Notes' });
    if (entryPoint === 'trip-ops') {
      await expect(disruption.getByTestId('irrops-active')).toContainText('ZZ-471');
      await disruption.getByLabel('Flight ref').fill('ZZ-472');
      await disruption.getByLabel('Delay (minutes)').fill('195');
      await notes.fill(draft);
    }
    const overflow: string[] = [];
    const clipped: number[] = [];
    for (const width of [320, 390, 639, 640, 767, 768, 854, 1024, 1280, 1440, 1920]) {
      await page.setViewportSize({ width, height: 900 });
      await expect(type).toHaveValue('hotel_confirmation');
      await expect(row).toContainText('Customer');
      await expect(row.getByRole('button', { name: 'Accept', exact: true })).toBeEnabled();
      await expect(row.getByTestId('ops-document-fixture-passport-reject-btn')).toBeEnabled();
      await expect(extraction).toBeVisible();
      if (entryPoint === 'trip-ops') {
        await expect(change.getByRole('button', { name: 'Resolve' })).toBeEnabled();
        await expect(disruption.getByLabel('Flight ref')).toHaveValue('ZZ-472');
        await expect(disruption.getByLabel('Delay (minutes)')).toHaveValue('195');
        await expect(notes).toHaveValue(draft);
        await expect(disruption.getByRole('button', { name: 'Mark resolved' })).toBeEnabled();
        await expect(disruption.getByRole('button', { name: 'Report disruption' })).toBeEnabled();
        if (capture && [320, 768, 1440].includes(width)) {
          await disruption.scrollIntoViewIfNeeded();
          await page.screenshot({ path: path.join(capture, 'disruption-' + width + '.png'), animations: 'disabled' });
        }
        for (const value of [supplierReference, changeNotes]) {
          const hidden = await change.getByText(value).evaluate(el => el.scrollWidth > el.clientWidth + 2);
          if (hidden) clipped.push(width);
        }
      }
      const spill = await page.locator('#main-content').evaluate(el => el.scrollWidth - el.clientWidth);
      if (spill > 2) {
        const elements = await page.locator('#main-content').evaluate(main => {
          const edge = main.getBoundingClientRect().right;
          return Array.from(main.querySelectorAll('*'))
            .filter(el => el.getBoundingClientRect().right > edge + 2 || el.scrollWidth > el.clientWidth + 2)
            .slice(0, 6)
            .map(el => el.tagName + ' ' + (el.getAttribute('data-testid') || el.className));
        });
        overflow.push(width + 'px: ' + spill + ' (' + elements.join(', ') + ')');
      }
      if (capture && [320, 768, 1440].includes(width)) {
        await (entryPoint === 'trip-ops' ? change : row).scrollIntoViewIfNeeded();
        await page.screenshot({ path: path.join(capture, entryPoint + '-' + width + '.png'), animations: 'disabled' });
      }
    }
    expect(overflow).toEqual([]);
    expect(clipped).toEqual([]);
    if (entryPoint === 'trip-ops') {
      await page.setViewportSize({ width: 320, height: 900 });
      expect(await notes.evaluate(el => el.clientHeight)).toBeGreaterThan(48);
    }
    await page.setViewportSize({ width: 320, height: 900 });
    await page.reload();
    await row.getByRole('button', { name: 'Extract', exact: true }).click();
    await expect(extraction).toContainText('Fictional Traveler With a Long Name');
  });
}
