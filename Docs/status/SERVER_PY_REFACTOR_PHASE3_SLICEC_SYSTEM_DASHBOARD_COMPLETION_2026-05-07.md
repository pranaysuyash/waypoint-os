# Server.py Refactor Phase 3 — Slice C (System + Dashboard) Completion

Date: 2026-05-07
Status: Completed
Scope executed: move only three system/dashboard routes from server.py to a dedicated APIRouter module.

## Implemented scope

Moved exactly:
- GET /api/system/unified-state
- GET /api/system/integrity/issues
- GET /api/dashboard/stats

No movement for:
- public checker
- agent runtime
- /run or /runs
- /trips
- analytics core
- drafts/settings/documents/booking collection
- startup/lifespan/app factory
- middleware/auth/rate-limit behavior

## Files changed

Created:
- spine_api/routers/system_dashboard.py
- tests/test_system_dashboard_router_behavior.py
- Docs/status/SERVER_PY_REFACTOR_PHASE3_SLICEC_SYSTEM_DASHBOARD_COMPLETION_2026-05-07.md

Modified:
- spine_api/server.py
  - import wiring (normal + fallback) for system_dashboard router
  - app.include_router(system_dashboard_router.router)
  - removed in-file handlers for the three moved routes
  - removed now-unused `IntegrityService` import from server.py
- tests/test_integrity.py
  - updated one patch target to `spine_api.routers.system_dashboard.IntegrityService.list_integrity_issues`

## Behavior preservation checks

Preserved:
- async route definitions
- endpoint-level Depends(get_current_agency)
- response_model on:
  - /api/system/integrity/issues -> IntegrityIssuesResponse
  - /api/dashboard/stats -> DashboardStatsResponse
- exact 500 detail strings:
  - "Internal integrity error" (unified-state + integrity/issues)
  - "Failed to compute dashboard stats" (dashboard/stats)
- logger.error(..., exc_info=True)
- agency.id forwarding to DashboardAggregator / IntegrityService service calls

Router design:
- `router = APIRouter()`
- no prefix
- no tags
- no router-level dependencies
- canonical imports only (no server.py imports)
- logger defined in router: `logger = logging.getLogger("spine_api")`

## Verification evidence

1) Required matrix
Command:
TMPDIR=/private/tmp PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest \
  tests/test_server_route_parity.py \
  tests/test_server_openapi_path_parity.py \
  tests/test_server_startup_invariants.py \
  tests/test_system_dashboard_router_behavior.py \
  tests/test_integrity.py -q

Result:
- 42 passed in 4.78s

2) Snapshot check
Command:
TMPDIR=/private/tmp PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/snapshot_server_routes.py

Result:
- route_count=129
- openapi_path_count=113

3) Forbidden server import check
Command:
grep -n "from spine_api.server\|import server" spine_api/routers/system_dashboard.py

Result:
- no matches (empty output, exit code 1)

## Stop condition

Slice C complete. Stopped here.
Did not begin Slice D.
