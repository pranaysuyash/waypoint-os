# Server.py Refactor Phase 3 — Slice D Candidate Comparison (Plan Only)

Date: 2026-05-07
Status: Comparison only. No route movement.

## Scope Guardrails
- Plan-only checkpoint.
- Do not move routes.
- Do not touch startup/lifespan/app factory/middleware/auth internals.
- Excluded by rule: /trips, core analytics, drafts, settings, documents, booking collection, /run, /runs.

## Candidate 1: Team routes

Exact routes:
1. GET /api/team/members
2. GET /api/team/members/{member_id}
3. POST /api/team/invite
4. PATCH /api/team/members/{member_id}
5. DELETE /api/team/members/{member_id}
6. GET /api/team/workload

Current behavior snapshot (server.py around lines 3887-3993):
- Auth/permissions/rate-limit:
  - Agency scoping present on 5/6 handlers via Depends(get_current_agency).
  - GET /api/team/members/{member_id} currently does not include agency dependency in function signature.
  - Permission gate present on mutating endpoints:
    - POST /api/team/invite -> require_permission("team:manage")
    - PATCH /api/team/members/{member_id} -> require_permission("team:manage")
    - DELETE /api/team/members/{member_id} -> require_permission("team:manage")
  - No limiter decorators.
- Dependencies and hidden coupling:
  - membership_service (list/get/invite/update/deactivate)
  - get_db / AsyncSession
  - AssignmentStore + TripStore for workload aggregation
- Persistence/write side effects:
  - POST/PATCH/DELETE write to membership data.
  - GET workload is read/compute only.
- Response models/contracts:
  - Mostly untyped dict/object responses; one explicit response_model=dict on list endpoint.
- Risk rating: Medium.
- Why/why not Slice D:
  - Why: coherent domain cluster; no rate limiting complexity.
  - Why not first choice: mixed permission profile + one route currently weaker scoping pattern makes parity-sensitive extraction slightly higher risk than followups.

## Candidate 2: Followup routes

Exact routes:
1. GET /followups/dashboard
2. PATCH /followups/{trip_id}/mark-complete
3. PATCH /followups/{trip_id}/snooze
4. PATCH /followups/{trip_id}/reschedule

Current behavior snapshot (server.py around lines 4195-4388):
- Auth/permissions/rate-limit:
  - Uniform agency dependency on all 4 endpoints via Depends(get_current_agency).
  - No permission decorators.
  - No limiter decorators.
- Dependencies and hidden coupling:
  - TripStore, AuditStore, local filesystem JSON read under data/trips in dashboard.
  - Inline datetime parsing/validation rules.
- Persistence/write side effects:
  - PATCH endpoints update TripStore and emit AuditStore events.
  - GET dashboard is read-only.
- Response models/contracts:
  - Untyped dict responses (no strict response_model decorators in this cluster).
  - Explicit HTTPException details for 404/400 validation paths.
- Risk rating: Low-Medium.
- Why/why not Slice D:
  - Why: smallest safe slice with uniform dependency/auth behavior and clear boundaries.
  - Why not: reads filesystem in dashboard and contains date parsing branches, but still materially less coupled than agent runtime/public checker.

## Candidate 3: Agent runtime routes

Exact routes:
1. GET /agents/runtime
2. POST /agents/runtime/run-once
3. GET /agents/runtime/events

Current behavior snapshot (server.py around lines 1623-1681):
- Auth/permissions/rate-limit:
  - Agency dependency on all 3 routes.
  - Permission gate on run-once: require_permission("ai_workforce:manage").
  - No limiter decorators.
- Dependencies and hidden coupling:
  - Process-global runtime objects: _agent_supervisor and _recovery_agent.
  - Coupled to supervisor health/registry and operational run path.
- Persistence/write side effects:
  - run-once triggers runtime execution pass (operational side effect).
  - events/runtime reads from AuditStore.
- Response models/contracts:
  - Untyped dict responses with runtime health payload shape.
- Risk rating: Medium-High.
- Why/why not Slice D:
  - Why: compact route count.
  - Why not: hidden operational coupling to global runtime state makes it poor next safety slice.

## Candidate 4: Public checker routes

Exact routes:
1. POST /api/public-checker/run
2. POST /api/public-checker/events
3. GET /api/public-checker/{trip_id}
4. GET /api/public-checker/{trip_id}/export
5. DELETE /api/public-checker/{trip_id}

Current behavior snapshot (server.py around lines 974-1120):
- Auth/permissions/rate-limit:
  - Mixed auth model:
    - run/events are intentionally unauthenticated public endpoints.
    - get/export/delete require agency + user dependencies.
  - Rate-limit decorators on public endpoints:
    - run -> 12/minute
    - events -> 30/minute
- Dependencies and hidden coupling:
  - run_public_checker_submission service wrapper
  - ProductBEventStore event ingestion
  - PublicCheckerArtifactStore export/delete
  - PUBLIC_CHECKER_EVENT_MAX_BYTES payload guard
- Persistence/write side effects:
  - event writes, artifact export/delete, trip deletion path.
- Response models/contracts:
  - Mixed explicit models (RunStatusResponse, PublicCheckerExportResponse, PublicCheckerDeleteResponse) + envelope validation.
- Risk rating: High.
- Why/why not Slice D:
  - Why: route group is contiguous.
  - Why not: mixed public/auth/rate-limit/persistence semantics in one group violates safest-next-slice heuristic.

## Recommendation (Rule Applied)
Rule: Prefer the smallest safe slice with uniform dependency behavior; avoid mixed public/auth/rate-limited groups.

Recommended Slice D: Followup routes.

Why:
- Uniform auth pattern (agency dependency across all four).
- No rate-limit decorators to migrate.
- No global runtime object coupling.
- Smaller and safer than Team when considering consistency of current dependency shape.

Second choice: Team routes.

Defer:
- Agent runtime routes (operational global-state coupling).
- Public checker routes (mixed public/auth + rate-limit + persistence-heavy side effects).

## Stop
Comparison complete. No implementation performed.