# Public Checker Agency Config Hardening - 2026-05-07

## Decision
Implemented option 2: environment-configured public checker agency id with startup-time invariant validation.

## First-principles rationale
Public checker persistence in SQL mode writes `trips.agency_id` on every run. That makes agency identity a hard invariant, not a soft preference. Therefore:
1) the agency id must be explicit and configurable per environment,
2) server must fail fast before serving requests if the configured id is invalid,
3) error must be actionable (exact env var + exact missing table/row condition).

This removes runtime 500s caused by hidden config/data mismatch and moves failure to startup with clear remediation.

## Code changes

### 1) server config + validation
File: `/Users/pranay/Projects/travel_agency_agent/spine_api/server.py`

Added:
- `DEFAULT_PUBLIC_CHECKER_AGENCY_ID = "waypoint-hq"`
- `_get_public_checker_agency_id()`
- `_is_sql_tripstore_backend()`
- `_validate_public_checker_agency_configuration()`

Behavior:
- If `PUBLIC_CHECKER_AGENCY_ID` resolves empty -> startup RuntimeError.
- If `TRIPSTORE_BACKEND != sql` -> validation skipped (logged).
- If SQL mode:
  - require `agencies` table to exist,
  - require configured agency row to exist,
  - otherwise raise startup RuntimeError with remediation text.

Lifespan wiring:
- Added call in startup sequence:
  - `await _validate_public_checker_agency_configuration()`

### 2) public checker runtime usage now resolves from env
Replaced hardcoded constant use with `_get_public_checker_agency_id()` for:
- event workspace id attribution,
- agency settings load,
- persisted trip agency_id,
- run status response agency_id.

### 3) tests env alignment
File: `/Users/pranay/Projects/travel_agency_agent/tests/conftest.py`
- Added default for test runtime:
  - `PUBLIC_CHECKER_AGENCY_ID=d1e3b2b6-5509-4c27-b123-4b1e02b0bf5b`

### 4) new unit tests
File: `/Users/pranay/Projects/travel_agency_agent/tests/test_public_checker_agency_config.py`
- validates pass path when agency exists,
- validates hard fail when agency missing,
- validates skip path when backend=file,
- validates env/default resolver behavior.

## Verification evidence

### Unit/regression tests
- `TMPDIR=/private/tmp PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest -q tests/test_public_checker_agency_config.py`
  - `4 passed in 2.00s`
- `TMPDIR=/private/tmp PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest -q tests/test_agent_events_api.py tests/test_spine_pipeline_unit.py`
  - `18 passed in 3.42s`

### Startup fail-fast check (default config)
Command:
- `TMPDIR=/private/tmp PYTHONDONTWRITEBYTECODE=1 uv run uvicorn spine_api.server:app --port 8000`

Observed startup error:
- `RuntimeError: Public checker agency invariant failed: configured agency_id 'waypoint-hq' (env PUBLIC_CHECKER_AGENCY_ID) is missing from agencies table...`

This is expected and desired (fail-fast instead of runtime 500).

### Smoke rerun with explicit env config
Backend started with:
- `PUBLIC_CHECKER_AGENCY_ID=d1e3b2b6-5509-4c27-b123-4b1e02b0bf5b`

Smoke results:
- `POST /api/public-checker/run` -> `200` (state=`blocked`, trip persisted, no FK crash)
- `POST /api/public-checker/events` -> `200` for posted events
- `GET /analytics/product-b/kpis` -> `200`
- event store line growth observed (`delta=4` in rerun)

## Operational requirement
Every SQL environment must set `PUBLIC_CHECKER_AGENCY_ID` to an existing `agencies.id` (or ensure default `waypoint-hq` exists). If not, server will refuse startup by design.
