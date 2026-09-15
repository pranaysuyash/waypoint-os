"""S-11/N-07/LR-B07 local durability checks for run artifacts.

These checks prove crash-safe publication and local-worker serialization only.
They do not prove a shared volume, replica convergence, backup, or hosted
deployment durability.
"""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import get_context
from pathlib import Path

import pytest


def _emit_event_in_child(runs_dir: str, run_id: str, index: int) -> None:
    """Exercise the same file lock from a separate worker process."""
    import spine_api.run_events as run_events

    run_events.RUNS_DIR = Path(runs_dir)
    run_events.emit(
        run_events.EventType.PIPELINE_STAGE_ENTERED,
        run_id,
        stage_name=f"child-{index}",
    )


@pytest.fixture
def isolated_run_ledger(tmp_path, monkeypatch):
    import spine_api.run_events as run_events
    import spine_api.run_ledger as run_ledger

    runs_dir = tmp_path / "runs"
    monkeypatch.setattr(run_ledger, "RUNS_DIR", runs_dir)
    monkeypatch.setattr(run_ledger, "_run_root", lambda run_id: runs_dir / run_id)
    monkeypatch.setattr(run_ledger, "_meta_path", lambda run_id: runs_dir / run_id / "meta.json")
    monkeypatch.setattr(run_ledger, "_steps_dir", lambda run_id: runs_dir / run_id / "steps")
    monkeypatch.setattr(run_events, "RUNS_DIR", runs_dir)

    def event_run_dir(run_id):
        run_dir = runs_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        return run_dir

    monkeypatch.setattr(run_events, "_run_dir", event_run_dir)
    monkeypatch.setattr(run_events, "_events_file", lambda run_id: runs_dir / run_id / "events.jsonl")
    return runs_dir


def test_failed_atomic_publication_keeps_last_valid_meta(isolated_run_ledger, monkeypatch):
    from spine_api import run_ledger
    from spine_api.run_ledger import RunLedger
    from spine_api.run_state import RunState

    RunLedger.create("atomic-run", None, "discovery", "normal")

    def fail_replace(_source, _destination):
        raise OSError("simulated crash before publication")

    monkeypatch.setattr(run_ledger.os, "replace", fail_replace)
    with pytest.raises(OSError, match="simulated crash"):
        RunLedger.set_state("atomic-run", RunState.RUNNING)

    assert RunLedger.get_meta("atomic-run")["state"] == RunState.QUEUED.value
    assert list((isolated_run_ledger / "atomic-run").glob("*.tmp")) == []


def test_concurrent_event_appends_remain_complete_json_lines(isolated_run_ledger):
    from spine_api.run_events import EventType, emit, get_run_events

    run_id = "event-race"

    def append_event(index: int):
        return emit(EventType.PIPELINE_STAGE_COMPLETED, run_id, stage_name=f"stage-{index}", execution_ms=index)

    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(append_event, range(80)))

    events_path = isolated_run_ledger / run_id / "events.jsonl"
    lines = events_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 80
    assert all(isinstance(json.loads(line), dict) for line in lines)
    assert len(get_run_events(run_id)) == 80


def test_cross_process_event_appends_remain_complete_json_lines(isolated_run_ledger):
    from spine_api.run_events import get_run_events

    run_id = "process-event-race"
    context = get_context("fork")
    workers = [
        context.Process(
            target=_emit_event_in_child,
            args=(str(isolated_run_ledger), run_id, index),
        )
        for index in range(8)
    ]
    for worker in workers:
        worker.start()
    for worker in workers:
        worker.join(timeout=10)
        assert worker.exitcode == 0

    events_path = isolated_run_ledger / run_id / "events.jsonl"
    lines = events_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 8
    assert all(isinstance(json.loads(line), dict) for line in lines)
    assert len(get_run_events(run_id)) == 8


def test_concurrent_state_transition_has_one_winner(isolated_run_ledger):
    from spine_api.run_ledger import RunLedger
    from spine_api.run_state import RunState

    RunLedger.create("transition-race", None, "discovery", "normal")

    def transition():
        try:
            RunLedger.set_state("transition-race", RunState.RUNNING)
            return True
        except ValueError:
            return False

    with ThreadPoolExecutor(max_workers=8) as pool:
        outcomes = list(pool.map(lambda _index: transition(), range(8)))

    assert outcomes.count(True) == 1
    assert RunLedger.get_meta("transition-race")["state"] == RunState.RUNNING.value


# ---------------------------------------------------------------------------
# FND-0226: SQL checkpoint durability + startup reconciliation.
#
# The run ledger's lifecycle truth must live in the same store as the trip
# state. When TRIPSTORE_BACKEND is sql/postgres every lifecycle meta
# transition is STRICTLY mirrored (a mirror failure raises — silent
# divergence is the split-brain this finding forbids), heartbeats/steps
# mirror best-effort, reads fall through to SQL on a disk-cache miss, and
# startup reconciliation marks orphaned queued/running runs INTERRUPTED.
# ---------------------------------------------------------------------------

import os  # noqa: E402
from datetime import datetime, timedelta, timezone  # noqa: E402
from types import SimpleNamespace  # noqa: E402

import spine_api.run_ledger as run_ledger_module  # noqa: E402
from spine_api.run_ledger import RunLedger  # noqa: E402
from spine_api.run_ledger_sql import (  # noqa: E402
    SQLRunCheckpointStore,
    checkpoint_backend_is_sql,
)
from spine_api.run_state import RunState  # noqa: E402


class _MirrorRecorder:
    """Fake SQLRunCheckpointStore double recording mirror calls."""

    def __init__(self, fail_meta: bool = False, fail_step: bool = False):
        self.fail_meta = fail_meta
        self.fail_step = fail_step
        self.meta_calls: list[dict] = []
        self.step_calls: list[tuple] = []
        self.sql_metas: dict[str, dict] = {}

    def mirror_meta(self, meta: dict) -> None:
        if self.fail_meta:
            raise RuntimeError("sql mirror unavailable")
        self.meta_calls.append(dict(meta))
        self.sql_metas[meta["run_id"]] = dict(meta)

    def mirror_step(self, run_id: str, step_name: str, checkpoint: dict) -> None:
        if self.fail_step:
            raise RuntimeError("sql mirror unavailable")
        self.step_calls.append((run_id, step_name))

    def load_meta(self, run_id: str):
        return self.sql_metas.get(run_id)

    def load_step(self, run_id: str, step_name: str):
        return None

    def list_metas(self, trip_id=None, state=None, limit=50):
        return []


def _pin_recorder(monkeypatch, recorder):
    monkeypatch.setattr(run_ledger_module, "_checkpoint_store", lambda: recorder)


def test_checkpoint_backend_env_parsing(monkeypatch):
    for raw in ("sql", "postgres", "POSTGRESQL"):
        monkeypatch.setenv("TRIPSTORE_BACKEND", raw)
        assert checkpoint_backend_is_sql() is True
    monkeypatch.delenv("TRIPSTORE_BACKEND", raising=False)
    assert checkpoint_backend_is_sql() is False
    monkeypatch.setenv("TRIPSTORE_BACKEND", "file")
    assert checkpoint_backend_is_sql() is False


def test_lifecycle_mirrors_reach_sql_store_when_pinned(isolated_run_ledger, monkeypatch):
    monkeypatch.delenv("TRIPSTORE_BACKEND", raising=False)
    recorder = _MirrorRecorder()
    _pin_recorder(monkeypatch, recorder)

    RunLedger.create("mirror-run", "trip-1", "discovery", "normal", agency_id="ag-1")
    RunLedger.set_state("mirror-run", RunState.RUNNING)
    RunLedger.complete("mirror-run", total_ms=12.5)

    states = [m["state"] for m in recorder.meta_calls]
    assert states == ["queued", "running", "completed"]
    assert recorder.meta_calls[-1]["total_ms"] == 12.5


def test_fail_and_block_and_update_mirror(isolated_run_ledger, monkeypatch):
    monkeypatch.delenv("TRIPSTORE_BACKEND", raising=False)
    recorder = _MirrorRecorder()
    _pin_recorder(monkeypatch, recorder)

    RunLedger.create("mirror-run-2", None, "discovery", "normal")
    RunLedger.set_state("mirror-run-2", RunState.RUNNING)
    RunLedger.fail("mirror-run-2", "RunTimeout", "boom", stage="decision")
    assert recorder.meta_calls[-1]["state"] == "failed"
    assert recorder.meta_calls[-1]["failure_class"]

    RunLedger.update_meta("mirror-run-2", trip_id="trip-late")
    assert recorder.meta_calls[-1]["trip_id"] == "trip-late"


def test_lifecycle_mirror_failure_is_strict(isolated_run_ledger, monkeypatch):
    monkeypatch.delenv("TRIPSTORE_BACKEND", raising=False)
    recorder = _MirrorRecorder()
    _pin_recorder(monkeypatch, recorder)

    RunLedger.create("strict-run", None, "discovery", "normal")
    RunLedger.set_state("strict-run", RunState.RUNNING)

    # From here the SQL mirror is down: the next lifecycle transition must
    # surface the failure loudly instead of silently diverging disk vs SQL
    # (the caller — the pipeline — decides how to recover, but it can never
    # be unaware that durability broke).
    recorder.fail_meta = True
    with pytest.raises(RuntimeError, match="sql mirror unavailable"):
        RunLedger.complete("strict-run", total_ms=1.0)
    assert RunLedger.get_meta("strict-run")["state"] == "completed"


def test_heartbeat_and_step_mirrors_are_best_effort(isolated_run_ledger, monkeypatch):
    monkeypatch.delenv("TRIPSTORE_BACKEND", raising=False)
    recorder = _MirrorRecorder()
    _pin_recorder(monkeypatch, recorder)

    RunLedger.create("besteffort-run", None, "discovery", "normal")
    RunLedger.set_state("besteffort-run", RunState.RUNNING)

    # Mirror outage: heartbeats and step artifacts are cache-grade — their
    # mirror failures are logged, never fatal.
    recorder.fail_meta = True
    recorder.fail_step = True
    RunLedger.touch("besteffort-run")  # must not raise
    RunLedger.save_step("besteffort-run", "packet", {"ok": True})  # must not raise
    assert RunLedger.get_meta("besteffort-run")["heartbeat_at"] is not None
    assert RunLedger.get_step("besteffort-run", "packet")["data"] == {"ok": True}


def test_file_backend_performs_no_sql_mirror(isolated_run_ledger, monkeypatch):
    monkeypatch.delenv("TRIPSTORE_BACKEND", raising=False)
    # File backend ⇒ _checkpoint_store() returns None ⇒ no SQL involvement.
    monkeypatch.setattr(run_ledger_module, "_checkpoint_store", lambda: None)
    RunLedger.create("file-run", None, "discovery", "normal")
    RunLedger.set_state("file-run", RunState.RUNNING)
    RunLedger.complete("file-run", total_ms=3.0)
    assert RunLedger.get_meta("file-run")["state"] == "completed"


def test_mark_interrupted_transition_guards(isolated_run_ledger, monkeypatch):
    monkeypatch.delenv("TRIPSTORE_BACKEND", raising=False)

    RunLedger.create("interrupt-run", None, "discovery", "normal")
    RunLedger.set_state("interrupt-run", RunState.RUNNING)
    RunLedger.mark_interrupted("interrupt-run", "startup_reconciliation: test")
    meta = RunLedger.get_meta("interrupt-run")
    assert meta["state"] == "interrupted"
    assert meta["reconciled_reason"].startswith("startup_reconciliation")
    assert meta["completed_at"] is not None

    # Terminal runs can never be clobbered by reconciliation.
    with pytest.raises(ValueError, match="only valid from"):
        RunLedger.mark_interrupted("interrupt-run", "again")


def test_reconcile_marks_orphans_interrupted(isolated_run_ledger, monkeypatch):
    monkeypatch.delenv("TRIPSTORE_BACKEND", raising=False)

    stale = datetime.now(timezone.utc) - timedelta(seconds=3600)
    fresh = datetime.now(timezone.utc)

    for run_id, created in (
        ("orphan-stale", stale),
        ("orphan-fresh", fresh),
    ):
        RunLedger.create(run_id, f"trip-{run_id}", "discovery", "normal")
        RunLedger.set_state(run_id, RunState.RUNNING)
        # Backdate the heartbeat so the stale run is genuinely stale.
        meta = RunLedger.get_meta(run_id)
        meta["heartbeat_at"] = created.isoformat()
        path = isolated_run_ledger / run_id / "meta.json"
        path.write_text(json.dumps(meta), encoding="utf-8")

    rows = [
        SimpleNamespace(
            run_id="orphan-stale", trip_id="trip-orphan-stale",
            state="running", heartbeat_at=stale,
        ),
        SimpleNamespace(
            run_id="orphan-fresh", trip_id="trip-orphan-fresh",
            state="running", heartbeat_at=fresh,
        ),
        # No disk cache (post-deploy cache loss) — SQL-only record.
        SimpleNamespace(
            run_id="orphan-nodisk", trip_id="trip-orphan-nodisk",
            state="queued", heartbeat_at=None,
        ),
    ]
    monkeypatch.setattr(SQLRunCheckpointStore, "_ensure_table", lambda: None)
    monkeypatch.setattr(SQLRunCheckpointStore, "_list_orphan_candidates", lambda: rows)
    monkeypatch.setattr(SQLRunCheckpointStore, "_lease_is_live", lambda trip_id: False)

    # Rehydrate seam: mark_interrupted reads through the (fake) SQL store.
    recorder = _MirrorRecorder()
    recorder.sql_metas["orphan-nodisk"] = {
        "run_id": "orphan-nodisk",
        "trip_id": "trip-orphan-nodisk",
        "state": "queued",
        "stage": "discovery",
        "operating_mode": "normal",
        "created_at": stale.isoformat(),
        "started_at": None,
        "completed_at": None,
        "heartbeat_at": None,
        "total_ms": None,
    }

    monkeypatch.setattr(run_ledger_module, "_checkpoint_store", lambda: recorder)

    reconciled = SQLRunCheckpointStore.reconcile_interrupted_runs(max_heartbeat_age_seconds=300)

    assert set(reconciled) == {"orphan-stale", "orphan-nodisk"}
    assert RunLedger.get_meta("orphan-stale")["state"] == "interrupted"
    assert RunLedger.get_meta("orphan-fresh")["state"] == "running"
    # SQL-only orphan was rehydrated into the disk cache as interrupted.
    assert RunLedger.get_meta("orphan-nodisk")["state"] == "interrupted"
    assert (isolated_run_ledger / "orphan-nodisk" / "meta.json").exists()


def test_reconcile_live_lease_blocks_interruption(isolated_run_ledger, monkeypatch):
    monkeypatch.delenv("TRIPSTORE_BACKEND", raising=False)

    stale = datetime.now(timezone.utc) - timedelta(seconds=3600)
    RunLedger.create("lease-kept", "trip-lease", "discovery", "normal")
    RunLedger.set_state("lease-kept", RunState.RUNNING)

    rows = [
        SimpleNamespace(
            run_id="lease-kept", trip_id="trip-lease",
            state="running", heartbeat_at=stale,
        ),
    ]
    monkeypatch.setattr(SQLRunCheckpointStore, "_ensure_table", lambda: None)
    monkeypatch.setattr(SQLRunCheckpointStore, "_list_orphan_candidates", lambda: rows)
    monkeypatch.setattr(SQLRunCheckpointStore, "_lease_is_live", lambda trip_id: True)

    reconciled = SQLRunCheckpointStore.reconcile_interrupted_runs(max_heartbeat_age_seconds=300)
    assert reconciled == []
    assert RunLedger.get_meta("lease-kept")["state"] == "running"


def test_interrupted_runs_are_gc_eligible(isolated_run_ledger, monkeypatch):
    # .env pins TRIPSTORE_BACKEND=sql session-wide; unit tests must never
    # engage the real SQL checkpoint store.
    monkeypatch.delenv("TRIPSTORE_BACKEND", raising=False)
    monkeypatch.setattr(run_ledger_module, "_checkpoint_store", lambda: None)
    from spine_api.run_ledger import TERMINAL_STATES

    assert "interrupted" in TERMINAL_STATES

    RunLedger.create("old-interrupted", None, "discovery", "normal")
    RunLedger.set_state("old-interrupted", RunState.RUNNING)
    RunLedger.mark_interrupted("old-interrupted", "test")
    # Backdate the meta write so the retention window has passed.
    old_ts = datetime.now(timezone.utc) - timedelta(days=40)
    os.utime(
        isolated_run_ledger / "old-interrupted" / "meta.json",
        (old_ts.timestamp(), old_ts.timestamp()),
    )

    deleted = RunLedger.prune_expired_runs(retention_days=30, max_delete=10)
    assert deleted == 1
    assert RunLedger.get_meta("old-interrupted") is None
