"""
spine_api.services.message_dispatch — Real outbound provider dispatch.

T1 slice (FND-0301): the messaging router previously returned an honest
"QUEUED" without any provider call. This service makes the dispatch real when
provider credentials exist, and keeps the response honest when they do not
(``NOT_CONFIGURED``) or when the provider rejects the send (``FAILED``).
It never fabricates ``SENT``.

Design boundaries:
- Credentials are env-driven (zero-implicit-defaults, ADR-008 §7); no creds
  means no dispatch and a truthful status, never a simulated success.
- The service is transport-only: message composition stays with callers
  (messaging router, followups send) so content policy lives in one place
  per surface.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger("spine_api.message_dispatch")

WHATSAPP_GRAPH_URL = "https://graph.facebook.com/v21.0"
SENDGRID_API_URL = "https://api.sendgrid.com/v3/mail/send"
DISPATCH_TIMEOUT_SECONDS = 10.0


def _whatsapp_credentials() -> Optional[tuple[str, str]]:
    token = os.getenv("WHATSAPP_ACCESS_TOKEN", "").strip()
    phone_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "").strip()
    if token and phone_id:
        return token, phone_id
    return None


def _sendgrid_credentials() -> Optional[str]:
    key = os.getenv("SENDGRID_API_KEY", "").strip()
    return key or None


def dispatch_outbound_message(*, recipient: str, channel: str, content: str) -> Dict[str, Any]:
    """Attempt real provider dispatch for one outbound message.

    Returns a dict with:
      - dispatch_status: SENT | FAILED | NOT_CONFIGURED | UNSUPPORTED
      - provider: canonical provider name for the channel
      - detail: human-readable context for audit logs (never contains creds)

    This function performs network I/O only when credentials are present.
    """
    channel_key = (channel or "").strip().lower()

    if channel_key == "whatsapp":
        provider = "whatsapp_cloud_api"
        creds = _whatsapp_credentials()
        if creds is None:
            return {
                "dispatch_status": "NOT_CONFIGURED",
                "provider": provider,
                "detail": "WHATSAPP_ACCESS_TOKEN / WHATSAPP_PHONE_NUMBER_ID not set",
            }
        token, phone_number_id = creds
        payload = {
            "messaging_product": "whatsapp",
            "to": recipient,
            "type": "text",
            "text": {"preview_url": False, "body": content},
        }
        try:
            response = httpx.post(
                f"{WHATSAPP_GRAPH_URL}/{phone_number_id}/messages",
                headers={"Authorization": f"Bearer {token}"},
                json=payload,
                timeout=DISPATCH_TIMEOUT_SECONDS,
            )
        except httpx.HTTPError as exc:
            logger.warning("WhatsApp dispatch error: %s", exc)
            return {"dispatch_status": "FAILED", "provider": provider, "detail": f"{type(exc).__name__}"}
        if response.status_code < 300:
            return {"dispatch_status": "SENT", "provider": provider, "detail": "accepted by Cloud API"}
        return {
            "dispatch_status": "FAILED",
            "provider": provider,
            "detail": f"provider HTTP {response.status_code}",
        }

    if channel_key == "email":
        provider = "sendgrid_email"
        api_key = _sendgrid_credentials()
        if api_key is None:
            return {
                "dispatch_status": "NOT_CONFIGURED",
                "provider": provider,
                "detail": "SENDGRID_API_KEY not set",
            }
        sender = os.getenv("SENDGRID_FROM_EMAIL", "").strip() or "no-reply@waypointos.local"
        payload = {
            "personalizations": [{"to": [{"email": recipient}]}],
            "from": {"email": sender},
            "subject": "Your travel plans — a quick question",
            "content": [{"type": "text/plain", "value": content}],
        }
        try:
            response = httpx.post(
                SENDGRID_API_URL,
                headers={"Authorization": f"Bearer {api_key}"},
                json=payload,
                timeout=DISPATCH_TIMEOUT_SECONDS,
            )
        except httpx.HTTPError as exc:
            logger.warning("SendGrid dispatch error: %s", exc)
            return {"dispatch_status": "FAILED", "provider": provider, "detail": f"{type(exc).__name__}"}
        if response.status_code < 300:
            return {"dispatch_status": "SENT", "provider": provider, "detail": "accepted by SendGrid"}
        return {
            "dispatch_status": "FAILED",
            "provider": provider,
            "detail": f"provider HTTP {response.status_code}",
        }

    return {
        "dispatch_status": "UNSUPPORTED",
        "provider": "none",
        "detail": f"channel '{channel}' has no dispatch adapter",
    }
