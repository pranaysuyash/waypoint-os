const path = require('node:path');
const { chromium } = require('playwright');

const base = process.env.RESPONSIVE_AUDIT_BASE || 'http://waypoint-demo.localhost:3017';
const publicMode = process.env.RESPONSIVE_AUDIT_PUBLIC === '1';
const widths = [320, 360, 390, 430, 639, 640, 767, 768, 820, 854, 1024, 1280, 1366, 1440, 1920];
const capture = process.env.RESPONSIVE_AUDIT_CAPTURE;
const captureWidths = (process.env.RESPONSIVE_AUDIT_CAPTURE_WIDTHS || '').split(',').map(Number);
const agency = [
  '/overview', '/inbox', '/communications', '/whatsapp', '/reviews', '/trips',
  '/quotes', '/bookings', '/documents', '/payments', '/suppliers', '/insights',
  '/destination-intelligence', '/audit', '/knowledge-base', '/knowledge',
  '/settings', '/seasons', '/inquiries/new?draft=new&tab=intake', '/trips/new/intake', '/workbench',
];
const publicRoutes = [
  '/', '/pricing', '/itinerary-checker', '/companion', '/corporate/offsites',
  '/login', '/signup', '/forgot-password', '/reset-password', '/privacy', '/terms', '/intake/fast',
];
const redirectPaths = {
  '/whatsapp': '/communications',
  '/knowledge-base': '/knowledge',
  '/workbench': '/inquiries/new',
  '/trips/new/intake': '/inquiries/new',
};
const routes = process.argv.slice(2);
const targets = routes.length ? routes : publicMode ? publicRoutes : agency;

async function audit() {
  const browser = await chromium.launch({ channel: 'chrome' });
  try {
    const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    await context.addInitScript(() => localStorage.setItem('waypoint:welcome-seen:v1', '1'));
    if (!publicMode) {
      const login = await context.newPage();
      await login.goto(base + '/api/demo-session', { timeout: 20000 });
      await login.close();
    }
    for (const route of targets) {
      const page = await context.newPage();
      try {
        const response = await page.goto(base + route, { timeout: 25000 });
        if (!response?.ok()) {
          console.log(JSON.stringify({ route, path: new URL(page.url()).pathname, status: response?.status(), error: 'Route did not render successfully' }));
          continue;
        }
        const redirectPath = redirectPaths[route];
        if (redirectPath) {
          await page.waitForURL(url => url.pathname === redirectPath, { timeout: 8000 });
        }
        await page.locator(publicMode ? 'body' : '#main-content').waitFor({ timeout: 8000 });
        await page.evaluate(() => document.fonts.ready);
        const observations = [];
        for (const width of widths) {
          await page.setViewportSize({ width, height: 900 });
          const layout = await page.evaluate((isPublic) => {
            const main = document.getElementById('main-content') ?? (isPublic ? document.body : null);
            if (!main) throw new Error('Workspace content is absent');
            const edge = Math.min(main.getBoundingClientRect().right, innerWidth);
            const clipped = Array.from(main.querySelectorAll('button, a[href], input, select, textarea, h1, h2'))
              .filter((element) => {
                const rect = element.getBoundingClientRect();
                if (rect.height === 0 || (rect.right <= edge + 2 && rect.left >= -2) || getComputedStyle(element).visibility !== 'visible') return false;
                for (let parent = element.parentElement; parent && parent !== main; parent = parent.parentElement) {
                  if (/auto|scroll/.test(getComputedStyle(parent).overflowX)) return false;
                }
                return true;
              })
              .slice(0, 10)
              .map((element) => ({
                tag: element.tagName,
                label: (element.getAttribute('aria-label') || element.textContent || '').trim().slice(0, 100),
              }));
            return {
              overflow: Math.max(0, main.scrollWidth - main.clientWidth, document.documentElement.scrollWidth - innerWidth),
              clipped,
            };
          }, publicMode);
          const flagged = layout.overflow > 2 || layout.clipped.length > 0;
          if (flagged) observations.push({ width, ...layout });
          if (capture && (flagged || captureWidths.includes(width))) {
            const name = route.split('?')[0].slice(1).replaceAll('/', '-') || 'home';
            await page.screenshot({ path: path.join(capture, name + '-' + width + '.png'), animations: 'disabled' });
          }
        }
        console.log(JSON.stringify({
          route, path: new URL(page.url()).pathname, status: response?.status(), widths, observations,
          headings: await page.locator(publicMode ? 'h1' : '#main-content h1').allTextContents(),
        }));
      } catch (error) {
        console.log(JSON.stringify({ route, error: String(error).split('\n')[0] }));
      } finally {
        await page.close();
      }
    }
  } finally {
    await browser.close();
  }
}

audit().catch((error) => { console.error(error); process.exitCode = 1; });
