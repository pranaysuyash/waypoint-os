# Settings Route + Subroute UX Contract

**Date**: 2026-04-23
**Status**: Canonical design contract
**Scope**: Route structure, subroute responsibilities, role-aware UX, state model, and migration boundaries for the real `/settings` control center.
**Parent roadmap**: `WORKSPACE_GOVERNANCE_ROADMAP_LIVING_2026-04-22.md`
**Related inputs**:

- `SETTINGS_PROFILE_EXPLORATION_2026-04-22.md`
- `CANONICAL_ROLE_PERMISSION_MATRIX_2026-04-22.md`
- `ASSIGNMENT_ESCALATION_STATE_MACHINE_SPEC_2026-04-22.md`
- `AI_WORKFORCE_REGISTRY_CONTRACT_2026-04-22.md`
- `SETTINGS_DASHBOARD_SPEC.md`

---

## Executive Summary

`/settings` should be the product's real governance control center, not a shallow profile page and not an expansion of the existing workbench drawer.

The route must do five jobs at once:

1. provide a stable home for personal preferences,
2. expose agency-level operating defaults,
3. centralize human governance and assignment policy,
4. expose AI workforce and D1 autonomy controls as first-class product surfaces,
5. give owners/admins a coherent audit trail for every governed change.

This contract resolves the remaining UX ambiguity by defining:

- the canonical `/settings` shell,
- the role-aware default landing behavior,
- the eight subroutes already named in the governance roadmap,
- which surfaces are immediate-save vs. draft-and-publish,
- and how current placeholder settings endpoints should converge into one coherent route model.

---

## Locked Decisions

1. `/settings` is the single canonical governance route family.
2. `frontend/src/app/workbench/SettingsPanel.tsx` remains a workbench-only pipeline/debug drawer and must not become the production governance surface.
3. `/settings` must be role-aware at entry time and at subroute level, not just a flat page with hidden sections.
4. Personal preferences may save immediately; agency-wide governance settings use a draft-and-publish workflow.
5. `/settings/pipeline` is the canonical home for D1 autonomy policy. The older placeholder approvals surface must not survive as a competing contract.

---

## Why This Exists

The repo currently has governance-adjacent settings scattered across multiple layers:

- [frontend/src/components/layouts/Shell.tsx](file:///Users/pranay/Projects/travel_agency_agent/frontend/src/components/layouts/Shell.tsx) has no `/settings` entry at all.
- [frontend/src/app/workbench/SettingsPanel.tsx](file:///Users/pranay/Projects/travel_agency_agent/frontend/src/app/workbench/SettingsPanel.tsx) only controls strict leakage, raw JSON visibility, and fixture scenario selection.
- [frontend/src/lib/governance-api.ts](file:///Users/pranay/Projects/travel_agency_agent/frontend/src/lib/governance-api.ts) still exposes placeholder `getPipelineStages()`, `getApprovalThresholds()`, and `getAutonomyPolicy()` paths at the same time.
- [frontend/src/types/governance.ts](file:///Users/pranay/Projects/travel_agency_agent/frontend/src/types/governance.ts) still uses the older `owner | manager | agent | viewer` vocabulary.
- [spine-api/server.py](file:///Users/pranay/Projects/travel_agency_agent/spine-api/server.py) already has a combined `GET /api/settings`, a separate `POST /api/settings/operational`, and a separate `GET/POST /api/settings/autonomy` surface.

If implementation starts without a UX contract, the app will likely ship:

- a route tree that does not match the role matrix,
- UI that keeps the legacy approvals model alive beside D1 autonomy,
- and duplicated settings entry points with different persistence semantics.

---

## UX Goals

The settings surface should make four things obvious:

1. what the current user is allowed to change,
2. which settings affect only them vs. the whole agency,
3. which settings are drafts vs. published policy,
4. how a routing or AI policy change will affect live operations.

The surface should feel like a control center, not a generic form dump.

---

## Canonical Route Family

### Top-Level Route

- `/settings`

### Canonical Subroutes

1. `/settings/profile`
2. `/settings/agency`
3. `/settings/people`
4. `/settings/assignments`
5. `/settings/ai-workforce`
6. `/settings/pipeline`
7. `/settings/integrations`
8. `/settings/audit`

### Route Responsibilities

| Route | Primary audience | Core responsibility | Persistence model |
|---|---|---|---|
| `/settings/profile` | all roles | personal preferences, operator defaults, communication signature, notification preferences | immediate save |
| `/settings/agency` | Owner, Admin | agency identity, operating hours, channels, business defaults | draft + publish |
| `/settings/people` | Owner, Admin | invites, activation, role assignment, delegation, ownership transfer | immediate action + audit |
| `/settings/assignments` | Owner, Admin; optional limited read for SeniorAgent | routing defaults, escalation defaults, claim policy, workload policy | draft + publish |
| `/settings/ai-workforce` | Owner, Admin | worker roster, stage scope, action mode, visibility scope, mutability hints | draft + publish |
| `/settings/pipeline` | Owner, Admin (Admin limited by owner envelope) | D1 autonomy matrix, mode overrides, review logic explanation | draft + publish |
| `/settings/integrations` | Owner, Admin (Admin limited) | external systems, API keys, webhook governance, sync posture | mixed: draft + publish for policy, explicit action for secrets |
| `/settings/audit` | Owner, Admin; limited read for SeniorAgent/JuniorAgent/Viewer where policy allows | audit history, filtering, event details, publish history | read only |

---

## Default Landing Behavior

### `/settings` Should Not Be A Dead Overview Page

The bare `/settings` route should resolve to the most relevant editable section for the current role.

### Role-Aware Default Route

| Role | Default landing |
|---|---|
| `Owner` | `/settings/agency` |
| `Admin` | `/settings/agency` |
| `SeniorAgent` | `/settings/profile` |
| `JuniorAgent` | `/settings/profile` |
| `Viewer` | `/settings/profile` |

Why this is correct:

- owners/admins usually enter settings to operate the workspace, not just edit their signature,
- agents/viewers usually need profile defaults first,
- and a role-aware redirect avoids an empty shell that forces every user through irrelevant sections.

---

## Settings Shell Contract

### Desktop Layout

The settings route should use a dedicated internal shell rather than the global app sidebar alone.

Required regions:

1. **Settings nav rail** — lists the eight subroutes with icons, labels, short descriptions, and permission state.
2. **Section header** — route title, purpose sentence, access badge, and draft/published status.
3. **Primary work area** — section-specific controls and explanatory content.
4. **Sticky change rail** — only appears for draftable sections and summarizes unsaved changes, last published time, and publish action.

### Mobile Layout

The settings nav rail collapses into a section picker at the top of the page.

Requirements:

- current section remains obvious,
- permission-restricted sections remain visible but marked read-only or unavailable,
- publish actions remain reachable without scrolling back to the top.

### Cross-Section UX Rules

1. Do not hide route existence just because a role cannot edit it; where appropriate, show the section with a clear access explanation.
2. Do not place agency-wide publish actions inside local personal settings.
3. Do not mix debug/pipeline fixture controls from workbench into `/settings`.
4. Do not force users through a generic overview dashboard before they can reach the real section they came for.

---

## Entry Points Into Settings

### Global Navigation

The main app shell should gain a real `Settings` destination under the governance grouping in [frontend/src/components/layouts/Shell.tsx](file:///Users/pranay/Projects/travel_agency_agent/frontend/src/components/layouts/Shell.tsx).

### Operator Avatar Menu

The top-right operator badge should eventually open profile-oriented quick links:

- `Profile`
- `Settings`
- `Notification preferences`

This is a convenience entry point, not the primary governance entry point.

### Contextual Deep Links

Operational surfaces should deep-link into the relevant settings section rather than sending users to generic settings root.

Examples:

- review screen explanation of governance threshold -> `/settings/pipeline`
- trip escalation explanation -> `/settings/assignments`
- AI worker rationale callout -> `/settings/ai-workforce`
- audit badge on publish action -> `/settings/audit`

---

## Subroute UX Contract

## 1. `/settings/profile`

Purpose:

- personal identity and working defaults only

Should contain:

- display name and avatar/initials
- role badge and current workspace context
- traveler-facing signature block
- communication style preset
- local workspace defaults such as density/theme/debug visibility where appropriate
- personal notification preferences

Behavior:

- immediate save is acceptable
- changes affect only the current operator
- no draft/publish bar

Important boundary:

- profile must not become a backdoor for agency-wide policy edits

## 2. `/settings/agency`

Purpose:

- agency identity and operational defaults

Should contain:

- agency name, logo, contact points, website
- operating hours and operating days
- preferred customer channels
- brand/tone defaults
- business defaults such as default currency and target margin posture where policy allows

Behavior:

- draft + publish
- change summary before publish
- audit link to last published change set

## 3. `/settings/people`

Purpose:

- human governance plane

Should contain:

- member roster
- invitation flow
- activation/deactivation controls
- canonical role assignment
- effective permission explanation
- ownership transfer flow
- owner/admin delegation explanation

Behavior:

- actions are immediate and individually audited
- destructive or authority-changing actions require explicit confirmation
- ownership transfer must be visually separated from ordinary role edits

## 4. `/settings/assignments`

Purpose:

- operational routing policy, not per-trip assignment execution

Should contain:

- explanation of routing slots: `primary_assignee`, `reviewer`, `escalation_owner`, `watchers`
- claim rules
- request-handoff policy
- reassignment policy
- escalation defaults
- review queue defaults
- ownership/review/handoff SLA policy explanation

Behavior:

- draft + publish
- every changed policy should preview its operational meaning in plain language
- route should explicitly reinforce that escalation preserves assignee by default

## 5. `/settings/ai-workforce`

Purpose:

- governed specialist AI workforce surface

Should contain:

- full worker roster, including planned/shadow/active/adaptive maturity
- worker purpose statement
- enabled/disabled state
- allowed stages
- action mode
- autonomy mode
- data visibility scope
- learning participation
- mutability hints showing what Admin can change vs Owner-only fields

Behavior:

- draft + publish
- clear warnings around `commercial_sensitive` visibility and high-risk autonomy
- UI should never make workers look like informal chatbot personalities

## 6. `/settings/pipeline`

Purpose:

- canonical D1 autonomy policy surface

Should contain:

- decision-state approval matrix
- mode overrides
- explanation of raw verdict vs effective action
- review threshold explanations
- learning toggle and rationale
- links from policy rows to affected review and escalation states

Behavior:

- draft + publish
- must enforce invariant messaging for `STOP_NEEDS_REVIEW`
- must retire the old threshold-only approvals mental model

Critical migration rule:

- do not ship `/settings/pipeline` while keeping a separate frontend concept of `approval thresholds` as a competing source of truth

## 7. `/settings/integrations`

Purpose:

- external connectivity governance

Should contain:

- provider roster
- connection state
- credential rotation metadata
- webhook destinations
- role limits for who can manage which connection
- sync direction and failure visibility

Behavior:

- policy changes may use draft + publish
- secret creation/rotation uses explicit immediate actions with confirmation and audit

## 8. `/settings/audit`

Purpose:

- authoritative audit viewing surface for settings, routing, AI, and override history

Should contain:

- timeline feed grouped by domain
- filters by subroute/domain/actor/trip/worker/date range
- detail drawer showing before/after change set
- publish history for draftable sections
- deep links back to affected settings section or workspace/trip

Behavior:

- read only
- must support redacted views for lower-permission roles

---

## State Model

Every draftable settings section must support these states:

1. **Loading** — show skeleton structure, not a blank page.
2. **Published / clean** — currently active policy with last published metadata.
3. **Dirty draft** — unsaved edits with field-level diff summary.
4. **Publishing** — explicit feedback and temporary action lock.
5. **Publish success** — timestamp, actor, and audit entry link.
6. **Publish conflict** — another actor changed the source policy; user can refresh, compare, or discard local draft.
7. **Read-only** — user can inspect but not change.
8. **Unauthorized** — route exists, but user is blocked from access and gets a clear explanation.

The non-draft sections also need:

- **Empty roster** for People,
- **No integrations configured** for Integrations,
- **No audit events yet** for Audit,
- **No AI worker active yet** for AI Workforce while still showing the planned roster.

---

## Role Visibility And Mutability

This route contract inherits the canonical route visibility matrix from `CANONICAL_ROLE_PERMISSION_MATRIX_2026-04-22.md`.

Additional UX rules:

1. visibility and editability are separate concepts,
2. route entry should explain read-only access rather than silently disabling everything,
3. Owner-only fields inside a shared Owner/Admin section must be visibly marked,
4. optional limited read states for `/settings/assignments` and `/settings/audit` should be additive, not substitutes for the main role matrix.

---

## Draft And Publish Rules

### Immediate-Save Sections

- `/settings/profile`
- most actions inside `/settings/people`
- credential rotation or connection actions inside `/settings/integrations`

### Draft-And-Publish Sections

- `/settings/agency`
- `/settings/assignments`
- `/settings/ai-workforce`
- `/settings/pipeline`
- policy-bearing integration defaults inside `/settings/integrations`

Why the split matters:

- profile changes should feel lightweight,
- policy changes should feel governed and attributable,
- and the publish moment becomes a natural audit boundary for agency-wide behavior.

---

## API Convergence Guidance

This UX contract does not define final backend endpoints in full detail, but it does define convergence rules.

### Rules

1. `GET /api/settings` may remain the aggregate loader for summary data.
2. `/settings/pipeline` must converge on the D1 autonomy contract, not legacy thresholds.
3. `frontend/src/lib/governance-api.ts` placeholders for `/api/settings/pipeline` and `/api/settings/approvals` must not survive as parallel long-term sources of truth.
4. Agency-wide settings should expose draft state and publish metadata once Phase 4 implementation begins.

### Recommended Resource Shape

- `GET /api/settings` -> summary + section availability + last-published metadata
- `GET /api/settings/profile`
- `GET /api/settings/agency`
- `GET /api/settings/people`
- `GET /api/settings/assignments`
- `GET /api/settings/ai-workforce`
- `GET /api/settings/pipeline`
- `GET /api/settings/integrations`
- `GET /api/settings/audit`

The exact endpoint plan may phase, but the route model should not.

---

## Relationship To Existing Workbench Settings

The existing [frontend/src/app/workbench/SettingsPanel.tsx](file:///Users/pranay/Projects/travel_agency_agent/frontend/src/app/workbench/SettingsPanel.tsx) remains useful for:

- scenario selection,
- leakage test posture,
- technical visibility during workbench analysis.

It should be relabeled and treated as:

- `Workbench settings`,
- `Pipeline debug settings`,
- or `Audit workbench settings`.

It should not be renamed or evolved into the canonical governance route.

---

## Implementation Implications

This contract means future implementation should proceed in this order:

1. add `/settings` route shell and role-aware nav entry,
2. wire role-aware route gating once identity/tenancy exists,
3. converge backend/frontend settings contracts around the subroute model,
4. retire the legacy approvals placeholder when `/settings/pipeline` becomes real,
5. add draft/publish and audit hooks for agency-wide policy surfaces.

---

## Non-Goals

This document does not define:

- the final visual design system for settings,
- the final auth/session architecture,
- the full backend persistence schema for settings drafts,
- the full audit payload taxonomy.

Those belong in sibling contracts.

---

## Acceptance Criteria

This UX contract is adopted when:

1. `/settings` exists as a real route family with the eight canonical subroutes,
2. the shell/nav model distinguishes profile from agency governance,
3. draftable governance sections use publish semantics while personal settings do not,
4. `/settings/pipeline` is clearly the D1 policy home and the placeholder approvals model is retired,
5. the workbench drawer is no longer treated as the future app settings destination.
