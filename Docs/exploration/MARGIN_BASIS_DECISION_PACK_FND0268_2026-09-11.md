# Margin-Basis Decision Pack — modeled heuristic vs real fee-matrix floor (FND-0268)

**Class:** EXPLORE → feeds a DECIDE (owner-gated). Produced by the Elena-council audit
remediation pass, 2026-09-11. No code was changed for this item.

## The gap

Elena's #1 evaluation criterion is a **hard quote-review gate on real margin** ("mandatory
escalation for any quote with margin <18%"). What ships today:

| Layer | What exists | Basis | Evidence |
|---|---|---|---|
| Flag | `calculate_margin` → `requires_review` at <15% | **Modeled**: `base_margin = 18.0` adjusted by party size / destination / ambiguity — never reads real cost vs retail | `src/analytics/engine.py:62-90,122-124` |
| Escalation | Owner review + 6h SLA at <8% | Same modeled margin | `src/analytics/policy_rules.py:114-121` |
| Send policy | Junior sends blocked when `requires_review`, critical state, or confidence <0.75 | Computed guidance surfaced to FE; no endpoint hard-blocks send on margin | `src/analytics/policy_rules.py:158-194`, surfaced at `frontend/src/lib/bff-trip-adapters.ts:537` |
| Ready check | Unapproved `requires_review` blocks "mark ready" | Modeled | `src/analytics/policy_rules.py:91-93` |
| Real-margin engine | USD margin floors per service category (retail − wholesale) | **Real** cost data — but **zero production callers** (tests only) | `spine_api/services/fee_matrix.py:24-91` |
| Dollar gate | Quotes ≥ $10,000 require senior approval | Absolute value, not margin | `spine_api/routers/team_workflows.py:143` |

The audit verified the fabrication class is closed — the modeled margin is *labeled*
truthfully as a model — but the gate Elena was promised gates a **heuristic**, while the
**real** margin engine sits orphaned (the same orphan pattern as FND-0261's LIVE rows).

## The decision (owner)

**Which margin basis may gate a quote send?**

1. **Option A — keep modeled basis (do nothing).** Zero work; gate stays a soft signal.
   Risk: the exact failure Elena fears (junior undercuts to 8-10%) is invisible when the
   model's base assumption (18%) is wrong for the actual booking.
2. **Option B — wire `fee_matrix` as the gate basis where cost data exists (recommended).**
   When a trip's option carries real wholesale cost, compute real margin and gate on it;
   fall back to the modeled margin (explicitly labeled `margin_basis: "modeled"`) when it
   does not. Additive: extend `compute_send_policy` with a cost-backed branch + tests; no
   schema change. Effort ~S-M. This makes the 15%/8% thresholds mean what Elena thinks they mean.
3. **Option C — block sends end-to-end on margin.** Adds a hard 409 in the send endpoint.
   Highest protection, highest product risk (false positives block real sends); should
   follow ADR-008 ratification (C1) because it touches money-execution authority.

**Recommendation:** Option B now; revisit C after ADR-008 §6 ratification (roadmap C1).

## Facts that hold regardless of the decision

- The 18% figure in Elena's criterion maps to the *modeled base*, not any enforced floor.
- `fee_matrix` floors are the only cost-anchored margin source in the repo; any wiring must
  extend it, not fork it (no-duplicate-systems rule).
- Any basis change must keep the real-or-None convention: no invented cost fallbacks.

## Execution addendum (2026-09-11, later same session)

**Option B is blocked by a data prerequisite.** Wiring `fee_matrix` requires a trip-side
wholesale-cost value to compare against; no producer exists — the sourcing-hierarchy
resolver is a STUB (E13, defaults to open_market) and there is no live inventory lane
(B6/B7 are quota-gated until 2026-10-06). Writing the gating branch now would be dormant
code with zero callers — the exact anti-pattern A5 was reclassified to avoid. FND-0268 is
therefore **deferred** (not closed) with reopen condition: *first real wholesale-cost
producer lands (B6/B7), or the owner selects Option C after ADR-008 §6 ratification.*
The seam for the future wiring is `compute_send_policy` (`src/analytics/policy_rules.py:158-194`)
plus `fee_matrix.calculate_package_pricing`; no other file needs to change.
