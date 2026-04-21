# v0.2 Governing Principles

**Date**: 2026-04-12
**Source**: Feedback on TEST_GAP_ANALYSIS.md
**Revised**: 7 corrections incorporated

---

## The Governing Rule

Do not ask "is this in scope?"
Ask only: **"Which layer owns this?"**

| Layer | Owns                                   |
| ----- | -------------------------------------- |
| NB01  | Truth capture and normalization        |
| NB02  | Judgment and routing                   |
| NB03  | Session behavior and prompt boundaries |
| NB04  | Evaluation                             |
| NB05  | Honest golden-path demos               |
| NB06  | Honest shadow-mode replay              |

## The Governing Principles

### 1. Deterministic-First
**Prefer rules over LLMs.**
Always attempt to solve a judgment or extraction task with deterministic rules first. Use LLMs only when the answer requires world knowledge, cross-field semantic judgment, or complex intent classification. Every repeated LLM judgment should be considered a candidate for graduation into a deterministic rule (see `src/decision/hybrid_engine.py`).

## The Clean Cut

Everything the travel-agency OS needs gets modeled **now**.
What can be phased later is only the **execution layer**, not the **state model**, **decision logic**, or **handoff artifacts**.

## How "Out of Scope" Scenarios Are Handled

P2 dashboards, CRM memory, post-booking anxiety, cancellation, emergency, referral, review timing — they are **not excluded**. They become one or more of:

- packet fields (e.g., `operating_mode="cancellation"`)
- derived signals (e.g., `document_risk` from passport + visa + date data)
- decision/risk modes (e.g., NB02 routes to `STOP_NEEDS_REVIEW` in emergency mode)
- strategy profiles (e.g., NB03 emergency builder with step-by-step prompts)
- handoff artifacts (e.g., structured brief for future owner-dashboard system)

This is how we stay comprehensive without turning NB01–NB03 into a random monolith.

## The Two Axes

Every packet is classified along **two orthogonal axes**:

### Axis 1: `decision_state` (what to do next)

- `ASK_FOLLOWUP`
- `PROCEED_INTERNAL_DRAFT`
- `PROCEED_TRAVELER_SAFE`
- `BRANCH_OPTIONS`
- `STOP_NEEDS_REVIEW`

### Axis 2: `operating_mode` (context of the interaction)

- `normal_intake`
- `audit`
- `emergency`
- `follow_up`
- `cancellation`
- `post_trip`
- `coordinator_group`
- `owner_review`

**Examples**:
| Scenario | `operating_mode` | `decision_state` |
|----------|-----------------|-----------------|
| Quote disaster review | `owner_review` | `STOP_NEEDS_REVIEW` or `BRANCH_OPTIONS` |
| Trip emergency | `emergency` | `STOP_NEEDS_REVIEW` |
| Ghost customer | `follow_up` | `BRANCH_OPTIONS` or `PROCEED_INTERNAL_DRAFT` |
| Visa crisis at booking | `normal_intake` | `STOP_NEEDS_REVIEW` |
| 3-family coordination | `coordinator_group` | `ASK_FOLLOWUP` (per-group) |
| Self-booked hotel mismatch | `audit` | `BRANCH_OPTIONS` |

**Critical**: `operating_mode` is a **top-level packet field**, not inside `facts`. It is system routing classification, not traveler truth.

## Implementation Order

1. **Pass 1: Contract reconciliation** — schema v0.2, field dictionary, operating_mode, ambiguities, new derived signals, visibility semantics
2. **Pass 2: NB01 hardening** — rename fields, structured budget/dates, parse ambiguity, parse owner context with visibility, add repeat-memory hooks, add audit intake, add multi-party structures, add schema validation, split cells
3. **Pass 3: NB02 hardening** — ambiguity-aware blocker engine, urgency-aware blocker suppression, budget feasibility, sourcing-path derivation, suitability derivation, visa/passport blockers, operating-mode judgment, invariant assertions
4. **Pass 4: NB03 hardening** — mode-specific builders, question-intent model, dynamic risk generation, structural traveler/internal sanitization (using visibility semantics), branch-quality refinement
5. **Pass 5: NB04/05/06 hardening** — richer evals, multiple golden paths, shadow-mode artifact suite, remove packet simulation shortcuts

## Rules Enforced by v0.2

1. **`operating_mode` is top-level**, never inside `facts`
2. **No duplication** between facts and derived signals — if it can be computed, it is derived
3. **Budget and dates are structured numeric**, not loose strings — feasibility and urgency need numbers
4. **`destination_candidates` is the discovery representation**; downstream stages resolve to `resolved_destination`
5. **`SubGroup` is a structural type**, not a loose dict blob
6. **Owner/agency fields have `visibility` semantics** — `internal_only` vs `traveler_safe_transformable`
7. **Schema + NB02 + NB03 are updated together** — not sequentially

---

_This document captures the governing principles. Implementation specs are in `NB01_V02_SPEC.md` (NB01), with NB02/NB03 specs to follow._
