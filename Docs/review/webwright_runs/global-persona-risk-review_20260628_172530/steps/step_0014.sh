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
