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
