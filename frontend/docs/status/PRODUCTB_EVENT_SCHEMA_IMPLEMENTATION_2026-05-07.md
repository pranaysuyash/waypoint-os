# Product B Event Schema Implementation Status (2026-05-07)

## Scope
Execution against todo phases t1-t5 for `Docs/PRODUCTB_EVENT_SCHEMA_V1_2026-05-07.md`.

## t1) Gap map summary (audit -> implementation)

### Existing coverage before implementation
- Public checker run existed: `POST /api/public-checker/run`.
- Public checker artifact export/delete existed.
- No dedicated Product B event ingestion endpoint.
- No Product B KPI endpoint.
- No dedicated Product B event storage (raw + normalized with dedup).
- FE had share/report UI affordances but no event emission.

### Gaps closed in this execution
- Added Product B event store with envelope validation, dedup by `event_id`, and raw+normalized JSONL persistence.
- Added public event ingestion endpoint.
- Added Product B KPI query endpoint with qualified sample filter.
- Added FE event emission for share/copy/evidence/revision/re-audit triggers.
- Added backend auto-emission for `intake_started` and `first_credible_finding_shown` inside public checker run.

## t2) Phase 0.1 schema wiring completed

### Backend
1) New event store module
- `spine_api/product_b_events.py`
  - required envelope validation
  - event-specific property validation
  - data-quality rule: rejects `first_credible_finding_shown` when `evidence_present=false`
  - deduplication by `event_id`
  - raw + normalized append-only files:
    - `data/product_b_events/events_raw.jsonl`
    - `data/product_b_events/events_normalized.jsonl`

2) API endpoint for event ingestion
- `spine_api/server.py`
  - `POST /api/public-checker/events`
  - returns 400 on validation error

3) Auto instrumentation in public checker run
- `spine_api/server.py`
  - emits `intake_started` before pipeline execution
  - emits `first_credible_finding_shown` after result materialization when blockers exist
  - persists `session_id` and `inquiry_id` in public checker trip meta

4) Frontend proxy mapping
- `frontend/src/lib/route-map.ts`
  - added route: `public-checker/events -> api/public-checker/events`

### Frontend
- `frontend/src/app/(traveler)/itinerary-checker/page.tsx`
  - added telemetry context IDs (`session_id`, `inquiry_id`)
  - added emit helper to post Product B events
  - emits:
    - `re_audit_started` (when analyzing again after prior result)
    - `action_packet_shared` (share CTA)
    - `action_packet_copied` (clipboard fallback)
    - `finding_evidence_opened` (JSON export interaction)
    - `agency_revision_reported` (new revision outcome buttons)

## t3) Phase 0.2 KPI definitions + query helpers completed

### KPI endpoint
- `spine_api/server.py`
  - `GET /analytics/product-b/kpis?window_days=&qualified_only=`

### KPI computation
- `spine_api/product_b_events.py`
  - p50/p90 `time_to_first_credible_finding_ms`
  - `forward_without_edit_rate`
  - `agency_revision_rate_observed_7d`
  - `inferred_revision_rate`
  - `dark_funnel_rate`
  - `product_a_pull_through`
  - confidence tier breakdown + counts

## t4) Phase 0.3 qualified sample filter completed

- Implemented in `ProductBEventStore.compute_kpis(..., qualified_only=True)`.
- Qualification rule currently:
  - inquiry has both `intake_started` and `first_credible_finding_shown`.

## t5) Verification evidence

### Python compile
Command:
`TMPDIR=/private/tmp PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m py_compile spine_api/server.py spine_api/product_b_events.py`
Result: pass (exit 0)

### New tests
Command:
`TMPDIR=/private/tmp PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest -q tests/test_product_b_events.py`
Result: `5 passed in 2.17s`

### Regression tests (targeted existing)
Command:
`TMPDIR=/private/tmp PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest -q tests/test_spine_pipeline_unit.py tests/test_agent_events_api.py`
Result: `18 passed in 1.91s`

Command:
`TMPDIR=/private/tmp PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest -q tests/test_call_capture_e2e.py`
Result: `12 passed in 1.78s`

### Frontend build verification
Commands:
- `npm install` (in `frontend/`)
- `npm run build` (in `frontend/`)

Result:
- install completed (`added 370 packages`)
- build passed (`Compiled successfully`, `Finished TypeScript`, static page generation complete)
