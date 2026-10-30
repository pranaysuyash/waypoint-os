import { chromium } from 'playwright';
import fs from 'fs';
import path from 'path';

const OUT_DIR = '/Users/pranay/Projects/travel_agency_agent/Docs/audits/visual-evidence/2026-10-30-aha-moments';
fs.mkdirSync(OUT_DIR, { recursive: true });

async function run() {
  const browser = await chromium.launch({
    headless: true,
    executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  });
  const context = await browser.newContext({
    viewport: { width: 1440, height: 1100 },
  });
  const page = await context.newPage();

  console.log('Navigating to http://localhost:3005/itinerary-checker...');
  await page.goto('http://localhost:3005/itinerary-checker', { waitUntil: 'networkidle' });

  // Switch to paste mode
  const pasteTab = page.locator('button:has-text("Paste itinerary")');
  await pasteTab.click();

  const textarea = page.locator('textarea');
  await textarea.fill(
    'Flight: British Airways BA178 JFK to LHR arriving 06:45 AM. Connecting flight: BA304 LHR to CDG departing 07:35 AM. Staying at The Ritz Paris for 3 nights. Then train to Rome for 2 nights at Hotel de Russie with my elderly parents. Day 2 Rome: Colosseum at 8am, Vatican Museum at 11am, Borghese Gallery at 2pm, Trastevere walking tour at 5pm.'
  );

  console.log('Submitting itinerary analysis...');
  const analyzeBtn = page.locator('button:has-text("Score My Itinerary")');
  await analyzeBtn.click();

  // Wait for results
  console.log('Waiting for results view...');
  await page.waitForSelector('text=Connection Stress', { timeout: 25000 });
  await page.waitForTimeout(2000);

  // 1. Desktop full page
  const fullDesktopPath = path.join(OUT_DIR, '01-results-showcase-desktop.png');
  await page.screenshot({ path: fullDesktopPath, fullPage: true });
  console.log('Saved:', fullDesktopPath);

  // 2. Tab: Stress Gauge
  await page.locator('button:has-text("Connection Stress")').scrollIntoViewIfNeeded();
  await page.waitForTimeout(500);
  const stressPath = path.join(OUT_DIR, '02-aha-connection-stress-gauge.png');
  await page.screenshot({ path: stressPath });
  console.log('Saved:', stressPath);

  // 2b. Tab: 2.5D Airport Cutaway
  console.log('Clicking 2.5D Airport Cutaway tab...');
  await page.locator('button:has-text("2.5D Airport Cutaway")').click();
  await page.waitForTimeout(1000);
  const airportCutawayPath = path.join(OUT_DIR, '08-aha-isometric-airport-cutaway.png');
  await page.screenshot({ path: airportCutawayPath });
  console.log('Saved:', airportCutawayPath);

  // 2c. Tab: 3D Globe Flight Arc
  console.log('Clicking 3D Globe Flight Arc tab...');
  await page.locator('button:has-text("3D Globe Flight Arc")').click();
  await page.waitForTimeout(1200);
  const globe3dPath = path.join(OUT_DIR, '09-aha-3d-globe-flight-arc.png');
  await page.screenshot({ path: globe3dPath });
  console.log('Saved:', globe3dPath);

  // 3. Tab: Route Arc Ribbon
  console.log('Clicking Route Arc Ribbon tab...');
  await page.locator('button:has-text("Route Arc Ribbon")').click();
  await page.waitForTimeout(800);
  const routePath = path.join(OUT_DIR, '03-aha-route-arc-ribbon.png');
  await page.screenshot({ path: routePath });
  console.log('Saved:', routePath);

  // 4. Tab: Pacing Curve
  console.log('Clicking Pacing Curve tab...');
  await page.locator('button:has-text("Pacing Curve")').click();
  await page.waitForTimeout(800);
  const pacingPath = path.join(OUT_DIR, '04-aha-pacing-curve.png');
  await page.screenshot({ path: pacingPath });
  console.log('Saved:', pacingPath);

  // 4b. Tab: 2.5D Suite Cutaway
  console.log('Clicking 2.5D Suite Cutaway tab...');
  await page.locator('button:has-text("2.5D Suite Cutaway")').click();
  await page.waitForTimeout(1000);
  const suiteCutawayPath = path.join(OUT_DIR, '10-aha-isometric-hotel-sanctuary.png');
  await page.screenshot({ path: suiteCutawayPath });
  console.log('Saved:', suiteCutawayPath);

  // 5. Tab: Before vs After
  console.log('Clicking Before vs After tab...');
  await page.locator('button:has-text("Before vs. After")').click();
  await page.waitForTimeout(800);
  const compPath = path.join(OUT_DIR, '05-aha-before-after.png');
  await page.screenshot({ path: compPath });
  console.log('Saved:', compPath);

  // 6. Tab: Perks Radar
  console.log('Clicking Perks Radar tab...');
  await page.locator('button:has-text("Perks Radar")').click();
  await page.waitForTimeout(800);
  const perksPath = path.join(OUT_DIR, '06-aha-perks-radar.png');
  await page.screenshot({ path: perksPath });
  console.log('Saved:', perksPath);

  // 7. Mobile Viewport
  console.log('Switching to mobile viewport 390x844...');
  await page.setViewportSize({ width: 390, height: 844 });
  await page.waitForTimeout(800);
  const mobilePath = path.join(OUT_DIR, '07-aha-results-mobile.png');
  await page.screenshot({ path: mobilePath, fullPage: true });
  console.log('Saved:', mobilePath);

  // Copy all artifacts to brain directory
  const BRAIN_DIR = '/Users/pranay/.gemini/antigravity/brain/36c33178-9471-4d93-ae01-4878db330ba6';
  const files = fs.readdirSync(OUT_DIR);
  for (const f of files) {
    if (f.endsWith('.png')) {
      fs.copyFileSync(path.join(OUT_DIR, f), path.join(BRAIN_DIR, f));
      console.log('Copied to brain artifact dir:', f);
    }
  }

  await browser.close();
  console.log('All visual captures completed successfully!');
}

run().catch((err) => {
  console.error('Error running capture:', err);
  process.exit(1);
});
