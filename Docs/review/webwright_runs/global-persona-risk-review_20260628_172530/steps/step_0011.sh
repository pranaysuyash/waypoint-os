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
