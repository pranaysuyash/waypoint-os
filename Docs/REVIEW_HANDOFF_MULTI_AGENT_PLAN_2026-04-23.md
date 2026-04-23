# REVIEW HANDOFF: Multi-Agent Infrastructure Plan

**Checklist applied**: `IMPLEMENTATION_AGENT_REVIEW_HANDOFF_CHECKLIST.md`
**Plan under review**: `Docs/AGENTIC_DATA_FLOW_AND_IMPLEMENTATION_PLAN_2026-04-22.md`
**Date**: 2026-04-23
**Scope**: Multi-agent infrastructure foundation (Phase 1) + Communicator Agent (Phase 2)
**Reviewer**: Pranay (product owner)

---

## A. Review Verdict

**Status**: Plan is comprehensive and additive, but contains 3 architectural decisions requiring explicit validation before first line of code is written.

---

## B. What Is Verified

| Claim | Evidence | Status |
|-------|----------|--------|
| Spine pipeline is untouched by agent layer | Plan explicitly states spine is invoked as tool, never modified | VERIFIED -- plan text + no agent code exists yet |
| Agents directory is empty | `ls -la src/agents/` shows only `__init__.py` (21 bytes) | VERIFIED |
| Existing spine handles blocked state | `src/intake/gates.py` has `GateVerdict` with escalate/degrade | VERIFIED |
| No existing agent infrastructure | `grep -r "class.*Agent" src/` returns zero matches | VERIFIED |
| Plan is 26KB, 575 lines | `wc -l Docs/AGENTIC_DATA_FLOW_AND_IMPLEMENTATION_PLAN_2026-04-22.md` | VERIFIED |

---

## C. 3 Architectural Decisions Requiring Review

### DECISION 1: Base Agent Class Inheritance Model
**Question**: Should agents inherit from a Python ABC, or use a protocol/dataclass composition pattern?

**Plan proposes**: Abstract Base Class with `@abstractmethod` decorators
```python
class BaseAgent(ABC):
    @abstractmethod
    async def execute(self, packet, context) -> AgentResult
    # ... other abstract methods
```

**Alternative**: Protocol-based (structural subtyping, no inheritance)
```python
class AgentProtocol(Protocol):
    async def execute(self, packet, context) -> AgentResult: ...
```

**Risk if wrong**: ABC is rigid; Protocol is flexible but less tooling support. Switching later touches every agent file.

**My recommendation**: ABC for now (explicit contract, IDE support, matches your existing codebase style in `src/llm/base.py`). Validate after 2 agents are built.

---

### DECISION 2: Async-First vs Sync-First Agent Execution
**Question**: Should agent `execute()` methods be `async def` or regular `def`?

**Plan proposes**: `async def execute()` throughout

**Context**: Your existing spine `run_spine_once()` is synchronous. Calling it from async agents requires `asyncio.to_thread()` or similar.

**Risk if wrong**: Async adds complexity if agents are CPU-bound (rule matching, LLM calls via sync clients). But sync blocks the orchestrator when managing multiple agents.

**My recommendation**: Async-first in the contract, but agents can delegate sync work to threads. Matches modern Python patterns and future-proofs for concurrent agent execution.

---

### DECISION 3: Where Agent Output Is Stored
**Question**: When Communicator Agent drafts 1-3 clarification messages, where do they live?

**Plan proposes**: Return as `AgentResult.artifacts` attached to the run state

**Options**:
1. **In-memory on run state** -- simplest, lost on restart
2. **SQLite/json file per run** -- persistent, matches your existing decision cache pattern in `src/decision/cache_storage.py`
3. **New column in existing database** -- if you have persistent storage for runs

**Risk if wrong**: If we pick in-memory and you need persistence later, we refactor all agents. If we pick files and you wanted DB, we migrate.

**My recommendation**: Start with in-memory (return via `AgentResult`). Add persistence layer only after Communicator Agent proves value and we know the exact query patterns. This is additive, not a migration.

---

## D. Task Package (If Review Approved)

### Task 1: Build Base Agent Foundation
**Objective**: Create the abstract base class and message types that all agents depend on

**Scope**:
- IN: `src/agents/base_agent.py`, `src/agents/messages.py`, `src/agents/__init__.py` updates
- IN: Enums (AgentType, MessageType, HealthStatus, ErrorAction)
- IN: Dataclasses (AgentConfig, AgentResult, AgentState, AgentMessage, AgentEvent)
- IN: BaseAgent ABC with lifecycle methods
- OUT: Orchestrator (Task 2), any concrete agents (Task 3+)
- OUT: Persistence layer, tool access implementation, observability hooks (stubs only)

**Expected files**:
```
src/agents/
  base_agent.py      (new)
  messages.py        (new)
  __init__.py        (updated to export public API)
```

**Acceptance criteria**:
1. `python -m py_compile src/agents/base_agent.py` -- no syntax errors
2. `python -m py_compile src/agents/messages.py` -- no syntax errors
3. `python -c "from src.agents import BaseAgent, AgentMessage"` -- imports cleanly
4. `python -c "from src.agents.base_agent import BaseAgent; print(BaseAgent.__abstractmethods__)"` -- shows execute, initialize, shutdown, declare_tools, save_state, load_state, health_check, handle_error
5. File docstrings explain: purpose, author, version, how to subclass

**Verification commands**:
```bash
cd /Users/pranay/Projects/travel_agency_agent
python -m py_compile src/agents/base_agent.py
python -m py_compile src/agents/messages.py
python -c "from src.agents import BaseAgent, AgentMessage; print('OK')"
python -c "from src.agents.base_agent import BaseAgent; print(sorted(BaseAgent.__abstractmethods__))"
```

**Non-goals**:
- No async runtime implementation
- No actual LLM calls
- No database persistence
- No frontend integration
- No changes to existing spine code

---

### Task 2: Build Communicator Agent (Highest Value)
**Objective**: Create the agent that auto-drafts clarification messages when NB02 hits blocked state

**Scope**:
- IN: `src/agents/communicator_agent.py`
- IN: Draft generation logic (template-based + LLM augmentation)
- IN: Validation via spine-as-tool pattern (mock for now)
- IN: Unit tests for draft generation
- OUT: Actual LLM integration (mock LLM client)
- OUT: Integration with NB02 blocked state hook (Task 3)
- OUT: Frontend message selection UI

**Expected files**:
```
src/agents/
  communicator_agent.py   (new)
tests/agents/
  test_communicator_agent.py  (new)
```

**Acceptance criteria**:
1. `CommunicatorAgent` inherits from `BaseAgent`
2. `execute()` accepts `(CanonicalPacket, context_dict)` and returns `AgentResult`
3. Can generate 1-3 message drafts from a blocked-reason string
4. Drafts include: empathetic tone, specific question, conversion-optimized close
5. Has unit test: given "missing_traveler_passport_expiry", produces draft containing "passport"

**Verification commands**:
```bash
cd /Users/pranay/Projects/travel_agency_agent
python -m py_compile src/agents/communicator_agent.py
python -m pytest tests/agents/test_communicator_agent.py -v
```

**Non-goals**:
- No actual spine invocation yet (mock the tool call)
- No WhatsApp/email sending
- No operator workbench integration
- No persistence of drafts beyond return value

---

### Task 3: Integrate Communicator with NB02 Blocked State
**Objective**: Wire Communicator Agent into the actual pipeline so it triggers on blocked state

**Scope**:
- IN: Hook in `src/intake/orchestration.py` after NB02 returns blocked
- IN: Spawn Communicator Agent with blocked context
- IN: Attach drafted messages to run state for operator access
- OUT: Frontend changes
- OUT: Message sending (WhatsApp/email)
- OUT: Automatic re-triggering after operator response

**Expected files**:
```
src/intake/
  orchestration.py    (minor edit: add agent spawn hook, feature-flagged)
```

**Acceptance criteria**:
1. Feature flag exists: `USE_COMMUNICATOR_AGENT=1` in config
2. When flag is OFF: existing behavior unchanged (backward compatibility)
3. When flag is ON and NB02 returns blocked: Communicator Agent spawns, drafts messages
4. Drafts are accessible via `run_state['communicator_drafts']`
5. Existing tests still pass

**Verification commands**:
```bash
cd /Users/pranay/Projects/travel_agency_agent
pytest tests/ -k "not integration"  # existing tests pass
python -c "from src.intake.orchestration import run_spine_once; print('Import OK')"
```

**Non-goals**:
- No frontend display of drafts yet
- No persistence of drafts to database
- No automatic pipeline re-trigger after clarification

---

## E. Decision Gate

**Recommendation**: GO on Task 1 and Task 2 (foundation + Communicator Agent) IF the following 3 decisions are validated by reviewer:

1. **DECISION 1 (ABC vs Protocol)**: Approve ABC inheritance model? If you want Protocol instead, say so now -- switching after 2 agents are built touches 5+ files.

2. **DECISION 2 (Async vs Sync)**: Approve async-first agent contracts? If you prefer sync for simplicity, I'll use sync with explicit thread delegation for I/O.

3. **DECISION 3 (Agent Output Storage)**: Approve in-memory AgentResult return for now? If you know the exact persistence mechanism you want (SQLite/PostgreSQL/file), tell me now and I'll include the interface.

**If any decision changes, I update the plan before writing code.**

If all 3 are approved: proceed with Task 1 (base_agent.py) immediately.

---

## F. Evidence Log

| Check | Result |
|-------|--------|
| Default docs read | `AGENTIC_DATA_FLOW_AND_IMPLEMENTATION_PLAN_2026-04-22.md` (576 lines) read |
| Scope docs read | `MULTI_AGENT_INFRASTRUCTURE_ASSESSMENT_2026-04-22.md` (479 lines) read |
| Existing code verified | `src/agents/` only contains `__init__.py` |
| Existing tests verified | `tests/` has passing tests for suitability (23), hybrid engine exists |
| No contradictions found | Plan explicitly preserves spine integrity (matches `AGENTS.md` rules) |

---

**Ready for your review. Please validate the 3 architectural decisions above.**
