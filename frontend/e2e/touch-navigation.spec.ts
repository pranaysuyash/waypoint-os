import { devices, expect, test } from '@playwright/test';

const demo = process.env.OVERVIEW_DEMO_URL;
test.use({ ...devices['iPhone 13'] });

test('touch navigation remains usable through portrait and landscape viewport changes', async ({ page }) => {
  test.skip(!demo, 'Requires the isolated authenticated preview.');
  await page.addInitScript(() => localStorage.setItem('waypoint:welcome-seen:v1', '1'));
  await page.goto(new URL('/api/demo-session', demo).href);
  const mobile = page.getByRole('navigation', { name: 'Mobile bottom navigation' });
  const more = mobile.getByRole('button', { name: 'More modules' });
  await expect(mobile).toBeVisible();
  await more.evaluate(el => {
    el.addEventListener('touchstart', event => {
      if (event.isTrusted) el.setAttribute('data-received-touch', 'true');
    }, { once: true });
  });
  await more.tap();
  await expect(more).toHaveAttribute('data-received-touch', 'true');
  const modules = mobile.getByRole('region', { name: 'More modules' });
  const last = modules.getByRole('link', { name: 'Seasonal Campaigns' });
  await expect(modules).toBeVisible();
  await last.scrollIntoViewIfNeeded();
  await expect(last).toBeInViewport();

  await page.setViewportSize({ width: 844, height: 390 });
  await expect(page.getByRole('navigation', { name: 'Primary navigation' })).toBeVisible();
  await expect(mobile).toBeHidden();

  await page.setViewportSize({ width: 390, height: 664 });
  await expect(more).toHaveAttribute('aria-expanded', 'false');
  const start = mobile.getByRole('link', { name: 'New' });
  await start.tap();
  await expect(page.getByRole('heading', { name: 'New Inquiry', exact: true })).toBeVisible();
  await expect(start).toHaveAttribute('aria-current', 'page');
});
