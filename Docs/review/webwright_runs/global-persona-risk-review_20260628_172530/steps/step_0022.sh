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
