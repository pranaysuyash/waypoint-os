# SERVER_PY_REFACTOR_STAGE_AUDIT_2026-05-07

## Scope and Method

- Objective: compare current refactor stage against original `HEAD` baseline `spine_api/server.py`, identify what is done vs pending, detect regressions/risks, and suggest improvements.
- Read method constraint followed: file inspection done via git commands only (`git diff`, `git show`, `git status`, `git diff --no-index`).
- Baseline commit used: `804d778` (current `HEAD`).

## Executive Summary

1. Refactor has progressed beyond Phase 1:
   - Phase 1 helper extraction is present.
   - Phase 2A public checker service extraction is present.
   - Phase 2B-style pipeline execution extraction has also already started (delegation to `pipeline_execution_service`), which exceeds the previously requested hold.
2. Security hardening/gates are present (parity snapshots/tests, startup invariants, product-B route hardening) and align with earlier closure docs.
3. No obvious contract-breaking regression is visible from diff-only review, but the sequencing risk is real: architectural movement happened before explicit Phase 2A code-review sign-off.

## Evidence Snapshot (git diff/status)

- `spine_api/server.py`: `76 insertions`, `723 deletions` vs `HEAD` baseline.
- `tests/test_product_b_events.py`: `231 insertions`.
- New untracked service files observed:
  - `spine_api/services/live_checker_service.py`
  - `spine_api/services/public_checker_service.py`
  - `spine_api/services/pipeline_execution_service.py`
- New parity fixtures observed (untracked):
  - `tests/fixtures/server_route_snapshot.json` with `"route_count": 129`
  - `tests/fixtures/server_openapi_paths_snapshot.json` with `"openapi_path_count": 113`

## Stage-by-Stage Assessment

### Phase 0 (Characterization + Safety Gates)

Status: **Implemented in workspace**

Evidence:
- Snapshot artifacts and tests exist:
  - `tests/fixtures/server_route_snapshot.json` (`route_count=129`)
  - `tests/fixtures/server_openapi_paths_snapshot.json` (`openapi_path_count=113`)
  - `tests/test_server_route_parity.py`
  - `tests/test_server_openapi_path_parity.py`
  - `tests/test_server_startup_invariants.py`
- Public-checker hardening surface added in `server.py`:
  - event payload max bytes guard (`413`)
  - route limiter annotations
  - auth dependencies added on public checker export/delete paths

Assessment:
- The authoritative parity baseline should now be these snapshots (129 routes / 113 openapi paths), not earlier decorator-count estimates.

### Phase 1 (Pure Helper Extraction Only)

Status: **Implemented**

Evidence:
- New helper module:
  - `spine_api/services/live_checker_service.py`
- Extracted helpers:
  - `build_consented_submission`
  - `collect_raw_text_sources`
  - `apply_live_checker_adjustments`
- `server.py` now imports and uses these helpers.
- Helper tests exist:
  - `tests/test_live_checker_service.py`

Assessment:
- Refactor intent for Phase 1 is satisfied.

### Phase 2A (Public Checker Service Extraction)

Status: **Implemented (provisionally)**

Evidence:
- New service module:
  - `spine_api/services/public_checker_service.py`
- `server.py` delegates `_run_public_checker_submission(...)` to `run_public_checker_submission(...)`.
- Service-level guards present:
  - `HTTPException(status_code=500, detail="Public checker submission failed")` masking internals.
  - `set_strict_mode(False)` in `finally`.
  - Uses shared helper (`apply_live_checker_adjustments`) rather than duplicate logic.

Assessment:
- Shape is consistent with planned Phase 2A boundary.
- Still requires explicit code-review sign-off before any Phase 2B advancement.

### Phase 2B (Authenticated `/run` Pipeline Service Extraction)

Status: **Already started (unexpected vs hold)**

Evidence:
- New module:
  - `spine_api/services/pipeline_execution_service.py`
- `server.py` now imports `execute_spine_pipeline` and delegates `_execute_spine_pipeline(...)` to service.
- Server-local `_update_draft_for_terminal_state` removed and equivalent helper exists inside service module.

Assessment:
- This is higher blast radius and should have remained on hold per prior instruction until Phase 2A code review completion.

## Regression and Risk Audit

### Potential regressions not proven from diff alone

1. Sequencing regression (process): Phase 2B extraction started before Phase 2A approval.
2. Behavioral coupling risk: moving `_execute_spine_pipeline` logic into injected-dependency service increases surface for subtle lifecycle drift (run ledger, draft linkage, stage events, strict leakage reset).
3. Route security drift risk: export/delete public-checker endpoints now include auth dependencies; likely intentional hardening, but compatibility impact should be explicitly documented.

### What appears preserved/improved

1. Public-checker error masking improved (no raw internal exception detail leakage).
2. Strict-leakage cleanup in public-checker path is explicitly preserved via `finally`.
3. Duplicate helper logic unified, reducing drift risk between authenticated and public-checker paths.
4. Product-B event API robustness improved via malformed payload and oversized payload handling tests.

## Pending Work (from current state)

1. Phase 2A formal code-review hold closure:
   - review and approve `public_checker_service.py` + server delegation diff.
2. Phase 2B gating reset:
   - either explicitly approve current extraction direction or roll back/defer pipeline service extraction to match agreed sequencing.
3. Ensure parity gates are run and recorded against current extraction state:
   - route parity
   - OpenAPI parity
   - startup invariants
   - public checker + product-B tests
   - pipeline-targeted tests
4. Commit hygiene:
   - many relevant files are still untracked/modified; no stage is truly durable until committed in coherent phase slices.

## Improvement Opportunities

1. Enforce phase gate with a CI check:
   - block introduction of `pipeline_execution_service` import in `server.py` unless Phase 2A approval marker doc is present/updated.
2. Add boundary tests that assert service modules do not import `spine_api.server` (public checker + pipeline service).
3. Consolidate dependency injection contracts into typed protocols for `pipeline_execution_service` to reduce accidental contract drift.
4. Document route-hardening decisions (auth/rate-limit/size caps) in a concise API change note to avoid silent client-impact confusion.

## Verdict

- **Phase 0:** Acceptable from evidence.
- **Phase 1:** Acceptable from evidence.
- **Phase 2A:** Technically plausible and mostly aligned, but should remain under explicit review hold until code sign-off.
- **Phase 2B:** Not approved yet; work has already begun and should be paused for review/alignment before further changes.
