# Server.py Refactor — Phase 3 Router Decomposition Plan (Plan Only)

Date: 2026-05-07
Status: Planning only (no route movement executed)
Scope: Smallest safe first router extraction after Phase 2B acceptance

Implementation starts only after plan approval.

## 0) Baseline evidence captured before planning

Commands run:
- TMPDIR=/private/tmp PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest tests/test_server_route_parity.py tests/test_server_openapi_path_parity.py tests/test_server_startup_invariants.py -q
  - Result: 7 passed
- TMPDIR=/private/tmp PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/snapshot_server_routes.py
  - Result: route_count=129, openapi_path_count=113

Purpose:
- Freeze current route/openapi baseline before any router movement.

## 1) Proposed first router group to extract

First slice: Run Status router only (not /run orchestrator, not /trips).

Rationale:
- Lowest blast radius among high-traffic core routes.
- Already grouped contiguously in server.py under "Run Status Endpoints (Wave A)".
- No rate-limiter decorators on this group.
- Keeps Phase 3 additive and isolated from pipeline execution ownership.

## 2) Exact routes included in Phase 3 Slice A

Move only these four handlers:
- GET /runs                        -> list_runs
- GET /runs/{run_id}               -> get_run_status
- GET /runs/{run_id}/steps/{step_name} -> get_run_step
- GET /runs/{run_id}/events        -> get_run_event_stream

Do not move:
- POST /run
- _execute_spine_pipeline delegator
- startup/lifespan/app creation/middleware/include_router wiring outside minimal include addition

## 3) Current auth/rate-limit/dependency behavior per route

GET /runs
- Dependencies: agency: Agency = Depends(get_current_agency)
- Behavior: filters RunLedger.list_runs(...) by agency.id and applies limit
- Rate limit: none

GET /runs/{run_id}
- Dependencies: agency: Agency = Depends(get_current_agency)
- Behavior: 404 on missing or wrong agency, stale timeout check for queued/running, returns steps/events summary
- Rate limit: none

GET /runs/{run_id}/steps/{step_name}
- Dependencies: agency: Agency = Depends(get_current_agency)
- Behavior: 404 on missing run/wrong agency/missing step
- Rate limit: none

GET /runs/{run_id}/events
- Dependencies: agency: Agency = Depends(get_current_agency)
- Behavior: 404 on missing run/wrong agency, returns chronological event list and total
- Rate limit: none

Preservation rule:
- Keep endpoint-level Depends(get_current_agency) exactly as-is in extracted router.
- No router-level dependency changes in Slice A.

## 4) APIRouter configuration for Slice A

New file:
- spine_api/routers/run_status.py

Router shape:
- router = APIRouter()
- No prefix (paths remain /runs* exactly)
- Route decorators in router module must keep exact paths and names

Dependencies/import strategy:
- Import canonical modules directly:
  - RunLedger from spine_api.run_ledger
  - get_run_events from spine_api.run_events
  - get_current_agency from spine_api.core.auth
  - Agency model + RunStatusResponse contract
- No import from spine_api.server in router module.

## 5) What remains in server.py after Slice A

Must remain:
- app creation/lifespan/middleware/OTel wiring
- existing include_router lines and auth toggle behavior
- POST /run route
- RunLedger.create(...) call in /run
- thread creation and thread.start() in /run
- _execute_spine_pipeline thin delegator (Phase 2B boundary)

Will change minimally:
- remove 4 moved /runs handlers from server.py
- add import for run_status router
- add app.include_router(run_status_router.router)
- keep all other routes untouched

## 6) Route/OpenAPI parity proof strategy

Gate A (must pass, no fixture write):
- tests/test_server_route_parity.py
- tests/test_server_openapi_path_parity.py
- tests/test_server_startup_invariants.py

Gate B (contract guards):
- tests/test_run_contract_drift_guard.py
- tests/test_spine_pipeline_unit.py

Gate C (targeted behavior after move):
- Add new unit test module: tests/test_run_status_router_behavior.py
  - wrong-agency => 404
  - missing run => 404
  - missing step => 404
  - success shape for /runs and /runs/{id}/events

Command matrix (proposed):
- TMPDIR=/private/tmp PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest \
  tests/test_server_route_parity.py \
  tests/test_server_openapi_path_parity.py \
  tests/test_server_startup_invariants.py \
  tests/test_run_contract_drift_guard.py \
  tests/test_spine_pipeline_unit.py \
  tests/test_run_status_router_behavior.py -q

Final check:
- TMPDIR=/private/tmp PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/snapshot_server_routes.py
- Expect unchanged route/openapi counts and path set.

## 7) Smallest safe first Phase 3 PR

PR contents (single slice):
1. Create spine_api/routers/run_status.py with four moved handlers.
2. Modify spine_api/server.py to include run_status router and remove the four in-file handlers.
3. Add tests/test_run_status_router_behavior.py.
4. No other route family movement.
5. No startup/app-factory/lifespan edits.
6. No auth/rate-limit/response-model changes.

## 8) Explicit non-goals for Slice A

- No movement of POST /run
- No movement of pipeline execution service boundaries
- No movement of public checker routes in this slice
- No movement of drafts/trips/analytics/settings/inbox/document routes
- No cleanup-only refactors mixed in

## 9) Decision

Recommended next action:
- Approve this plan, then execute Slice A exactly as scoped.

Blocked until approval:
- Any Phase 3 code movement beyond plan documentation.