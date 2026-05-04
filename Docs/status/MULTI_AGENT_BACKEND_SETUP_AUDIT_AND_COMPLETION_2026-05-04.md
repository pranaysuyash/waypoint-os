# Multi-Agent Backend Setup Audit and Completion (2026-05-04)

## Scope
- Backend-only assessment and completion pass for the current multi-agent setup.
- Sources used: live codebase, repo docs, scenario tests, and external agent-architecture guidance.
- Frontend changes intentionally excluded.

## Objective to Deliverables Mapping
1. Identify current multi-agent setup in code + docs.
2. Identify what is missing / improvable.
3. Complete the backend agentic setup to a stronger operational baseline.
4. Test scenarios and runtime behavior.
5. Document the setup end-to-end for future agents/operators.

## Current Backend Multi-Agent Setup (Code Truth)

### 1) Asynchronous run lifecycle backbone (implemented)
- `POST /run` returns accepted state and `run_id`; terminal state is polled.
- Canonical modules:
  - `spine_api/run_state.py`
  - `spine_api/run_ledger.py`
  - `spine_api/run_events.py`
  - `spine_api/server.py`

### 2) Frontier agentic pass in orchestration (implemented)
- In-process advanced pass after core decisioning:
  - `src/intake/frontier_orchestrator.py`
  - `src/intake/checker_agent.py`
  - integration in `src/intake/orchestration.py`
- Includes:
  - Ghost trigger heuristics
  - checker audit
  - intelligence lookup
  - specialty knowledge
  - negotiation subsystem hook

### 3) Autonomous recovery agent (implemented)
- `src/agents/recovery_agent.py`
- Instantiated and lifecycle-managed in `spine_api/server.py` lifespan hooks.
- Detects stuck trips and applies escalation ladder: `re_queue` -> `escalate`.

## Docs Consistency Audit

### Still aligned with code
- `Docs/OPERATOR_RUN_RUNBOOK_2026-04-18.md`
- `Docs/status/ASYNC_RUN_CONTRACT_GUARDRAILS_2026-04-28.md`
- `Docs/BACKEND_WAVE_A_IMPL_NOTES_2026-04-18.md`
- `Docs/AGENTIC_PIPELINE_CODE_AUDIT_2026-04-27.md`

### Partially stale/conflicting
- `Docs/AGENTIC_DATA_FLOW_AND_IMPLEMENTATION_PLAN_2026-04-22.md`
  - claims `src/agents/` is effectively empty; no longer true.
- `Docs/MULTI_AGENT_INFRASTRUCTURE_ASSESSMENT_2026-04-22.md`
  - useful target architecture, but states full absence of runtime agent infra.
- `Docs/AI_AGENT_SYSTEM_READINESS_ASSESSMENT_2026-04-22.md`
  - mixes product backend state and development-agent ecosystem context.

## Key Missing Gaps Before This Pass
1. No canonical structured event envelope for product-agent actions.
2. No dedicated tests for `RecoveryAgent` decision ladder/fail-closed behavior.
3. No single up-to-date backend multi-agent setup document reconciling stale docs.

## Completion Changes Implemented in This Pass

### A) Added canonical product-agent event schema
- New file: `src/agents/events.py`
- Adds:
  - `AgentEventType` enum
  - `AgentEvent` dataclass envelope with:
    - `agent_name`
    - `event_type`
    - `trip_id` / `run_id`
    - `correlation_id`
    - `timestamp`
    - structured `payload`

### B) Wired recovery agent to emit structured agent events
- Updated: `src/agents/recovery_agent.py`
- Changes:
  - emits `agent_decision` before recovery action selection
  - emits `agent_action` on success
  - emits `agent_failed` on failure
  - event payloads now include standardized metadata and action details
  - audit logs now use `event_type="agent_event"` with canonical envelope

### C) Added dedicated recovery-agent test suite
- New file: `tests/test_recovery_agent.py`
- Covers:
  - requeue when under limit
  - escalation after requeue ceiling
  - fail-closed behavior on runner failure
  - structured event emission presence

### D) Added trip-scoped product-agent observability API
- Updated: `spine_api/persistence.py`
  - Added `AuditStore.get_agent_events_for_trip(trip_id, limit)`
- Updated: `spine_api/server.py`
  - Added `GET /trips/{trip_id}/agent-events`
  - Enforces trip ownership via agency scope
- New tests:
  - `tests/test_agent_events_api.py`

## Scenario and Verification Evidence

### Commands run
1. `uv run pytest -q tests/test_recovery_agent.py tests/test_singapore_canonical_regression.py`
2. `uv run pytest -q tests/test_realworld_scenarios_v02.py tests/test_run_lifecycle.py tests/test_run_contract_drift_guard.py`

### Results
- Command 1: `4 passed`
- Command 2: `40 passed`
- Command 3: `uv run pytest -q tests/test_agent_events_api.py tests/test_recovery_agent.py` → `6 passed`
- Command 4: `uv run pytest -q tests/test_singapore_canonical_regression.py tests/test_realworld_scenarios_v02.py tests/test_run_lifecycle.py tests/test_run_contract_drift_guard.py` → `41 passed`
- Command 5: `uv run pytest -q tests/test_agent_events_api.py tests/test_recovery_agent.py tests/test_singapore_canonical_regression.py tests/test_realworld_scenarios_v02.py tests/test_run_lifecycle.py tests/test_run_contract_drift_guard.py` → `47 passed`
- Total in this completion pass: `51 passed`

## External Research Applied (Architecture Guidance)

### OpenAI (Agents SDK + handoff patterns)
- Agent workflows should explicitly support specialized handoffs and traceability.
- Source:
  - https://platform.openai.com/docs/guides/agents-sdk/
  - https://platform.openai.com/docs/guides/voice-agents

### Anthropic (workflows vs agents, orchestrator-worker)
- Prefer clear orchestrator-worker control flow and incremental reliability over premature complexity.
- Source:
  - https://www.anthropic.com/engineering/building-effective-agents

### LangGraph references (supervisor/multi-agent orchestration concepts)
- Supervisor-style orchestration and role-separation patterns are useful for future hardening.
- Source:
  - https://langchain-ai.github.io/langgraphjs/reference/modules/langgraph-supervisor.html
  - https://langchain-ai.github.io/langgraphjs/reference/modules/langgraph.html

## Current Canonical Backend Multi-Agent Pattern
1. Deterministic spine (`run_spine_once`) remains canonical.
2. Frontier pass acts as an additive agentic enrichment stage.
3. RecoveryAgent operates as asynchronous self-healing supervision loop.
4. Run lifecycle + ledger + events provide deterministic trace and polling contract.
5. Agent-specific events now have a dedicated typed envelope for observability.

## Open Follow-Ups (Next Increment)
1. Add dashboard-level aggregation endpoint for `agent_event` metrics/SLO rollups.
2. Add concurrency ownership doc for multi-worker deployment semantics.
3. Add tests for frontier-checker branch outcomes under threshold variations.
4. Introduce a canonical agent registry when more product agents are added.

## Notes for Future Agents
- Do not rely on April 2026 “zero infra” statements without code verification.
- Treat `src/agents/events.py` as the canonical envelope for product-agent observability.
- Keep agentic logic additive to spine canonical path; avoid parallel run routes.
