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
