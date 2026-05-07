# Server.py Refactor Phase 3 — Slice A Completion

Date: 2026-05-07
Status: Completed (Slice A only)
Scope executed: move run-status routes from server.py to dedicated APIRouter module.

## Implemented scope

Moved exactly four routes:
- GET /runs
- GET /runs/{run_id}
- GET /runs/{run_id}/steps/{step_name}
- GET /runs/{run_id}/events

No movement for:
- POST /run
- pipeline execution delegator
- startup/lifespan/app factory
- public-checker routes
- any other route family

## Files changed

Created:
- spine_api/routers/run_status.py
- tests/test_run_status_router_behavior.py
- Docs/status/SERVER_PY_REFACTOR_PHASE3_SLICEA_COMPLETION_2026-05-07.md

Modified:
- spine_api/server.py
  - Added run_status router import in both normal and fallback import paths
  - Added app.include_router(run_status_router.router)
  - Removed in-file /runs* handlers now hosted in router module
  - Removed now-unused get_run_events import from run_events import list
- Docs/status/SERVER_PY_REFACTOR_PHASE3_ROUTER_DECOMPOSITION_PLAN_2026-05-07.md
  - Updated APIRouter declaration to APIRouter() (no new tags)

## Boundary checks

- Endpoint-level Depends(get_current_agency) preserved exactly per moved route.
- No router-level dependency injection introduced for run_status router.
- No response model change.
- No route path change.
- No handler name change.
- No import of spine_api.server inside run_status router.

Verification command:
- grep -n "from spine_api.server\|import server" spine_api/routers/run_status.py
- Result: no matches (grep exit code 1 with empty output)

## Verification results

Required matrix:
- TMPDIR=/private/tmp PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest \
  tests/test_server_route_parity.py \
  tests/test_server_openapi_path_parity.py \
  tests/test_server_startup_invariants.py \
  tests/test_run_contract_drift_guard.py \
  tests/test_spine_pipeline_unit.py \
  tests/test_run_status_router_behavior.py -q
- Result: 32 passed in 2.92s

Snapshot parity:
- TMPDIR=/private/tmp PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/snapshot_server_routes.py
- Result:
  - route_count = 129
  - openapi_path_count = 113
  - no path/method drift observed

## Verdict

Slice A is complete and parity-safe.
Phase 3 overall remains in progress (additional route families still pending extraction in future slices).