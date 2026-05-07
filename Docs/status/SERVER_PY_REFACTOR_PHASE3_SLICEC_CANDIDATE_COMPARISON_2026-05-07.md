# Server.py Refactor Phase 3 — Slice C Candidate Comparison

Date: 2026-05-07
Status: Plan-only checkpoint (no implementation)

## Context

Phase status:
- Slice A accepted
- Slice B accepted
- Phase 3 remains in progress

Goal of this checkpoint:
- Compare next extraction candidates before creating Slice C plan doc.
- Keep blast radius low and preserve route/OpenAPI/startup parity discipline.

## Candidates requested

Group A (small system/dashboard set):
1. GET /api/system/unified-state
2. GET /api/system/integrity/issues
3. GET /api/dashboard/stats

Group B (more coupled sets):
- agent runtime routes
- public checker routes

## Evidence from current server.py

### Group A routes (3 total)
- /api/system/unified-state at server.py:3883-3895
- /api/system/integrity/issues at server.py:3898-3910
- /api/dashboard/stats at server.py:3913-3926

Shared characteristics:
- All are async GET endpoints.
- All use agency dependency: Depends(get_current_agency).
- No rate limiter decorators.
- No direct persistence writes in handlers.
- Error shape is straightforward (HTTP 500 with static detail on exception).
- Service calls are narrow:
  - DashboardAggregator.get_unified_state(...)
  - IntegrityService.list_integrity_issues(...)
  - DashboardAggregator.get_dashboard_stats(...)

### Group B1: agent runtime routes (3 total)
- /agents/runtime at server.py:1617-1641
- /agents/runtime/run-once at server.py:1644-1662
- /agents/runtime/events at server.py:1665-1675

Coupling/risk:
- Uses process-global runtime objects:
  - _agent_supervisor
  - _recovery_agent
- Includes permission gate on run-once:
  - require_permission("ai_workforce:manage")
- Touches operational runtime behavior (run_once execution path), not read-only analytics.

### Group B2: public checker routes (5 total)
- /api/public-checker/run at server.py:968-977
- /api/public-checker/events at server.py:997-1019
- /api/public-checker/{trip_id} at server.py:1072-1082
- /api/public-checker/{trip_id}/export at server.py:1085-1095
- /api/public-checker/{trip_id} DELETE at server.py:1098-1109+

Coupling/risk:
- Rate limiter decorators present (12/min, 30/min).
- Mixed auth model (unauth run/events vs auth-gated artifact fetch/delete).
- Persistence-heavy side effects (event store + artifact store + trip deletion).
- Additional model and payload constraints in route section (PublicCheckerEventEnvelope, max payload bytes).

## Comparison verdict

### Safety and extraction complexity

1) Group A (system/dashboard) — best Slice C candidate
- Small, coherent 3-route cluster.
- Uniform dependency pattern (agency only).
- No rate limiter migration concerns.
- No startup/lifespan/app-factory coupling.
- Minimal side effects.
- Good next step to exercise async route extraction discipline.

2) Agent runtime routes — defer
- Operationally coupled to long-lived in-memory supervisor/recovery components.
- Contains manage-permission path and active run trigger.
- Better after another low-risk slice proves parity on async/auth-only service routes.

3) Public checker routes — defer
- Highest coupling among compared options.
- Mixed auth/rate-limit/persistence semantics in one cluster.
- Larger blast radius and more likely to introduce behavior drift if moved too early.

## Recommendation

Choose Group A as Slice C:
- GET /api/system/unified-state
- GET /api/system/integrity/issues
- GET /api/dashboard/stats

Defer agent runtime and public checker to later slices.

## Proposed next step (plan-only)

Create a dedicated Slice C plan doc before any movement:
- Docs/status/SERVER_PY_REFACTOR_PHASE3_SLICEC_SYSTEM_DASHBOARD_PLAN_2026-05-07.md

With constraints mirroring Slice A/B discipline:
- Plan only, no implementation.
- Move only those 3 routes.
- Router = APIRouter() with no prefix/tags/router-level dependencies.
- No startup/lifespan/app-factory/middleware/auth-rate-limit changes.
- No /trips, core /analytics, drafts, settings, documents, booking-collection movement.
- Include parity tests + snapshot checks + forbidden server-import check.

## Stop

This checkpoint is comparison-only.
No Slice C implementation started.