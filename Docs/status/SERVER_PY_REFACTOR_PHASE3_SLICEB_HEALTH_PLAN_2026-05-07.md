# Server.py Refactor Phase 3 — Slice B Plan (/health only)

Date: 2026-05-07
Status: Plan only (not implemented)

Checklist applied: IMPLEMENTATION_AGENT_REVIEW_HANDOFF_CHECKLIST.md

## Scope lock

This document is plan-only for Phase 3 Slice B.

Allowed target:
- Move only GET /health into a dedicated router module.

Proposed new file:
- spine_api/routers/health.py

Hard constraints:
- No route movement in this step (planning only).
- No app factory changes.
- No lifespan/startup movement.
- No middleware changes.
- No public checker movement.
- No /run or /runs movement.
- No auth/rate-limit behavior changes.
- No cleanup-only refactors.

Implementation starts only after approval.

## 1) Exact route to move

- GET /health

Current location evidence:
- spine_api/server.py:844-855

## 2) Current behavior to preserve exactly

Handler contract in server.py today:
- response_model=HealthResponse
- route function attempts in-function import:
  - from src.decision.health import health_check_dict
- on success, returns:
  - HealthResponse(status="ok", version="1.0.0", components=..., issues=...)
  - components and issues sourced from health_check_dict()
- on exception, falls back to:
  - HealthResponse(status="ok", version="1.0.0")
- no auth required
- no rate limit

Critical preservation note:
- Keep import of health_check_dict inside the route function in the moved router.
- Do not move that import to module top-level.
- Reason: fallback behavior depends on catching failures inside the route execution path.

## 3) Router shape

Target module shape:
- router = APIRouter()
- no prefix
- no tags unless existing OpenAPI metadata already has tags
  - current /health decorator has no tags
- no router-level dependencies

## 4) server.py changes after approval

After plan approval, and only then:

1. Add health router import in both import paths already used for other routers.

Normal import block (near spine_api/server.py:281):
- from routers import health as health_router

Fallback import block (near spine_api/server.py:288+):
- dynamic import for routers/health.py into health_router

2. Register router:
- app.include_router(health_router.router)

3. Remove in-file /health handler only:
- remove spine_api/server.py:844-855

No other handler removals or movement.

## 5) Tests to add

New test file:
- tests/test_health_router_behavior.py

Test cases:
1. success path with monkeypatched health_check_dict
   - monkeypatch src.decision.health.health_check_dict to return dict with components/issues
   - assert response contains status/version/components/issues

2. fallback path when health_check_dict raises
   - monkeypatch health_check_dict to raise
   - assert response is HealthResponse(status="ok", version="1.0.0")
   - assert no crash and no auth/rate-limit requirements introduced

## 6) Verification matrix

Run all:
- tests/test_server_route_parity.py
- tests/test_server_openapi_path_parity.py
- tests/test_server_startup_invariants.py
- tests/test_health_router_behavior.py

Expected:
- all pass
- no route parity drift
- no OpenAPI path drift
- no startup invariant regression

## 7) Snapshot check

Command:
- scripts/snapshot_server_routes.py

Expected snapshot values:
- route_count=129
- openapi_path_count=113

Any drift blocks merge until explained and corrected.

## 8) Forbidden import check

Command:
- grep -n "from spine_api.server\|import server" spine_api/routers/health.py

Expected:
- no matches

## Execution sequence (post-approval only)

1. Create spine_api/routers/health.py with isolated /health handler preserving in-function import + fallback semantics.
2. Wire server.py imports (normal + fallback) and include_router call.
3. Remove only in-file /health route.
4. Add tests/test_health_router_behavior.py.
5. Run verification matrix.
6. Run snapshot check and confirm counts.
7. Run forbidden import check.
8. Stop and report evidence.

## Non-goals

- No extraction of any other route family.
- No contract/schema changes.
- No startup/lifespan edits.
- No middleware/auth/rate-limit edits.
- No public checker, /run, or /runs modifications.
- No unrelated refactors.
