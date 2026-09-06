"""
run_ledger.py — Deterministic step ledger for Waypoint OS spine_api.

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
import os
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from spine_api.run_state import RunState, assert_can_transition

# ---------------------------------------------------------------------------
# Storage root
# ---------------------------------------------------------------------------

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
# ``WAYPOINT_RUNS_DIR`` is the deployment seam for a mounted durable volume.
# Keep the repository-local default for development and tests, but do not bake
# the package path into a deployment where a machine restart can discard the
# operational record.
RUNS_DIR = Path(os.environ.get("WAYPOINT_RUNS_DIR", str(DATA_DIR / "runs"))).expanduser()

KNOWN_STEPS = ("packet", "validation", "decision", "strategy", "safety", "output", "blocked_result")


def _run_root(run_id: str) -> Path:
    return RUNS_DIR / run_id


def _meta_path(run_id: str) -> Path:
    return _run_root(run_id) / "meta.json"


def _steps_dir(run_id: str) -> Path:
    return _run_root(run_id) / "steps"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def _file_lock(path: Path):
    """Serialize writes to one ledger file across local worker processes.

    The lock is deliberately next to the file so a mounted ``RUNS_DIR`` carries
    the synchronization primitive with the data. ``fcntl`` is available on the
    supported Linux deployment targets; the no-op fallback keeps the pure file
    backend importable on platforms without it, while atomic replacement still
    prevents readers from observing partially written JSON.
    """
    lock_path = path.with_name(path.name + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_file = lock_path.open("a+", encoding="utf-8")
    try:
        try:
            import fcntl
        except ImportError:  # pragma: no cover - Windows uses the SQL backend.
            fcntl = None
        if fcntl is not None:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        yield
    finally:
        if fcntl is not None:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
        lock_file.close()


def _atomic_write_json(path: Path, payload: Any) -> None:
    """Replace one JSON artifact atomically and flush it before publication."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(
        f".{path.name}.{os.getpid()}.{threading.get_ident()}.tmp"
    )
    try:
        with temp_path.open("w", encoding="utf-8") as fh:
            # ``save_step`` historically accepted arbitrary pipeline objects
            # and stringified non-JSON values; keep that contract while making
            # publication atomic.
            json.dump(payload, fh, indent=2, default=str)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(temp_path, path)
        # The file is now atomically visible. Flush the containing directory
        # where the platform permits it so a host crash cannot lose the rename.
        try:
            dir_fd = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(dir_fd)
            finally:
                os.close(dir_fd)
        except OSError:
            # Windows and some network filesystems do not permit directory
            # fsync; the atomic replace remains the relevant safety property.
            pass
    finally:
        try:
            temp_path.unlink()
        except FileNotFoundError:
            pass


# ---------------------------------------------------------------------------
# RunLedger
# ---------------------------------------------------------------------------


class RunLedger:
    """
    Static interface for reading and writing the run ledger.
    All file I/O is synchronous; artifact writes are safe across local workers
    sharing the same filesystem. Replica-wide durability still requires a
    shared durable volume or a database-backed ledger.
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
        agency_id: Optional[str] = None,
        draft_id: Optional[str] = None,
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
            "draft_id":       draft_id,
            "state":          RunState.QUEUED.value,
            "stage":          stage,
            "operating_mode": operating_mode,
            "agency_id":      agency_id,
            "started_at":     None,
            "completed_at":   None,
            "total_ms":       None,
            "created_at":     _now_iso(),
        }

        path = _meta_path(run_id)
        with _file_lock(path):
            if not path.exists():
                _atomic_write_json(path, meta)

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

        path = _meta_path(run_id)
        with _file_lock(path):
            # Re-read under the lock so two workers cannot both validate and
            # publish conflicting lifecycle transitions from the same snapshot.
            locked_meta = RunLedger.get_meta(run_id)
            if locked_meta is None:
                raise FileNotFoundError(f"No ledger entry for run_id={run_id!r}")
            locked_current = RunState(locked_meta["state"])
            assert_can_transition(locked_current, state)
            locked_meta["state"] = state.value
            if state == RunState.RUNNING and locked_meta.get("started_at") is None:
                locked_meta["started_at"] = _now_iso()
            _atomic_write_json(path, locked_meta)

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
        with _file_lock(step_path):
            _atomic_write_json(step_path, checkpoint)

    @staticmethod
    def complete(run_id: str, total_ms: float) -> None:
        """Mark run as COMPLETED with timing. Enforces transition guard."""
        meta = RunLedger.get_meta(run_id)
        if meta is None:
            raise FileNotFoundError(f"No ledger entry for run_id={run_id!r}")

        current = RunState(meta["state"])
        assert_can_transition(current, RunState.COMPLETED)

        path = _meta_path(run_id)
        with _file_lock(path):
            locked_meta = RunLedger.get_meta(run_id)
            if locked_meta is None:
                raise FileNotFoundError(f"No ledger entry for run_id={run_id!r}")
            assert_can_transition(RunState(locked_meta["state"]), RunState.COMPLETED)
            locked_meta["state"] = RunState.COMPLETED.value
            locked_meta["completed_at"] = _now_iso()
            locked_meta["total_ms"] = round(total_ms, 2)
            _atomic_write_json(path, locked_meta)

    @staticmethod
    def fail(run_id: str, error_type: str, error_message: str) -> None:
        """Mark run as FAILED. Enforces transition guard."""
        meta = RunLedger.get_meta(run_id)
        if meta is None:
            raise FileNotFoundError(f"No ledger entry for run_id={run_id!r}")

        current = RunState(meta["state"])
        assert_can_transition(current, RunState.FAILED)

        path = _meta_path(run_id)
        with _file_lock(path):
            locked_meta = RunLedger.get_meta(run_id)
            if locked_meta is None:
                raise FileNotFoundError(f"No ledger entry for run_id={run_id!r}")
            assert_can_transition(RunState(locked_meta["state"]), RunState.FAILED)
            locked_meta["state"] = RunState.FAILED.value
            locked_meta["completed_at"] = _now_iso()
            locked_meta["error_type"] = error_type
            locked_meta["error_message"] = error_message
            _atomic_write_json(path, locked_meta)

    @staticmethod
    def block(run_id: str, block_reason: str) -> None:
        """Mark run as BLOCKED (strict leakage violation). Enforces transition guard."""
        meta = RunLedger.get_meta(run_id)
        if meta is None:
            raise FileNotFoundError(f"No ledger entry for run_id={run_id!r}")

        current = RunState(meta["state"])
        assert_can_transition(current, RunState.BLOCKED)

        path = _meta_path(run_id)
        with _file_lock(path):
            locked_meta = RunLedger.get_meta(run_id)
            if locked_meta is None:
                raise FileNotFoundError(f"No ledger entry for run_id={run_id!r}")
            assert_can_transition(RunState(locked_meta["state"]), RunState.BLOCKED)
            locked_meta["state"] = RunState.BLOCKED.value
            locked_meta["completed_at"] = _now_iso()
            locked_meta["block_reason"] = block_reason
            _atomic_write_json(path, locked_meta)

    @staticmethod
    def update_meta(run_id: str, **kwargs: Any) -> None:
        """
        Merge kwargs into the run's meta.json. Useful for late-binding fields
        like trip_id that are assigned after the pipeline completes.

        Raises FileNotFoundError if the run does not exist.
        """
        meta = RunLedger.get_meta(run_id)
        if meta is None:
            raise FileNotFoundError(f"No ledger entry for run_id={run_id!r}")
        path = _meta_path(run_id)
        with _file_lock(path):
            locked_meta = RunLedger.get_meta(run_id)
            if locked_meta is None:
                raise FileNotFoundError(f"No ledger entry for run_id={run_id!r}")
            locked_meta.update(kwargs)
            _atomic_write_json(path, locked_meta)

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
            except (OSError, ValueError):
                continue

        return runs

    @staticmethod
    def timeout_stale_runs(max_age_seconds: int = 300) -> list[str]:
        """
        Mark any run stuck in queued/running for longer than max_age_seconds as FAILED.

        Returns list of run_ids that were timed out.
        """
        if not RUNS_DIR.exists():
            return []

        import datetime as _dt

        now = _dt.datetime.now(_dt.timezone.utc)
        timed_out: list[str] = []

        for meta_path in sorted(RUNS_DIR.glob("*/meta.json"), reverse=True):
            try:
                with meta_path.open(encoding="utf-8") as fh:
                    meta = json.load(fh)

                state = meta.get("state", "")
                if state not in ("queued", "running"):
                    continue

                created = meta.get("created_at") or meta.get("started_at")
                if not created:
                    continue

                created_dt = _dt.datetime.fromisoformat(created)
                age = (now - created_dt).total_seconds()

                if age > max_age_seconds:
                    run_id = meta["run_id"]
                    try:
                        RunLedger.fail(
                            run_id,
                            error_type="RunTimeout",
                            error_message=f"Run timed out after {int(age)}s (max {max_age_seconds}s)",
                        )
                        timed_out.append(run_id)
                    except (ValueError, FileNotFoundError):
                        pass
            except (OSError, ValueError):
                continue

        return timed_out
