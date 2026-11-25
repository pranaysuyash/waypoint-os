import { expect, test } from '@playwright/test';
import path from 'node:path';

const demo = process.env.OVERVIEW_DEMO_URL;
const capture = process.env.FAST_INTAKE_CAPTURE;
test.use({ channel: process.env.OVERVIEW_BROWSER_CHANNEL });

test('fast intake preserves the teaser link and actions on narrow screens', async ({ page }) => {
  test.skip(!demo, 'Requires an isolated local preview.');
  const teaser = '/p/fixture-' + 'longtoken'.repeat(10);
  const note = 'Fictional family trip to Kyoto in November.';
  await page.route('**/api/v1/inbox/parse_social', route => route.fulfill({
    headers: { 'access-control-allow-origin': '*' },
    json: { ok: true, teaser_url: teaser, suitability_score: 87 },
  }));
  await page.addInitScript(() => {
    Object.defineProperty(navigator, 'clipboard', {
      value: {
        writeText: async (value: string) => {
          if (!sessionStorage.getItem('fixture-clipboard-denied')) {
            sessionStorage.setItem('fixture-clipboard-denied', '1');
            throw new Error('Clipboard denied');
          }
          sessionStorage.setItem('fixture-clipboard-value', value);
        },
      },
    });
  });
  await page.setViewportSize({ width: 320, height: 850 });
  await page.goto(new URL('/intake/fast', demo).href);
  await page.getByPlaceholder(/Paste DM/).fill(note);
  await page.getByRole('button', { name: 'Generate Interactive Teaser Link' }).click();
  const preview = page.getByRole('link', { name: 'Preview Teaser' });
  await expect(preview).toHaveAttribute('href', teaser);
  if (capture) {
    await preview.scrollIntoViewIfNeeded();
    await page.screenshot({ path: path.join(capture, 'fast-intake-320.png'), animations: 'disabled' });
  }
  for (const width of [320, 390, 640, 768, 1024, 1440]) {
    await page.setViewportSize({ width, height: 850 });
    const url = page.getByText(teaser, { exact: true });
    expect(await url.evaluate(el => el.scrollWidth - el.clientWidth)).toBeLessThanOrEqual(2);
    await expect(page.getByRole('textbox', { name: 'Paste Follower DM / Inquiry Text' })).toHaveValue(note);
    await expect(page.getByRole('button', { name: 'Copy Link' })).toBeEnabled();
    await expect(preview).toHaveAttribute('href', teaser);
  }
  await page.setViewportSize({ width: 320, height: 850 });
  const copy = page.getByRole('button', { name: 'Copy Link' });
  await copy.click();
  if (capture) {
    await preview.scrollIntoViewIfNeeded();
    await page.screenshot({ path: path.join(capture, 'fast-intake-copy-320.png'), animations: 'disabled' });
  }
  await expect(page.getByRole('alert').filter({ hasText: 'Could not copy the link' })).toBeVisible({ timeout: 2000 });
  await expect(page.getByRole('button', { name: 'Copied!' })).toHaveCount(0);
  await copy.click();
  await expect(page.getByRole('button', { name: 'Copied!' })).toBeVisible();
  expect(await page.evaluate(() => sessionStorage.getItem('fixture-clipboard-value')))
    .toBe(new URL(teaser, demo).href);
});
