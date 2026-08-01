python - <<'PY'
import asyncio, os, httpx
from pathlib import Path
from playwright.async_api import async_playwright

BASE='http://127.0.0.1:3103'
WORKSPACE=Path(os.getcwd())
SS=WORKSPACE/'screenshots'
SS.mkdir(exist_ok=True)

async def main():
    client=httpx.Client(base_url=BASE, follow_redirects=True, timeout=30)
    r=client.post('/api/auth/login', json={'email':'newuser@test.com','password':'testpass123'})
    assert r.status_code==200, r.text
    cookies=[]
    for c in client.cookies.jar:
        cookies.append({'name':c.name,'value':c.value,'domain':'127.0.0.1','path':'/'})
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True)
        context=await browser.new_context(viewport={'width':1280,'height':1800})
        await context.add_cookies(cookies)
        page=await context.new_page()
        urls=[
            '/trips',
            '/trips/trip_591a648aedc8',
            '/trip/trip_591a648aedc8',
            '/workbench/trip_591a648aedc8',
            '/workbench?trip=trip_591a648aedc8',
            '/review/trip_591a648aedc8',
        ]
        for i,u in enumerate(urls,1):
            try:
                await page.goto(BASE+u, wait_until='domcontentloaded', timeout=15000)
                await page.screenshot(path=str(SS/f'route_probe_{i}.png'))
                print('\nURL',u)
                print('FINAL', page.url)
                print('TITLE', await page.title())
                print('H1S', await page.locator('h1,h2,h3,[role="heading"]').all_inner_texts())
                print('BUTTONS', await page.get_by_role('button').all_inner_texts())
                print('LINKS', await page.get_by_role('link').all_inner_texts())
                print('BODY', (await page.locator('body').inner_text())[:2000].replace('\n',' | '))
            except Exception as e:
                print('ERR',u,repr(e))
        await browser.close()

asyncio.run(main())
PY
