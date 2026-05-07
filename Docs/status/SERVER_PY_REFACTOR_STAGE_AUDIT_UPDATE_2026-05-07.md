# SERVER_PY_REFACTOR_STAGE_AUDIT_UPDATE_2026-05-07

## Recheck Scope

- Recheck request: compare current refactor stage vs original `server.py` baseline and update status.
- Constraint followed: used git commands to read files (`git status`, `git diff`, `git show`).
- Current baseline commit: `d3d0554`.

## Delta from Previous Audit

Previous audit flagged that extraction had progressed beyond expected hold and was still in workspace/uncommitted flow.

After recheck:
- Refactor files are now in `HEAD` (committed baseline).
- Current working tree has no refactor-file drift; only `.gitignore` is modified plus one new planning doc.
- Therefore, the “uncommitted extraction drift” concern is closed for now.

## Current State (Authoritative as of `d3d0554`)

### server.py footprint
- `spine_api/server.py` line count at `HEAD`: `4474`.
- This is reduced from earlier `~5249` baseline.

### Stage completion map

1. Phase 0 (safety gates): **Present**
   - `tests/fixtures/server_route_snapshot.json`: `"route_count": 129`
   - `tests/fixtures/server_openapi_paths_snapshot.json`: `"openapi_path_count": 113`
   - Gate tests present:
     - `tests/test_server_route_parity.py`
     - `tests/test_server_openapi_path_parity.py`
     - `tests/test_server_startup_invariants.py`

2. Phase 1 (pure helpers): **Present**
   - `spine_api/services/live_checker_service.py`
   - helpers:
     - `build_consented_submission`
     - `collect_raw_text_sources`
     - `apply_live_checker_adjustments`
   - tests:
     - `tests/test_live_checker_service.py`

3. Phase 2A (public checker service extraction): **Present**
   - `spine_api/services/public_checker_service.py`
   - `server.py` delegates `_run_public_checker_submission(...)` to service
   - key safeguards present in service:
     - masked error: `HTTPException(status_code=500, detail="Public checker submission failed")`
     - strict reset in `finally`: `set_strict_mode(False)`

4. Phase 2B-style extraction (pipeline execution): **Present**
   - `spine_api/services/pipeline_execution_service.py`
   - `server.py` delegates `_execute_spine_pipeline(...)` to service
   - service boundary test present:
     - `tests/test_pipeline_execution_service_boundaries.py`
     - includes no-import-of-`server` assertion and strict reset path assertion.

## Regression Check (git evidence-based)

### What looks improved

1. Duplication reduction:
   - shared live-checker logic is centralized.
2. Public checker hardening:
   - explicit event payload size limit (`413` path) and route-level tests.
3. Error hygiene:
   - internal errors masked in public checker flow.
4. Runtime artifact hygiene:
   - `.gitignore` contains:
     - `pytest-of-pranay/`
     - `pytest-of-pranay*/`
     - `data/product_b_events/*.jsonl`

### What still needs caution

1. Blast radius remains high for pipeline extraction:
   - RunLedger state transitions, draft updates, event emission, and persistence all moved behind service injection seams.
2. Phase labeling/doc consistency:
   - ensure docs do not describe Phase 2B as pending if code is already extracted in `HEAD`.
3. Behavioral proof should stay test-first:
   - parity/startup/public-checker tests must remain mandatory before any Phase 3 movement.

## Pending vs Done (Updated)

### Done
- Phase 0 implemented with parity baselines and tests.
- Phase 1 implemented with helper extraction and tests.
- Phase 2A implemented with service delegation and masking/reset safeguards.
- Pipeline service extraction already present in `HEAD`.

### Pending
- Formal approval checkpoint for extracted pipeline service path (if governance requires Phase 2A sign-off before 2B).
- Next-phase refactor work should be explicitly sliced and re-baselined from `d3d0554`.

## Recommended Next Step

Before any additional refactor:
1. Freeze this state as the new architectural baseline (`d3d0554`).
2. Update stage docs to reflect that Phase 2B-style extraction is already present.
3. Require the existing parity + startup + public checker + pipeline boundary tests as gate set for the next slice.
