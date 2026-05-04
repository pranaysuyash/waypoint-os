# Multi-Agent Runtime Test Evidence Matrix — 2026-05-04

## Latest Continuation Verification
1. `uv run python -m py_compile src/agents/events.py src/agents/recovery_agent.py src/agents/tool_contracts.py src/agents/live_tools.py src/agents/runtime.py spine_api/persistence.py spine_api/server.py tools/run_multi_agent_runtime_scenarios.py`
   - Result: success
2. `uv run pytest tests/test_agent_runtime.py tests/test_agent_events_api.py tests/test_recovery_agent.py -q`
   - Result: `38 passed in 21.52s`
   - Note: pytest printed the passing result but stayed alive in this environment; PIDs `5821` and `5825` were killed after pass output was captured.
3. `uv run python tools/run_multi_agent_runtime_scenarios.py`
   - Result: success; refreshed `Docs/status/MULTI_AGENT_RUNTIME_SCENARIO_EVIDENCE_2026-05-04.md`
4. `TRAVEL_AGENT_ENABLE_LIVE_TOOLS=1 uv run python -c "...build_weather_tool_from_env().current_conditions('Singapore')..."`
   - Result: success; returned `open_meteo_weather`, source `open_meteo`, fresh `True`, requested location `Singapore`, provider match `Temasek`, and non-empty precipitation probability data.
5. `uv run pytest tests/test_agent_runtime.py -q`
   - Result: `28 passed in 0.63s` after supplier/GDS implementation.
6. `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -c "import src.agents.runtime; import src.agents.live_tools; import spine_api.models.agent_work; import spine_api.services.agent_work_coordinator; print('imports_ok')"`
   - Result: `imports_ok` after durable SQL coordinator additions.
7. `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -s tests/test_agent_runtime.py tests/test_recovery_agent.py -q`
   - Result: `33 passed in 1.14s`
8. `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python tools/run_multi_agent_runtime_scenarios.py`
   - Result: success; refreshed `Docs/status/MULTI_AGENT_RUNTIME_SCENARIO_EVIDENCE_2026-05-04.md`
9. `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -s tests/test_agent_runtime.py tests/test_recovery_agent.py tests/test_agent_tripstore_adapter.py -q`
   - Result: `34 passed in 7.62s`
10. `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=spine_api:src:. .venv/bin/python -c "import server; print('server_import_ok')"`
   - Result: `server_import_ok`
11. `npm test -- src/lib/__tests__/bff-trip-adapters.test.ts src/lib/__tests__/route-map.test.ts --run`
   - Result: `20 passed`; verifies the BFF preserves backend product-agent operation packets and the catch-all proxy maps canonical runtime/event routes.
12. `npm run build`
   - Result: success; Next.js production build and TypeScript completed after adding the Agent Operations panel and refresh action.
13. `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -s tests/test_live_tools.py tests/test_agent_runtime.py tests/test_recovery_agent.py tests/test_agent_tripstore_adapter.py -q`
   - Result: `40 passed in 1.44s`; verifies configured HTTP flight, price, safety, State Department safety normalization, deterministic fallbacks, runtime agent behavior, recovery, and TripStore adapter hardening.
14. `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python tools/run_multi_agent_runtime_scenarios.py`
   - Result: success; refreshed `Docs/status/MULTI_AGENT_RUNTIME_SCENARIO_EVIDENCE_2026-05-04.md`.
15. `UV_CACHE_DIR=/private/tmp/uv-cache uv run alembic upgrade head`
   - Result: success with elevated local DB access; applied `add_agent_work_leases` and then the existing pending RLS migration in the local database.
16. Preview checks:
   - `curl -sS http://localhost:8000/health` returned `status: ok` with LLM unavailable.
   - `curl -sS -o /dev/null -w "%{http_code}" http://127.0.0.1:3000` returned `200`.
   - `curl -sS http://127.0.0.1:8000/agents/runtime` outside sandbox returned `{"detail":"Not authenticated"}`, confirming the route is reachable and auth-protected.
17. `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -s tests/test_persistence_runtime_boundaries.py tests/test_live_tools.py tests/test_agent_runtime.py tests/test_recovery_agent.py tests/test_agent_tripstore_adapter.py -q`
   - Result: `41 passed in 9.07s`; verifies stale audit-lock recovery, configured live-tool adapters, runtime agents, recovery, and TripStore adapter hardening.
18. `cd /Users/pranay/Projects/travel_agency_agent && UV_CACHE_DIR=/private/tmp/uv-cache uv run uvicorn spine_api.server:app --port 8010`
   - Result: startup completed cleanly with local Postgres enabled after the serialized SQL bridge, loop-local TripStore engine, and stale lock fixes.
   - `curl -sS http://127.0.0.1:8010/health` returned `status: ok` with LLM unavailable.
   - `curl -sS http://127.0.0.1:8010/agents/runtime` returned `{"detail":"Not authenticated"}`, confirming runtime route reachability and auth protection.
   - Runtime/recovery startup scans ran without the earlier asyncpg `bound to a different event loop` crash. The server still prints repeated `Decryption failed` messages for existing encrypted rows that cannot be decrypted with the current local key; this is separate data/key hygiene, not Postgres connectivity.
19. `npm test -- src/lib/__tests__/bff-trip-adapters.test.ts src/lib/__tests__/route-map.test.ts --run`
   - Result: `20 passed`; confirms restored inbox adapter exports, agent-operation packet preservation, and canonical runtime route mapping.
20. `npm run build`
   - Result: success; Next.js production build and TypeScript completed after final packet panel/route map changes.

## Blocked Verification

- `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -s tests/test_agent_runtime.py tests/test_agent_events_api.py tests/test_recovery_agent.py -q`
  - Result: `33 passed, 5 errors`; the 5 errors were all FastAPI `session_client` startup failures from local PostgreSQL socket access being blocked by the sandbox (`PermissionError: Operation not permitted`).
  - Escalated pytest rerun was requested and rejected, so API event-route pytest verification could not be refreshed in this sandbox. Direct local server/curl verification outside the sandbox confirmed backend route reachability.
- `uv run ...` verification could not be used after the durable coordinator pass because the root volume/temp directory is full (`No space left on device`). Direct Python with `-s` and `PYTHONDONTWRITEBYTECODE=1` was used for non-DB verification.

## Executed Verification Commands
1. `uv run pytest -q tests/test_agent_runtime.py tests/test_agent_events_api.py tests/test_recovery_agent.py tests/test_run_lifecycle.py tests/test_run_contract_drift_guard.py tests/test_partial_intake_lifecycle.py tests/test_singapore_canonical_regression.py tests/test_realworld_scenarios_v02.py`
   - Result: `72 passed in 32.70s`
2. `python -m py_compile src/agents/runtime.py src/agents/events.py src/agents/recovery_agent.py spine_api/server.py spine_api/persistence.py`
   - Result: success

## Requirement-to-Test Mapping

### Runtime primitives
- Registry definitions exposed
  - `tests/test_agent_runtime.py::test_default_registry_exposes_operational_product_agents_beyond_recovery`
- Supervisor execution pass
  - `tests/test_agent_runtime.py::test_happy_path_orchestration_runs_both_product_agents`
- Ownership collision prevention + idempotent re-entry
  - `tests/test_agent_runtime.py::test_ownership_collision_prevention_and_idempotent_reentry`
- Retry semantics
  - `tests/test_agent_runtime.py::test_transient_dependency_failure_retries_then_succeeds`
- Terminal/poison escalation
  - `tests/test_agent_runtime.py::test_terminal_failure_poisons_and_escalates_after_retry_budget`

### Product agent behavior
- Front-door classification
  - `tests/test_agent_runtime.py::test_front_door_agent_classifies_incomplete_inquiry_and_drafts_acknowledgment`
- Sales activation follow-up scheduling
  - `tests/test_agent_runtime.py::test_sales_activation_agent_schedules_follow_up_for_idle_lead`
- Document readiness checklist
  - `tests/test_agent_runtime.py::test_document_readiness_agent_builds_visa_passport_transit_checklist`
- Destination intelligence freshness-aware behavior
  - `tests/test_agent_runtime.py::test_destination_intelligence_agent_attaches_fresh_weather_snapshot`
  - `tests/test_agent_runtime.py::test_destination_intelligence_agent_refuses_stale_weather_as_current_evidence`
- Weather pivot behavior
  - `tests/test_agent_runtime.py::test_weather_pivot_agent_builds_activity_and_transfer_pivot_packet`
  - `tests/test_agent_runtime.py::test_weather_pivot_agent_refuses_stale_destination_evidence`
- Constraint feasibility behavior
  - `tests/test_agent_runtime.py::test_constraint_feasibility_agent_flags_hard_and_soft_blockers`
  - `tests/test_agent_runtime.py::test_constraint_feasibility_agent_skips_when_current_assessment_exists`
- Proposal readiness behavior
  - `tests/test_agent_runtime.py::test_proposal_readiness_agent_blocks_thin_or_risky_proposal`
  - `tests/test_agent_runtime.py::test_proposal_readiness_agent_marks_complete_proposal_reviewable`
- Booking readiness behavior
  - `tests/test_agent_runtime.py::test_booking_readiness_agent_blocks_missing_traveler_and_payer_data`
  - `tests/test_agent_runtime.py::test_booking_readiness_agent_marks_complete_data_ready_for_human_booking`
- Flight status behavior
  - `tests/test_agent_runtime.py::test_flight_status_agent_attaches_delay_snapshot_and_escalates`
- Ticket price watch behavior
  - `tests/test_agent_runtime.py::test_ticket_price_watch_agent_flags_quote_drift`
- Safety alert behavior
  - `tests/test_agent_runtime.py::test_safety_alert_agent_attaches_alert_packet`
- Supplier/GDS behavior
  - `tests/test_agent_runtime.py::test_gds_schema_bridge_agent_normalizes_provider_records`
  - `tests/test_agent_runtime.py::test_pnr_shadow_agent_flags_name_mismatch`
  - `tests/test_agent_runtime.py::test_supplier_intelligence_agent_flags_low_reliability_supplier`
- Quality escalation behavior
  - `tests/test_agent_runtime.py::test_quality_agent_escalates_high_suitability_flags`

### Runtime observability and APIs
- Trip-scoped agent events API
  - `tests/test_agent_events_api.py::test_get_trip_agent_events_filters_and_returns_payload`
  - `tests/test_agent_events_api.py::test_get_trip_agent_events_enforces_agency_scope`
- Runtime introspection API
  - `tests/test_agent_events_api.py::test_get_agent_runtime_returns_registry_and_health`
- Manual runtime pass API
  - `tests/test_agent_events_api.py::test_run_agent_runtime_once_returns_results`
- Runtime events query API
  - `tests/test_agent_events_api.py::test_get_agent_runtime_events_filters_agent_events`

### Recovery loop verification
- Recovery requeue/escalation/fail-closed behavior
  - `tests/test_recovery_agent.py` (full file)

### Canonical run lifecycle and scenario packs
- Run lifecycle and contract drift guard
  - `tests/test_run_lifecycle.py`
  - `tests/test_run_contract_drift_guard.py`
  - `tests/test_partial_intake_lifecycle.py`
- Scenario packs
  - `tests/test_singapore_canonical_regression.py`
  - `tests/test_realworld_scenarios_v02.py`

## Coverage Notes
- This matrix verifies single-worker runtime semantics and endpoint contracts.
- Multi-worker distributed lease/ownership semantics are not validated by this test set.
- Frontend verification now covers preservation of runtime packet fields through the BFF adapter and a TypeScript-checked production build.
- Live-tool verification now covers configurable provider adapters while preserving deterministic local fallbacks.
