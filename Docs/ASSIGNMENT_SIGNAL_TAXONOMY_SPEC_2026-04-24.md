# Assignment Signal Taxonomy Spec

**Date**: 2026-04-24
**Status**: Draft Spec
**Scope**: Canonical signal taxonomy for governed case-to-operator matching. Defines which signals are allowed as hard gates, transparent ranking inputs, learning-only calibration inputs, or forbidden inputs.
**Related docs**:

- `AUTO_ASSIGNMENT_AND_LEARNED_ROUTING_EXPLORATION_2026-04-24.md`
- `ASSIGNMENT_ESCALATION_STATE_MACHINE_SPEC_2026-04-22.md`
- `CANONICAL_ROLE_PERMISSION_MATRIX_2026-04-22.md`
- `SETTINGS_ROUTE_SUBROUTE_UX_CONTRACT_2026-04-23.md`
- `GOVERNANCE_AUDIT_EVENT_TAXONOMY_2026-04-23.md`

---

## Executive Summary

Waypoint should not let routing logic grow as a pile of ad-hoc heuristics.

It needs a canonical signal taxonomy so the system can answer five questions clearly:

1. Which signals decide eligibility?
2. Which signals may affect ranking?
3. Which signals are learning-only and must not directly assign work?
4. Which signals are forbidden?
5. What evidence threshold is required before a learned signal can influence live routing?

This spec defines four signal classes:

1. `eligibility` — hard gates that determine who can receive the case at all.
2. `ranking` — transparent signals that can move an eligible operator up or down.
3. `learning_only` — outcome-informed signals that can calibrate ranking weights only after enough evidence exists.
4. `forbidden` — signals that must never influence assignment.

---

## Core Rules

### 1. Hard Gates Come First

No ranking or learning signal can rescue an operator who failed an eligibility check.

### 2. Continuity Is A First-Class Routing Signal

Continuity is not a soft afterthought. When traveler, trip, or review context already belongs with a current operator, continuity should usually outrank optimization.

### 3. Matching And Performance Evaluation Stay Separate

The system may learn from outcomes, but it must not collapse assignment into an opaque worker score.

### 4. Every Live Signal Needs Provenance

Each signal used in routing should be traceable to:

- its source system,
- its update cadence,
- whether it is operator-entered, system-derived, or model-derived,
- and whether it is currently trusted for live use.

### 5. Unknown Or Untrusted Signals Must Fail Closed

If a signal is stale, undersampled, or structurally missing, it should drop out of routing rather than silently inventing confidence.

---

## Canonical Signal Classes

## 1. Eligibility Signals

These are hard gates.

If an operator fails one of these checks, they are excluded from the candidate pool.

| Signal ID | Purpose | Typical Source | Use |
| --- | --- | --- | --- |
| `member_active` | Operator must be active in the workspace | membership / team store | hard gate |
| `role_eligible` | Operator role must be allowed for the queue/stage | canonical role matrix | hard gate |
| `queue_access` | Operator must be allowed to receive this queue | assignment policy | hard gate |
| `stage_scope_allowed` | Operator must be allowed to own the current stage/type of work | assignment policy / role policy | hard gate |
| `capacity_available` | Operator must have non-zero available capacity if queue uses hard capacity blocking | people profile / workload model | hard gate |
| `manual_holdout` | Operator may be excluded from auto-assignment temporarily | assignment policy / member profile | hard gate |
| `channel_coverage` | Queue may require a supported channel or shift window | member profile / queue policy | hard gate |
| `specialization_required` | Queue may require a specific certification/specialization | skills profile | hard gate |

Notes:

- `capacity_available` may be a hard gate for auto-apply flows but only a penalty signal in suggestion mode, depending on policy.
- `specialization_required` should only be used when the queue explicitly requires it. Otherwise specialization belongs in ranking.

## 2. Ranking Signals

These apply only after eligibility is resolved.

They affect ordering, not access.

| Signal ID | Purpose | Typical Source | Use |
| --- | --- | --- | --- |
| `continuity_current_trip_owner` | Preserve existing trip context | assignment state | rank bonus |
| `continuity_customer_owner` | Prefer operator with traveler/household context | traveler relationship layer | rank bonus |
| `specialization_destination_match` | Prefer operators with destination fit | skills profile | rank bonus |
| `specialization_trip_type_match` | Prefer operators with trip-type fit | skills profile | rank bonus |
| `capacity_headroom` | Prefer operators with room to take work | workload model | rank bonus |
| `active_load_pressure` | Penalize overloaded operators | workload model | rank penalty |
| `review_backlog_pressure` | Penalize operators already carrying too much review burden | review queue metrics | rank penalty |
| `escalation_backlog_pressure` | Penalize operators/escalation owners already saturated with escalations | routing telemetry | rank penalty |
| `sla_risk_pressure` | Penalize operators already close to SLA breach load | SLA telemetry | rank penalty |
| `recent_handoff_pressure` | Penalize operators with unusually high recent handoff churn | routing telemetry | rank penalty |
| `fairness_rebalance_bonus` | Prevent the same top-ranked operator from receiving all eligible work in a balanced queue | routing policy | rank bonus |

Notes:

- `fairness_rebalance_bonus` is not a social-good garnish. It is an operational safeguard against funneling every easy case to one operator and starving the rest of the team.
- `continuity_current_trip_owner` should normally dominate all other ranking signals unless policy explicitly authorizes handoff/reassignment.

## 3. Learning-Only Signals

These should not directly assign work in early phases.

They calibrate ranking weights only after evidence thresholds are satisfied.

| Signal ID | Purpose | Typical Source | Use |
| --- | --- | --- | --- |
| `response_timeliness_by_trip_class` | Learn which operators keep pace on a trip cohort | event timestamps | learning only |
| `review_approval_rate_by_trip_class` | Learn where review outcomes tend to succeed without rework | review outcomes | learning only |
| `reassignment_rate_by_trip_class` | Learn which assignment patterns later unwind | routing history | learning only |
| `handoff_rate_by_trip_class` | Learn which operators or cohorts frequently require handoff | routing history | learning only |
| `override_rate_by_trip_class` | Learn where human overrides consistently reject recommendations | governance events | learning only |
| `customer_satisfaction_by_trip_class` | Learn quality outcomes on completed cases | post-trip feedback | learning only |
| `completion_latency_by_trip_class` | Learn speed only after complexity normalization | case lifecycle telemetry | learning only |

Notes:

- Every `*_by_trip_class` signal assumes the system has a trustworthy cohort model. Without cohorts, these signals are too blunt.
- No learning-only signal should become active for routing if it is based on global aggregates across all trip types.

## 4. Forbidden Signals

These must never influence assignment.

| Signal ID | Why It Is Forbidden |
| --- | --- |
| `protected_class_proxy` | Creates direct fairness and compliance risk |
| `raw_global_revenue_total` | Confuses assignment with commercial ranking and rewards case mix, not fit |
| `raw_global_conversion_rate` | Distorts routing by case difficulty and lead quality |
| `surveillance_productivity_signal` | Keystroke/mouse or similar monitoring is outside the intended governance model |
| `opaque_llm_worker_score` | Not explainable, contestable, or governance-safe |
| `free_text_character_inference` | The system should not infer operator merit or personality from text artifacts |
| `private_manager_note_score` | Private qualitative commentary should not silently influence allocation |

---

## Signal Definition Shape

The exact implementation can evolve, but the canonical definition should look roughly like this:

```ts
type AssignmentSignalClass =
  | 'eligibility'
  | 'ranking'
  | 'learning_only'
  | 'forbidden'

type AssignmentSignalUse =
  | 'hard_gate'
  | 'rank_bonus'
  | 'rank_penalty'
  | 'learning_only'
  | 'disallowed'

type SignalTrustLevel = 'trusted' | 'partial' | 'experimental' | 'blocked'

interface AssignmentSignalDefinition {
  id: string
  label: string
  class: AssignmentSignalClass
  use: AssignmentSignalUse
  description: string
  sourceOfTruth: string
  requiresCohort: boolean
  minSampleSize?: number
  trustLevel: SignalTrustLevel
  explainabilityRequired: boolean
}
```

The important part is not the exact interface. The important part is that every routing signal becomes explicit and reviewable.

---

## Cohort Model For Learning Signals

Learning signals should operate on routing cohorts rather than one giant undifferentiated pool.

Recommended cohort dimensions:

- destination region
- trip type
- value band
- complexity band
- urgency band
- intake channel
- traveler repeat/new status
- documentation burden

Example cohort:

- `family_europe_mid_value_high_doc_burden`

This is intentionally operational, not academic. The goal is to learn assignment quality for similar kinds of cases.

---

## Minimum Sample Rules

Suggested starting rules for any learning-based calibration:

1. Minimum `20` completed cases for an operator within a cohort before a learning signal is considered.
2. Minimum `2` eligible operators meeting sample threshold within the same cohort before live comparison-based tuning is allowed.
3. Metrics older than `180` days should decay or drop unless the cohort volume is very low and explicitly allowed by policy.
4. Any learning effect should be bounded so it can reorder near-ties, not overwhelm hard-fit signals like continuity or specialization.
5. If a learning signal conflicts with recent repeated human overrides, the system should lower confidence and prefer suggestion mode.

These are governance defaults, not immutable mathematical truths.

---

## Signal Readiness Expectations

This taxonomy is broader than the current codebase can support.

Current-state implication:

- eligibility signals can ship first,
- a subset of ranking signals can ship next,
- most learning-only signals remain blocked until the routing telemetry and metrics layer are hardened.

The companion audit document `ROUTING_METRICS_READINESS_AUDIT_2026-04-24.md` should be treated as the authority on what is currently trustworthy enough to use.

---

## Audit Requirements

Every live ranking or auto-assignment decision should be able to emit:

- the eligible operator set,
- the top-ranked candidates,
- the top contributing signals,
- whether the final action was suggestion-only or auto-applied,
- and whether a human accepted or overrode the recommendation.

The routing layer should never be able to say only: "the model picked this person."

---

## Final Recommendation

Use this taxonomy as the contract boundary for future routing work:

- hard gates for eligibility,
- transparent signals for ranking,
- bounded evidence-based signals for learning,
- explicit forbidden signals for safety and fairness.

That keeps routing explainable, governable, and compatible with the broader assignment state machine instead of becoming another hidden scoring subsystem.
