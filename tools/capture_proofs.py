"""
tools/capture_proofs.py — Automated screenshot capture for visual verification.
Captures live screenshots of /intake/fast, /proposals/prop_demo123, and /corporate/offsites.
"""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

ARTIFACT_DIR = Path("/Users/pranay/.gemini/antigravity/brain/c076d50a-93f3-406d-85f7-41b771ca0650")

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1280, "height": 800})
        page = await context.new_page()

        # 1. Capture /intake/fast
        print("Navigating to http://localhost:3005/intake/fast...")
        await page.goto("http://localhost:3005/intake/fast", wait_until="networkidle")
        await page.screenshot(path=str(ARTIFACT_DIR / "proof_intake_fast.png"))
        print("Captured proof_intake_fast.png")

        # 2. Capture /proposals/prop_demo123
        print("Navigating to http://localhost:3005/proposals/prop_demo123...")
        await page.goto("http://localhost:3005/proposals/prop_demo123", wait_until="networkidle")
        await page.screenshot(path=str(ARTIFACT_DIR / "proof_proposal_teaser.png"))
        print("Captured proof_proposal_teaser.png")

        # 3. Capture /corporate/offsites
        print("Navigating to http://localhost:3005/corporate/offsites...")
        await page.goto("http://localhost:3005/corporate/offsites", wait_until="networkidle")
        await page.screenshot(path=str(ARTIFACT_DIR / "proof_corporate_offsites.png"))
        print("Captured proof_corporate_offsites.png")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
