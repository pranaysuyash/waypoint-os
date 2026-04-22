# Workspace Governance Roadmap (Living)

**Date**: 2026-04-22
**Status**: Living roadmap
**Scope**: Full production roadmap for roles, settings, assignment/reassignment, escalation governance, and admin-controlled AI workforce.
**Positioning**: Phased by dependency, not ambition. This is not an MVP scoping document.

---

## Executive Summary

The best approach is to treat workspace governance as a **full operating model**, not a missing settings page.

That operating model has five coupled systems:

1. **Identity and tenancy** — who the workspace belongs to.
2. **Human governance** — roles, permissions, approvals, and ownership.
3. **Operational routing** — assignment, escalation, review, and reassignment.
4. **AI workforce governance** — which specialist AI workers exist, what they can see, and what they can do.
5. **Adaptive control loops** — override learning, policy suggestions, and owner-approved autonomy tuning.

### Decisions Locked For This Roadmap

These are now the recommended defaults for the program:

1. **Workspace creator is the Owner and Admin bootstrap identity.**
2. **Escalation preserves the current primary assignee by default.**
3. **Escalation may open a managed reassignment path, but escalation itself is not implicit reassignment.**
4. **The system should support the full specialist AI workforce model, not a narrow MVP subset.**
5. **Delivery should be phased, but every phase must fit the final production architecture without throwaway contracts.**

---

## Why This Is The Best Approach

### 1. The problem is not “missing settings.”

The current repo has:

- a stub-like app-level settings concept,
- an agency-level autonomy policy already forming in backend code,
- governance hooks and role types in frontend,
- assignment/review concepts in UX,
- and no canonical unifying control plane.

If we build a page before the model, we will create more drift.

### 2. Creator = Owner/Admin is the right bootstrap

For a workspace product, the creator should immediately have:

- tenant ownership,
- admin privileges,
- governance authority,
- AI policy authority,
- billing and integration authority.

That avoids the awkwardness of asking “who is the real owner?” after workspace creation.

Later, those privileges can be delegated to additional admins without weakening the creator bootstrap.

### 3. Escalation should preserve continuity

The trip operator usually holds the most context.

If escalation automatically reassigns the trip away from them, the system destroys context continuity and adds operational churn. The better pattern is:

- keep the current operator as **primary assignee**,
- add **reviewer / escalation owner**,
- require approval or oversight,
- reassign only as an explicit follow-on action.

### 4. AI needs first-class governance, not hidden toggles

This repo already has the beginnings of an autonomy policy and a specialist-role philosophy. The long-term system should therefore treat AI workers like a governed workforce:

- explicit worker types,
- explicit scopes,
- explicit permissions,
- explicit data visibility,
- explicit review/autonomy rules,
- explicit logging and learning behavior.

### 5. Full roadmap beats patchwork

The user directive is correct: this should not be solved via small settings patches. The right move is to define the full target architecture and then phase implementation in the dependency order that preserves contracts.

---

## Canonical End-State Model

### Control Plane 1: Identity & Tenancy

Core entities:

- `Agency`
- `Workspace`
- `AgencyUser`
- `Membership`
- `WorkspaceOwnership`

### Control Plane 2: Human Governance

Canonical role catalog:

1. `Owner`
2. `Admin`
3. `SeniorAgent`
4. `JuniorAgent`
5. `Viewer`

Interpretation:

- The **workspace creator** gets `Owner` and `Admin` capabilities at bootstrap.
- `Admin` is delegable.
- `Owner` is the business/governance authority role.
- `SeniorAgent` and `JuniorAgent` model operational capability tiers.
- `Viewer` is read-only.

### Control Plane 3: Operational Routing

Each trip/workspace should support separate routing slots:

1. `primary_assignee`
2. `reviewer`
3. `escalation_owner`
4. `watchers`
5. `handoff_history`

### Control Plane 4: AI Workforce

Canonical worker registry:

1. `intake_extractor`
2. `risk_sentinel`
3. `quote_drafter`
4. `sourcing_scout`
5. `followup_composer`
6. `review_auditor`
7. `insights_analyst`

Each worker has its own policy object.

### Control Plane 5: Adaptive Governance

This is the long-loop layer that learns from:

- overrides,
- reassignment patterns,
- review bottlenecks,
- worker-level acceptance/rejection,
- trip-classification pass-through,
- false-positive/false-negative governance events.

This layer proposes changes. It does not auto-rewrite policy without approval.

---

## Foundational Principles

### Principle 1: One canonical vocabulary

Resolve current role drift into one official catalog.

### Principle 2: Preserve raw judgment, govern execution separately

The backend already moves in this direction with a distinction between raw verdict and policy outcome. The same separation should exist in UI and routing.

### Principle 3: Escalation is oversight first

Escalation adds governance. Reassignment changes ownership. They are related but not identical.

### Principle 4: AI workers are governed actors

Not all AI should be able to draft, widen sourcing, or consume internal/commercial data.

### Principle 5: Phases add capability without replacing contracts

Every phase must fit the final architecture so we do not replace role models, settings routes, or policy objects later.

---

## Recommended Information Architecture

### Top-Level Route

Create one real governance surface:

- `/settings`

### Subroutes

1. `/settings/profile`
2. `/settings/agency`
3. `/settings/people`
4. `/settings/assignments`
5. `/settings/ai-workforce`
6. `/settings/pipeline`
7. `/settings/integrations`
8. `/settings/audit`

### Ownership Model By Subroute

**Profile**

- personal preferences
- local/operator defaults

**Agency**

- brand, hours, channels, business defaults

**People**

- roles, invites, deactivation, membership

**Assignments**

- routing rules, escalation defaults, workload policy, claim policy

**AI Workforce**

- worker registry, stage scope, action mode, visibility scope, autonomy scope

**Pipeline**

- D1 autonomy matrix, stage rules, operational parameters

**Integrations**

- external systems, supplier APIs, email/calendar/webhooks

**Audit**

- settings changes, assignment events, override history, AI action log

---

## Canonical Human Role Strategy

### Creator Bootstrap

At workspace creation:

- `created_by_user_id` becomes the default `workspace_owner_id`
- creator receives `Owner + Admin` capabilities
- creator becomes default `escalation_owner` until changed

### Role Semantics

**Owner**

- commercial and governance authority
- final say on policy, billing, integration, hard safety/commercial controls

**Admin**

- day-to-day workspace administration
- team management, assignments, AI worker operations, routing defaults

**SeniorAgent**

- full operational trip work
- can claim, request handoff, operate assigned trips, act within thresholds

**JuniorAgent**

- assigned-only default scope
- stronger review gates and restricted finalization powers

**Viewer**

- read-only

### Why Owner And Admin Are Both Needed

The creator should start as both.

But the model still needs both concepts because later the owner may want to delegate administration without delegating business control.

That means:

- bootstrap: same person,
- later operation: possibly different people.

---

## Escalation, Review, and Reassignment Strategy

### Default Rule

Escalation does the following by default:

1. keeps `primary_assignee` unchanged,
2. attaches `reviewer` or `escalation_owner`,
3. raises governance priority,
4. adds approval constraints,
5. records audit/log events,
6. optionally opens a reassignment action.

### Reassignment Rule

Reassignment is a separate explicit transition:

- manual admin action,
- owner action,
- or policy-authorized routing action.

### Routing Actions To Support

1. `assign`
2. `claim`
3. `unassign`
4. `request_handoff`
5. `reassign`
6. `escalate`
7. `return_for_changes`
8. `add_reviewer`
9. `watch`

### SLA Strategy

Do not use a single SLA clock only.

Split into:

1. **ownership SLA** — how long primary assignee has held action
2. **review SLA** — how long review is pending
3. **handoff SLA** — how long reassignment/request-handoff is unresolved

This avoids losing accountability when escalation happens.

---

## AI Workforce Governance Strategy

### Worker Policy Object

Every AI worker should eventually have a policy object with fields like:

- `enabled`
- `allowed_stages`
- `action_mode`
- `autonomy_mode`
- `data_visibility_scope`
- `allowed_sources`
- `escalation_behavior`
- `learning_enabled`
- `requires_human_review`

### Action Modes

1. `suggest`
2. `draft`
3. `queue_review`
4. `block_only`
5. `analyze_only`

### Visibility Scopes

1. `traveler_safe_only`
2. `internal_ops`
3. `commercial_sensitive`
4. `history_augmented`

### Governance Split

**Owner-controlled AI decisions**

- hard commercial thresholds
- margin-sensitive worker access
- agency-wide autonomy defaults
- learning opt-in for policy changes

**Admin-controlled AI decisions**

- enable/disable workers
- stage scope
- action mode
- routing defaults
- worker-specific operational tuning

### Why Full Specialist Workforce Is Correct

The repo’s architecture already trends toward specialist roles. The system should therefore expose the workforce as a governed roster, even if some workers activate later than others.

That preserves the final design while allowing staged activation.

---

## Living Roadmap Phases

## Phase 0 — Vocabulary and Contract Hardening

**Goal**: lock the control model before more UI and APIs drift.

### Deliverables

- canonical human role catalog
- canonical assignment slot schema
- canonical AI worker registry
- canonical settings route map
- canonical audit event taxonomy for settings/routing/AI actions

### Acceptance Signals

- no competing role vocabularies remain in active design docs
- frontend/backed/docs use the same role names
- assignment and escalation terminology is stable

---

## Phase 1 — Identity, Tenancy, and Workspace Ownership

**Goal**: make the workspace creator model real.

### Deliverables

- auth/provider integration
- agencies/workspaces/users/memberships schema
- creator bootstrap to `Owner + Admin`
- tenant-aware session model
- permission checks on settings/governance routes

### Acceptance Signals

- creator is deterministically recognized as owner/admin
- settings visibility is role-aware
- agency-scoped data isolation exists

---

## Phase 2 — People and Permission Administration

**Goal**: make the human governance plane operable.

### Deliverables

- `/settings/people`
- invite/deactivate/assign-role flows
- role descriptions and effective permission views
- owner/admin delegation rules
- audit trail for people changes

### Acceptance Signals

- owner can add another admin
- senior/junior/viewer differences are enforced in UI and API
- membership changes emit audit events

---

## Phase 3 — Assignment, Escalation, and Review Engine

**Goal**: turn assignment into a real routing system.

### Deliverables

- primary assignee / reviewer / escalation owner support
- claim rules
- request-handoff flow
- explicit reassignment flow
- escalation that preserves assignee by default
- split SLA model

### Acceptance Signals

- escalated trip keeps primary owner unless explicit reassignment occurs
- reassignment history is visible and audited
- review queue and trip workspace agree on routing state

---

## Phase 4 — Settings Control Center

**Goal**: ship the real governance surface.

### Deliverables

- `/settings` shell + subroute layout
- agency/profile/people/assignments/ai-workforce/pipeline/integrations/audit sections
- draft-and-publish settings workflow
- settings change audit trail
- route-level role gating

### Acceptance Signals

- no more dependence on workbench settings drawer for app governance
- admins can operate routing and AI sections from one place
- audit log shows who changed what

---

## Phase 5 — AI Workforce Activation and Worker Governance

**Goal**: make AI workers first-class governed actors.

### Deliverables

- worker registry backend contract
- `/settings/ai-workforce`
- enable/disable workers
- stage scope + action mode + visibility scope
- worker-level access rules tied to agency policy
- UI explanation of what each worker can and cannot do

### Acceptance Signals

- owner/admin can inspect full AI workforce roster
- workers with commercial-sensitive access are visibly governed
- worker actions are logged and attributable

---

## Phase 6 — D1 Policy Surface and Approval Governance

**Goal**: expose agency autonomy as a real product surface.

### Deliverables

- `/settings/pipeline` autonomy matrix
- decision-state gate editing
- mode override editing
- review-threshold explanation UI
- link from escalations and review queues back to autonomy policy

### Acceptance Signals

- owner can explain why a trip was auto/review/block from UI
- raw verdict and effective action remain distinct in API and UI
- no competing approval settings contract exists

---

## Phase 7 — Override Learning and Adaptive Governance

**Goal**: let the system suggest governance changes from evidence.

### Deliverables

- D5 override event bus in production
- worker-level acceptance/rejection telemetry
- trip classification support for autonomy analysis
- suggestion inbox for policy changes
- owner-approved policy updates only

### Acceptance Signals

- system can surface “this class of trips is over-reviewed” suggestions
- system can surface “this worker is frequently overridden in this stage” suggestions
- owner approves or rejects suggested changes from a governed UI

---

## Phase 8 — Enterprise Governance and Integration Surface

**Goal**: make the operating model enterprise-ready.

### Deliverables

- integration permissions by role
- export/compliance/audit views
- API key and webhook governance
- multi-admin governance rules
- data retention and access policy controls

### Acceptance Signals

- tenant administrators can govern integrations without bypassing owner controls
- compliance and audit surfaces are coherent with people/AI/routing history

---

## Priority Order Inside The Program

If we execute this program properly, the dependency order should be:

1. vocabulary/contracts
2. identity/tenancy/bootstrap ownership
3. human roles and people admin
4. assignment/escalation/review engine
5. unified settings surface
6. AI workforce control plane
7. adaptive learning/governance loops
8. enterprise/compliance/integration governance

This is the correct order because:

- assignment without identity is fake,
- settings without role enforcement is unsafe,
- AI controls without unified settings become fragmented,
- adaptive autonomy without audit and override capture is premature.

---

## What Should Happen To Existing Docs

This roadmap should become the umbrella reference for this topic.

Existing docs should be treated as inputs:

- `SETTINGS_PROFILE_EXPLORATION_2026-04-22.md` → route and IA exploration
- `ROLE_ASSIGNMENT_AND_AI_AGENT_GOVERNANCE_EXPLORATION_2026-04-22.md` → detailed governance model exploration
- `SETTINGS_DASHBOARD_SPEC.md` → earlier UI/dashboard concept, to be reconciled not duplicated
- `ARCHITECTURE_DECISION_D1_AUTONOMY_GRADIENT_2026-04-18.md` → autonomy policy contract
- `ARCHITECTURE_DECISION_D5_OVERRIDE_LEARNING_2026-04-18.md` → adaptive governance learning layer
- `DISCOVERY_GAP_AUTH_IDENTITY_MULTI_AGENT_2026-04-16.md` → auth and identity dependency map

---

## Living Document Rules

This roadmap should be updated when any of these change:

1. canonical role catalog
2. assignment slot contract
3. AI worker registry
4. settings IA
5. auth/tenant model
6. autonomy contract
7. override learning contract

Update protocol:

- preserve prior decisions,
- add a dated addendum section when strategy changes,
- do not silently rewrite history,
- mark each phase as `planned`, `active`, `partially shipped`, or `complete`.

---

## Recommended Immediate Next Artifacts

The next planning documents that should follow this roadmap are:

1. **Canonical Role & Permission Matrix**
2. **Assignment / Escalation State Machine Spec**
3. **AI Workforce Registry Contract**
4. **Settings Route + Subroute UX Contract**
5. **Governance Audit Event Taxonomy**

---

## Final Recommendation

The best approach is:

- make the workspace creator the owner/admin bootstrap,
- preserve assignee continuity during escalation,
- make reassignment explicit and audited,
- treat AI workers as a governed specialist workforce,
- centralize everything in a real settings/governance control center,
- and phase implementation in dependency order without shrinking the final design.

That gives you a system that can scale from solo agency founder to multi-operator team to fully governed AI-assisted operating system without changing its core contracts halfway through.
