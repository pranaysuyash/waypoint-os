cd /Users/pranay/Projects/travel_agency_agent/Docs/review/webwright_runs/global-persona-risk-review_20260628_172530 && python - <<'PY'
import asyncio, os
from pathlib import Path
from playwright.async_api import async_playwright
root = Path('/Users/pranay/Projects/travel_agency_agent/Docs/review/webwright_runs/global-persona-risk-review_20260628_172530')
ss = root / 'screenshots'
ss.mkdir(exist_ok=True)

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1280, 'height': 1800})
        page = await context.new_page()
        await page.goto('http://localhost:3100/login', wait_until='networkidle')
        print('URL1', page.url)
        print('TITLE1', await page.title())
        print('BODY1', (await page.locator('body').inner_text())[:4000])
        await page.screenshot(path=str(ss/'explore_01_login.png'))
        await page.get_by_label('Email').fill('newuser@test.com')
        await page.get_by_label('Password').fill('testpass123')
        await page.get_by_role('button', name='Login').click()
        await page.wait_for_load_state('networkidle')
        await page.screenshot(path=str(ss/'explore_02_after_login.png'))
        print('URL2', page.url)
        print('TITLE2', await page.title())
        print('BODY2', (await page.locator('body').inner_text())[:6000])
        print('LINKS', await page.get_by_role('link').all_inner_texts())
        print('BUTTONS', await page.get_by_role('button').all_inner_texts())
        await browser.close()

asyncio.run(main())
PY
