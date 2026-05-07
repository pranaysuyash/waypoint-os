# SERVER_PY_REFACTOR_PHASE0_BASELINE_2026-05-07

## Purpose
Freeze pre-refactor behavior for `spine_api/server.py` before any extraction work.

## Baseline Artifacts

1. Route snapshot generator
- `scripts/snapshot_server_routes.py`

2. Route parity snapshot fixture
- `tests/fixtures/server_route_snapshot.json`
- Baseline count: `route_count = 129`

3. OpenAPI path parity snapshot fixture
- `tests/fixtures/server_openapi_paths_snapshot.json`
- Baseline count: `openapi_path_count = 113`

4. Parity gates
- `tests/test_server_route_parity.py`
- `tests/test_server_openapi_path_parity.py`

5. Startup invariant characterization
- `tests/test_server_startup_invariants.py`
- Matrix covered:
  - file backend skip path
  - SQL agencies table missing (fail-fast)
  - SQL agency missing (fail-fast)
  - SQL agency exists (success)
  - SQL unexpected DB exception (wrapped fail-fast)

## Public Checker Non-Prod Config Lock (Phase 0 dependency hardening)

- Canonical non-prod agency id selected:
  - `d1e3b2b6-5509-4c27-b123-4b1e02b0bf5b`
- Default updated in `spine_api/server.py` (`DEFAULT_PUBLIC_CHECKER_AGENCY_ID`)
- Deployment/env templates updated:
  - `.env.example`
  - `render.yaml`
  - `fly.toml`
- SQL bootstrap seeder added:
  - `scripts/bootstrap_public_checker_agency.py`
- Local dev SQL bootstrap integrated:
  - `dev.sh` runs migration + bootstrap when `TRIPSTORE_BACKEND=sql`

## Verification Evidence

Executed:

1) Snapshot generation
- Command:
  - `TMPDIR=/private/tmp PYTHONDONTWRITEBYTECODE=1 uv run python scripts/snapshot_server_routes.py --write`
- Result:
  - success
  - route_count 129
  - openapi_path_count 113

2) Phase-0 test gates + Product B endpoint/API tests
- Command:
  - `TMPDIR=/private/tmp PYTHONDONTWRITEBYTECODE=1 uv run pytest tests/test_public_checker_agency_config.py tests/test_product_b_events.py tests/test_server_route_parity.py tests/test_server_openapi_path_parity.py tests/test_server_startup_invariants.py -q`
- Result:
  - `21 passed in 3.00s`

## Notes
- This document is the reference baseline for refactor diffs.
- Any route or OpenAPI drift must be explicit and accompanied by intentional fixture updates.
- Missing evidence is treated as UNCLEAR, not PASS.
