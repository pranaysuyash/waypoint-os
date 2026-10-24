import { chromium } from "playwright";
import { readFileSync } from "node:fs";

const cookies = readFileSync("/tmp/wp_cookies_3017.txt", "utf8")
  .split("\n").filter(l => l && !l.startsWith("#") && l.trim())
  .map(l => { const [domain, , path, secure, expires, name, value] = l.split("\t");
    return { name, value, domain, path, expires: Number(expires) || -1, httpOnly: false, secure: secure === "TRUE" }; });

const browser = await chromium.launch({ headless: true, channel: "chrome" });
const context = await browser.newContext({ viewport: { width: 1280, height: 900 } });
await context.addCookies(cookies);
const page = await context.newPage();
await page.goto("http://127.0.0.1:3017/trips/trip_visual_fd_unknown/decision", { waitUntil: "domcontentloaded" });
await page.waitForSelector('[data-testid="fare-drop-decision-card"]', { timeout: 60000 });
await page.waitForTimeout(4000);
await page.screenshot({ path: "/Users/pranay/Projects/travel_agency_agent/Docs/sims/assets/fare_drop_card_unknown_state.png", fullPage: true, type: "png" });
const unknown = await page.locator('[data-testid="fare-drop-options-unavailable"]').count();
const options = await page.locator('[data-testid="fare-drop-options"]').count();
console.log(JSON.stringify({ unknownTile: unknown, optionsTile: options }));
await browser.close();
