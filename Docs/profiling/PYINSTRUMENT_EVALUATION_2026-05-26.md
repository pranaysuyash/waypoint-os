# Pyinstrument Evaluation (2026-05-26)

## Scope
- Repo: `/Users/pranay/Projects/travel_agency_agent`
- Tool: `pyinstrument` via ephemeral uv environment (`uv run --with pyinstrument ...`)
- Targets:
  - `tests/test_smoke_test.py`
  - `tests/test_live_checker_service.py`

## Commands Run
```bash
uv run --with pyinstrument pyinstrument -r text -m pytest tests/test_smoke_test.py -q
uv run --with pyinstrument pyinstrument -r text -m pytest tests/test_live_checker_service.py -q

mkdir -p Docs/profiling/pyinstrument
uv run --with pyinstrument pyinstrument -r html --outfile Docs/profiling/pyinstrument/smoke_test_profile.html -m pytest tests/test_smoke_test.py -q
uv run --with pyinstrument pyinstrument -r html --outfile Docs/profiling/pyinstrument/live_checker_profile.html -m pytest tests/test_live_checker_service.py -q
```

## Result Artifacts
- `Docs/profiling/pyinstrument/smoke_test_profile.html`
- `Docs/profiling/pyinstrument/live_checker_profile.html`

## Key Findings
1. The majority of runtime in both targets is test/session setup overhead rather than test body logic.
2. The dominant hotspot is fixture setup path:
   - `conftest.py: reset_global_singletons`
   - imports through `src/intake/decision.py` -> `src/decision/hybrid_engine.py` -> `src/llm/__init__.py`
3. Heavy import-time cost comes from model/type construction in:
   - `google/genai/types.py` (Pydantic model construction)
   - `openai/types/*` import tree
4. Cleanup/GC at pytest unconfigure is also visible (multi-second tail), which can mask micro-optimizations in individual tests.

## Operational Notes
- A first text run raised:
  - `FileExistsError: /Users/pranay/Library/Application Support/pyinstrument/reports`
- Using explicit `--outfile` avoided the issue and produced stable artifacts.
- Recommendation for this workspace:
  - Always run pyinstrument with explicit `--outfile` in repo-local `Docs/profiling/pyinstrument/`.

## Practical Usefulness Verdict
- Pyinstrument is useful here for identifying import/setup bottlenecks and fixture-cost drift.
- For endpoint/request-level latency, pair this with app-level profiling on real requests (FastAPI middleware profiling) to separate app runtime from pytest harness overhead.

## Request-Level Profiling (App Path, 2026-05-26)

### Why this second pass
The first pyinstrument runs were pytest-targeted and highlighted harness/import overhead. To profile request handling directly, we ran in-process ASGI requests with app lifespan enabled.

### Commands used
```bash
uv run --with pyinstrument --with asgi-lifespan python - <<'PY'
# profile /health with httpx.AsyncClient + ASGITransport + LifespanManager
PY
```

### New artifact
- `Docs/profiling/pyinstrument/request_health_async_profile.html`

### Findings from request-path profile (`/health`)
- The dominant costs are middleware and framework layers, not business logic (expected for health endpoint):
  - `SlowAPIMiddleware.dispatch` and limiter checks
  - OpenTelemetry ASGI/FastAPI instrumentation wrappers
  - Core middleware chain (`AuthMiddleware`, request size, CORS, exception middleware)
  - FastAPI dependency solve + response serialization
- The endpoint function itself is lightweight; most time is per-request plumbing.

### Additional observation
- `/runs` and `/api/system/unified-state` returned `401` in this direct request setup without auth context, so they were not used for final app-path performance conclusions in this pass.

### Practical interpretation
- For micro-endpoints like `/health`, middleware overhead dominates latency.
- For feature endpoints, next step should include authenticated request profiling (or a controlled auth fixture) so route-specific business logic can be measured separately from shared middleware baseline.

## Authenticated Endpoint Profiling (Validated Useful)

### Target and setup
- Endpoint: `GET /runs` (auth-protected)
- Auth method: real cookie session from `POST /api/auth/signup`
- Transport: in-process ASGI requests with app lifespan enabled (`asgi-lifespan` + `httpx.ASGITransport`)

### Command pattern used
```bash
uv run --with pyinstrument --with asgi-lifespan python - <<'PY'
# signup -> warmup /runs -> profile repeated /runs -> write HTML
PY
```

### New artifact
- `Docs/profiling/pyinstrument/request_runs_authenticated_profile.html`

### Why this is useful
This profile captures actual protected-route behavior rather than unauthenticated middleware baseline:
- Dominant cost in this run is route execution and dependency chain for auth context.
- `get_current_user` and `get_current_membership` DB lookups are visible in the stack.
- FastAPI dependency solving and middleware overhead are separable from endpoint body cost.

### Validation verdict
- Useful: **Yes**.
- This method provides actionable visibility for protected endpoint latency and should be used when Python request performance is under investigation.

## Hotspot Fix Pass (motto_v2-aligned)

### What was optimized
1. **Removed duplicate current-user DB fetches within a single request**
   - File: `spine_api/core/auth.py`
   - Change: added per-request cache (`request.state.current_user`) in `get_current_user`.
   - Effect: when `_auth_or_skip` and downstream dependencies both request user context, the second lookup reuses cached user instead of re-querying DB.

2. **Removed unnecessary agency object DB reads for endpoints that only need `agency_id`**
   - Files:
     - `spine_api/routers/run_status.py`
     - `spine_api/routers/inbox.py`
   - Change: replaced `Depends(get_current_agency)` with `Depends(get_current_agency_id)` and switched internal usage from `agency.id` to `agency_id`.
   - Effect: drops one DB query per request on these routes.

### Before/After profiling artifacts

- `/runs` (authenticated):
  - Before: `Docs/profiling/pyinstrument/request_runs_authenticated_profile.html`
  - After:  `Docs/profiling/pyinstrument/request_runs_authenticated_after_profile.html`
  - Observed duration for profiled request batch: **~9.892s -> ~5.611s**

- `/inbox` (authenticated):
  - Before: `Docs/profiling/pyinstrument/request_inbox_authenticated_before_profile.html`
  - After:  `Docs/profiling/pyinstrument/request_inbox_authenticated_after_profile.html`
  - Observed duration for profiled request batch: **~2.274s -> ~0.821s**

### Interpretation
- The largest measurable win came from reducing auth/dependency DB overhead and duplicate dependency work.
- Remaining dominant cost on `/runs` and `/inbox` is `run_in_threadpool` for sync endpoints plus shared middleware stack (SlowAPI, telemetry, auth/cors/exceptions).
- Further optimization should prioritize route-level business logic only after confirming whether sync endpoint execution model should remain (it currently protects event loop from blocking TripStore/ledger operations).

### Verification
- Tests run after changes:
  - `tests/test_run_status_router_behavior.py`
  - `tests/test_inbox_router_contract.py`
  - `tests/test_auth_membership_regression.py`
- Result: **12 passed**
