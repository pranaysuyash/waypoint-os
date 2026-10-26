import fs from "node:fs";
import { chromium } from "/Users/pranay/Projects/travel_agency_agent/frontend/node_modules/playwright/index.mjs";

const brainDir = "/Users/pranay/.gemini/antigravity/brain/5f300d3d-dc79-47ee-b13b-b72d067aef9f";
const scratchDir = `${brainDir}/scratch`;

async function saveBoth(page, filename) {
  const scratchPath = `${scratchDir}/${filename}`;
  const artifactPath = `${brainDir}/${filename}`;
  await page.screenshot({ path: scratchPath, fullPage: false });
  fs.copyFileSync(scratchPath, artifactPath);
}

const browser = await chromium.launch({
  headless: true,
  executablePath: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
});

const page = await browser.newPage({ viewport: { width: 1672, height: 941 } });
await page.goto("http://localhost:3005", { waitUntil: "networkidle", timeout: 30000 });
await page.mouse.move(10, 10);
await page.waitForTimeout(1200);

// 1. Frame 1: Italy Resolved Hero (no bottom dock visible)
await saveBoth(page, "after_frame1_italy_hero.png");
console.log("Captured Frame 1 (Italy Hero)");

// 2. Frame 2: Click "See it work ->" (Voice Ingest + Scanning Dates)
await page.getByTestId("see-it-work-cta").click();
await page.mouse.move(10, 10);
await page.waitForTimeout(950);
await saveBoth(page, "after_frame2_voice_ingest.png");
console.log("Captured Frame 2 (Voice Ingest + Finalizing Dates)");

// 3. Frame 3: Click "Brief X-Ray" (Provenance Wires + Slide-Over Brief Drawer)
await page.getByTestId("mode-toggle-provenance").click({ force: true });
await page.mouse.move(10, 10);
await page.waitForTimeout(1100);
await saveBoth(page, "after_frame3_provenance_brief.png");
console.log("Captured Frame 3 (Provenance Wires + Brief Drawer)");

// 4. Frame 4a: Switch back to Hero mode and click "Japan · Culture + Food"
await page.getByTestId("mode-toggle-provenance").click({ force: true });
await page.getByTestId("inquiry-pill-japan").click({ force: true });
await page.mouse.move(10, 10);
await page.waitForTimeout(1300);
await saveBoth(page, "after_frame4_japan_switched.png");
console.log("Captured Frame 4a (Japan Switched)");

// 5. Frame 4b: Click "Morocco · Adventure"
await page.getByTestId("inquiry-pill-morocco").click({ force: true });
await page.mouse.move(10, 10);
await page.waitForTimeout(1300);
await saveBoth(page, "after_frame4_morocco_switched.png");
console.log("Captured Frame 4b (Morocco Switched)");

await browser.close();
