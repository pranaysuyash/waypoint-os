# Multi-Agent Runtime Implementation Tracker

Date: 2026-05-14
Source: Random Document Audit (Multi-Agent Runtime concept)

## Current Implemented Runtime

- **16 registered agents** in `build_default_registry()` (`src/agents/runtime.py`)
- **1 recovery agent** (`src/agents/recovery_agent.py`) — accepts `requeue_port` or deprecated `spine_runner`
- **3 API endpoints** (`spine_api/routers/agent_runtime.py`): GET /agents/runtime, POST /agents/runtime/run-once, GET /agents/runtime/events
- **2 work coordinators**: `InMemoryWorkCoordinator` + `SQLWorkCoordinator` (both tested)
- **3 requeue port impls**: `DisabledSpineRequeuePort`, `InlineSpineRequeuePort`, `_RawCallableRequeuePort`
- **Config factory**: `spine_api/services/agent_runtime_factory.py`
- **Runtime adapters**: `spine_api/services/agent_runtime_adapters.py`
- **Startup construction**: Runtime bundle built during lifespan startup (`_build_agent_runtime_bundle()`), not at import time

## Issues

| ID | Title | Priority | Status |
|---|---|---|---|
| 001 | SQLWorkCoordinator Has Zero Direct Tests | P1 | Complete |
| 002 | Recovery Agent Re-queue Path Disabled | P1 | Complete (port abstracted + tested) |
| 003 | Multi-Agent Infrastructure Summary Docs Are Stale | P3 | Complete |
| 004 | TRIPSTORE_BACKEND Coupling in Coordinator Selection | P3 | Complete |
| 005 | `build_safety_alert_tool_from_env()` StateDept Path Untested | P3 | Complete |

## Units

### Unit 1 — SQLWorkCoordinator Tests
**Status:** Complete
`tests/test_agent_work_coordinator.py` — 19 tests covering `ensure_schema`, `acquire`, `complete`, `fail`, `snapshot`.

### Unit 2A — Runtime Config Factory
**Status:** Complete
`spine_api/services/agent_runtime_factory.py` + `spine_api/services/agent_runtime_adapters.py` + tests. Decoupled `TRIPSTORE_BACKEND` from `AGENT_WORK_COORDINATOR`. Added `DEPLOYMENT_MODE` and `AGENT_RECOVERY_REQUEUE_MODE`.

### Unit 2B — Helper Consolidation
**Status:** Complete
Extracted `_normalize_list` from 3 copy-pasted class methods to module-level function. -48 lines. Left as follow-up: `_get_nested` duplicates in `spine_api/services/inbox_projection.py` and `spine_api/scoring/__init__.py` (6-line helpers, low value to extract).

### Unit 3 — Recovery Requeue Port
**Status:** Complete
`src/agents/requeue.py` + `tests/test_agent_requeue.py` (20 tests). Port/protocol abstraction with Disabled, Inline, and backward-compat RawCallable implementations.

### Unit 4 — Live Tool Env Tests
**Status:** Complete
2 new tests for `build_safety_alert_tool_from_env()`: `TRAVEL_AGENT_SAFETY_PROVIDER=state_dept` path and URL template precedence. 8/8 live tool tests passing.

### Unit 5 — Roadmap Doc + ADR Corrections
**Status:** Complete
- `Docs/architecture/MULTI_AGENT_RUNTIME_ROADMAP.md` created — valid aspirations preserved, superseded assumptions marked
- `Docs/architecture/adr/ADR-006-MULTI-AGENT-RUNTIME_2026-05-04.md` corrected — 16 agents, SQL coordinator, config factory, requeue port, roadmap pointer
- `MULTI_AGENT_INFRASTRUCTURE_SUMMARY.txt` rewritten — supersession notice, current implementation, valid roadmap, superseded assumptions

## Test Summary

All agent-related tests: **118 passing** across 10 test files.
Commands: `.venv/bin/python -m pytest tests/test_agent_requeue.py tests/test_recovery_agent.py tests/test_agent_runtime_factory.py tests/test_agent_runtime.py tests/test_agent_events_api.py tests/test_live_tools.py tests/test_risk_contracts.py tests/test_agent_work_coordinator.py tests/test_agent_tripstore_adapter.py -v --tb=short`
