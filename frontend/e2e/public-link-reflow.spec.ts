import { expect, test } from '@playwright/test';

const demo = process.env.OVERVIEW_DEMO_URL;
test.use({ channel: process.env.OVERVIEW_BROWSER_CHANNEL });

const cases = [
  ['/join/fixture-invalid-invite', 'Invalid invitation'],
  ['/check/fixture-nonexistent-agency', 'Advisor link not found'],
  ['/p/fixture-invalid-proposal', 'Proposal unavailable'],
  ['/a/fixture-invalid-ask', 'Questions unavailable'],
  ['/g/fixture-invalid-deposit', 'Group Invite Not Found'],
] as const;

for (const [route, heading] of cases) {
  test(heading + ' remains readable after resize', async ({ page }) => {
    test.skip(!demo, 'Requires an isolated preview with the public API running.');
    await page.setViewportSize({ width: 320, height: 640 });
    await page.goto(new URL(route, demo).href);
    const message = page.getByRole('heading', { name: heading, exact: true });
    await expect(message).toBeVisible();
    for (const width of [320, 390, 768, 1024, 1440, 320]) {
      await page.setViewportSize({ width, height: 640 });
      await expect(message).toBeInViewport();
      expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width + 2);
    }
  });
}
