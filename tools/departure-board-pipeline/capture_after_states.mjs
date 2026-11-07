import { chromium } from "/Users/pranay/Projects/travel_agency_agent/frontend/node_modules/playwright/index.mjs";

const dir = "/Users/pranay/.gemini/antigravity/brain/5f300d3d-dc79-47ee-b13b-b72d067aef9f/scratch";
const artDir = "/Users/pranay/.gemini/antigravity/brain/5f300d3d-dc79-47ee-b13b-b72d067aef9f";

const browser = await chromium.launch({
  headless: true,
  executablePath: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
});

const page = await browser.newPage({ viewport: { width: 1672, height: 941 } });
await page.goto("http://localhost:3005", { waitUntil: "networkidle", timeout: 30000 });
await page.waitForTimeout(1200);

// 1. Frame 1: Italy Resolved Hero
await page.screenshot({ path: `${dir}/after_frame1_italy_hero.png`, fullPage: false });
await page.screenshot({ path: `${artDir}/after_frame1_italy_hero.png`, fullPage: false });
console.log("Captured Frame 1 (Italy Hero)");

// 1b. Frame 1 under extreme bottom-right mouse hover (verifies zero armchair/coffee-table/pedestal ghosting or cutoff)
await page.mouse.move(1580, 910);
await page.waitForTimeout(250);
await page.screenshot({ path: `${dir}/after_frame1_mouse_extreme.png`, fullPage: false });
await page.mouse.move(836, 470);
await page.waitForTimeout(150);

// 2. Frame 2: Click "See it work ->" (Voice Ingest + Scanning Dates)
await page.getByTestId("see-it-work-cta").click();
await page.waitForTimeout(350);
await page.screenshot({ path: `${dir}/after_frame2_voice_ingest.png`, fullPage: false });
await page.screenshot({ path: `${artDir}/after_frame2_voice_ingest.png`, fullPage: false });
console.log("Captured Frame 2 (Voice Ingest + Finalizing Dates)");

// 3. Frame 3: Click "Brief X-Ray" (Provenance Wires + Slide-Over Brief Drawer)
await page.getByTestId("mode-toggle-provenance").click();
await page.waitForTimeout(450);
await page.screenshot({ path: `${dir}/after_frame3_provenance_brief.png`, fullPage: false });
await page.screenshot({ path: `${artDir}/after_frame3_provenance_brief.png`, fullPage: false });
console.log("Captured Frame 3 (Provenance Wires + Brief Drawer)");

// 4. Frame 4a: Switch back to Hero mode and click "Japan · Culture + Food"
await page.getByTestId("mode-toggle-provenance").click();
await page.getByTestId("inquiry-pill-japan").click();
await page.waitForTimeout(1300);
await page.screenshot({ path: `${dir}/after_frame4_japan_switched.png`, fullPage: false });
await page.screenshot({ path: `${artDir}/after_frame4_japan_switched.png`, fullPage: false });
console.log("Captured Frame 4a (Japan Switched)");

// 5. Frame 4b: Click "Morocco · Adventure"
await page.getByTestId("inquiry-pill-morocco").click();
await page.waitForTimeout(1300);
await page.screenshot({ path: `${dir}/after_frame4_morocco_switched.png`, fullPage: false });
await page.screenshot({ path: `${artDir}/after_frame4_morocco_switched.png`, fullPage: false });
console.log("Captured Frame 4b (Morocco Switched)");

await browser.close();
