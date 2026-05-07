# server.py Refactor Phase 2B Extraction Plan (Approved With Tightening)

Date: 2026-05-07
Status: APPROVED TO IMPLEMENT (after plan tightening)

## Goal
Extract authenticated `/run` orchestration from `spine_api/server.py` into a dedicated service module with zero route/startup boundary movement and zero contract drift.

## 1) New file(s)

Create:
- `spine_api/services/pipeline_execution_service.py`

No additional modules unless strictly required for test scaffolding.

## 2) Exact server.py functions to move/delegate

Delegate/move:
- `_execute_spine_pipeline(...)` -> `execute_spine_pipeline(...)` in new service
- `_update_draft_for_terminal_state(...)` may move only if behavior remains identical

Nested helpers that remain internal to service execution flow:
- `_checkpoint_result_steps(...)`
- `_stage_checkpoint(...)`

Keep in `server.py` and pass as callable:
- `_close_inherited_lock_fds(...)`

## 3) Exact functions/components that must stay in server.py

Must remain unchanged in ownership:
- Route decorators and handlers (including `/run`)
- `run_spine` route entrypoint
- `RunLedger.create(...)` inside `/run` before thread start
- Background thread creation and `thread.start()` inside `/run`
- Lifespan/startup guards
- App initialization, middleware registration, router registration
- `_get_public_checker_agency_id`
- `_validate_public_checker_agency_configuration`

## 4) Dependency passing strategy (tightened)

Hard rule:
- `pipeline_execution_service.py` must not import `spine_api.server`

Phase 2B dependency mode:
- Prefer explicit injection from `server.py` for server-resolved/fallback-sensitive dependencies.

Pass explicitly from `server.py`:
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

Allowed canonical imports in service:
- `SpineRunRequest`, `RunMeta`
- `RunLedger`, `RunState`
- `DraftStore`
- `emit_run_started`, `emit_run_completed`, `emit_run_blocked`, `emit_run_failed`
- `emit_stage_entered`, `emit_stage_completed`
- `AgencySettingsStore`
- `set_strict_mode`
- `build_live_checker_signals`
- `apply_live_checker_adjustments`, `build_consented_submission`, `collect_raw_text_sources`

Recommended service signature:
- `execute_spine_pipeline(run_id, request_dict, agency_id, user_id, *, build_envelopes, load_fixture_expectations, to_dict, close_inherited_lock_fds, save_processed_trip, trip_store, audit_store, run_spine_once_fn, logger, otel_tracer)`

## 5) Behavior preservation checklist (must remain unchanged)

1. `RunLedger.create(...)` stays in `/run` route before thread start
2. Background thread still starts from `server.py`
3. Run state transitions unchanged: queued/running/completed/blocked/failed
4. `emit_run_started/completed/blocked/failed` unchanged
5. Stage checkpoint behavior unchanged
6. Draft update behavior unchanged
7. `AuditStore.log_event("draft_process_started", ...)` unchanged
8. `save_processed_trip` payload shape unchanged for success/partial paths
9. `agency_id` and `user_id` scoping unchanged
10. strict leakage set/reset unchanged
11. `ValueError` strict leakage maps to BLOCKED
12. generic `Exception` maps to FAILED
13. `partial_intake` behavior unchanged
14. validation-invalid behavior unchanged
15. live checker adjustment remains via shared helper
16. OTel behavior preserved as-is (no semantic changes in this phase)

## 6) Tests to run after implementation

Required matrix:
- `tests/test_server_route_parity.py`
- `tests/test_server_openapi_path_parity.py`
- `tests/test_server_startup_invariants.py`
- `tests/test_spine_pipeline_unit.py`
- `tests/test_agent_events_api.py`
- `tests/test_public_checker_agency_config.py`
- `tests/test_product_b_events.py`
- `tests/test_live_checker_service.py`

Required command:
`TMPDIR=/private/tmp PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest tests/test_server_route_parity.py tests/test_server_openapi_path_parity.py tests/test_server_startup_invariants.py tests/test_spine_pipeline_unit.py tests/test_agent_events_api.py tests/test_public_checker_agency_config.py tests/test_product_b_events.py tests/test_live_checker_service.py -q`

Additional tests to add in Phase 2B:
- No-server-import guard for new service (source-level/import-level assertion)
- At least one direct service-boundary unit test using injected fakes (`run_spine_once_fn`, `save_processed_trip`, logger/tracer/persistence hooks)

Then run full suite if environment permits and report either:
- full-suite result, or
- explicit environment blocker

## 7) Explicit non-goals

- No route movement
- No app factory
- No startup/lifespan movement
- No auth/rate-limit/response model changes
- No behavior cleanup outside extraction boundary
- No unrelated security hardening
- No router decomposition (Phase 3 only)
- No public-checker service refactor in this phase

## 8) Phase 2B execution order

1. Create `pipeline_execution_service.py` with extracted flow and injected dependencies
2. Update `server.py` so thread target delegates to new service function
3. Keep `/run` route and thread lifecycle in `server.py`
4. Add no-server-import test
5. Add service-boundary fake-based test
6. Run required matrix command
7. Run full suite if feasible
8. Write Phase 2B completion doc with behavior checklist verdicts

## 9) Reporting requirements after implementation

Report must include:
1. Files changed
2. Exact `server.py` diff summary
3. Final service dependency map (explicit injected + canonical imports)
4. Behavior checklist with PASS/FAIL/UNCLEAR per item
5. Required matrix test results
6. Full-suite result or explicit reason not run
7. Explicit confirmation: no route/startup/router/app-factory movement
