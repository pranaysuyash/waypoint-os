# Product B Smoke Run - 2026-05-07

## Scope
Validate live local smoke for Product B instrumentation after implementation:
1) backend + frontend servers boot and health
2) public checker run path
3) Product B event ingestion path
4) KPI endpoint returns non-zero sample and KPI values
5) event persistence confirms writes

## Environment
- Repo: `/Users/pranay/Projects/travel_agency_agent`
- Backend process session: `proc_79aa9ec4f81d`
- Frontend process session: `proc_8719699b4b65`
- Backend command:
  - `TMPDIR=/private/tmp PYTHONDONTWRITEBYTECODE=1 uv run uvicorn spine_api.server:app --port 8000`
- Frontend command:
  - `TMPDIR=/private/tmp npm run dev`

## Health checks (required)
- `curl -s http://localhost:8000/health`
  - Result: `{"status":"ok",...}`
- `curl -s -o /dev/null -w "%{http_code}" http://localhost:3000`
  - Result: `200`

## Smoke execution
Tracking IDs used:
- `session_id=smoke_sess_1778153394`
- `inquiry_id=smoke_inq_1778153394`

### A) Public checker run endpoint
- Endpoint: `POST /api/public-checker/run`
- Result: `500`
- Error:
  - `ForeignKeyViolationError: Key (agency_id)=(waypoint-hq) is not present in table "agencies"`
- Interpretation:
  - this is a real environment/data invariant failure in public checker persistence path,
  - not an event schema failure.

### B) Product B event ingestion endpoint
Posted canonical chain events directly to `POST /api/public-checker/events`:
- `intake_started` -> 200
- `first_credible_finding_shown` -> 200
- `action_packet_shared` -> 200
- `agency_revision_reported` -> 200
- `product_a_interest_signal` -> 200

All event posts returned `ok=true`.

### C) KPI endpoint
Authenticated with cookie flow (`POST /api/auth/signup`) and then called:
- `GET /analytics/product-b/kpis?window_days=30&qualified_only=false`
- Result: `200`

Key response evidence:
- sample:
  - `events=7`
  - `inquiries_total=2`
  - `qualified_inquiries=1`
- kpis_subset:
  - `agency_revision_rate_observed_7d=1.0`
  - `dark_funnel_rate=0.0`
  - `product_a_pull_through=1.0`

### D) Event store persistence
- File: `/Users/pranay/Projects/travel_agency_agent/data/product_b_events/events_normalized.jsonl`
- line growth during smoke: `before=1`, `after=7`, `delta=6`
- Stored events include the exact tracking IDs above.

## Verdict
- Event instrumentation path: PASS (event ingestion + KPI computation + persistence verified live)
- KPI endpoint: PASS (auth + non-zero sample + expected KPI keys)
- Public checker run path: FAIL in this local DB due to missing `waypoint-hq` agency row

## Root cause to fix next
`PUBLIC_CHECKER_AGENCY_ID` is set to `waypoint-hq`, but local DB does not contain that agency record. Public checker run cannot persist trip rows until this invariant is repaired.

## Recommended fix options
1) seed/create `waypoint-hq` agency in local DB, or
2) make `PUBLIC_CHECKER_AGENCY_ID` configurable per environment with bootstrap validation, or
3) derive a guaranteed existing agency ID in local/dev mode for public checker persistence.
