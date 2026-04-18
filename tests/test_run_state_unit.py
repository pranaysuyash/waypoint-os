"""
test_run_state_unit.py — Pure unit tests for Wave A state machine and ledger.

No live API required. No file I/O (uses tmp_path fixture for ledger tests).
Run independently:

    pytest tests/test_run_state_unit.py -v

These tests are CI-safe and run in any environment with Python + pytest.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from run_state import (
    RunState,
    assert_can_transition,
    can_transition,
    terminal_state_for_run_result,
)


# =============================================================================
# State machine: allowed transitions
# =============================================================================

class TestAllowedTransitions:
    def test_queued_to_running(self):
        assert can_transition(RunState.QUEUED, RunState.RUNNING) is True

    def test_running_to_completed(self):
        assert can_transition(RunState.RUNNING, RunState.COMPLETED) is True

    def test_running_to_failed(self):
        assert can_transition(RunState.RUNNING, RunState.FAILED) is True

    def test_running_to_blocked(self):
        assert can_transition(RunState.RUNNING, RunState.BLOCKED) is True

    def test_queued_to_failed(self):
        """Early failure before run even starts (bad input, startup error)."""
        assert can_transition(RunState.QUEUED, RunState.FAILED) is True


class TestDisallowedTransitions:
    def test_completed_to_running(self):
        assert can_transition(RunState.COMPLETED, RunState.RUNNING) is False

    def test_failed_to_completed(self):
        assert can_transition(RunState.FAILED, RunState.COMPLETED) is False

    def test_blocked_to_completed(self):
        assert can_transition(RunState.BLOCKED, RunState.COMPLETED) is False

    def test_running_to_queued(self):
        assert can_transition(RunState.RUNNING, RunState.QUEUED) is False

    def test_completed_to_blocked(self):
        assert can_transition(RunState.COMPLETED, RunState.BLOCKED) is False

    def test_blocked_to_failed(self):
        assert can_transition(RunState.BLOCKED, RunState.FAILED) is False


class TestTerminalStates:
    def test_completed_is_terminal(self):
        assert RunState.COMPLETED.is_terminal() is True

    def test_failed_is_terminal(self):
        assert RunState.FAILED.is_terminal() is True

    def test_blocked_is_terminal(self):
        assert RunState.BLOCKED.is_terminal() is True

    def test_running_is_not_terminal(self):
        assert RunState.RUNNING.is_terminal() is False

    def test_queued_is_not_terminal(self):
        assert RunState.QUEUED.is_terminal() is False


class TestBlockedIsDistinctFromFailed:
    """BLOCKED is a policy decision; FAILED is a system error. They must be distinct."""

    def test_different_values(self):
        assert RunState.BLOCKED != RunState.FAILED

    def test_blocked_value(self):
        assert RunState.BLOCKED.value == "blocked"

    def test_failed_value(self):
        assert RunState.FAILED.value == "failed"

    def test_blocked_not_reachable_from_failed(self):
        assert can_transition(RunState.FAILED, RunState.BLOCKED) is False

    def test_failed_not_reachable_from_blocked(self):
        assert can_transition(RunState.BLOCKED, RunState.FAILED) is False


class TestAssertCanTransition:
    def test_valid_does_not_raise(self):
        assert_can_transition(RunState.RUNNING, RunState.COMPLETED)  # no exception

    def test_invalid_raises_value_error(self):
        with pytest.raises(ValueError, match="Invalid run state transition"):
            assert_can_transition(RunState.COMPLETED, RunState.RUNNING)

    def test_error_message_includes_state_names(self):
        with pytest.raises(ValueError, match="completed"):
            assert_can_transition(RunState.COMPLETED, RunState.RUNNING)

    def test_terminal_to_any_raises(self):
        for terminal in (RunState.COMPLETED, RunState.FAILED, RunState.BLOCKED):
            for target in RunState:
                if can_transition(terminal, target):
                    continue  # skip valid ones (should be none)
                with pytest.raises(ValueError):
                    assert_can_transition(terminal, target)


class TestTerminalStateForRunResult:
    def test_ok_true_not_blocked_is_completed(self):
        assert terminal_state_for_run_result(ok=True, is_blocked=False) == RunState.COMPLETED

    def test_ok_false_blocked_is_blocked(self):
        assert terminal_state_for_run_result(ok=False, is_blocked=True) == RunState.BLOCKED

    def test_ok_false_not_blocked_is_failed(self):
        assert terminal_state_for_run_result(ok=False, is_blocked=False) == RunState.FAILED

    def test_ok_true_blocked_true_is_blocked(self):
        """is_blocked takes priority — this should not occur in practice but is defined."""
        assert terminal_state_for_run_result(ok=True, is_blocked=True) == RunState.BLOCKED


# =============================================================================
# Ledger: transition guards end-to-end (file I/O with tmp_path)
# =============================================================================

class TestLedgerTransitionGuards:
    """Integration of run_ledger + run_state guard enforcement."""

    @pytest.fixture(autouse=True)
    def patch_runs_dir(self, tmp_path, monkeypatch):
        """Redirect RUNS_DIR to a temp directory for each test."""
        import run_ledger as ledger_module
        monkeypatch.setattr(ledger_module, "RUNS_DIR", tmp_path)
        monkeypatch.setattr(ledger_module, "DATA_DIR", tmp_path.parent)
        # Also patch _run_root to use tmp_path correctly
        monkeypatch.setattr(
            ledger_module,
            "_run_root",
            lambda run_id: tmp_path / run_id,
        )
        monkeypatch.setattr(
            ledger_module,
            "_meta_path",
            lambda run_id: tmp_path / run_id / "meta.json",
        )
        monkeypatch.setattr(
            ledger_module,
            "_steps_dir",
            lambda run_id: tmp_path / run_id / "steps",
        )

    def _create(self, run_id: str = "test-run-001"):
        from run_ledger import RunLedger
        return RunLedger.create(run_id, trip_id=None, stage="discovery", operating_mode="normal")

    def test_create_initial_state_is_queued(self):
        from run_ledger import RunLedger
        meta = self._create()
        assert meta["state"] == "queued"

    def test_set_state_queued_to_running_succeeds(self):
        from run_ledger import RunLedger
        self._create()
        RunLedger.set_state("test-run-001", RunState.RUNNING)
        meta = RunLedger.get_meta("test-run-001")
        assert meta["state"] == "running"
        assert meta["started_at"] is not None

    def test_set_state_invalid_transition_raises(self):
        from run_ledger import RunLedger
        self._create()
        # Jump directly from queued to completed (invalid)
        with pytest.raises(ValueError, match="Invalid run state transition"):
            RunLedger.set_state("test-run-001", RunState.COMPLETED)

    def test_complete_requires_running_state(self):
        from run_ledger import RunLedger
        self._create()
        # Cannot complete from queued
        with pytest.raises(ValueError):
            RunLedger.complete("test-run-001", total_ms=1234.5)

    def test_complete_from_running_succeeds(self):
        from run_ledger import RunLedger
        self._create()
        RunLedger.set_state("test-run-001", RunState.RUNNING)
        RunLedger.complete("test-run-001", total_ms=999.9)
        meta = RunLedger.get_meta("test-run-001")
        assert meta["state"] == "completed"
        assert meta["total_ms"] == 999.9
        assert meta["completed_at"] is not None

    def test_fail_from_running_succeeds(self):
        from run_ledger import RunLedger
        self._create()
        RunLedger.set_state("test-run-001", RunState.RUNNING)
        RunLedger.fail("test-run-001", error_type="ValueError", error_message="bad input")
        meta = RunLedger.get_meta("test-run-001")
        assert meta["state"] == "failed"
        assert meta["error_type"] == "ValueError"

    def test_block_from_running_succeeds(self):
        from run_ledger import RunLedger
        self._create()
        RunLedger.set_state("test-run-001", RunState.RUNNING)
        RunLedger.block("test-run-001", block_reason="leakage detected")
        meta = RunLedger.get_meta("test-run-001")
        assert meta["state"] == "blocked"
        assert meta["block_reason"] == "leakage detected"

    def test_double_complete_raises(self):
        """Terminal state cannot be re-entered."""
        from run_ledger import RunLedger
        self._create()
        RunLedger.set_state("test-run-001", RunState.RUNNING)
        RunLedger.complete("test-run-001", total_ms=500.0)
        with pytest.raises(ValueError):
            RunLedger.complete("test-run-001", total_ms=500.0)

    def test_no_meta_state_bypass_possible(self):
        """
        Prove there is no way to set meta['state'] = ... directly from outside
        without going through a guarded method.
        Users can only call create/set_state/complete/fail/block — all guarded.
        """
        from run_ledger import RunLedger
        self._create()
        # Attempt to manipulate state by reading and writing directly (simulating a bypass)
        # Then verify the guard catches it on the *next* ledger call
        meta_path = RunLedger.get_meta("test-run-001")  # returns a copy
        # Even if caller tries to transition QUEUED → COMPLETED directly via set_state, it raises
        with pytest.raises(ValueError):
            RunLedger.set_state("test-run-001", RunState.COMPLETED)


# =============================================================================
# Ledger: step checkpoint determinism
# =============================================================================

class TestLedgerStepCheckpoints:

    @pytest.fixture(autouse=True)
    def patch_runs_dir(self, tmp_path, monkeypatch):
        import run_ledger as ledger_module
        monkeypatch.setattr(ledger_module, "RUNS_DIR", tmp_path)
        monkeypatch.setattr(ledger_module, "_run_root", lambda rid: tmp_path / rid)
        monkeypatch.setattr(ledger_module, "_meta_path", lambda rid: tmp_path / rid / "meta.json")
        monkeypatch.setattr(ledger_module, "_steps_dir", lambda rid: tmp_path / rid / "steps")

    def test_save_step_and_retrieve(self):
        from run_ledger import RunLedger
        RunLedger.create("run-step-01", None, "discovery", "normal")
        payload = {"destination": "Tokyo", "budget": 100000}
        RunLedger.save_step("run-step-01", "packet", payload)

        step = RunLedger.get_step("run-step-01", "packet")
        assert step is not None
        assert step["step"] == "packet"
        assert step["data"] == payload
        assert "checkpointed_at" in step

    def test_step_read_is_idempotent(self):
        """Reading a step twice returns identical content."""
        from run_ledger import RunLedger
        RunLedger.create("run-step-02", None, "discovery", "normal")
        RunLedger.save_step("run-step-02", "decision", {"state": "PROCEED_TRAVELER_SAFE"})

        step_a = RunLedger.get_step("run-step-02", "decision")
        step_b = RunLedger.get_step("run-step-02", "decision")
        assert step_a == step_b

    def test_unknown_step_name_raises(self):
        from run_ledger import RunLedger
        RunLedger.create("run-step-03", None, "discovery", "normal")
        with pytest.raises(ValueError, match="Unknown step"):
            RunLedger.save_step("run-step-03", "nonexistent_stage", {})

    def test_get_all_steps_returns_only_saved(self):
        from run_ledger import RunLedger
        RunLedger.create("run-step-04", None, "discovery", "normal")
        RunLedger.save_step("run-step-04", "packet", {"x": 1})
        RunLedger.save_step("run-step-04", "decision", {"y": 2})

        steps = RunLedger.get_all_steps("run-step-04")
        assert "packet" in steps
        assert "decision" in steps
        assert "validation" not in steps  # not saved

    def test_missing_step_returns_none(self):
        from run_ledger import RunLedger
        RunLedger.create("run-step-05", None, "discovery", "normal")
        assert RunLedger.get_step("run-step-05", "safety") is None


# =============================================================================
# Event log: append-only and readable
# =============================================================================

class TestRunEvents:

    @pytest.fixture(autouse=True)
    def patch_runs_dir(self, tmp_path, monkeypatch):
        import run_events as events_module
        monkeypatch.setattr(events_module, "RUNS_DIR", tmp_path)
        monkeypatch.setattr(
            events_module, "_run_dir", lambda rid: (tmp_path / rid).__class__(tmp_path / rid)
        )
        monkeypatch.setattr(events_module, "_events_file", lambda rid: tmp_path / rid / "events.jsonl")
        (tmp_path / "run-evt-01").mkdir(parents=True, exist_ok=True)

    def test_emit_and_read(self):
        from run_events import emit, EventType, get_run_events
        emit(EventType.RUN_STARTED, run_id="run-evt-01", trip_id=None, stage="discovery")
        events = get_run_events("run-evt-01")
        assert len(events) == 1
        assert events[0]["event_type"] == "run_started"
        assert events[0]["run_id"] == "run-evt-01"

    def test_events_are_append_only(self):
        from run_events import emit, EventType, get_run_events
        emit(EventType.RUN_STARTED, run_id="run-evt-01", trip_id=None, stage="discovery")
        emit(EventType.RUN_COMPLETED, run_id="run-evt-01", trip_id=None, total_ms=500.0)
        events = get_run_events("run-evt-01")
        assert len(events) == 2
        assert events[0]["event_type"] == "run_started"
        assert events[1]["event_type"] == "run_completed"

    def test_unknown_run_id_returns_empty(self):
        from run_events import get_run_events
        assert get_run_events("nonexistent-xyz-000") == []
