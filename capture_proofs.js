const { chromium } = require('playwright');
const path = require('path');

(async () => {
  console.log('🚀 Launching Playwright Chromium for E2E Visual Screenshots...');
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

  // 1. Capture B2B Workbench UI
  console.log('📸 Navigating to B2B Workbench: http://localhost:3005/...');
  await page.goto('http://localhost:3005/', { waitUntil: 'networkidle' });
  await page.waitForTimeout(3000);
  const workbenchPath = '/Users/pranay/.gemini/antigravity/brain/c076d50a-93f3-406d-85f7-41b771ca0650/e2e_workbench_live.png';
  await page.screenshot({ path: workbenchPath, fullPage: false });
  console.log(`✅ Saved Workbench Screenshot to ${workbenchPath}`);

  // 2. Capture Interactive Traveler Proposal UI
  console.log('📸 Navigating to Interactive Proposal: http://localhost:3005/proposals/test-proposal-123...');
  await page.goto('http://localhost:3005/proposals/test-proposal-123', { waitUntil: 'networkidle' });
  await page.waitForTimeout(3000);
  const proposalPath = '/Users/pranay/.gemini/antigravity/brain/c076d50a-93f3-406d-85f7-41b771ca0650/e2e_proposal_page_live.png';
  await page.screenshot({ path: proposalPath, fullPage: false });
  console.log(`✅ Saved Proposal Screenshot to ${proposalPath}`);

  await browser.close();
  console.log('🎉 Playwright E2E Screenshot Capture Completed Successfully!');
})();
