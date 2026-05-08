# Server.py Refactor Phase 3 — Slice E Candidate Comparison (Plan Only)

Date: 2026-05-08
Status:
- Phase 3 Slice D: accepted and closed
- Phase 3 Slice E: plan-only comparison approved

## Scope Guardrails (Hard)
- Plan only. No implementation.
- Do not move routes.
- No app factory changes.
- No lifespan/startup movement.
- No middleware changes.
- No auth/rate-limit behavior changes.
- No cleanup-only refactors.
- Public checker remains deferred unless comparison evidence is overwhelming.

## Candidate 1: Team routes

Exact route inventory with current line references (server.py):
1. GET /api/team/members (line 4001)
2. GET /api/team/members/{member_id} (line 4011)
3. POST /api/team/invite (line 4023)
4. PATCH /api/team/members/{member_id} (line 4048)
5. DELETE /api/team/members/{member_id} (line 4064)
6. GET /api/team/workload (line 4078)

Coupling/risk analysis:
- Auth coupling: mixed but coherent. 5/6 routes use Depends(get_current_agency); GET /api/team/members/{member_id} currently does not.
- Agency-scoping coupling: significant in list/update/delete/workload; one unscoped GET contract must be preserved as-is in extraction.
- Startup/lifespan coupling: none.
- Persistence/store coupling: membership_service + get_db/AsyncSession; workload uses AssignmentStore + TripStore.
- Side-effect/audit coupling: invite/update/deactivate write membership state; workload is read/compute.
- Blast radius: medium (single coherent domain cluster, 1 router + server wiring + behavior tests).
- Verification complexity: medium; route/OpenAPI parity + behavior tests for mixed scoped/unscoped pattern.

## Candidate 2: Agent runtime routes

Exact route inventory with current line references (server.py):
1. POST /run (line 1045)
2. GET /agents/runtime (line 1630)
3. POST /agents/runtime/run-once (line 1657)
4. GET /agents/runtime/events (line 1678)

Coupling/risk analysis:
- Auth coupling: all routes agency-scoped; run-once additionally requires require_permission("ai_workforce:manage").
- Agency-scoping coupling: high and security-sensitive.
- Startup/lifespan coupling: high via process-global runtime objects (_agent_supervisor, _recovery_agent).
- Persistence/store coupling: RunLedger + pipeline execution path + AuditStore event reads.
- Side-effect/audit coupling: POST /run and run-once are operationally mutating.
- Blast radius: high (runtime orchestration contracts + operational behavior).
- Verification complexity: high (parity + runtime behavior invariants + permission behavior).

## Candidate 3: Public checker routes

Exact route inventory with current line references (server.py):
1. POST /api/public-checker/run (line 981)
2. POST /api/public-checker/events (line 1010)
3. GET /api/public-checker/{trip_id} (line 1085)
4. GET /api/public-checker/{trip_id}/export (line 1098)
5. DELETE /api/public-checker/{trip_id} (line 1111)

Coupling/risk analysis:
- Auth coupling: mixed public + authenticated routes in one family.
- Agency-scoping coupling: mixed (public run/events intentionally unauthenticated; artifact routes are auth-gated).
- Startup/lifespan coupling: medium via public-checker config/service wrappers.
- Persistence/store coupling: ProductBEventStore + PublicCheckerArtifactStore + TripStore deletion path.
- Side-effect/audit coupling: high (event ingestion, artifact writes/deletes, trip deletion semantics).
- Blast radius: high.
- Verification complexity: high (rate limits, payload guards, mixed auth semantics, persistence side effects).

## Candidate 4: Small settings-read routes only (if separable)

Exact route inventory with current line references (server.py):
1. GET /api/settings (line 3486)
2. GET /api/settings/autonomy (line 3602)
3. GET /api/settings/pipeline (line 4277)
4. GET /api/settings/approvals (line 4291)

Coupling/risk analysis:
- Auth coupling: mixed. /api/settings has settings:read permission; autonomy read currently has no explicit permission gate; pipeline/approvals reads currently ungated.
- Agency-scoping coupling: partial; defaults and config stores are mixed.
- Startup/lifespan coupling: low.
- Persistence/store coupling: AgencySettingsStore + ConfigStore across split sections.
- Side-effect/audit coupling: read-only in this candidate, but tightly adjacent to write siblings.
- Blast radius: medium due non-contiguous placement and shared write-adjacent logic.
- Verification complexity: medium-high because separability is imperfect.

## Ranking
1) Team routes (best next extraction slice)
2) Small settings-read routes only (secondary, but less cleanly separable)
3) Agent runtime routes (defer)
4) Public checker routes (defer)

## Behavior-Preservation Contract for Recommended Candidate (Team)
- Preserve all current response payload shapes and status codes.
- Preserve current dependency profile exactly, including existing unscoped behavior of:
  GET /api/team/members/{member_id}
- Do not scope-harden or permission-harden in Slice E extraction.
- Any hardening for that endpoint is a separate explicit slice after extraction parity is proven.

## Router Shape Proposal (post-approval)
- New file: spine_api/routers/team.py
- router = APIRouter()
- No prefix.
- No tags unless existing OpenAPI metadata already has tags.
- No router-level dependencies.
- Keep endpoint-level dependencies identical to current contracts.

## server.py wiring plan after approval (post-approval only)
1. Add normal import path for team router.
2. Add fallback importlib path for team router (matching existing pattern).
3. Add app.include_router(team_router.router).
4. Remove only moved in-file team handlers from server.py.

## Verification matrix (post-approval)
- tests/test_server_route_parity.py
- tests/test_server_openapi_path_parity.py
- tests/test_server_startup_invariants.py
- New: tests/test_team_router_behavior.py
  - include explicit tests preserving current GET /api/team/members/{member_id} unscoped behavior
  - include list/invite/update/delete/workload parity checks

## Snapshot + hygiene checks (post-approval)
- scripts/snapshot_server_routes.py
- Expected counts pre-implementation baseline: route_count=129, openapi_path_count=113
- Forbidden import check in router module:
  grep -n "from spine_api.server\|import server" spine_api/routers/team.py
  Expected: no matches

## Non-goals
- No startup/lifespan/app-factory changes.
- No middleware/auth/rate-limit refactors.
- No runtime/public-checker/settings-write movement.
- No behavior hardening bundled into extraction.

## Stop Rule
Stop after writing this plan. Await approval before implementation.

Recommended Slice E: Team routes
Top 3 risks:
1. Accidental scoping change on GET /api/team/members/{member_id} (must preserve as-is).
2. Hidden behavior drift in workload aggregation (AssignmentStore + TripStore interactions).
3. Dependency mismatch during import wiring (normal vs fallback path parity).