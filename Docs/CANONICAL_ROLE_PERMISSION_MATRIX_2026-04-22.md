# Canonical Role & Permission Matrix

**Date**: 2026-04-22
**Status**: Canonical design contract
**Scope**: Human roles, bootstrap ownership, delegated administration, route visibility, and permission enforcement for workspace governance.
**Parent roadmap**: `WORKSPACE_GOVERNANCE_ROADMAP_LIVING_2026-04-22.md`

---

## Executive Summary

This document resolves the repo's current role vocabulary drift into one canonical human governance model.

### Canonical Roles

1. `Owner`
2. `Admin`
3. `SeniorAgent`
4. `JuniorAgent`
5. `Viewer`

### Locked Decisions

1. The **workspace creator** is bootstrapped as both `Owner` and `Admin`.
2. `Owner` and `Admin` remain distinct capabilities even if initially held by the same person.
3. Predefined roles are the canonical model for the production architecture.
4. Custom per-user permission edits are additive later, not a replacement for the canonical role catalog.

---

## Why This Exists

Current role vocabularies in the repo conflict:

- `owner | manager | agent | viewer`
- `owner | agent | junior`
- `owner | senior | junior`

That makes it impossible to build coherent settings, routing, audit, or AI governance.

This document defines the one vocabulary that future UI, API, persistence, and docs must use.

---

## Bootstrap Model

### Workspace Creator

When a workspace is created:

- the creating user becomes `workspace_owner_id`
- the creating user gets `Owner` capability
- the creating user gets `Admin` capability
- the creating user becomes default `escalation_owner`

This is the bootstrap rule. It avoids ambiguity about who can configure the system initially.

### Why Owner And Admin Are Both Real Concepts

Even though the creator starts as both, they are not the same concept forever.

**Owner** is the business/governance authority.

**Admin** is the delegated operational administrator.

This allows the system to support future situations like:

- founder remains owner, ops lead becomes admin
- owner delegates team/assignment/AI operations without giving away billing or hard policy control

---

## Legacy Mapping

| Legacy Term | Canonical Role |
|---|---|
| `owner` | `Owner` |
| `manager` | `Admin` |
| `agent` | `SeniorAgent` |
| `senior` | `SeniorAgent` |
| `junior` | `JuniorAgent` |
| `viewer` | `Viewer` |

Rules:

- New code and docs should use only canonical names.
- Migration adapters may map legacy names for backward compatibility during transition.
- No new design artifact should introduce a sixth human role unless this matrix is updated first.

---

## Role Semantics

### Owner

Business and governance authority.

Responsibilities:

- final authority on commercial and safety policy
- billing and subscription control
- ownership transfer authority
- final approval on hard governance decisions
- approval of AI policy changes that affect business risk

### Admin

Delegated workspace administrator.

Responsibilities:

- day-to-day workspace management
- team membership administration
- assignment and workload control
- AI worker operations within the owner-defined envelope
- settings administration for non-destructive operational areas

### SeniorAgent

Primary operator role.

Responsibilities:

- claim and work trips
- operate assigned workspaces
- request handoff
- participate in reviews within configured thresholds
- work with AI suggestions and drafts

### JuniorAgent

Guided operator role.

Responsibilities:

- operate assigned trips with stronger review boundaries
- request help, escalate, or hand off
- cannot finalize actions above configured governance thresholds

### Viewer

Read-only visibility role.

Responsibilities:

- read dashboards and workspace information allowed by policy
- cannot change settings, routing, approvals, or AI behavior

---

## Permission Domains

The permission model should be grouped by domain rather than by screen-specific toggles.

### Domains

1. `workspace`
2. `review`
3. `people`
4. `assignments`
5. `settings_profile`
6. `settings_agency`
7. `settings_pipeline`
8. `settings_ai_workforce`
9. `integrations`
10. `audit`
11. `billing`
12. `ownership`

---

## Permission Matrix

Legend:

- `full` = unrestricted within tenant/workspace scope
- `limited` = allowed with scope limits or thresholds
- `read` = view only
- `none` = not allowed

| Capability | Owner | Admin | SeniorAgent | JuniorAgent | Viewer |
|---|---|---|---|---|---|
| View workspace list and trip workspaces | full | full | full | limited | read |
| Claim unassigned trip | full | full | full | limited | none |
| Operate assigned trip | full | full | full | limited | none |
| Operate any trip regardless of assignment | full | full | limited | none | none |
| Request handoff | full | full | full | full | none |
| Reassign trip | full | full | none | none | none |
| Add/remove reviewer or escalation owner | full | full | none | none | none |
| Approve standard review items | full | full | limited | none | none |
| Approve high-risk / hard governance items | full | none | none | none | none |
| Invite/deactivate members | full | full | none | none | none |
| Change user role | full | full | none | none | none |
| Edit own profile/preferences | full | full | full | full | limited |
| Edit agency profile/hours/channels | full | full | none | none | none |
| Edit hard commercial thresholds | full | none | none | none | none |
| Edit autonomy policy matrix | full | limited | none | none | none |
| Edit AI worker operational settings | full | full | none | none | none |
| Grant commercial-sensitive AI access | full | none | none | none | none |
| Manage integrations/webhooks/API keys | full | limited | none | none | none |
| View audit logs | full | full | limited | limited | read |
| Manage billing/subscription | full | none | none | none | none |
| Transfer ownership | full | none | none | none | none |

---

## Notes On Limited Permissions

### SeniorAgent Limited Scope

`SeniorAgent` may have limited approval ability, but only within owner/admin-configured thresholds.

Examples:

- approve low-risk follow-up drafts
- approve normal-value internal draft steps
- cannot approve hard stops or high-risk escalations

### JuniorAgent Limited Scope

`JuniorAgent` may:

- claim from explicitly allowed queues
- work assigned trips
- draft but not finalize sensitive actions
- escalate or request handoff

### Viewer Limited Scope

`Viewer` visibility may still be filtered by data-sensitivity policy.

For example:

- may read operational dashboards
- may not see commercial-sensitive margin fields
- may not see AI internal-only rationale where policy forbids it

---

## Route Visibility Matrix

| Route | Owner | Admin | SeniorAgent | JuniorAgent | Viewer |
|---|---|---|---|---|---|
| `/settings/profile` | yes | yes | yes | yes | yes |
| `/settings/agency` | yes | yes | no | no | no |
| `/settings/people` | yes | yes | no | no | no |
| `/settings/assignments` | yes | yes | read-only optional | no | no |
| `/settings/ai-workforce` | yes | yes | no | no | no |
| `/settings/pipeline` | yes | limited | no | no | no |
| `/settings/integrations` | yes | limited | no | no | no |
| `/settings/audit` | yes | yes | limited | limited | read-only optional |
| `/owner/reviews` | yes | yes | limited by threshold | no | no |
| `/owner/insights` | yes | yes | limited/own scope optional | limited/own scope optional | read-only optional |

---

## Ownership Transfer Rules

Ownership transfer is a special action and must not be modeled as ordinary role editing.

Rules:

1. Only current `Owner` can initiate ownership transfer.
2. Target user must already be a valid member of the workspace/agency.
3. Transfer emits a dedicated audit event.
4. Previous owner may optionally retain `Admin` after transfer, but that is explicit.

---

## AI Workforce Governance Authority Split

This matrix is specifically important because AI governance is not ordinary settings.

### Owner-only AI authorities

- grant commercial-sensitive worker visibility
- set hard autonomy envelope for risky states
- enable learning that can propose policy changes
- approve high-risk worker behavior changes

### Admin AI authorities

- enable/disable workers within approved envelope
- set stage scope
- set operational action mode
- set routing defaults and notification behavior

### Agent AI interaction rights

`SeniorAgent` and `JuniorAgent` do not govern workforce policy globally.

They may still:

- use AI within allowed workspace flow
- override drafts where policy allows
- generate feedback signals that feed learning loops

---

## Audit Requirements

At minimum, the system should emit distinct audit events for:

- user invited
- user removed
- role changed
- owner transferred
- assignment reassigned
- escalation created
- reviewer added/removed
- settings changed
- AI worker policy changed
- autonomy policy changed

This goes beyond the current lightweight audit type set and should become the basis for the future audit taxonomy.

---

## Enforcement Strategy

### UI Layer

- hide or disable actions the current user cannot take
- explain why an action is unavailable when appropriate

### API Layer

- treat API authorization as canonical
- never rely on UI hiding alone

### Persistence Layer

- role and membership changes must be auditable
- ownership transfer should be transactionally safe

---

## Non-Goals

This document does not define:

- assignment state machine details
- AI worker registry schema
- settings page UX layout
- audit event payload schema in full detail

Those are handled by sibling specs.

---

## Acceptance Criteria

This matrix is considered adopted when:

1. frontend types use canonical role names
2. backend auth/membership layer uses canonical role names
3. settings and governance routes enforce this matrix
4. no active planning doc uses the older competing role catalogs without an explicit legacy note
