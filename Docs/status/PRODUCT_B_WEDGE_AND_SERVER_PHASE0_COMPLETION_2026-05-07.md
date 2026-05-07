# Product B + server.py Phase-0 Completion Log (2026-05-07)

## Scope Completed

Completed all queued items:
- pb-next-1
- pb-next-2
- pb-next-3
- pb-next-4
- pb-next-5
- srv-refactor-p0-1
- srv-refactor-p0-2
- srv-refactor-p0-3
- srv-refactor-p0-4

## What Changed

### Config / deployment / bootstrap hardening
- `.env.example`
  - added canonical `PUBLIC_CHECKER_AGENCY_ID`
  - added SQL preflight query requirement comment
- `render.yaml`
  - added `PUBLIC_CHECKER_AGENCY_ID`
  - added `preDeployCommand` for migration + bootstrap seed
- `fly.toml`
  - added `PUBLIC_CHECKER_AGENCY_ID`
  - added `release_command` for migration + bootstrap seed
- `dev.sh`
  - SQL-mode startup now runs:
    - `alembic upgrade head`
    - `scripts/bootstrap_public_checker_agency.py`
- `scripts/bootstrap_public_checker_agency.py`
  - new idempotent SQL bootstrap for canonical public-checker agency row

### Canonical non-prod agency selection
- `spine_api/server.py`
  - `DEFAULT_PUBLIC_CHECKER_AGENCY_ID` set to:
    - `d1e3b2b6-5509-4c27-b123-4b1e02b0bf5b`
- `tests/test_public_checker_agency_config.py`
  - default expectation updated accordingly

### API-level test coverage added
- `tests/test_product_b_events.py`
  - `/api/public-checker/run` is verified public (auth bypass preserved)
  - `/api/public-checker/run` rejects unknown fields (422)
  - `/api/public-checker/events` malformed payload rejection (422)
  - `/analytics/product-b/kpis` auth-failure checks (401 invalid/missing)
  - KPI visibility check for observed/inferred/unknown + dark_funnel_rate

### Refactor safety gates (Phase 0)
- `scripts/snapshot_server_routes.py`
  - generates route/openapi snapshots
- `tests/fixtures/server_route_snapshot.json`
  - baseline `route_count = 129`
- `tests/fixtures/server_openapi_paths_snapshot.json`
  - baseline `openapi_path_count = 113`
- `tests/test_server_route_parity.py`
  - route parity gate
- `tests/test_server_openapi_path_parity.py`
  - OpenAPI path parity gate
- `tests/test_server_startup_invariants.py`
  - startup invariant matrix in SQL/file modes
- `Docs/status/SERVER_PY_REFACTOR_PHASE0_BASELINE_2026-05-07.md`
  - baseline evidence doc

### Runbook / docs updates
- `Docs/operations/MULTI_AGENT_BACKEND_OPERATIONS_RUNBOOK_2026-05-04.md`
  - added SQL startup preflight section for `PUBLIC_CHECKER_AGENCY_ID`
- `Docs/DEPLOYMENT.md`
  - added required env + bootstrap + SQL preflight steps
- `Docs/TRAVEL_AGENCY_TODO.md`
  - marked all nine queued items complete

## Verification Evidence

### A) Focused new/changed tests
Command:
- `TMPDIR=/private/tmp PYTHONDONTWRITEBYTECODE=1 uv run pytest tests/test_public_checker_agency_config.py tests/test_product_b_events.py tests/test_server_route_parity.py tests/test_server_openapi_path_parity.py tests/test_server_startup_invariants.py -q`
Result:
- `21 passed`

### B) Full backend sweep
Command:
- `TMPDIR=/private/tmp PYTHONDONTWRITEBYTECODE=1 uv run pytest -q`
Result:
- `1706 passed, 44 skipped, 3 warnings`

### C) Frontend verification
- `npm run lint` script is absent in this repo’s frontend package.
- Lint-equivalent static check executed:
  - `npx tsc -p tsconfig.json --noEmit` (from `frontend/`) -> pass
- Build executed:
  - `npm run build` (from `frontend/`) -> pass

### D) SQL-seeded end-to-end smoke
1) DB/bootstrap
- `uv run alembic upgrade head` -> pass
- `uv run python scripts/bootstrap_public_checker_agency.py` -> pass (`seeded=false`, row already present)

2) Runtime smoke (SQL mode backend on port 8001)
- `/health` -> 200
- `POST /api/public-checker/run` -> 200
- `POST /api/public-checker/events` -> 200
- `POST /api/auth/login` -> 200 (cookie transport)
- `GET /analytics/product-b/kpis?window_days=30&qualified_only=true` with auth cookies -> 200

## Conclusion
All nine queued tasks are complete with code + tests + docs + verification evidence.
