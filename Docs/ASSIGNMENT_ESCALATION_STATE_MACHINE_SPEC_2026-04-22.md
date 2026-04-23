# Assignment & Escalation State Machine Spec

**Date**: 2026-04-22
**Status**: Canonical design contract
**Scope**: Operational routing model for assignment, escalation, review, handoff, and reassignment.
**Parent roadmap**: `WORKSPACE_GOVERNANCE_ROADMAP_LIVING_2026-04-22.md`

---

## Executive Summary

Assignment and escalation should not be modeled as a single mutable `assigned_to` field.

The correct model has:

1. explicit routing slots,
2. explicit routing actions,
3. explicit audit history,
4. explicit SLA clocks,
5. escalation that preserves ownership by default.

### Locked Decisions

1. Escalation preserves `primary_assignee` unless a separate reassignment action occurs.
2. Reassignment is an explicit transition, never the default meaning of escalation.
3. `Request Changes` returns work to the current primary assignee unless a reviewer explicitly chooses a different routing action.
4. Routing state should be modeled separately from the trip's business stage.

---

## Why This Exists

The repo currently has:

- frontend assignment and reassignment request shapes,
- a file-backed assignment store,
- analytics/review flows that assume assigned ownership,
- and no canonical operational state machine.

Without a state machine, escalation, reassignment, review, and workload become inconsistent across screens and services.

---

## Canonical Routing Record

Each trip/workspace should have a routing record distinct from its trip content.

```ts
type RoutingRecord = {
  tripId: string
  primaryAssigneeId: string | null
  reviewerId: string | null
  escalationOwnerId: string | null
  watcherIds: string[]
  handoffRequestId: string | null
  ownershipState: OwnershipState
  governanceState: GovernanceState
  ownershipSlaStartedAt: string | null
  reviewSlaStartedAt: string | null
  handoffSlaStartedAt: string | null
  updatedAt: string
}
```

---

## Routing Slots

### 1. Primary Assignee

The human currently responsible for driving the trip forward.

### 2. Reviewer

The human expected to review or approve the next governed action.

### 3. Escalation Owner

The human responsible for oversight when the trip is escalated.

### 4. Watchers

Humans who should see updates but are not routing owners.

### 5. Handoff Request

An explicit pending request that asks for ownership transfer without changing ownership yet.

---

## Two-Axis State Model

Routing should be represented on two axes.

### Axis A: OwnershipState

1. `unassigned`
2. `assigned`
3. `handoff_requested`
4. `reassignment_pending`
5. `closed`

### Axis B: GovernanceState

1. `normal`
2. `review_required`
3. `escalated`
4. `blocked_pending_owner`
5. `returned_for_changes`

These axes intentionally separate:

- who owns the work,
- from what level of governance is currently active.

---

## Allowed Actions

Canonical routing actions:

1. `assign`
2. `claim`
3. `unassign`
4. `request_handoff`
5. `cancel_handoff_request`
6. `reassign`
7. `add_reviewer`
8. `remove_reviewer`
9. `escalate`
10. `deescalate`
11. `return_for_changes`
12. `approve_review`
13. `reject_review`
14. `watch`
15. `unwatch`

---

## Transition Rules

### Assign

**Preconditions**:

- actor is `Owner` or `Admin`
- target user is valid member

**Effects**:

- `primaryAssigneeId = target`
- `ownershipState = assigned`
- start or reset ownership SLA according to policy

### Claim

**Preconditions**:

- trip is `unassigned`
- actor is allowed to claim from that queue

**Effects**:

- actor becomes `primaryAssigneeId`
- `ownershipState = assigned`

### Request Handoff

**Preconditions**:

- actor is current assignee or authorized reviewer/admin

**Effects**:

- `ownershipState = handoff_requested`
- handoff request record created
- primary assignee remains unchanged until approved
- start handoff SLA

### Reassign

**Preconditions**:

- actor is `Owner` or `Admin`, or other explicitly authorized role

**Effects**:

- `primaryAssigneeId = target`
- `ownershipState = assigned`
- handoff request cleared if present
- reassignment event appended to history

### Escalate

**Preconditions**:

- governance condition triggered or human action initiated

**Effects**:

- `governanceState = escalated` or `blocked_pending_owner` depending on policy
- `primaryAssigneeId` unchanged
- `reviewerId` and/or `escalationOwnerId` populated
- start review SLA if review is required

### Return For Changes

**Preconditions**:

- review exists

**Effects**:

- `governanceState = returned_for_changes`
- `primaryAssigneeId` unchanged by default
- review notes attached

### Approve Review

**Effects**:

- governance state moves back toward `normal`
- review SLA stops
- assignee continuity preserved

---

## Core Invariant

### Escalation Does Not Imply Reassignment

This is the most important invariant in the state machine.

When a trip is escalated:

- the current operator keeps ownership,
- governance overlays are added,
- reassignment becomes available as a separate action.

This preserves context continuity and prevents blind churn.

---

## State Transition Table

| Current OwnershipState | Current GovernanceState | Action | Result |
|---|---|---|---|
| `unassigned` | `normal` | `assign` | `assigned + normal` |
| `unassigned` | `normal` | `claim` | `assigned + normal` |
| `assigned` | `normal` | `request_handoff` | `handoff_requested + normal` |
| `assigned` | `normal` | `escalate` | `assigned + escalated` |
| `assigned` | `review_required` | `return_for_changes` | `assigned + returned_for_changes` |
| `handoff_requested` | `normal` | `reassign` | `assigned + normal` |
| `assigned` | `escalated` | `reassign` | `assigned + escalated` with new assignee |
| `assigned` | `escalated` | `approve_review` | `assigned + normal` or `review_required` resolved |
| `assigned` | `returned_for_changes` | assignee addresses changes | `assigned + review_required` or `normal` |

---

## SLA Model

The routing engine should support three parallel SLA clocks.

### 1. Ownership SLA

Tracks how long the current primary assignee has had the work.

### 2. Review SLA

Tracks how long a review or escalation approval is pending.

### 3. Handoff SLA

Tracks how long a request-handoff or pending reassignment remains unresolved.

### Why Three Clocks

If escalation happens on a single-SLA system, accountability becomes muddy.

Splitting clocks allows the system to answer:

- Is the operator stalled?
- Is the reviewer the bottleneck?
- Is handoff administration delayed?

---

## Audit Event Requirements

At minimum, the routing engine must emit:

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
- `returned_for_changes`
- `review_approved`
- `review_rejected`

Each event should include:

- actor id
- previous slot values
- next slot values
- reason
- timestamp
- trip/workspace id

---

## UI Implications

### Inbox / Queue Views

Should display:

- primary assignee
- escalated status
- reviewer if present
- ownership SLA
- review SLA if active

### Workspace Header

Should display:

- primary assignee
- escalation badge
- reviewer badge
- handoff pending badge

### Review Screens

Should support:

- approve without ownership change
- return for changes to current assignee
- explicit “reassign while escalating” flow when desired

---

## Persistence Guidance

Current file-backed assignment storage is acceptable as a temporary infrastructure layer, but the data model should already reflect the future contract.

That means even if persistence starts simple, the shape should not be limited to:

- one `assigned_to`
- one `assigned_to_name`

The routing record contract should be future-safe from the start.

---

## Non-Goals

This document does not define:

- human role permissions in full detail
- AI worker registry structure
- autonomy policy matrix editing rules

Those belong in sibling contracts.

---

## Acceptance Criteria

This state machine is adopted when:

1. routing state is represented separately from trip business stage
2. escalation preserves assignee by default in both UI and API
3. explicit reassignment exists as a separate action
4. SLA reporting distinguishes ownership, review, and handoff bottlenecks
5. audit events can reconstruct routing history end-to-end
