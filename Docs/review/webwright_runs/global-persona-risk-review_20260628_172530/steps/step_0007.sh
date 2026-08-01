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
    print('BODY', body[:5000])
    try:
        print('HEADINGS', await page.get_by_role('heading').all_inner_texts())
    except Exception as e:
        print('HEADINGS_ERR', e)
    try:
        print('BUTTONS', await page.get_by_role('button').all_inner_texts())
    except Exception as e:
        print('BUTTONS_ERR', e)
    try:
        print('LINKS', await page.get_by_role('link').all_inner_texts())
    except Exception as e:
        print('LINKS_ERR', e)

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1280, 'height': 1800})
        page = await context.new_page()
        await page.goto('http://127.0.0.1:3103/login', wait_until='domcontentloaded')
        await page.wait_for_timeout(2000)
        await page.screenshot(path=str(ss/'explore_03_login_3103.png'))
        await dump(page, 'LOGIN_PAGE')
        for label in ['Email', 'Password']:
            print('HAS_LABEL', label, await page.get_by_label(label).count())
        await page.get_by_label('Email').fill('newuser@test.com')
        await page.get_by_label('Password').fill('testpass123')
        await page.get_by_role('button', name='Sign in').click()
        await page.wait_for_timeout(5000)
        await page.screenshot(path=str(ss/'explore_04_after_login_3103.png'))
        await dump(page, 'AFTER_LOGIN')
        await browser.close()

asyncio.run(main())
PY
