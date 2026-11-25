import { expect, test } from '@playwright/test';
import path from 'node:path';

const demo = process.env.OVERVIEW_DEMO_URL;
const capture = process.env.LANDING_CAPTURE;
test.use({ channel: process.env.OVERVIEW_BROWSER_CHANNEL });

test('departure board stage controls fit and keep working through resize', async ({ page }) => {
  test.skip(!demo, 'Requires the isolated demo with the departure board landing.');
  await page.setViewportSize({ width: 640, height: 900 });
  await page.goto(new URL('/', demo).href);
  const quote = page.getByRole('button', { name: '3 · Quote-Ready Brief' });
  const voice = page.getByRole('button', { name: '1 · Voice & Message Capture' });
  const hold = page.getByRole('button', { name: '2 · Missing-Date Hold' });
  const stage = page.getByTestId('departure-board-stage');
  const artwork = page.getByTestId('departure-board-artwork');
  const clipped: string[] = [];
  for (const width of [320, 390, 639, 640, 767, 768, 854, 1024, 1279, 1280, 1440, 1920]) {
    await page.setViewportSize({ width, height: 900 });
    const art = await artwork.boundingBox();
    const copy = await stage.getByTestId('hero-book-demo-cta').boundingBox();
    expect(art!.x + art!.width).toBeLessThanOrEqual(width + 1);
    if (width < 1280) expect(copy!.y + copy!.height).toBeLessThanOrEqual(art!.y);
    for (const button of [voice, hold, quote]) {
      await expect(button).toBeVisible();
      const box = await button.boundingBox();
      if (!box || box.x < 0 || box.x + box.width > width + 1) {
        clipped.push(width + 'px: ' + await button.innerText());
      }
    }
    if (capture && [320, 640, 854, 1440].includes(width)) {
      await quote.locator('..').screenshot({
        path: path.join(capture, 'landing-stage-' + width + '.png'),
        animations: 'disabled',
      });
    }
  }
  expect(clipped).toEqual([]);
  await page.setViewportSize({ width: 640, height: 900 });
  await voice.click();
  await expect(stage.getByRole('heading', { name: 'From inquiry to itinerary.' })).toBeVisible();
  await hold.click();
  await expect(stage.getByRole('heading', { name: 'See how it organizes the request.' })).toBeVisible();
  await quote.click();
  await expect(page.locator('#why-waypoint').getByText('Dates Confirmed', { exact: true })).toBeVisible();
  await expect(stage.getByRole('heading', { name: 'See how it organizes the request.' })).toBeVisible();
  await page.setViewportSize({ width: 320, height: 900 });
  await page.reload();
  await expect(stage.getByRole('heading', { name: 'Every inquiry. Under control.' })).toBeVisible();
  const destination = artwork.getByRole('button', { name: 'Inspect DESTINATION provenance' });
  await destination.click();
  await expect(stage.getByRole('heading', { name: 'See how it organizes the request.' })).toBeVisible();
});
