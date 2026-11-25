import { expect, test } from '@playwright/test';
import path from 'node:path';

const demo = process.env.OVERVIEW_DEMO_URL;
const capture = process.env.SHELL_CAPTURE;
test.use({ channel: process.env.OVERVIEW_BROWSER_CHANNEL });

test('shared command bar reflows and the account menu remains usable', async ({ page }) => {
  test.skip(!demo, 'Requires the isolated authenticated demo.');
  await page.addInitScript(() => localStorage.setItem('waypoint:welcome-seen:v1', '1'));
  await page.goto(new URL('/api/demo-session', demo).href);
  await page.goto(new URL('/insights', demo).href);
  const breadcrumb = page.getByRole('navigation', { name: 'Breadcrumb navigation' });
  const header = page.getByRole('banner').filter({ has: breadcrumb });
  const status = header.getByText('System ready', { exact: true });
  const user = header.getByRole('button', { name: 'User menu' });
  const wrapped: string[] = [];

  for (const width of [320, 360, 390, 639, 640, 767, 768, 854, 1024, 1440, 1920]) {
    await page.setViewportSize({ width, height: 900 });
    await expect(breadcrumb.getByRole('link', { name: 'Waypoint OS' })).toHaveAttribute('href', '/overview');
    for (const element of [breadcrumb.getByRole('link', { name: 'Waypoint OS' }), status]) {
      const lines = await element.evaluate((node) => {
        const range = document.createRange();
        range.selectNodeContents(node);
        return range.getClientRects().length;
      });
      if (lines !== 1) wrapped.push(width + 'px ' + await element.innerText() + ' occupies ' + lines + ' lines');
    }
    if (capture && [320, 390, 768, 1440].includes(width)) {
      await header.screenshot({ path: path.join(capture, 'command-bar-' + width + '.png') });
    }
    await user.click();
    const menu = page.getByRole('menu', { name: 'User menu' });
    await expect(menu).toBeVisible();
    await page.keyboard.press('Escape');
    await expect(menu).toHaveCount(0);
    await expect(user).toBeFocused();
  }
  expect(wrapped).toEqual([]);
});

test('mobile navigation preserves desktop destinations and call capture', async ({ page }) => {
  test.skip(!demo, 'Requires the isolated authenticated demo.');
  await page.addInitScript(() => localStorage.setItem('waypoint:welcome-seen:v1', '1'));
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto(new URL('/api/demo-session', demo).href);
  const desktop = page.getByRole('navigation', { name: 'Primary navigation' });
  await expect(desktop).toBeVisible();
  const destinations = await desktop.getByRole('link').evaluateAll(links => links.map(link => link.getAttribute('href')));
  const callHref = await page.getByRole('link', { name: 'New Inquiry', exact: true }).getAttribute('href');
  for (const width of [320, 390, 639, 767, 768, 790]) {
    await page.setViewportSize({ width, height: 420 });
    const mobile = page.getByRole('navigation', { name: 'Mobile bottom navigation' });
    const desktopBreakpoint = await page.evaluate(() => matchMedia('(min-width: 768px)').matches);
    if (width === 790) expect(desktopBreakpoint).toBe(true);
    if (desktopBreakpoint) {
      await expect(desktop).toBeVisible();
      await expect(mobile).toBeHidden();
      continue;
    }
    const more = mobile.getByRole('button', { name: 'More modules' });
    await more.click();
    const menu = mobile.getByRole('region', { name: 'More modules' });
    await expect(menu).toBeVisible();
    if (capture && width === 320) {
      await page.screenshot({ path: path.join(capture, 'mobile-modules-320.png'), animations: 'disabled' });
    }
    const links = await mobile.locator('a').evaluateAll(items => items.map(item => item.getAttribute('href')));
    expect(links).toEqual(expect.arrayContaining([...destinations, callHref]));
    const menuBox = await menu.boundingBox();
    expect(menuBox!.y).toBeGreaterThanOrEqual(0);
    await expect(desktop).toBeHidden();
    await menu.getByRole('link', { name: 'Seasonal Campaigns' }).scrollIntoViewIfNeeded();
    await expect(menu.getByRole('link', { name: 'Seasonal Campaigns' })).toBeInViewport();
    await menu.getByRole('link', { name: 'Seasonal Campaigns' }).press('Escape');
    await expect(menu).toBeHidden();
    await expect(more).toBeFocused();
  }
  await page.setViewportSize({ width: 390, height: 740 });
  const mobile = page.getByRole('navigation', { name: 'Mobile bottom navigation' });
  await expect(mobile.getByRole('link', { name: 'Inbox' })).toHaveAttribute('aria-current', 'page');
  const newInquiry = mobile.getByRole('link', { name: 'New' });
  await newInquiry.click();
  await expect(page).toHaveURL(/inquiries\/new/);
  if (capture) {
    await expect(page.getByRole('heading', { name: 'New Inquiry', exact: true })).toBeVisible();
    await page.screenshot({ path: path.join(capture, 'mobile-new-390.png'), animations: 'disabled' });
  }
  await expect(newInquiry).toHaveAttribute('aria-current', 'page');
  await expect(mobile.getByRole('link', { name: 'Inbox' })).not.toHaveAttribute('aria-current', 'page');
});

test('resizing an open mobile disclosure keeps keyboard focus in the workspace', async ({ page }) => {
  test.skip(!demo, 'Requires the isolated authenticated demo.');
  await page.addInitScript(() => localStorage.setItem('waypoint:welcome-seen:v1', '1'));
  await page.setViewportSize({ width: 390, height: 740 });
  await page.goto(new URL('/api/demo-session', demo).href);
  const more = page.getByRole('button', { name: 'More modules' });
  await more.click();
  const payments = page.getByRole('region', { name: 'More modules' }).getByRole('link', { name: 'Payments' });
  await payments.focus();
  await expect(payments).toBeFocused();

  await page.setViewportSize({ width: 1024, height: 740 });
  await expect(page.getByRole('navigation', { name: 'Primary navigation' })).toBeVisible();
  await expect(page.locator('#main-content')).toBeFocused();
  await page.setViewportSize({ width: 390, height: 740 });
  await expect(more).toHaveAttribute('aria-expanded', 'false');
  await expect(payments).toHaveCount(0);
  await expect(page.locator('#main-content')).toBeFocused();

  await more.click();
  const account = page.getByRole('button', { name: 'User menu' });
  await account.focus();
  await page.setViewportSize({ width: 1024, height: 740 });
  await expect(account).toBeFocused();
  await page.setViewportSize({ width: 390, height: 740 });
  await expect(more).toHaveAttribute('aria-expanded', 'false');
});
