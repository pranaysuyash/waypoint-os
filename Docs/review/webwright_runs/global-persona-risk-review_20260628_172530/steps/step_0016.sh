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
    cookies = [{'name': c.name, 'value': c.value, 'domain': '127.0.0.1', 'path': '/'} for c in client.cookies.jar]

msg = "London-based events team of 42 wants Cape Town in March for a leadership offsite. Budget GBP 68,000. Needs premium hotel, meeting room, airport transfers, flexible dates, child-free, sunset cruise, winery visit, and VIP airport fast track."
notes = "Source market: London, UK. Corporate events/leadership offsite. Please process end-to-end and surface any safety/risk review issues explicitly."

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width':1280,'height':1800})
        await context.add_cookies(cookies)
        page = await context.new_page()
        page.on('response', lambda r: print('RESP', r.status, r.request.method, r.url) if '/api/' in r.url else None)
        page.on('console', lambda m: print('CONSOLE', m.type, m.text) if m.type in ('error','warning') else None)
        await page.goto(base + '/workbench', wait_until='domcontentloaded')
        await page.wait_for_timeout(3000)
        print('TEXTAREAS', await page.locator('textarea').evaluate_all("els => els.map((e,i) => ({i, placeholder:e.placeholder, value:e.value, labels:[...(document.querySelectorAll('label'))].filter(l => l.htmlFor===e.id).map(l=>l.textContent)}))"))
        print('INPUTS', await page.locator('input').evaluate_all("els => els.map((e,i) => ({i, id:e.id, type:e.type, placeholder:e.placeholder, value:e.value}))"))
        await page.screenshot(path=str(ss/'explore_13_workbench_before_fill.png'))
        tas = page.locator('textarea')
        await tas.nth(0).fill(msg)
        await tas.nth(1).fill(notes)
        await page.screenshot(path=str(ss/'explore_14_workbench_filled.png'))
        print('BODY_FILLED', (await page.locator('body').inner_text())[:7000])
        await page.get_by_role('button', name='Process Inquiry').click()
        await page.wait_for_timeout(10000)
        await page.screenshot(path=str(ss/'explore_15_after_process.png'))
        print('URL', page.url)
        print('TITLE', await page.title())
        print('BODY_AFTER', (await page.locator('body').inner_text())[:12000])
        try:
            print('HEADINGS', await page.get_by_role('heading').all_inner_texts())
        except Exception as e:
            print('HEADINGS_ERR', e)
        try:
            print('BUTTONS', await page.get_by_role('button').all_inner_texts())
        except Exception as e:
            print('BUTTONS_ERR', e)
        print('ARIA_BODY', await page.locator('body').aria_snapshot())
        await browser.close()

asyncio.run(main())
PY
