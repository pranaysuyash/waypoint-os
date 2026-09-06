"""
Trip History & Invertible Undo/Redo API Router.

Provides endpoints for creating trip mutation checkpoints, undoing/redoing state changes,
and inspecting the historical mutation timeline.
"""

from __future__ import annotations

from typing import Any, Dict
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.state.mutation_history_stack import TripMutationHistoryStack

router = APIRouter(prefix="/api/v1/trips", tags=["trip-history"])


class CheckpointRequest(BaseModel):
    state_payload: Dict[str, Any]
    author: str = "agent"
    description: str = "Manual edit"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class UndoRedoRequest(BaseModel):
    current_live_state: Dict[str, Any]


@router.post("/{trip_id}/history/checkpoint")
def create_checkpoint(trip_id: str, payload: CheckpointRequest) -> Dict[str, Any]:
    """Capture a snapshot checkpoint before applying a mutation."""
    checkpoint = TripMutationHistoryStack.push_checkpoint(
        trip_id=trip_id,
        current_state=payload.state_payload,
        author=payload.author,
        description=payload.description,
        metadata=payload.metadata,
    )
    return {
        "status": "checkpoint_saved",
        "checkpoint": checkpoint.to_dict(),
    }


@router.post("/{trip_id}/history/undo")
def undo_trip_mutation(trip_id: str, payload: UndoRedoRequest) -> Dict[str, Any]:
    """Revert trip state to the previous checkpoint."""
    restored = TripMutationHistoryStack.undo(
        trip_id=trip_id,
        current_live_state=payload.current_live_state,
    )
    if restored is None:
        raise HTTPException(status_code=400, detail="No undo checkpoints available")
    return {
        "status": "undone",
        "restored_state": restored,
    }


@router.post("/{trip_id}/history/redo")
def redo_trip_mutation(trip_id: str, payload: UndoRedoRequest) -> Dict[str, Any]:
    """Re-apply the next checkpoint."""
    restored = TripMutationHistoryStack.redo(
        trip_id=trip_id,
        current_live_state=payload.current_live_state,
    )
    if restored is None:
        raise HTTPException(status_code=400, detail="No redo checkpoints available")
    return {
        "status": "redone",
        "restored_state": restored,
    }


@router.get("/{trip_id}/history")
def get_trip_history(trip_id: str) -> Dict[str, Any]:
    """Get the mutation history timeline for a trip."""
    return {
        "status": "success",
        "timeline": TripMutationHistoryStack.get_timeline(trip_id),
    }
