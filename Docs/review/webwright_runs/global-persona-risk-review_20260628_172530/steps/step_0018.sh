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
