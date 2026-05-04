"""
Routing service — state machine transitions for trip assignment.

All mutations go through this service. Each transition:
1. Validates the current state allows the requested action.
2. Updates the TripRoutingState row.
3. Appends a handoff_history entry.
4. Returns the updated state dict (caller logs audit event).

The service is stateless — it reads from and writes to the DB session.
It does NOT emit audit events directly; that is the router's responsibility.

State transitions:
  assign(trip, assignee)     unassigned → assigned
  claim(trip, claimer)       unassigned → assigned  (self-assign by senior agent)
  escalate(trip, escalator)  assigned   → escalated (escalation_owner set; primary preserved)
  reassign(trip, new_owner)  any        → assigned  (new primary_assignee; handoff logged)
  return_for_changes(trip)   escalated  → returned  (reviewer sends back; becomes assigned state)
  unassign(trip)             any        → unassigned (admin reset)
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from spine_api.models.routing import TripRoutingState, ROUTING_STATUSES


class RoutingError(ValueError):
    """Raised when a state transition is invalid."""


async def get_or_create_routing_state(
    db: AsyncSession,
    trip_id: str,
    agency_id: str,
) -> TripRoutingState:
    """Fetch the routing state for a trip, creating a new unassigned record if absent."""
    result = await db.execute(
        select(TripRoutingState).where(TripRoutingState.trip_id == trip_id)
    )
    state = result.scalar_one_or_none()
    if state is None:
        state = TripRoutingState(
            trip_id=trip_id,
            agency_id=agency_id,
            status="unassigned",
            handoff_history=[],
        )
        db.add(state)
        await db.flush()
    return state


def _append_history(
    state: TripRoutingState,
    action: str,
    by_user_id: str,
    from_user_id: Optional[str] = None,
    to_user_id: Optional[str] = None,
    reason: Optional[str] = None,
) -> None:
    entry = {
        "action": action,
        "by_user_id": by_user_id,
        "at": datetime.now(timezone.utc).isoformat(),
    }
    if from_user_id:
        entry["from_user_id"] = from_user_id
    if to_user_id:
        entry["to_user_id"] = to_user_id
    if reason:
        entry["reason"] = reason

    state.handoff_history = (state.handoff_history or []) + [entry]


def _to_dict(state: TripRoutingState) -> dict:
    return {
        "id": state.id,
        "trip_id": state.trip_id,
        "agency_id": state.agency_id,
        "status": state.status,
        "primary_assignee_id": state.primary_assignee_id,
        "reviewer_id": state.reviewer_id,
        "escalation_owner_id": state.escalation_owner_id,
        "assigned_at": state.assigned_at.isoformat() if state.assigned_at else None,
        "escalated_at": state.escalated_at.isoformat() if state.escalated_at else None,
        "handoff_history": state.handoff_history,
        "created_at": state.created_at.isoformat() if state.created_at else None,
        "updated_at": state.updated_at.isoformat() if state.updated_at else None,
    }


async def assign_trip(
    db: AsyncSession,
    trip_id: str,
    agency_id: str,
    assignee_id: str,
    assigned_by: str,
) -> dict:
    """Admin assigns a trip to an agent. Trip must be unassigned."""
    state = await get_or_create_routing_state(db, trip_id, agency_id)

    if state.status != "unassigned":
        raise RoutingError(
            f"Cannot assign trip '{trip_id}': current status is '{state.status}'. "
            "Use reassign to change an existing assignee."
        )

    now = datetime.now(timezone.utc)
    state.primary_assignee_id = assignee_id
    state.status = "assigned"
    state.assigned_at = now
    state.updated_at = now
    _append_history(state, "assign", by_user_id=assigned_by, to_user_id=assignee_id)

    await db.commit()
    await db.refresh(state)
    return _to_dict(state)


async def claim_trip(
    db: AsyncSession,
    trip_id: str,
    agency_id: str,
    claimer_id: str,
) -> dict:
    """Senior agent self-assigns an unassigned trip."""
    state = await get_or_create_routing_state(db, trip_id, agency_id)

    if state.status != "unassigned":
        raise RoutingError(
            f"Cannot claim trip '{trip_id}': already '{state.status}'."
        )

    now = datetime.now(timezone.utc)
    state.primary_assignee_id = claimer_id
    state.status = "assigned"
    state.assigned_at = now
    state.updated_at = now
    _append_history(state, "claim", by_user_id=claimer_id, to_user_id=claimer_id)

    await db.commit()
    await db.refresh(state)
    return _to_dict(state)


async def escalate_trip(
    db: AsyncSession,
    trip_id: str,
    agency_id: str,
    escalation_owner_id: str,
    escalated_by: str,
    reason: Optional[str] = None,
) -> dict:
    """Escalate an assigned trip. primary_assignee is preserved; escalation_owner is added."""
    state = await get_or_create_routing_state(db, trip_id, agency_id)

    if state.status not in {"assigned", "returned"}:
        raise RoutingError(
            f"Cannot escalate trip '{trip_id}': status is '{state.status}'. "
            "Only assigned or returned trips can be escalated."
        )

    now = datetime.now(timezone.utc)
    prev_escalation_owner = state.escalation_owner_id
    state.escalation_owner_id = escalation_owner_id
    state.status = "escalated"
    state.escalated_at = now
    state.updated_at = now
    _append_history(
        state,
        "escalate",
        by_user_id=escalated_by,
        from_user_id=prev_escalation_owner,
        to_user_id=escalation_owner_id,
        reason=reason,
    )

    await db.commit()
    await db.refresh(state)
    return _to_dict(state)


async def reassign_trip(
    db: AsyncSession,
    trip_id: str,
    agency_id: str,
    new_assignee_id: str,
    reassigned_by: str,
    reason: Optional[str] = None,
) -> dict:
    """
    Reassign a trip to a new primary owner. Valid from any non-unassigned state.
    Clears escalation_owner; resets status to 'assigned'.
    Previous assignee and reason are recorded in handoff_history.
    """
    state = await get_or_create_routing_state(db, trip_id, agency_id)

    if state.status == "unassigned":
        raise RoutingError(
            f"Cannot reassign trip '{trip_id}': not yet assigned. Use assign instead."
        )

    now = datetime.now(timezone.utc)
    prev_assignee = state.primary_assignee_id
    state.primary_assignee_id = new_assignee_id
    state.escalation_owner_id = None
    state.escalated_at = None
    state.status = "assigned"
    state.updated_at = now
    _append_history(
        state,
        "reassign",
        by_user_id=reassigned_by,
        from_user_id=prev_assignee,
        to_user_id=new_assignee_id,
        reason=reason,
    )

    await db.commit()
    await db.refresh(state)
    return _to_dict(state)


async def return_for_changes(
    db: AsyncSession,
    trip_id: str,
    agency_id: str,
    returned_by: str,
    reason: Optional[str] = None,
) -> dict:
    """
    Reviewer returns a trip for changes.
    Sets status to 'returned' (primary_assignee remains responsible).
    Clears escalation_owner.
    """
    state = await get_or_create_routing_state(db, trip_id, agency_id)

    if state.status not in {"assigned", "escalated"}:
        raise RoutingError(
            f"Cannot return trip '{trip_id}': status is '{state.status}'."
        )

    now = datetime.now(timezone.utc)
    state.status = "returned"
    state.escalation_owner_id = None
    state.escalated_at = None
    state.updated_at = now
    _append_history(
        state,
        "return_for_changes",
        by_user_id=returned_by,
        reason=reason,
    )

    await db.commit()
    await db.refresh(state)
    return _to_dict(state)


async def unassign_trip(
    db: AsyncSession,
    trip_id: str,
    agency_id: str,
    unassigned_by: str,
    reason: Optional[str] = None,
) -> dict:
    """Admin reset: return trip to unassigned pool."""
    state = await get_or_create_routing_state(db, trip_id, agency_id)

    now = datetime.now(timezone.utc)
    prev_assignee = state.primary_assignee_id
    state.primary_assignee_id = None
    state.reviewer_id = None
    state.escalation_owner_id = None
    state.escalated_at = None
    state.status = "unassigned"
    state.updated_at = now
    _append_history(
        state,
        "unassign",
        by_user_id=unassigned_by,
        from_user_id=prev_assignee,
        reason=reason,
    )

    await db.commit()
    await db.refresh(state)
    return _to_dict(state)


async def get_routing_state(
    db: AsyncSession,
    trip_id: str,
    agency_id: str,
) -> Optional[dict]:
    """Return routing state for a trip, or None if no record exists yet."""
    result = await db.execute(
        select(TripRoutingState)
        .where(TripRoutingState.trip_id == trip_id)
        .where(TripRoutingState.agency_id == agency_id)
    )
    state = result.scalar_one_or_none()
    return _to_dict(state) if state else None
