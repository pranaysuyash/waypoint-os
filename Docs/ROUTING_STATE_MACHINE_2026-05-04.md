# Assignment Routing State Machine — Implementation Notes (2026-05-04)

**Task**: Phase 4 backend — trip assignment routing state machine
**Status**: Shipped — 18 new tests, 48 total passing (no regressions)

---

## What Was Built

### Files Created

| File | Purpose |
|------|---------|
| `spine_api/models/routing.py` | `TripRoutingState` SQLAlchemy model |
| `spine_api/services/routing_service.py` | State machine transitions (6 actions) |
| `spine_api/services/sla_service.py` | SLA deadline classification |
| `spine_api/routers/assignments.py` | REST API (7 endpoints) |
| `tests/test_routing_state_machine.py` | 18 tests: 12 state machine + 6 SLA |

**Modified**: `spine_api/server.py` — registered `assignments_router`

---

## State Machine

```
unassigned
  ↓ assign(assignee_id, by=admin)    [admin assigns to specific agent]
  ↓ claim(by=senior_agent)           [self-assign by senior+]
assigned
  ↓ escalate(escalation_owner_id)    [primary_assignee preserved; escalation_owner added]
escalated
  ↓ reassign(new_assignee_id)        [any non-unassigned state; clears escalation_owner]
  ↓ return_for_changes(reason)       [reviewer sends back; clears escalation_owner]
returned
  ↓ escalate(...)                    [can re-escalate a returned trip]
  ↓ unassign(reason)                 [admin reset from any state]
```

**Key invariant**: `primary_assignee_id` is NEVER cleared by escalation. Escalation adds `escalation_owner_id` alongside the primary assignee. Only `reassign` and `unassign` can change `primary_assignee_id`.

**handoff_history**: Every transition appends an entry: `{action, by_user_id, to_user_id?, from_user_id?, reason?, at}`. This is append-only — no entry is ever removed.

---

## API Endpoints

All routes are under `/api/assignments/{trip_id}`. Auth: JWT required (router-level `Depends(get_current_user)`). `agency_id` always comes from `get_current_membership`, never from the request body.

| Method | Path | Body fields |
|--------|------|-------------|
| GET    | `/{trip_id}` | — |
| POST   | `/{trip_id}/assign` | `assignee_id` |
| POST   | `/{trip_id}/claim` | — |
| POST   | `/{trip_id}/escalate` | `escalation_owner_id`, `reason?` |
| POST   | `/{trip_id}/reassign` | `new_assignee_id`, `reason?` |
| POST   | `/{trip_id}/return` | `reason?` |
| POST   | `/{trip_id}/unassign` | `reason?` |

All mutation endpoints return `{"ok": true, "routing_state": {...}, "sla": {...}}`.

GET returns a virtual unassigned state if no routing record exists yet (trip exists but was never assigned — no DB error, clean UI default).

---

## SLA Thresholds

| SLA type | Warn | Breach |
|----------|------|--------|
| Ownership (since assigned_at) | 4 hrs | 24 hrs |
| Escalation (since escalated_at) | 2 hrs | 8 hrs |

Thresholds are parameters to `compute_sla()` — agency settings can override them in future.
`worst` field summarizes the highest-severity of both SLAs: `not_started | on_track | at_risk | breached`.

---

## Integration with Existing System

The existing `persistence.AssignmentStore` (JSON-file based) is **not replaced** — it is additive. The new `TripRoutingState` SQLAlchemy model lives alongside it. Both systems co-exist:
- Old: `AssignmentStore` tracks `assigned_to` / `assigned_to_name` for inbox projection
- New: `TripRoutingState` tracks full routing state with history, escalation, SLA

A future migration task should deprecate `AssignmentStore` by:
1. Making `InboxProjectionService` read `assigned_to` from `TripRoutingState.primary_assignee_id`
2. Removing JSON-file reads from inbox queries
3. Deleting `AssignmentStore`

That is out of scope for this task (no regressions allowed).

---

## What's Still Missing

- Role gate on claim (should require senior_agent+; currently any authenticated user can claim)
- Frontend components: `AssignmentPanel`, `ClaimButton`, `EscalateButton`, `SLAIndicator` (Phase 4 frontend — separate task)
- Route-map entries for `/api/assignments/{id}/*` endpoints (needed when frontend consumes these)
- Review queue endpoint (`GET /api/review-queue`) — not included here, separate router

---

## Testing Note

SQLAlchemy ORM instances cannot be constructed via `__new__()` without going through the mapper — doing so causes `AttributeError: 'NoneType' object has no attribute 'set'` when setting columns. Use `MagicMock()` with explicit attribute assignment instead (same pattern as `test_agent_join_flow.py`). This is documented here so future agents don't rediscover it.
