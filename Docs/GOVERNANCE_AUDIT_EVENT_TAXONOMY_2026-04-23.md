# Governance Audit Event Taxonomy

**Date**: 2026-04-23
**Status**: Canonical design contract
**Scope**: Event naming, envelope schema, domain taxonomy, migration rules, and UI-facing requirements for governance audit history.
**Parent roadmap**: `WORKSPACE_GOVERNANCE_ROADMAP_LIVING_2026-04-22.md`
**Related inputs**:

- `CANONICAL_ROLE_PERMISSION_MATRIX_2026-04-22.md`
- `ASSIGNMENT_ESCALATION_STATE_MACHINE_SPEC_2026-04-22.md`
- `AI_WORKFORCE_REGISTRY_CONTRACT_2026-04-22.md`
- `ARCHITECTURE_DECISION_D1_AUTONOMY_GRADIENT_2026-04-18.md`
- `ARCHITECTURE_DECISION_D5_OVERRIDE_LEARNING_2026-04-18.md`

---

## Executive Summary

The repo already emits audit-like events, but the current model is too lightweight for governed settings, routing, and AI workforce control.

Today the codebase still relies on a generic shape:

- backend writes `{id, type, user_id, timestamp, details}` via [spine-api/persistence.py](file:///Users/pranay/Projects/travel_agency_agent/spine-api/persistence.py),
- frontend types expose a small enum with values like `trip_assigned` and `settings_changed` in [frontend/src/types/governance.ts](file:///Users/pranay/Projects/travel_agency_agent/frontend/src/types/governance.ts),
- review actions are collapsed into a single `review_action` event in [src/analytics/review.py](file:///Users/pranay/Projects/travel_agency_agent/src/analytics/review.py).

That shape is acceptable for a prototype but not for the governance system defined in the roadmap.

This taxonomy upgrades the audit model to support:

1. precise domain-specific event names,
2. reconstructable before/after state,
3. role-aware visibility and redaction,
4. explicit publish boundaries for agency-wide settings,
5. future D5 override learning and policy-suggestion tracing.

---

## Locked Decisions

1. Governance audit history is append-only and immutable.
2. Event names must be domain-specific; generic catch-alls like `settings_changed` and `review_action` are not sufficient long term.
3. Routing, review, AI policy, and autonomy policy changes must be distinguishable without inspecting free-form notes.
4. Draft save and publish are separate audit concepts.
5. Audit history must preserve the distinction between raw system judgment, policy-enforced action, and final human action.

---

## Why This Exists

The canonical governance docs already require more precision than the current audit layer provides.

Evidence:

- [CANONICAL_ROLE_PERMISSION_MATRIX_2026-04-22.md](file:///Users/pranay/Projects/travel_agency_agent/Docs/CANONICAL_ROLE_PERMISSION_MATRIX_2026-04-22.md) requires auditable user invites, role changes, owner transfer, settings changes, AI worker policy changes, and autonomy policy changes.
- [ASSIGNMENT_ESCALATION_STATE_MACHINE_SPEC_2026-04-22.md](file:///Users/pranay/Projects/travel_agency_agent/Docs/ASSIGNMENT_ESCALATION_STATE_MACHINE_SPEC_2026-04-22.md) requires distinct assignment, handoff, reassignment, escalation, and review events.
- [AI_WORKFORCE_REGISTRY_CONTRACT_2026-04-22.md](file:///Users/pranay/Projects/travel_agency_agent/Docs/AI_WORKFORCE_REGISTRY_CONTRACT_2026-04-22.md) requires worker-level policy events.
- [ARCHITECTURE_DECISION_D5_OVERRIDE_LEARNING_2026-04-18.md](file:///Users/pranay/Projects/travel_agency_agent/Docs/ARCHITECTURE_DECISION_D5_OVERRIDE_LEARNING_2026-04-18.md) requires structured override events that can later support learning suggestions.

If the audit contract stays generic, the UI will not be able to answer basic questions such as:

- who reassigned this trip and why,
- who changed the AI worker visibility envelope,
- whether a policy change was merely drafted or actually published,
- whether a final action came from the raw verdict, the policy layer, or a human override.

---

## Canonical Event Envelope

Every governance audit entry should conform to a single shared envelope even though event names differ by domain.

```ts
type GovernanceAuditEvent = {
  id: string
  type: GovernanceAuditEventType
  occurredAt: string
  actor: AuditActor
  scope: AuditScope
  subject: AuditSubject
  source: AuditSource
  reason?: string | null
  summary: string
  previousState?: Record<string, unknown> | null
  nextState?: Record<string, unknown> | null
  diff?: Record<string, { before: unknown; after: unknown }>
  policyContext?: AuditPolicyContext | null
  visibility: AuditVisibility
  tags: string[]
  correlationId?: string | null
  requestId?: string | null
}

type AuditActor = {
  actorId: string
  actorKind: 'user' | 'system' | 'worker' | 'migration'
  displayName?: string
  role?: 'Owner' | 'Admin' | 'SeniorAgent' | 'JuniorAgent' | 'Viewer'
}

type AuditScope = {
  agencyId: string
  workspaceId?: string | null
  tripId?: string | null
  settingsSection?:
    | 'profile'
    | 'agency'
    | 'people'
    | 'assignments'
    | 'ai-workforce'
    | 'pipeline'
    | 'integrations'
    | 'audit'
}

type AuditSubject = {
  subjectKind:
    | 'membership'
    | 'ownership'
    | 'assignment'
    | 'review'
    | 'agency_settings'
    | 'autonomy_policy'
    | 'ai_worker_policy'
    | 'integration'
    | 'override'
    | 'policy_suggestion'
  subjectId: string
  label?: string
}

type AuditSource = 'ui' | 'api' | 'system' | 'learning' | 'migration'
type AuditVisibility = 'full' | 'redacted' | 'restricted'

type AuditPolicyContext = {
  rawVerdict?: string
  effectiveAction?: string
  reviewerId?: string | null
  escalationOwnerId?: string | null
  draftId?: string | null
  publishId?: string | null
}
```

---

## Naming Rules

### Rule 1: Use `<domain>_<verb>` Style Names

Examples:

- `member_invited`
- `assignment_reassigned`
- `ai_worker_enabled`
- `autonomy_policy_published`

### Rule 2: Encode Semantic Difference In The Name

Do not collapse multiple actions into a single umbrella event with an `action` field when the actions matter independently for governance.

Bad:

- `review_action`

Good:

- `review_approved`
- `review_rejected`
- `review_returned_for_changes`
- `trip_escalated`

### Rule 3: Keep Publish Separate From Draft Save

Examples:

- `agency_settings_draft_saved`
- `agency_settings_published`
- `autonomy_policy_draft_saved`
- `autonomy_policy_published`

---

## Canonical Event Families

## 1. Membership And Ownership

Required events:

- `member_invited`
- `member_activated`
- `member_deactivated`
- `member_removed`
- `member_role_changed`
- `admin_delegated`
- `admin_revoked`
- `ownership_transfer_initiated`
- `ownership_transferred`

Required payload fragments:

- affected member id
- previous role and next role when relevant
- inviter / remover / transfer initiator
- agency/workspace scope
- reason when deactivating or transferring ownership

## 2. Assignment, Handoff, And Escalation

Required events:

- `assignment_assigned`
- `assignment_claimed`
- `assignment_unassigned`
- `handoff_requested`
- `handoff_cancelled`
- `assignment_reassigned`
- `reviewer_added`
- `reviewer_removed`
- `trip_escalated`
- `trip_deescalated`
- `review_returned_for_changes`
- `review_approved`
- `review_rejected`

Required payload fragments:

- previous routing slots
- next routing slots
- ownership state and governance state before/after
- ownership, review, and handoff SLA impact if changed
- reason for reassignment/escalation/review outcome

## 3. Agency And Profile Settings

Required events:

- `profile_preferences_updated`
- `agency_settings_draft_saved`
- `agency_settings_published`
- `agency_profile_updated`
- `agency_operational_defaults_updated`

Notes:

- `profile_preferences_updated` is immediate-save and user-scoped.
- agency-wide changes should usually roll into draft and publish events rather than a generic field-level spam stream.

## 4. Assignment Policy Settings

Required events:

- `assignment_policy_draft_saved`
- `assignment_policy_published`
- `assignment_claim_policy_changed`
- `assignment_escalation_defaults_changed`
- `assignment_sla_policy_changed`

## 5. D1 Autonomy And Pipeline Governance

Required events:

- `autonomy_policy_draft_saved`
- `autonomy_policy_published`
- `autonomy_gate_changed`
- `autonomy_mode_override_changed`
- `autonomy_learning_changed`
- `autonomy_review_threshold_explainer_updated`

Required payload fragments:

- raw verdict or decision-state reference
- previous gate and next gate
- invariant handling where relevant, especially `STOP_NEEDS_REVIEW`
- publish boundary metadata

## 6. AI Workforce Governance

Required events:

- `ai_worker_enabled`
- `ai_worker_disabled`
- `ai_worker_stage_scope_changed`
- `ai_worker_action_mode_changed`
- `ai_worker_autonomy_mode_changed`
- `ai_worker_visibility_scope_changed`
- `ai_worker_learning_changed`
- `ai_worker_policy_published`

Required payload fragments:

- worker id
- old policy fragment and new policy fragment
- whether the changed field was Owner-only or Admin-editable
- reason for high-risk visibility or autonomy changes

## 7. Integration Governance

Required events:

- `integration_connected`
- `integration_disconnected`
- `integration_policy_changed`
- `integration_webhook_updated`
- `integration_api_key_rotated`
- `integration_access_scope_changed`

## 8. Overrides And Adaptive Governance

Required events:

- `override_created`
- `override_rationale_recorded`
- `override_pattern_detected`
- `policy_suggestion_created`
- `policy_suggestion_approved`
- `policy_suggestion_rejected`

Required payload fragments:

- override category
- affected decision / worker / route policy
- rationale text and structured tags
- whether the event is descriptive telemetry or an approved policy change

---

## Required Cross-Cutting Fields By Domain

### Routing Events

Routing events must always include:

- `tripId`
- slot deltas
- actor
- reason
- timestamp

### Publish Events

Publish events must always include:

- draft id
- publisher id
- settings section
- summary of changed fields
- previous published version reference when available

### AI Worker Events

AI worker events must always include:

- worker id
- changed fields
- old value and new value
- mutability tier (`Owner` vs `Admin` authority)

### Override Events

Override events must always include:

- override id
- trip or policy target
- override type
- rationale
- structured tags when available

---

## Current-State To Canonical Migration Map

| Current event or pattern | Canonical outcome |
|---|---|
| `trip_assigned` | `assignment_assigned` |
| `trip_unassigned` | `assignment_unassigned` |
| `review_action` with `approved` | `review_approved` |
| `review_action` with `rejected` | `review_rejected` |
| `review_action` with `revision_needed` | `review_returned_for_changes` |
| `review_action` with `escalated` | `trip_escalated` |
| `settings_changed` | one of the specific section/domain events above |
| `user_invited` | `member_invited` |
| `user_removed` | `member_removed` or `member_deactivated` depending on behavior |
| `override_created` | remains `override_created` but must adopt canonical envelope |

Important rule:

- do not preserve old generic names as long-term first-class events once the canonical taxonomy is implemented.

Compatibility shims are acceptable during migration, but the UI and docs should speak canonical names.

---

## Visibility And Redaction Rules

Audit visibility should be role-aware.

### `full`

- visible to Owner/Admin and any other role explicitly allowed by policy

### `redacted`

- event is visible, but sensitive fields are masked
- example: a Viewer may see that an AI worker visibility scope changed without seeing the sensitive old/new commercial settings payload

### `restricted`

- event exists but is not disclosed at all to that role

This matters especially for:

- billing/integration credentials,
- commercial-sensitive AI worker access,
- owner-only policy changes,
- potentially customer-sensitive override rationale.

---

## UI Implications

The audit feed in `/settings/audit` should be able to group events by these domains:

1. People
2. Assignments
3. Pipeline
4. AI Workforce
5. Integrations
6. Overrides
7. Publish History

The UI should not have to parse arbitrary `details` blobs to determine which badge, title, or diff summary to show.

This is one of the main reasons the taxonomy needs precise event names.

---

## Relationship To D1 And D5

### D1 Autonomy

Governance audit history must preserve:

- raw decision judgment,
- policy-enforced action,
- human final action.

Without that separation, future settings/audit UI cannot explain why the system auto-routed, blocked, or escalated a trip.

### D5 Override Learning

Override-learning suggestions should not silently mutate policy.

The audit layer therefore needs to distinguish:

- descriptive evidence (`override_created`, `override_pattern_detected`),
- from acted-on governance (`policy_suggestion_approved`, `autonomy_policy_published`).

---

## Persistence Guidance

The current [spine-api/persistence.py](file:///Users/pranay/Projects/travel_agency_agent/spine-api/persistence.py) file-based `AuditStore` may remain temporarily, but the stored shape should evolve toward the canonical envelope instead of accumulating more `type + details` shortcuts.

That means:

- new event writes should already prefer canonical names,
- review/routing code should stop collapsing actions into generic umbrella events,
- frontend types should migrate from the old narrow enum to the canonical taxonomy.

---

## Non-Goals

This document does not define:

- the final storage engine for audit events,
- the full UI layout of `/settings/audit`,
- event retention periods,
- compliance export formats.

Those belong in sibling implementation and enterprise-governance phases.

---

## Acceptance Criteria

This taxonomy is adopted when:

1. settings, routing, review, AI, and override changes use canonical domain-specific event names,
2. generic `settings_changed` and `review_action` no longer carry the long-term governance load,
3. audit entries can reconstruct before/after routing and policy state,
4. the audit feed can render domain-aware labels and diffs without parsing ambiguous free-form payloads,
5. D1 and D5 flows can attach raw verdict, effective action, and final override metadata to the same audit history.
