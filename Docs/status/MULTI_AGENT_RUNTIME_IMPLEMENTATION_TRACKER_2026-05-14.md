# Multi-Agent Runtime Implementation Tracker

Date: 2026-05-14
Source: Random Document Audit (Multi-Agent Runtime concept)
Audit report: `Docs/random_document_audit_v3_2026-05-04.md` (concept audit)

## Current Implemented Runtime

- **16 registered agents** in `build_default_registry()` (`src/agents/runtime.py:3143-3161`)
- **1 recovery agent** (`src/agents/recovery_agent.py`)
- **3 API endpoints** (`spine_api/routers/agent_runtime.py`): GET /agents/runtime, POST /agents/runtime/run-once, GET /agents/runtime/events
- **2 work coordinators**: `InMemoryWorkCoordinator` (tested), `SQLWorkCoordinator` (untested)
- **1 recovery requeue**: disabled in production (`spine_runner=None`)

## Issues Found

| ID | Title | Priority | Status |
|----|-------|----------|--------|
| 001 | SQLWorkCoordinator Has Zero Direct Tests | P1 | Complete |
| 002 | Recovery Agent Re-queue Path Disabled | P1 | Pending |
| 003 | Multi-Agent Infrastructure Summary Docs Are Stale | P3 | Pending |
| 004 | TRIPSTORE_BACKEND Coupling in Coordinator Selection | P3 | Complete |
| 005 | build_safety_alert_tool_from_env() StateDept Path Untested | P3 | Pending |

## Valid Roadmap Aspirations (not implemented, not stale)

Aspirations from `MULTI_AGENT_INFRASTRUCTURE_SUMMARY.txt` that remain valid product direction but are not yet built:

- **Communicator Agent**: blocked state -> clarification drafts for operator review
- **Scout Agent**: proactive info retrieval (visa, weather, safety, availability)
- **QA Agent**: analyze failures, propose fixtures and tests
- **Committee System**: Budget Optimizer + Experience Maximizer + Trip Architect
- **Operator Copilot**: natural-language intervention on canonical packet

## Superseded Implementation Assumptions (from infrastructure summary)

These were described as "Phase 1 Foundation" but are no longer the planned approach:

- `src/agents/orchestrator.py` as mandatory first file
- `src/agents/base_agent.py` as mandatory first file
- Dynamic discovery as near-term registry mechanism
- Message bus before durable work coordination exists
- Agent memory before clear state model exists
- Resource isolation before job execution model exists

## Unit Tracking

### Unit 1: SQLWorkCoordinator Tests

**Status:** Complete (19 tests, all passing)
**Owner:** Current Agent
**Files:**
- `tests/test_agent_work_coordinator.py` (new, 19 tests)
- `Docs/status/MULTI_AGENT_RUNTIME_IMPLEMENTATION_TRACKER_2026-05-14.md` (updated)
**Tests:**
- [x] ensure_schema creates schema and is idempotent
- [x] acquire fresh work returns acquired and attempt=1
- [x] completed work returns idempotent_reentry_completed
- [x] poisoned work returns poisoned_fail_closed
- [x] active running lease blocks another owner
- [x] expired running lease can be reacquired
- [x] retry exhaustion poisons the work item
- [x] complete marks terminal completed state
- [x] fail marks terminal failed/poisoned state
- [x] snapshot returns backend=sql and correct counts

### Unit 2A: Runtime Config Factory

**Status:** Complete
**Files:**
- `spine_api/services/agent_runtime_factory.py` (new)
- `tests/test_agent_runtime_factory.py` (new, 17 tests)
- `spine_api/server.py` (modified — replaced module-level construction with factory call)
- `spine_api/routers/agent_runtime.py` (modified — runtime endpoint exposes config)

**Behavior changes:**
- `TRIPSTORE_BACKEND=sql` no longer forces `AGENT_WORK_COORDINATOR=sql`
- `DEPLOYMENT_MODE` env var added (local | test | dogfood | beta | production)
- `AGENT_RECOVERY_REQUEUE_MODE` env var added (disabled | inline) — config only, no behavior yet
- `AGENT_WORK_COORDINATOR` defaults to `memory` instead of `None`
- All invalid env values fail fast with ValueError
- Runtime `/agents/runtime` endpoint exposes config
- Backward compatible: `configure_runtime()`, `_agent_supervisor`, `_recovery_agent` module globals preserved for tests

**Tests passed:** 91/91 across all 7 agent-related test files

**Guardrails:**
- [x] No InlineSpineRequeuePort in Unit 2A (config-only)
- [x] No helper consolidation mixed in
- [x] Backward compat with tests that monkeypatch globals
- [x] Env vars read at call time, never at import time
- [x] Coordinator selection explicit (no TRIPSTORE_BACKEND coupling)
- [x] Fail-fast on invalid env values
- [x] Runtime endpoint exposes config

### Unit 2B: Helper Consolidation (separate patch)

**Status:** Pending
**Scope:** Extraction of `_normalize_list` from 3 copy-pasted class methods in `runtime.py`. Extraction of `_get_nested` from `inbox_projection.py` and `scoring/__init__.py`.

### Unit 3: Recovery Requeue Port

**Status:** Pending
**Files:**
- `src/agents/requeue.py` (new)
- `src/agents/recovery_agent.py` (modify)
- `tests/test_recovery_agent.py` (add tests)
**Scope:**
- `SpineRequeueResult` dataclass
- `SpineRequeuePort` protocol
- `DisabledSpineRequeuePort` — current behavior
- `InlineSpineRequeuePort` — calls pipeline with reconstructed context
- RecoveryAgent depends on port, not raw callable
- Hard constraint: no faking success when requeue cannot faithfully run

### Unit 4: Live Tool Env Tests

**Status:** Pending
**Scope:** Tests for `TRAVEL_AGENT_SAFETY_PROVIDER=state_dept` path, URL template precedence

### Unit 5: Roadmap Doc + ADR Corrections

**Status:** Pending
**Files:**
- `Docs/architecture/MULTI_AGENT_RUNTIME_ROADMAP.md` (new)
- `Docs/architecture/adr/ADR-006-MULTI-AGENT-RUNTIME_2026-05-04.md` (modify)
- `MULTI_AGENT_INFRASTRUCTURE_SUMMARY.txt` (rewrite or archive)
