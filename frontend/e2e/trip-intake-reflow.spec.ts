import { expect, test } from '@playwright/test';
import path from 'node:path';

const demo = process.env.OVERVIEW_DEMO_URL;
const capture = process.env.TRIP_INTAKE_CAPTURE;
test.use({ channel: process.env.OVERVIEW_BROWSER_CHANNEL });

test('loaded Intake preserves actions and an unsaved call note while resizing', async ({ page }) => {
  test.skip(!demo, 'Requires the isolated demo enquiry.');
  await page.setViewportSize({ width: 320, height: 900 });
  await page.addInitScript(() => localStorage.setItem('waypoint:welcome-seen:v1', '1'));
  await page.goto(new URL('/api/demo-session', demo).href);
  await page.goto(new URL('/overview', demo).href);
  await page.getByRole('link', { name: 'Open oldest enquiry' }).first().click();
  const activity = page.getByRole('button', { name: /(?:show|hide) activity/i });
  const rail = page.getByRole('complementary', { name: 'Trip timeline' });
  const tabs = page.getByRole('navigation', { name: 'Workspace stage tabs' }).locator('a,button');
  const captureCall = page.getByRole('button', { name: 'Capture call notes' });
  await expect(captureCall).toBeVisible();
  const tabLabels = await tabs.allTextContents();
  if (await activity.getAttribute('aria-expanded') !== 'true') await activity.click();
  await expect(rail).toBeVisible();

  const widths = [320, 390, 767, 768, 854, 1024, 1279, 1280, 1440, 1920];
  for (const width of widths) {
    await page.setViewportSize({ width, height: 900 });
    await expect(tabs).toHaveText(tabLabels);
    await expect(activity).toHaveAttribute('aria-expanded', 'true');
    const overflow = await page.locator('#main-content').evaluate((main) => main.scrollWidth - main.clientWidth);
    expect(overflow, 'Trip Intake overflow at ' + width + 'px').toBeLessThanOrEqual(2);
    for (const name of ['Copy message', 'Send Ask Link', 'Start planning']) {
      const button = page.getByRole('button', { name, exact: true });
      await expect(button).toBeVisible();
      const box = await button.boundingBox();
      expect(box!.x).toBeGreaterThanOrEqual(0);
      expect(box!.x + box!.width).toBeLessThanOrEqual(width + 1);
    }
  }

  await page.setViewportSize({ width: 320, height: 900 });
  await page.evaluate(() => window.scrollTo(0, 0));
  if (capture) {
    await page.screenshot({ path: path.join(capture, 'rail-open-320.png'), fullPage: true, animations: 'disabled' });
  }
  await captureCall.click();
  const drawer = page.getByRole('dialog', { name: 'Capture call notes' });
  const note = drawer.getByRole('textbox', { name: 'What did the customer tell you?' });
  await expect(note).toBeVisible();
  if (capture) {
    await page.screenshot({ path: path.join(capture, 'capture-call-320.png'), animations: 'disabled' });
  }
  await note.fill('Synthetic drawer resize check');
  for (const width of [320, 390, 768, 1440, 320]) {
    const height = width === 320 ? 640 : 900;
    await page.setViewportSize({ width, height });
    await expect(note).toHaveValue('Synthetic drawer resize check');
    for (const name of ['Cancel', 'Save Draft', 'Save and Process']) {
      const action = drawer.getByRole('button', { name, exact: true });
      await expect(action).toBeEnabled();
      const box = await action.boundingBox();
      expect(box!.x).toBeGreaterThanOrEqual(0);
      expect(box!.x + box!.width).toBeLessThanOrEqual(width + 1);
      expect(box!.y).toBeGreaterThanOrEqual(0);
      expect(box!.y + box!.height).toBeLessThanOrEqual(height + 1);
    }
  }
  await drawer.getByRole('button', { name: 'Cancel', exact: true }).click();
  await expect(note).toHaveCount(0);
  await expect(captureCall).toBeFocused();
  await activity.click();
  await expect(rail).toHaveCount(0);
});
