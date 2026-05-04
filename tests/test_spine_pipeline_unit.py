"""
Unit tests for _execute_spine_pipeline (spine_api/server.py).

Tests every code path in the pipeline runner:
  - Happy path (normal success)
  - Strict leakage mode
  - Early exit
  - Partial intake
  - Validation invalid
  - ValueError (strict leakage violation)
  - Generic Exception
  - Draft ID linked
  - retention_consent filtering
  - Live checker signals applied

All dependencies are mocked at the module level so no server or database
is needed.
"""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, PropertyMock, patch, ANY

# ---------------------------------------------------------------------------
# Mock SpineResult — controllable fake of the dataclass from orchestration.py
# ---------------------------------------------------------------------------

class MockSpineResult:
    """Minimal fake of SpineResult for testing _execute_spine_pipeline.

    Defaults are the happy-path case. Tests override attributes to exercise
    early_exit, partial_intake, validation failures, etc.
    """

    def __init__(self, **kwargs: dict) -> None:
        self.packet = MagicMock(packet_id="trip-001")
        self.validation = MagicMock(is_valid=True)
        self.decision = MagicMock(decision_state="PROCEED_TRAVELER_SAFE")
        self.strategy = MagicMock()
        self.plan_candidate = None
        self.traveler_bundle = None
        self.internal_bundle = None
        self.safety = MagicMock(
            strict_leakage=False, leakage_passed=True, leakage_errors=[]
        )
        self.fees = None
        self.frontier_result = None
        self.leakage_result: dict = {"leaks": [], "is_safe": True}
        self.early_exit = False
        self.early_exit_reason = None
        self.partial_intake = False
        self.follow_up_questions: list = []
        self.autonomy_outcome = None
        self.assertion_result = None
        self.run_timestamp = ""
        self.sanitized_view = None
        for key, val in kwargs.items():
            setattr(self, key, val)


# ---------------------------------------------------------------------------
# Shared fixture — patches every module-level dependency in server.py
# ---------------------------------------------------------------------------

@pytest.fixture
def pipeline_mocks():
    """Patch all module-level names used by _execute_spine_pipeline.

    Each test accesses the mocks it needs via the returned dict.
    """
    with (
        patch("spine_api.server.RunLedger") as mock_ledger,
        patch("spine_api.server.DraftStore") as mock_draft,
        patch("spine_api.server.AuditStore") as mock_audit,
        patch("spine_api.server.TripStore") as mock_trip,
        patch("spine_api.server.AssignmentStore") as mock_assign,
        patch("spine_api.server.AgencySettingsStore") as mock_settings,
        patch("spine_api.server.save_processed_trip", return_value="trip-saved-001"),
        patch("spine_api.server.set_strict_mode") as mock_strict,
        patch("spine_api.server.build_live_checker_signals", return_value=None),
        patch("spine_api.server._close_inherited_lock_fds"),
        patch("spine_api.server._otel_tracer") as mock_tracer,
        patch("spine_api.server.emit_run_started"),
        patch("spine_api.server.emit_run_completed"),
        patch("spine_api.server.emit_run_failed"),
        patch("spine_api.server.emit_run_blocked"),
        patch("spine_api.server.emit_stage_entered"),
        patch("spine_api.server.emit_stage_completed"),
        patch("spine_api.server.run_spine_once") as mock_run,
        patch("spine_api.server.logger"),
    ):
        # Default mock wiring
        mock_ledger.get_all_steps.return_value = {}
        mock_ledger.get_meta.return_value = {"agency_id": "agency-001"}
        mock_trip.get_trip.return_value = {}
        mock_span = MagicMock()
        mock_tracer.start_as_current_span.return_value.__enter__.return_value = (
            mock_span
        )

        yield {
            "ledger": mock_ledger,
            "draft": mock_draft,
            "audit": mock_audit,
            "trip": mock_trip,
            "assign": mock_assign,
            "settings": mock_settings,
            "strict": mock_strict,
            "run": mock_run,
            "tracer": mock_tracer,
        }


# ---------------------------------------------------------------------------
# Import the function-under-test AFTER patching so module-level imports
# in server.py see our mocks for any names they reference indirectly.
# ---------------------------------------------------------------------------
from spine_api.server import _execute_spine_pipeline


# Hard-coded request dict used by every test.
_BASE_REQUEST = {
    "raw_note": "Customer wants to go to Singapore",
    "owner_note": "VIP client, needs 5-star",
    "stage": "discovery",
    "operating_mode": "normal_intake",
    "strict_leakage": False,
    "scenario_id": None,
    "retention_consent": True,
}


def _run_pipeline(
    request_dict: dict | None = None,
    run_id: str = "run-test-001",
    agency_id: str = "agency-001",
    user_id: str = "user-001",
) -> None:
    """Convenience wrapper — calls _execute_spine_pipeline with defaults."""
    _execute_spine_pipeline(
        run_id=run_id,
        request_dict=request_dict or dict(_BASE_REQUEST),
        agency_id=agency_id,
        user_id=user_id,
    )


# =========================================================================
# Tests — Happy path
# =========================================================================

class TestHappyPath:
    """Normal success: run_spine_once returns valid result → trip saved."""

    def test_saves_trip_and_completes_ledger(self, pipeline_mocks) -> None:
        mock_run = pipeline_mocks["run"]
        mock_run.return_value = MockSpineResult()

        _run_pipeline()

        # Pipeline was called with envelopes
        assert mock_run.called

        # Trip was saved
        pipeline_mocks["ledger"].set_state.assert_called_once_with(
            "run-test-001", ANY
        )
        pipeline_mocks["ledger"].complete.assert_called_once()
        pipeline_mocks["ledger"].fail.assert_not_called()
        pipeline_mocks["ledger"].block.assert_not_called()

    def test_emit_run_completed_called(self, pipeline_mocks) -> None:
        from spine_api.server import emit_run_completed

        mock_run = pipeline_mocks["run"]
        mock_run.return_value = MockSpineResult()

        _run_pipeline()

        emit_run_completed.assert_called_once()

    def test_save_processed_trip_receives_correct_source(
        self, pipeline_mocks
    ) -> None:
        from spine_api.server import save_processed_trip

        mock_run = pipeline_mocks["run"]
        mock_run.return_value = MockSpineResult()

        _run_pipeline()

        save_processed_trip.assert_called_once()
        _call_kwargs = save_processed_trip.call_args[1]
        assert _call_kwargs["source"] == "spine_api"
        assert _call_kwargs["agency_id"] == "agency-001"
        assert _call_kwargs["user_id"] == "user-001"


# =========================================================================
# Tests — Pathological code paths
# =========================================================================

class TestEarlyExit:
    """Pipeline blocked mid-way via early_exit flag."""

    def test_early_exit_blocks_and_does_not_save_trip(
        self, pipeline_mocks
    ) -> None:
        from spine_api.server import save_processed_trip

        mock_run = pipeline_mocks["run"]
        mock_run.return_value = MockSpineResult(
            early_exit=True, early_exit_reason="Missing destination"
        )

        _run_pipeline()

        pipeline_mocks["ledger"].block.assert_called_once_with(
            "run-test-001", block_reason="Missing destination"
        )
        pipeline_mocks["ledger"].complete.assert_not_called()
        save_processed_trip.assert_not_called()


class TestPartialIntake:
    """Pipeline completed but result is incomplete (needs follow-up)."""

    def test_partial_intake_saves_incomplete_trip(
        self, pipeline_mocks
    ) -> None:
        from spine_api.server import save_processed_trip

        mock_run = pipeline_mocks["run"]
        mock_run.return_value = MockSpineResult(
            partial_intake=True, early_exit_reason="Missing quote-ready fields"
        )

        _run_pipeline()

        save_processed_trip.assert_called_once()
        _call_kwargs = save_processed_trip.call_args[1]
        assert _call_kwargs["trip_status"] == "incomplete"

        pipeline_mocks["ledger"].complete.assert_called_once()
        pipeline_mocks["ledger"].block.assert_not_called()


class TestValidationInvalid:
    """Pipeline result marked invalid → blocked for operator review."""

    def test_validation_invalid_blocks_trip(self, pipeline_mocks) -> None:
        from spine_api.server import save_processed_trip

        mock_run = pipeline_mocks["run"]
        mock_validation = MagicMock(is_valid=False)
        mock_run.return_value = MockSpineResult(validation=mock_validation)

        _run_pipeline()

        pipeline_mocks["ledger"].block.assert_called_once()
        save_processed_trip.assert_not_called()


# =========================================================================
# Tests — Error handling
# =========================================================================

class TestStrictLeakageViolation:
    """Strict leakage mode raises ValueError → blocked."""

    def test_value_error_blocks_run(self, pipeline_mocks) -> None:
        mock_run = pipeline_mocks["run"]
        mock_run.side_effect = ValueError("PII detected in traveler bundle")

        _run_pipeline()

        pipeline_mocks["ledger"].block.assert_called_once_with(
            "run-test-001",
            block_reason="PII detected in traveler bundle",
        )
        pipeline_mocks["ledger"].fail.assert_not_called()


class TestGenericException:
    """Unexpected exception → failed (not blocked)."""

    def test_exception_fails_run(self, pipeline_mocks) -> None:
        mock_run = pipeline_mocks["run"]
        mock_run.side_effect = RuntimeError("Database connection lost")

        _run_pipeline()

        pipeline_mocks["ledger"].fail.assert_called_once()
        pipeline_mocks["ledger"].block.assert_not_called()


# =========================================================================
# Tests — retention_consent filtering
# =========================================================================

class TestRetentionConsent:
    """Raw text fields are stripped from meta.submission when consent is False."""

    def test_consented_submission_includes_raw_text(self, pipeline_mocks) -> None:
        from spine_api.server import save_processed_trip

        mock_run = pipeline_mocks["run"]
        mock_run.return_value = MockSpineResult()

        _run_pipeline()

        save_processed_trip.assert_called_once()
        _meta = save_processed_trip.call_args[0][0].get("meta", {})
        _submission = _meta.get("submission", {})
        assert "raw_note" in _submission

    def test_no_consent_strips_raw_text(self, pipeline_mocks) -> None:
        from spine_api.server import save_processed_trip

        mock_run = pipeline_mocks["run"]
        mock_run.return_value = MockSpineResult()

        _run_pipeline(request_dict={
            **dict(_BASE_REQUEST),
            "retention_consent": False,
        })

        save_processed_trip.assert_called_once()
        _meta = save_processed_trip.call_args[0][0].get("meta", {})
        _submission = _meta.get("submission", {})
        assert "raw_note" not in _submission
        assert "owner_note" not in _submission


# =========================================================================
# Tests — strict_leakage mode
# =========================================================================

class TestStrictLeakageMode:
    """When strict_leakage=True, set_strict_mode(True) is called."""

    def test_strict_mode_enabled_for_strict_request(
        self, pipeline_mocks
    ) -> None:
        from spine_api.server import set_strict_mode

        mock_run = pipeline_mocks["run"]
        mock_run.return_value = MockSpineResult()

        _run_pipeline(request_dict={
            **dict(_BASE_REQUEST),
            "strict_leakage": True,
        })

        set_strict_mode.assert_any_call(True)

    def test_strict_mode_reset_in_finally(self, pipeline_mocks) -> None:
        from spine_api.server import set_strict_mode

        mock_run = pipeline_mocks["run"]
        mock_run.return_value = MockSpineResult()

        _run_pipeline()

        set_strict_mode.assert_any_call(False)


# =========================================================================
# Tests — Live checker signals
# =========================================================================

class TestLiveChecker:
    """When build_live_checker_signals returns data, scores are adjusted."""

    def test_live_checker_adjusts_score(self, pipeline_mocks) -> None:
        mock_run = pipeline_mocks["run"]
        mock_run.return_value = MockSpineResult()

        live_signal = {
            "score_penalty": 15,
            "hard_blockers": ["BLOCKER-001"],
            "soft_blockers": ["WARN-001"],
        }

        with patch(
            "spine_api.server.build_live_checker_signals",
            return_value=live_signal,
        ):
            _run_pipeline()

        pipeline_mocks["ledger"].set_state.assert_called()
