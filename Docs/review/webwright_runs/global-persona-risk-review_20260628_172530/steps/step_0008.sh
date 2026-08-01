cd /Users/pranay/Projects/travel_agency_agent/Docs/review/webwright_runs/global-persona-risk-review_20260628_172530 && python - <<'PY'
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright
root = Path('/Users/pranay/Projects/travel_agency_agent/Docs/review/webwright_runs/global-persona-risk-review_20260628_172530')
ss = root / 'screenshots'
ss.mkdir(exist_ok=True)

async def dump(page, tag):
    print(f'--- {tag} ---')
    print('URL', page.url)
    print('TITLE', await page.title())
    body = await page.locator('body').inner_text()
    print('BODY', body[:7000])
    for name, locator in [('HEADINGS', page.get_by_role('heading')), ('BUTTONS', page.get_by_role('button')), ('LINKS', page.get_by_role('link'))]:
        try:
            vals = await locator.all_inner_texts()
            print(name, vals[:100])
        except Exception as e:
            print(name + '_ERR', e)

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1280, 'height': 1800})
        page = await context.new_page()
        await page.goto('http://127.0.0.1:3103/login', wait_until='domcontentloaded')
        await page.wait_for_timeout(1500)
        await page.fill('#email', 'newuser@test.com')
        await page.fill('#password', 'testpass123')
        await page.screenshot(path=str(ss/'explore_05_login_filled.png'))
        await page.get_by_role('button', name='Sign in').click()
        await page.wait_for_timeout(6000)
        await page.screenshot(path=str(ss/'explore_06_after_login.png'))
        await dump(page, 'AFTER_LOGIN')
        await browser.close()

asyncio.run(main())
PY
