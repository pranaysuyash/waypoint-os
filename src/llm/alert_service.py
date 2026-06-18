"""
llm.alert_service — Alert delivery for LLM usage guard events.

Sends notifications via email and/or webhook when guard thresholds are
breached or calls are blocked.  Designed for fire-and-forget delivery:
alert failures are logged but never block the caller.

Supported channels:
  - ``webhook``: POST a JSON payload to a URL.
  - ``email``:   SMTP-based delivery (stdlib ``smtplib``).

Configuration lives in env vars:
  LLM_ALERT_WEBHOOK_URLS   — comma-separated webhook endpoints
  LLM_ALERT_EMAIL_TO       — comma-separated recipient addresses
  LLM_ALERT_EMAIL_FROM     — sender address (default: no-reply@waypoint.ai)
  LLM_ALERT_EMAIL_SMTP     — SMTP host (default: localhost)
  LLM_ALERT_EMAIL_PORT     — SMTP port (default: 25)
  LLM_ALERT_EMAIL_USER     — SMTP username (optional)
  LLM_ALERT_EMAIL_PASSWORD — SMTP password (optional, prefer STARTTLS)
"""

from __future__ import annotations

import json
import logging
import os
import smtplib
import ssl
from dataclasses import dataclass, field
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional, Protocol

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Event types
# ---------------------------------------------------------------------------

class AlertEventType:
    """Canonical alert event types emitted by the usage guard."""
    THRESHOLD_WARNING = "threshold_warning"
    RATE_LIMIT_BLOCKED = "rate_limit_blocked"
    MODEL_RATE_LIMIT_BLOCKED = "model_rate_limit_blocked"
    BUDGET_EXCEEDED = "budget_exceeded"
    GUARD_UNAVAILABLE = "guard_unavailable"


@dataclass(slots=True)
class AlertPayload:
    """Structured alert to deliver."""
    event_type: str
    agency_id: str
    title: str
    detail: str
    severity: str = "warning"          # "warning" | "critical"
    model: str = ""
    feature: str = ""
    current_value: Optional[float] = None
    limit_value: Optional[float] = None
    metadata: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Channel protocols
# ---------------------------------------------------------------------------

class AlertChannel(Protocol):
    """Any alert delivery channel must implement this."""
    def send(self, payload: AlertPayload) -> bool: ...


# ---------------------------------------------------------------------------
# Webhook channel
# ---------------------------------------------------------------------------

class WebhookChannel:
    """POST alert payloads to one or more webhook URLs."""

    def __init__(self, urls: list[str], timeout_seconds: int = 10) -> None:
        self.urls = urls
        self.timeout = timeout_seconds

    def send(self, payload: AlertPayload) -> bool:
        import urllib.request

        body = json.dumps({
            "event_type": payload.event_type,
            "severity": payload.severity,
            "agency_id": payload.agency_id,
            "title": payload.title,
            "detail": payload.detail,
            "model": payload.model,
            "feature": payload.feature,
            "current_value": payload.current_value,
            "limit_value": payload.limit_value,
            "metadata": payload.metadata,
        }, default=str).encode()

        headers = {"Content-Type": "application/json"}
        any_ok = False

        for url in self.urls:
            try:
                req = urllib.request.Request(url, data=body, headers=headers, method="POST")
                ctx = ssl.create_default_context()
                with urllib.request.urlopen(req, timeout=self.timeout, context=ctx) as resp:
                    if resp.status < 300:
                        any_ok = True
                        logger.info("alert_webhook.delivered url=%s status=%d", url, resp.status)
                    else:
                        logger.warning("alert_webhook.failed url=%s status=%d", url, resp.status)
            except Exception as exc:
                logger.warning("alert_webhook.error url=%s error=%s", url, exc)

        return any_ok


# ---------------------------------------------------------------------------
# Email channel
# ---------------------------------------------------------------------------

class EmailChannel:
    """Send alert emails via SMTP."""

    def __init__(
        self,
        recipients: list[str],
        sender: str = "no-reply@waypoint.ai",
        smtp_host: str = "localhost",
        smtp_port: int = 25,
        smtp_user: Optional[str] = None,
        smtp_password: Optional[str] = None,
    ) -> None:
        self.recipients = recipients
        self.sender = sender
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password

    def send(self, payload: AlertPayload) -> bool:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"[Waypoint {payload.severity.upper()}] {payload.title}"
            msg["From"] = self.sender
            msg["To"] = ", ".join(self.recipients)

            text_body = (
                f"Event: {payload.event_type}\n"
                f"Agency: {payload.agency_id}\n"
                f"Severity: {payload.severity}\n"
                f"Detail: {payload.detail}\n"
            )
            if payload.model:
                text_body += f"Model: {payload.model}\n"
            if payload.current_value is not None and payload.limit_value is not None:
                text_body += f"Current: {payload.current_value} / Limit: {payload.limit_value}\n"

            html_body = text_body.replace("\n", "<br>\n")
            html_body = f"<html><body><pre>{html_body}</pre></body></html>"

            msg.attach(MIMEText(text_body, "plain"))
            msg.attach(MIMEText(html_body, "html"))

            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10) as server:
                if self.smtp_user and self.smtp_password:
                    server.starttls(context=ssl.create_default_context())
                    server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.sender, self.recipients, msg.as_string())

            logger.info("alert_email.delivered recipients=%s", self.recipients)
            return True
        except Exception as exc:
            logger.warning("alert_email.error recipients=%s error=%s", self.recipients, exc)
            return False


# ---------------------------------------------------------------------------
# Alert service
# ---------------------------------------------------------------------------

class AlertDeliveryService:
    """
    Fire-and-forget alert delivery for LLM guard events.

    Aggregates multiple channels and sends to all configured destinations.
    Alert delivery failures are logged but never raise.
    """

    def __init__(self, channels: Optional[list[AlertChannel]] = None) -> None:
        self.channels: list[AlertChannel] = channels or []

    def send(self, payload: AlertPayload) -> None:
        """Send alert to all channels. Never raises."""
        for channel in self.channels:
            try:
                channel.send(payload)
            except Exception as exc:
                logger.warning("alert_delivery.channel_error error=%s", exc)

    def send_threshold_warning(
        self,
        agency_id: str,
        model: str,
        feature: str,
        warning: str,
        current_cost: float,
        budget: float,
    ) -> None:
        """Convenience: send a budget threshold warning."""
        self.send(AlertPayload(
            event_type=AlertEventType.THRESHOLD_WARNING,
            agency_id=agency_id,
            title="LLM Budget Threshold Warning",
            detail=warning,
            severity="warning",
            model=model,
            feature=feature,
            current_value=current_cost,
            limit_value=budget,
        ))

    def send_rate_limit_blocked(
        self,
        agency_id: str,
        model: str,
        feature: str,
        reason: str,
        current_calls: int,
        limit: int,
    ) -> None:
        """Convenience: send a rate-limit block alert."""
        self.send(AlertPayload(
            event_type=AlertEventType.RATE_LIMIT_BLOCKED,
            agency_id=agency_id,
            title="LLM Rate Limit Exceeded",
            detail=reason,
            severity="critical",
            model=model,
            feature=feature,
            current_value=float(current_calls),
            limit_value=float(limit),
        ))

    def send_budget_exceeded(
        self,
        agency_id: str,
        model: str,
        feature: str,
        reason: str,
        projected_cost: float,
        budget: float,
    ) -> None:
        """Convenience: send a budget-exceeded alert."""
        self.send(AlertPayload(
            event_type=AlertEventType.BUDGET_EXCEEDED,
            agency_id=agency_id,
            title="LLM Daily Budget Exceeded",
            detail=reason,
            severity="critical",
            model=model,
            feature=feature,
            current_value=projected_cost,
            limit_value=budget,
        ))

    def send_guard_unavailable(self, agency_id: str, error: str) -> None:
        """Convenience: send a guard-storage failure alert."""
        self.send(AlertPayload(
            event_type=AlertEventType.GUARD_UNAVAILABLE,
            agency_id=agency_id,
            title="LLM Guard Storage Unavailable",
            detail=error,
            severity="critical",
        ))


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def alert_service_from_env() -> AlertDeliveryService:
    """Build an AlertDeliveryService from environment variables."""
    channels: list[AlertChannel] = []

    # Webhooks
    webhook_urls_raw = os.environ.get("LLM_ALERT_WEBHOOK_URLS", "").strip()
    if webhook_urls_raw:
        urls = [u.strip() for u in webhook_urls_raw.split(",") if u.strip()]
        if urls:
            channels.append(WebhookChannel(urls))

    # Email
    email_to_raw = os.environ.get("LLM_ALERT_EMAIL_TO", "").strip()
    if email_to_raw:
        recipients = [r.strip() for r in email_to_raw.split(",") if r.strip()]
        if recipients:
            channels.append(EmailChannel(
                recipients=recipients,
                sender=os.environ.get("LLM_ALERT_EMAIL_FROM", "no-reply@waypoint.ai"),
                smtp_host=os.environ.get("LLM_ALERT_EMAIL_SMTP", "localhost"),
                smtp_port=int(os.environ.get("LLM_ALERT_EMAIL_PORT", "25")),
                smtp_user=os.environ.get("LLM_ALERT_EMAIL_USER") or None,
                smtp_password=os.environ.get("LLM_ALERT_EMAIL_PASSWORD") or None,
            ))

    return AlertDeliveryService(channels)


def alert_service_from_settings(alert_destinations) -> AlertDeliveryService:
    """Build an AlertDeliveryService from persisted AlertDestinationsSettings.

    Falls back to env-var factory when no destinations are configured,
    preserving backward compatibility.
    """
    if not alert_destinations or not alert_destinations.enabled or not alert_destinations.destinations:
        return alert_service_from_env()

    channels: list[AlertChannel] = []
    severity_rank = {"warning": 1, "critical": 2}

    for dest in alert_destinations.destinations:
        if not dest.enabled:
            continue

        # Wrap each destination in a filter that checks severity + event_types
        min_sev = severity_rank.get(dest.min_severity, 1)
        allowed_events = set(dest.event_types) if dest.event_types else None

        if dest.type == "webhook" and dest.url:
            base_channel = WebhookChannel([dest.url])
            channels.append(_FilteredChannel(base_channel, min_sev, allowed_events))

        elif dest.type == "email" and dest.email_to:
            recipients = [r.strip() for r in dest.email_to.split(",") if r.strip()]
            if recipients:
                base_channel = EmailChannel(
                    recipients=recipients,
                    sender=dest.sender or "no-reply@waypoint.ai",
                    smtp_host=dest.smtp_host or "localhost",
                    smtp_port=dest.smtp_port or 25,
                    smtp_user=dest.smtp_user or None,
                    smtp_password=dest.smtp_password or None,
                )
                channels.append(_FilteredChannel(base_channel, min_sev, allowed_events))

    return AlertDeliveryService(channels)


class _FilteredChannel:
    """Wraps an AlertChannel with severity and event-type filtering."""

    def __init__(self, inner: AlertChannel, min_severity_rank: int, allowed_events: Optional[set[str]] = None) -> None:
        self._inner = inner
        self._min_severity_rank = min_severity_rank
        self._allowed_events = allowed_events

    def send(self, payload: AlertPayload) -> bool:
        sev_rank = {"warning": 1, "critical": 2}.get(payload.severity, 0)
        if sev_rank < self._min_severity_rank:
            return True  # Below threshold — skip silently
        if self._allowed_events is not None and payload.event_type not in self._allowed_events:
            return True  # Not in event type filter — skip silently
        return self._inner.send(payload)
