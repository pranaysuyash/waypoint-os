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

## Recommended sequencing (for owner ratification, no code in this doc)

1. Adopt `NEEDS_INFORMATION` rendering from `classify_missing_fields`
   (T-O2 machinery) — no new states needed; render blockers per stage.
2. Add `feasibility` as a real transition target before planning (decision
   layer already computes feasibility risks; promote to a state).
3. Add `change_requested` + `booking_exception` (component states) when
   booking work begins — mirrors taught model §7/§8.
4. Approval-recheck state when booking execution lands.

## Falsifier

If the owner ratifies the current coarse machine as sufficient for the
pilot (invite-only, operator-in-the-loop), the taught states remain
documentation-only and the reconciliation closes as "covered by operator
workflow instead of system states."
