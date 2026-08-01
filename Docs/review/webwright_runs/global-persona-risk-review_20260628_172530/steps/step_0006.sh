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
