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
