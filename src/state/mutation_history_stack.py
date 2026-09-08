"""
src/state/mutation_history_stack.py — Invertible Time-Travel & Undo/Redo State Mutation Stack.

Maintains immutable snapshot checkpoints for trips, enabling lossless rollback,
counterfactual branch exploration, and deterministic undo/redo state restoration.
"""

from __future__ import annotations

import copy
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass(slots=True)
class CheckpointSnapshot:
    checkpoint_id: str
    trip_id: str
    state_payload: Dict[str, Any]
    author: str
    description: str
    created_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    # PA-15 (additive): agency scope the checkpoint belongs to. Empty for
    # legacy in-process callers that never scoped (tests, pre-PA-15 usage).
    agency_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "checkpoint_id": self.checkpoint_id,
            "trip_id": self.trip_id,
            "author": self.author,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "state_payload": self.state_payload,
            "metadata": self.metadata,
            "agency_id": self.agency_id,
        }


class TripMutationHistoryStack:
    """Manages undo and redo snapshot stacks per trip with delta logging.

    PA-15 (2026-09-06):
    - Stacks are keyed per ``(agency_id, trip_id)`` when an ``agency_id`` is
      supplied, so one agency can never read or mutate another agency's
      history. The unscoped ``trip_id``-only behavior is preserved for
      existing in-process callers.
    - Stacks are capped (``MAX_STACK_DEPTH``, drop-oldest). They were
      previously in-memory and unbounded (audit PA-15/PA-30).
    """

    MAX_STACK_DEPTH = 50

    _undo_stacks: Dict[str, List[CheckpointSnapshot]] = {}
    _redo_stacks: Dict[str, List[CheckpointSnapshot]] = {}
    _current_states: Dict[str, Dict[str, Any]] = {}

    @staticmethod
    def _scope_key(trip_id: str, agency_id: Optional[str]) -> str:
        """Internal dict key: scoped per agency when the agency is known."""
        if agency_id:
            return f"{agency_id}:{trip_id}"
        return trip_id

    @classmethod
    def _append_capped(
        cls, stack: List[CheckpointSnapshot], snapshot: CheckpointSnapshot
    ) -> None:
        """Append, dropping the OLDEST entries beyond MAX_STACK_DEPTH."""
        stack.append(snapshot)
        if len(stack) > cls.MAX_STACK_DEPTH:
            del stack[: len(stack) - cls.MAX_STACK_DEPTH]

    @classmethod
    def push_checkpoint(
        cls,
        trip_id: str,
        current_state: Dict[str, Any],
        author: str = "agent",
        description: str = "State mutation",
        metadata: Optional[Dict[str, Any]] = None,
        agency_id: Optional[str] = None,
    ) -> CheckpointSnapshot:
        """Capture current state before applying a mutation."""
        key = cls._scope_key(trip_id, agency_id)
        if key not in cls._undo_stacks:
            cls._undo_stacks[key] = []
            cls._redo_stacks[key] = []

        # Clear redo stack upon new mutation
        cls._redo_stacks[key].clear()

        checkpoint = CheckpointSnapshot(
            checkpoint_id=f"chk_{uuid.uuid4().hex[:12]}",
            trip_id=trip_id,
            state_payload=copy.deepcopy(current_state),
            author=author,
            description=description,
            created_at=datetime.now(timezone.utc),
            metadata=metadata or {},
            agency_id=agency_id or "",
        )
        cls._append_capped(cls._undo_stacks[key], checkpoint)
        cls._current_states[key] = copy.deepcopy(current_state)
        return checkpoint

    @classmethod
    def undo(
        cls,
        trip_id: str,
        current_live_state: Dict[str, Any],
        agency_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Revert to the previous checkpoint."""
        key = cls._scope_key(trip_id, agency_id)
        undo_stack = cls._undo_stacks.get(key, [])
        if not undo_stack:
            return None

        # Push current live state to redo stack
        redo_checkpoint = CheckpointSnapshot(
            checkpoint_id=f"redo_{uuid.uuid4().hex[:12]}",
            trip_id=trip_id,
            state_payload=copy.deepcopy(current_live_state),
            author="undo_action",
            description="Pre-undo snapshot",
            created_at=datetime.now(timezone.utc),
            agency_id=agency_id or "",
        )
        if key not in cls._redo_stacks:
            cls._redo_stacks[key] = []
        cls._append_capped(cls._redo_stacks[key], redo_checkpoint)

        # Pop previous checkpoint from undo stack
        target = undo_stack.pop()
        cls._current_states[key] = copy.deepcopy(target.state_payload)
        return target.state_payload

    @classmethod
    def redo(
        cls,
        trip_id: str,
        current_live_state: Dict[str, Any],
        agency_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Re-apply the next checkpoint."""
        key = cls._scope_key(trip_id, agency_id)
        redo_stack = cls._redo_stacks.get(key, [])
        if not redo_stack:
            return None

        # Push current state back to undo stack
        undo_checkpoint = CheckpointSnapshot(
            checkpoint_id=f"undo_{uuid.uuid4().hex[:12]}",
            trip_id=trip_id,
            state_payload=copy.deepcopy(current_live_state),
            author="redo_action",
            description="Pre-redo snapshot",
            created_at=datetime.now(timezone.utc),
            agency_id=agency_id or "",
        )
        if key not in cls._undo_stacks:
            cls._undo_stacks[key] = []
        cls._append_capped(cls._undo_stacks[key], undo_checkpoint)

        # Pop target state from redo stack
        target = redo_stack.pop()
        cls._current_states[key] = copy.deepcopy(target.state_payload)
        return target.state_payload

    @classmethod
    def get_timeline(cls, trip_id: str, agency_id: Optional[str] = None) -> Dict[str, Any]:
        """Return history metadata and stack depths for a trip."""
        key = cls._scope_key(trip_id, agency_id)
        undo_stack = cls._undo_stacks.get(key, [])
        redo_stack = cls._redo_stacks.get(key, [])

        return {
            "trip_id": trip_id,
            "agency_id": agency_id or "",
            "undo_available": len(undo_stack) > 0,
            "redo_available": len(redo_stack) > 0,
            "undo_count": len(undo_stack),
            "redo_count": len(redo_stack),
            "checkpoints": [c.to_dict() for c in undo_stack],
        }

    @classmethod
    def clear(cls) -> None:
        """Reset state for testing."""
        cls._undo_stacks.clear()
        cls._redo_stacks.clear()
        cls._current_states.clear()
