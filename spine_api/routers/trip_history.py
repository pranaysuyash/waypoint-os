"""
Trip History & Invertible Undo/Redo API Router.

Provides endpoints for creating trip mutation checkpoints, undoing/redoing state changes,
and inspecting the historical mutation timeline.

PA-15 (2026-09-06) hardening:
- Agency scoping: every endpoint requires the authenticated agency
  (``get_current_agency_id``, same dependency as other tenant-scoped routers)
  and verifies the trip belongs to that agency via ``TripStore.get_trip_for_agency``
  before touching history. Mismatches return 404 (existence not revealed), and
  history stacks are keyed per ``(agency_id, trip_id)`` in
  ``src/state/mutation_history_stack.py``.
- Bounds: the per-trip stack is capped (drop-oldest) in the history stack.

IMPORTANT payload semantics (deliberate design — no second write path to trips):
undo/redo and checkpoint endpoints NEVER write TripStore directly. They return
a ``restored_state`` payload for the CLIENT to apply through the canonical
guarded trip save (status guard + optimistic-version CAS in spine_api/persistence.py).
This keeps a single write path to the trip of record: an in-router restore would
bypass those guards and create a parallel mutation route.
"""

from __future__ import annotations

from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from spine_api.core.auth import get_current_agency_id

try:
    from spine_api import persistence
except (ImportError, ValueError):
    import persistence

from src.state.mutation_history_stack import TripMutationHistoryStack

TripStore = persistence.TripStore

router = APIRouter(prefix="/api/v1/trips", tags=["trip-history"])


class CheckpointRequest(BaseModel):
    state_payload: Dict[str, Any]
    author: str = "agent"
    description: str = "Manual edit"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class UndoRedoRequest(BaseModel):
    current_live_state: Dict[str, Any]


def _require_trip_in_agency(trip_id: str, agency_id: str) -> dict:
    """Verify the trip exists and belongs to the caller's agency.

    PA-15: the router previously had no agency dependency at all, so any
    authenticated caller could read/push another agency's history stacks.
    Missing or foreign trips both return 404 (existence not revealed);
    infrastructure failures surface as 503 rather than silent fabrication.
    """
    try:
        trip = TripStore.get_trip_for_agency(trip_id, agency_id)
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="trip history lookup temporarily unavailable",
        ) from exc
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip


@router.post("/{trip_id}/history/checkpoint")
def create_checkpoint(
    trip_id: str,
    payload: CheckpointRequest,
    agency_id: str = Depends(get_current_agency_id),
) -> Dict[str, Any]:
    """Capture a snapshot checkpoint before applying a mutation (agency-scoped)."""
    _require_trip_in_agency(trip_id, agency_id)
    checkpoint = TripMutationHistoryStack.push_checkpoint(
        trip_id=trip_id,
        current_state=payload.state_payload,
        author=payload.author,
        description=payload.description,
        metadata=payload.metadata,
        agency_id=agency_id,
    )
    return {
        "status": "checkpoint_saved",
        "checkpoint": checkpoint.to_dict(),
    }


@router.post("/{trip_id}/history/undo")
def undo_trip_mutation(
    trip_id: str,
    payload: UndoRedoRequest,
    agency_id: str = Depends(get_current_agency_id),
) -> Dict[str, Any]:
    """Revert trip state to the previous checkpoint.

    Returns a restored-state payload; the CLIENT applies it via the canonical
    guarded save (see module docstring — no second write path to trips).
    """
    _require_trip_in_agency(trip_id, agency_id)
    restored = TripMutationHistoryStack.undo(
        trip_id=trip_id,
        current_live_state=payload.current_live_state,
        agency_id=agency_id,
    )
    if restored is None:
        raise HTTPException(status_code=400, detail="No undo checkpoints available")
    return {
        "status": "undone",
        "restored_state": restored,
    }


@router.post("/{trip_id}/history/redo")
def redo_trip_mutation(
    trip_id: str,
    payload: UndoRedoRequest,
    agency_id: str = Depends(get_current_agency_id),
) -> Dict[str, Any]:
    """Re-apply the next checkpoint.

    Returns a restored-state payload; the CLIENT applies it via the canonical
    guarded save (see module docstring — no second write path to trips).
    """
    _require_trip_in_agency(trip_id, agency_id)
    restored = TripMutationHistoryStack.redo(
        trip_id=trip_id,
        current_live_state=payload.current_live_state,
        agency_id=agency_id,
    )
    if restored is None:
        raise HTTPException(status_code=400, detail="No redo checkpoints available")
    return {
        "status": "redone",
        "restored_state": restored,
    }


@router.get("/{trip_id}/history")
def get_trip_history(
    trip_id: str,
    agency_id: str = Depends(get_current_agency_id),
) -> Dict[str, Any]:
    """Get the mutation history timeline for a trip (agency-scoped)."""
    _require_trip_in_agency(trip_id, agency_id)
    return {
        "status": "success",
        "timeline": TripMutationHistoryStack.get_timeline(trip_id, agency_id=agency_id),
    }
