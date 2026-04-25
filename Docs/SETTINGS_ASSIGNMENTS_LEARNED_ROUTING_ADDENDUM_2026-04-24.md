# Settings Assignments Learned Routing Addendum

**Date**: 2026-04-24
**Status**: Draft Addendum
**Scope**: Exact `/settings/assignments` controls for suggestion-first routing, continuity policy, workload balancing, and bounded learned-routing posture.
**Parent doc**: `SETTINGS_ROUTE_SUBROUTE_UX_CONTRACT_2026-04-23.md`
**Related docs**:

- `AUTO_ASSIGNMENT_AND_LEARNED_ROUTING_EXPLORATION_2026-04-24.md`
- `ASSIGNMENT_SIGNAL_TAXONOMY_SPEC_2026-04-24.md`
- `ASSIGNMENT_ESCALATION_STATE_MACHINE_SPEC_2026-04-22.md`
- `CANONICAL_ROLE_PERMISSION_MATRIX_2026-04-22.md`
- `GOVERNANCE_AUDIT_EVENT_TAXONOMY_2026-04-23.md`

---

## Executive Summary

`/settings/assignments` already owns routing policy at a high level.

This addendum defines what that route must contain once Waypoint introduces assignment intelligence.

The key product rule is:

- assignment intelligence belongs in policy settings,
- per-trip assignment execution belongs in inbox and trip flows,
- and learned routing must start as a transparent recommendation system before any limited auto-assign mode is enabled.

---

## Product Positioning

This route is not a staffing dashboard and not a worker leaderboard.

It is the place where Owner/Admin govern:

- who is eligible to receive what kind of work,
- how continuity vs workload is balanced,
- whether the product suggests assignees or applies low-risk assignment automatically,
- and how much influence learned routing is allowed to have.

---

## Recommended Information Architecture

## 1. Assignment Mode

Purpose:

- define how much authority the system has for initial assignment.

Required controls:

- `Manual only`
- `Ranked suggestions`
- `Auto-assign low-risk queues`
- `Auto-assign selected queues`

Required guidance copy:

- `Manual only` means the system shows no recommendation.
- `Ranked suggestions` means the system recommends but never applies automatically.
- Auto-assign modes are limited to eligible low-risk queues and remain fully audited.

Recommended initial default:

- workspace default should remain `Manual only` until signal readiness is sufficient.
- first guided rollout target should be `Ranked suggestions`.

## 2. Routing Slots Explainer

Purpose:

- preserve the canonical routing model as assignment intelligence is added.

Must explain:

- `primary_assignee`
- `reviewer`
- `escalation_owner`
- `watchers`

Must reinforce this invariant in plain language:

- escalation adds oversight by default and does not automatically replace the current assignee.

## 3. Eligibility Rules

Purpose:

- define which operators can enter the candidate pool for each queue or work class.

Required controls:

- eligible roles
- required queue access
- required stage scope
- optional specialization requirement
- capacity blocking behavior
- temporary manual holdout

Recommended UI behavior:

- show a plain-language summary such as: `Junior agents may receive discovery leads but not escalation-owned review work.`

## 4. Continuity Policy

Purpose:

- define how strongly the system preserves traveler and trip context.

Required controls:

- `Prefer current trip owner`
- `Prefer returning-traveler owner`
- `Allow reassignment when overloaded`
- `Require explicit handoff for active owned work`

Recommended defaults:

- active trip continuity should be treated as effectively required unless a human initiates handoff or reassignment.
- returning-traveler continuity should be high priority but not absolute.

## 5. Capacity And SLA Balancing

Purpose:

- prevent the product from optimizing assignment fit while collapsing queue health.

Required controls:

- target capacity model
- overload threshold
- near-limit threshold
- SLA pressure penalty toggle
- review backlog penalty toggle
- escalation backlog penalty toggle

Required explanation:

- `Capacity` is not the same as skill.
- `Best fit` is not allowed to repeatedly overload the same operator.

## 6. Suggestion Explainability

Purpose:

- make recommendation logic contestable and trusted.

Required controls:

- show top recommendation only vs top three ranked options
- show reason summary
- show continuity explanation
- show workload explanation
- show why specific operators were excluded

Recommended UI pattern:

- top recommendation card
- expandable `Why this recommendation?`
- optional `Why not others?` panel

## 7. Learned Routing Posture

Purpose:

- constrain how much influence historical outcomes can have.

Required controls:

- `Learning disabled`
- `Use learning for suggestion ranking only`
- `Allow learning to tune low-risk auto-assign queues`

Required explanatory text:

- learning changes recommendation ordering inside policy guardrails.
- learning never overrides role eligibility, explicit queue restrictions, or continuity invariants.

Required guardrails:

- minimum sample threshold
- confidence threshold for auto-apply
- human override capture required
- fairness review reminder before enabling auto-assign learning

## 8. Fairness And Safety Guardrails

Purpose:

- keep assignment intelligence from becoming opaque labor allocation.

Required controls:

- explainability required toggle
- audit trail required toggle (should default on and effectively be mandatory)
- protected/forbidden signals notice
- recourse/override notice

Required warning states:

- `Specialization data incomplete`
- `Learning inputs undersampled`
- `Metrics include simulated values`
- `Frontend/backend role vocabulary mismatch`

## 9. Draft, Review, And Publish

Purpose:

- preserve the route-level governance model already defined in the parent contract.

Publish flow must show:

- changed policy areas
- affected queues
- changed assignment mode
- continuity changes
- learning posture changes
- whether any queue becomes newly eligible for auto-assign

Required publish warnings:

- if continuity protection is lowered
- if learning is newly enabled
- if auto-assign expands to additional queues

---

## Recommended Policy Shape

```ts
type AssignmentMode =
  | 'manual_only'
  | 'ranked_suggestions'
  | 'auto_assign_low_risk'
  | 'auto_assign_selected_queues'

interface AssignmentPolicyDraft {
  mode: AssignmentMode
  eligibleRoles: string[]
  queueScopes: string[]
  requireStageScope: boolean
  requireSpecializationForQueues: string[]
  continuityCurrentTripOwner: 'required' | 'preferred' | 'off'
  continuityReturningTravelerOwner: 'high' | 'medium' | 'off'
  capacityModel: 'advisory' | 'hard_cap'
  overloadThresholdPct: number
  applySlaPenalty: boolean
  applyReviewBacklogPenalty: boolean
  applyEscalationBacklogPenalty: boolean
  showTopThreeSuggestions: boolean
  learningMode: 'disabled' | 'suggestion_only' | 'bounded_auto_assign'
  minLearningSampleSize: number
  minAutoAssignConfidence: number
  explainabilityRequired: boolean
}
```

Again, exact fields can change. The important point is that the policy becomes explicit and publishable.

---

## Mutability Rules

Recommended split:

| Area | Owner | Admin | SeniorAgent |
| --- | --- | --- | --- |
| queue eligibility rules | yes | yes | read only |
| continuity policy | yes | yes | read only |
| suggestion explainability prefs | yes | yes | read only |
| learning enable/disable | yes | yes, if workspace permits | read only |
| auto-assign expansion to new queues | yes | no or owner-approved only | read only |
| forbidden signal policy | yes | no | read only |

This keeps day-to-day routing governable by Admin while reserving high-risk posture changes for Owner-level review.

---

## Non-Goals For This Route

This route should not become:

- the per-trip assignment screen,
- a live employee ranking board,
- a substitute for member profile editing,
- or an analytics screen with no policy effect.

It should govern policy, not execute every assignment interaction.

---

## Audit Implications

If this addendum is adopted, the audit taxonomy should later be extended to include events like:

- `assignment_policy_learning_mode_changed`
- `assignment_policy_continuity_changed`
- `assignment_policy_capacity_model_changed`
- `assignment_policy_auto_assign_scope_changed`
- `assignment_policy_explainability_changed`

Those events should sit under assignment policy governance, not generic settings change spam.

---

## Final Recommendation

The first shipping posture should be:

- `Manual only` by default,
- `Ranked suggestions` as the first guided rollout,
- explicit continuity controls,
- explicit capacity balancing controls,
- and learning disabled until the metrics-readiness audit is resolved for the required signal families.

That keeps `/settings/assignments` aligned with the broader governance architecture instead of letting assignment intelligence sneak in as a hidden inbox behavior.
