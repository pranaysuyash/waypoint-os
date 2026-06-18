"""Tests for llm.alert_service — P4-05 Alert Delivery."""

import json
import smtplib
import pytest
from unittest.mock import patch, MagicMock
from src.llm.alert_service import (
    AlertDeliveryService,
    AlertPayload,
    AlertEventType,
    WebhookChannel,
    EmailChannel,
    alert_service_from_env,
)
from src.llm.usage_guard import LLMUsageGuard, LLMUsageDecision


class TestAlertPayload:
    def test_creates_with_defaults(self):
        p = AlertPayload(
            event_type=AlertEventType.THRESHOLD_WARNING,
            agency_id="test-agency",
            title="Test",
            detail="Test detail",
        )
        assert p.severity == "warning"
        assert p.metadata == {}
        assert p.model == ""

    def test_creates_critical(self):
        p = AlertPayload(
            event_type=AlertEventType.BUDGET_EXCEEDED,
            agency_id="test",
            title="Budget",
            detail="Over",
            severity="critical",
        )
        assert p.severity == "critical"


class TestWebhookChannel:
    def test_send_success(self):
        with patch("urllib.request.urlopen") as mock_open:
            mock_resp = MagicMock()
            mock_resp.status = 200
            mock_resp.__enter__ = MagicMock(return_value=mock_resp)
            mock_resp.__exit__ = MagicMock(return_value=False)
            mock_open.return_value = mock_resp

            ch = WebhookChannel(["https://hooks.example.com/alert"])
            payload = AlertPayload(
                event_type=AlertEventType.THRESHOLD_WARNING,
                agency_id="a1", title="T", detail="D",
            )
            assert ch.send(payload) is True

    def test_send_failure_logs_and_returns_false(self):
        with patch("urllib.request.urlopen", side_effect=ConnectionError("refused")):
            ch = WebhookChannel(["https://bad.example.com"])
            payload = AlertPayload(
                event_type=AlertEventType.BUDGET_EXCEEDED,
                agency_id="a1", title="T", detail="D",
                severity="critical",
            )
            assert ch.send(payload) is False

    def test_multiple_urls_all_tried(self):
        with patch("urllib.request.urlopen") as mock_open:
            mock_resp = MagicMock()
            mock_resp.status = 200
            mock_resp.__enter__ = MagicMock(return_value=mock_resp)
            mock_resp.__exit__ = MagicMock(return_value=False)
            mock_open.return_value = mock_resp

            ch = WebhookChannel(["https://a.example.com", "https://b.example.com"])
            payload = AlertPayload(
                event_type=AlertEventType.RATE_LIMIT_BLOCKED,
                agency_id="a1", title="T", detail="D",
            )
            ch.send(payload)
            assert mock_open.call_count == 2


class TestEmailChannel:
    def test_send_success(self):
        with patch("smtplib.SMTP") as mock_smtp:
            server = MagicMock()
            mock_smtp.return_value.__enter__ = MagicMock(return_value=server)
            mock_smtp.return_value.__exit__ = MagicMock(return_value=False)

            ch = EmailChannel(recipients=["ops@example.com"])
            payload = AlertPayload(
                event_type=AlertEventType.GUARD_UNAVAILABLE,
                agency_id="a1", title="Guard down", detail="Storage failed",
                severity="critical",
            )
            assert ch.send(payload) is True
            server.sendmail.assert_called_once()

    def test_send_failure_returns_false(self):
        with patch("smtplib.SMTP", side_effect=smtplib.SMTPException("connection refused")):
            ch = EmailChannel(recipients=["ops@example.com"])
            payload = AlertPayload(
                event_type=AlertEventType.THRESHOLD_WARNING,
                agency_id="a1", title="T", detail="D",
            )
            assert ch.send(payload) is False

    def test_tls_login_when_credentials(self):
        with patch("smtplib.SMTP") as mock_smtp:
            server = MagicMock()
            ctx = MagicMock()
            mock_smtp.return_value.__enter__ = MagicMock(return_value=server)
            mock_smtp.return_value.__exit__ = MagicMock(return_value=False)

            ch = EmailChannel(
                recipients=["ops@example.com"],
                smtp_host="smtp.example.com",
                smtp_port=587,
                smtp_user="user",
                smtp_password="pass",
            )
            payload = AlertPayload(
                event_type=AlertEventType.THRESHOLD_WARNING,
                agency_id="a1", title="T", detail="D",
            )
            ch.send(payload)
            server.starttls.assert_called_once()
            server.login.assert_called_once_with("user", "pass")


class TestAlertDeliveryService:
    def test_send_no_channels(self):
        svc = AlertDeliveryService([])
        # Should not raise
        svc.send(AlertPayload(
            event_type=AlertEventType.THRESHOLD_WARNING,
            agency_id="a1", title="T", detail="D",
        ))

    def test_send_all_channels_called(self):
        ch1 = MagicMock()
        ch2 = MagicMock()
        svc = AlertDeliveryService([ch1, ch2])
        payload = AlertPayload(
            event_type=AlertEventType.RATE_LIMIT_BLOCKED,
            agency_id="a1", title="T", detail="D",
        )
        svc.send(payload)
        ch1.send.assert_called_once_with(payload)
        ch2.send.assert_called_once_with(payload)

    def test_channel_error_does_not_propagate(self):
        ch = MagicMock()
        ch.send.side_effect = RuntimeError("boom")
        svc = AlertDeliveryService([ch])
        svc.send(AlertPayload(
            event_type=AlertEventType.BUDGET_EXCEEDED,
            agency_id="a1", title="T", detail="D",
            severity="critical",
        ))

    def test_send_threshold_warning(self):
        ch = MagicMock()
        svc = AlertDeliveryService([ch])
        svc.send_threshold_warning("a1", "gpt-4", "chat", "80% used", 80.0, 100.0)
        sent = ch.send.call_args[0][0]
        assert sent.event_type == AlertEventType.THRESHOLD_WARNING
        assert sent.agency_id == "a1"
        assert sent.current_value == 80.0
        assert sent.limit_value == 100.0

    def test_send_rate_limit_blocked(self):
        ch = MagicMock()
        svc = AlertDeliveryService([ch])
        svc.send_rate_limit_blocked("a1", "gemini", "extract", "95/100", 95, 100)
        sent = ch.send.call_args[0][0]
        assert sent.event_type == AlertEventType.RATE_LIMIT_BLOCKED
        assert sent.severity == "critical"
        assert sent.current_value == 95.0
        assert sent.limit_value == 100.0

    def test_send_budget_exceeded(self):
        ch = MagicMock()
        svc = AlertDeliveryService([ch])
        svc.send_budget_exceeded("a1", "gpt-4", "plan", "over budget", 150.0, 100.0)
        sent = ch.send.call_args[0][0]
        assert sent.event_type == AlertEventType.BUDGET_EXCEEDED
        assert sent.severity == "critical"

    def test_send_guard_unavailable(self):
        ch = MagicMock()
        svc = AlertDeliveryService([ch])
        svc.send_guard_unavailable("a1", "Redis down")
        sent = ch.send.call_args[0][0]
        assert sent.event_type == AlertEventType.GUARD_UNAVAILABLE
        assert sent.severity == "critical"


class TestAlertServiceFromEnv:
    def test_no_channels_when_no_env(self):
        with patch.dict("os.environ", {}, clear=False):
            svc = alert_service_from_env()
            assert len(svc.channels) == 0

    def test_webhook_from_env(self):
        env = {"LLM_ALERT_WEBHOOK_URLS": "https://a.com, https://b.com"}
        with patch.dict("os.environ", env, clear=False):
            svc = alert_service_from_env()
            assert len(svc.channels) == 1
            assert isinstance(svc.channels[0], WebhookChannel)
            assert len(svc.channels[0].urls) == 2

    def test_email_from_env(self):
        env = {
            "LLM_ALERT_EMAIL_TO": "ops@ex.com, admin@ex.com",
            "LLM_ALERT_EMAIL_SMTP": "smtp.ex.com",
            "LLM_ALERT_EMAIL_PORT": "587",
            "LLM_ALERT_EMAIL_USER": "user",
            "LLM_ALERT_EMAIL_PASSWORD": "pass",
        }
        with patch.dict("os.environ", env, clear=False):
            svc = alert_service_from_env()
            assert len(svc.channels) == 1
            assert isinstance(svc.channels[0], EmailChannel)
            assert svc.channels[0].smtp_host == "smtp.ex.com"

    def test_both_channels(self):
        env = {
            "LLM_ALERT_WEBHOOK_URLS": "https://a.com",
            "LLM_ALERT_EMAIL_TO": "ops@ex.com",
        }
        with patch.dict("os.environ", env, clear=False):
            svc = alert_service_from_env()
            assert len(svc.channels) == 2


class TestGuardIntegration:
    """Test that the guard fires alerts on threshold warnings and blocks."""

    def test_guard_sends_threshold_warning(self):
        alerts = MagicMock()
        guard = LLMUsageGuard(
            enabled=True,
            agency_id="test",
            daily_budget=100.0,
            budget_mode="warn",
            budget_warning_thresholds=[0.8],
        )
        guard.set_alert_service(alerts)

        # Mock the store to return a warning
        mock_reservation = {
            "event_id": "e1",
            "daily_cost": 85.0,
            "projected_cost": 85.0,
            "hourly_calls": 5,
            "warnings": ["Budget at 85% (threshold: 80%)"],
        }
        guard.store = MagicMock()
        guard.store.check_and_reserve.return_value = mock_reservation

        decision = guard.check_before_call(model="gpt-4", estimated_cost=1.0, feature="chat")
        assert decision.allowed is True
        alerts.send_threshold_warning.assert_called_once()

    def test_guard_sends_block_alert(self):
        alerts = MagicMock()
        guard = LLMUsageGuard(
            enabled=True,
            agency_id="test",
            max_calls_per_hour=10,
            budget_mode="warn",
        )
        guard.set_alert_service(alerts)

        mock_reservation = {
            "event_id": "e1",
            "block_reason": "rate_limit_exceeded",
            "hourly_calls": 10,
            "daily_cost": 5.0,
            "projected_cost": 5.0,
        }
        guard.store = MagicMock()
        guard.store.check_and_reserve.return_value = mock_reservation

        decision = guard.check_before_call(model="gpt-4", estimated_cost=1.0, feature="chat")
        assert decision.allowed is False
        alerts.send_rate_limit_blocked.assert_called_once()

    def test_guard_sends_guard_unavailable_alert(self):
        from src.llm.usage_store import GuardStorageError
        alerts = MagicMock()
        guard = LLMUsageGuard(enabled=True, agency_id="test")
        guard.set_alert_service(alerts)

        guard.store = MagicMock()
        guard.store.check_and_reserve.side_effect = GuardStorageError("DB down")

        decision = guard.check_before_call(model="gpt-4", estimated_cost=1.0, feature="chat")
        assert decision.allowed is False
        assert decision.block_reason == "guard_unavailable"
        alerts.send_guard_unavailable.assert_called_once()

    def test_guard_no_alerts_when_not_configured(self):
        guard = LLMUsageGuard(
            enabled=True,
            agency_id="test",
            daily_budget=100.0,
            budget_mode="warn",
            budget_warning_thresholds=[0.8],
        )
        # No alert service attached
        mock_reservation = {
            "event_id": "e1",
            "daily_cost": 85.0,
            "projected_cost": 85.0,
            "hourly_calls": 5,
            "warnings": ["Budget at 85%"],
        }
        guard.store = MagicMock()
        guard.store.check_and_reserve.return_value = mock_reservation

        decision = guard.check_before_call(model="gpt-4", estimated_cost=1.0, feature="chat")
        assert decision.allowed is True  # Should still work without alerts
