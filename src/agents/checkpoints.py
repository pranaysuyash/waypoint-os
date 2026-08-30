"""
src/agents/checkpoints.py — Execution checkpointing and state resumption engine.

Grounding doctrine:
- PER-0700 (Agentic Systems Architect): Granular step checkpointing allows deterministic resumption without re-running side-effects.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger("src.agents.checkpoints")


@dataclass(slots=True)
class ExecutionCheckpoint:
    """Snapshot of agent execution state at a specific step."""
    checkpoint_id: str
    run_id: str
    trip_id: str
    step_index: int
    step_name: str
    completed_steps: List[str] = field(default_factory=list)
    state_payload: Dict[str, Any] = field(default_factory=dict)
    tool_outputs: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

    def to_json(self) -> str:
        return json.dumps(asdict(self), sort_keys=True, default=str)

    @classmethod
    def from_json(cls, json_str: str) -> ExecutionCheckpoint:
        data = json.loads(json_str)
        return cls(**data)


class CheckpointStore:
    """Store and retriever for execution checkpoints."""

    _instance: Optional[CheckpointStore] = None

    def __init__(self):
        self._checkpoints: Dict[str, List[ExecutionCheckpoint]] = {}  # run_id -> list of checkpoints

    @classmethod
    def get_instance(cls) -> CheckpointStore:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def save_checkpoint(
        self,
        run_id: str,
        trip_id: str,
        step_index: int,
        step_name: str,
        completed_steps: List[str],
        state_payload: Dict[str, Any],
        tool_outputs: Dict[str, Any],
    ) -> ExecutionCheckpoint:
        """Create and persist a new execution checkpoint."""
        checkpoint_id = f"chk:{run_id}:step_{step_index}:{int(time.time()*1000)}"
        cp = ExecutionCheckpoint(
            checkpoint_id=checkpoint_id,
            run_id=run_id,
            trip_id=trip_id,
            step_index=step_index,
            step_name=step_name,
            completed_steps=list(completed_steps),
            state_payload=dict(state_payload),
            tool_outputs=dict(tool_outputs),
        )
        self._checkpoints.setdefault(run_id, []).append(cp)
        logger.info("Saved checkpoint %s for run_id=%s step=%s", checkpoint_id, run_id, step_name)
        return cp

    def get_latest_checkpoint(self, run_id: str) -> Optional[ExecutionCheckpoint]:
        """Retrieve the latest checkpoint for a run to resume execution."""
        cps = self._checkpoints.get(run_id, [])
        return cps[-1] if cps else None

    def get_all_checkpoints(self, run_id: str) -> List[ExecutionCheckpoint]:
        """Return full history of checkpoints for audit and deterministic replay."""
        return list(self._checkpoints.get(run_id, []))
