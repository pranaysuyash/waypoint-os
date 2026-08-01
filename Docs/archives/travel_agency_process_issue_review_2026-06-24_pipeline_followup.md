# Travel Agency Process Issue Review - 2026-06-24 Pipeline Follow-Up

## Archive Note

Archived on 2026-06-30. The pipeline follow-up items in this document are closed, and this copy is kept only for historical reference.

## Scope

This follow-up covers the review feedback on:

- `spine_api/services/pipeline_execution_service.py`
- `spine_api/server.py`
- `src/intake/orchestration.py`
- `src/intake/strategy.py`
- `src/intake/safety.py`
- the public-checker live-check path

The goal was to close the remaining architectural gaps, not just make the files compile.

## What Was Fixed

- Live-check finalization now runs through a shared canonical helper instead of wrapper-specific post-processing.
- `run_spine_once()` now accepts a result finalizer and a request-scoped `strict_leakage` flag.
- Traveler-safe bundle enforcement now uses the request-scoped strict flag instead of mutable process-global toggles.
- The OTel span in `pipeline_execution_service.py` now wraps the actual pipeline work.
- The terminal-state logic no longer hangs under the `hasattr(result, "packet")` guard.
- The strict-leakage path no longer depends on `set_strict_mode()` in the FastAPI worker path.

## Verification

Completed checks:

- `python -m py_compile src/intake/orchestration.py src/intake/strategy.py src/intake/safety.py spine_api/services/live_checker_service.py spine_api/services/pipeline_execution_service.py spine_api/services/public_checker_service.py spine_api/server.py tests/test_pipeline_execution_service_boundaries.py tests/test_spine_pipeline_unit.py`
- `uv run pytest tests/test_pipeline_execution_service_boundaries.py tests/test_spine_pipeline_unit.py tests/test_live_checker_service.py tests/test_run_lifecycle.py -q`

Result:

- `53 passed`

## Notes

- The repo still contains other pre-existing modified files outside this follow-up slice.
- The strict-leakage behavior is now owned by the request/pipeline contract instead of a shared mutable toggle.
- The no-packet regression is covered by a targeted boundary test so the run cannot get stranded in a non-terminal state.
- `SpineRunRequest.strict_leakage` defaults to `False` and `TripPatchRequest` forbids unknown fields, matching the current backend contract boundary.
