# server.py Refactor — Phase 2B Completion (Authenticated /run Service Extraction)

Date: 2026-05-07
Status: Completed

## Scope executed

Executed exactly the Phase 2B extraction scope documented in:
- `Docs/status/SERVER_PY_REFACTOR_PHASE2B_EXTRACTION_PLAN_2026-05-07.md`

No scope expansion.

## 1) Files changed

Modified:
- `spine_api/server.py`

Added:
- `spine_api/services/pipeline_execution_service.py`
- `tests/test_pipeline_execution_service_boundaries.py`

Docs added:
- `Docs/status/SERVER_PY_REFACTOR_PHASE2B_COMPLETION_2026-05-07.md`

## 2) Exact server.py diff summary

- Added import:
  - `from spine_api.services.pipeline_execution_service import execute_spine_pipeline`
- Removed full in-file implementation bodies:
  - `_update_draft_for_terminal_state(...)`
  - `_execute_spine_pipeline(...)` heavy orchestration body
- Replaced with thin delegator:
  - `_execute_spine_pipeline(...)` now forwards to `execute_spine_pipeline(...)`
  - Passes explicit dependencies from `server.py` including:
    - `build_envelopes`
    - `load_fixture_expectations`
    - `_to_dict`
    - `_close_inherited_lock_fds`
    - `save_processed_trip`
    - `TripStore`
    - `AuditStore`
    - `run_spine_once`
    - `logger`
    - `_otel_tracer`
    - `RunLedger`
    - `RunState.RUNNING`
    - `DraftStore`
    - `AgencySettingsStore`
    - `set_strict_mode`
    - `build_live_checker_signals`
    - `emit_run_started/completed/failed/blocked`
    - `emit_stage_entered/completed`

## 3) Final service dependency map

Service module:
- `spine_api/services/pipeline_execution_service.py`

Direct imports in service:
- `RunMeta`, `SpineRunRequest`
- live-checker helper functions:
  - `apply_live_checker_adjustments`
  - `build_consented_submission`
  - `collect_raw_text_sources`

Injected dependencies (from server wrapper):
- execution/serialization:
  - `build_envelopes`, `load_fixture_expectations`, `to_dict`, `run_spine_once_fn`
- persistence/runtime:
  - `save_processed_trip`, `trip_store`, `audit_store`
- run lifecycle:
  - `run_ledger`, `run_state_running`, `draft_store`
  - `emit_run_started_fn`, `emit_run_completed_fn`, `emit_run_failed_fn`, `emit_run_blocked_fn`
  - `emit_stage_entered_fn`, `emit_stage_completed_fn`
- safety/config:
  - `close_inherited_lock_fds`, `agency_settings_store`, `set_strict_mode_fn`, `build_live_checker_signals_fn`
- diagnostics:
  - `logger`, `otel_tracer`

Boundary confirmation:
- `pipeline_execution_service.py` does not import `spine_api.server`.

## 4) Behavior checklist

1. RunLedger.create in `/run` before thread start: PASS
2. Background thread starts from `server.py`: PASS
3. RunLedger running/completed/blocked/failed transitions unchanged: PASS
4. emit_run_started/completed/blocked/failed unchanged: PASS
5. Stage checkpoint behavior unchanged: PASS
6. DraftStore update behavior unchanged: PASS
7. AuditStore `draft_process_started` unchanged: PASS
8. save_processed_trip payload unchanged (success/partial): PASS
9. agency_id/user_id scoping unchanged: PASS
10. strict leakage set/reset unchanged: PASS
11. ValueError strict leakage => BLOCKED: PASS
12. generic Exception => FAILED: PASS
13. partial_intake behavior unchanged: PASS
14. validation_invalid behavior unchanged: PASS
15. live checker adjustment remains shared helper: PASS
16. OTel behavior preserved as-is: PASS

## 5) Required matrix result

Command:
`TMPDIR=/private/tmp PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest tests/test_server_route_parity.py tests/test_server_openapi_path_parity.py tests/test_server_startup_invariants.py tests/test_spine_pipeline_unit.py tests/test_agent_events_api.py tests/test_public_checker_agency_config.py tests/test_product_b_events.py tests/test_live_checker_service.py -q`

Result:
- `47 passed in 2.76s`

Additional new tests:
- `tests/test_pipeline_execution_service_boundaries.py`
  - no-server-import guard via source inspection
  - direct service-boundary fake-injection test

## 6) Full-suite result

Command:
`TMPDIR=/private/tmp PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider`

Result:
- `1719 passed, 44 skipped, 3 warnings in 43.38s`
- Warnings are pre-existing runtime warnings in audit bridge tests (no failures).

## 7) Structural movement confirmation

Confirmed unchanged:
- No route movement
- No startup/lifespan movement
- No router decomposition
- No app factory introduction
- No auth/rate-limit/response model changes

## Verification command requested in review thread

Executed:
`grep -n "def _execute_spine_pipeline\|def _update_draft_for_terminal_state\|run_spine_once(" spine_api/server.py spine_api/services/pipeline_execution_service.py`

Observed shape:
- `server.py` retains thin `_execute_spine_pipeline` delegator only
- `_update_draft_for_terminal_state` is owned by service module
- service uses injected `run_spine_once_fn(...)` (no direct `run_spine_once` import)
