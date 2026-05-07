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
