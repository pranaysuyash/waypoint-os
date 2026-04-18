"""
run_ledger.py — Deterministic step ledger for Waypoint OS spine-api.

Persists per-run metadata and per-stage step outputs so any run can be
inspected or replayed from disk without re-execution.

File layout
-----------
    data/runs/{run_id}/
        meta.json            run-level metadata (state, timing, trip_id)
        steps/
            packet.json      output of packet stage + timestamp
            validation.json  output of validation stage + timestamp
            decision.json    output of decision stage + timestamp
            strategy.json    output of strategy stage + timestamp
            safety.json      output of safety stage + timestamp
        events.jsonl         append-only event log (written by run_events.py)

Usage
-----
    from spine_api.run_ledger import RunLedger

    RunLedger.create(run_id, trip_id, stage, operating_mode)
    RunLedger.set_state(run_id, RunState.RUNNING)
    RunLedger.save_step(run_id, "packet", packet_dict)
    RunLedger.complete(run_id, total_ms)

    meta = RunLedger.get_meta(run_id)        # → dict | None
    step = RunLedger.get_step(run_id, "decision")  # → dict | None
    runs = RunLedger.list_runs(trip_id=...)   # → list[dict]
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from run_state import RunState, assert_can_transition

# ---------------------------------------------------------------------------
# Storage root
# ---------------------------------------------------------------------------

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
RUNS_DIR = DATA_DIR / "runs"

KNOWN_STEPS = ("packet", "validation", "decision", "strategy", "safety", "output")


def _run_root(run_id: str) -> Path:
    return RUNS_DIR / run_id


def _meta_path(run_id: str) -> Path:
    return _run_root(run_id) / "meta.json"


def _steps_dir(run_id: str) -> Path:
    return _run_root(run_id) / "steps"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# RunLedger
# ---------------------------------------------------------------------------


class RunLedger:
    """
    Static interface for reading and writing the run ledger.
    All file I/O is synchronous; safe for single-worker uvicorn.
    """

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------

    @staticmethod
    def create(
        run_id: str,
        trip_id: Optional[str],
        stage: str,
        operating_mode: str,
    ) -> dict[str, Any]:
        """
        Initialize meta.json for a new run in QUEUED state.
        Idempotent if called multiple times with the same run_id.
        """
        run_root = _run_root(run_id)
        run_root.mkdir(parents=True, exist_ok=True)
        _steps_dir(run_id).mkdir(exist_ok=True)

        meta: dict[str, Any] = {
            "run_id":         run_id,
            "trip_id":        trip_id,
            "state":          RunState.QUEUED.value,
            "stage":          stage,
            "operating_mode": operating_mode,
            "started_at":     None,
            "completed_at":   None,
            "total_ms":       None,
            "created_at":     _now_iso(),
        }

        path = _meta_path(run_id)
        if not path.exists():
            with path.open("w", encoding="utf-8") as fh:
                json.dump(meta, fh, indent=2)

        # Idempotency policy (explicit, documented):
        # create() is idempotent — calling it again with the same run_id is a no-op.
        # Each call to POST /run generates a new run_id (via uuid4), so true
        # duplicates from the same HTTP call are impossible. This guard protects
        # against unexpected double-initialisation within a single request lifecycle.
        return RunLedger.get_meta(run_id) if path.exists() and not meta else meta

    @staticmethod
    def set_state(run_id: str, state: RunState) -> None:
        """
        Update the run state in meta.json.

        Enforces the state machine transition rules via assert_can_transition.
        Sets started_at when transitioning to RUNNING.
        Raises ValueError on invalid transition.
        """
        meta = RunLedger.get_meta(run_id)
        if meta is None:
            raise FileNotFoundError(f"No ledger entry for run_id={run_id!r}")

        current = RunState(meta["state"])
        assert_can_transition(current, state)  # raises ValueError on invalid

        meta["state"] = state.value

        if state == RunState.RUNNING and meta.get("started_at") is None:
            meta["started_at"] = _now_iso()

        with _meta_path(run_id).open("w", encoding="utf-8") as fh:
            json.dump(meta, fh, indent=2)

    @staticmethod
    def save_step(
        run_id: str,
        step_name: str,
        data: Any,
    ) -> None:
        """
        Persist a pipeline step output with a checkpoint timestamp.

        step_name must be one of: packet, validation, decision, strategy, safety, output
        """
        if step_name not in KNOWN_STEPS:
            raise ValueError(
                f"Unknown step {step_name!r}. Valid: {KNOWN_STEPS}"
            )

        _steps_dir(run_id).mkdir(parents=True, exist_ok=True)

        checkpoint = {
            "step":          step_name,
            "run_id":        run_id,
            "checkpointed_at": _now_iso(),
            "data":          data,
        }

        step_path = _steps_dir(run_id) / f"{step_name}.json"
        with step_path.open("w", encoding="utf-8") as fh:
            json.dump(checkpoint, fh, indent=2, default=str)

    @staticmethod
    def complete(run_id: str, total_ms: float) -> None:
        """Mark run as COMPLETED with timing. Enforces transition guard."""
        meta = RunLedger.get_meta(run_id)
        if meta is None:
            raise FileNotFoundError(f"No ledger entry for run_id={run_id!r}")

        current = RunState(meta["state"])
        assert_can_transition(current, RunState.COMPLETED)

        meta["state"]        = RunState.COMPLETED.value
        meta["completed_at"] = _now_iso()
        meta["total_ms"]     = round(total_ms, 2)

        with _meta_path(run_id).open("w", encoding="utf-8") as fh:
            json.dump(meta, fh, indent=2)

    @staticmethod
    def fail(run_id: str, error_type: str, error_message: str) -> None:
        """Mark run as FAILED. Enforces transition guard."""
        meta = RunLedger.get_meta(run_id)
        if meta is None:
            raise FileNotFoundError(f"No ledger entry for run_id={run_id!r}")

        current = RunState(meta["state"])
        assert_can_transition(current, RunState.FAILED)

        meta["state"]         = RunState.FAILED.value
        meta["completed_at"]  = _now_iso()
        meta["error_type"]    = error_type
        meta["error_message"] = error_message

        with _meta_path(run_id).open("w", encoding="utf-8") as fh:
            json.dump(meta, fh, indent=2)

    @staticmethod
    def block(run_id: str, block_reason: str) -> None:
        """Mark run as BLOCKED (strict leakage violation). Enforces transition guard."""
        meta = RunLedger.get_meta(run_id)
        if meta is None:
            raise FileNotFoundError(f"No ledger entry for run_id={run_id!r}")

        current = RunState(meta["state"])
        assert_can_transition(current, RunState.BLOCKED)

        meta["state"]        = RunState.BLOCKED.value
        meta["completed_at"] = _now_iso()
        meta["block_reason"] = block_reason

        with _meta_path(run_id).open("w", encoding="utf-8") as fh:
            json.dump(meta, fh, indent=2)

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    @staticmethod
    def get_meta(run_id: str) -> Optional[dict[str, Any]]:
        """Return run metadata, or None if not found."""
        path = _meta_path(run_id)
        if not path.exists():
            return None
        with path.open(encoding="utf-8") as fh:
            return json.load(fh)

    @staticmethod
    def get_step(run_id: str, step_name: str) -> Optional[dict[str, Any]]:
        """Return a checkpointed step output, or None if not yet written."""
        path = _steps_dir(run_id) / f"{step_name}.json"
        if not path.exists():
            return None
        with path.open(encoding="utf-8") as fh:
            return json.load(fh)

    @staticmethod
    def get_all_steps(run_id: str) -> dict[str, Any]:
        """Return all checkpointed steps as {step_name: checkpoint_data}."""
        result: dict[str, Any] = {}
        steps_dir = _steps_dir(run_id)
        if not steps_dir.exists():
            return result
        for step_name in KNOWN_STEPS:
            path = steps_dir / f"{step_name}.json"
            if path.exists():
                with path.open(encoding="utf-8") as fh:
                    result[step_name] = json.load(fh)
        return result

    @staticmethod
    def list_runs(
        trip_id: Optional[str] = None,
        state: Optional[str] = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """
        List runs in reverse-chronological order (newest first).
        Optionally filter by trip_id and/or state.
        """
        if not RUNS_DIR.exists():
            return []

        runs: list[dict[str, Any]] = []

        for meta_path in sorted(RUNS_DIR.glob("*/meta.json"), reverse=True):
            try:
                with meta_path.open(encoding="utf-8") as fh:
                    meta = json.load(fh)

                if trip_id is not None and meta.get("trip_id") != trip_id:
                    continue
                if state is not None and meta.get("state") != state:
                    continue

                runs.append(meta)

                if len(runs) >= limit:
                    break
            except Exception:
                continue

        return runs
