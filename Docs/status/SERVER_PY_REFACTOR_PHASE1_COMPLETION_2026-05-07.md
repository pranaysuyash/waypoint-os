# server.py Refactor Phase 1 Completion (2026-05-07)

## Scope
Implement Phase 1 only (pure helper extraction) after Phase 0 gates, with no route movement and no startup/bootstrap relocation.

## Deliverables Completed

1. New helper module:
   - `spine_api/services/live_checker_service.py`
   - Extracted pure helpers:
     - `build_consented_submission`
     - `collect_raw_text_sources`
     - `apply_live_checker_adjustments`

2. `server.py` integration:
   - `_execute_spine_pipeline` now delegates duplicated helper logic to `live_checker_service`.
   - `_run_public_checker_submission` now delegates duplicated helper logic to `live_checker_service`.
   - No route decorators moved.
   - No startup/lifespan logic moved.

3. Unit tests added:
   - `tests/test_live_checker_service.py`
   - Coverage includes:
     - consent-redaction behavior
     - raw text assembly behavior
     - live checker score adjustment and blocker merge behavior
     - decision-state fallback scoring behavior

## Verification

Command:

```bash
TMPDIR=/private/tmp PYTHONDONTWRITEBYTECODE=1 uv run pytest \
  tests/test_live_checker_service.py \
  tests/test_public_checker_agency_config.py \
  tests/test_product_b_events.py \
  tests/test_server_route_parity.py \
  tests/test_server_openapi_path_parity.py \
  tests/test_server_startup_invariants.py -q
```

Result:
- `29 passed in 5.73s`

## Review Readiness

- Phase 0 status: complete (already present before this change set).
- Phase 1 status: complete (this change set).
- Safe to request secondary architecture review for Phase 1 output and Phase 2 sequencing.
