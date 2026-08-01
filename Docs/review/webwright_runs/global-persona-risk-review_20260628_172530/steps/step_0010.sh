cd /Users/pranay/Projects/travel_agency_agent/Docs/review/webwright_runs/global-persona-risk-review_20260628_172530 && python - <<'PY'
import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width':1280,'height':1800})
        page = await context.new_page()
        await page.goto('http://127.0.0.1:3103/login', wait_until='domcontentloaded')
        await page.wait_for_timeout(1200)
        print('FORMS', await page.locator('form').count())
        for i in range(await page.locator('form').count()):
            print('FORM', i, await page.locator('form').nth(i).evaluate("el => ({action: el.action, method: el.method, outer: el.outerHTML})"))
        print('INPUTS', await page.locator('input').evaluate_all("els => els.map(e => ({id:e.id, type:e.type, placeholder:e.placeholder, required:e.required, name:e.name, value:e.value, outer:e.outerHTML}))"))
        await page.locator('#email').click()
        await page.locator('#email').type('newuser@test.com', delay=40)
        await page.locator('#password').click()
        await page.locator('#password').type('testpass123', delay=40)
        print('AFTER_TYPE', await page.locator('input').evaluate_all("els => els.map(e => ({id:e.id, type:e.type, value:e.value}))"))
        await browser.close()

asyncio.run(main())
PY
