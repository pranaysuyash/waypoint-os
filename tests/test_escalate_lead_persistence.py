"""ESCALATE lead persistence — ADR_ESCALATE_LEAD_PERSISTENCE_2026-08-31.

A blocked (ESCALATE) run must persist the inquiry as an incomplete lead so the
Lead Inbox promise holds. ESCALATE must NEVER overwrite an existing trip: when
the run belongs to a trip that already has a record (auto-reassess-on-edit or
draft reprocess), the save is skipped and the record stands.
"""

from __future__ import annotations

from contextlib import nullcontext
from types import SimpleNamespace
from unittest.mock import MagicMock

import spine_api.services.pipeline_execution_service as svc


def _base_request() -> dict:
    return {
        "raw_note": "test",
        "stage": "discovery",
        "operating_mode": "normal_intake",
        "strict_leakage": False,
        "retention_consent": True,
        "scenario_id": None,
    }


def _escalating_result():
    """Mirror the orchestration early-exit result shape (has strategy etc.)."""
    return SimpleNamespace(
        packet=SimpleNamespace(packet_id="packet-1"),
        validation=SimpleNamespace(is_valid=False),
        decision=SimpleNamespace(),
        strategy=SimpleNamespace(),
        plan_candidate=SimpleNamespace(),
        leakage_result={"leaks": [], "is_safe": True},
        early_exit=True,
        early_exit_reason="Trip details are incomplete.",
    )


def _make_ledger(meta: dict):
    """Fresh ledger fake per test — no shared mutable class state."""

    class Ledger:
        state: dict = dict(meta)

        @staticmethod
        def set_state(run_id, state):
            _ = (run_id, state)

        @staticmethod
        def get_all_steps(run_id):
            _ = run_id
            return {}

        @staticmethod
        def save_step(run_id, step, payload):
            _ = (run_id, step, payload)

        @staticmethod
        def update_meta(run_id, **kwargs):
            Ledger.state.update(kwargs)

        @staticmethod
        def get_meta(run_id):
            _ = run_id
            return dict(Ledger.state)

        @staticmethod
        def block(run_id, block_reason):
            _ = (run_id, block_reason)

    return Ledger


def _run_escalate(draft_store, trip_store=None, save_processed_trip=None, target_trip_id=None):
    logger = MagicMock()
    emit_blocked = MagicMock()
    emit_completed = MagicMock()
    save_mock = save_processed_trip or MagicMock(return_value="trip-new")

    svc.execute_spine_pipeline(
        run_id="run-1",
        request_dict=_base_request(),
        agency_id="agency-1",
        user_id="user-1",
        build_envelopes=lambda _payload: [],
        load_fixture_expectations=lambda _scenario_id: None,
        to_dict=lambda obj: obj if isinstance(obj, dict) else getattr(obj, "__dict__", obj),
        close_inherited_lock_fds=lambda: None,
        save_processed_trip=save_mock,
        trip_store=trip_store or SimpleNamespace(get_trip=MagicMock(return_value={})),
        audit_store=SimpleNamespace(log_event=MagicMock()),
        run_spine_once_fn=lambda **_kwargs: _escalating_result(),
        logger=logger,
        otel_tracer=SimpleNamespace(
            start_as_current_span=lambda _name: nullcontext(
                SimpleNamespace(set_attribute=lambda *_a, **_k: None)
            )
        ),
        run_ledger=_make_ledger({"draft_id": "draft-1"}),
        run_state_running="running",
        draft_store=draft_store,
        agency_settings_store=SimpleNamespace(load=MagicMock(return_value={})),
        build_live_checker_signals_fn=lambda _packet, _raw: None,
        emit_run_started_fn=MagicMock(),
        emit_run_completed_fn=emit_completed,
        emit_run_failed_fn=MagicMock(),
        emit_run_blocked_fn=emit_blocked,
        emit_stage_entered_fn=MagicMock(),
        emit_stage_completed_fn=MagicMock(),
        target_trip_id=target_trip_id,
    )
    return SimpleNamespace(
        logger=logger,
        emit_blocked=emit_blocked,
        emit_completed=emit_completed,
        save_processed_trip=save_mock,
        draft_store=draft_store,
    )


def test_escalate_persists_incomplete_lead_and_links_draft() -> None:
    """First ESCALATE run: trip saved as incomplete, draft records the linkage."""
    update_run_state = MagicMock()
    draft_store = SimpleNamespace(
        get=MagicMock(return_value=None),
        update_run_state=update_run_state,
    )

    result = _run_escalate(draft_store)

    result.save_processed_trip.assert_called_once()
    call_kwargs = result.save_processed_trip.call_args.kwargs
    assert call_kwargs["trip_status"] == "incomplete"
    assert call_kwargs["preserve_trip_id"] is None
    assert call_kwargs["agency_id"] == "agency-1"

    # The run ledger and downstream consumers learn the trip id.
    result.emit_blocked.assert_called_once()
    assert result.emit_blocked.call_args.kwargs["trip_id"] == "trip-new"
    result.emit_completed.assert_not_called()

    # The draft records the linkage (update_run_state carries the trip id).
    update_run_state.assert_called_once()
    assert update_run_state.call_args.kwargs.get("linked_trip_id") == "trip-new"
    assert update_run_state.call_args.kwargs["run_state"] == "blocked"


def test_escalate_with_existing_linked_trip_never_overwrites_it() -> None:
    """Draft reprocess: the linked trip already holds the record — skip the save."""
    draft = SimpleNamespace(
        promoted_trip_id=None,
        linked_trip_ids=["trip-42"],
    )
    draft_store = SimpleNamespace(
        get=MagicMock(return_value=draft),
        update_run_state=MagicMock(),
    )
    trip_store = SimpleNamespace(
        get_trip=MagicMock(return_value={"status": "awaiting_customer_details"}),
    )

    result = _run_escalate(draft_store, trip_store=trip_store)

    # The early-exit packet must not clobber the existing trip record.
    result.save_processed_trip.assert_not_called()
    result.emit_blocked.assert_called_once()
    assert result.emit_blocked.call_args.kwargs["trip_id"] == "trip-42"


def test_escalate_with_target_trip_id_reassessment_skips_save() -> None:
    """Auto-reassess-on-edit flow: target_trip_id set — record stands, run blocks."""
    draft_store = SimpleNamespace(
        get=MagicMock(return_value=None),
        update_run_state=MagicMock(),
    )

    result = _run_escalate(draft_store, target_trip_id="trip-target")

    result.save_processed_trip.assert_not_called()
    result.emit_blocked.assert_called_once()
    assert result.emit_blocked.call_args.kwargs["trip_id"] == "trip-target"


def test_escalate_reprocess_with_deleted_trip_creates_new_lead() -> None:
    """A dead linked-trip id must not be resurrected as the preserve target."""
    draft = SimpleNamespace(
        promoted_trip_id=None,
        linked_trip_ids=["trip-deleted"],
    )
    draft_store = SimpleNamespace(
        get=MagicMock(return_value=draft),
        update_run_state=MagicMock(),
    )
    trip_store = SimpleNamespace(
        get_trip=MagicMock(return_value=None),
    )

    result = _run_escalate(draft_store, trip_store=trip_store)

    result.save_processed_trip.assert_called_once()
    call_kwargs = result.save_processed_trip.call_args.kwargs
    assert call_kwargs["preserve_trip_id"] is None
    assert call_kwargs["trip_status"] == "incomplete"


def test_escalate_lead_save_failure_still_blocks_cleanly() -> None:
    """A failed lead save must not crash the block path — but must log loudly."""
    draft_store = SimpleNamespace(
        get=MagicMock(return_value=None),
        update_run_state=MagicMock(),
    )

    result = _run_escalate(
        draft_store,
        save_processed_trip=MagicMock(side_effect=RuntimeError("db down")),
    )

    result.emit_blocked.assert_called_once()
    assert result.emit_blocked.call_args.kwargs["trip_id"] is None
    error_calls = [
        call for call in result.logger.error.call_args_list
        if call.args and call.args[0] == "ESCALATE lead persistence failed for run %s: %s"
    ]
    assert error_calls, "expected the loud lead-persistence failure log"
    assert error_calls[0].args[1] == "run-1"


def test_degrade_reprocess_resolves_linked_trip_too() -> None:
    """The DEGRADE path shares the draft-reprocess idempotency guarantee."""
    draft = SimpleNamespace(promoted_trip_id=None, linked_trip_ids=["trip-7"])
    draft_store = SimpleNamespace(
        get=MagicMock(return_value=draft),
        update_run_state=MagicMock(),
    )
    trip_store = SimpleNamespace(
        get_trip=MagicMock(return_value={"status": "incomplete"}),
    )
    save_mock = MagicMock(return_value="trip-7")
    logger = MagicMock()

    partial_result = SimpleNamespace(
        packet=SimpleNamespace(packet_id="packet-1"),
        validation=SimpleNamespace(is_valid=True),
        decision=SimpleNamespace(),
        strategy=SimpleNamespace(),
        leakage_result={"leaks": [], "is_safe": True},
        partial_intake=True,
        early_exit=False,
        early_exit_reason="Missing quote-ready fields.",
    )

    Ledger = _make_ledger({"draft_id": "draft-1"})

    svc.execute_spine_pipeline(
        run_id="run-2",
        request_dict=_base_request(),
        agency_id="agency-1",
        user_id="user-1",
        build_envelopes=lambda _payload: [],
        load_fixture_expectations=lambda _scenario_id: None,
        to_dict=lambda obj: obj if isinstance(obj, dict) else getattr(obj, "__dict__", obj),
        close_inherited_lock_fds=lambda: None,
        save_processed_trip=save_mock,
        trip_store=trip_store,
        audit_store=SimpleNamespace(log_event=MagicMock()),
        run_spine_once_fn=lambda **_kwargs: partial_result,
        logger=logger,
        otel_tracer=SimpleNamespace(
            start_as_current_span=lambda _name: nullcontext(
                SimpleNamespace(set_attribute=lambda *_a, **_k: None)
            )
        ),
        run_ledger=Ledger,
        run_state_running="running",
        draft_store=draft_store,
        agency_settings_store=SimpleNamespace(load=MagicMock(return_value={})),
        build_live_checker_signals_fn=lambda _packet, _raw: None,
        emit_run_started_fn=MagicMock(),
        emit_run_completed_fn=MagicMock(),
        emit_run_failed_fn=MagicMock(),
        emit_run_blocked_fn=MagicMock(),
        emit_stage_entered_fn=MagicMock(),
        emit_stage_completed_fn=MagicMock(),
    )

    call_kwargs = save_mock.call_args.kwargs
    assert call_kwargs["preserve_trip_id"] == "trip-7"
    assert call_kwargs["trip_status"] == "incomplete"
