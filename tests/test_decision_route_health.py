"""Tests for decision route health evaluation and alerting (G-02 / ADR-008 item 6)."""

from unittest.mock import patch

from src.decision.route_health import _MIN_SAMPLES, _recent, record_and_evaluate
from src.decision.telemetry import DecisionTelemetry


def setup_function():
    """Reset the rolling window between test cases."""
    _recent.clear()


def test_insufficient_samples_does_not_evaluate():
    with patch("src.decision.route_health._emit_alert") as mock_emit:
        for i in range(_MIN_SAMPLES - 1):
            record_and_evaluate("test_decision", source="default", latency_ms=10.0)
        assert len(_recent) == _MIN_SAMPLES - 1
        mock_emit.assert_not_called()


def test_healthy_decision_route_does_not_alert():
    with patch("src.decision.route_health._emit_alert") as mock_emit:
        for _ in range(15):
            record_and_evaluate("test_decision", source="rule", latency_ms=15.0)
        assert len(_recent) == 15
        mock_emit.assert_not_called()


def test_high_default_fallback_emits_warning():
    with patch("src.decision.route_health._emit_alert") as mock_emit:
        # 4 defaults out of 10 = 40% (>= 30% warning threshold)
        for _ in range(6):
            record_and_evaluate("test_decision", source="rule", latency_ms=10.0)
        for _ in range(4):
            record_and_evaluate("test_decision", source="default", latency_ms=10.0)

        assert mock_emit.called
        call_kwargs = mock_emit.call_args.kwargs
        assert call_kwargs["status"] == "warning"
        assert call_kwargs["metrics"]["default_fallback_rate"] == 0.4


def test_critical_default_fallback_emits_critical():
    with patch("src.decision.route_health._emit_alert") as mock_emit:
        # 6 defaults out of 10 = 60% (>= 50% critical threshold)
        for _ in range(4):
            record_and_evaluate("test_decision", source="rule", latency_ms=10.0)
        for _ in range(6):
            record_and_evaluate("test_decision", source="default", latency_ms=10.0)

        assert mock_emit.called
        call_kwargs = mock_emit.call_args.kwargs
        assert call_kwargs["status"] == "critical"
        assert call_kwargs["metrics"]["default_fallback_rate"] == 0.6


def test_high_error_rate_emits_warning_and_critical():
    with patch("src.decision.route_health._emit_alert") as mock_emit:
        # 3 errors out of 10 = 30% (>= 20% warning threshold)
        for _ in range(7):
            record_and_evaluate("test_decision", source="rule", latency_ms=10.0)
        for _ in range(3):
            record_and_evaluate("test_decision", source="rule", latency_ms=10.0, error="boom")

        assert mock_emit.called
        call_kwargs = mock_emit.call_args.kwargs
        assert call_kwargs["status"] == "warning"
        assert call_kwargs["metrics"]["error_rate"] == 0.3


def test_telemetry_record_decision_integration():
    telemetry = DecisionTelemetry()
    with patch("src.decision.route_health.record_and_evaluate") as mock_rae:
        telemetry.record_decision(
            decision_type="strategy",
            source="rule",
            latency_ms=12.5,
            cache_hit=False,
            llm_used=False,
            error=None,
        )
        mock_rae.assert_called_once_with(
            decision_type="strategy",
            source="rule",
            latency_ms=12.5,
            error=None,
        )
