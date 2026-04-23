# AI Workforce Registry Contract

**Date**: 2026-04-22
**Status**: Canonical design contract
**Scope**: Registry, policy schema, governance split, activation model, and audit expectations for specialist AI workers.
**Parent roadmap**: `WORKSPACE_GOVERNANCE_ROADMAP_LIVING_2026-04-22.md`

---

## Executive Summary

The system should not model AI as one generic assistant with scattered flags.

It should model a governed workforce of specialist AI workers whose powers are explicit, auditable, and configurable.

### Canonical Worker Registry

1. `intake_extractor`
2. `risk_sentinel`
3. `quote_drafter`
4. `sourcing_scout`
5. `followup_composer`
6. `review_auditor`
7. `insights_analyst`

### Locked Decisions

1. The full specialist workforce is the target architecture.
2. Worker activation may phase, but the registry contract is full from the start.
3. AI governance belongs in a dedicated `AI Workforce` settings area, not buried in generic settings.
4. `Owner` defines the hard policy envelope; `Admin` manages worker operations within that envelope.

---

## Why This Exists

The repo already points in this direction:

- autonomy policy exists in backend form,
- specialist role thinking is already documented,
- the detailed agent map catalogs differentiated worker types,
- and override learning implies worker-level feedback loops.

Without a registry contract, the product risks accumulating one-off toggles and hidden worker behaviors.

---

## Core Registry Shape

```ts
type AiWorkerRegistry = {
  version: string
  workers: AiWorkerDefinition[]
}

type AiWorkerDefinition = {
  id: AiWorkerId
  label: string
  category: AiWorkerCategory
  description: string
  stageScopeDefault: WorkspaceStage[]
  defaultPolicy: AiWorkerPolicy
  maturity: WorkerMaturity
  ownerPlane: 'owner' | 'admin'
}
```

### Worker ID Enum

```ts
type AiWorkerId =
  | 'intake_extractor'
  | 'risk_sentinel'
  | 'quote_drafter'
  | 'sourcing_scout'
  | 'followup_composer'
  | 'review_auditor'
  | 'insights_analyst'
```

### Category Enum

```ts
type AiWorkerCategory =
  | 'extractor'
  | 'validator'
  | 'composer'
  | 'ranker'
  | 'analyst'
```

### Maturity Enum

```ts
type WorkerMaturity =
  | 'planned'
  | 'shadow'
  | 'active'
  | 'adaptive'
```

This allows the full roster to exist before every worker is operationally active.

---

## Worker Policy Shape

```ts
type AiWorkerPolicy = {
  enabled: boolean
  allowedStages: WorkspaceStage[]
  actionMode: ActionMode
  autonomyMode: AutonomyMode
  dataVisibilityScope: DataVisibilityScope
  allowedSources: AllowedSource[]
  escalationBehavior: EscalationBehavior
  learningEnabled: boolean
  requiresHumanReview: boolean
}
```

### Action Mode

```ts
type ActionMode =
  | 'suggest'
  | 'draft'
  | 'queue_review'
  | 'block_only'
  | 'analyze_only'
```

### Autonomy Mode

```ts
type AutonomyMode =
  | 'auto'
  | 'review'
  | 'block'
```

### Data Visibility Scope

```ts
type DataVisibilityScope =
  | 'traveler_safe_only'
  | 'internal_ops'
  | 'commercial_sensitive'
  | 'history_augmented'
```

### Allowed Source

```ts
type AllowedSource =
  | 'trip_input'
  | 'customer_history'
  | 'agency_policy'
  | 'supplier_policy'
  | 'scenario_fixture'
  | 'commercial_settings'
```

### Escalation Behavior

```ts
type EscalationBehavior = {
  canRaiseReview: boolean
  canSuggestReviewer: boolean
  canOpenHandoffSuggestion: boolean
  canCreateFollowupTask: boolean
}
```

---

## Canonical Worker Definitions

## 1. Intake Extractor

**Category**: `extractor`

Purpose:

- converts messy notes into structured internal facts

Default policy:

- enabled: true
- allowed stages: `intake`, `packet`
- action mode: `suggest`
- autonomy mode: `auto`
- data scope: `internal_ops`

Restrictions:

- never sends traveler-facing content

## 2. Risk Sentinel

**Category**: `validator`

Purpose:

- detects risk, blockers, and review requirements

Default policy:

- enabled: true
- allowed stages: all decision-bearing stages
- action mode: `block_only`
- autonomy mode: `block`
- data scope: `commercial_sensitive`

Restrictions:

- can block or request review, not silently finalize traveler communication

## 3. Quote Drafter

**Category**: `composer`

Purpose:

- produces editable internal and traveler-safe draft output

Default policy:

- enabled: true
- allowed stages: `strategy`, `output`
- action mode: `draft`
- autonomy mode: `review`
- data scope: `internal_ops`

Restrictions:

- does not auto-publish by default

## 4. Sourcing Scout

**Category**: `ranker`

Purpose:

- explores sourcing options and widening paths

Default policy:

- enabled: true
- allowed stages: `strategy`
- action mode: `suggest`
- autonomy mode: `review`
- data scope: `commercial_sensitive`

Restrictions:

- widening beyond preferred tiers must honor sourcing/autonomy policy

## 5. Follow-up Composer

**Category**: `composer`

Purpose:

- drafts clarification questions, updates, and next-step communications

Default policy:

- enabled: true
- allowed stages: `intake`, `output`, `safety`
- action mode: `draft`
- autonomy mode: `review`
- data scope: `traveler_safe_only`

Restrictions:

- cannot access commercial-sensitive data unless explicitly elevated by policy

## 6. Review Auditor

**Category**: `validator`

Purpose:

- audits output for leakage, completeness, and policy gaps

Default policy:

- enabled: true
- allowed stages: `decision`, `strategy`, `output`, `safety`
- action mode: `analyze_only`
- autonomy mode: `review`
- data scope: `commercial_sensitive`

Restrictions:

- annotates, does not function as final human approver

## 7. Insights Analyst

**Category**: `analyst`

Purpose:

- summarizes bottlenecks, override patterns, worker health, and operational trends

Default policy:

- enabled: true
- allowed stages: management/analytics surfaces
- action mode: `analyze_only`
- autonomy mode: `auto`
- data scope: `history_augmented`

Restrictions:

- analysis only, no direct trip mutation

---

## Governance Split

### Owner-Controlled Decisions

Owner retains control over:

- granting `commercial_sensitive` worker visibility
- granting agency-wide autonomy envelope changes
- enabling learning that can generate policy suggestions
- worker policies that affect business risk or traveler trust boundaries

### Admin-Controlled Decisions

Admin may control:

- worker enable/disable
- stage scope
- action mode
- routing and notification behaviors
- worker operations inside the owner-defined safety/commercial envelope

### Agent-Level Interaction

Agents do not administer the registry globally.

They may still:

- use worker output
- trigger worker runs in authorized contexts
- override worker suggestions where policy allows
- contribute feedback signals into override learning loops

---

## Registry Activation Strategy

The product should expose the **full registry** from the start even if not every worker is fully active.

### Maturity Semantics

**planned**

- worker is part of the architecture but not yet executing in production

**shadow**

- worker runs without affecting live decisions

**active**

- worker participates in governed live workflows

**adaptive**

- worker participates in feedback-driven tuning or suggestion loops

This allows the roster to remain stable while capability matures per worker.

---

## Settings and API Contract

### Suggested Endpoints

- `GET /api/settings/ai-workforce`
- `PATCH /api/settings/ai-workforce/:workerId`
- `POST /api/settings/ai-workforce/publish`
- `GET /api/settings/ai-workforce/audit`

### API Response Shape

The `GET` response should include:

- registry version
- worker definitions
- effective policies
- role-based mutability hints for current user
- publish/draft state if a draft-and-publish model is used

---

## Audit Requirements

Every worker policy change should emit audit events such as:

- `ai_worker_enabled`
- `ai_worker_disabled`
- `ai_worker_stage_scope_changed`
- `ai_worker_action_mode_changed`
- `ai_worker_visibility_scope_changed`
- `ai_worker_learning_changed`
- `ai_worker_policy_published`

Each event should record:

- actor id
- worker id
- old policy fragment
- new policy fragment
- reason / note if provided
- timestamp

---

## Relationship To D1 And D5

### D1 Autonomy

Worker autonomy must not compete with the agency-level autonomy contract.

Interpretation:

- worker policy defines what the worker is allowed to attempt
- D1 agency autonomy policy governs whether the resulting action may auto/review/block

### D5 Override Learning

Worker-level feedback should be capturable as part of override learning.

Examples:

- quote drafts frequently overridden in one stage
- sourcing scout recommendations consistently rejected for one destination class
- follow-up composer outputs frequently approved unchanged in one context

That data should feed adaptive governance suggestions, not silent auto-rewrites.

---

## UI Implications

The `AI Workforce` settings surface should show:

- the full worker roster
- maturity status
- a one-line purpose statement
- enabled/disabled state
- stage scope
- action mode
- autonomy mode
- visibility scope
- who can edit this setting

The UI should make it obvious which worker can:

- only analyze,
- draft editable artifacts,
- block,
- or request review.

---

## Non-Goals

This document does not define:

- human role permission matrix in full
- trip routing state machine
- audit payload taxonomy in complete detail
- exact frontend component layout

Those belong in sibling specs.

---

## Acceptance Criteria

This registry contract is adopted when:

1. the full specialist workforce has stable IDs and categories
2. worker policies are represented explicitly rather than by scattered flags
3. ownership between `Owner` and `Admin` for AI governance is unambiguous
4. worker policy changes are auditable
5. D1 autonomy and D5 override learning can integrate with the worker layer without schema replacement
