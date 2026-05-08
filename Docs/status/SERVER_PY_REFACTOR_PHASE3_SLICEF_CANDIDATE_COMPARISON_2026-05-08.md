# Server.py Refactor Phase 3 — Slice F Candidate Comparison (Plan Only)

Date: 2026-05-08
Status: Comparison-only (no implementation)

## Scope Guardrails (Hard)
- Plan/comparison only. No route movement.
- No code edits in `spine_api/server.py` or routers.
- No snapshot updates.
- No mutating git commands.
- `/run` and `/runs` are explicitly excluded from candidate inventory.
- Public checker remains deferred unless evidence is decisively stronger than alternatives.
- No hardening/cleanup bundled with extraction.

## Candidate 1: Agent runtime routes (excluding `/run`)

Exact route inventory (method + path + server.py line):
1. GET `/agents/runtime` (line 1641)
2. POST `/agents/runtime/run-once` (line 1668)
3. GET `/agents/runtime/events` (line 1689)

Auth/dependency profile:
- All 3 depend on `get_current_agency`.
- `run-once` adds `require_permission("ai_workforce:manage")`.
- Query dependencies on events endpoint (`limit`, `agent_name`, `correlation_id`).

Permission profile:
- Explicit permission on 1/3 routes (`ai_workforce:manage` on run-once).

Rate-limit decorators:
- None.

Persistence/store coupling:
- Reads/writes through `_agent_supervisor` and `_recovery_agent` process globals.
- Runtime events endpoint reads `AuditStore.get_agent_events(...)`.

Side effects/audit/events:
- `run-once` is operationally mutating: executes supervisor pass and can emit/write agent events.
- Other 2 routes are read surfaces.

Startup/lifespan/global-state coupling:
- High coupling to lifespan start/stop (`_agent_supervisor.start/stop`, `_recovery_agent.start/stop`; lines 531-542).
- Uses process-global supervisor state in handler responses.

Response models/contracts:
- No explicit `response_model` contracts on these 3 routes (dict payloads built inline).

Risk rating: High

Why should/should not be Slice F:
- Should: coherent domain cluster already grouped by `/agents/runtime` prefix.
- Should not: high global-state/lifecycle coupling and mutating `run-once` path make parity verification and rollback harder for next slice.

---

## Candidate 2: Public checker routes

Exact route inventory (method + path + server.py line):
1. POST `/api/public-checker/run` (line 988)
2. POST `/api/public-checker/events` (line 1017)
3. GET `/api/public-checker/{trip_id}` (line 1092)
4. GET `/api/public-checker/{trip_id}/export` (line 1105)
5. DELETE `/api/public-checker/{trip_id}` (line 1118)

Auth/dependency profile:
- Mixed auth model by design:
  - Public submission/event ingestion routes are unauthenticated handler inputs (`Request/Response` + payload), no agency/user dependency.
  - Artifact read/delete routes require `get_current_agency` and `get_current_user`.

Permission profile:
- No explicit `require_permission(...)` decorators in this group.

Rate-limit decorators:
- `POST /api/public-checker/run`: `@limiter.limit("12/minute")` (line 989)
- `POST /api/public-checker/events`: `@limiter.limit("30/minute")` (line 1018)

Persistence/store coupling:
- Submission path delegates to `run_public_checker_submission(...)` wrapper (`_run_public_checker_submission`, lines 973-982).
- Event ingestion writes to `ProductBEventStore.log_event(...)`.
- Artifact routes use `PublicCheckerArtifactStore` and `TripStore.delete_trip(...)`.

Side effects/audit/events:
- Writes/ingestion/deletion side effects are central to this group.
- Event endpoint is explicitly ingestion + persistence.

Startup/lifespan/global-state coupling:
- Medium: startup validates public checker agency configuration (`_validate_public_checker_agency_configuration`, line 521) and helper `_get_public_checker_agency_id` is part of submission path.

Response models/contracts:
- Explicit contracts on run/export/delete:
  - `RunStatusResponse`
  - `PublicCheckerExportResponse` (both GETs)
  - `PublicCheckerDeleteResponse`
- Event endpoint returns ad-hoc `{ok: True, ...}` payload.

Risk rating: High

Why should/should not be Slice F:
- Should: route family is prefix-coherent.
- Should not: mixed-auth semantics + rate limiting + write/delete side effects make this a higher-risk extraction than remaining read-only candidates.

---

## Candidate 3: Small settings-read routes only

Exact route inventory (method + path + server.py line):
1. GET `/api/settings` (line 3497)
2. GET `/api/settings/autonomy` (line 3613)
3. GET `/api/settings/pipeline` (line 4175)
4. GET `/api/settings/approvals` (line 4189)

Auth/dependency profile:
- `/api/settings`: explicit `require_permission("settings:read")`.
- `/api/settings/autonomy`: no explicit permission dependency.
- `/api/settings/pipeline`: no explicit permission dependency.
- `/api/settings/approvals`: no explicit permission dependency.
- No `get_current_agency` dependency on these 4 GET routes; default agency/config values are read directly.

Permission profile:
- Mixed: 1 protected route, 3 currently unguarded reads.

Rate-limit decorators:
- None.

Persistence/store coupling:
- `/api/settings*` reads from `AgencySettingsStore` (file-backed) and `ConfigStore`.

Side effects/audit/events:
- None for these 4 read routes (read-only responses).

Startup/lifespan/global-state coupling:
- Low direct lifespan coupling.
- Moderate implicit coupling to file-backed config schemas and defaults (`agency_id="waypoint-hq"`).

Response models/contracts:
- No explicit `response_model` on these 4 routes; dict contracts are inline and currently heterogeneous.

Risk rating: Medium

Why should/should not be Slice F:
- Should: read-only extraction, no rate limits, no run loop coupling, no mutation side effects.
- Should not: permission/auth inconsistency is already present in current behavior and must be preserved exactly; accidental normalization during extraction is a parity risk.

---

## Candidate 4: Product-B KPI read route group (single-route coherent slice)

Exact route inventory (method + path + server.py line):
1. GET `/analytics/product-b/kpis` (line 1042)

Auth/dependency profile:
- Depends on `get_current_agency`.
- Query params only: `window_days`, `qualified_only`.

Permission profile:
- No explicit `require_permission(...)`.

Rate-limit decorators:
- None.

Persistence/store coupling:
- Read-only compute path via `ProductBEventStore.compute_kpis(...)`.

Side effects/audit/events:
- No write side effects in handler (read-only aggregation).

Startup/lifespan/global-state coupling:
- Low: no direct lifecycle-managed runtime object usage.

Response models/contracts:
- No explicit `response_model`; payload shape comes from `ProductBEventStore.compute_kpis(...)`.

Risk rating: Low

Why should/should not be Slice F:
- Should: smallest blast radius, pure read route, no rate limiter, no mutating store path.
- Should not: single-route slice gives limited proof of repeated extraction discipline compared with a slightly larger multi-route group.

---

## Ranking (safest to riskiest for Slice F)
1) Product-B KPI read route group (Candidate 4)
2) Small settings-read routes only (Candidate 3)
3) Agent runtime routes (Candidate 1)
4) Public checker routes (Candidate 2)

## Recommendation
Recommended Slice F: Product-B KPI read route group (GET `/analytics/product-b/kpis`)

Rationale:
- Lowest coupling to startup/lifespan globals.
- No mutating side effects.
- Clean read-only semantics with a single coherent endpoint.
- Safest next repetition of router extraction mechanics before touching mixed-auth or runtime-coupled clusters.

## Top 3 risks for recommended candidate
1. Contract drift risk because endpoint has no explicit `response_model` and relies on `ProductBEventStore.compute_kpis(...)` return shape.
2. Accidental auth behavior change if extraction introduces/removes `get_current_agency` dependency wiring.
3. Over-fragmentation risk (single-route slice) reducing refactor throughput; must be balanced by keeping subsequent slice cadence disciplined.

## Stop Rule
Stop after this comparison doc. Await explicit approval before any Slice F implementation.
