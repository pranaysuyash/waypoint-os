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
