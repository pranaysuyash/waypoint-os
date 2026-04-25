# Next Priority Reassessment — Thinking from Code, Not Just Queue

**Date**: 2026-04-24  
**Status**: Decision record — pre-launch execution priority  
**Trigger**: User instruction: "dont only depend on what docs say, think first"

---

## 1) What I Was About to Do (Doc-Dependent)

The `BUILD_QUEUE_CONSOLIDATED.md` labels P1-D (Tier 3 LLM scorer) as the next item. I was about to build it. That is queue-dependent reasoning. Here's why it's wrong right now.

---

## 2) Why Tier 3 Is Deferred (Not Rejected)

### Architectural Self-Contradiction
The `ARCHITECTURE_DECISION_D4_SUBDECISIONS_ADDENDUM_2026-04-18.md` explicitly states in section "Pending: Tier 3 LLM Contextual Scorer":

> **Status**: Deferred — spec when Tiers 1+2 are implemented and borderline cases are observable.

Tiers 1+2 ARE implemented. But:
- **Zero borderline cases observed.** No operator has ever seen a suitability flag. No one has overridden one.
- Zero empirical data exists on when deterministic tiers conflict.
- No override signal = no trigger calibration dataset = no graduation path for cache → rule.

Building Tier 3 now would violate the architecture's own guardrail. It would be a speculative feature solving problems that may not exist.

### Cost Without Value
- Every Tier 3 call costs LLM tokens.
- Without calibrated triggers, obvious deterministic cases (toddler + bungee jump) would hit the LLM unnecessarily.
- The 11-dimension audit framework from `AGENTS.md` explicitly labels "operators can use day 1" as a blocking dimension. Tier 3 adds no operator visibility.

### When We Do Build It
Condition: 100+ real suitability decisions have been processed and 10+ operator overrides have been logged. Then we have empirical signal for trigger calibration.

---

## 3) Why Frontend Panel Is Lower Priority Right Now

The `ACTIVITY_SUITABILITY_IMPLEMENTATION_HANDOFF_2026-04-16.md` states:

> The frontend currently surfaces generic `risk_flags` in `frontend/src/components/workspace/panels/DecisionPanel.tsx`, but it does not yet include a dedicated activity suitability panel, iconography, or user-facing suitability presentation.

Building the panel would unlock operator visibility, but:
- It requires React/TS work (scope shift from the current backend-heavy session).
- It requires UI/UX decisions that haven't been made.
- The backend API contract already emits suitability flags; the frontend can consume them once prioritized.
- It's a **presentation-layer problem**, not a **structural-risk problem**.

Verdict: Valid, valuable, but second to hardening the backend that powers it.

---

## 4) What the Code Actually Shows (Independent Analysis)

I read all target directories. The highest-value corrective work is closing the `travel_agency_codebase_audit_2026-04-19.md` findings that remain unaddressed.

### P0-2: Fragile Import in `src/intake/decision.py`

**Code**: `from src.decision.hybrid_engine import create_hybrid_engine` (line 44)

**Why it's broken**: This import assumes `src/` is on `sys.path`. It is — because `spine_api/server.py` mutates `sys.path` at startup. But if `intake.decision` is imported from any other context (script, test, notebook), this crashes with `ModuleNotFoundError`.

**Impact**: Runtime crash on non-server invocation paths.

### P1-3: Internal Data Leakage on Traveler Bundle

**Code**: `src/intake/decision.py:911` — `build_traveler_safe_bundle` sets `bundle.internal_notes = "LEAKAGE DETECTED: ..."`

**Why it's a bug**: `to_traveler_dict()` excludes `internal_notes`, but `to_dict()` does not. The `/run` endpoint calls `_to_dict(result.internal_bundle)` to serialize the response. This path reads `__dict__` and includes `internal_notes`.

**Impact**: If leakage is detected but not raised, internal reasoning strings leak to the traveler-facing response payload.

### P2-5: Duplicate Budget Feasibility Table

**Code**:
- `src/intake/decision.py` lines 503–532 (`BUDGET_FEASIBILITY_TABLE`)
- `src/decision/rules/budget_feasibility.py` (same table)

**Why it's a bug**: Divergence. One table gets updated for Dubai, the other doesn't. Same trip produces different feasibility verdicts depending on which code path is hit.

**Impact**: Silent data inconsistency. Wrong feasibility warnings shown to operators.

---

## 5) Decision

### Do NOT Build Tier 3
Condition not met. No empirical borderline cases. Building it now is speculative and contradicts the deferral clause in its own architecture document.

### Do NOT Build Frontend Panel Yet
Presentation is important, but the backend powering it has latent bugs. Harden first, surface second.

### DO: Audit Closure Phase
Close the three verified issues above (P0-2, P1-3, P2-5). This is concrete, bounded, testable, and prevents production regressions.

---

## 6) Open Research Areas (Documented for Future)

| Area | Current Status | When to Address |
|---|---|---|
| Tier 3 LLM trigger calibration | No data | After 100+ real suitability decisions |
| Tier 3 LLM prompt templates | Not defined | After trigger calibration dataset exists |
| Frontend suitability panel | Not started | After audit closure |
| LLM monthly budget guardrails | Not defined | Before Tier 3 activation |
| Operator override telemetry | Not instrumented | Before Tier 3 activation |

---

## 7) Next Immediate Action

1. Fix P0-2 import (proper path-safe import)
2. Fix P1-3 leakage (raise on leakage OR enforce `to_traveler_dict()` in serialization)
3. Fix P2-5 deduplication (canonical table in one location)
4. Run test suite after each fix
5. Update this decision record with verification outcomes

**Checklist applied:** `AGENTS.md` 11-dimension audit / Fix & Verify / Review & Iterate discipline.

---

*This document exists because the instruction was: "dont only depend on what docs say, think first" and "document each discussion no matter what it is on."*
