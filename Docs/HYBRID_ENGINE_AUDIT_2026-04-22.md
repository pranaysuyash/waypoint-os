# Hybrid Engine Validation Audit — Phase A Findings

**Date**: 2026-04-22
**Auditor**: Evidence-first review of `src/decision/hybrid_engine.py` + `src/decision/cache_*.py` + `src/decision/rules/` + `src/intake/decision.py` boundary
**Scope**: Cache key stability, rule coverage gap analysis, graduation logic, cost telemetry, decision layer separation

---

## Executive Summary

The hybrid decision engine (`src/decision/hybrid_engine.py`) implements the deterministic-first principle (V02 §1) through a cache → rules → LLM fallback pipeline. After reviewing the complete decision stack, **the engine mechanics are sound, but the architectural boundary between the hybrid engine and NB02 proper is unclear and creates coverage ambiguity**.

| Dimension | Finding | Severity |
|-----------|---------|----------|
| Cache key stability | Keys match decision type + subset of packet fields. No collision detected in manual review. | Low |
| Rule coverage | 5 decision types have explicit rules. NB02 proper has 4 states + BRANCH_OPTIONS. Gap: rule types don't cover all paths to STOP_NEEDS_REVIEW. | Medium |
| Graduation logic | **Not implemented.** No code promotes cached LLM decisions to hard rules. | High |
| Cost telemetry | Metrics exist (`EngineMetrics`, `CacheStats`) but are **never persisted or inspected**. | Medium |
| Decision layer separation | **Two `DecisionResult` types exist** — one in `intake/decision.py`, one in `decision/hybrid_engine.py`. They conflate different concerns. | High |

---

## 1. Architecture Map: Two Decision Layers

### Discovery
The codebase has **two separate decision layers** that are easy to conflate:

**Layer A — NB02 Proper (`src/intake/decision.py`, 2165L)**
- Input: `CanonicalPacket`
- Output: `DecisionResult` with `decision_state` ∈ {`ASK_FOLLOWUP`, `PROCEED_INTERNAL_DRAFT`, `PROCEED_TRAVELER_SAFE`, `STOP_NEEDS_REVIEW`, `BRANCH_OPTIONS`}
- Logic: ambiguity resolution, contradiction handling, soft/hard blockers, invariant checks
- This is the **agency judgment engine** per the v0.2 spec

**Layer B — Hybrid Decision Engine (`src/decision/hybrid_engine.py`, 741L)**
- Input: `CanonicalPacket` + `decision_type` string
- Output: `DecisionResult` (different class!) with risk assessment dicts
- Logic: cache → rules → LLM fallback
- Decision types: `elderly_mobility_risk`, `toddler_pacing_risk`, `budget_feasibility`, `visa_timeline_risk`, `composition_risk`
- This produces **risk flags** that feed into Layer A

### Problem
`src/intake/decision.py` has `generate_risk_flags_with_hybrid_engine()` (line 61) which calls the hybrid engine. But the risk flags are **additive** — they inform NB02 but don't determine the final state. The final state depends on ambiguity resolution, which the hybrid engine never sees.

**Implication**: The hybrid engine's "learning" mechanism (cache → rule graduation) only applies to risk flags. The actual decision state logic in `intake/decision.py` (2000+ lines) is entirely outside the learning loop.

---

## 2. Cache Key Stability Audit

### How Keys Are Built
`src/decision/cache_key.py` generates SHA-256 hashes from `decision_type` + relevant packet fields:

| Decision Type | Key Fields |
|---------------|-----------|
| `budget_feasibility` | destination, resolved_destination, budget_min, party_size, duration_days, domestic_or_intl |
| `composition_risk` | destination, party_composition |
| `elderly_mobility_risk` | destination, has_elderly, elderly_count |
| `toddler_pacing_risk` | destination, has_toddler, toddler_ages, duration_days |
| `visa_timeline_risk` | destination, domestic_or_intl, urgency, visa_required |
| (default) | All facts + all derived_signals (fallback) |

### Findings
1. **Budget feasibility key includes `budget_min` but not `budget_max`.** If budget range changes but min stays same, cache key is stable even though feasibility calculus changes. Severity: Low (budget_max rarely differs from budget_min in practice, but edge case exists).
2. **Date-based duration calculation is in the key extraction path.** `_get_trip_duration()` parses ISO dates. If the duration is computed from start/end dates, the extracted `duration_days` is the same regardless of absolute dates. This is correct — a 7-day trip in January vs July should share a key for pacing risk.
3. **No test for key stability.** `tests/test_decision_cache.py` tests storage mechanics but doesn't verify that equivalent packets produce identical keys.

### Verdict
Cache keys are **reasonably stable** but have edge cases. No active corruption detected.

---

## 3. Rule Coverage Gap Analysis

### Decision Type Coverage

| Decision Type | Rules Registered | Decision State Mapping | Gap |
|---------------|-----------------|------------------------|-----|
| `budget_feasibility` | `rule_budget_feasibility` | Maps to ASK_FOLLOWUP in NB02 when infeasible | Rule exists but NB02 also does independent budget checks (line 2122). Double-check risk: **low** because both paths reach same state |
| `composition_risk` | `rule_composition_risk` | Not directly mapped in NB02 state machine | **Gap**: NB02 doesn't consume `composition_risk` flags for state transitions. Risk flags exist but don't block. |
| `elderly_mobility_risk` | `rule_elderly_mobility_risk` | Not directly mapped in NB02 state machine | **Gap**: Same as above — risk flag exists but doesn't affect decision_state unless `hard_blockers` or `soft_blockers` separately identify elderly field. |
| `toddler_pacing_risk` | `rule_toddler_pacing_risk` | Same gap | Same |
| `visa_timeline_risk` | `rule_visa_timeline_risk` | Maps to hard blocker via `document_conflict` in NB02 | **Partial**: `document_conflict` in NB02 triggers `STOP_NEEDS_REVIEW`. Hybrid engine's visa rule produces a risk flag, but NB02 independently checks visa_status field. |

### The Core Gap
The hybrid engine's 5 decision types are **risk assessments** for specific concerns. But NB02's state machine transitions are driven by:
1. `critical_contradictions` (date_conflict, document_conflict → STOP; destination/origin/budget/party/general → ASK)
2. `hard_blockers` (missing required fields → ASK)
3. `soft_blockers` (missing optional fields → INTERNAL_DRAFT)
4. `blocking_ambiguities` (unresolved alternatives → ASK)
5. Budget feasibility status (infeasible + PROCEED_TRAVELER_SAFE → downgrade)

**The hybrid engine risk flags are additive metadata**, not state determinants. This is architecturally correct (separation of concerns), but it means:
- **Cache → rule graduation only affects risk flag generation**
- **NB02 proper (the state machine) is NOT cached or rule-optimized**
- Every packet still runs through 2000+ lines of `intake/decision.py` logic

### Rule Coverage of `decision_state` Space

| decision_state | What triggers it | Hybrid engine covers it? |
|----------------|-----------------|--------------------------|
| `STOP_NEEDS_REVIEW` | date_conflict, document_conflict | No (visa_timeline is related but separate) |
| `ASK_FOLLOWUP` | hard_blockers, critical_contradictions (non-STOP), blocking_ambiguities | No |
| `PROCEED_INTERNAL_DRAFT` | soft_blockers only | No |
| `PROCEED_TRAVELER_SAFE` | no blockers, no ambiguities, feasible budget | No (budget_feasibility is a check, not the final state) |
| `BRANCH_OPTIONS` | budget_conflict contradictions | No |

**Verdict**: The hybrid engine covers 0% of the `decision_state` transitions. It covers 100% of the risk flag generation for 5 specific concerns. This is by design, but it means the governing principle "prefer rules over LLMs" is only applied to **a narrow slice** of the judgment layer.

---

## 4. Graduation Logic Audit

### Expected Behavior (per governing principle)
> "Every repeated LLM judgment should be considered a candidate for graduation into a deterministic rule"

### Actual Behavior
**There is no graduation logic.** Search the codebase:

```bash
grep -r "graduate\|promote.*rule\|cache.*to.*rule\|rule.*from.*cache" src/decision/
# No results
grep -rn "_register.*rule" src/decision/hybrid_engine.py
# Only _register_builtin_rules() — static registration at init
grep -rn "compile.*rule\|rule.*compilation" src/decision/
# No results
```

The flow in `HybridDecisionEngine.decide()` (line ~300+):
1. Generate cache key
2. Check cache → return if hit
3. Try registered rules in order → cache and return if match
4. Call LLM → **cache the result** and return
5. Fallback to default

**Step 3 → Step 4 is where graduation would happen.** If an LLM decision is cached, the next identical packet hits the cache and never calls the LLM again. But **the cached decision never becomes a rule** that other code paths can inspect, modify, or review.

### Cache vs Rule Distinction
- **Cache**: per-input memoization. Opaque. Keyed by hash. `CachedDecision` has `source` field indicating `"llm_compiled"` or `"rule_engine"`.
- **Rule**: deterministic code (`Callable`) registered with the engine. Can be reasoned about, tested independently, versioned.

The cache makes repeated LLM calls cheap (₹0), but it doesn't make them **transparent**. A cached LLM decision is still a black box — it can't be promoted to a rule without human review because the LLM's reasoning is embedded in the `decision` dict, not extractable as code.

### D6 Connection
This is exactly why D6 (eval) exists. The NB05 golden-path fixtures would generate labeled examples. The eval would verify them. Only after eval validation could a cached LLM decision be "graduated" to a hard rule. **Without D6, graduation is dangerous.**

**Verdict**: Graduation logic is **correctly absent** given the lack of eval infrastructure. Attempting to auto-generate rules from cached LLM decisions would be premature and risky.

---

## 5. Cost Telemetry Audit

### What Exists
1. `EngineMetrics` in `hybrid_engine.py` — tracks total_decisions, cache_hits, rule_hits, llm_calls, default_fallbacks, total_cost_inr
2. `CacheStats` in `cache_schema.py` — tracks total_lookups, cache_hits, cache_misses, llm_calls
3. `CachedDecision` — tracks use_count, success_rate, feedback_count

### What Is Missing
1. **No persistence.** `EngineMetrics` is held in memory on the `HybridDecisionEngine` instance. When the engine is recreated (every request?), metrics reset.
2. **No inspection.** There is no API endpoint, no log output, no dashboard that surfaces these metrics.
3. **No trend analysis.** Success rate is per-entry, not per-rule-type or global. No way to answer "is our LLM call rate decreasing over time?"
4. **Cost is hardcoded.** `cost_inr` is set to ₹0.10 per LLM call in `hybrid_engine.py` (line ~470+) but the actual cost depends on model choice, token count, etc. No actual cost tracking.

### Search Evidence
```
grep -rn "EngineMetrics\|CacheStats\|get_stats\|metrics.to_dict" src/ spine-api/
grep -rn "total_cost_inr\|metrics" spine-api/server.py
# No server.py references to engine metrics
```

**Verdict**: Telemetry scaffolding exists but is **not wired to production visibility**. This is a medium gap — the data exists but no one consumes it.

---

## 6. Decision Layer Conflation

### Finding
`src/intake/decision.py` and `src/decision/hybrid_engine.py` both define a `DecisionResult` dataclass with entirely different shapes:

**`intake/decision.py` (~line 130)**:
- Has `decision_state`, `confidence_scorecard`, `follow_up_questions`, `branch_options`, `risk_flags`, `packet` reference
- This is the **canonical NB02 output**

**`decision/hybrid_engine.py` (~line 38)**:
- Has `decision` (dict), `source` (cache/rule/llm/default), `confidence`, `cache_hit`, `rule_hit`, `llm_used`, `cost_inr`, `decision_type`
- This is the **risk flag output**

### Problem
They share a name but serve different purposes. Callers in `intake/decision.py` receive `DecisionResult` from the hybrid engine and embed it into their own `DecisionResult` as `risk_flags`. This is not technically a bug, but it is **architectural confusion** that makes reasoning about "the decision" harder.

**Recommendation**: Rename the hybrid engine's result to `RiskAssessmentResult` or similar to eliminate the collision.

---

## 7. Critical Finding: The NB02 State Machine Is Outside the Learning Loop

### Diagram

```
Inbound Message → NB01 Normalization → CanonicalPacket
                                    ↓
                              ┌──────────────┐
                              │ NB02 Proper  │  ← 2000+ lines, NOT cached
                              │ (intake/     │  ← NOT rule-optimized
                              │  decision.py)│  ← NOT in hybrid engine
                              └──────────┬───┘
                                         ↓
                              decision_state + flags
                                         ↓
                              ┌──────────────┐
                              │ D1 Autonomy  │  ← Just implemented
                              │ Gate         │  ← Evaluates policy
                              └──────────┬───┘
                                         ↓
                              AutonomyOutcome
                                         ↓
                              NB03 Builder Selection
```

The hybrid engine is a **sidecar** to NB02. It generates risk flags that NB02 may or may not consume. NB02 proper — the actual state machine determining `ASK_FOLLOWUP` vs `PROCEED_TRAVELER_SAFE` — is entirely deterministic already but **not optimized** (it runs 2000+ lines of Python per request).

### Implication for D2/D5/D6
- D6 eval needs to validate **NB02 state machine outcomes**, not just hybrid engine risk flags.
- D5 override learning needs to learn from **NB02 decisions + owner overrides**, not just risk flags.
- D2 consumer surface depends on **NB02 verdict accuracy**, which is currently un-evaluated.

---

## 8. Recommendations (Priority Ordered)

### Immediate (P0)
1. **Rename hybrid engine `DecisionResult` → `RiskAssessmentResult`** — Eliminates naming collision, clarifies separation of concerns.
2. **Document the two-layer architecture** — Add a comment at the top of `hybrid_engine.py`: "This module generates risk flags, not decision states. See `intake/decision.py` for the NB02 state machine."

### Short-term (P1)
3. **Add cache key stability test** — Create `tests/test_cache_key_stability.py` that verifies equivalent packets produce identical keys for each decision type.
4. **Wire EngineMetrics to telemetry** — Persist metrics per-request and aggregate. At minimum, log to stdout in structured JSON. Better: add `/stats/engine-metrics` endpoint to spine-api.
5. **Map risk flags to decision_state impact** — For each decision type, document whether and how its output affects NB02 state transitions. If a risk flag never blocks, that may be a bug or by design — it should be explicit.

### Medium-term (P2)
6. **NB02 state machine eval framework** — D6 should evaluate `intake/decision.py` outcomes, not just hybrid engine risk flags. Design golden-path fixtures that exercise the state machine directly.
7. **Rule expansion for state transitions** — Consider whether `hard_blockers` and `soft_blockers` resolution in NB02 can be partially rule-ified. Currently they're field-name-based; if destination is missing → ASK. This is deterministic — could be a fast-path rule.

### Deferred (until D6 eval exists)
8. **Graduation logic** — Only implement after eval validation confirms that cached LLM decisions are correct and stable. The current absence is **correct**.

---

## Verification Commands

```bash
# Check for graduation logic (should return nothing)
grep -r "graduate\|promote.*rule\|cache.*to.*rule" src/decision/

# Check for metrics persistence in API (should return nothing)
grep -rn "EngineMetrics\|CacheStats\|total_cost_inr" spine-api/server.py

# Run existing tests
uv run pytest tests/test_decision_cache.py tests/test_hybrid_engine.py tests/test_decision_rules.py -q
```

---

Checklist applied: IMPLEMENTATION_AGENT_REVIEW_HANDOFF_CHECKLIST.md
Session: 2026-04-22
