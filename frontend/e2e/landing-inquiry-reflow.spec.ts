import { expect, test } from '@playwright/test';
import path from 'node:path';

const demo = process.env.OVERVIEW_DEMO_URL;
const capture = process.env.LANDING_CAPTURE;
test.use({ channel: process.env.OVERVIEW_BROWSER_CHANNEL });

test('landing inquiry controls stay available and update the board after resizing', async ({ page }) => {
  test.skip(!demo, 'Requires the departure-board demo.');
  await page.setViewportSize({ width: 320, height: 900 });
  await page.goto(new URL('/', demo).href);
  const strip = page.getByTestId('hero-live-destination-strip');
  const input = strip.getByRole('textbox', { name: 'Enter any travel inquiry' });
  const submit = strip.getByTestId('hero-custom-inquiry-submit');
  const rotate = strip.getByTestId('hero-auto-rotate-toggle');
  const tag = page.getByTestId('board-hanging-iata-tag');
  await rotate.click();
  await expect(rotate).toContainText('Paused');
  const presets = strip.getByTestId(/^hero-dest-chip-/);
  const labels = await presets.allTextContents();
  expect(labels).toHaveLength(7);

  const note = '2 travelers for Dubai around June next year';
  await input.fill(note);
  for (const width of [320, 360, 390, 430, 639, 640, 767, 768, 854, 1024, 1280, 1440, 1920]) {
    await page.setViewportSize({ width, height: 900 });
    await expect(input).toHaveValue(note);
    await expect(presets).toHaveText(labels);
    for (const control of [input, submit, rotate]) {
      await control.scrollIntoViewIfNeeded();
      await expect(control).toBeInViewport({ ratio: 0.95 });
      const box = await control.boundingBox();
      expect(box!.x).toBeGreaterThanOrEqual(0);
      expect(box!.x + box!.width).toBeLessThanOrEqual(width + 1);
    }
    if (capture && [320, 640, 854, 1440].includes(width)) {
      await strip.screenshot({ path: path.join(capture, 'hero-inquiry-' + width + '.png'), animations: 'disabled' });
    }
  }

  await page.setViewportSize({ width: 320, height: 900 });
  await submit.click();
  await expect(tag).toHaveAttribute('data-iata-code', 'DXB');
  await expect(strip.getByTestId('hero-live-sync-badge')).toContainText('DXB · 2 travelers');
  await expect(input).toHaveValue(note);
  const japan = strip.getByTestId('hero-dest-chip-japan');
  await japan.focus();
  await japan.press('Enter');
  await expect(tag).toHaveAttribute('data-iata-code', 'JPN');
  await expect(japan).toHaveAttribute('aria-pressed', 'true');
  await expect(japan).toBeFocused();
  await expect(strip.getByTestId('hero-live-sync-badge')).toHaveAttribute('aria-live', 'polite');
  await rotate.click();
  await expect(rotate).toContainText('Auto-Cycling');
  await expect(rotate).toHaveAttribute('aria-pressed', 'true');
});
