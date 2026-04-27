# Waypoint OS — Agentic Pipeline Audit
**Date**: 2026-04-27  
**Scope**: Full codebase — fresh-eyes structural review  
**Auditor**: Antigravity (Gemini)

---

## TL;DR

The **deterministic spine is excellent** — NB01→Validate→NB02→Strategy→Safety is clean, well-tested (53 test files), and properly separated from API concerns. The **hybrid decision engine** (rule→cache→LLM) is a strong foundation.

The problem is what's layered *around* the spine: **the "agentic" layer is mostly stubs and in-process simulations dressed up as real agents.** The frontier orchestrator, checker agent, federated intelligence, and negotiation engine are all synchronous, in-memory mock code embedded inside the spine itself — not real autonomous agents. The agent infrastructure directory (`src/agents/`) is literally empty.

This is not a failure — it's an honest, documented gap (AGENTIC_DATA_FLOW_AND_IMPLEMENTATION_PLAN_2026-04-22.md identifies it clearly). But it means **the system cannot yet be called agentic in any production sense.**

Here is the complete picture.

---

## 1. What Is Actually Working (✅)

| Layer | State | Evidence |
|-------|-------|----------|
| **Spine pipeline** (`run_spine_once`) | ✅ Solid | Clean 9-phase chain, proper early exits |
| **Extraction** (`extractors.py`, 57KB) | ✅ Solid | Comprehensive NLP extraction with authority tracking |
| **Validation** | ✅ Solid | Schema-validated `CanonicalPacket`, blocker/soft-blocker aware |
| **Decision engine** (`run_gap_and_decision`) | ✅ Working | MVB evaluation, contradiction classification, commercial decisions |
| **Hybrid engine** (rule→cache→LLM) | ✅ Working | 5 decision types, 18 rules, caching, telemetry |
| **Suitability scoring** | ✅ Working | Tier 1 + Tier 2, 23 passing tests |
| **Safety / leakage guard** | ✅ Working | Forbidden-terms scan on traveler bundle |
| **Fee calculation** | ✅ Working | Risk-adjusted, party-composition aware |
| **Gate system** (NB01/NB02) | ✅ Working | PROCEED/RETRY/ESCALATE/DEGRADE verdicts |
| **Autonomy policy** (D1 gate) | ✅ Working | Approval thresholds, mode overrides |
| **Persistence layer** | ✅ Working (dogfood) | TripStore, AuditStore, OverrideStore, ConfigStore |
| **Auth + multi-tenant shell** | ✅ Partial | JWT auth, agency scoping, workspace concept |
| **Frontend workbench** | ✅ Partial | Inbox, workbench, settings, owner views |
| **Test coverage** | ✅ Strong | 53 test files covering most spine stages |

---

## 2. The Core Structural Problem: "Frontier" Is a Facade

The biggest architectural issue is that **"agentic" features are implemented as synchronous subroutines inside the spine run**, not as real agents.

### 2.1 `frontier_orchestrator.py` — 128 lines, all synchronous

```python
# What it claims to be:
"Ghost Concierge, Emotional State Monitoring, Intelligence Pool Integration"

# What it actually does:
def _calculate_sentiment_heuristic(packet):  # keyword scan, not LLM
    score = 0.5
    for word in stress_keywords: score -= 0.05   # <-- this is not sentiment analysis
    
def run_frontier_orchestration(packet, decision):
    # Synchronous, blocking, no I/O, no network, no async
    # Returns immediately with fake data
```

**Issue**: This runs inside `run_spine_once()` on every trip. If it ever actually called an LLM or external API, it would block the request. The "Ghost Concierge trigger" sets a flag but does nothing — no workflow is actually launched.

### 2.2 `federated_intelligence.py` — In-memory mock, loses data on restart

```python
class FederatedIntelligenceService:
    def __init__(self):
        self._pool: List = []   # <-- in-memory, not persisted
    
    def query_risks(self, location: str):
        # Hardcoded mock: always returns Singapore visa spike
        if not hits and "Singapore" in location:
            hits.append({"type": "visa_processing_delay", ...})
```

**Issue**: Every process restart loses all reported incidents. The "federation" is a singleton list. This is a local variable, not a federated intelligence pool.

### 2.3 `checker_agent.py` — Heuristic rule check, not an agent

```python
class CheckerAgent:
    def audit(self, packet, decision):
        # 3 heuristic checks (missing budget, high-risk purpose, low confidence)
        # No LLM, no external judgment, no second model
        # Returns immediately
```

**Issue**: Named "agent" but is a pure function with 3 if-statements. A second LLM pass or different model (as the docstring intends: "Claude 3.5 → GPT-4o") is never actually invoked.

### 2.4 `negotiation_engine.py` — Static price arithmetic

```python
def _identify_opportunities(self, packet, decision):
    if pax_count >= 8:
        opportunities.append(NegotiationOpportunity(
            supplier_name=f"Grand {dest} Hotel",
            original_price=1200.0,       # hardcoded
            target_price=950.0,          # hardcoded
```

**Issue**: No real supplier API, no actual negotiation, no state persistence. Returns fake "NEGOTIATING" status immediately.

### 2.5 `src/agents/` directory — Empty

```
src/agents/
└── __init__.py   # "# src/agents package" — literally just a comment
```

The entire agent infrastructure documented in `AGENTIC_DATA_FLOW_AND_IMPLEMENTATION_PLAN_2026-04-22.md` has not been built.

---

## 3. Architectural Smell: Spine Is Doing Too Much

`orchestration.py:run_spine_once()` currently runs:
1. Extraction
2. Validation  
3. NB01 gate
4. Decision
5. Suitability assessment ← *added as Phase 3.5*
6. NB02 gate
7. **Frontier orchestration** ← *all four "agents" run here synchronously*
8. Strategy
9. Internal bundle
10. Traveler bundle
11. Sanitization
12. Leakage check
13. Fee calculation
14. Fixture compare

**Every trip processes through all 14 phases synchronously in one HTTP request.** This works at demo scale. At production scale (say, 1000 trips/day), this is a bottleneck because:
- Any slow phase blocks the request thread
- No ability to retry a single phase independently
- No ability to run phases in parallel where possible (e.g., suitability + frontier can be concurrent)
- No ability to defer async work (e.g., negotiation, federated intelligence query)

> **Root cause**: The spine was designed correctly as a deterministic processor, but subsequent features were attached in-line rather than decoupled as separate concerns.

---

## 4. Decision Layer: `decision.py` Is a Monolith (2,241 Lines)

The file contains at minimum 7 distinct responsibilities:
- Budget bucket tables (230+ lines of hardcoded destination data)
- Ambiguity classification
- Contradiction classification
- Field resolution logic
- Budget feasibility calculation
- Risk flag generation
- The main orchestrator (`run_gap_and_decision`)
- Commercial decision scoring
- Confidence scoring
- Destination alias mapping

**Why this matters for agentic development**: When agents need to query or modify a specific concern (e.g., budget feasibility), they have to import from a 2,241-line file with no clear boundaries. This creates tight coupling that will make agent wiring brittle.

The existing audit (`AUDIT_CLOSURE_TRIAGE_2026-04-26.md`) correctly rates this as P1 technical debt. The **primary refactor target** is the budget bucket table (lines 505–786) — 280+ lines of static data that should be in a JSON/YAML config file, not Python source.

---

## 5. Persistence: Three Unconnected Event Streams

There are currently **three separate audit/event systems** that don't talk to each other:

| System | Location | What It Captures |
|--------|----------|-----------------|
| `AuditStore` | `persistence.py` | Manual audit events (trip_created, trip_assigned) |
| `TripEventLogger` | `analytics/logger.py` | Stage transitions, timeline events |
| `RunLedger` | `spine_api/run_ledger.py` | Run lifecycle (started, completed, failed, blocked) |

**Problem**: To reconstruct "what happened to trip X", you have to query all three systems separately. There's no unified event bus or single source of truth for trip history. The `_emit_audit_event()` function in `orchestration.py` bridges to `TripEventLogger`, but `AuditStore` and `RunLedger` have their own independent paths.

**Impact on agents**: When a QA agent or monitoring agent wants to analyze failed runs, it has to understand three different storage formats and query patterns.

---

## 6. The `agency_id` Isolation Problem

The code has multi-tenant *scaffolding* but the spine itself ignores `agency_id`:

```python
# server.py line 560:
agency_settings = AgencySettingsStore.load("waypoint-hq")  # ← hardcoded!
```

The `run_spine_once()` function signature accepts `agency_settings` but the actual agency of the calling user is not reliably extracted from the request:

```python
# server.py lines 583-587:
try:
    agency_id = get_current_agency_id(credentials=Depends(security_bearer), db=Depends(get_db))
except Exception:
    agency_id = None   # <-- silently falls back to None
```

`Depends()` is a FastAPI concept that only works *inside* a route function's parameters — calling it manually like this doesn't work. The agency_id will always be `None` here. This means **all trips save to no agency**, breaking the multi-tenant model at the persistence layer.

---

## 7. LLM Usage Guard: Production-Unsafe (Already Documented, Not Fixed)

The in-memory `LLMUsageGuard` singleton is known to be broken across 4 uvicorn workers (each gets its own counter). This was identified in `AUDIT_CLOSURE_TRIAGE_2026-04-26.md` as P0 before production. It remains unfixed.

> **Current risk**: 4 workers × ₹1,000 daily budget = ₹4,000 effective daily spend limit at production deployment.

---

## 8. What the "Agentic" Path Forward Actually Requires

Based on the documented plan (`AGENTIC_DATA_FLOW_AND_IMPLEMENTATION_PLAN_2026-04-22.md`) and the actual codebase, here is the honest gap:

### Phase 0 — Cleanup Before Agent Build (Not Doing This Will Cause Pain)

| Task | Why It Matters |
|------|---------------|
| Fix the hardcoded `"waypoint-hq"` agency_id in `/run` endpoint | Agents need to know which agency they're working for |
| Fix `Depends()` abuse in `run_spine()` — use proper route parameter injection | Currently breaks agency scoping silently |
| Extract budget bucket table from `decision.py` to `data/budget_tables.yaml` | Agents need to reference/modify budgets without importing 2k-line file |
| Add event correlation — `trip_id` + `run_id` should flow through all three event systems | Agents need coherent trip history |
| SQLite-back the LLMUsageGuard | Required before production |

### Phase 1 — Real Agent Infrastructure (`src/agents/`)

The plan is already written. The directory is empty. The build is:

```
src/agents/
├── messages.py        # AgentMessage, AgentEvent types
├── base_agent.py      # BaseAgent ABC with lifecycle methods
├── registry.py        # AgentRegistry for discovery
├── state.py           # AgentStateManager for persistence
└── orchestrator.py    # AgentOrchestrator (spawn, route, supervise)
```

### Phase 2 — Decouple Frontier From Spine

Move the frontier orchestration **out of** `run_spine_once()` and into an **async post-processing step**:

```
HTTP /run request:
  1. run_spine_once() → synchronous result (same as today)
  2. Return result immediately to caller
  3. Enqueue async work:
     - Frontier orchestration (sentiment, ghost trigger, intelligence query)
     - Negotiation engine
     - Checker agent (if confidence low)
```

This preserves spine purity while enabling real async agent behavior.

### Phase 3 — Implement First Real Agent: Communicator Agent

The highest-value first real agent: when NB02 returns `blocked`, auto-draft 1-3 clarification messages for the operator to send to the traveler. This plugs directly into the existing blocked state and requires:
- LLM call (draft generation)
- Spine call (validate draft clarity)
- Persistence (save draft for operator)

This is a real, testable, user-visible agentic behavior.

---

## 9. Structural Issues Not Previously Audited

### 9.1 Empty Module Directories

```
src/agents/        — documented as ❌ Not started
src/agents/llm/    — empty __init__.py
src/pipelines/     — empty __init__.py  
```

`src/pipelines/` in particular is confusing — it's in the source tree but empty and unused. Should be removed or populated.

### 9.2 `page.bak.tsx` in Production Source Tree

```
frontend/src/app/page.bak.tsx   # 10KB backup file
```

Backup files in the source tree are a code smell. Should be removed or git-ignored.

### 9.3 Duplicate Destination Aliases in `decision.py`

```python
# Lines 526-530: "Andaman" key in BUDGET_BUCKET_RANGES
# Lines 656-664: "Andamans" key in BUDGET_BUCKET_RANGES (duplicate, same data)
# Lines 788-789: _DESTINATION_ALIASES["Andamans"] = "Andaman"

# Also:
# "Istanbul" key in BUDGET_BUCKET_RANGES (lines 716-725)
# _DESTINATION_ALIASES["Istanbul"] = "Turkey"  — but Istanbul already has its own entry
```

This creates ambiguous lookup behavior and inconsistent cost estimates depending on how the destination string arrives.

### 9.4 `print()` Statements in Production Code

```python
# decision.py line 55:
print(f"Warning: Failed to initialize hybrid engine: {e}")

# decision.py line 136:
print(f"Warning: Hybrid engine failed for {decision_type}: {e}")
```

These should be `logger.warning()`. They bypass the logging infrastructure and won't be captured by any monitoring system.

### 9.5 Singleton Modules Without Cleanup

```python
# federated_intelligence.py:
intelligence_service = FederatedIntelligenceService()   # module-level singleton

# negotiation_engine.py:
negotiation_service = NegotiationEngine()               # module-level singleton

# checker_agent.py:
checker_agent = CheckerAgent()                          # module-level singleton
```

All three are module-level singletons with mutable state. In a multi-worker deployment, each worker gets its own singleton, so state is not shared. This is expected for stateless objects, but the `NegotiationEngine` has `self.active_haggles: Dict` which is instance-state that will never be shared between workers.

### 9.6 `_hybrid_engine_instance` Global Singleton in `decision.py`

```python
# decision.py line 33:
_hybrid_engine_instance = None  # global, module-level

def _get_hybrid_engine():
    global _hybrid_engine_instance
    if _hybrid_engine_instance is None:
        _hybrid_engine_instance = create_hybrid_engine(...)
```

This works fine in a single-process but is reset on every worker restart. The hybrid engine's in-memory rule cache is lost on each restart, requiring re-registration of all 18 rules. This is not a bug (rules are registered from code), but the metrics/telemetry are lost.

---

## 10. Priority Action Matrix

### 🔴 P0 — Fix Before Any Agent Work

| # | Issue | File | Fix |
|---|-------|------|-----|
| P0.1 | Hardcoded `"waypoint-hq"` agency_id in `/run` endpoint | `server.py:560` | Pass `current_user.agency_id` from route dependency |
| P0.2 | `Depends()` misuse — agency_id always `None` | `server.py:583-587` | Use route parameter for agency extraction |
| P0.3 | LLMUsageGuard not shared across 4 workers | `usage_guard.py` | SQLite-backed storage (per triage doc) |

### 🟡 P1 — Before Production

| # | Issue | Fix |
|---|-------|-----|
| P1.1 | Frontier orchestration blocks every `/run` request synchronously | Decouple to async post-processing |
| P1.2 | Three separate event systems with no correlation | Add `trip_id` correlation across AuditStore, TripEventLogger, RunLedger |
| P1.3 | Budget bucket table hardcoded in `decision.py` | Extract to `data/budget_tables.yaml` |
| P1.4 | Duplicate destination entries in budget tables | Consolidate Andaman/Andamans, Istanbul/Turkey |
| P1.5 | `print()` statements in `decision.py` | Replace with `logger.warning()` |

### 🟢 P2 — Agent Infrastructure Build

| # | Task | Priority Rationale |
|---|------|--------------------|
| P2.1 | Build `src/agents/` foundation (messages, base, registry, state, orchestrator) | Gate for all real agent work |
| P2.2 | Implement Communicator Agent (first real agent) | Highest user-visible value, clear trigger state |
| P2.3 | Implement Scout Agent with real external API calls (Sherpa visa, weather) | Fills the actual data gap that blocks NB02 most often |
| P2.4 | Replace `federated_intelligence.py` in-memory mock with persistent store | Required for any meaningful cross-trip intelligence |
| P2.5 | Replace sentiment heuristic with actual LLM sentiment call (async) | Current keyword scan is not sentiment analysis |

### 🔵 P3 — Platform

| # | Task |
|---|------|
| P3.1 | Remove `src/pipelines/` empty directory |
| P3.2 | Remove `page.bak.tsx` from source tree |
| P3.3 | Refactor `checker_agent.py` into real second-model pass |
| P3.4 | Build real negotiation engine with supplier API integration |
| P3.5 | PostgreSQL migration for TripStore |

---

## 11. The One Strategic Decision That Unlocks Everything

> **Should the frontier orchestration run synchronously inside the spine, or asynchronously after the spine returns?**

Currently: synchronous (everything in one HTTP request)  
This creates: request latency pressure, inability to retry, inability to parallelize

**Recommended**: Spine stays pure and synchronous. Frontier/agents run async after spine returns.

```
Client → POST /run
           ↓
       run_spine_once()      ← synchronous, fast, deterministic
           ↓
       save_processed_trip() ← synchronous
           ↓
       return SpineRunResponse to client  ← immediate
           ↓ (background)
       enqueue_async_work(trip_id):
         - frontier_orchestration()
         - negotiation_check()
         - checker_agent() if low confidence
         - federated_intel query
```

This one architectural decision enables real agents: they run as background workers responding to events, not as blocking code in the request path.

The infrastructure for this (background tasks) is trivially available in FastAPI via `BackgroundTasks`. The agent orchestrator handles the rest.

---

## 12. Honest Assessment

| Dimension | Score | Notes |
|-----------|-------|-------|
| **Deterministic pipeline quality** | 9/10 | Excellent — well-tested, clean, proper separation |
| **Actual agentic capability** | 2/10 | Stubs dressed as agents; no real autonomy |
| **Code structure** | 6/10 | Good in most places; `decision.py` is a monolith |
| **Test coverage** | 8/10 | 53 test files, real scenarios, good fixture system |
| **Production readiness** | 4/10 | JSON persistence, in-memory guard, hardcoded agency_id |
| **Documentation** | 9/10 | Exceptional — plans, specs, ADRs all exist |
| **Gap between docs and code** | 🔴 High | The plan is excellent; the implementation hasn't caught up |

**The system is a very strong prototype with excellent foundations.** The path to real agentic capability is clear and the documentation is ahead of the code. The build order is: fix P0 issues → build real agent infrastructure → move frontier async → implement Communicator Agent as proof of concept → expand from there.

---

*Audit completed: 2026-04-27*  
*Files reviewed: server.py (1973 lines), decision.py (2241 lines), orchestration.py (620 lines), hybrid_engine.py (821 lines), persistence.py (660 lines), frontier_orchestrator.py (128 lines), federated_intelligence.py (70 lines), checker_agent.py (77 lines), negotiation_engine.py (103 lines), AUDIT_CLOSURE_TRIAGE_2026-04-26.md, AGENTIC_DATA_FLOW_AND_IMPLEMENTATION_PLAN_2026-04-22.md, and 53 test files inventoried*
