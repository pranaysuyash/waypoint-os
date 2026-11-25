import { expect, test } from '@playwright/test';
import path from 'node:path';

const demo = process.env.OVERVIEW_DEMO_URL;
const capture = process.env.OVERVIEW_CAPTURE;
const widths = [360, 390, 430, 639, 640, 767, 768, 820, 854, 1024, 1280, 1366, 1440, 1920];

test.use({ channel: process.env.OVERVIEW_BROWSER_CHANNEL });

test('Overview keeps queue details and links usable when the window is resized', async ({ page }) => {
  test.skip(!demo, 'Requires the isolated Overview demo with seeded enquiries.');
  await page.setViewportSize({ width: 854, height: 1000 });
  await page.addInitScript(() => localStorage.setItem('waypoint:welcome-seen:v1', '1'));
  await page.goto(new URL('/api/demo-session', demo).href);
  await page.goto(new URL('/overview', demo).href);

  const queue = page.getByRole('region', { name: 'Action Required' }).locator('li').filter({
    hasText: 'Enquiries needing review',
  }).first();
  const oldest = queue.getByRole('link', { name: 'Open oldest enquiry' });
  const all = queue.getByRole('link', { name: 'Open all enquiries' });
  await expect(oldest).toBeVisible();
  const examples = queue.getByText('Actionable Queue Items', { exact: true }).locator('..').getByRole('link');
  await expect(examples).toHaveCount(2);
  const links = await examples.evaluateAll((nodes) => nodes.map((node) => node.getAttribute('href')));
  const primaryHref = await oldest.getAttribute('href');
  const secondaryHref = await all.getAttribute('href');
  expect(links[0]).toBe(primaryHref);
  expect(links[0]).not.toBe(links[1]);
  expect(secondaryHref).toBeTruthy();

  const squeezed: string[] = [];
  for (const width of widths) {
    await page.setViewportSize({ width, height: 1000 });
    await expect(oldest).toBeVisible();
    await expect(all).toBeVisible();
    await expect(oldest).toHaveAttribute('href', primaryHref!);
    await expect(all).toHaveAttribute('href', secondaryHref!);
    for (const [index, href] of links.entries()) {
      const example = examples.nth(index);
      await expect(example).toBeVisible();
      await expect(example).toHaveAttribute('href', href!);
      await expect(example).toContainText(/Travel.*2027/);
      await expect(example).toContainText(/(?:17|8) pax/);
      await expect(example).toContainText('Not assigned');
      await expect(example).toContainText(/Ref\s+\w+/);
    }
    const layout = await queue.evaluate((card) => {
      const grid = Array.from(card.querySelectorAll('p'))
        .find((node) => node.textContent === 'Actionable Queue Items')?.nextElementSibling;
      const cardWidth = card.getBoundingClientRect().width;
      const gridWidth = grid?.getBoundingClientRect().width ?? 0;
      const narrowestTile = Math.min(...Array.from(grid?.children ?? [], (tile) => tile.getBoundingClientRect().width));
      return { cardWidth, gridWidth, narrowestTile, scrollWidth: document.documentElement.scrollWidth };
    });
    if (layout.gridWidth < layout.cardWidth - 36 || layout.narrowestTile < Math.min(250, layout.gridWidth - 1) || layout.scrollWidth > width) {
      squeezed.push(`${width}px ${JSON.stringify(layout)}`);
    }
    if (capture && [390, 768, 854, 1024, 1440].includes(width)) {
      await queue.screenshot({ path: path.join(capture, `overview-${width}.png`), animations: 'disabled' });
    }
  }
  expect(squeezed, 'Queue tiles must use the card width and avoid compressed columns or page overflow').toEqual([]);

  await page.setViewportSize({ width: 854, height: 1000 });
  await oldest.click();
  await expect(page).toHaveURL(new URL(primaryHref!, demo).href);
  await page.goto(new URL('/overview', demo).href);
  await all.click();
  await expect(page).toHaveURL(new URL(secondaryHref!, demo).href);
});
