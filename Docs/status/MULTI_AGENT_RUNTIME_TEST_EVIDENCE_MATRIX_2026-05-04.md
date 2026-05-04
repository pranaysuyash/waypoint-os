# Multi-Agent Runtime Test Evidence Matrix

- Date: 2026-05-04
- Scope: backend-only runtime primitives, product agents, API surfaces, and scenario drills

## Command Evidence

| Command | Result | Notes |
| --- | --- | --- |
| `uv run python -m py_compile src/agents/events.py src/agents/recovery_agent.py src/agents/runtime.py spine_api/persistence.py spine_api/server.py tools/run_multi_agent_runtime_scenarios.py` | Pass | Static compile sanity for touched backend modules and scenario tool. |
| `uv run pytest tests/test_agent_runtime.py tests/test_agent_events_api.py tests/test_recovery_agent.py -q` | `22 passed in 12.64s` | The pytest process stayed alive after reporting success in this environment; PIDs were killed after pass output was captured. |
| `uv run python tools/run_multi_agent_runtime_scenarios.py` | Pass | Wrote `Docs/status/MULTI_AGENT_RUNTIME_SCENARIO_EVIDENCE_2026-05-04.md`. |

## Requirement Coverage

| Requirement | Test / Artifact | Coverage |
| --- | --- | --- |
| Static registry with explicit contracts | `tests/test_agent_runtime.py::test_default_registry_exposes_two_product_agents_beyond_recovery` | Verifies both registered agents and all contract fields. |
| Happy path orchestration | `tests/test_agent_runtime.py::test_happy_path_orchestration_runs_both_product_agents` and scenario evidence | Verifies both product agents execute and update trip records. |
| Transient failure + retry | `tests/test_agent_runtime.py::test_transient_dependency_failure_retries_then_succeeds` and scenario evidence | Verifies retry-pending first pass and successful second pass. |
| Terminal failure + escalation | `tests/test_agent_runtime.py::test_terminal_failure_poisons_and_escalates_after_retry_budget` and scenario evidence | Verifies poisoned state and `agent_escalated` event. |
| Ownership collision / idempotent re-entry | `tests/test_agent_runtime.py::test_ownership_collision_prevention_and_idempotent_reentry` and scenario evidence | Verifies lease denial and completed idempotency skip. |
| High-risk quality trigger | `tests/test_agent_runtime.py::test_quality_agent_escalates_high_suitability_flags` | Verifies suitability flag escalation. |
| Tool evidence freshness | `tests/test_agent_runtime.py::test_tool_result_marks_stale_evidence_not_fresh` | Verifies `ToolResult` refuses expired evidence as fresh. |
| Document readiness checklist | `tests/test_agent_runtime.py::test_document_readiness_agent_builds_visa_passport_transit_checklist` | Verifies visa/passport/transit/insurance checklist, must-confirm fields, and tool evidence. |
| Document readiness idempotent skip | `tests/test_agent_runtime.py::test_document_readiness_agent_skips_when_checklist_exists` | Verifies completed document checklist is not re-created without fact changes. |
| Recovery compatibility | `tests/test_recovery_agent.py::test_recovery_agent_detects_dict_trip_records` | Verifies server adapter dict records do not break `RecoveryAgent`. |
| Trip-scoped event API | `tests/test_agent_events_api.py::test_get_trip_agent_events_filters_and_returns_payload` | Verifies trip event response shape. |
| Agency access on trip events | `tests/test_agent_events_api.py::test_get_trip_agent_events_enforces_agency_scope` | Verifies cross-agency trip event lookup returns 404. |
| Runtime registry API | `tests/test_agent_events_api.py::test_get_agent_runtime_returns_registry_and_health` | Verifies `/agents/runtime` shape. |
| Runtime run-once API | `tests/test_agent_events_api.py::test_run_agent_runtime_once_returns_results` | Verifies `/agents/runtime/run-once`. |
| Runtime events API | `tests/test_agent_events_api.py::test_get_agent_runtime_events_filters_agent_events` | Verifies `/agents/runtime/events` filtering. |

## Scenario Artifact

`Docs/status/MULTI_AGENT_RUNTIME_SCENARIO_EVIDENCE_2026-05-04.md` captures:

- generation timestamp,
- command line,
- in-memory storage statement,
- happy path orchestration results,
- transient dependency failure plus retry results,
- terminal failure plus escalation results,
- ownership/idempotent re-entry results.
- document readiness checklist results.

## Residual Risk

The tests cover the single-process runtime contract. They do not prove distributed locking across multiple uvicorn workers; that is listed as a production-hardening gap in the runbook and completion report.
