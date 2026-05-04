# Discussion: Unit Tests for _execute_spine_pipeline

**Date:** 2026-05-04
**Context:** ISSUE-002 from random document audit — `_execute_spine_pipeline` had zero unit tests

## Problem

`_execute_spine_pipeline()` (spine_api/server.py:862) is a 415-line function that runs every trip submission. It had **zero direct unit tests**. Only 8 HTTP integration tests existed, sharing one fixture and testing only SC-001 happy path. Every error path, edge case, and environment-specific behavior was untested.

## Coverage Added

| Test | Code Path | What It Verifies |
|------|-----------|------------------|
| `test_saves_trip_and_completes_ledger` | Happy path | RunLedger.set_state + complete called; fail/block not called |
| `test_emit_run_completed_called` | Happy path | emit_run_completed fires on success |
| `test_save_processed_trip_receives_correct_source` | Happy path | save_processed_trip gets correct source/agency_id/user_id |
| `test_early_exit_blocks_and_does_not_save_trip` | early_exit | RunLedger.block called; save_processed_trip NOT called |
| `test_partial_intake_saves_incomplete_trip` | partial_intake | Trip saved with status="incomplete"; RunLedger.complete called |
| `test_validation_invalid_blocks_trip` | validation_invalid | RunLedger.block called; trip NOT saved |
| `test_value_error_blocks_run` | ValueError (strict leakage) | RunLedger.block called, not fail |
| `test_exception_fails_run` | Generic Exception | RunLedger.fail called, not block |
| `test_consented_submission_includes_raw_text` | retention_consent=True | Raw text preserved in meta.submission |
| `test_no_consent_strips_raw_text` | retention_consent=False | Raw text stripped from meta.submission |
| `test_strict_mode_enabled_for_strict_request` | strict_leakage=True | set_strict_mode(True) is called |
| `test_strict_mode_reset_in_finally` | Error/success cleanup | set_strict_mode(False) is called in finally block |
| `test_live_checker_adjusts_score` | Live checker signals | Score adjustment path is exercised |

## Test Architecture

### Mock Strategy

All module-level dependencies are patched via a single `pytest.fixture` using `unittest.mock.patch`:

```
RunLedger        → MagicMock  (records set_state, block, fail, complete, save_step)
DraftStore       → MagicMock  (records update_run_state calls)
AuditStore       → MagicMock  (records log_event calls)
TripStore        → MagicMock  (records get_trip for feedback_reopen)
AssignmentStore  → MagicMock  (side effect not used in pipeline)
AgencySettingsStore → MagicMock (load returns settings)
save_processed_trip → return_value="trip-saved-001" (controlled trip ID)
set_strict_mode  → MagicMock  (tracks enable/disable calls)
run_spine_once   → MagicMock  (returns MockSpineResult with controllable attributes)
```

### MockSpineResult

A lightweight class mimicking the real `SpineResult` dataclass (14 fields). Defaults are set to happy-path values. Tests override attributes through constructor kwargs:

```python
MockSpineResult()                          # happy path
MockSpineResult(early_exit=True, ...)      # blocked path
MockSpineResult(partial_intake=True, ...)  # incomplete path
```

### Why Not Integration Tests

The existing 8 HTTP integration tests (`test_spine_api_contract.py`) cover the end-to-end flow but require a running server, database, and fixture files. Unit tests run in 2.7s with zero infrastructure, making them suitable for CI and TDD.

## Files

- `tests/test_spine_pipeline_unit.py` — 13 tests (new)
- `spine_api/server.py` — function under test (unchanged)

## Results

- New tests: **13 passed** (2.7s)
- All backend unit tests: **116 passed** (10.9s)
- Frontend tests: **666 passed** / 1 pre-existing failure (unchanged)
- Zero regressions

## Future Work

Potential coverage extensions (P2/P3):
- Draft ID linking path (DraftStore.update_run_state called)
- Feedback recovery trigger (feedback_reopen=True on returned trip)
- Live checker with hard_blockers and soft_blockers merging
- Pipeline span attribute assertions (otel tracing)
