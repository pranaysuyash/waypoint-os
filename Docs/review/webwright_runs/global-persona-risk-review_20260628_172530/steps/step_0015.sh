cd /Users/pranay/Projects/travel_agency_agent/Docs/review/webwright_runs/global-persona-risk-review_20260628_172530 && python - <<'PY'
import asyncio, httpx
from pathlib import Path
from playwright.async_api import async_playwright
root = Path('/Users/pranay/Projects/travel_agency_agent/Docs/review/webwright_runs/global-persona-risk-review_20260628_172530')
ss = root / 'screenshots'
ss.mkdir(exist_ok=True)
base='http://127.0.0.1:3103'
with httpx.Client(base_url=base, follow_redirects=True, timeout=20) as client:
    client.post('/api/auth/login', json={'email':'newuser@test.com','password':'testpass123'}).raise_for_status()
    cookies = []
    for c in client.cookies.jar:
        cookies.append({'name': c.name, 'value': c.value, 'domain': '127.0.0.1', 'path': '/'})

async def dump(page, tag, shot):
    await page.wait_for_timeout(3000)
    await page.screenshot(path=str(ss/shot))
    print(f'--- {tag} ---')
    print('URL', page.url)
    print('TITLE', await page.title())
    print('BODY', (await page.locator('body').inner_text())[:9000])
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
        await context.add_cookies(cookies)
        page = await context.new_page()
        for path, tag, shot in [('/overview','OVERVIEW','explore_10_overview_auth.png'),('/workbench','WORKBENCH','explore_11_workbench_auth.png'),('/trips','TRIPS','explore_12_trips_auth.png')]:
            await page.goto(base+path, wait_until='domcontentloaded')
            await dump(page, tag, shot)
        await browser.close()

asyncio.run(main())
PY
