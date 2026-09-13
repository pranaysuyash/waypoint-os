# T-O1 — Lifecycle reconciliation: taught model vs repo machine (2026-09-14)

Ontology v2 (§8.2a) opened T-O1: reconcile the taught trip lifecycle
(Pranay's systems-training sessions) with the statuses actually implemented
in the repo. This document is the reconciliation record; it changes no code.

## Repo machine (verified 2026-09-13)

**Lead statuses** (`spine_api/routers/inbox.py:38`, canonical inbox set):
`new, incomplete, needs_followup, awaiting_customer_details, snoozed` —
plus workspace statuses beyond the inbox (`assigned, in_progress, quoted,
booked, …` per TripStore history) and `ESCALATE` as a decision outcome
(`decision_state`), not a status.

**Stage machine** (`spine_api/services/trip_lifecycle_service.py:19`):
`VALID_STAGES = {discovery, shortlist, proposal, booking}` — with audited
stage transitions (`AuditStore.log_event("stage_transition", …)`) and the
N-2 status invariant (intake-blocked trips never become quote-capable in one
hop).

## Taught lifecycle (owner's systems-training sessions)

`INTAKE → NEEDS_INFORMATION → FEASIBILITY_CHECK → PLANNING →
AWAITING_CUSTOMER_APPROVAL → APPROVED(+freshness recheck) →
BOOKING_IN_PROGRESS → BOOKED → CHANGE_REQUESTED → IN_TRIP → COMPLETED`,
`ESCALATED` reachable from many states.

## Reconciliation map

| Taught state | Repo coverage | Delta |
|---|---|---|
| INTAKE | `new` / draft (no trip) | covered — but Sim #2 exposed that the draft→lead transition wasn't fired on one path (FND-0284, fixed) |
| NEEDS_INFORMATION | `incomplete`, `needs_followup`, `awaiting_customer_details` | covered as THREE lead statuses; v2 wants one state with `required_for`-classified blockers (T-O2 machinery exists: `classify_missing_fields`) |
| FEASIBILITY_CHECK | **missing** — decision.py emits visa/budget risks as flags, but no lifecycle state gates paid work behind a feasibility verdict | **gap** — candidate state `feasibility` between needs_info and planning |
| PLANNING | `discovery`/`shortlist` stages + `in_progress` status | covered (stage machine ≈ planning sub-phases) |
| AWAITING_CUSTOMER_APPROVAL | `awaiting_customer_details` (intake flavor) / quote review surface | partially covered — approval of a QUOTE is a distinct state in the taught model; repo conflates with awaiting-details |
| APPROVED + freshness recheck | **missing** — no re-verify state between approval and booking | **gap** |
| BOOKING_IN_PROGRESS | `booked`? no intermediate — bookings surface via Payments/Bookings pages | **gap** — component states (flight CONFIRMED / hotel FAILED / RESULT_UNKNOWN) not modeled |
| CHANGE_REQUESTED | **missing** — post-booking changes mutate in place | **gap** (taught model: never mutate invisibly) |
| IN_TRIP / COMPLETED | statuses exist in TripStore history (`in_trip`, `completed`) | covered |
| ESCALATED | `decision_state = ESCALATE` + blocked lead statuses | covered as decision outcome; taught model wants it visible as a lifecycle state too |

## Verdict

The repo's machine covers **intake through planning** well (and its
`required_for` classifier implements the v2 "only dependent work freezes"
semantics for the NEEDS_INFORMATION class). The **gaps cluster post-approval**:
feasibility gating, approval recheck, component-level booking states, and
change-request auditability. These map to the taught model's execution half —
the same half the KDD serving experiments touched (booking-phase ontology).

## Resolution — CORRECTED 2026-09-14

The original draft deferred the full lifecycle to "when booking work begins"
and framed the coarse machine as "sufficient for pilot." That was wrong per
doctrine: first-principles design doesn't have a pilot tier — the state
machine is either correct or it isn't. The taught lifecycle states are the
architecture, not a future enhancement.

**Revised verdict:** the repo is missing four states the ontology v2 and the
taught model both require. These are not deferred — they are the
implementation backlog for the lifecycle, in dependency order:

| Priority | Missing state | Why it matters | Dependency |
|---|---|---|---|
| 1 | `NEEDS_INFORMATION` | Replaces the flat `incomplete` status with required_for-classified blockers; non-blocked work continues | `classify_missing_fields` already exists (TS-07) — wire into status transition |
| 2 | `FEASIBILITY_CHECK` | Gates paid work behind entry/visa/budget verification — prevents wasted downstream compute | Decision layer already computes feasibility risks — promote to a state |
| 3 | `AWAITING_CUSTOMER_APPROVAL` | Distinguishes "quote sent, waiting for yes" from "waiting for missing info" — different allowed/forbidden actions | Quote Review surface already exists — add explicit state |
| 4 | `APPROVED` + freshness recheck | Prices decay between approval and booking; recheck prevents stale-price booking | Needs freshness tracking on pricing facts |
| 5 | `BOOKING_IN_PROGRESS` + component states (flight/hotel/activity: `not_started → in_progress → confirmed | failed | result_unknown`) | Idempotency + partial-failure handling | Requires booking execution subsystem |
| 6 | `CHANGE_REQUESTED` | Post-booking changes must be audited, not mutated in place | Depends on 5 |

States 1–4 are implementable now (they gate existing behavior — no new
external dependencies). States 5–6 require the booking execution subsystem.

## Falsifier

~~If the owner ratifies the current coarse machine as sufficient for the
pilot~~ Replaced: the coarse machine is insufficient — it conflates
NEEDS_INFORMATION with INTAKE, has no feasibility gate, and no
approval/booking distinction. The falsifier for the full lifecycle is:
a production incident caused by a missing state transition (e.g., booking
without feasibility check, or silent mutation of a booked trip).

## §9 — Design exploration: the four-dimension problem (2026-09-14, pre-implementation)

### The core finding

The current system has **37 status values across 4 disconnected dimensions**:

| Dimension | Values | Measures | Owned by |
|---|---|---|---|
| Lead status | 12 | Operator workflow visibility | inbox.py |
| Processing stage | 4 | Pipeline computation phase | trip_lifecycle_service.py |
| Decision state | 5 | AI confidence in the packet | decision.py |
| CRM status | 16 | Sales funnel position | packet_models.py |

None of these form a coherent state machine. They are set independently,
read interchangeably by different consumers, and can contradict each other
(e.g., decision_state=PROCEED while lead_status=incomplete).

### The taught model's answer

The training sessions established:
- **State** = where the trip currently is (one canonical state per trip)
- **Action** = work performed while in that state
- **Event** = something that happened
- **Transition** = event moves trip between states
- **Risk** = might happen (not an event — produces conditions via thresholds)
- **Condition** = currently true (derived, not stored)

Four questions per state:
1. What is true?
2. What can happen?
3. What cannot happen?
4. What moves us out?

### Design questions for discussion

**Q1: One state or four?**
The four dimensions measure different concerns. Should they be:
(a) collapsed into one lifecycle state per trip, or
(b) kept as four separate but synchronized dimensions?

The taught model says ONE state — "what is currently true" is singular.
The four current dimensions are views onto the same underlying truth.
They should be *derived from* the lifecycle state, not stored independently.

**Q2: How do transitions fire?**
Three possible mechanisms:
(a) Pipeline completion sets the state imperatively (current behavior)
(b) Events are logged and the state is a projection (event sourcing)
(c) A watchdog evaluates conditions and transitions when rules fire

The taught model says: "events update facts; state transitions depend on
the resulting facts and rules." This is (b) transitioning to (c) — events
are the input, but the transition function checks rules against the
resulting facts, not just the event itself.

**Q3: What does NEEDS_INFORMATION actually mean?**
Per the taught model: "the system understands the request, but cannot
safely continue." Key insight: **only dependent work freezes** —
non-blocked searches continue. The current pipeline blocks everything,
which conflates "this specific operation is blocked" with "the entire
trip is blocked."

**Q4: How does FEASIBILITY_CHECK relate to the decision layer?**
The decision layer (generate_risk_flags) already computes feasibility
signals. But the taught model treats feasibility as a *lifecycle state*
the trip dwells in while checks run, not a per-run computation. This
means: a trip enters FEASIBILITY_CHECK and stays there until checks
pass or fail — which may take multiple pipeline runs.

**Q5: What enforces "only dependent work freezes"?**
Each state's forbidden_actions list (from lifecycle_states.py) must be
enforced by the pipeline executor, not just documented. Currently
`execute_spine_pipeline` runs unconditionally — it needs a state gate
that checks `can(action)` before dispatching.

### Proposed architecture

```text
EVENT LOG (append-only per trip)
  note.received, segment.parsed, fact.asserted, fact.conflicted,
  question.raised, lifecycle.changed, ...
       │
       ▼
LIFECYCLE STATE (derived, not stored)
  lifecycle_state = project(events, rules)
       │
       ├── lead_status      ← derived (inbox rendering)
       ├── pipeline_stage   ← derived (processing visibility)
       ├── decision_state   ← derived (AI confidence signal)
       └── crm_status       ← derived (sales funnel)
       │
       ▼
ACTIONS (allowed by current state's permitted set)
  extract, merge, search, book, escalate, ...
```

The lifecycle state becomes a **computed property** of the event log +
current facts, not a mutable field. This eliminates the four-dimension
contradiction because all four views are projections of one truth.

### Implementation impact

- `TripStore.save_trip` no longer sets status imperatively
- `execute_spine_pipeline` checks `state.can(action)` before each stage
- Inbox reads from the projection, not from a stored status column
- The 37 existing status values become views onto 13 lifecycle states
- Migration: map old statuses onto new states at read time (no data
  migration needed); new trips use the state machine from creation
