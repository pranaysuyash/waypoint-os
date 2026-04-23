# AGENTIC DATA FLOW & IMPLEMENTATION PLAN

**Product**: travel_agency_agent (Multi-Agent Agentic AI Travel Agency SaaS)
**Date**: 2026-04-23
**Prepared by**: Hermes (development agent)
**Status**: Research Complete — Ready for Implementation

---

## 1. EXECUTIVE SUMMARY

This document captures the complete analysis of:
- Current codebase agent readiness
- Available skills and patterns from the Hermes ecosystem
- Agentic data flow architecture (how agents spawn, communicate, and collaborate)
- Concrete implementation plan with file-by-file specifications

**Key Finding**: The travel_agency_agent has an excellent deterministic spine (NB01->NB02->NB03) but ZERO agent infrastructure. The `src/agents/` directory contains only an empty `__init__.py`. All agent orchestration, communication, lifecycle, and concrete agent implementations must be built from scratch.

---

## 2. CURRENT STATE INVENTORY

### 2.1 What EXISTS (Foundation to Build On)

| Component | Location | Status | Notes |
|-----------|----------|--------|-------|
| Spine Pipeline | `src/intake/orchestration.py` | ✅ Working | `run_spine_once()` — NB01->Validate->NB02->NB03->Safety->Fees |
| Hybrid Decision Engine | `src/decision/hybrid_engine.py` | ✅ Working | Rule engine -> LLM fallback with caching |
| Suitability Scoring | `src/suitability/` | ✅ 23 tests passing | Tier 1 + Tier 2 scoring, 18 activity catalog |
| Packet Models | `src/intake/packet_models.py` | ✅ Working | `CanonicalPacket` with source tracking, provenance |
| Gates & Autonomy | `src/intake/gates.py` | ✅ Working | `GateVerdict` (proceed/retry/escalate/degrade) |
| LLM Clients | `src/llm/` | ✅ Working | Gemini, local, base abstractions |
| Fee Calculation | `src/fees/calculation.py` | ✅ Working | Risk-adjusted fee calculator |
| Frontend Workbench | `frontend/` | ✅ Working | 5-screen React/TypeScript |
| Decision Cache | `src/decision/cache_storage.py` | ✅ Working | SQLite-backed decision cache |
| Decision Telemetry | `src/decision/telemetry.py` | ✅ Working | Structured telemetry for decisions |
| Decision Health | `src/decision/health.py` | ✅ Working | Health checks for decision engine |
| Decision Rules | `src/decision/rules/` | ✅ Working | Deterministic rule engine |

### 2.2 What's MISSING (Must Be Built)

| Component | Target Location | Status | Dependencies |
|-----------|----------------|--------|--------------|
| Base Agent Classes | `src/agents/base_agent.py` | ❌ Not started | None |
| Agent Orchestrator | `src/agents/orchestrator.py` | ❌ Not started | base_agent.py |
| Agent Messages | `src/agents/messages.py` | ❌ Not started | None |
| Agent Registry | `src/agents/registry.py` | ❌ Not started | base_agent.py |
| Agent State Manager | `src/agents/state.py` | ❌ Not started | messages.py |
| Scout Agent | `src/agents/scout_agent.py` | ❌ Not started | orchestrator, base_agent |
| Communicator Agent | `src/agents/communicator_agent.py` | ❌ Not started | orchestrator, base_agent |
| QA Agent | `src/agents/qa_agent.py` | ❌ Not started | orchestrator, base_agent |
| Budget Optimizer Agent | `src/agents/committee/budget_optimizer_agent.py` | ❌ Not started | orchestrator, base_agent |
| Experience Maximizer Agent | `src/agents/committee/experience_maximizer_agent.py` | ❌ Not started | orchestrator, base_agent |
| Trip Architect Agent | `src/agents/committee/trip_architect_agent.py` | ❌ Not started | orchestrator, base_agent |
| Operator Copilot Agent | `src/agents/operator_copilot_agent.py` | ❌ Not started | orchestrator, base_agent |

### 2.3 Existing Agent Directory State

```
src/agents/
└── __init__.py    # Contains only: "# src/agents package"
```

### 2.4 Existing LLM Agents Directory

```
src/llm/agents/
└── __init__.py    # Contains only: "# src/llm/agents package"
```

---

## 3. SKILLS ECOSYSTEM ANALYSIS

### 3.1 Available Agent-Related Skills (3,128 total skills installed)

From the Hermes skills ecosystem (`hermes skills list`), these are the most relevant patterns:

**Orchestration Skills:**
| Skill | Category | Source | Relevance |
|-------|----------|--------|-----------|
| `agent-orchestration` | codex | local | High — Direct agent orchestration patterns |
| `agent-orchestration-improve-agent` | codex | local | Medium — Agent improvement patterns |
| `agent-orchestration-multi-agent-optimize` | codex | local | High — Multi-agent optimization |
| `workflow-orchestration-patterns` | codex | local | Medium — General workflow patterns |
| `saga-orchestration` | codex | local | Medium — Distributed transaction patterns |
| `acceptance-orchestrator` | codex | local | Low — Acceptance testing patterns |

**Multi-Agent Skills:**
| Skill | Category | Source | Relevance |
|-------|----------|--------|-----------|
| `crewai-multi-agent` | codex | local | High — Multi-agent orchestration framework |
| `multi-agent-patterns` | codex | local | High — Core multi-agent design patterns |
| `multi-agent-brainstorming` | codex | local | Low — Brainstorming only |

**Agent Construction Skills:**
| Skill | Category | Source | Relevance |
|-------|----------|--------|-----------|
| `agent-harness-construction` | agents | local | High — Design agent action spaces and tool definitions |
| `agent-pipeline-local-testing` | agents | local | High — Test multi-stage agent pipelines locally |
| `agentic-engineering` | agents | local | High — Eval-first execution, decomposition |
| `continuous-agent-loop` | agents | local | Medium — Autonomous agent loop patterns |
| `autonomous-loops` | agents | local | Medium — Patterns for autonomous agent loops |

**Development Agent Skills (Hermes as builder):**
| Skill | Category | Source | Relevance |
|-------|----------|--------|-----------|
| `claude-code` | autonomous-ai-agents | builtin | Medium — Claude Code CLI agent |
| `codex` | autonomous-ai-agents | builtin | Medium — Codex CLI agent |
| `hermes-agent` | autonomous-ai-agents | builtin | Medium — Hermes agent patterns |

### 3.2 Missing Skills (Gaps in Ecosystem)

No installed skills cover these critical patterns:
- ❌ Agent registry/discovery service
- ❌ Inter-agent message passing (pub-sub, request-reply)
- ❌ Shared state / blackboard / tuple space
- ❌ Agent supervision trees (OTP-like)
- ❌ Agent-specific tool access control
- ❌ Agent observability (structured logging, metrics, distributed tracing)
- ❌ Agent lifecycle management (spawn, monitor, terminate, restart)

### 3.3 Skills to Load During Implementation

When building each component, load these skills:

| Component Being Built | Skills to Load |
|-----------------------|----------------|
| Base Agent Classes | `agent-harness-construction`, `agentic-engineering`, `python-patterns` |
| Orchestrator | `agent-orchestration`, `multi-agent-patterns`, `autonomous-loops` |
| Communicator Agent | `agentic-engineering`, `verification-before-completion` |
| Scout Agent | `agent-harness-construction`, `agentic-engineering` |
| QA Agent | `agent-pipeline-local-testing`, `tdd-workflow` |
| Committee System | `multi-agent-patterns`, `crewai-multi-agent` |
| Operator Copilot | `agentic-engineering`, `python-patterns` |
| Unit Tests | `tdd-workflow`, `python-testing`, `verification-before-completion` |

---

## 4. AGENTIC DATA FLOW ARCHITECTURE

### 4.1 High-Level Data Flow

```
[USER INPUT / WHATSAPP / FORM]
        |
        v
[INTAKE LAYER] (src/intake/)
        |
        v
[AGENT ORCHESTRATOR] <---> (src/agents/orchestrator.py) NEW
        |
        +---> [SCOUT AGENT]          When: NB02 flags missing info
        |         |                       Source: Sherpa API, weather, advisories
        |         v                       Output: Enriched CanonicalPacket
        |     [SPINE AS TOOL]        Agent calls run_spine_once() with new context
        |
        +---> [COMMUNICATOR AGENT]  When: Pipeline hits 'blocked' state
        |         |                       Action: Draft 1-3 clarification msgs
        |         v                       Output: Message drafts for operator
        |     [SPINE AS TOOL]        Agent validates drafts via spine
        |
        +---> [QA AGENT]            When: Cron/event scans failed runs
        |         |                       Action: Analyze failures, generate fixtures
        |         v                       Output: New test cases in data/fixtures/
        |     [FILE/GIT TOOLS]       Agent writes fixtures, optional PRs
        |
        +---> [COMMITTEE SYSTEM]     When: Strategy phase needs tiered options
        |         |
        |         +--> [BUDGET OPTIMIZER]   Mandate: Minimize cost
        |         +--> [EXPERIENCE MAXIMIZER] Mandate: Maximize comfort
        |         |
        |         v
        |     [TRIP ARCHITECT]       Synthesize into High/Med/Low tiers
        |         |
        |         v
        |     [SPINE AS TOOL]       Validate each tier via spine
        |
        +---> [OPERATOR COPILOT]     When: Operator speaks natural language
                  |                       Action: Parse intent, mutate packet
                  v                       Output: Updated pipeline state
              [SPINE AS TOOL]        Re-trigger from appropriate stage
```

### 4.2 Spine Interaction Pattern (CRITICAL)

The spine (`run_spine_once()`) must remain PURE and DETERMINISTIC. Agents use it as a tool:

```python
# PATTERN: Agent uses spine as deterministic tool
class SomeAgent(BaseAgent):
    def execute(self, packet: CanonicalPacket, context: dict) -> AgentResult:
        # 1. Agent does its specialized work (gather info, draft messages, etc.)
        enriched = self.do_specialized_work(packet, context)

        # 2. Agent invokes spine AS A TOOL for judgment/processing
        #    Does NOT modify spine internals
        spine_result = self.orchestrator.run_spine_as_tool(
            base_packet=enriched,
            additional_context=context,
            operating_mode="agent_enrichment"
        )

        # 3. Return result for further processing
        return AgentResult(
            status="completed",
            packet=spine_result.packet,
            artifacts=spine_result.artifacts
        )
```

### 4.3 Inter-Agent Communication Flow

```
Agent A (sender)                Orchestrator               Agent B (receiver)
    |                               |                           |
    |-- AgentMessage(request) ----->|                           |
    |                               |-- route_message() -------->|
    |                               |                           |-- process()
    |                               |<-- AgentMessage(response) -|
    |<-- AgentMessage(response) ----|                           |
    |                               |                           |
```

Message types:
1. **Request-Reply**: Synchronous, agent waits for response (timeout + retry)
2. **Fire-and-Forget**: Asynchronous, no response expected (events, notifications)
3. **Broadcast**: One-to-many (agent publishes, subscribers receive)
4. **Blackboard**: Shared state space for coordination

### 4.4 Agent Lifecycle Flow

```
[CREATED] --> [INITIALIZING] --> [READY] --> [RUNNING] --> [COMPLETED]
                  |                 |           |              |
                  v                 v           v              v
              [FAILED]         [PAUSED]    [FAILED]       [ARCHIVED]
                  |                 |           |
                  v                 v           v
              [RETRY]           [RESUME]   [RETRY/ESCALATE]
```

### 4.5 State Management Flow

```
Short-Term (per invocation):
  - Current input, intermediate state, conversation turn
  - Stored in-memory during agent execution
  - Cleared after agent completes

Long-Term (across invocations):
  - Learned preferences, patterns, discoveries, corrections
  - Persisted to file storage or lightweight DB
  - Loaded on agent initialization

Persistent (agent definition):
  - Configuration, capabilities, version
  - Deployment metadata, usage stats, health
  - Read from YAML/JSON config files
```

---

## 5. FILE-BY-FILE SPECIFICATIONS

### 5.1 Foundation Layer

#### `src/agents/base_agent.py`
**Purpose**: Abstract base class for all product agents

```python
class BaseAgent(ABC):
    # Identity
    agent_id: str
    agent_type: AgentType  # SCOUT, COMMUNICATOR, QA, COMMITTEE, COPILOT
    version: str

    # Lifecycle
    @abstractmethod
    async def initialize(self, config: AgentConfig) -> None
    @abstractmethod
    async def execute(self, packet: CanonicalPacket, context: dict) -> AgentResult
    @abstractmethod
    async def shutdown(self) -> None

    # Tool Access
    @abstractmethod
    def declare_tools(self) -> List[ToolSpec]

    # State
    @abstractmethod
    def save_state(self) -> AgentState
    @abstractmethod
    def load_state(self, state: AgentState) -> None

    # Observability
    @abstractmethod
    def health_check(self) -> HealthStatus

    # Error Handling
    @abstractmethod
    def handle_error(self, error: Exception) -> ErrorAction
```

Key classes to implement:
- `BaseAgent` — Abstract base with lifecycle methods
- `AgentConfig` — Typed configuration model
- `AgentResult` — Standardized output contract
- `AgentState` — State persistence model
- `AgentType` — Enum of agent types
- `ToolSpec` — Tool declaration schema
- `HealthStatus` — Liveness/readiness status
- `ErrorAction` — Error handling strategies (retry/escalate/degrade/abort)

#### `src/agents/messages.py`
**Purpose**: Standardized inter-agent message types

```python
@dataclass
class AgentMessage:
    message_id: str
    sender_id: str
    recipient_id: str  # or "broadcast"
    message_type: MessageType  # REQUEST, RESPONSE, EVENT, COMMAND
    payload: dict
    correlation_id: str  # for request-reply correlation
    timestamp: datetime
    ttl: int  # time-to-live in seconds

@dataclass
class AgentEvent:
    event_type: str  # "agent.started", "agent.failed", "data.enriched", etc.
    source_agent: str
    payload: dict
    timestamp: datetime
```

#### `src/agents/registry.py`
**Purpose**: Agent discovery and instantiation

```python
class AgentRegistry:
    def register(agent_type: AgentType, agent_class: Type[BaseAgent]) -> None
    def get(agent_id: str) -> BaseAgent
    def list_agents(capability: str = None) -> List[AgentInfo]
    def create_agent(agent_type: AgentType, config: dict) -> BaseAgent
```

#### `src/agents/state.py`
**Purpose**: Agent state persistence

```python
class AgentStateManager:
    def save(agent_id: str, state: AgentState) -> None
    def load(agent_id: str) -> AgentState
    def clear(agent_id: str) -> None
    def list_active() -> List[str]
```

#### `src/agents/orchestrator.py`
**Purpose**: Core orchestration — agent lifecycle, messaging, supervision

```python
class AgentOrchestrator:
    # Lifecycle
    async def spawn(agent_type: AgentType, config: dict) -> str
    async def terminate(agent_id: str) -> None
    async def restart(agent_id: str) -> None

    # Messaging
    async def send_message(msg: AgentMessage) -> Optional[AgentMessage]
    async def broadcast(event: AgentEvent) -> None
    async def subscribe(agent_id: str, event_type: str) -> None

    # Spine Integration
    def run_spine_as_tool(packet, context, mode) -> SpineResult

    # Supervision
    async def health_check_all() -> Dict[str, HealthStatus]
    async def handle_failure(agent_id: str, error: Exception) -> None

    # Query
    def get_agent_status(agent_id: str) -> AgentStatus
    def list_active_agents() -> List[AgentInfo]
```

### 5.2 Specialized Agents

#### `src/agents/scout_agent.py`
**Purpose**: Proactive information retrieval when NB02 flags missing data
**Trigger**: NB02 returns flags like "missing_visa_requirement", "missing_weather_data"
**Input**: CanonicalPacket + list of missing data flags
**Output**: Enriched CanonicalPacket with gathered information
**Tools**: web (API calls), file (caching), terminal (script execution)
**External Sources**: Sherpa (visa), weather APIs, travel advisories, flight trackers
**Spine Usage**: Calls `run_spine_once()` with enriched packet to validate

#### `src/agents/communicator_agent.py`
**Purpose**: Autonomous clarification drafting when pipeline hits 'blocked' state
**Trigger**: NB02 returns `blocked` state with contradiction or critical ambiguity
**Input**: CanonicalPacket + blocked reason + ambiguity details
**Output**: 1-3 drafted clarification messages for operator selection
**Tools**: web (research tone/examples), file (templates), LLM (draft generation)
**Spine Usage**: Validates draft clarity via spine judgment
**Highest Value**: Plugs directly into existing blocked state — immediate operator relief

#### `src/agents/qa_agent.py`
**Purpose**: Self-healing evaluation loop from audit trail
**Trigger**: Background cron or event-based scan of failed/blocked runs
**Input**: List of failed run IDs from audit trail
**Output**: New test fixtures in `data/fixtures/`, optional PRs for prompt/extractor fixes
**Tools**: file (fixture manipulation), git via terminal, web (research if needed)
**Spine Usage**: Tests fixes by running spine against sanitized test cases

#### `src/agents/committee/budget_optimizer_agent.py`
**Purpose**: Find cost-effective routing/vendor combinations
**Mandate**: Minimize cost while meeting constraints
**Input**: CanonicalPacket with budget constraints
**Output**: Optimized proposal with cost breakdown
**Spine Usage**: Validates proposal feasibility via spine

#### `src/agents/committee/experience_maximizer_agent.py`
**Purpose**: Find comfort/premium routing/vendor combinations
**Mandate**: Maximize comfort, minimize layovers, premium selection
**Input**: CanonicalPacket with comfort preferences
**Output**: Premium proposal with experience highlights
**Spine Usage**: Validates proposal via spine

#### `src/agents/committee/trip_architect_agent.py`
**Purpose**: Synthesize optimizer/maximizer proposals into tiered options
**Input**: Budget Optimizer proposal + Experience Maximizer proposal
**Output**: High/Medium/Low tier options for operator presentation
**Spine Usage**: Validates each tier via spine

#### `src/agents/operator_copilot_agent.py`
**Purpose**: Conversational state intervention for natural language corrections
**Trigger**: Operator natural language input in workbench
**Input**: Operator message + current CanonicalPacket state
**Output**: Updated CanonicalPacket + re-triggered pipeline from appropriate stage
**Tools**: file (packet manipulation), LLM (intent parsing)
**Spine Usage**: Re-triggers spine from appropriate stage after mutation

---

## 6. IMPLEMENTATION PLAN — PHASED APPROACH

### Phase 1: Foundation (Week 1-2)

| # | File | Depends On | Skills to Load | Tests |
|---|------|------------|----------------|-------|
| 1.1 | `src/agents/messages.py` | None | `python-patterns` | `tests/agents/test_messages.py` |
| 1.2 | `src/agents/base_agent.py` | messages | `agent-harness-construction`, `python-patterns` | `tests/agents/test_base_agent.py` |
| 1.3 | `src/agents/registry.py` | base_agent | `agentic-engineering` | `tests/agents/test_registry.py` |
| 1.4 | `src/agents/state.py` | messages | `python-patterns` | `tests/agents/test_state.py` |
| 1.5 | `src/agents/orchestrator.py` | base_agent, registry, state, messages | `agent-orchestration`, `multi-agent-patterns`, `autonomous-loops` | `tests/agents/test_orchestrator.py` |
| 1.6 | `src/agents/__init__.py` | All above | — | Integration test |

**Verification Gate**: All foundation tests pass. Orchestrator can spawn a mock agent, send a message, and terminate it.

### Phase 2: Communicator Agent (Week 3)

| # | File | Depends On | Skills to Load | Tests |
|---|------|------------|----------------|-------|
| 2.1 | `src/agents/communicator_agent.py` | orchestrator | `agentic-engineering`, `verification-before-completion` | `tests/agents/test_communicator_agent.py` |
| 2.2 | Integrate with NB02 blocked state | communicator_agent | `systematic-debugging` | Integration test |
| 2.3 | Frontend integration | communicator_agent | `frontend-patterns` | E2E test |

**Verification Gate**: When NB02 returns `blocked`, Communicator Agent auto-spawns and drafts clarification messages. Operator can select draft in workbench.

### Phase 3: Scout Agent (Week 4)

| # | File | Depends On | Skills to Load | Tests |
|---|------|------------|----------------|-------|
| 3.1 | `src/agents/scout_agent.py` | orchestrator | `agent-harness-construction`, `agentic-engineering` | `tests/agents/test_scout_agent.py` |
| 3.2 | External API integrations | scout_agent | `api-design` | Integration test |
| 3.3 | Cache layer | scout_agent | `python-patterns` | Test with cache hits/misses |

**Verification Gate**: When NB02 flags missing info, Scout Agent auto-spawns, gathers data, enriches packet, spine re-evaluates.

### Phase 4: QA Agent (Week 5)

| # | File | Depends On | Skills to Load | Tests |
|---|------|------------|----------------|-------|
| 4.1 | `src/agents/qa_agent.py` | orchestrator | `agent-pipeline-local-testing`, `tdd-workflow` | `tests/agents/test_qa_agent.py` |
| 4.2 | Fixture generation pipeline | qa_agent | `python-testing` | Verify fixtures created |
| 4.3 | PII sanitization | qa_agent | `security-best-practices` | Sanitization tests |

**Verification Gate**: QA Agent scans failed runs, sanitizes PII, generates test fixtures, validates via spine.

### Phase 5: Committee System (Week 6)

| # | File | Depends On | Skills to Load | Tests |
|---|------|------------|----------------|-------|
| 5.1 | `src/agents/committee/__init__.py` | None | — | — |
| 5.2 | `src/agents/committee/budget_optimizer_agent.py` | orchestrator | `multi-agent-patterns`, `agentic-engineering` | `tests/agents/committee/test_budget_optimizer.py` |
| 5.3 | `src/agents/committee/experience_maximizer_agent.py` | orchestrator | `multi-agent-patterns`, `agentic-engineering` | `tests/agents/committee/test_experience_maximizer.py` |
| 5.4 | `src/agents/committee/trip_architect_agent.py` | orchestrator | `multi-agent-patterns`, `crewai-multi-agent` | `tests/agents/committee/test_trip_architect.py` |
| 5.5 | Committee orchestration integration | All committee agents | `agent-orchestration-multi-agent-optimize` | Integration test |

**Verification Gate**: Budget Optimizer and Experience Maximizer run concurrently, Trip Architect synthesizes tiered options.

### Phase 6: Operator Copilot (Week 6-7)

| # | File | Depends On | Skills to Load | Tests |
|---|------|------------|----------------|-------|
| 6.1 | `src/agents/operator_copilot_agent.py` | orchestrator | `agentic-engineering`, `python-patterns` | `tests/agents/test_operator_copilot.py` |
| 6.2 | Intent parsing via LLM | operator_copilot | `cost-aware-llm-pipeline` | Intent recognition tests |
| 6.3 | Packet mutation safety | operator_copilot | `security-review` | Mutation safety tests |

**Verification Gate**: Operator types natural language correction, Copilot parses intent, safely mutates packet, re-triggers spine.

---

## 7. ARCHITECTURAL GUARDRAILS

### 7.1 Spine Integrity (CRITICAL — NON-NEGOTIABLE)

- NEVER add agent state or logic to the spine pipeline
- NEVER modify `run_spine_once()` to accept agent-specific parameters
- ALWAYS invoke spine as a pure tool from agent code
- ALWAYS preserve the rules-first, LLM-for-judgment architecture

### 7.2 Additive Implementation

- Build alongside existing code — don't refactor what works
- Use feature flags for gradual agent rollouts
- Maintain backward compatibility with existing API contracts
- Only refactor when absolutely necessary for correctness

### 7.3 Observability From Day One

Every agent MUST have:
- Structured logging (JSON format per agent)
- Metrics (invocation count, latency p50/p95/p99, success/failure rate)
- Distributed tracing (trace/span IDs propagated through messages)
- Health checks (liveness + readiness endpoints)

### 7.4 Test-Driven Development

- Follow existing patterns (23 passing suitability tests)
- Write tests BEFORE implementation (TDD)
- Use `verification-before-completion` skill before marking any task done
- Run full test suite before AND after each agent integration

### 7.5 Cost Discipline

- Track per-agent LLM API costs
- Use cheaper models for simple tasks (classification, boilerplate)
- Reserve expensive models for complex judgment
- Cache aggressively (leverage existing decision cache patterns)

---

## 8. CROSS-REFERENCES

| Document | Path | Relationship |
|----------|------|--------------|
| Multi-Agent Infrastructure Assessment | `Docs/MULTI_AGENT_INFRASTRUCTURE_ASSESSMENT_2026-04-22.md` | Detailed specifications for each component |
| Hermes Development Agent Setup | `Docs/HERMES_DEVELOPMENT_AGENT_SETUP_2026-04-22.md` | How to use Hermes to build these components |
| Backend Code Quality Audit | `Docs/BACKEND_CODE_QUALITY_ARCHITECTURE_AUDIT_2026-04-18.md` | Existing code quality baseline |
| D1 Implementation Handoff | `Docs/D1_IMPLEMENTATION_AGENT_HANDOFF_2026-04-21.md` | Implementation agent patterns |
| Review Handoff Checklist | `Docs/IMPLEMENTATION_AGENT_REVIEW_HANDOFF_CHECKLIST.md` | Review protocol for agent work |
| Data Architecture Flow Audit | `Docs/DATA_ARCHITECTURE_FLOW_AUDIT_2026-04-18.md` | Existing data flow analysis |
| Master Product Spec | `Docs/MASTER_PRODUCT_SPEC.md` | Product requirements |
| Cross-Project Agentic Patterns | `Docs/CROSS_PROJECT_AGENTIC_PATTERNS_2026-04-20.md` | Agentic patterns across projects |

---

## 9. VERIFICATION & SIGN-OFF

This document serves as the implementation plan for building the multi-agent infrastructure into travel_agency_agent. Each phase has clear verification gates that must pass before proceeding to the next phase.

**Implementation Start Condition**: Phase 1 foundation can begin immediately — no external dependencies beyond existing codebase.

**First Actionable Step**: Create `src/agents/messages.py` and `src/agents/base_agent.py` following the specifications above.