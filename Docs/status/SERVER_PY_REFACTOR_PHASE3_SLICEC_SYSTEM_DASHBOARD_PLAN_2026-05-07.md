# Server.py Refactor Phase 3 — Slice C Plan (System + Dashboard)

Date: 2026-05-07
Status: Plan only (not implemented)

Checklist applied: IMPLEMENTATION_AGENT_REVIEW_HANDOFF_CHECKLIST.md

## Scope lock

Move only these routes:
- GET /api/system/unified-state
- GET /api/system/integrity/issues
- GET /api/dashboard/stats

Create (post-approval implementation target):
- spine_api/routers/system_dashboard.py

Hard constraints:
- Plan only, no implementation.
- router = APIRouter()
- No prefix.
- No tags unless existing OpenAPI metadata already has tags.
- No router-level dependencies.
- Preserve endpoint-level Depends(get_current_agency).
- Preserve response_model for integrity/issues and dashboard/stats.
- Preserve async route functions.
- Preserve current error handling details exactly.
- No startup/lifespan/app-factory movement.
- No middleware/auth/rate-limit changes.
- No movement of /trips, analytics, drafts, settings, documents, booking collection, public checker, agent runtime, /run, or /runs.

Implementation starts only after approval.

## 1) Exact routes to move

1. GET /api/system/unified-state
   - Current location: spine_api/server.py:3883-3895
2. GET /api/system/integrity/issues
   - Current location: spine_api/server.py:3898-3910
3. GET /api/dashboard/stats
   - Current location: spine_api/server.py:3913-3926

## 2) Current behavior to preserve

### GET /api/system/unified-state
- async function
- endpoint dependency: agency: Agency = Depends(get_current_agency)
- success: return DashboardAggregator.get_unified_state(agency_id=agency.id)
- failure: logs with logger.error(..., exc_info=True)
- failure response: HTTPException(status_code=500, detail="Internal integrity error")

### GET /api/system/integrity/issues
- async function
- endpoint dependency: agency: Agency = Depends(get_current_agency)
- response_model=IntegrityIssuesResponse
- success: return IntegrityService.list_integrity_issues(agency_id=agency.id)
- failure: logs with logger.error(..., exc_info=True)
- failure response: HTTPException(status_code=500, detail="Internal integrity error")

### GET /api/dashboard/stats
- async function
- endpoint dependency: agency: Agency = Depends(get_current_agency)
- response_model=DashboardStatsResponse
- success: return DashboardAggregator.get_dashboard_stats(agency_id=agency.id)
- failure: logs with logger.error(..., exc_info=True)
- failure response: HTTPException(status_code=500, detail="Failed to compute dashboard stats")

## 3) Imports/dependencies needed in new router

Import directly from canonical modules (not from server.py):
- from fastapi import APIRouter, Depends, HTTPException
- from spine_api.core.auth import get_current_agency
- from spine_api.models.tenant import Agency
- from spine_api.contract import IntegrityIssuesResponse, DashboardStatsResponse
- from src.services.dashboard_aggregator import DashboardAggregator
- from src.services.integrity_service import IntegrityService
- import logging

Router declaration:
- router = APIRouter()

No-go:
- APIRouter(prefix="/api/system")

## 4) server.py changes after approval

After approval only:
1. Import new router module in normal import path and fallback import path pattern used in server.py.
2. app.include_router(system_dashboard_router.router)
3. Remove only these three in-file handlers from server.py:
   - get_unified_state
   - get_integrity_issues
   - get_dashboard_stats
4. Keep all other routes and runtime sections untouched.

## 5) Tests to add

Create:
- tests/test_system_dashboard_router_behavior.py

Test cases:
1. /api/system/unified-state success path returns aggregator output.
2. /api/system/unified-state failure path raises 500 with detail "Internal integrity error".
3. /api/system/integrity/issues success path returns IntegrityIssuesResponse shape.
4. /api/system/integrity/issues failure path raises 500 with detail "Internal integrity error".
5. /api/dashboard/stats success path returns DashboardStatsResponse shape.
6. /api/dashboard/stats failure path raises 500 with detail "Failed to compute dashboard stats".
7. agency scope is passed through to service calls (agency.id argument assertions).

Use monkeypatch/patch to isolate service behavior without changing route contracts.

## 6) Verification matrix

Run:
- tests/test_server_route_parity.py
- tests/test_server_openapi_path_parity.py
- tests/test_server_startup_invariants.py
- tests/test_system_dashboard_router_behavior.py
- tests/test_integrity.py

Expected:
- all pass
- no route path/method drift
- no OpenAPI path drift
- no startup invariant regressions

## 7) Snapshot check expectations

Run:
- scripts/snapshot_server_routes.py

Expect unchanged counts:
- route_count=129
- openapi_path_count=113

## 8) Forbidden server import check

Run:
- grep -n "from spine_api.server\|import server" spine_api/routers/system_dashboard.py

Expected:
- no matches

## 9) Non-goals

- No extraction of any route outside the three listed above.
- No auth semantics change.
- No rate-limit change.
- No middleware change.
- No startup/lifespan/app-factory edits.
- No public checker/agent runtime movement.
- No /run or /runs movement.
- No data contract changes.

## Stop

Plan document complete.
Do not implement Slice C until explicit approval.
