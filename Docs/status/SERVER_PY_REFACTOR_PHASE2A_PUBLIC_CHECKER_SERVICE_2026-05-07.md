# server.py Refactor — Phase 2A (Public Checker Service Extraction)

Date: 2026-05-07

## Objective
Extract the public-checker orchestration path out of `spine_api/server.py` into a dedicated service module, while keeping route decorators and startup/bootstrap wiring in `server.py` unchanged.

This is Phase 2-style service extraction without router movement.

## Changes made

1) New service module
- Added: `spine_api/services/public_checker_service.py`
- Extracted logic from server into service function:
  - `run_public_checker_submission(...)`
- Extracted local helpers into service module:
  - `_derive_product_b_finding_category(...)`
  - `_safe_log_product_b_event(...)`

2) server.py delegation
- Updated `spine_api/server.py`:
  - `_run_public_checker_submission(...)` now delegates to:
    - `run_public_checker_submission(...)`
  - kept route handlers in place (no route movement)
  - removed now-redundant local helper definitions for finding categorization/event-safe-log

3) test adaptation
- Updated `tests/test_product_b_events.py`:
  - `test_public_checker_run_masks_internal_errors` monkeypatch target changed from `server.run_spine_once` to `spine_api.services.public_checker_service.run_spine_once`.
  - This keeps the same behavioral assertion (internal exception detail is masked) after extraction.

## Behavior/contract expectations preserved
- `/api/public-checker/run` route signature and limiter unchanged.
- Public checker event logging semantics unchanged.
- Public checker persistence contract unchanged.
- Route/OpenAPI parity preserved (validated below).
- Startup invariant behavior unchanged (validated below).

## Verification evidence

Command executed:

`TMPDIR=/Users/pranay/Projects/travel_agency_agent PYTHONDONTWRITEBYTECODE=1 uv run pytest -q -p no:cacheprovider tests/test_live_checker_service.py tests/test_public_checker_agency_config.py tests/test_product_b_events.py tests/test_public_checker_path_safety.py tests/test_server_route_parity.py tests/test_server_openapi_path_parity.py tests/test_server_startup_invariants.py`

Result:
- `32 passed in 6.58s`

## Scope notes
- This is intentionally not router decomposition.
- Startup/bootstrap logic was not moved in this change.
- Next safe step is pending explicit review hold clearance.

## Working tree status (refactor slice only)
- Modified: `spine_api/server.py`
- Modified: `tests/test_product_b_events.py`
- Added: `spine_api/services/public_checker_service.py`

## Addendum — review hold before Phase 2B (2026-05-07)
Decision: HOLD.

Reason: sequencing discipline requires explicit review of Phase 2A extraction before any authenticated `/run` extraction.

Checklist verification status:
1. `public_checker_service` does not import `spine_api.server`: PASS
2. `server.py` remains route owner: PASS (`@app.post("/api/public-checker/run")` and `@app.post("/api/public-checker/events")` stay in server)
3. route/openapi/startup parity drift: PASS (`7 passed` on parity/invariant suite)
4. public-checker reduced persistence contract: PASS (service persists packet/validation/decision/strategy/meta only in this path)
5. Product B event names/properties unchanged: PASS (`intake_started`, `first_credible_finding_shown` with existing property contract)
6. `PUBLIC_CHECKER_AGENCY_ID` resolution centralized/unchanged: PASS (service receives callable, server owns `_get_public_checker_agency_id`)
7. strict leakage mode reset in `finally`: PASS (`set_strict_mode(False)` in service finally)
8. public checker failures masked: PASS (`HTTPException(500, "Public checker submission failed")`)
9. no private/internal compartments persisted from public checker path: PASS (`internal_bundle`/`traveler_bundle` not set by public checker service payload)
10. no duplicated live-checker adjustment implementation: PASS (single implementation in `spine_api/services/live_checker_service.py`)

Coordination rule for continuation:
- Only one agent modifies `spine_api/server.py` at a time.
- Phase 2B remains blocked until this Phase 2A review hold is explicitly lifted.

## Addendum — hold-lift precheck completed (2026-05-07)
Executed pre-Phase-2B cleanup verification commands:
- `git diff -- .gitignore`
- `git status --short`
- `git check-ignore -v pytest-of-pranay/foo`
- `git check-ignore -v data/product_b_events/events_raw.jsonl`
- `git check-ignore -v data/product_b_events/events_normalized.jsonl`

Result:
- `.gitignore` already contains:
  - `pytest-of-pranay/`
  - `pytest-of-pranay*/`
  - `data/product_b_events/*.jsonl`
- `git check-ignore -v` confirms all three ignore behaviors are active.

Additional acceptance matrix baseline run executed before Phase 2B:
- `TMPDIR=/private/tmp PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest tests/test_server_route_parity.py tests/test_server_openapi_path_parity.py tests/test_server_startup_invariants.py tests/test_spine_pipeline_unit.py tests/test_agent_events_api.py tests/test_public_checker_agency_config.py tests/test_product_b_events.py tests/test_live_checker_service.py -q`
- Result: `47 passed in 5.48s`

Conclusion:
- Phase 2A hold conditions are satisfied.
- Phase 2B may start under strict scope constraints (service-only extraction, no route/startup/router movement).
