# Agent Readiness Assessment
**Project**: travel_agency_agent (Waypoint OS spine)
**Date**: 2026-04-22
**Prepared by**: Hermes Agent
**Status**: Final

## Executive Summary
The travel_agency_agent project has a **production-ready deterministic spine pipeline** with excellent documentation for multi-agent capabilities, but **zero multi-agent infrastructure is implemented**. All Wave B agent concepts (Scout, Communicator, QA, Committee, Operator Copilot) exist as design documents only. The agent directories (`src/agents/`, `src/llm/agents/`) are empty packages.

The system is fundamentally a **compiler pipeline (NB01→NB02→NB03)** with deterministic rules first, LLM second for semantic judgment — not an agentic swarm. To become multi-agent, infrastructure must be built before agent specializations can be added.

## Current State: What's Built
### ✅ Deterministic Spine Pipeline (Production Ready)
- `src/intake/orchestration.py`: Single entrypoint `run_spine_once()` chains:
  NB01 (Extract) → Validate → NB02 (Decision) → NB03 (Strategy) → Safety → Fees
- `src/intake/decision.py`: Hybrid decision engine (rules + LLM)
  - Rule engine: deterministic gap/ambiguity detection
  - LLM layer: Gemini Flash (primary), GPT-4o-mini (fallback), local LLM (last resort)
  - Feature-flagged: `USE_HYBRID_DECISION_ENGINE=1`
- `src/suitability/`: Tier 1/2 scoring catalog (18 activities, deterministic)
- `src/intake/gates.py`: NB01/NB02 gates with `AutonomyOutcome`
- `src/llm/`: Gemini, OpenAI, local LLM clients (single-decision calls)
- `src/fees/calculation.py`: Trip fee calculator
- Frontend: Next.js workbench with 5 screens (Intake, Decision, Strategy, Safety, Flow Sim)

### ❌ Missing: Multi-Agent Infrastructure
- No agent orchestrator/router
- No agent registry or pool
- No inter-agent communication bus
- No agent state persistence
- No agent timeout/retry policies
- `src/agents/__init__.py`: empty
- `src/llm/agents/__init__.py`: empty

### ❌ Missing: Agent Feedback Loop (Spec Written, Not Built)
- Override API spec: WRITTEN (`AGENT_FEEDBACK_LOOP_SPEC_2026-04-22.md`)
- Override implementation: NOT BUILT
- `CachedDecision.feedback_count`: Schema exists, nothing populates it
- `AutonomyPolicy.learn_from_overrides`: Flag exists, no impl

### ❌ Missing: Governance / Roles (Partial)
- Role vocabulary: DRIFTING (3 different role catalogs)
- Assignment/reassignment: Frontend stubs exist, no backend impl
- Admin UX for AI behavior: NOT BUILT

### ❌ Missing: Integration Gaps
- No external API integrations (Sherpa, visa, flights)
- No WhatsApp/email sending capability
- No persistent database (JSON file storage only)
- No caching layer for LLM calls (spec mentions it, not built)

## Wave B Agent Concepts (Design Only)
These exist as **excellent documentation but zero implementation**:

| Agent | Doc | Status | Key Inputs | Key Outputs |
|-------|-----|--------|------------|-------------|
| **Scout** (Proactive Info Retrieval) | WAVE_B doc (Sec 1) | Design only | Missing info flags (visa, requirements) | Real-time data from external APIs |
| **Communicator** (Autonomous Clarification Drafting) | WAVE_B doc (Sec 2) | Design only | Blocked state + DecisionState | 1-3 empathetic message drafts for operator |
| **QA Agent** (Self-Healing Evaluation Loop) | WAVE_B doc (Sec 3) | Design only | Audit trail (failed/blocked runs) | JSON test fixtures + optional PRs |
| **Budget Optimizer** | WAVE_B doc (Sec 4) | Design only | Complex trip constraints | Cost-effective routing/vendor combos |
| **Experience Maximizer** | WAVE_B doc (Sec 4) | Design only | Complex trip constraints | Comfort/premium routing/vendor combos |
| **Trip Architect** (Synthesizer) | WAVE_B doc (Sec 4) | Design only | Optimizer/Maximizer proposals | Blended StrategyBundle (High/Med/Low tiers) |
| **Operator Copilot** (Conversational State Intervention) | WAVE_B doc (Sec 5) | Design only | Operator natural language | Safe packet mutation + pipeline re-trigger |

## Persona Impact: What's Missing
From `PERSONA_PROCESS_GAP_ANALYSIS_2026-04-16.md`:

**P1 Solo Agent (Priya)**:
- ❌ Customer recognition / history lookup
- ❌ WhatsApp paste → auto-process
- ❌ Trip-scoped workspace (inbox links to `/workbench` not `/workspace/[tripId]`)
- ❌ Quote/proposal builder (no option generator, no pricing)
- ❌ Send proposal to client (no output delivery)
- ❌ Follow-up tracking (no engagement timeline)
- ❌ Budget feasibility check (no min-cost logic)
- ❌ Urgency handling (doesn't suppress soft blockers)
- ❌ Ambiguity detection (proceeds on ambiguous data)
- ❌ Change management (no revision tracking)
- ❌ Document tracking (manual in WhatsApp)
- ❌ Cancellation handling (no penalty engine)
- ❌ Post-trip follow-up (no lifecycle)
- ❌ Booking confirmation workflow (no readiness checks)

**P2 Agency Owner (Rajesh)**:
- ❌ Weekend work review / junior agent quote validation
- ❌ Pipeline health monitoring
- ❌ Margin adherence tracking
- ❌ Agent utilization insights
- ❌ Escalation queue visibility
- ❌ Supplier exposure/risk concentration
- ❌ Conversion funnel analytics

## Shared Patterns: AdShot → WaypointOS (Not Adopted)
From `CROSS_PROJECT_AGENTIC_PATTERNS_2026-04-20.md`:

1. **Quality Gates at Every Pipeline Stage** (AdShot ADR-002)
   - WaypointOS has implicit boundaries but no explicit gate contract
   - Needed: `NB01CompletionGate`, `NB02JudgmentGate` with `proceed/retry/escalate/degrade`

2. **3-Layer Evaluation Scorecard** (AdShot external review)
   - WaypointOS `DecisionResult.confidence_score` is single float
   - Needed: Technical/Judgment/Commercial confidence layers
   - Feeds into D1 autonomy gates (auto-proceed only when ALL layers above threshold)

3. **Artifact Lineage** (AdShot asset tracking)
   - WaypointOS derived signals don't trace back to source facts
   - Needed: `derived_from: List[str]` on `Slot` model
   - Enables evidence display in override UX

## Governance & Principles (Well Documented)
- `V02_GOVERNING_PRINCIPLES.md`: Layer ownership (NB01/NB02/NB03), operating_mode axes
- Agent Feedback Loop spec: complete override lifecycle design
- Detailed Agent Map: exhaustive catalog (Core v1 Stack + Full Operational Stack)
- Cross-Project Patterns: validated approach via AdShot exchange

## Recommendation: Build Order
To go multi-agent while preserving deterministic core:

1. **Run Lifecycle State Machine** (Wave A prerequisite)
   - Enables orchestration awareness (running/completed/failed/blocked)

2. **Agent Orchestrator Pattern**
   - Router + registry for agent discovery/instantiation
   - Inter-agent communication (message bus or shared state)
   - State persistence for agent context

3. **Single Specialist Agent: Communicator**
   - Simplest to implement (plugs into existing `blocked` state)
   - Highest immediate value (reduces operator cognitive load)
   - Reuse existing LLM clients + prompt engineering

4. **Operator Copilot**
   - Conversational patch + safe re-trigger
   - Requires Workspace domain boundary (frozen per FRONTEND_WAVE_2_READINESS)

5. **Scout Agent**
   - External API integrations (Sherpa, visa, flight trackers)
   - Caching layer for LLM/API calls

6. **Committee (Multi-Agent Debate)**
   - Budget Optimizer + Experience Maximizer + Trip Architect
   - LangGraph or similar for scoped debate workflow

## Risk Assessment
**Low Risk**: Deterministic spine remains untouched; agents additive
**Medium Risk**: Integration complexity (external APIs, state persistence)
**High Risk**: None if build order followed (spine → orchestrator → agents)

## Next Steps
Review `AGENTS.md` for skill locations and workflows, then begin implementing:
1. Agent orchestrator in `src/agents/orchestrator.py`
2. Communicator agent in `src/agents/communicator.py`
3. Override API endpoint in `spine_api/server.py`
