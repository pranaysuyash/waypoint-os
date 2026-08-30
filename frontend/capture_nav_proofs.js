const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const targetDir = '/Users/pranay/.gemini/antigravity/brain/75e69aa1-b102-49fd-a614-fe795a8063f3';

(async () => {
  console.log('🚀 Launching Playwright for Navigation E2E Verification...');
  const browser = await chromium.launch({ headless: true });

  // Pre-hydrate auth cookie so protected routes render cleanly
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  await context.addCookies([
    {
      name: 'access_token',
      value: 'test_token',
      domain: 'localhost',
      path: '/',
      httpOnly: false,
      secure: false,
      sameSite: 'Lax',
    },
  ]);

  const page = await context.newPage();

  const routes = [
    { name: 'overview', url: 'http://localhost:3005/overview' },
    { name: 'inquiries_new', url: 'http://localhost:3005/inquiries/new' },
    { name: 'quotes', url: 'http://localhost:3005/quotes' },
    { name: 'bookings', url: 'http://localhost:3005/bookings' },
    { name: 'suppliers', url: 'http://localhost:3005/suppliers' },
    { name: 'knowledge', url: 'http://localhost:3005/knowledge' },
    { name: 'documents', url: 'http://localhost:3005/documents' },
  ];

  for (const r of routes) {
    try {
      console.log(`📸 Capturing ${r.name}: ${r.url}...`);
      await page.goto(r.url, { waitUntil: 'domcontentloaded' });
      await page.waitForTimeout(1500);
      const screenshotPath = path.join(targetDir, `nav_${r.name}.png`);
      await page.screenshot({ path: screenshotPath, fullPage: false });
      console.log(`✅ Saved ${r.name} screenshot to ${screenshotPath}`);
    } catch (e) {
      console.error(`❌ Failed to capture ${r.name}: ${e.message}`);
    }
  }

  await browser.close();
  console.log('🎉 Navigation E2E Visual Verification Completed!');
})();
