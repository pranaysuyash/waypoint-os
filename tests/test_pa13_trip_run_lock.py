"""PA-13 Wave 2 — per-trip/draft in-flight execution lock (S2 evidence).

FAILED BEFORE: two concurrent runs for the same draft or trip (double-click
"process draft", operator edit racing an auto-reassess) both executed the full
spine pipeline and raced save_processed_trip — duplicated LLM spend and
last-writer-wins trip state.

PASSES AFTER: execute_spine_pipeline (the single choke point shared by POST
/run and trip reassessment) acquires ``trip-run:draft:{id}`` /
``trip-run:trip:{id}`` from the durable IdempotencyRegistry:
- a PENDING holder blocks the second run (BLOCKED — a policy rejection that
  recovery never auto-requeues — never FAILED);
- the holder releases in ``finally`` with its fencing token; release uses the
  registry's only immediately re-acquirable terminal state so a completed run
  never wedges a legitimate reprocess (verified: mark_completed would answer
  re-acquire with (False, COMPLETED) until the 30-min TTL lapses);
- brand-new trips (no draft id, no target trip) take no lock.

The registry is swapped for a fresh in-memory instance per test so the suite
is independent of SPINE_API_IDEMPOTENCY_BACKEND and of other modules' keys.
"""

from __future__ import annotations

from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

import spine_api.services.pipeline_execution_service as svc
import spine_api.services.trip_lifecycle_service as lifecycle_svc
from src.agents.idempotency import IdempotencyRegistry, IdempotencyStatus

TRIP_RUN_LOCK_CONFLICT_REASON = (
    "concurrent run already in flight for this trip/draft"
)


@pytest.fixture
def memory_registry():
    """Swap the process-wide registry for a fresh in-memory instance."""
    previous = IdempotencyRegistry._instance
    registry = IdempotencyRegistry()  # direct construction → memory backend
    IdempotencyRegistry._instance = registry
    try:
        yield registry
    finally:
        IdempotencyRegistry._instance = previous


class _StatefulFakeLedger:
    """Fake ledger mirroring the real RunLedger's meta/state contract."""

    def __init__(self, draft_id=None):
        self.meta = {
            "run_id": "run-under-test",
            "draft_id": draft_id,
            "state": "queued",
        }
        self.block_calls: list[dict] = []
        self.fail_calls: list[dict] = []
        self.complete_calls: list[dict] = []

    def set_state(self, run_id, state):
        _ = run_id
        self.meta["state"] = state

    def get_meta(self, run_id):
        _ = run_id
        return dict(self.meta)

    def update_meta(self, run_id, **kwargs):
        _ = run_id
        self.meta.update(kwargs)

    def block(self, run_id, block_reason):
        _ = run_id
        self.meta["state"] = "blocked"
        self.meta["block_reason"] = block_reason
        self.block_calls.append({"block_reason": block_reason})

    def fail(self, run_id, error_type, error_message, failure_class="unclassified", stage=None):
        _ = run_id
        self.meta["state"] = "failed"
        self.fail_calls.append(
            {"error_type": error_type, "error_message": error_message, "failure_class": failure_class}
        )

    def complete(self, run_id, total_ms):
        _ = run_id
        self.meta["state"] = "completed"
        self.complete_calls.append({"total_ms": total_ms})

    def touch(self, run_id):
        _ = run_id

    def save_step(self, run_id, step, payload):
        _ = (run_id, step, payload)

    def get_all_steps(self, run_id):
        _ = run_id
        return {}


def _base_request(draft_id=None) -> dict:
    request = {
        "raw_note": "test",
        "stage": "discovery",
        "operating_mode": "normal_intake",
        "strict_leakage": False,
        "retention_consent": True,
        "scenario_id": None,
    }
    if draft_id is not None:
        request["draft_id"] = draft_id
    return request


def _successful_result() -> SimpleNamespace:
    return SimpleNamespace(
        packet=SimpleNamespace(packet_id="packet-1"),
        validation=SimpleNamespace(is_valid=True),
        decision=SimpleNamespace(),
        strategy=SimpleNamespace(),
        leakage_result={"leaks": [], "is_safe": True},
    )


def _execute(
    *,
    run_id="run-under-test",
    request_dict,
    run_ledger,
    run_spine_once_fn,
    target_trip_id=None,
):
    logger = MagicMock()
    emit_blocked = MagicMock()
    emit_failed = MagicMock()
    emit_completed = MagicMock()
    save_processed_trip = MagicMock(return_value="trip-1")
    draft_store = SimpleNamespace(
        get=MagicMock(return_value=None),
        update_run_state=MagicMock(),
    )

    svc.execute_spine_pipeline(
        run_id=run_id,
        request_dict=request_dict,
        agency_id="agency-1",
        user_id="user-1",
        build_envelopes=lambda _payload: [],
        load_fixture_expectations=lambda _scenario_id: None,
        to_dict=lambda obj: obj if isinstance(obj, dict) else getattr(obj, "__dict__", obj),
        close_inherited_lock_fds=lambda: None,
        save_processed_trip=save_processed_trip,
        trip_store=SimpleNamespace(get_trip=MagicMock(return_value={})),
        audit_store=SimpleNamespace(log_event=MagicMock()),
        run_spine_once_fn=run_spine_once_fn,
        logger=logger,
        otel_tracer=SimpleNamespace(
            start_as_current_span=lambda _name: nullcontext(
                SimpleNamespace(set_attribute=lambda *_a, **_k: None)
            )
        ),
        run_ledger=run_ledger,
        run_state_running="running",
        draft_store=draft_store,
        agency_settings_store=SimpleNamespace(load=MagicMock(return_value={})),
        build_live_checker_signals_fn=lambda _packet, _raw: None,
        emit_run_started_fn=MagicMock(),
        emit_run_completed_fn=emit_completed,
        emit_run_failed_fn=emit_failed,
        emit_run_blocked_fn=emit_blocked,
        emit_stage_entered_fn=MagicMock(),
        emit_stage_completed_fn=MagicMock(),
        target_trip_id=target_trip_id,
    )
    return SimpleNamespace(
        logger=logger,
        emit_blocked=emit_blocked,
        emit_failed=emit_failed,
        emit_completed=emit_completed,
        save_processed_trip=save_processed_trip,
        draft_store=draft_store,
    )


def test_pre_acquired_draft_lock_blocks_run(memory_registry):
    """(a) Lock held in-flight → run ends BLOCKED with the conflict reason."""
    registry = memory_registry
    acquired, held = registry.try_acquire(
        "trip-run:draft:draft-1",
        trip_id="",
        action_name="trip_run_lock",
        payload={"run_id": "the-other-run"},
        ttl_seconds=1800,
    )
    assert acquired and held.status == IdempotencyStatus.PENDING

    def _must_not_execute(**_kwargs):
        raise AssertionError("pipeline stages must not execute while locked")

    ledger = _StatefulFakeLedger(draft_id="draft-1")
    result = _execute(
        request_dict=_base_request(draft_id="draft-1"),
        run_ledger=ledger,
        run_spine_once_fn=_must_not_execute,
    )

    # Blocked, not failed — recovery must never auto-requeue this run.
    assert ledger.meta["state"] == "blocked"
    assert ledger.meta["block_reason"] == TRIP_RUN_LOCK_CONFLICT_REASON
    assert ledger.block_calls and ledger.fail_calls == []
    assert ledger.meta.get("trip_run_lock_conflict") is True
    result.emit_failed.assert_not_called()
    result.emit_blocked.assert_called_once()
    assert result.emit_blocked.call_args.kwargs["block_reason"] == TRIP_RUN_LOCK_CONFLICT_REASON
    result.save_processed_trip.assert_not_called()

    # Draft moved to blocked with the conflict snapshot.
    result.draft_store.update_run_state.assert_called_once()
    kwargs = result.draft_store.update_run_state.call_args.kwargs
    assert kwargs["run_state"] == "blocked"
    assert kwargs["run_snapshot"]["conflict"] is True
    assert kwargs["run_snapshot"]["block_reason"] == TRIP_RUN_LOCK_CONFLICT_REASON

    # The blocked run must not release a lock it never held: the ORIGINAL
    # holder still owns the PENDING record (fencing token untouched).
    acquired_again, existing = registry.try_acquire(
        "trip-run:draft:draft-1",
        trip_id="",
        action_name="trip_run_lock",
        payload={"run_id": "probe"},
        ttl_seconds=1800,
    )
    assert acquired_again is False
    assert existing.status == IdempotencyStatus.PENDING
    assert existing.fencing_token == held.fencing_token


def test_uncontended_run_executes_and_releases_lock(memory_registry):
    """(b) No lock held → executes normally, releases; subsequent acquire succeeds."""
    registry = memory_registry
    ledger = _StatefulFakeLedger(draft_id="draft-2")
    result = _execute(
        request_dict=_base_request(draft_id="draft-2"),
        run_ledger=ledger,
        run_spine_once_fn=lambda **_kwargs: _successful_result(),
    )

    result.emit_completed.assert_called_once()
    result.save_processed_trip.assert_called_once()
    assert ledger.meta["state"] == "completed"

    # Acquire + fencing token stashed into run meta for auditability.
    assert ledger.meta.get("trip_run_lock") == "trip-run:draft:draft-2"
    assert ledger.meta.get("trip_run_lock_fencing")

    # Released: a subsequent acquire (the next reprocess) succeeds immediately.
    acquired, record = registry.try_acquire(
        "trip-run:draft:draft-2",
        trip_id="",
        action_name="trip_run_lock",
        payload={"run_id": "next-run"},
        ttl_seconds=1800,
    )
    assert acquired is True
    assert record.status == IdempotencyStatus.PENDING


def test_failed_run_releases_lock_for_immediate_retry(memory_registry):
    """(c) FAILED run releases the lock — an immediate retry can acquire."""
    registry = memory_registry
    ledger = _StatefulFakeLedger(draft_id="draft-3")

    def _exploding_run(**_kwargs):
        raise RuntimeError("pipeline down")

    result = _execute(
        request_dict=_base_request(draft_id="draft-3"),
        run_ledger=ledger,
        run_spine_once_fn=_exploding_run,
    )

    assert ledger.meta["state"] == "failed"
    result.emit_failed.assert_called_once()

    acquired, record = registry.try_acquire(
        "trip-run:draft:draft-3",
        trip_id="",
        action_name="trip_run_lock",
        payload={"run_id": "retry-run"},
        ttl_seconds=1800,
    )
    assert acquired is True
    assert record.status == IdempotencyStatus.PENDING


def test_trip_lock_key_used_for_reassessment_path(memory_registry):
    """No draft_id + target_trip_id → trip key ``trip-run:trip:{id}`` blocks."""
    registry = memory_registry
    acquired, _held = registry.try_acquire(
        "trip-run:trip:trip-9",
        trip_id="",
        action_name="trip_run_lock",
        payload={"run_id": "reassess-in-flight"},
        ttl_seconds=1800,
    )
    assert acquired

    def _must_not_execute(**_kwargs):
        raise AssertionError("reassessment must not execute while the trip is locked")

    ledger = _StatefulFakeLedger(draft_id=None)
    result = _execute(
        request_dict=_base_request(draft_id=None),
        run_ledger=ledger,
        run_spine_once_fn=_must_not_execute,
        target_trip_id="trip-9",
    )

    assert ledger.meta["state"] == "blocked"
    assert ledger.meta["block_reason"] == TRIP_RUN_LOCK_CONFLICT_REASON
    result.emit_blocked.assert_called_once()
    assert result.emit_blocked.call_args.kwargs["trip_id"] == "trip-9"


def test_brand_new_trip_takes_no_lock(memory_registry):
    """No draft and no target trip → no lock; run completes; registry untouched."""
    registry = memory_registry
    ledger = _StatefulFakeLedger(draft_id=None)
    result = _execute(
        request_dict=_base_request(draft_id=None),
        run_ledger=ledger,
        run_spine_once_fn=lambda **_kwargs: _successful_result(),
    )

    result.emit_completed.assert_called_once()
    assert "trip_run_lock" not in ledger.meta
    assert registry._records == {}  # nothing was ever acquired


def test_release_is_noop_when_lock_never_acquired(memory_registry):
    """A registry outage at acquire time fails open — run proceeds, release no-ops."""
    registry = memory_registry

    class _ExplodingRegistry:
        def try_acquire(self, *args, **kwargs):
            raise RuntimeError("registry down")

        def mark_failed(self, *args, **kwargs):
            raise AssertionError("release must not fire when nothing was acquired")

        def mark_completed(self, *args, **kwargs):
            raise AssertionError("release must not fire when nothing was acquired")

    IdempotencyRegistry._instance = _ExplodingRegistry()
    try:
        ledger = _StatefulFakeLedger(draft_id="draft-4")
        result = _execute(
            request_dict=_base_request(draft_id="draft-4"),
            run_ledger=ledger,
            run_spine_once_fn=lambda **_kwargs: _successful_result(),
        )
        result.emit_completed.assert_called_once()
    finally:
        IdempotencyRegistry._instance = registry


def test_trip_lifecycle_service_does_not_double_lock() -> None:
    """The reassess path funnels into the single choke point — no second lock.

    execute_spine_pipeline owns the PA-13 lock (it covers both /run draft
    reprocesses and queue_trip_reassessment via target_trip_id); trip_lifecycle
    must stay lock-free or reassessment runs would be double-locked.
    """
    source = Path(lifecycle_svc.__file__).read_text()
    for forbidden_call in ("try_acquire(", "mark_completed(", "mark_failed("):
        assert forbidden_call not in source, forbidden_call
