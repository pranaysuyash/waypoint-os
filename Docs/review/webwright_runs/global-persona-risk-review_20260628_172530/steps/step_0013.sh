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
    print('BODY', (await page.locator('body').inner_text())[:8000])
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
        context = await browser.new_context(viewport={'width':1280,'height':1800})
        page = await context.new_page()
        page.on('response', lambda r: print('RESP', r.status, r.request.method, r.url) if ('/api/auth/' in r.url or '/api/' in r.url) else None)
        page.on('console', lambda m: print('CONSOLE', m.type, m.text) if m.type in ('error','warning') else None)
        await page.goto('http://127.0.0.1:3103/login', wait_until='domcontentloaded')
        await page.wait_for_timeout(1500)
        await page.locator('#email').click()
        await page.locator('#email').type('newuser@test.com', delay=50)
        await page.locator('#password').click()
        await page.locator('#password').type('testpass123', delay=50)
        print('VALUES_BEFORE', await page.locator('input').evaluate_all("els => els.map(e => ({id:e.id, value:e.value}))"))
        await page.screenshot(path=str(ss/'explore_08_login_typed.png'))
        async with page.expect_response(lambda r: '/api/auth/login' in r.url, timeout=15000) as resp_info:
            await page.get_by_role('button', name='Sign in').click()
        resp = await resp_info.value
        print('LOGIN_STATUS', resp.status)
        try:
            print('LOGIN_JSON', await resp.json())
        except Exception:
            print('LOGIN_TEXT', await resp.text())
        await page.wait_for_timeout(5000)
        await page.screenshot(path=str(ss/'explore_09_post_login.png'))
        await dump(page, 'POST_LOGIN')
        await browser.close()

asyncio.run(main())
PY
