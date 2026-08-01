# Step 1
cd /Users/pranay/Projects/travel_agency_agent/Docs/review/webwright_runs/global-persona-risk-review_20260628_172530 && ls -la && echo '---TASK.JSON---' && sed -n '1,220p' task.json

# Step 2
cd /Users/pranay/Projects/travel_agency_agent/Docs/review/webwright_runs/global-persona-risk-review_20260628_172530 && cat > plan.md <<'EOF'
# Critical Points
- [ ] CP1: Log in successfully with newuser@test.com / testpass123.
- [ ] CP2: Open the workbench after login.
- [ ] CP3: Create a new trip or clearly reuse an existing trip suitable for this scenario.
- [ ] CP4: Set destination to Cape Town.
- [ ] CP5: Set travel timing to March.
- [ ] CP6: Set group size to exactly 42 travelers.
- [ ] CP7: Capture that the scenario is for a leadership offsite / events team from London.
- [ ] CP8: Set budget to GBP 68,000.
- [ ] CP9: Apply premium hotel requirement.
- [ ] CP10: Apply meeting room requirement.
- [ ] CP11: Apply airport transfers requirement.
- [ ] CP12: Apply flexible dates requirement.
- [ ] CP13: Apply child-free requirement.
- [ ] CP14: Apply sunset cruise requirement.
- [ ] CP15: Apply winery visit requirement.
- [ ] CP16: Apply VIP airport fast track requirement.
- [ ] CP17: Submit or advance the workflow so the app processes the completed trip request.
- [ ] CP18: Reach the Risk Review stage/page in the app.
- [ ] CP19: In the safety section, verify the UI shows the actual leaked terms or jargon, not only a generic failure message.
- [ ] CP20: Capture evidence needed to document what is good, bad, missing, and workflow gaps observed during the end-to-end flow.
EOF
python - <<'PY'
import json
from pathlib import Path
root = Path('/Users/pranay/Projects/travel_agency_agent/Docs/review/webwright_runs/global-persona-risk-review_20260628_172530')
critical_points = '''1. CP1: Log in successfully with newuser@test.com / testpass123.
2. CP2: Open the workbench after login.
3. CP3: Create a new trip or clearly reuse an existing trip suitable for this scenario.
4. CP4: Set destination to Cape Town.
5. CP5: Set travel timing to March.
6. CP6: Set group size to exactly 42 travelers.
7. CP7: Capture that the scenario is for a leadership offsite / events team from London.
8. CP8: Set budget to GBP 68,000.
9. CP9: Apply premium hotel requirement.
10. CP10: Apply meeting room requirement.
11. CP11: Apply airport transfers requirement.
12. CP12: Apply flexible dates requirement.
13. CP13: Apply child-free requirement.
14. CP14: Apply sunset cruise requirement.
15. CP15: Apply winery visit requirement.
16. CP16: Apply VIP airport fast track requirement.
17. CP17: Submit or advance the workflow so the app processes the completed trip request.
18. CP18: Reach the Risk Review stage/page in the app.
19. CP19: In the safety section, verify the UI shows the actual leaked terms or jargon, not only a generic failure message.
20. CP20: Capture evidence needed to document what is good, bad, missing, and workflow gaps observed during the end-to-end flow.'''
task_desc = 'Log in with newuser@test.com / testpass123, open the workbench, create or reuse a new trip, and simulate this exact customer scenario end-to-end: London-based events team of 42 wants Cape Town in March for a leadership offsite, GBP 68k budget, premium hotel, meeting room, airport transfers, flexible dates, child-free, sunset cruise, winery visit, VIP airport fast track. Verify the app reaches Risk Review and the safety section lists the actual leaked terms or jargon instead of only a generic failure. Document what is good, bad, missing, and any workflow gaps you see.'
config = {
  'image_judge_system_prompt': 'You are a harsh evaluator of web automation evidence. Return ONLY two labelled lines exactly in this format:\nReasoning: <1-2 sentences describing what the screenshot shows and which critical points it provides evidence for or against>\nScore: <integer 1-5, where 5 = this screenshot clearly evidences a critical point and 1 = this screenshot contains no relevant evidence>\nBe strict: if evidence is ambiguous, partially occluded, or indirect, score low.',
  'image_judge_user_prompt': f'Task description:\n{task_desc}\n\nCritical points to consider for this single screenshot:\n{critical_points}\n\nEvaluate this one image against ALL critical points, not just the most obvious one. Be harsh when evidence is ambiguous, partially hidden, or only implied. Score 5 only when the image clearly proves one or more critical points.',
  'final_verdict_system_prompt': 'You are a harsh aggregated judge of whether a web task was truly completed. You will receive the task description, critical points, the action history log, per-image reasonings, and all screenshots. First provide a Thoughts: block that explicitly evaluates every critical point and whether the combined evidence satisfies it. Then end your reply with EXACTLY one final line on its own: Status: success OR Status: failure. Be strict: missing, ambiguous, or indirect evidence means failure.',
  'final_verdict_user_prompt': f'Task description:\n{task_desc}\n\nCritical points:\n{critical_points}\n\nAction history log:\n{{action_history_log}}\n\nPer-image reasonings:\n{{image_reasonings}}\n\nUsing the complete action log, all screenshot reasonings, and the attached screenshots, determine whether every critical point is satisfied. Also assess whether the evidence documents what is good, bad, missing, and workflow gaps observed in the flow. If the app reaches Risk Review but the safety section does not visibly list actual leaked terms or jargon, treat that as a failure for CP19. Respond with a Thoughts: block that covers every critical point, then end with the required status line.'
}
(root / 'self_reflect_config.json').write_text(json.dumps(config, indent=2))
print('WROTE', root / 'self_reflect_config.json')
PY
ls -la plan.md self_reflect_config.json && sed -n '1,220p' plan.md && echo '---CONFIG---' && sed -n '1,260p' self_reflect_config.json

# Step 3
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

# Step 4
cd /Users/pranay/Projects/travel_agency_agent/Docs/review/webwright_runs/global-persona-risk-review_20260628_172530 && (echo '---PORTS---' && lsof -nP -iTCP -sTCP:LISTEN | sed -n '1,120p' && echo '---CONFIG SNAPSHOT SEARCH---' && grep -RniE '3100|localhost|port' config_snapshot logs .tmp 2>/dev/null | sed -n '1,220p')

# Step 5
cd /Users/pranay/Projects/travel_agency_agent/Docs/review/webwright_runs/global-persona-risk-review_20260628_172530 && python - <<'PY'
import httpx, re
from bs4 import BeautifulSoup
ports = [3000,3103,4173,5000,5173,5174,5175,5176,5177,5178]
for port in ports:
    url = f'http://127.0.0.1:{port}/'
    try:
        r = httpx.get(url, timeout=3.0, follow_redirects=True)
        text = r.text[:5000]
        m = re.search(r'<title>(.*?)</title>', text, re.I|re.S)
        title = m.group(1).strip() if m else ''
        soup = BeautifulSoup(text, 'html.parser')
        body = ' '.join(soup.get_text(' ', strip=True).split())[:300]
        print('PORT', port, 'STATUS', r.status_code, 'FINAL', str(r.url), 'TITLE', title)
        print('BODY', body)
        print('---')
    except Exception as e:
        print('PORT', port, 'ERROR', repr(e))
        print('---')
PY

# Step 6
cd /Users/pranay/Projects/travel_agency_agent/Docs/review/webwright_runs/global-persona-risk-review_20260628_172530 && python - <<'PY'
import httpx, re
ports = [3000,3103,4173,5000,5173,5174,5175,5176,5177,5178]
for port in ports:
    url = f'http://127.0.0.1:{port}/'
    try:
        r = httpx.get(url, timeout=3.0, follow_redirects=True)
        text = r.text[:8000]
        m = re.search(r'<title>(.*?)</title>', text, re.I|re.S)
        title = re.sub(r'\s+', ' ', m.group(1)).strip() if m else ''
        body = re.sub(r'<script.*?</script>|<style.*?</style>', ' ', text, flags=re.I|re.S)
        body = re.sub(r'<[^>]+>', ' ', body)
        body = re.sub(r'\s+', ' ', body).strip()[:400]
        print('PORT', port, 'STATUS', r.status_code, 'FINAL', str(r.url), 'TITLE', title)
        print('BODY', body)
        print('---')
    except Exception as e:
        print('PORT', port, 'ERROR', repr(e))
        print('---')
PY

# Step 7
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

# Step 8
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

# Step 9
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

# Step 10
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

# Step 11
cd /Users/pranay/Projects/travel_agency_agent/Docs/review/webwright_runs/global-persona-risk-review_20260628_172530 && python - <<'PY'
import httpx,re
from urllib.parse import urljoin
base='http://127.0.0.1:3103/login'
html=httpx.get(base,timeout=10).text
scripts=re.findall(r'<script[^>]+src="([^"]+)"', html)
print('SCRIPTS', scripts)
for src in scripts:
    if '/_next/static/' not in src:
        continue
    url=urljoin(base,src)
    try:
        txt=httpx.get(url,timeout=10).text
    except Exception as e:
        print('ERR',url,e)
        continue
    hits=[]
    for pat in ['newuser@test.com','testpass123','localStorage','sessionStorage','signin','signIn','login','auth','overview','workbench','trip']:
        if pat.lower() in txt.lower():
            hits.append(pat)
    if hits:
        print('URL',url)
        print('HITS',hits)
        for pat in hits[:6]:
            idx=txt.lower().find(pat.lower())
            if idx!=-1:
                print('SNIP',pat,txt[max(0,idx-220):idx+500])
        print('---')
PY

# Step 12
cd /Users/pranay/Projects/travel_agency_agent/Docs/review/webwright_runs/global-persona-risk-review_20260628_172530 && python - <<'PY'
import httpx, re
url='http://127.0.0.1:3103/_next/static/chunks/_075ey_2._.js'
txt=httpx.get(url,timeout=15).text
patterns=['handleSubmit','onSubmit','/api/auth/login','login: async','signIn: async','mockUsers','newuser@test.com','testpass123','Invalid credentials','router.push','/overview','/workbench']
for pat in patterns:
    idx=txt.find(pat)
    print('\n===', pat, idx, '===')
    if idx!=-1:
        print(txt[max(0,idx-1200):idx+2200])
PY

# Step 13
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

# Step 14
cd /Users/pranay/Projects/travel_agency_agent/Docs/review/webwright_runs/global-persona-risk-review_20260628_172530 && python - <<'PY'
import httpx, json
base='http://127.0.0.1:3103'
with httpx.Client(base_url=base, follow_redirects=True, timeout=20) as client:
    r = client.post('/api/auth/login', json={'email':'newuser@test.com','password':'testpass123'})
    print('LOGIN_STATUS', r.status_code)
    print('LOGIN_TEXT', r.text[:1000])
    print('COOKIES', client.cookies)
    me = client.get('/api/auth/me')
    print('ME_STATUS', me.status_code)
    print('ME_TEXT', me.text[:2000])
    for path in ['/overview','/workbench','/trips','/api/trips','/api/drafts','/api/inquiries']:
        try:
            rr = client.get(path)
            print('PATH', path, 'STATUS', rr.status_code, 'CT', rr.headers.get('content-type'))
            print(rr.text[:800])
        except Exception as e:
            print('PATH_ERR', path, repr(e))
        print('---')
PY

# Step 15
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

# Step 16
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

# Step 17
cd /Users/pranay/Projects/travel_agency_agent/Docs/review/webwright_runs/global-persona-risk-review_20260628_172530 && python - <<'PY'
import httpx
url='http://127.0.0.1:3103/_next/static/chunks/src_app_(agency)_workbench_IntakeTab_tsx_0ftqrot._.js'
txt=httpx.get(url,timeout=20).text
patterns=['Process Inquiry','disabled','customerMessage','agentNotes','textarea','trip purpose','purpose','Advanced Configuration','System Ready','onSubmit','/api/drafts','/api/trips','/api/workbench','/api/intake','/api/parse','/api/inquiries','risk review','safety','child','budget','party','destination','march']
for pat in patterns:
    idx=txt.lower().find(pat.lower())
    print('\n===', pat, idx, '===')
    if idx!=-1:
        print(txt[max(0,idx-1200):idx+2600])
PY

# Step 18
cd /Users/pranay/Projects/travel_agency_agent/Docs/review/webwright_runs/global-persona-risk-review_20260628_172530 && python - <<'PY'
import httpx,re
from urllib.parse import urljoin
base='http://127.0.0.1:3103/workbench'
html=httpx.get(base,timeout=20).text
scripts=re.findall(r'<script[^>]+src="([^"]+)"', html)
preloads=re.findall(r'<link[^>]+rel="preload"[^>]+as="script"[^>]+href="([^"]+)"', html)
urls=[]
for src in scripts+preloads:
    if '/_next/static/chunks/' in src and src not in urls:
        urls.append(src)
print('COUNT', len(urls))
patterns=['Process inquiry','Process Inquiry','Save Draft','Captured Details','Advanced Configuration','System Ready','Customer Message','Agent Notes','Risk Review','/api/auth/me','/api/drafts','/api/trips','/api/workbench','/api/intake','/api/inquiries','/api/parse','draft','process','inquiry','safety']
for src in urls:
    url=urljoin(base,src)
    try:
        txt=httpx.get(url,timeout=20).text
    except Exception as e:
        print('ERR',url,e)
        continue
    hits=[p for p in patterns if p.lower() in txt.lower()]
    if hits:
        print('\nURL',url)
        print('HITS',hits)
        for pat in hits[:8]:
            idx=txt.lower().find(pat.lower())
            print('SNIP',pat,txt[max(0,idx-400):idx+1200])
        print('---')
PY

# Step 19
cd /Users/pranay/Projects/travel_agency_agent/Docs/review/webwright_runs/global-persona-risk-review_20260628_172530 && python - <<'PY'
import httpx
url='http://127.0.0.1:3103/_next/static/chunks/src_1vd3mnq._.js'
txt=httpx.get(url,timeout=20).text
patterns=['Process Inquiry','Save Draft','Reset','Captured Details','Customer Message','Agent Notes','Advanced Configuration','Risk Review','api.post(','api.get(','/api/drafts','/api/trips','/api/auth/me','/api/safety','/api/reviews','draft_id','tripId','processInquiry','saveDraft','handleProcess','handleSave','disabled:','isValid','canProcess','textarea','onClick','onSubmit']
for pat in patterns:
    idx=txt.find(pat)
    print('\n===', pat, idx, '===')
    if idx!=-1:
        print(txt[max(0,idx-1800):idx+3200])
PY

# Step 20
cd /Users/pranay/Projects/travel_agency_agent/Docs/review/webwright_runs/global-persona-risk-review_20260628_172530 && python - <<'PY'
import httpx, json
base='http://127.0.0.1:3103'
msg = "London-based events team of 42 wants Cape Town in March for a leadership offsite. Budget GBP 68,000. Needs premium hotel, meeting room, airport transfers, flexible dates, child-free, sunset cruise, winery visit, and VIP airport fast track."
notes = "Source market: London, UK. Corporate events/leadership offsite. Please process end-to-end and surface any safety/risk review issues explicitly."
with httpx.Client(base_url=base, follow_redirects=True, timeout=30) as client:
    client.post('/api/auth/login', json={'email':'newuser@test.com','password':'testpass123'}).raise_for_status()
    payload = {
        'name': 'London events team Cape Town March risk review',
        'customer_message': msg,
        'agent_notes': notes,
        'status': 'open'
    }
    r = client.post('/api/drafts', json=payload)
    print('CREATE_DRAFT_STATUS', r.status_code)
    print('CREATE_DRAFT_TEXT', r.text[:4000])
    data = r.json() if 'application/json' in r.headers.get('content-type','') else {}
    draft_id = data.get('draft_id') or data.get('id') or data.get('item',{}).get('draft_id')
    print('DRAFT_ID', draft_id)
    if draft_id:
        gd = client.get(f'/api/drafts/{draft_id}')
        print('GET_DRAFT_STATUS', gd.status_code)
        print('GET_DRAFT_TEXT', gd.text[:8000])
        trip_seed = {
            'destination': 'Cape Town',
            'origin': 'London',
            'party': 42,
            'budget': 'GBP 68,000',
            'dateWindow': 'March',
            'tripPurpose': 'leadership offsite',
            'type': 'business',
            'contactName': 'London Events Team'
        }
        ct = client.post('/api/trips', json=trip_seed)
        print('CREATE_TRIP_STATUS', ct.status_code)
        print('CREATE_TRIP_TEXT', ct.text[:4000])
        trip = ct.json() if 'application/json' in ct.headers.get('content-type','') else {}
        trip_id = trip.get('id') or trip.get('trip_id') or trip.get('item',{}).get('id')
        print('TRIP_ID', trip_id)
        if trip_id:
            pd = client.post(f'/api/drafts/{draft_id}/promote', json={'trip_id': trip_id})
            print('PROMOTE_STATUS', pd.status_code)
            print('PROMOTE_TEXT', pd.text[:4000])
            gt = client.get(f'/api/trips/{trip_id}')
            print('GET_TRIP_STATUS', gt.status_code)
            print('GET_TRIP_TEXT', gt.text[:12000])
            rr = client.post(f'/api/trips/{trip_id}/reassess', json={})
            print('REASSESS_STATUS', rr.status_code)
            print('REASSESS_TEXT', rr.text[:4000])
PY

# Step 21
cd /Users/pranay/Projects/travel_agency_agent/Docs/review/webwright_runs/global-persona-risk-review_20260628_172530 && ls -la && echo '--- plan.md ---' && sed -n '1,240p' plan.md && echo '--- self_reflect_config.json ---' && sed -n '1,260p' self_reflect_config.json && echo '--- screenshots ---' && ls -la screenshots

# Step 22
python - <<'PY'
import httpx, json
BASE='http://127.0.0.1:3103'
client=httpx.Client(base_url=BASE, follow_redirects=True, timeout=30)
r=client.post('/api/auth/login', json={'email':'newuser@test.com','password':'testpass123'})
print('LOGIN', r.status_code)
for path in ['/api/auth/me','/api/trips','/api/trips/trip_591a648aedc8','/api/drafts/draft_496b37a2a6c8']:
    resp=client.get(path)
    print('\n===', path, resp.status_code, '===')
    txt=resp.text
    try:
        data=resp.json()
        print(json.dumps(data, indent=2)[:12000])
    except Exception:
        print(txt[:4000])
PY

# Step 23
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

