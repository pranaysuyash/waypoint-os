# server.py Refactor — Phase 0 Closure Note (2026-05-07)

## 1) Exact Tests Run and Results

Project venv command:

```bash
TMPDIR=/private/tmp PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest \
  tests/test_live_checker_service.py \
  tests/test_public_checker_agency_config.py \
  tests/test_product_b_events.py \
  tests/test_public_checker_path_safety.py \
  tests/test_server_route_parity.py \
  tests/test_server_openapi_path_parity.py \
  tests/test_server_startup_invariants.py \
  tests/test_agent_events_api.py \
  tests/test_spine_pipeline_unit.py -q
```

Result:
- `50 passed in 13.15s`

Coverage included:
- Public-checker security regression tests
- Route parity tests
- Startup invariant tests
- Product B event/API tests
- Authenticated run/event targeted tests
- New Phase 1 helper unit tests

Additional repo-wide run (latest successful):

```bash
TMPDIR=/private/tmp PYTHONDONTWRITEBYTECODE=1 uv run pytest -q
```

Result:
- `1717 passed, 44 skipped, 3 warnings in 89.24s`

## 2) Exact Known Limitation

- Previous disk pressure / Errno 28 issue was real in earlier runs and was documented.
- Current state: disk-pressure blocker is cleared for this session; no Errno 28 in the latest full-suite execution.
- Remaining caveat is environmental/sandbox variability for DB-backed tests if run without required local permissions.

## 3) Confirmation server.py is still monolithic (Phase 0 boundary preserved)

- No route movement.
- No app factory movement.
- No startup/bootstrap relocation.
- No service extraction of `_execute_spine_pipeline`.
- No service extraction of `_run_public_checker_submission`.
- `server.py` behavior remains intact except safe delegation to pure helper functions (Phase 1 scope).

## 4) Confirmation of Current Gates

- Route parity snapshot exists:
  - `tests/fixtures/server_route_snapshot.json`
- OpenAPI path snapshot exists:
  - `tests/fixtures/server_openapi_paths_snapshot.json`
- Parity gate tests exist:
  - `tests/test_server_route_parity.py`
  - `tests/test_server_openapi_path_parity.py`
- Startup invariant tests exist:
  - `tests/test_server_startup_invariants.py`
- Public/private public-checker behavior is tested:
  - `tests/test_product_b_events.py`
  - `tests/test_public_checker_path_safety.py`

## Phase 1 Scope Discipline Confirmation

Implemented Phase 1 is pure helper extraction only:
- `build_consented_submission`
- `collect_raw_text_sources`
- `apply_live_checker_adjustments`

Explicitly not done in Phase 1:
- No route decorator movement
- No lifespan/startup guard movement
- No `app_factory` introduction
- No `_execute_spine_pipeline` service extraction
- No `_run_public_checker_submission` service extraction
- No endpoint signature/response/auth/rate-limit/audit contract changes
