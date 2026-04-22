# Role, Assignment, and AI Agent Governance Exploration

**Date**: 2026-04-22
**Status**: Exploration
**Scope**: Define how the future settings/admin surface should model human roles, trip/workspace assignment, reassignment, and admin-controlled AI worker behavior.

---

## Executive Summary

The repo currently mixes three different concerns that should be modeled separately:

1. **Human access roles** — who can see, approve, assign, edit, and configure.
2. **Assignment state** — who currently owns a trip/workspace, who reviews it, and how handoffs work.
3. **AI worker roles** — which specialist AI agents are enabled, what they are allowed to do, and how much autonomy they have.

The biggest current problem is not just missing UI. It is **role vocabulary drift** and **control-plane conflation**.

Right now the repo contains at least three different human role catalogs:

- `owner | manager | agent | viewer`
- `owner | agent | junior`
- `owner | senior | junior`

That drift should be resolved before building a serious settings/admin page.

---

## Current State Evidence

### 1. Human Role Model Is Inconsistent

Evidence across the repo:

- `frontend/src/types/governance.ts` defines `UserRole = 'owner' | 'manager' | 'agent' | 'viewer'`.
- `Docs/MULTI_TENANT_ACCESS_CONTROL_DISCUSSION.md` models `owner`, `agent`, and `junior`.
- `Docs/research/DATA_STRATEGY.md` models `owner`, `senior`, and `junior`.

This means there is no single canonical answer yet to basic questions like:

- Is `manager` a real product role or a draft alias?
- Is `agent` equivalent to `senior`?
- Is `junior` a distinct access tier or just a training mode?

### 2. Assignment/Reassignment Is Sketched, Not Defined End-to-End

What exists:

- `frontend/src/types/governance.ts` defines `AssignmentRequest` and `ReassignmentRequest`.
- `frontend/src/lib/governance-api.ts` exposes `assignTrips()` and `reassignTrip()`.
- `frontend/src/components/workspace/ReviewControls.tsx` already assumes `Request Changes` can reassign work back to an agent.

What is still undefined:

- Who is allowed to assign versus only claim?
- Whether reassignment is direct, request-based, or approval-based.
- Whether escalation means reassignment or management oversight.
- Whether a trip has one owner only or multiple assignment slots.

### 3. Autonomy Policy Already Exists, But It Is Agency-Level

The backend already has an agency-level autonomy policy shape:

- `src/intake/config/agency_settings.py` defines `AgencyAutonomyPolicy` with `approval_gates`, `mode_overrides`, `auto_proceed_with_warnings`, and `learn_from_overrides`.
- `src/intake/gates.py` defines `AutonomyOutcome`, explicitly separating raw system judgment from policy-enforced action.

This is important because it shows the repo already has a **policy layer** for AI behavior, but it is not yet surfaced as a real admin UX.

### 4. The Architecture Prefers Specialist Roles, Not Generic Agent Swarms

`Docs/CROSS_PROJECT_AGENTIC_PATTERNS_2026-04-20.md` explicitly reinforces a “compiler pipeline, not agentic swarm” approach and calls out **specialist roles, not generic agents**.

That strongly suggests future AI agents here should be modeled as **specialist worker profiles** tied to pipeline responsibilities, not as freeform chat personas.

---

## Key Separation: Three Control Planes

### A. Human Access Plane

Controls what people in the agency can do.

Examples:

- Can invite teammates
- Can edit agency settings
- Can approve high-risk trips
- Can see internal margin data
- Can configure AI worker behavior

### B. Assignment Plane

Controls operational ownership of work.

Examples:

- Trip is unassigned
- Trip is assigned to Priya
- Rahul is backup reviewer
- Owner is escalation authority
- Request changes returns trip to original operator

### C. AI Execution Plane

Controls which AI workers exist and how far they may act.

Examples:

- Intake Extractor can suggest only
- Quote Drafter can prepare traveler-safe drafts
- Risk Sentinel can block only by surfacing review
- Sourcing Scout can widen search only with approval
- Review Auditor can annotate but not send

These are not the same thing. A human `viewer` role and an AI `risk sentinel` role belong to different planes.

---

## Recommended Human Role Model

### Recommendation: Predefined Roles For MVP

Do **not** start with fully custom permissions.

Use a predefined role catalog first, then add additive custom permissions later if needed.

### Proposed Canonical Human Roles

1. **Owner**
2. **Workspace Admin**
3. **Senior Agent**
4. **Junior Agent**
5. **Viewer**

### Why This Set

- `Owner` preserves existing business-owner semantics.
- `Workspace Admin` gives you the operational manager role the user is asking about, without overloading `manager` ambiguously.
- `Senior Agent` resolves the current `agent` vs `senior` drift.
- `Junior Agent` preserves training/review restrictions already discussed in docs.
- `Viewer` remains the lowest-risk read-only role.

### Suggested Mapping From Existing Drift

- Existing `owner` → `Owner`
- Existing `manager` → `Workspace Admin`
- Existing `agent` → `Senior Agent`
- Existing `junior` → `Junior Agent`
- Existing `viewer` → `Viewer`

### Suggested Permission Shape

**Owner**

- billing and subscription
- global agency settings
- team invites/deactivation
- AI policy and autonomy controls
- review overrides and exception approvals

**Workspace Admin**

- team assignment and capacity management
- workflow defaults and notifications
- AI worker enable/disable and scope controls
- review queue management
- cannot change billing or destructive tenant settings by default

**Senior Agent**

- full trip/workspace operations
- can claim and work assigned trips
- can request reassignment
- can approve within configured thresholds
- limited AI preference control, not global AI policy control

**Junior Agent**

- assigned-trip-only editing by default
- cannot finalize traveler-facing send for gated states
- can request help, escalate, and hand off

**Viewer**

- read-only visibility
- no assignment or approval actions

---

## Recommended Assignment Model

### Recommendation: Explicit Assignment Slots, Not A Single Ambiguous Owner Field

For each trip/workspace, model these separately:

1. **Primary Assignee**
2. **Reviewer**
3. **Escalation Owner**
4. **Watchers / Followers**

This avoids overloading one `assigned_to` field with every operational meaning.

### Assignment Actions To Support

1. **Assign** — admin/owner/workspace admin assigns directly.
2. **Claim** — senior/junior agent claims from an unassigned queue if allowed.
3. **Unassign** — remove primary assignee.
4. **Request Handoff** — assignee asks for reassignment but does not directly move ownership.
5. **Reassign** — admin or authorized reviewer transfers ownership.
6. **Escalate** — adds oversight/review, but does not necessarily change assignee.
7. **Return For Changes** — preserves original context and routes work back to the previous operator.

### Important Recommendation: Escalation Is Not Always Reassignment

The repo’s first-principles analysis already leans toward **management oversight rather than blind automatic reassignment**.

That is the correct default here too.

If a trip is risky or high-value:

- keep the current operator as primary assignee,
- add reviewer/escalation owner,
- require approval before certain actions,
- only reassign when there is an actual handoff reason.

This preserves context continuity.

### Reassignment Rules

Recommended defaults:

- `Owner` and `Workspace Admin` can reassign any trip.
- `Senior Agent` can request handoff, but not force-reassign peers by default.
- `Junior Agent` can request help/escalation, not direct reassignment.
- `Request Changes` should route back to the primary assignee unless a reviewer explicitly selects another destination.

### Audit Requirements

Every assignment transition should log:

- who changed it,
- from whom,
- to whom,
- why,
- whether notification was sent,
- whether SLA clock changed.

---

## Recommended AI Agent Role Model

### Recommendation: Predefined Specialist AI Workers

Do not model AI as freeform named bots with arbitrary powers.

Instead, use predefined specialist worker roles aligned to the existing pipeline.

### Proposed AI Worker Catalog

1. **Intake Extractor**
2. **Risk Sentinel**
3. **Quote Drafter**
4. **Sourcing Scout**
5. **Follow-up Composer**
6. **Review Auditor**
7. **Insights Analyst**

### Why This Fits The Existing Architecture

- It aligns with the repo’s specialist-role philosophy.
- It maps cleanly to existing notebook/stage boundaries.
- It gives the admin a concrete, explainable AI workforce instead of vague "AI settings."

### What These AI Roles Mean

**Intake Extractor**

- extracts facts from messy notes
- can suggest structure
- never sends customer-facing content

**Risk Sentinel**

- flags blockers and review conditions
- can force `review` or `block` through policy
- should not silently auto-send

**Quote Drafter**

- drafts internal and traveler-safe output
- can propose, not publish, unless policy explicitly allows

**Sourcing Scout**

- broadens sourcing options
- can be restricted from widening search beyond preferred tiers without approval

**Follow-up Composer**

- drafts clarification messages and status updates
- may be allowed to auto-surface follow-up drafts for low-risk cases

**Review Auditor**

- analyzes quality, leakage risk, and completeness
- annotates, never approves in final human sense

**Insights Analyst**

- summarizes pipeline, workload, override patterns, and bottlenecks
- read/analyze role, not action role

---

## What Workspace Admin Should Be Able To Control For AI

### Recommendation: Workspace Admin Can Control AI Operations, Owner Controls Tenant-Global Business Risk

This creates a clean split:

- `Owner` controls billing, legal/commercial defaults, and hard governance boundaries.
- `Workspace Admin` controls day-to-day AI operations inside the workspace.

### Proposed AI Control Surface

For each AI worker, allow the admin to configure:

1. **Enabled / Disabled**
2. **Allowed stages**
3. **Action mode**: `suggest` | `draft` | `queue_review` | `block_only`
4. **Autonomy gate**: `auto` | `review` | `block`
5. **Data visibility scope**
6. **Allowed sources**
7. **Escalation behavior**
8. **Learning participation**

### Concrete Controls

**Enabled / Disabled**

- turn a worker on or off per agency

**Allowed stages**

- e.g. Quote Drafter active only in `strategy` and `output`

**Action mode**

- `suggest`: show recommendations only
- `draft`: create editable draft artifacts
- `queue_review`: generate output only when routed to approval
- `block_only`: only raise flags, never produce outbound drafts

**Data visibility scope**

- traveler-safe only
- internal planning only
- commercial/margin data allowed or forbidden
- customer history allowed or forbidden

**Allowed sources**

- fixture/scenario data
- customer history
- supplier policy
- agency brand/tone settings
- margin settings

**Escalation behavior**

- when to notify human reviewer
- whether AI can assign reviewer suggestions
- whether it can create draft follow-up tasks

**Learning participation**

- whether overrides feed future tuning
- whether that worker participates in D5-style learning loops

### Controls That Should Probably Remain Owner-Only

- hard safety invariants
- who may see margin-sensitive data
- agency-wide commercial thresholds
- global autonomy defaults for risky states
- destructive or external-integrations access

---

## Recommended Settings IA For This Governance Area

Inside `/settings`, this area should likely become three sections:

1. **People & Roles**
2. **Assignments & Review Flow**
3. **AI Workforce**

### 1. People & Roles

- canonical role catalog
- invite/deactivate users
- assign role
- show effective permissions

### 2. Assignments & Review Flow

- claim rules
- assignment defaults
- reviewer defaults
- escalation owner rules
- request-changes routing
- SLA behavior on reassignment

### 3. AI Workforce

- worker roster
- enable/disable workers
- stage scope
- action mode
- autonomy mode
- data visibility and source access
- audit/log visibility

---

## Recommended Product Decisions

- **ACCEPT**: Use predefined human roles for MVP.
- **ACCEPT**: Introduce `Workspace Admin` as the operational control role.
- **ACCEPT**: Treat assignment as its own domain model, not just a field on trips.
- **ACCEPT**: Model AI workers as predefined specialist roles, not generic bots.
- **ACCEPT+MODIFY**: Let workspace admins configure AI worker operations, but reserve hard business-risk controls for owners.
- **DEFER**: Fully custom permission builder until canonical roles prove insufficient.
- **REJECT**: A single flat “Settings” form that mixes billing, team roles, assignment rules, and AI autonomy in one page.

---

## Open Questions

1. Should `Workspace Admin` be a distinct role, or just the final name for today’s `manager` concept?
2. Should senior agents be allowed to claim any unassigned trip, or only from certain queues?
3. Should reassignment restart SLA timers, preserve them, or split them into ownership vs review SLAs?
4. Which AI workers should exist in v1 of the admin surface: just `Quote Drafter` and `Risk Sentinel`, or the full specialist roster?
5. Should AI worker permissions be visible as a matrix next to human roles, or kept in a dedicated “AI Workforce” section to avoid confusion?
