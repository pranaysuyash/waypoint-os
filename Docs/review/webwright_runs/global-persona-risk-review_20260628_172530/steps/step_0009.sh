cd /Users/pranay/Projects/travel_agency_agent/Docs/review/webwright_runs/global-persona-risk-review_20260628_172530 && python - <<'PY'
import asyncio
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
        page.on('response', lambda r: print('RESP', r.status, r.url) if ('login' in r.url or 'auth' in r.url or '/api/' in r.url) else None)
        page.on('console', lambda m: print('CONSOLE', m.type, m.text))
        await page.goto('http://127.0.0.1:3103/login', wait_until='domcontentloaded')
        await page.wait_for_timeout(1500)
        await page.fill('#email', 'newuser@test.com')
        await page.fill('#password', 'testpass123')
        await page.get_by_role('button', name='Sign in').click()
        await page.wait_for_timeout(5000)
        await page.screenshot(path=str(ss/'explore_07_login_attempt_result.png'))
        print('URL', page.url)
        print('TITLE', await page.title())
        print('BODY', (await page.locator('body').inner_text())[:5000])
        print('ALERTS', await page.get_by_role('alert').all_inner_texts())
        print('TEXTBOXES', await page.get_by_role('textbox').evaluate_all('(els) => els.map(e => ({id:e.id, name:e.name, type:e.type, value:e.value, ariaInvalid:e.getAttribute("aria-invalid"), validationMessage:e.validationMessage}))'))
        await browser.close()

asyncio.run(main())
PY
