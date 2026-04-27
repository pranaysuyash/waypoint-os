# Waypoint OS — Agentic Pipeline Code Audit
**Date**: 2026-04-27  
**Scope**: Full codebase — fresh-eyes structural review  
**Companion doc**: `FIRST_PRINCIPLES_AGENTIC_AUDIT_2026-04-27.md`

---

## TL;DR

The **deterministic spine is excellent** — NB01→Validate→NB02→Strategy→Safety is clean, well-tested, and properly separated from API concerns. The **hybrid decision engine** (rule→cache→LLM) is a strong foundation.

The problem is what's layered *around* the spine: **the "agentic" layer is mostly stubs and in-process simulations dressed up as real agents.** The frontier orchestrator, checker agent, federated intelligence, and negotiation engine are all synchronous, in-memory mock code embedded inside the spine itself — not real autonomous agents. The agent infrastructure directory (`src/agents/`) is literally empty.

---

## 1. What Is Actually Working (✅)

| Layer | State | Evidence |
|-------|-------|----------|
| **Spine pipeline** (`run_spine_once`) | ✅ Solid | Clean 9-phase chain, proper early exits |
| **Extraction** (`extractors.py`) | ✅ Solid | Comprehensive NLP extraction with authority tracking |
| **Validation** | ✅ Solid | Schema-validated `CanonicalPacket`, blocker/soft-blocker aware |
| **Decision engine** (`run_gap_and_decision`) | ✅ Working | MVB evaluation, contradiction classification, commercial decisions |
| **Hybrid engine** (rule→cache→LLM) | ✅ Working | 5 decision types, 18 rules, caching, telemetry |
| **Suitability scoring** | ✅ Working | Tier 1 + Tier 2, 23 passing tests |
| **Safety / leakage guard** | ✅ Working | Forbidden-terms scan on traveler bundle |
| **Fee calculation** | ✅ Working | Risk-adjusted, party-composition aware |
| **Gate system** (NB01/NB02) | ✅ Working | PROCEED/RETRY/ESCALATE/DEGRADE verdicts |
| **Autonomy policy** (D1 gate) | ✅ Working | Approval thresholds, mode overrides |
| **Persistence layer** | ✅ Working (dogfood) | TripStore, AuditStore, OverrideStore, ConfigStore |
| **Test coverage** | ✅ Strong | 53 test files covering most spine stages |

---

## 2. The Core Structural Problem: "Frontier" Is a Facade

### 2.1 `frontier_orchestrator.py` — 128 lines, all synchronous

```python
# Claims: "Ghost Concierge, Emotional State Monitoring, Intelligence Pool Integration"
# Reality: synchronous keyword scan, no I/O, no network, returns immediately with fake data

def _calculate_sentiment_heuristic(packet):
    score = 0.5
    for word in stress_keywords: score -= 0.05   # not sentiment analysis
```

The "Ghost Concierge trigger" sets a flag but launches no workflow. Runs inside `run_spine_once()` on every trip, blocking the request thread.

### 2.2 `federated_intelligence.py` — In-memory mock, loses data on restart

```python
class FederatedIntelligenceService:
    def __init__(self):
        self._pool: List = []   # in-memory, not persisted

    def query_risks(self, location):
        # Hardcoded mock: always returns Singapore visa spike
        if not hits and "Singapore" in location:
            hits.append({...})
```

Every process restart loses all reported incidents. Not a federated pool — a local list.

### 2.3 `checker_agent.py` — 3 if-statements, not an agent

```python
class CheckerAgent:
    def audit(self, packet, decision):
        # 3 heuristic checks (missing budget, high-risk purpose, low confidence)
        # No LLM, no external judgment, no second model, returns immediately
```

Named "agent" but is a pure function. The docstring says "call a different LLM model (e.g. Claude 3.5 → GPT-4o)" — this never happens.

### 2.4 `negotiation_engine.py` — Static price arithmetic

```python
opportunities.append(NegotiationOpportunity(
    supplier_name=f"Grand {dest} Hotel",
    original_price=1200.0,   # hardcoded
    target_price=950.0,      # hardcoded
    reason="Group volume discount (8+ pax)"
))
```

No supplier API, no actual negotiation, returns fake "NEGOTIATING" status immediately.

### 2.5 `src/agents/` — Empty

```
src/agents/
└── __init__.py   # "# src/agents package" — literally just a comment
```

The entire agent infrastructure documented in `AGENTIC_DATA_FLOW_AND_IMPLEMENTATION_PLAN_2026-04-22.md` has not been built.

---

## 3. Architectural Issues

### 3.1 Spine Is Doing Too Much (14 phases, all synchronous)

`run_spine_once()` currently runs all of: extraction, validation, NB01, decision, suitability, NB02, **frontier orchestration**, strategy, bundles, sanitization, leakage, fees, fixture compare — in one HTTP request.

Every trip processes through all 14 phases synchronously. No ability to retry a single phase, run phases concurrently, or defer async work.

### 3.2 `decision.py` Is a 2,241-Line Monolith

Contains at minimum 7 distinct responsibilities mixed together:
- Budget bucket tables (280+ lines of hardcoded destination data)
- Ambiguity classification, contradiction classification, field resolution
- Budget feasibility calculation, risk flag generation
- The main orchestrator (`run_gap_and_decision`)
- Commercial decision scoring, confidence scoring

Primary refactor target: extract the budget bucket table to `data/budget_tables.yaml`.

### 3.3 Three Unconnected Event Streams

| System | Location | What It Captures |
|--------|----------|-----------------|
| `AuditStore` | `persistence.py` | Manual audit events |
| `TripEventLogger` | `analytics/logger.py` | Stage transitions |
| `RunLedger` | `spine_api/run_ledger.py` | Run lifecycle |

No unified event bus. To reconstruct "what happened to trip X" requires querying all three separately.

### 3.4 `agency_id` Is Always `None` in Production

```python
# server.py line 560:
agency_settings = AgencySettingsStore.load("waypoint-hq")  # hardcoded!

# server.py lines 583-587: Depends() called manually — doesn't work in FastAPI
agency_id = get_current_agency_id(credentials=Depends(security_bearer), ...)
# ↑ always None — multi-tenant model broken at persistence layer
```

### 3.5 LLMUsageGuard Not Shared Across 4 Workers

In-memory singleton. 4 uvicorn workers = 4 independent guards. Effective daily budget at production: 4× the configured limit. Identified in `AUDIT_CLOSURE_TRIAGE_2026-04-26.md` as P0, not yet fixed.

---

## 4. Smaller Issues Not Previously Audited

| Issue | Location | Severity |
|-------|----------|----------|
| `print()` statements instead of `logger.warning()` | `decision.py` lines 55, 136 | P2 |
| Duplicate destination entries (Andaman/Andamans, Istanbul/Turkey) | `decision.py` budget tables | P2 |
| `page.bak.tsx` backup file in production source tree | `frontend/src/app/` | P3 |
| `src/pipelines/` empty directory, unused | `src/pipelines/__init__.py` | P3 |
| `NegotiationEngine.active_haggles` dict is per-worker, never shared | `negotiation_engine.py` | P2 |

---

## 5. Priority Action Matrix

### 🔴 P0 — Fix Before Any Agent Work

| # | Issue | File | Fix |
|---|-------|------|-----|
| P0.1 | Hardcoded `"waypoint-hq"` agency_id | `server.py:560` | Pass `current_user.agency_id` from route dependency |
| P0.2 | `Depends()` misuse — agency_id always `None` | `server.py:583-587` | Use route parameter for agency extraction |
| P0.3 | LLMUsageGuard not shared across 4 workers | `usage_guard.py` | SQLite-backed storage |

### 🟡 P1 — Before Production

| # | Issue | Fix |
|---|-------|-----|
| P1.1 | Frontier orchestration blocks every `/run` synchronously | Decouple to async post-processing (FastAPI `BackgroundTasks`) |
| P1.2 | Three event systems with no correlation | Add `trip_id` as correlation key across all three |
| P1.3 | Budget bucket table hardcoded in `decision.py` | Extract to `data/budget_tables.yaml` |
| P1.4 | Duplicate destination entries | Consolidate Andaman/Andamans, Istanbul/Turkey |
| P1.5 | `print()` in production decision code | Replace with `logger.warning()` |

### 🟢 P2 — Agent Infrastructure Build

| # | Task | Priority Rationale |
|---|------|--------------------|
| P2.1 | Build `src/agents/` foundation | Gate for all real agent work |
| P2.2 | Move frontier orchestration to async (BackgroundTasks) | Unlocks real event-driven agent behavior |
| P2.3 | Implement Communicator Agent (first real agent) | Highest user-visible value, clear trigger state |
| P2.4 | Replace federated intelligence in-memory mock with persistent store | Required for meaningful cross-trip intelligence |

---

## 6. The One Architectural Decision That Unlocks Everything

> **Move frontier orchestration out of the synchronous request path.**

```
Client → POST /run
           ↓
       run_spine_once()      ← synchronous, fast, deterministic (same as today)
           ↓
       return SpineRunResponse to client  ← immediate
           ↓ (background via FastAPI BackgroundTasks)
       enqueue_async_work(trip_id):
         - frontier_orchestration()
         - negotiation_check()
         - checker_agent() if low confidence
```

This preserves spine purity, eliminates request blocking, and enables real event-driven agent behavior. FastAPI's `BackgroundTasks` requires zero new infrastructure.

---

*Code audit — 2026-04-27*  
*Files reviewed: server.py, decision.py, orchestration.py, hybrid_engine.py, persistence.py, frontier_orchestrator.py, federated_intelligence.py, checker_agent.py, negotiation_engine.py*
