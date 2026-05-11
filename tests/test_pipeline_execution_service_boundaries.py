from __future__ import annotations

from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import spine_api.services.pipeline_execution_service as svc


def test_pipeline_execution_service_source_has_no_server_import() -> None:
    source = Path(svc.__file__).read_text()
    forbidden = [
        "import spine_api.server",
        "from spine_api import server",
        "from spine_api.server import",
        "import server",
        "from server import",
    ]
    assert all(token not in source for token in forbidden)


def test_execute_spine_pipeline_uses_injected_run_and_persistence() -> None:
    calls: list[bool] = []

    class FakeRunLedger:
        @staticmethod
        def set_state(run_id, state):
            _ = (run_id, state)

        @staticmethod
        def get_meta(run_id):
            _ = run_id
            return {"draft_id": None}

        @staticmethod
        def fail(run_id, error_type, error_message):
            _ = (run_id, error_type, error_message)

    emit_started = MagicMock()
    emit_completed = MagicMock()
    emit_failed = MagicMock()
    emit_blocked = MagicMock()
    emit_stage_entered = MagicMock()
    emit_stage_completed = MagicMock()

    def fake_set_strict_mode(value: bool) -> None:
        calls.append(value)

    logger = MagicMock()

    def exploding_run_spine_once_fn(**_kwargs):
        raise RuntimeError("boom")

    svc.execute_spine_pipeline(
        run_id="run-1",
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
        to_dict=lambda obj: obj,
        close_inherited_lock_fds=lambda: None,
        save_processed_trip=MagicMock(),
        trip_store=SimpleNamespace(get_trip=MagicMock(return_value={})),
        audit_store=SimpleNamespace(log_event=MagicMock()),
        run_spine_once_fn=exploding_run_spine_once_fn,
        logger=logger,
        otel_tracer=SimpleNamespace(start_as_current_span=lambda _name: nullcontext(SimpleNamespace(set_attribute=lambda *_a, **_k: None))),
        run_ledger=FakeRunLedger,
        run_state_running="running",
        draft_store=SimpleNamespace(update_run_state=MagicMock()),
        agency_settings_store=SimpleNamespace(load=MagicMock(return_value={})),
        set_strict_mode_fn=fake_set_strict_mode,
        build_live_checker_signals_fn=lambda _packet, _raw: None,
        emit_run_started_fn=emit_started,
        emit_run_completed_fn=emit_completed,
        emit_run_failed_fn=emit_failed,
        emit_run_blocked_fn=emit_blocked,
        emit_stage_entered_fn=emit_stage_entered,
        emit_stage_completed_fn=emit_stage_completed,
    )

    # Generic exceptions must map to FAILED path
    emit_failed.assert_called_once()
    emit_blocked.assert_not_called()
    emit_completed.assert_not_called()

    # strict mode always reset in finally
    assert calls and calls[-1] is False


def _base_request() -> dict:
    return {
        "raw_note": "test",
        "stage": "discovery",
        "operating_mode": "normal_intake",
        "strict_leakage": False,
        "retention_consent": True,
        "scenario_id": None,
    }


def _successful_result() -> SimpleNamespace:
    return SimpleNamespace(
        packet=SimpleNamespace(packet_id="packet-1"),
        validation=SimpleNamespace(is_valid=True),
        decision=SimpleNamespace(),
        strategy=SimpleNamespace(),
        leakage_result={"leaks": [], "is_safe": True},
    )


def _execute_for_boundary_test(*, run_ledger, run_spine_once_fn=None):
    calls: list[bool] = []
    logger = MagicMock()
    emit_started = MagicMock()
    emit_completed = MagicMock()
    emit_failed = MagicMock()
    emit_blocked = MagicMock()
    save_processed_trip = MagicMock(return_value="trip-1")

    svc.execute_spine_pipeline(
        run_id="run-1",
        request_dict=_base_request(),
        agency_id="agency-1",
        user_id="user-1",
        build_envelopes=lambda _payload: [],
        load_fixture_expectations=lambda _scenario_id: None,
        to_dict=lambda obj: obj if isinstance(obj, dict) else getattr(obj, "__dict__", obj),
        close_inherited_lock_fds=lambda: None,
        save_processed_trip=save_processed_trip,
        trip_store=SimpleNamespace(get_trip=MagicMock(return_value={})),
        audit_store=SimpleNamespace(log_event=MagicMock()),
        run_spine_once_fn=run_spine_once_fn or (lambda **_kwargs: _successful_result()),
        logger=logger,
        otel_tracer=SimpleNamespace(start_as_current_span=lambda _name: nullcontext(SimpleNamespace(set_attribute=lambda *_a, **_k: None))),
        run_ledger=run_ledger,
        run_state_running="running",
        draft_store=SimpleNamespace(update_run_state=MagicMock()),
        agency_settings_store=SimpleNamespace(load=MagicMock(return_value={})),
        set_strict_mode_fn=lambda value: calls.append(value),
        build_live_checker_signals_fn=lambda _packet, _raw: None,
        emit_run_started_fn=emit_started,
        emit_run_completed_fn=emit_completed,
        emit_run_failed_fn=emit_failed,
        emit_run_blocked_fn=emit_blocked,
        emit_stage_entered_fn=MagicMock(),
        emit_stage_completed_fn=MagicMock(),
    )

    return SimpleNamespace(
        strict_mode_calls=calls,
        logger=logger,
        emit_completed=emit_completed,
        emit_failed=emit_failed,
        emit_blocked=emit_blocked,
        save_processed_trip=save_processed_trip,
    )


def test_execute_spine_pipeline_isolates_result_checkpoint_ledger_failure() -> None:
    class FailingCheckpointLedger:
        @staticmethod
        def set_state(run_id, state):
            _ = (run_id, state)

        @staticmethod
        def get_all_steps(run_id):
            _ = run_id
            raise RuntimeError("checkpoint store down")

        @staticmethod
        def update_meta(run_id, **kwargs):
            _ = (run_id, kwargs)

        @staticmethod
        def get_meta(run_id):
            _ = run_id
            return {"draft_id": None}

        @staticmethod
        def complete(run_id, total_ms):
            _ = (run_id, total_ms)

    result = _execute_for_boundary_test(run_ledger=FailingCheckpointLedger)

    result.save_processed_trip.assert_called_once()
    result.emit_completed.assert_called_once()
    result.logger.error.assert_any_call(
        "Wave A: result step checkpointing failed for run %s: %s",
        "run-1",
        result.logger.error.call_args_list[0][0][2],
    )
    assert result.strict_mode_calls[-1] is False


def test_execute_spine_pipeline_persists_traveler_bundle_public_projection() -> None:
    class Ledger:
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
            _ = (run_id, kwargs)

        @staticmethod
        def get_meta(run_id):
            _ = run_id
            return {"draft_id": None}

        @staticmethod
        def complete(run_id, total_ms):
            _ = (run_id, total_ms)

    class TravelerBundle:
        def __init__(self):
            self.system_context = "traveler system context"
            self.user_message = "traveler message"
            self.internal_notes = "internal margin and vendor notes"

        def to_traveler_dict(self):
            return {
                "system_context": self.system_context,
                "user_message": self.user_message,
                "audience": "traveler",
            }

    result = _execute_for_boundary_test(
        run_ledger=Ledger,
        run_spine_once_fn=lambda **_kwargs: SimpleNamespace(
            packet=SimpleNamespace(packet_id="packet-1"),
            validation=SimpleNamespace(is_valid=True),
            decision=SimpleNamespace(),
            strategy=SimpleNamespace(),
            traveler_bundle=TravelerBundle(),
            internal_bundle=SimpleNamespace(internal_notes="internal bundle stays internal"),
            leakage_result={"leaks": [], "is_safe": True},
        ),
    )

    persisted = result.save_processed_trip.call_args[0][0]

    assert persisted["traveler_bundle"] == {
        "system_context": "traveler system context",
        "user_message": "traveler message",
        "audience": "traveler",
    }
    assert "internal_notes" not in persisted["traveler_bundle"]
    assert persisted["internal_bundle"]["internal_notes"] == "internal bundle stays internal"


def test_execute_spine_pipeline_isolates_complete_ledger_failure() -> None:
    class FailingCompleteLedger:
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
            _ = (run_id, kwargs)

        @staticmethod
        def get_meta(run_id):
            _ = run_id
            return {"draft_id": None}

        @staticmethod
        def complete(run_id, total_ms):
            _ = (run_id, total_ms)
            raise RuntimeError("complete store down")

    result = _execute_for_boundary_test(run_ledger=FailingCompleteLedger)

    result.save_processed_trip.assert_called_once()
    result.emit_completed.assert_not_called()
    result.logger.error.assert_any_call(
        "Wave A: ledger complete failed for run %s: %s",
        "run-1",
        result.logger.error.call_args_list[-1][0][2],
    )
    assert result.strict_mode_calls[-1] is False


def test_execute_spine_pipeline_isolates_block_ledger_failure() -> None:
    class FailingBlockLedger:
        @staticmethod
        def set_state(run_id, state):
            _ = (run_id, state)

        @staticmethod
        def block(run_id, block_reason):
            _ = (run_id, block_reason)
            raise RuntimeError("block store down")

    result = _execute_for_boundary_test(
        run_ledger=FailingBlockLedger,
        run_spine_once_fn=lambda **_kwargs: (_ for _ in ()).throw(ValueError("strict leakage")),
    )

    result.emit_blocked.assert_not_called()
    result.logger.error.assert_any_call(
        "Wave A: block ledger failed for run %s: %s",
        "run-1",
        result.logger.error.call_args_list[-1][0][2],
    )
    assert result.strict_mode_calls[-1] is False


def test_execute_spine_pipeline_isolates_fail_ledger_failure() -> None:
    class FailingFailLedger:
        @staticmethod
        def set_state(run_id, state):
            _ = (run_id, state)

        @staticmethod
        def fail(run_id, error_type, error_message):
            _ = (run_id, error_type, error_message)
            raise RuntimeError("fail store down")

    result = _execute_for_boundary_test(
        run_ledger=FailingFailLedger,
        run_spine_once_fn=lambda **_kwargs: (_ for _ in ()).throw(RuntimeError("pipeline down")),
    )

    result.emit_failed.assert_not_called()
    result.logger.error.assert_any_call(
        "Wave A: fail ledger failed for run %s: %s",
        "run-1",
        result.logger.error.call_args_list[-1][0][2],
    )
    assert result.strict_mode_calls[-1] is False
