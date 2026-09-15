"""
run_ledger.py — Deterministic step ledger for Waypoint OS spine_api.

Persists per-run metadata and per-stage step outputs so any run can be
inspected or replayed without re-execution.

Durability model (FND-0226)
---------------------------
The lifecycle truth lives in the SAME store as the trip state. When
``TRIPSTORE_BACKEND`` is sql/postgres, every meta transition is STRICTLY
mirrored into the ``run_checkpoints`` SQL table (see
``spine_api.run_ledger_sql``); a failed mirror raises so the divergence
surfaces instead of silently re-creating the disk/SQL split-brain. The
on-disk ``data/runs/`` tree is a local cache in that mode: step artifacts
and heartbeats mirror best-effort, and reads fall through to SQL on a
cache miss (e.g. after a rolling deploy replaced the pod's disk).

File layout (disk cache)
------------------------
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
import logging
import os
import shutil
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from spine_api.failure_taxonomy import FailureClass
from spine_api.run_state import RunState, assert_can_transition

logger = logging.getLogger(__name__)

# Terminal ledger states eligible for garbage collection (PA-12).
# ``interrupted`` is the honest FND-0226 terminal state for runs whose
# worker vanished (deploy/crash) with no live lease/heartbeat.
TERMINAL_STATES = {"completed", "failed", "blocked", "interrupted"}

# Lazy-GC throttle: prune at most once per hour, keyed on a marker file in
# RUNS_DIR so multi-worker deployments share the throttle through the volume.
_PRUNE_MARKER_NAME = ".last_prune"
_PRUNE_INTERVAL_SECONDS = 3600

# The lazy trigger is opt-in (WAYPOINT_RUN_LEDGER_GC=1). Pruning deletes run
# directories, so it must never fire implicitly against a live data/runs tree
# — including when tests import server modules and exercise the GET /runs
# sweep path. Deployments enable it explicitly; operators can always run
# prune_expired_runs() directly (see the manual first-prune command).

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


def _checkpoint_store():
    """Return the SQL checkpoint store when the state store is SQL-backed.

    FND-0226: checkpoint durability must live in the same store as the trip
    state. Deferred import keeps the file-backend path (tests, local dev)
    free of any SQL dependency, and keeps run_ledger ↔ run_ledger_sql from
    forming an import cycle (reconciliation calls back into RunLedger).

    ``RUNNING_TESTS=1`` (set by tests/conftest.py) disables the mirror so
    unrelated unit tests exercising RunLedger can never write synthetic
    rows into a development database that happens to run with
    ``TRIPSTORE_BACKEND=sql``. Tests that need the real store monkeypatch
    ``_checkpoint_store`` directly (see tests/test_run_ledger_durability.py).
    """
    if os.getenv("RUNNING_TESTS", "").strip().lower() in ("1", "true", "yes"):
        return None

    from spine_api.run_ledger_sql import SQLRunCheckpointStore, checkpoint_backend_is_sql

    if checkpoint_backend_is_sql():
        return SQLRunCheckpointStore
    return None


def _mirror_meta_strict(meta: dict[str, Any]) -> None:
    """Mirror a lifecycle meta transition into SQL. Raises on mirror failure.

    STRICT on purpose: swallowing a mirror failure would let the SQL store
    and the disk cache disagree about lifecycle truth — exactly the silent
    split-brain FND-0226 forbids. Callers (pipeline error handling) already
    convert raised errors into loud run failures.
    """
    store = _checkpoint_store()
    if store is not None:
        store.mirror_meta(meta)


def _mirror_best_effort(operation, *args) -> None:
    """Mirror a non-lifecycle artifact (heartbeat / step) without ever raising.

    Heartbeats and step payloads are cache-grade data: losing one mirror
    write degrades observability or replay, never lifecycle honesty.
    """
    store = _checkpoint_store()
    if store is None:
        return
    try:
        operation(*args)
    except Exception as exc:  # noqa: BLE001 — cache mirror must never break the run
        logger.warning("Run-ledger SQL mirror (best-effort) failed: %s", exc)


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
                stored = RunLedger.get_meta(run_id)
                if stored is not None:
                    _mirror_meta_strict(stored)

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
        _mirror_meta_strict(locked_meta)

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

        def _mirror_step() -> None:
            from spine_api.run_ledger_sql import SQLRunCheckpointStore

            SQLRunCheckpointStore.mirror_step(run_id, step_name, checkpoint)

        _mirror_best_effort(_mirror_step)

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
        _mirror_meta_strict(locked_meta)

    @staticmethod
    def complete_after_timeout(
        run_id: str,
        total_ms: Optional[float] = None,
    ) -> None:
        """Reconcile a run the stale sweep FAILED while its thread was alive.

        PA-17: the sweep can mark a live run FAILED; when the pipeline then
        finishes and saves its trip successfully, ``complete()`` raises on the
        illegal failed→completed transition and the ledger would forever say
        FAILED even though the trip exists. This method is the explicit,
        audited reconciliation: it marks the run COMPLETED and records
        ``recovered_after_timeout: true`` in meta.

        Unlike ``complete()`` this deliberately bypasses the state machine's
        transition guard — but only from ``failed``. Any other source state
        raises ValueError so this can never mask a genuinely illegal write.
        """
        path = _meta_path(run_id)
        with _file_lock(path):
            locked_meta = RunLedger.get_meta(run_id)
            if locked_meta is None:
                raise FileNotFoundError(f"No ledger entry for run_id={run_id!r}")
            current = RunState(locked_meta["state"])
            if current is not RunState.FAILED:
                raise ValueError(
                    f"complete_after_timeout is only valid from 'failed', "
                    f"got {current!r} for run {run_id!r}"
                )
            locked_meta["state"] = RunState.COMPLETED.value
            locked_meta["completed_at"] = _now_iso()
            if total_ms is not None:
                locked_meta["total_ms"] = round(total_ms, 2)
            locked_meta["recovered_after_timeout"] = True
            _atomic_write_json(path, locked_meta)
        _mirror_meta_strict(locked_meta)

    @staticmethod
    def touch(run_id: str) -> None:
        """Heartbeat a live run (PA-17).

        Cheap meta merge: updates ``heartbeat_at`` so ``timeout_stale_runs``
        can distinguish a live run (fresh heartbeat) from a genuinely stuck
        one. Raises FileNotFoundError if the run does not exist; callers in
        the checkpoint path guard this — observability must never break a run.
        """
        meta = RunLedger.get_meta(run_id)
        if meta is None:
            raise FileNotFoundError(f"No ledger entry for run_id={run_id!r}")
        path = _meta_path(run_id)
        with _file_lock(path):
            locked_meta = RunLedger.get_meta(run_id)
            if locked_meta is None:
                raise FileNotFoundError(f"No ledger entry for run_id={run_id!r}")
            locked_meta["heartbeat_at"] = _now_iso()
            _atomic_write_json(path, locked_meta)

        def _mirror_heartbeat() -> None:
            from spine_api.run_ledger_sql import SQLRunCheckpointStore

            SQLRunCheckpointStore.mirror_meta(locked_meta)

        _mirror_best_effort(_mirror_heartbeat)

    @staticmethod
    def fail(
        run_id: str,
        error_type: str,
        error_message: str,
        failure_class: str = FailureClass.UNCLASSIFIED.value,
        stage: Optional[str] = None,
    ) -> None:
        """Mark run as FAILED. Enforces transition guard.

        PA-07: besides the raw ``error_type`` (kept as-is — existing callers
        and consumers are unchanged), the ledger meta now records a stable
        ``failure_class`` (see spine_api.failure_taxonomy) and the
        ``stage_at_failure`` so recovery can branch on cause instead of
        requeueing class-blind.
        """
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
            locked_meta["failure_class"] = failure_class
            locked_meta["stage_at_failure"] = stage
            _atomic_write_json(path, locked_meta)
        _mirror_meta_strict(locked_meta)

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
        _mirror_meta_strict(locked_meta)

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
        _mirror_meta_strict(locked_meta)

    @staticmethod
    def mark_interrupted(run_id: str, reason: str) -> None:
        """Mark a queued/running run INTERRUPTED — honest deploy/crash state.

        FND-0226: the startup reconciliation uses this to convert orphaned
        SQL run records (no live lease, stale heartbeat) from a lying
        ``running`` into an honest ``interrupted``. The disk cache is
        updated too when present, and the SQL mirror is strict like every
        other lifecycle transition.

        Unlike ``complete_after_timeout`` this deliberately bypasses the
        generic transition guard ONLY for queued/running → interrupted; any
        other source state raises ValueError so reconciliation can never
        clobber a terminal record.
        """
        meta = RunLedger.get_meta(run_id)
        if meta is None:
            raise FileNotFoundError(f"No ledger entry for run_id={run_id!r}")

        current = RunState(meta["state"])
        if current not in (RunState.QUEUED, RunState.RUNNING):
            raise ValueError(
                f"mark_interrupted is only valid from 'queued'/'running', "
                f"got {current!r} for run {run_id!r}"
            )

        path = _meta_path(run_id)
        with _file_lock(path):
            locked_meta = RunLedger.get_meta(run_id)
            if locked_meta is None:
                raise FileNotFoundError(f"No ledger entry for run_id={run_id!r}")
            locked_current = RunState(locked_meta["state"])
            if locked_current not in (RunState.QUEUED, RunState.RUNNING):
                raise ValueError(
                    f"mark_interrupted is only valid from 'queued'/'running', "
                    f"got {locked_current!r} for run {run_id!r}"
                )
            now = _now_iso()
            locked_meta["state"] = RunState.INTERRUPTED.value
            locked_meta["completed_at"] = now
            locked_meta["reconciled_at"] = now
            locked_meta["reconciled_reason"] = reason
            _atomic_write_json(path, locked_meta)
        _mirror_meta_strict(locked_meta)

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    @staticmethod
    def get_meta(run_id: str) -> Optional[dict[str, Any]]:
        """Return run metadata, or None if not found.

        FND-0226: when the SQL checkpoint store is active, a disk miss falls
        through to the durable store — a pod that lost its local cache in a
        rolling deploy still reads honest lifecycle state.
        """
        path = _meta_path(run_id)
        if path.exists():
            with path.open(encoding="utf-8") as fh:
                return json.load(fh)

        store = _checkpoint_store()
        if store is not None:
            return store.load_meta(run_id)
        return None

    @staticmethod
    def get_step(run_id: str, step_name: str) -> Optional[dict[str, Any]]:
        """Return a checkpointed step output, or None if not yet written."""
        path = _steps_dir(run_id) / f"{step_name}.json"
        if path.exists():
            with path.open(encoding="utf-8") as fh:
                return json.load(fh)

        store = _checkpoint_store()
        if store is not None:
            return store.load_step(run_id, step_name)
        return None

    @staticmethod
    def get_all_steps(run_id: str) -> dict[str, Any]:
        """Return all checkpointed steps as {step_name: checkpoint_data}.

        Disk cache wins where present; SQL fills any gaps (post-deploy
        cache-miss read-through).
        """
        result: dict[str, Any] = {}
        steps_dir = _steps_dir(run_id)
        if steps_dir.exists():
            for step_name in KNOWN_STEPS:
                path = steps_dir / f"{step_name}.json"
                if path.exists():
                    with path.open(encoding="utf-8") as fh:
                        result[step_name] = json.load(fh)

        if len(result) < len(KNOWN_STEPS):
            store = _checkpoint_store()
            if store is not None:
                for step_name in KNOWN_STEPS:
                    if step_name in result:
                        continue
                    mirrored = store.load_step(run_id, step_name)
                    if mirrored is not None:
                        result[step_name] = mirrored
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

        FND-0226: when the SQL checkpoint store is active, SQL records not
        present in the local disk cache (post-deploy cache loss) are merged
        in so the run list stays honest; disk entries win on run_id
        collision because they are the hot cache.
        """
        runs: list[dict[str, Any]] = []
        seen_run_ids: set[str] = set()

        if RUNS_DIR.exists():
            for meta_path in sorted(RUNS_DIR.glob("*/meta.json"), reverse=True):
                try:
                    with meta_path.open(encoding="utf-8") as fh:
                        meta = json.load(fh)

                    if trip_id is not None and meta.get("trip_id") != trip_id:
                        continue
                    if state is not None and meta.get("state") != state:
                        continue

                    runs.append(meta)
                    seen_run_ids.add(meta.get("run_id", ""))

                    if len(runs) >= limit:
                        break
                except (OSError, ValueError):
                    continue

        if len(runs) < limit:
            store = _checkpoint_store()
            if store is not None:
                try:
                    for meta in store.list_metas(trip_id=trip_id, state=state, limit=limit * 2):
                        if meta.get("run_id") in seen_run_ids:
                            continue
                        runs.append(meta)
                        seen_run_ids.add(meta.get("run_id", ""))
                        if len(runs) >= limit:
                            break
                except Exception as exc:  # noqa: BLE001 — read path must not crash listing
                    logger.warning("Run-ledger SQL read-through listing failed: %s", exc)

        runs.sort(key=lambda m: m.get("created_at") or "", reverse=True)
        return runs[:limit]

    @staticmethod
    def latest_run_for_trip(trip_id: str) -> Optional[dict[str, Any]]:
        """Return the most recent run meta for a trip, or None (PA-07 helper).

        Used by the recovery agent to read ``failure_class`` /
        ``stage_at_failure`` from the trip's latest run so recovery can branch
        on cause. Missing/invalid ledgers degrade to None — recovery falls
        back to its existing ladder.
        """
        if not trip_id or not RUNS_DIR.exists():
            return None
        try:
            runs = RunLedger.list_runs(trip_id=trip_id, limit=1)
        except (OSError, ValueError):  # defensive — never break recovery
            return None
        return runs[0] if runs else None

    @staticmethod
    def prune_expired_runs(retention_days: int = 30, max_delete: int = 500) -> int:
        """Delete terminal run dirs older than the retention window (PA-12).

        Safety properties (deliberately conservative):
          - Only directories whose meta.json parses AND whose state is
            terminal (completed/failed/blocked) are ever removed.
          - Runs in queued/running state are never touched, no matter how old.
          - Anything without a readable meta.json is skipped (never delete
            unknown dirs).
          - Hard cap of ``max_delete`` deletions per invocation so a first
            sweep on the 648MB backlog is bounded.
          - Age is judged by the meta.json mtime (last write to the record).

        Returns the number of run directories deleted. Never raises on
        individual deletion failures (logged and skipped).
        """
        if not RUNS_DIR.exists():
            return 0

        import datetime as _dt

        cutoff = _dt.datetime.now(_dt.timezone.utc) - _dt.timedelta(days=retention_days)
        deleted = 0

        for run_dir in RUNS_DIR.iterdir():
            if deleted >= max_delete:
                break
            if not run_dir.is_dir() or run_dir.name.startswith("."):
                continue
            meta_path = run_dir / "meta.json"
            if not meta_path.exists():
                continue  # never delete unknown dirs
            try:
                with meta_path.open(encoding="utf-8") as fh:
                    meta = json.load(fh)
                state = meta.get("state", "")
                if state not in TERMINAL_STATES:
                    continue
                mtime = _dt.datetime.fromtimestamp(
                    meta_path.stat().st_mtime, tz=_dt.timezone.utc
                )
                if mtime >= cutoff:
                    continue
                shutil.rmtree(run_dir)
                deleted += 1
            except (OSError, ValueError) as exc:
                logger.warning("prune_expired_runs: skipping %s: %s", run_dir, exc)
                continue

        return deleted

    @staticmethod
    def timeout_stale_runs(max_age_seconds: int = 300) -> list[str]:
        """
        Mark any run stuck in queued/running for longer than max_age_seconds as FAILED.

        PA-17 sweep awareness: a run with a fresh ``heartbeat_at`` (updated by
        RunLedger.touch() at each pipeline stage checkpoint) is ALIVE — a
        long-running pipeline, not a dead thread — and must be skipped even if
        it has been running longer than the threshold. Only runs whose
        heartbeat is absent (legacy runs) or older than the threshold are
        timed out.

        PA-12 lazy GC: this is the only path that already scans the whole
        ledger, so it also serves as the throttled prune trigger — at most
        once per hour (marker file in RUNS_DIR) it prunes expired terminal
        runs with the default retention. The prune is best-effort and fully
        failure-tolerant: it must never break this scan or the GET path that
        drives it.

        Returns list of run_ids that were timed out.
        """
        if not RUNS_DIR.exists():
            return []

        timed_out: list[str] = RunLedger._timeout_scan(max_age_seconds)

        # Throttled lazy GC trigger (PA-12). Opt-in via WAYPOINT_RUN_LEDGER_GC=1
        # so deletion can never happen implicitly against live data (tests hit
        # this sweep path too). Everything here is guarded: a prune failure
        # must never break the GET path that called us.
        try:
            if os.environ.get("WAYPOINT_RUN_LEDGER_GC", "0") == "1" and RunLedger._prune_throttle_due():
                pruned = RunLedger.prune_expired_runs()
                logger.info(
                    "Run-ledger lazy GC pruned %d terminal run dirs (retention trigger)",
                    pruned,
                )
        except Exception as exc:  # noqa: BLE001 — GC must never break the scan
            logger.warning("Run-ledger lazy GC skipped after error: %s", exc)

        return timed_out

    @staticmethod
    def _timeout_scan(max_age_seconds: int) -> list[str]:
        """Heartbeat-aware stale-run scan (PA-17). See timeout_stale_runs."""
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

                # Fresh heartbeat ⇒ alive. Skip regardless of total age.
                heartbeat = meta.get("heartbeat_at")
                if heartbeat:
                    try:
                        heartbeat_dt = _dt.datetime.fromisoformat(heartbeat)
                        heartbeat_age = (now - heartbeat_dt).total_seconds()
                        if heartbeat_age <= max_age_seconds:
                            continue
                    except ValueError:
                        pass  # malformed heartbeat falls through to legacy check

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
                            failure_class=FailureClass.ENVIRONMENT.value,
                            stage=meta.get("stage"),
                        )
                        timed_out.append(run_id)
                    except (ValueError, FileNotFoundError):
                        pass
            except (OSError, ValueError):
                continue

        return timed_out

    # ------------------------------------------------------------------
    # Lazy-GC throttle (PA-12)
    # ------------------------------------------------------------------

    @staticmethod
    def _prune_marker_path() -> Path:
        return RUNS_DIR / _PRUNE_MARKER_NAME

    @staticmethod
    def _prune_throttle_due() -> bool:
        """Return True at most once per _PRUNE_INTERVAL_SECONDS (marker file)."""
        marker = RunLedger._prune_marker_path()

        if marker.exists():
            try:
                last = float(marker.read_text(encoding="utf-8").strip())
                if (datetime.now(timezone.utc).timestamp() - last) < _PRUNE_INTERVAL_SECONDS:
                    return False
            except (OSError, ValueError):
                pass  # unreadable marker → treat as due
        return RunLedger._write_prune_marker()

    @staticmethod
    def _write_prune_marker() -> bool:
        """Atomically write the throttle marker. Failure-tolerant by design."""
        try:
            marker = RunLedger._prune_marker_path()
            RUNS_DIR.mkdir(parents=True, exist_ok=True)
            temp_path = marker.with_name(
                f".{_PRUNE_MARKER_NAME}.{os.getpid()}.{threading.get_ident()}.tmp"
            )
            try:
                with temp_path.open("w", encoding="utf-8") as fh:
                    fh.write(str(datetime.now(timezone.utc).timestamp()))
                os.replace(temp_path, marker)
            finally:
                try:
                    temp_path.unlink()
                except FileNotFoundError:
                    pass
            return True
        except OSError as exc:
            logger.warning("Run-ledger prune marker write failed: %s", exc)
            return False
