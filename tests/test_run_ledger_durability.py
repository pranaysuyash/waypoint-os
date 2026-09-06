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
