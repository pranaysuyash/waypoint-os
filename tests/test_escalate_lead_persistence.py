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
        fail_calls: list = []

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
        def fail(run_id, error_type, error_message, failure_class="unclassified", stage=None):
            Ledger.fail_calls.append(
                {
                    "run_id": run_id,
                    "error_type": error_type,
                    "error_message": error_message,
                    "failure_class": failure_class,
                    "stage": stage,
                }
            )

        @staticmethod
        def block(run_id, block_reason):
            _ = (run_id, block_reason)

    return Ledger


def _run_escalate(draft_store, trip_store=None, save_processed_trip=None, target_trip_id=None):
    logger = MagicMock()
    emit_blocked = MagicMock()
    emit_completed = MagicMock()
    emit_failed = MagicMock()
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
        emit_run_failed_fn=emit_failed,
        emit_run_blocked_fn=emit_blocked,
        emit_stage_entered_fn=MagicMock(),
        emit_stage_completed_fn=MagicMock(),
        target_trip_id=target_trip_id,
    )
    return SimpleNamespace(
        logger=logger,
        emit_blocked=emit_blocked,
        emit_completed=emit_completed,
        emit_failed=emit_failed,
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


def test_escalate_lead_save_failure_is_loud_and_failed_not_blocked() -> None:
    """PA-27: two consecutive lead-save failures FAIL the run (classified), loudly.

    Failed-before: the save failure was logged and the run proceeded to
    BLOCKED with no trip (silent lead loss to the traveler). Passes-after:
    the save is retried once, then the run is marked FAILED with
    failure_class="state" and the error propagates so the lost lead is loud
    AND classified.
    """
    import pytest

    from spine_api.services.pipeline_execution_service import LeadPersistenceError

    draft_store = SimpleNamespace(
        get=MagicMock(return_value=None),
        update_run_state=MagicMock(),
    )
    ledger = _make_ledger({"draft_id": "draft-1"})
    save_mock = MagicMock(side_effect=RuntimeError("db down"))
    logger = MagicMock()
    emit_blocked = MagicMock()
    emit_failed = MagicMock()

    with pytest.raises(LeadPersistenceError):
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
            trip_store=SimpleNamespace(get_trip=MagicMock(return_value={})),
            audit_store=SimpleNamespace(log_event=MagicMock()),
            run_spine_once_fn=lambda **_kwargs: _escalating_result(),
            logger=logger,
            otel_tracer=SimpleNamespace(
                start_as_current_span=lambda _name: nullcontext(
                    SimpleNamespace(set_attribute=lambda *_a, **_k: None)
                )
            ),
            run_ledger=ledger,
            run_state_running="running",
            draft_store=draft_store,
            agency_settings_store=SimpleNamespace(load=MagicMock(return_value={})),
            build_live_checker_signals_fn=lambda _packet, _raw: None,
            emit_run_started_fn=MagicMock(),
            emit_run_completed_fn=MagicMock(),
            emit_run_failed_fn=emit_failed,
            emit_run_blocked_fn=emit_blocked,
            emit_stage_entered_fn=MagicMock(),
            emit_stage_completed_fn=MagicMock(),
        )

    # Retried exactly once (two attempts), then failed loudly.
    assert save_mock.call_count == 2
    # The run is FAILED with the state failure class — not blocked-without-trip.
    assert len(ledger.fail_calls) == 1
    assert ledger.fail_calls[0]["failure_class"] == "state"
    assert "Lead persistence failed after retry" in ledger.fail_calls[0]["error_message"]
    assert emit_failed.call_count == 1
    # stage_at_failure kwarg is carried (None here: the fake never checkpoints
    # a stage, so no stage has been entered yet).
    assert "stage_at_failure" in emit_failed.call_args.kwargs
    # The blocked path must NOT claim the run.
    emit_blocked.assert_not_called()
    # Each attempt logged loudly.
    error_calls = [
        call for call in logger.error.call_args_list
        if call.args and "lead persistence failed" in str(call.args[0])
    ]
    assert len(error_calls) >= 2


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
