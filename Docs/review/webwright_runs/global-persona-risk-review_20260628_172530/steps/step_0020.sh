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
