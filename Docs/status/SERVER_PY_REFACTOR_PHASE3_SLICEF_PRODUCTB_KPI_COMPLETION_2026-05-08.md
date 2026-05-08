# Server.py Refactor Phase 3 — Slice F Product-B KPI Completion

Date: 2026-05-08
Status: Implemented and verified (stopped at Slice F)

## Scope implemented
Moved only:
1. GET /analytics/product-b/kpis

## Files changed
- `spine_api/routers/product_b_analytics.py` (new)
- `spine_api/server.py` (Slice F wiring + removal of in-file handler)
- `tests/test_product_b_analytics_router_behavior.py` (new)

## Behavior contract preserved
- Function name: `get_product_b_kpis`
- Path: `/analytics/product-b/kpis`
- Query params:
  - `window_days: int = Query(default=30, ge=1, le=365)`
  - `qualified_only: bool = Query(default=False)`
- Dependency: `agency: Agency = Depends(get_current_agency)`
- Handler behavior preserved:
  - `_ = agency`
  - `return ProductBEventStore.compute_kpis(window_days=window_days, qualified_only=qualified_only)`
- No `response_model`
- No permission dependency
- No rate-limit decorator
- No persistence writes in handler

## server.py changes performed
- Added normal import:
  - `from routers import product_b_analytics as product_b_analytics_router`
- Added fallback importlib loading block for `routers.product_b_analytics`
- Added include router call:
  - `app.include_router(product_b_analytics_router.router)`
- Removed only in-file `get_product_b_kpis` handler from `server.py`

## Verification executed

### Test matrix
Command:
`TMPDIR=/private/tmp PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest tests/test_server_route_parity.py tests/test_server_openapi_path_parity.py tests/test_server_startup_invariants.py tests/test_product_b_events.py tests/test_product_b_analytics_router_behavior.py -q`

Result:
- `22 passed in 4.82s`

### Snapshot check
Command:
`TMPDIR=/private/tmp PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/snapshot_server_routes.py`

Observed:
- `route_count = 131`
- `openapi_path_count = 115`

### Forbidden import check
Command:
`grep -n "from spine_api.server\|import server" spine_api/routers/product_b_analytics.py`

Result:
- No matches

## Non-goals honored
- No public checker movement
- No agent runtime movement
- No settings movement
- No `/run` or `/runs` movement
- No startup/lifespan/app-factory/middleware changes
- No cleanup/hardening mixed into extraction

## Acceptance update (2026-05-08)
- Verdict: Phase 3 Slice F accepted.
- Scope acceptance: router extraction and behavior parity confirmed for `GET /analytics/product-b/kpis`.
- Phase status tracking:
  - Slice A: accepted
  - Slice B: accepted
  - Slice C: accepted
  - Slice D: accepted
  - Slice E: accepted
  - Slice F: accepted
  - Phase 3 overall: in progress

## Merge condition (carried forward)
- Merge only a Slice F-isolated patch.
- Do not bundle unrelated workspace drift, snapshot changes, extraction-route changes, frontend changes, or cleanup/hardening with this slice.

## Stop condition
Stopped after Slice F implementation and verification. No further slice work started.
