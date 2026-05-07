# server.py Refactor Review (2026-05-07)

## Why this review
`spine_api/server.py` has become a high-blast-radius file. It now mixes app bootstrap, startup migrations/guards, route definitions, pipeline orchestration, product-B instrumentation, and domain operations.

## Current state snapshot (evidence)
- File: `spine_api/server.py`
- Total lines: 5249
- Route decorators in file: 105
- Top route groups:
  - `/api/*`: 37
  - `/trips/*`: 33
  - `/analytics/*`: 15
- Largest top-level blocks:
  - `_execute_spine_pipeline`: 415 lines
  - `_run_public_checker_submission`: 266 lines
  - `patch_trip`: 159 lines
  - `get_trip_timeline`: 129 lines

## Structural problems (root-cause level)
1. **Too many responsibilities in one module**
   - Bootstrapping, env/runtime setup, middleware wiring, startup schema guards, route handlers, and orchestration logic all co-located.
2. **Cross-path duplication**
   - Public checker path and main run path duplicate logic for:
     - consented submission shaping
     - raw text assembly
     - live checker score/blocker adjustment
     - result packaging/persistence scaffolding
3. **HTTP concerns and domain concerns are interwoven**
   - Route handlers contain orchestration and data-shaping logic that should live in service layer.
4. **Large mutable scope and implicit coupling**
   - Global stores/services and helper functions increase accidental coupling and regression risk.

## Non-negotiables for refactor
- No behavior regression for existing endpoints and contracts.
- Keep fail-fast startup invariant for `PUBLIC_CHECKER_AGENCY_ID` in SQL mode.
- Preserve current auth semantics, rate limits, and event/audit side effects.
- Preserve additive documentation trail under `Docs/`.
- Use phased extraction, not rewrite.

## Target architecture (incremental)
1. `spine_api/app_factory.py`
   - FastAPI app construction, middleware, router registration.
2. `spine_api/bootstrap/startup.py`
   - lifespan/startup checks:
     - agencies/memberships schema compatibility
     - public-checker agency invariant validator
3. `spine_api/services/pipeline_execution_service.py`
   - extracted from `_execute_spine_pipeline`
   - run lifecycle, checkpointing, completion/block/fail transitions
4. `spine_api/services/public_checker_service.py`
   - extracted from `_run_public_checker_submission`
   - product-B flow, event emissions, persistence mapping
5. `spine_api/services/live_checker_service.py`
   - shared pure helpers for score adjustment and blocker merging
6. `spine_api/routes/*.py` routers
   - move route groups out of `server.py`:
     - `routes/public_checker.py`
     - `routes/runs.py`
     - `routes/trips.py`
     - `routes/analytics.py`
     - `routes/followups.py`
     - `routes/settings.py`

## Phase plan (safe order)

### Phase 1: Pure helper extraction (lowest risk)
Extract duplication-only pure functions first:
- `build_consented_submission(request_dict, retention_consent)`
- `collect_raw_text_sources(request)`
- `apply_live_checker_adjustments(packet, validation, decision, raw_text)`

Acceptance:
- No endpoint signature changes.
- Existing tests pass unchanged.
- Add unit tests for extracted pure helpers.

### Phase 2: Service extraction without route movement
Move function bodies into services but keep route decorators in `server.py` delegating to services.

Acceptance:
- Endpoint behavior unchanged.
- `tests/test_public_checker_agency_config.py` and Product B tests still pass.
- Run smoke for:
  - `/api/public-checker/run`
  - `/api/public-checker/events`
  - `/analytics/product-b/kpis`

### Phase 3: Router decomposition
Move route groups to `APIRouter` modules and include from app factory.

Acceptance:
- Route table parity (count/path/method).
- Auth dependencies unchanged.
- No diff in OpenAPI path set except ordering.

### Phase 4: Startup/bootstrap isolation
Move lifespan and startup guards into `bootstrap/startup.py`; keep behavior identical.

Acceptance:
- Misconfigured SQL startup still fails fast with same actionable error.
- Correctly configured startup still passes health check.

### Phase 5: Cleanup and hard boundaries
- Trim `server.py` to thin composition entrypoint.
- Enforce “no business logic in route handlers” rule.

Acceptance:
- `server.py` reduced to app assembly and glue only.
- No regression in full backend tests + smoke.

## Regression harness required each phase
1. Targeted tests:
   - `tests/test_public_checker_agency_config.py`
   - `tests/test_product_b_events.py`
   - `tests/test_agent_events_api.py`
   - `tests/test_spine_pipeline_unit.py`
2. Contract checks:
   - route parity snapshot (method/path)
   - startup invariant checks (fail-fast + success path)
3. Smoke checks:
   - backend health
   - public checker run/event
   - product-B KPI endpoint

## Risks and controls
- Risk: hidden side-effect ordering changes.
  - Control: move logic with characterization tests first, then extract.
- Risk: auth dependency drift when moving routers.
  - Control: snapshot dependency wiring and verify path-by-path.
- Risk: startup validator drift.
  - Control: explicit tests for empty env / missing agency / existing agency.

## Recommended immediate execution slice
Start with **Phase 1 only** in next change set. Do not combine Phase 1+2 in one PR.

## Addendum A (external secondary review integration, 2026-05-07)
An external review challenged sequencing and recommended a stricter pre-refactor gate. We are adopting that correction.

Adopted changes to plan:
1. Add **Phase 0: characterization + safety harness** before any extraction.
2. Invert early service extraction order:
   - Extract public checker service first.
   - Extract full authenticated pipeline service after that.
3. Delay router decomposition until route/auth/rate-limit parity is mechanically proven.

### Phase 0 (new, mandatory)
Deliverables:
- `scripts/snapshot_server_routes.py`
- `tests/test_server_route_parity.py`
- `tests/test_server_startup_invariants.py`
- Route/OpenAPI snapshot artifact under docs/tests snapshots

Hard gates before Phase 1:
- Route parity proven (method/path + response model + dependency class + public/private classification).
- Startup invariant proven:
  - file backend skip path
  - SQL missing table fail-fast
  - SQL missing agency fail-fast
  - empty agency id fail-fast
  - valid agency startup success

### Execution policy update
- Missing evidence is **UNCLEAR**, never PASS.
- No route movement in same PR as first helper extraction.
- No startup/bootstrap relocation before Phase 0 tests pass.
