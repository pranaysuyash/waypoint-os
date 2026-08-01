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
