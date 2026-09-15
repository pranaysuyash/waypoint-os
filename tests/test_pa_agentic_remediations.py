"""PA-03/04/07/12/17/20/21/27 remediation tests (persona audit 2026-09-06).

All run-ledger tests use a tmp RUNS_DIR — the GC/prune machinery is never
allowed to touch the repository's live data/runs store.
"""

from __future__ import annotations

import os
from contextlib import nullcontext
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

import spine_api.run_ledger as run_ledger_module
from spine_api.failure_taxonomy import (
    ESCALATE_ONLY_CLASSES,
    NEVER_REQUEUE_CLASSES,
    REQUEUEABLE_CLASSES,
    FailureClass,
    classify_failure,
    recovery_action_for,
)
from spine_api.run_ledger import RunLedger
from spine_api.run_state import RunState


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def isolated_run_ledger(tmp_path, monkeypatch):
    """Point the real RunLedger at a tmp directory (never live data)."""
    runs_dir = tmp_path / "runs"
    monkeypatch.setattr(run_ledger_module, "RUNS_DIR", runs_dir)
    monkeypatch.setattr(
        run_ledger_module,
        "_run_root",
        lambda run_id: runs_dir / run_id,
    )
    monkeypatch.setattr(
        run_ledger_module,
        "_meta_path",
        lambda run_id: runs_dir / run_id / "meta.json",
    )
    monkeypatch.setattr(
        run_ledger_module,
        "_steps_dir",
        lambda run_id: runs_dir / run_id / "steps",
    )
    return runs_dir


def _age_meta(runs_dir, run_id, days: float) -> None:
    """Backdate a run's meta.json mtime for retention tests."""
    meta_path = runs_dir / run_id / "meta.json"
    old = (datetime.now(timezone.utc) - timedelta(days=days)).timestamp()
    os.utime(meta_path, (old, old))


# ---------------------------------------------------------------------------
# PA-03 — determinism default
# ---------------------------------------------------------------------------


class TestPA03HybridDefault:
    def test_default_is_off_when_env_unset(self, monkeypatch):
        from src.intake.decision import _is_hybrid_engine_enabled, _reset_hybrid_engine

        monkeypatch.delenv("USE_HYBRID_DECISION_ENGINE", raising=False)
        _reset_hybrid_engine()
        try:
            assert _is_hybrid_engine_enabled() is False
        finally:
            _reset_hybrid_engine()

    def test_env_still_wins_when_set(self, monkeypatch):
        from src.intake.decision import _is_hybrid_engine_enabled, _reset_hybrid_engine

        monkeypatch.setenv("USE_HYBRID_DECISION_ENGINE", "1")
        _reset_hybrid_engine()
        try:
            assert _is_hybrid_engine_enabled() is True
        finally:
            _reset_hybrid_engine()

    def test_enabled_flag_emits_one_time_warning(self, monkeypatch, caplog):
        import logging

        import src.intake.decision as decision_module

        monkeypatch.setenv("USE_HYBRID_DECISION_ENGINE", "1")
        decision_module._HYBRID_ENABLED_WARNING_EMITTED = False
        _reset = decision_module._reset_hybrid_engine
        _reset()
        try:
            with caplog.at_level(logging.WARNING, logger="src.intake.decision"):
                decision_module._is_hybrid_engine_enabled()
                decision_module._is_hybrid_engine_enabled()
            warnings = [
                r for r in caplog.records
                if "Hybrid decision engine ENABLED" in r.getMessage()
            ]
            assert len(warnings) == 1
            assert "PA-03" in warnings[0].getMessage()
        finally:
            _reset()

    def test_disabled_flag_emits_no_warning(self, monkeypatch, caplog):
        import logging

        import src.intake.decision as decision_module

        monkeypatch.delenv("USE_HYBRID_DECISION_ENGINE", raising=False)
        decision_module._HYBRID_ENABLED_WARNING_EMITTED = False
        decision_module._reset_hybrid_engine()
        try:
            with caplog.at_level(logging.WARNING, logger="src.intake.decision"):
                decision_module._is_hybrid_engine_enabled()
            assert not [r for r in caplog.records if "Hybrid decision engine ENABLED" in r.getMessage()]
        finally:
            decision_module._reset_hybrid_engine()

    def test_factory_default_agrees_off(self, monkeypatch):
        from src.decision.hybrid_engine import create_hybrid_engine

        monkeypatch.delenv("USE_HYBRID_DECISION_ENGINE", raising=False)
        engine = create_hybrid_engine()
        assert engine.enable_llm is False

    def test_compose_and_fly_no_longer_pin_hybrid_on(self):
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        fly = open(os.path.join(repo_root, "fly.toml"), encoding="utf-8").read()
        compose = open(os.path.join(repo_root, "docker-compose.yml"), encoding="utf-8").read()
        assert "USE_HYBRID_DECISION_ENGINE = \"1\"" not in fly
        assert "USE_HYBRID_DECISION_ENGINE:-1" not in compose
        assert "USE_HYBRID_DECISION_ENGINE:-0" in compose

    def test_no_dockerfile_bakes_hybrid_on(self):
        # ADR-008 §7 item 2 (Addendum 9): zero implicit defaults. A Dockerfile
        # ENV silently overrides the code default for every envelope built from
        # it (the main image made Fly prod hybrid-ON while fly.toml's comment
        # claimed deterministic — the exact accident this contract ends).
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        for name in ("Dockerfile", "Dockerfile.spine_api"):
            with open(os.path.join(repo_root, name), encoding="utf-8") as fh:
                content = fh.read()
            assert "USE_HYBRID_DECISION_ENGINE=1" not in content, (
                f"{name} bakes USE_HYBRID_DECISION_ENGINE=1 — prod envelopes "
                "must declare 0 explicitly (hybrid opt-in is envelope-level, "
                "never image-level)."
            )
            assert "USE_HYBRID_DECISION_ENGINE=0" in content, (
                f"{name} must declare USE_HYBRID_DECISION_ENGINE explicitly."
            )


# ---------------------------------------------------------------------------
# PA-07 — failure taxonomy
# ---------------------------------------------------------------------------


class TestPA07Taxonomy:
    def test_timeout_is_environment(self):
        assert classify_failure(TimeoutError("too slow")) == FailureClass.ENVIRONMENT.value

    def test_timeout_message_is_environment(self):
        assert classify_failure(RuntimeError("request timed out after 30s")) == (
            FailureClass.ENVIRONMENT.value
        )

    def test_database_error_is_state(self):
        import sqlite3

        assert classify_failure(sqlite3.OperationalError("db locked")) == FailureClass.STATE.value

    def test_tripstore_message_is_state(self):
        assert classify_failure(RuntimeError("TripStore update failed")) == FailureClass.STATE.value

    def test_strict_leakage_is_policy_block(self):
        from src.intake.safety import StrictLeakageViolation

        assert classify_failure(StrictLeakageViolation("forbidden concept")) == (
            FailureClass.POLICY_BLOCK.value
        )

    def test_plain_assertion_is_verification(self):
        assert classify_failure(AssertionError("postcondition violated")) == (
            FailureClass.VERIFICATION.value
        )

    def test_llm_error_is_model(self):
        class FakeLLMError(Exception):
            pass

        assert classify_failure(FakeLLMError("generation failed")) == FailureClass.MODEL.value

    def test_connection_error_is_tool(self):
        assert classify_failure(ConnectionError("peer reset")) == FailureClass.TOOL.value

    def test_permission_error_is_authority(self):
        assert classify_failure(PermissionError("agency mismatch")) == FailureClass.AUTHORITY.value

    def test_unknown_is_unclassified(self):
        assert classify_failure(RuntimeError("boom")) == FailureClass.UNCLASSIFIED.value
        assert classify_failure(None) == FailureClass.UNCLASSIFIED.value

    def test_recovery_action_mapping(self):
        assert recovery_action_for("tool") == "requeue"
        assert recovery_action_for("model") == "requeue"
        assert recovery_action_for("environment") == "requeue"
        assert recovery_action_for("state") == "escalate"
        assert recovery_action_for("verification") == "escalate"
        assert recovery_action_for("authority") == "escalate"
        assert recovery_action_for("policy_block") == "never_requeue"
        assert recovery_action_for("unclassified") == "default"
        assert recovery_action_for(None) == "default"

    def test_class_sets_are_consistent(self):
        assert REQUEUEABLE_CLASSES.isdisjoint(ESCALATE_ONLY_CLASSES)
        assert NEVER_REQUEUE_CLASSES == {FailureClass.POLICY_BLOCK.value}


class TestPA07LedgerRoundtrip:
    def test_fail_records_class_and_stage(self, isolated_run_ledger):
        RunLedger.create("run-cls", "trip-1", "decision", "normal_intake")
        RunLedger.set_state("run-cls", RunState.RUNNING)
        RunLedger.fail(
            "run-cls",
            error_type="OperationalError",
            error_message="db went away",
            failure_class="state",
            stage="decision",
        )
        meta = RunLedger.get_meta("run-cls")
        assert meta["state"] == "failed"
        assert meta["failure_class"] == "state"
        assert meta["stage_at_failure"] == "decision"
        assert meta["error_type"] == "OperationalError"  # raw type preserved

    def test_fail_default_keeps_backward_compat_shape(self, isolated_run_ledger):
        RunLedger.create("run-legacy", None, "discovery", "normal_intake")
        RunLedger.set_state("run-legacy", RunState.RUNNING)
        RunLedger.fail("run-legacy", "ValueError", "bad input")  # positional, legacy
        meta = RunLedger.get_meta("run-legacy")
        assert meta["state"] == "failed"
        assert meta["failure_class"] == "unclassified"
        assert meta["stage_at_failure"] is None

    def test_latest_run_for_trip(self, isolated_run_ledger):
        assert RunLedger.latest_run_for_trip("trip-x") is None
        RunLedger.create("run-a", "trip-x", "discovery", "normal_intake")
        RunLedger.create("run-b", "trip-x", "decision", "normal_intake")
        latest = RunLedger.latest_run_for_trip("trip-x")
        assert latest is not None
        assert latest["run_id"] == "run-b"


class TestPA07RecoveryBranch:
    @dataclass
    class _Trip:
        id: str
        stage: str
        updated_at: datetime

    class _TripRepo:
        def __init__(self, trips):
            self._trips = trips
            self.review_updates = []

        def list_active(self):
            return self._trips

        def set_review_status(self, trip_id, status):
            self.review_updates.append((trip_id, status))

    def _agent(self, repo, monkeypatch, failure_meta):
        from src.agents.recovery_agent import RecoveryAgent

        monkeypatch.setenv("RECOVERY_STUCK_INTAKE_H", "1")
        if failure_meta is None:
            monkeypatch.setattr(
                "src.agents.recovery_agent._get_latest_run_meta",
                lambda trip_id: None,
            )
        else:
            monkeypatch.setattr(
                "src.agents.recovery_agent._get_latest_run_meta",
                lambda trip_id: failure_meta,
            )
        return RecoveryAgent(
            interval_seconds=1,
            audit_store=None,
            trip_repo=repo,
            requeue_port=None,  # disabled → requeue path not enabled
        )

    def _stuck_trip(self, trip_id="t-state"):
        return self._Trip(
            id=trip_id,
            stage="intake",
            updated_at=datetime.now(timezone.utc) - timedelta(hours=5),
        )

    def test_state_failure_escalates_without_requeue(self, monkeypatch):
        repo = self._TripRepo([self._stuck_trip("t-state")])
        agent = self._agent(repo, monkeypatch, {"state": "failed", "failure_class": "state"})
        results = agent.run_once()
        assert len(results) == 1
        assert results[0].action == "escalate"
        assert "failure_class=state" in results[0].reason
        assert repo.review_updates == [("t-state", "escalated")]

    def test_policy_block_never_requeues(self, monkeypatch):
        repo = self._TripRepo([self._stuck_trip("t-policy")])
        agent = self._agent(repo, monkeypatch, {"state": "failed", "failure_class": "policy_block"})
        results = agent.run_once()
        assert results[0].action == "escalate"
        assert "never requeued" in results[0].reason

    def test_tool_failure_keeps_requeue_ladder(self, monkeypatch):
        # requeue disabled → even a tool-class run escalates via the ladder,
        # but the branch must NOT inject the class-specific escalate reason.
        repo = self._TripRepo([self._stuck_trip("t-tool")])
        agent = self._agent(repo, monkeypatch, {"state": "failed", "failure_class": "tool"})
        results = agent.run_once()
        assert results[0].action == "escalate"  # ladder fallback (port disabled)
        assert "failure_class=" not in results[0].reason

    def test_no_failed_run_uses_existing_ladder(self, monkeypatch):
        repo = self._TripRepo([self._stuck_trip("t-plain")])
        agent = self._agent(repo, monkeypatch, None)
        results = agent.run_once()
        assert results[0].action == "escalate"  # port disabled fallback
        assert "failure_class=" not in results[0].reason


# ---------------------------------------------------------------------------
# PA-12 — run-ledger GC
# ---------------------------------------------------------------------------


class TestPA12Prune:
    def _make_run(self, run_id, state, trip_id=None):
        RunLedger.create(run_id, trip_id, "discovery", "normal_intake")
        if state == "failed":
            RunLedger.set_state(run_id, RunState.RUNNING)
            RunLedger.fail(run_id, "E", "m")
        elif state == "blocked":
            RunLedger.set_state(run_id, RunState.RUNNING)
            RunLedger.block(run_id, "leak")
        elif state == "completed":
            RunLedger.set_state(run_id, RunState.RUNNING)
            RunLedger.complete(run_id, total_ms=1.0)

    def test_prune_deletes_only_old_terminal_runs(self, isolated_run_ledger):
        self._make_run("old-completed", "completed")
        self._make_run("new-completed", "completed")
        self._make_run("old-running", "queued")  # still queued = never touched
        self._make_run("old-failed", "failed")
        (isolated_run_ledger / "no-meta-dir").mkdir()
        (isolated_run_ledger / "no-meta-dir" / "junk.txt").write_text("keep?")
        _age_meta(isolated_run_ledger, "old-completed", days=40)
        _age_meta(isolated_run_ledger, "old-failed", days=40)
        _age_meta(isolated_run_ledger, "old-running", days=400)
        # no-meta-dir has no meta.json at all — prune must skip it regardless.

        deleted = RunLedger.prune_expired_runs(retention_days=30, max_delete=500)

        assert deleted == 2
        assert not (isolated_run_ledger / "old-completed").exists()
        assert not (isolated_run_ledger / "old-failed").exists()
        assert (isolated_run_ledger / "new-completed").exists()
        assert (isolated_run_ledger / "old-running").exists()
        assert (isolated_run_ledger / "no-meta-dir").exists()

    def test_prune_respects_max_delete_cap(self, isolated_run_ledger):
        for index in range(5):
            run_id = f"cap-{index}"
            self._make_run(run_id, "completed")
            _age_meta(isolated_run_ledger, run_id, days=60)

        deleted = RunLedger.prune_expired_runs(retention_days=30, max_delete=3)

        assert deleted == 3
        remaining = [p.name for p in isolated_run_ledger.iterdir() if p.is_dir()]
        assert len(remaining) == 2

    def test_lazy_trigger_is_opt_in(self, isolated_run_ledger, monkeypatch):
        """Default: the sweep must never prune — live data safety."""
        self._make_run("old-run", "completed")
        _age_meta(isolated_run_ledger, "old-run", days=400)
        monkeypatch.delenv("WAYPOINT_RUN_LEDGER_GC", raising=False)

        RunLedger.timeout_stale_runs(max_age_seconds=300)

        assert (isolated_run_ledger / "old-run").exists()
        assert not (isolated_run_ledger / ".last_prune").exists()

    def test_lazy_trigger_runs_once_per_interval(self, isolated_run_ledger, monkeypatch):
        self._make_run("old-run", "completed")
        _age_meta(isolated_run_ledger, "old-run", days=400)
        monkeypatch.setenv("WAYPOINT_RUN_LEDGER_GC", "1")

        RunLedger.timeout_stale_runs(max_age_seconds=300)
        assert not (isolated_run_ledger / "old-run").exists()
        assert (isolated_run_ledger / ".last_prune").exists()

        # Second call within the hour: throttle marker prevents re-prune work.
        self._make_run("old-run-2", "completed")
        _age_meta(isolated_run_ledger, "old-run-2", days=400)
        RunLedger.timeout_stale_runs(max_age_seconds=300)
        assert (isolated_run_ledger / "old-run-2").exists()

        # Force the marker stale → prune due again.
        marker = isolated_run_ledger / ".last_prune"
        marker.write_text(str(0.0), encoding="utf-8")
        RunLedger.timeout_stale_runs(max_age_seconds=300)
        assert not (isolated_run_ledger / "old-run-2").exists()


# ---------------------------------------------------------------------------
# PA-17 — heartbeat, sweep awareness, completion reconciliation
# ---------------------------------------------------------------------------


class TestPA17HeartbeatAndSweep:
    def test_touch_writes_fresh_heartbeat(self, isolated_run_ledger):
        RunLedger.create("run-hb", None, "discovery", "normal_intake")
        assert "heartbeat_at" not in RunLedger.get_meta("run-hb")
        RunLedger.touch("run-hb")
        assert RunLedger.get_meta("run-hb")["heartbeat_at"] is not None

    def test_sweep_skips_fresh_heartbeat_run(self, isolated_run_ledger):
        RunLedger.create("run-alive", None, "discovery", "normal_intake")
        RunLedger.set_state("run-alive", RunState.RUNNING)
        RunLedger.touch("run-alive")
        # Backdate created_at far beyond the threshold; heartbeat stays fresh.
        meta = RunLedger.get_meta("run-alive")
        stale_time = datetime.now(timezone.utc) - timedelta(hours=4)
        meta["created_at"] = stale_time.isoformat()
        run_ledger_module._atomic_write_json(
            run_ledger_module._meta_path("run-alive"), meta
        )

        timed_out = RunLedger.timeout_stale_runs(max_age_seconds=300)

        assert timed_out == []
        assert RunLedger.get_meta("run-alive")["state"] == "running"

    def test_sweep_times_out_stale_heartbeat_run(self, isolated_run_ledger):
        RunLedger.create("run-dead", None, "decision", "normal_intake")
        RunLedger.set_state("run-dead", RunState.RUNNING)
        RunLedger.touch("run-dead")
        meta = RunLedger.get_meta("run-dead")
        old = (datetime.now(timezone.utc) - timedelta(hours=4)).isoformat()
        meta["heartbeat_at"] = old
        meta["created_at"] = old
        run_ledger_module._atomic_write_json(
            run_ledger_module._meta_path("run-dead"), meta
        )

        timed_out = RunLedger.timeout_stale_runs(max_age_seconds=300)

        assert timed_out == ["run-dead"]
        sweep_meta = RunLedger.get_meta("run-dead")
        assert sweep_meta["state"] == "failed"
        # The sweep itself classifies timeouts as environment faults (PA-07).
        assert sweep_meta["failure_class"] == "environment"
        assert sweep_meta["stage_at_failure"] == "decision"

    def test_sweep_times_out_legacy_run_without_heartbeat(self, isolated_run_ledger):
        RunLedger.create("run-legacy", None, "discovery", "normal_intake")
        RunLedger.set_state("run-legacy", RunState.RUNNING)
        meta = RunLedger.get_meta("run-legacy")
        meta["created_at"] = (
            datetime.now(timezone.utc) - timedelta(hours=4)
        ).isoformat()
        run_ledger_module._atomic_write_json(
            run_ledger_module._meta_path("run-legacy"), meta
        )

        timed_out = RunLedger.timeout_stale_runs(max_age_seconds=300)

        assert timed_out == ["run-legacy"]

    def test_complete_after_timeout_reconciles_failed_run(self, isolated_run_ledger):
        RunLedger.create("run-race", "trip-9", "strategy", "normal_intake")
        RunLedger.set_state("run-race", RunState.RUNNING)
        RunLedger.fail("run-race", "RunTimeout", "sweep raced the thread")

        RunLedger.complete_after_timeout("run-race", total_ms=123.4)

        meta = RunLedger.get_meta("run-race")
        assert meta["state"] == "completed"
        assert meta["recovered_after_timeout"] is True
        assert meta["total_ms"] == 123.4

    def test_complete_after_timeout_only_from_failed(self, isolated_run_ledger):
        RunLedger.create("run-live", None, "discovery", "normal_intake")
        RunLedger.set_state("run-live", RunState.RUNNING)
        with pytest.raises(ValueError, match="only valid from 'failed'"):
            RunLedger.complete_after_timeout("run-live")

    def test_state_machine_still_rejects_other_illegal_transitions(
        self, isolated_run_ledger
    ):
        RunLedger.create("run-term", None, "discovery", "normal_intake")
        RunLedger.set_state("run-term", RunState.RUNNING)
        RunLedger.complete("run-term", total_ms=1.0)
        with pytest.raises(ValueError, match="Invalid run state transition"):
            RunLedger.set_state("run-term", RunState.FAILED)


# ---------------------------------------------------------------------------
# PA-04 — decision evidence on the production trip timeline
# ---------------------------------------------------------------------------


def _pipeline_harness(
    *,
    run_spine_once_fn,
    run_ledger,
    audit_store,
    save_processed_trip=None,
    draft_store=None,
):
    import spine_api.services.pipeline_execution_service as svc

    captured = {"audit": audit_store, "ledger": run_ledger}
    svc.execute_spine_pipeline(
        run_id="run-ev",
        request_dict={
            "raw_note": "test",
            "stage": "discovery",
            "operating_mode": "normal_intake",
            "strict_leakage": False,
            "retention_consent": True,
            "scenario_id": None,
        },
        agency_id="agency-1",
        user_id="user-1",
        build_envelopes=lambda _payload: [],
        load_fixture_expectations=lambda _scenario_id: None,
        to_dict=lambda obj: obj if isinstance(obj, dict) else getattr(obj, "__dict__", obj),
        close_inherited_lock_fds=lambda: None,
        save_processed_trip=save_processed_trip or MagicMock(return_value="trip-ev-1"),
        trip_store=SimpleNamespace(get_trip=MagicMock(return_value={})),
        audit_store=audit_store,
        run_spine_once_fn=run_spine_once_fn,
        logger=MagicMock(),
        otel_tracer=SimpleNamespace(
            start_as_current_span=lambda _name: nullcontext(
                SimpleNamespace(set_attribute=lambda *_a, **_k: None)
            )
        ),
        run_ledger=run_ledger,
        run_state_running="running",
        draft_store=draft_store or SimpleNamespace(
            get=MagicMock(return_value=None),
            update_run_state=MagicMock(),
        ),
        agency_settings_store=SimpleNamespace(load=MagicMock(return_value={})),
        build_live_checker_signals_fn=lambda _packet, _raw: None,
        emit_run_started_fn=MagicMock(),
        emit_run_completed_fn=MagicMock(),
        emit_run_failed_fn=MagicMock(),
        emit_run_blocked_fn=MagicMock(),
        emit_stage_entered_fn=MagicMock(),
        emit_stage_completed_fn=MagicMock(),
    )
    return captured


class _CapturingAudit:
    def __init__(self):
        self.events = []

    def log_event(self, event_type, user_id, details):
        self.events.append(
            {"event_type": event_type, "user_id": user_id, "details": details}
        )
        return {"event_type": event_type}


class _FakeLedger:
    def __init__(self, meta=None):
        self.state = dict(meta or {"draft_id": None})
        self.fail_calls = []

    def set_state(self, run_id, state):
        _ = (run_id, state)

    def get_meta(self, run_id):
        _ = run_id
        return dict(self.state)

    def touch(self, run_id):
        _ = run_id

    def save_step(self, run_id, step, payload):
        _ = (run_id, step, payload)

    def get_all_steps(self, run_id):
        _ = run_id
        return {}

    def update_meta(self, run_id, **kwargs):
        self.state.update(kwargs)

    def complete(self, run_id, total_ms):
        _ = (run_id, total_ms)

    def block(self, run_id, block_reason):
        _ = (run_id, block_reason)

    def fail(self, run_id, error_type, error_message, failure_class="unclassified", stage=None):
        self.fail_calls.append(
            {"run_id": run_id, "error_type": error_type, "failure_class": failure_class, "stage": stage}
        )


def _successful_spine_result():
    return SimpleNamespace(
        packet=SimpleNamespace(packet_id="packet-ev-1"),
        validation=SimpleNamespace(is_valid=True),
        decision=SimpleNamespace(
            decision_state="QUOTE_READY",
            hard_blockers=[],
            soft_blockers=["seasonality_unknown"],
            confidence=SimpleNamespace(
                overall=0.82,
                data_quality=0.9,
                judgment_confidence=0.8,
                commercial_confidence=0.7,
            ),
            rationale={
                "autonomy": {"reasons": ["rule hit: normal_intake"]},
                "budget_feasibility": {"margin_risk": "low"},
            },
        ),
        strategy=SimpleNamespace(),
        autonomy_outcome=SimpleNamespace(
            raw_verdict="AUTO_PROCEED",
            effective_action="proceed",
            approval_required=False,
            rule_source="default_rule_policy",
        ),
        leakage_result={"leaks": [], "is_safe": True},
    )


class TestPA04DecisionEvidence:
    def test_success_path_writes_spine_decision_with_real_trip_id(self):
        audit = _CapturingAudit()
        ledger = _FakeLedger()
        _pipeline_harness(
            run_spine_once_fn=lambda **_kwargs: _successful_spine_result(),
            run_ledger=ledger,
            audit_store=audit,
        )

        decision_events = [
            e for e in audit.events if e["event_type"] == "spine_decision"
        ]
        assert len(decision_events) == 1
        details = decision_events[0]["details"]
        # The REAL saved trip id — not packet.packet_id (the old id mismatch).
        assert details["trip_id"] == "trip-ev-1"
        assert details["run_id"] == "run-ev"
        assert details["nb01"] == {"gate": "intake_completion", "outcome": "pass"}
        assert details["nb02"]["raw_verdict"] == "AUTO_PROCEED"
        assert details["nb02"]["effective_action"] == "proceed"
        assert details["nb02"]["approval_required"] is False
        assert details["nb02"]["rule_source"] == "default_rule_policy"
        assert details["rationale"]["hard_blockers"] == []
        assert details["rationale"]["soft_blockers"] == ["seasonality_unknown"]
        assert details["rationale"]["confidence"]["overall"] == 0.82
        assert details["rationale"]["feasibility"] == {"margin_risk": "low"}

    def test_escalate_path_writes_spine_decision_for_incomplete_trip(self):
        audit = _CapturingAudit()
        ledger = _FakeLedger()
        escalate_result = SimpleNamespace(
            packet=SimpleNamespace(packet_id="packet-ev-2"),
            validation=SimpleNamespace(is_valid=False),
            decision=SimpleNamespace(decision_state="STOP_NEEDS_REVIEW"),
            strategy=SimpleNamespace(),
            leakage_result={"leaks": [], "is_safe": True},
            early_exit=True,
            early_exit_reason="Trip details are incomplete.",
        )
        _pipeline_harness(
            run_spine_once_fn=lambda **_kwargs: escalate_result,
            run_ledger=ledger,
            audit_store=audit,
            save_processed_trip=MagicMock(return_value="trip-ev-incomplete"),
        )

        decision_events = [
            e for e in audit.events if e["event_type"] == "spine_decision"
        ]
        assert len(decision_events) == 1
        details = decision_events[0]["details"]
        assert details["trip_id"] == "trip-ev-incomplete"
        assert details["nb01"]["outcome"] == "escalate"
        assert details["decision_state"] == "STOP_NEEDS_REVIEW"


# ---------------------------------------------------------------------------
# PA-20 — cost correlation
# ---------------------------------------------------------------------------


class TestPA20UsageCorrelation:
    def _reservation_kwargs(self):
        return dict(
            request_id="req-1",
            agency_id="agency-1",
            model="gemini-flash",
            feature="hybrid_engine",
            estimated_cost=0.10,
            hourly_limit=100,
            model_hourly_limit=None,
            daily_budget=10.0,
            budget_mode="block",
            warning_thresholds=[0.5, 0.8],
            now_func=datetime.now,
        )

    def test_inmemory_record_carries_correlation(self):
        from src.llm.usage_store import (
            InMemoryUsageStore,
            clear_usage_context,
            set_usage_context,
        )

        store = InMemoryUsageStore()
        clear_usage_context()
        set_usage_context(run_id="run-42", trip_id=None)
        try:
            # InMemoryUsageStore returns the reservation dict directly.
            reservation = store.check_and_reserve(**self._reservation_kwargs())
            event = store.get_event(reservation["event_id"])
            metadata = event["metadata"]
            assert metadata["correlation"]["run_id"] == "run-42"
            assert metadata["correlation"]["trip_id"] is None
            # PA-20 Wave 2: the real columns carry the same correlation.
            assert event["run_id"] == "run-42"
            assert event["trip_id"] is None

            # finalize (the record_call sink) re-merges — trip id lands late.
            set_usage_context(run_id="run-42", trip_id="trip-42")
            store.finalize_reservation(
                event_id=reservation["event_id"], actual_cost=0.12, status="completed"
            )
            event = store.get_event(reservation["event_id"])
            assert event["metadata"]["correlation"] == {
                "run_id": "run-42",
                "trip_id": "trip-42",
            }
            assert event["run_id"] == "run-42"
            assert event["trip_id"] == "trip-42"
        finally:
            clear_usage_context()

    def test_sqlite_record_carries_correlation(self, tmp_path):
        from src.llm.usage_store import LLMUsageStore, clear_usage_context, set_usage_context

        store = LLMUsageStore(db_path=tmp_path / "usage.db")
        set_usage_context(run_id="run-sql", trip_id="trip-sql")
        try:
            allowed, reservation = store.check_and_reserve(**self._reservation_kwargs())
            assert allowed
            event = store.get_event(reservation["event_id"])
            assert event["metadata"]["correlation"] == {
                "run_id": "run-sql",
                "trip_id": "trip-sql",
            }
            # PA-20 Wave 2: the real columns carry the same correlation.
            assert event["run_id"] == "run-sql"
            assert event["trip_id"] == "trip-sql"
        finally:
            clear_usage_context()

    def test_no_context_writes_no_correlation(self):
        from src.llm.usage_store import InMemoryUsageStore, clear_usage_context

        store = InMemoryUsageStore()
        clear_usage_context()
        reservation = store.check_and_reserve(**self._reservation_kwargs())
        event = store.get_event(reservation["event_id"])
        assert event["metadata_json"] is None
        # PA-20 Wave 2: no context → NULL correlation columns.
        assert event.get("run_id") is None
        assert event.get("trip_id") is None

    def test_get_events_for_run_roundtrip(self, tmp_path):
        """PA-20 Wave 2: run-scoped query over the real run_id column."""
        from src.llm.usage_store import (
            InMemoryUsageStore,
            LLMUsageStore,
            clear_usage_context,
            set_usage_context,
        )

        for store in (InMemoryUsageStore(), LLMUsageStore(db_path=tmp_path / "usage.db")):
            # InMemory returns the reservation dict directly; SQLite returns
            # (allowed, reservation) — normalize to (allowed, reservation).
            def _reserve(target_store, **kwargs):
                out = target_store.check_and_reserve(**kwargs)
                return (True, out) if isinstance(out, dict) else out

            clear_usage_context()
            set_usage_context(run_id="run-a", trip_id="trip-a")
            allowed_a, res_a = _reserve(store, **self._reservation_kwargs())
            assert allowed_a
            set_usage_context(run_id="run-b", trip_id="trip-b")
            allowed_b, res_b = _reserve(store, **self._reservation_kwargs())
            assert allowed_b
            clear_usage_context()

            events_a = store.get_events_for_run("run-a")
            assert [e["id"] for e in events_a] == [res_a["event_id"]]
            assert events_a[0]["run_id"] == "run-a"
            assert events_a[0]["trip_id"] == "trip-a"
            assert store.get_events_for_run("run-missing") == []
            assert {res_a["event_id"], res_b["event_id"]} == {
                e["id"] for e in store.get_events_for_run("run-a")
            } | {e["id"] for e in store.get_events_for_run("run-b")}

    def test_sqlite_legacy_rows_and_schema_still_load(self, tmp_path):
        """Rows written before the run_id/trip_id columns read back as NULL."""
        import sqlite3

        from src.llm.usage_store import LLMUsageStore, clear_usage_context, set_usage_context

        legacy_path = tmp_path / "legacy.db"
        conn = sqlite3.connect(str(legacy_path))
        try:
            # Pre-Wave-2 schema: no run_id/trip_id columns.
            conn.execute(
                """
                CREATE TABLE usage_events (
                    id           INTEGER PRIMARY KEY AUTOINCREMENT,
                    request_id   TEXT NOT NULL,
                    agency_id    TEXT DEFAULT 'default',
                    model        TEXT NOT NULL,
                    feature      TEXT NOT NULL,
                    created_at   TEXT NOT NULL,
                    usage_date   TEXT NOT NULL,
                    status       TEXT NOT NULL,
                    estimated_cost REAL NOT NULL DEFAULT 0.0,
                    actual_cost    REAL,
                    block_reason TEXT,
                    warning_flags TEXT,
                    metadata_json TEXT
                )
                """
            )
            conn.execute(
                """
                INSERT INTO usage_events
                (request_id, agency_id, model, feature, created_at, usage_date,
                 status, estimated_cost)
                VALUES ('legacy-req', 'agency-1', 'm', 'f',
                        '2026-01-01T00:00:00', '2026-01-01', 'completed', 1.0)
                """
            )
            conn.commit()
        finally:
            conn.close()

        # Opening the store self-heals the schema; the legacy row survives
        # with NULL correlation columns and new writes populate them.
        store = LLMUsageStore(db_path=legacy_path)
        clear_usage_context()
        set_usage_context(run_id="run-new", trip_id="trip-new")
        try:
            allowed, reservation = store.check_and_reserve(**self._reservation_kwargs())
            assert allowed
            legacy_event = store.get_event(1)
            assert legacy_event["run_id"] is None
            assert legacy_event["trip_id"] is None
            new_event = store.get_event(reservation["event_id"])
            assert new_event["run_id"] == "run-new"
            assert new_event["trip_id"] == "trip-new"
            assert [e["id"] for e in store.get_events_for_run("run-new")] == [
                reservation["event_id"]
            ]
        finally:
            clear_usage_context()


# ---------------------------------------------------------------------------
# PA-21 — closed-loop verdict honesty
# ---------------------------------------------------------------------------


class _RecordingTripRepo:
    def __init__(self, trip):
        self._trip = trip
        self.updates = []

    def list_active(self):
        return [self._trip]

    def update_trip(self, trip_id, updates):
        self.updates.append((trip_id, updates))
        return dict(self._trip, **updates)


class TestPA21VerdictHonesty:
    def _work_item(self):
        from src.agents.runtime import WorkItem

        now = datetime.now(timezone.utc)
        return WorkItem(
            agent_name="closed_loop_learning_agent",
            trip_id="trip-cl",
            action="generate_fix_candidate",
            idempotency_key="k",
            payload={
                "failure_signature": "sig-1",
                "failure_layer": "intake",
                "next_fix_layer": "decision",
                "occurrences": 3,
                "first_seen": now.isoformat(),
                "last_seen": now.isoformat(),
                "sample_events": ["e1"],
                "severity": "medium",
            },
        )

    def _trip(self):
        return {
            "id": "trip-cl",
            "status": "new",
            "execution_events": [
                {
                    "id": "e1",
                    "event_metadata": {"failure_layer": "decision"},
                }
            ],
        }

    def test_shadow_result_carries_honesty_fields(self):
        from src.agents.closed_loop_learning import (
            FixCandidate,
            run_shadow_test,
        )

        candidate = FixCandidate(
            candidate_id="fix_x",
            failure_signature="sig-1",
            failure_layer="intake",
            next_fix_layer="decision",
            severity="medium",
            proposed_change="c",
            expected_improvement="i",
            regression_risk="r",
            rerun_subset="s",
            owner="o",
            occurrences=3,
            first_seen="2026-01-01T00:00:00+00:00",
            last_seen="2026-01-01T00:00:00+00:00",
            sample_events=[],
        )
        result = run_shadow_test(
            candidate,
            [{"event_metadata": {"failure_layer": "decision"}}],
        )
        assert result.verdict == "proceed"
        payload = result.to_dict()
        assert payload["verdict_basis"] == "heuristic_string_match"
        assert payload["demonstrated"] is False

    def test_execute_writes_honesty_fields_to_trip(self):
        from src.agents.closed_loop_learning import ClosedLoopLearningAgent

        trip = self._trip()
        repo = _RecordingTripRepo(trip)
        agent = ClosedLoopLearningAgent()
        result = agent.execute(self._work_item(), repo)

        assert result.success is True
        assert result.output["verdict_basis"] == "heuristic_string_match"
        assert result.output["demonstrated"] is False
        assert "not demonstrated" in result.reason

        trip_id, updates = repo.updates[0]
        assert trip_id == "trip-cl"
        assert updates["closed_loop_verdict_basis"] == "heuristic_string_match"
        assert updates["closed_loop_verdict_demonstrated"] is False
        # Back-compat field is still written for existing readers.
        assert updates["closed_loop_verdict"] in {"proceed", "defer", "reject"}
        # The shadow-test snapshot itself carries the honesty fields.
        assert updates["closed_loop_shadow_test"]["verdict_basis"] == (
            "heuristic_string_match"
        )


# ---------------------------------------------------------------------------
# PA-27 — lead-save fail-loud (pipeline level, real ledger meta)
# ---------------------------------------------------------------------------


class TestPA27LeadSaveFailLoud:
    def test_double_save_failure_marks_run_failed_state_class(self, isolated_run_ledger):
        import spine_api.services.pipeline_execution_service as svc

        RunLedger.create("run-loud", None, "discovery", "normal_intake")

        def _escalating_result():
            return SimpleNamespace(
                packet=SimpleNamespace(packet_id="packet-loud"),
                validation=SimpleNamespace(is_valid=False),
                decision=SimpleNamespace(decision_state="STOP_NEEDS_REVIEW"),
                strategy=SimpleNamespace(),
                leakage_result={"leaks": [], "is_safe": True},
                early_exit=True,
                early_exit_reason="Trip details are incomplete.",
            )

        save_mock = MagicMock(side_effect=RuntimeError("pg down"))
        emit_failed = MagicMock()
        emit_blocked = MagicMock()

        with pytest.raises(svc.LeadPersistenceError):
            svc.execute_spine_pipeline(
                run_id="run-loud",
                request_dict={
                    "raw_note": "test",
                    "stage": "discovery",
                    "operating_mode": "normal_intake",
                    "strict_leakage": False,
                    "retention_consent": True,
                    "scenario_id": None,
                },
                agency_id="agency-1",
                user_id="user-1",
                build_envelopes=lambda _payload: [],
                load_fixture_expectations=lambda _scenario_id: None,
                to_dict=lambda obj: obj if isinstance(obj, dict) else getattr(obj, "__dict__", obj),
                close_inherited_lock_fds=lambda: None,
                save_processed_trip=save_mock,
                trip_store=SimpleNamespace(get_trip=MagicMock(return_value={})),
                audit_store=_CapturingAudit(),
                run_spine_once_fn=lambda **_kwargs: _escalating_result(),
                logger=MagicMock(),
                otel_tracer=SimpleNamespace(
                    start_as_current_span=lambda _name: nullcontext(
                        SimpleNamespace(set_attribute=lambda *_a, **_k: None)
                    )
                ),
                run_ledger=RunLedger,
                run_state_running=RunState.RUNNING,
                draft_store=SimpleNamespace(
                    get=MagicMock(return_value=None),
                    update_run_state=MagicMock(),
                ),
                agency_settings_store=SimpleNamespace(load=MagicMock(return_value={})),
                build_live_checker_signals_fn=lambda _packet, _raw: None,
                emit_run_started_fn=MagicMock(),
                emit_run_completed_fn=MagicMock(),
                emit_run_failed_fn=emit_failed,
                emit_run_blocked_fn=emit_blocked,
                emit_stage_entered_fn=MagicMock(),
                emit_stage_completed_fn=MagicMock(),
            )

        # Retried once, then failed — NOT blocked-without-trip.
        assert save_mock.call_count == 2
        meta = RunLedger.get_meta("run-loud")
        assert meta["state"] == "failed"
        assert meta["failure_class"] == "state"
        assert meta["error_type"] == "RuntimeError"
        assert emit_failed.call_count == 1
        emit_blocked.assert_not_called()

    def test_single_save_failure_recovers_into_blocked_flow(self, isolated_run_ledger):
        """One transient failure retries and the normal block path proceeds."""
        import spine_api.services.pipeline_execution_service as svc

        RunLedger.create("run-retry", None, "discovery", "normal_intake")

        def _escalating_result():
            return SimpleNamespace(
                packet=SimpleNamespace(packet_id="packet-retry"),
                validation=SimpleNamespace(is_valid=False),
                decision=SimpleNamespace(decision_state="STOP_NEEDS_REVIEW"),
                strategy=SimpleNamespace(),
                leakage_result={"leaks": [], "is_safe": True},
                early_exit=True,
                early_exit_reason="Trip details are incomplete.",
            )

        responses = [RuntimeError("transient"), "trip-recovered"]
        save_mock = MagicMock(side_effect=responses)
        emit_blocked = MagicMock()

        svc.execute_spine_pipeline(
            run_id="run-retry",
            request_dict={
                "raw_note": "test",
                "stage": "discovery",
                "operating_mode": "normal_intake",
                "strict_leakage": False,
                "retention_consent": True,
                "scenario_id": None,
            },
            agency_id="agency-1",
            user_id="user-1",
            build_envelopes=lambda _payload: [],
            load_fixture_expectations=lambda _scenario_id: None,
            to_dict=lambda obj: obj if isinstance(obj, dict) else getattr(obj, "__dict__", obj),
            close_inherited_lock_fds=lambda: None,
            save_processed_trip=save_mock,
            trip_store=SimpleNamespace(get_trip=MagicMock(return_value={})),
            audit_store=_CapturingAudit(),
            run_spine_once_fn=lambda **_kwargs: _escalating_result(),
            logger=MagicMock(),
            otel_tracer=SimpleNamespace(
                start_as_current_span=lambda _name: nullcontext(
                    SimpleNamespace(set_attribute=lambda *_a, **_k: None)
                )
            ),
            run_ledger=RunLedger,
            run_state_running=RunState.RUNNING,
            draft_store=SimpleNamespace(
                get=MagicMock(return_value=None),
                update_run_state=MagicMock(),
            ),
            agency_settings_store=SimpleNamespace(load=MagicMock(return_value={})),
            build_live_checker_signals_fn=lambda _packet, _raw: None,
            emit_run_started_fn=MagicMock(),
            emit_run_completed_fn=MagicMock(),
            emit_run_failed_fn=MagicMock(),
            emit_run_blocked_fn=emit_blocked,
            emit_stage_entered_fn=MagicMock(),
            emit_stage_completed_fn=MagicMock(),
        )

        assert save_mock.call_count == 2
        meta = RunLedger.get_meta("run-retry")
        assert meta["state"] == "blocked"
        assert meta["trip_id"] == "trip-recovered"
        emit_blocked.assert_called_once()


# ---------------------------------------------------------------------------
# PA-17 pipeline-level: completion reconciliation + heartbeat on checkpoints
# ---------------------------------------------------------------------------


class TestPA17PipelineReconciliation:
    def test_completed_after_sweep_failure_transition(self, isolated_run_ledger):
        """The sweep fails the run mid-flight; the live thread still saves the trip."""
        import spine_api.services.pipeline_execution_service as svc

        RunLedger.create("run-race-2", None, "discovery", "normal_intake")
        audit = _CapturingAudit()

        def sweep_races_then_saves(*_args, **_kwargs):
            # The stale sweep fires in the race window — the run is marked
            # FAILED while the pipeline thread is between stages — then the
            # trip save succeeds anyway (what PA-17 observed in production).
            RunLedger.fail("run-race-2", "RunTimeout", "sweep raced the thread")
            return "trip-raced"

        svc.execute_spine_pipeline(
            run_id="run-race-2",
            request_dict={
                "raw_note": "test",
                "stage": "discovery",
                "operating_mode": "normal_intake",
                "strict_leakage": False,
                "retention_consent": True,
                "scenario_id": None,
            },
            agency_id="agency-1",
            user_id="user-1",
            build_envelopes=lambda _payload: [],
            load_fixture_expectations=lambda _scenario_id: None,
            to_dict=lambda obj: obj if isinstance(obj, dict) else getattr(obj, "__dict__", obj),
            close_inherited_lock_fds=lambda: None,
            save_processed_trip=sweep_races_then_saves,
            trip_store=SimpleNamespace(get_trip=MagicMock(return_value={})),
            audit_store=audit,
            run_spine_once_fn=lambda **_kwargs: _successful_spine_result(),
            logger=MagicMock(),
            otel_tracer=SimpleNamespace(
                start_as_current_span=lambda _name: nullcontext(
                    SimpleNamespace(set_attribute=lambda *_a, **_k: None)
                )
            ),
            run_ledger=RunLedger,
            run_state_running=RunState.RUNNING,
            draft_store=SimpleNamespace(
                get=MagicMock(return_value=None),
                update_run_state=MagicMock(),
            ),
            agency_settings_store=SimpleNamespace(load=MagicMock(return_value={})),
            build_live_checker_signals_fn=lambda _packet, _raw: None,
            emit_run_started_fn=MagicMock(),
            emit_run_completed_fn=MagicMock(),
            emit_run_failed_fn=MagicMock(),
            emit_run_blocked_fn=MagicMock(),
            emit_stage_entered_fn=MagicMock(),
            emit_stage_completed_fn=MagicMock(),
        )

        meta = RunLedger.get_meta("run-race-2")
        assert meta["state"] == "completed"
        assert meta["recovered_after_timeout"] is True
        assert meta["trip_id"] == "trip-raced"

    def test_stage_checkpoints_write_heartbeat_meta(self, isolated_run_ledger):
        """stage_callback checkpoints touch the ledger heartbeat (real ledger)."""
        import spine_api.services.pipeline_execution_service as svc

        RunLedger.create("run-hb-2", None, "discovery", "normal_intake")

        def run_with_callback(**kwargs):
            callback = kwargs["stage_callback"]
            callback("packet", {"event": "entered"})
            callback("packet", {"event": "completed", "data": {"ok": True}})
            return _successful_spine_result()

        svc.execute_spine_pipeline(
            run_id="run-hb-2",
            request_dict={
                "raw_note": "test",
                "stage": "discovery",
                "operating_mode": "normal_intake",
                "strict_leakage": False,
                "retention_consent": True,
                "scenario_id": None,
            },
            agency_id="agency-1",
            user_id="user-1",
            build_envelopes=lambda _payload: [],
            load_fixture_expectations=lambda _scenario_id: None,
            to_dict=lambda obj: obj if isinstance(obj, dict) else getattr(obj, "__dict__", obj),
            close_inherited_lock_fds=lambda: None,
            save_processed_trip=MagicMock(return_value="trip-hb"),
            trip_store=SimpleNamespace(get_trip=MagicMock(return_value={})),
            audit_store=_CapturingAudit(),
            run_spine_once_fn=run_with_callback,
            logger=MagicMock(),
            otel_tracer=SimpleNamespace(
                start_as_current_span=lambda _name: nullcontext(
                    SimpleNamespace(set_attribute=lambda *_a, **_k: None)
                )
            ),
            run_ledger=RunLedger,
            run_state_running=RunState.RUNNING,
            draft_store=SimpleNamespace(
                get=MagicMock(return_value=None),
                update_run_state=MagicMock(),
            ),
            agency_settings_store=SimpleNamespace(load=MagicMock(return_value={})),
            build_live_checker_signals_fn=lambda _packet, _raw: None,
            emit_run_started_fn=MagicMock(),
            emit_run_completed_fn=MagicMock(),
            emit_run_failed_fn=MagicMock(),
            emit_run_blocked_fn=MagicMock(),
            emit_stage_entered_fn=MagicMock(),
            emit_stage_completed_fn=MagicMock(),
        )

        meta = RunLedger.get_meta("run-hb-2")
        assert meta["heartbeat_at"] is not None
        assert meta["state"] == "completed"
