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

WHATSAPP_GRAPH_URL = "https://graph.facebook.com/v25.0"
SENDGRID_API_URL = "https://api.sendgrid.com/v3/mail/send"
DISPATCH_TIMEOUT_SECONDS = 10.0
# Meta Cloud API rejects text bodies over 4096 chars — fail before the network
# call so the operator sees the real reason, not a provider 400.
WHATSAPP_MAX_BODY_CHARS = 4096


def _whatsapp_credentials() -> Optional[tuple[str, str]]:
    token = os.getenv("WHATSAPP_ACCESS_TOKEN", "").strip()
    phone_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "").strip()
    if token and phone_id:
        return token, phone_id
    return None


def _sendgrid_credentials() -> Optional[str]:
    key = os.getenv("SENDGRID_API_KEY", "").strip()
    return key or None


def dispatch_outbound_message(
    *, recipient: str, channel: str, content: str, agency_id: str | None = None,
    whatsapp_inbox_id: str | None = None, callback_id: str | None = None,
) -> Dict[str, Any]:
    """Attempt real provider dispatch for one outbound message.

    Returns a dict with:
      - dispatch_status: SENT | FAILED | DELIVERY_UNKNOWN | NOT_CONFIGURED | STAFF_REVIEW_REQUIRED | UNSUPPORTED
      - provider: canonical provider name for the channel
      - detail: human-readable context for audit logs (never contains creds)

    This function performs network I/O only when credentials are present.
    """
    channel_key = (channel or "").strip().lower()

    if channel_key == "whatsapp":
        provider = "whatsapp_cloud_api"
        # Pre-flight guards: invalid content is invalid regardless of creds,
        # and Meta's `to` is digits-only (no '+', spaces, or dashes).
        if len(content or "") > WHATSAPP_MAX_BODY_CHARS:
            return {
                "dispatch_status": "FAILED",
                "provider": provider,
                "detail": f"body exceeds WhatsApp {WHATSAPP_MAX_BODY_CHARS}-char limit",
            }
        recipient_digits = "".join(ch for ch in (recipient or "") if ch.isdigit())
        if not recipient_digits:
            return {
                "dispatch_status": "FAILED",
                "provider": provider,
                "detail": "recipient has no phone digits",
            }
        creds = _whatsapp_credentials()
        if creds is None:
            return {
                "dispatch_status": "NOT_CONFIGURED",
                "provider": provider,
                "detail": "WHATSAPP_ACCESS_TOKEN / WHATSAPP_PHONE_NUMBER_ID not set",
            }
        token, phone_number_id = creds
        # Only the managed WhatsApp dispatch path has a claimed, tenant-bound
        # attempt. Legacy manual surfaces can still provide a link for sharing.
        from spine_api.services.whatsapp_journal import bound_inbox

        if not agency_id or not callback_id or whatsapp_inbox_id != phone_number_id or bound_inbox(agency_id) != phone_number_id:
            return {
                "dispatch_status": "STAFF_REVIEW_REQUIRED", "provider": provider,
                "detail": "Send through the agency's managed WhatsApp conversation",
            }
        payload = {
            "messaging_product": "whatsapp",
            "to": recipient_digits,
            "type": "text",
            "text": {"preview_url": False, "body": content},
            "biz_opaque_callback_data": callback_id,
        }
        try:
            response = httpx.post(
                f"{WHATSAPP_GRAPH_URL}/{phone_number_id}/messages",
                headers={"Authorization": f"Bearer {token}"},
                json=payload,
                timeout=DISPATCH_TIMEOUT_SECONDS,
            )
        except httpx.HTTPError as exc:
            logger.warning("WhatsApp transport result unavailable: %s", type(exc).__name__)
            return {"dispatch_status": "DELIVERY_UNKNOWN", "provider": provider, "detail": type(exc).__name__}
        if 200 <= response.status_code < 300:
            # Capture Meta's provider-assigned message id: delivery statuses
            # arrive keyed by THIS id, so the caller stores outbound rows with
            # it (reply threading rides a separate reply_to field).
            provider_message_id = None
            try:
                body = response.json()
                messages = body.get("messages") if isinstance(body, dict) else None
                if isinstance(messages, list) and messages and isinstance(messages[0], dict):
                    provider_message_id = str(messages[0].get("id") or "") or None
            except Exception:
                provider_message_id = None
            return {
                "dispatch_status": "SENT" if provider_message_id else "DELIVERY_UNKNOWN",
                "provider": provider,
                "detail": "accepted by Cloud API" if provider_message_id else "Provider response did not contain a message ID",
                "provider_message_id": provider_message_id,
            }
        return {
            "dispatch_status": "FAILED" if 400 <= response.status_code < 500 and response.status_code != 408 else "DELIVERY_UNKNOWN",
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
