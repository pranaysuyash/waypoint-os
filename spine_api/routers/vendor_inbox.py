"""
spine_api/routers/vendor_inbox.py — B2 vendor quote inbox (map §5 B2; the last
reserved door in DOOR_CONTRACTS).

Vendors (DMCs, hotels, tour operators) send quotes to the AGENCY by email.
Before this router those quotes lived in operators' inboxes, invisible to the
system — the operator manually re-keyed numbers into the quotes flow, or missed
them. This is the supply-side counterpart of the B1 WhatsApp webhook:

  provider webhook (SendGrid Inbound Parse / generic JSON)
    → default-deny shared-secret verification (B1 pattern)
    → deterministic trip binding (explicit id or subject trip_ pattern —
      NEVER inferred from destination text; the origin-fabrication class)
    → deterministic body-signal extraction (amounts/currency/dates, stored as
      UNVERIFIED metadata signals — extraction never feeds facts or quotes)
    → message_store row (channel="vendor_email", idempotent on Message-ID)
    → vendor_quote_inbox door classification (origin=supply)
    → operator visibility via the channel-messages feed

Reality boundaries (honest, recorded):
- Attachment CONTENT is not parsed here: binary document parsing belongs to
  the multimodal document lane; this router records attachment presence
  (filename/mime) so the operator opens them in the existing pipeline.
- Extracted amounts are candidate signals only. Quotes enter the quotes read
  model exclusively through operator action (the money boundary: the system
  never moves or commits money on extraction).

Config (all optional — key-ready):
  VENDOR_INBOX_WEBHOOK_SECRET  — shared secret; unset → webhook 401s (default-deny)
  VENDOR_INBOX_AGENCY_ID       — agency binding for unauthenticated webhooks
                                 (falls back to MESSAGING_WEBHOOK_AGENCY_ID,
                                 then "webhook-unattributed", mirroring B1)
"""

from __future__ import annotations

import hmac
import logging
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import json

from fastapi import APIRouter, Depends, HTTPException, Request

from spine_api.core.auth import get_current_agency_id
from spine_api.persistence import AuditStore

logger = logging.getLogger("spine_api.vendor_inbox")

router = APIRouter(prefix="/api/v1/vendor-inbox", tags=["vendor-inbox"])
# B1-style split: the webhook is public (default-deny via shared secret —
# providers cannot present a JWT); the operator GET is JWT-gated at mount.
public_router = APIRouter(prefix="/api/v1/vendor-inbox", tags=["vendor-inbox-public"])

_EMAIL_ADDR_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
# Deterministic trip reference: the canonical trip id shape, matched only as a
# whole token. A vendor writing "trip for trip_abc123" binds; "Bali package"
# binds nothing.
_TRIP_ID_RE = re.compile(r"\b(trip_[a-z0-9_]{6,})\b", re.IGNORECASE)
# Amount signals: currency symbol/code + number (incl. k/lakh/crore units).
_AMOUNT_RE = re.compile(
    r"(?P<cur>₹|rs\.?|inr|\$|usd|€|eur|£|gbp)\s?(?P<amt>\d[\d,]*(?:\.\d+)?)\s*(?P<unit>k|lakh|lac|crore|cr)?",
    re.IGNORECASE,
)
_CURRENCY_MAP = {"₹": "INR", "rs": "INR", "inr": "INR", "$": "USD", "usd": "USD",
                 "€": "EUR", "eur": "EUR", "£": "GBP", "gbp": "GBP"}
_UNIT_MULT = {"k": 1_000, "thousand": 1_000, "lakh": 100_000, "lac": 100_000,
              "crore": 10_000_000, "cr": 10_000_000}


def _verify_webhook_token(presented: Optional[str]) -> bool:
    secret = os.environ.get("VENDOR_INBOX_WEBHOOK_SECRET", "")
    if not secret:
        return False  # default-deny: unconfigured → refuse
    if not presented:
        return False
    return hmac.compare_digest(presented, secret)


def _inbox_agency() -> str:
    return (
        os.environ.get("VENDOR_INBOX_AGENCY_ID", "").strip()
        or os.environ.get("MESSAGING_WEBHOOK_AGENCY_ID", "").strip()
        or "webhook-unattributed"
    )


def _extract_email_address(raw: str) -> str:
    m = _EMAIL_ADDR_RE.search(raw or "")
    return m.group(0) if m else (raw or "").strip()


def _extract_amounts(text: str) -> List[Dict[str, Any]]:
    """Deterministic amount signals from the quote text. Stored as UNVERIFIED
    metadata — never written to facts, packets, or the quotes read model."""
    signals: List[Dict[str, Any]] = []
    for m in _AMOUNT_RE.finditer(text or ""):
        cur_raw = m.group("cur").lower().rstrip(".")
        currency = _CURRENCY_MAP.get(cur_raw, cur_raw.upper())
        try:
            amount = float(m.group("amt").replace(",", ""))
        except ValueError:
            continue
        unit = (m.group("unit") or "").lower()
        if unit in _UNIT_MULT:
            amount *= _UNIT_MULT[unit]
        signals.append({
            "currency": currency,
            "amount": amount,
            "raw": m.group(0).strip(),
        })
    return signals[:20]  # bounded: a quote email does not carry 20 amounts


def _bind_trip(fields: Dict[str, str], agency_id: str) -> Optional[str]:
    """Deterministic trip binding: explicit field first, then a whole-token
    trip_ id in the subject or body, VALIDATED against the store. Returns
    None when nothing verifiable binds — never guesses from destination text."""
    from spine_api.persistence import TripStore

    candidates: List[str] = []
    if fields.get("trip_id"):
        candidates.append(fields["trip_id"].strip())
    for text in (fields.get("subject"), fields.get("body")):
        if text:
            m = _TRIP_ID_RE.search(text)
            if m:
                candidates.append(m.group(1))
    for trip_id in candidates:
        if TripStore.get_trip_for_agency(trip_id, agency_id):
            return trip_id
    return None


async def _read_webhook_fields(request: Request) -> Dict[str, Any]:
    """Accept both SendGrid Inbound Parse (multipart/form-data) and a plain
    JSON envelope — providers and tests should not need to care."""
    content_type = request.headers.get("content-type", "")
    if content_type.startswith("application/json"):
        body = await request.body()
        try:
            return json.loads(body.decode("utf-8")) if body else {}
        except Exception:
            return {}
    form = await request.form()
    fields: Dict[str, Any] = {}
    for key in ("from", "to", "subject", "text", "body-plain", "body_html",
                "Message-ID", "trip_id"):
        val = form.get(key)
        if val is not None:
            fields[key] = str(val)
    # SendGrid attachment metadata: count + names only (content not parsed).
    attachments_info: List[Dict[str, Any]] = []
    for i in range(1, 11):
        info = form.get(f"attachment-info{i if i > 1 else ''}")
        if info:
            try:
                parsed = json.loads(str(info))
                if isinstance(parsed, dict):
                    for a in parsed.values():
                        attachments_info.append({
                            "filename": a.get("filename"),
                            "type": a.get("type"),
                        })
            except Exception:
                continue
    n_files = form.get("attachments")
    if attachments_info:
        fields["attachments"] = attachments_info
    elif n_files:
        try:
            fields["attachments"] = [{"count": int(str(n_files))}]
        except ValueError:
            pass
    return fields


@public_router.post("/webhook", summary="Vendor quote email webhook (SendGrid Inbound Parse / generic JSON)")
async def vendor_inbox_webhook(request: Request) -> Dict[str, Any]:
    """Ingest a vendor quote email. Default-deny: 401 unless
    VENDOR_INBOX_WEBHOOK_SECRET is configured AND the X-Webhook-Token header
    matches (constant-time)."""
    if not _verify_webhook_token(request.headers.get("X-Webhook-Token")):
        raise HTTPException(
            status_code=401,
            detail="VENDOR_INBOX_WEBHOOK_SECRET is not configured or X-Webhook-Token is invalid; refusing unauthenticated payload",
        )

    fields = await _read_webhook_fields(request)
    subject = str(fields.get("subject") or "")
    body = str(fields.get("text") or fields.get("body-plain") or "")
    from_raw = str(fields.get("from") or "")
    vendor_email = _extract_email_address(from_raw)

    if not body and not subject and not fields.get("attachments"):
        return {"ok": True, "stored": 0, "skipped": 0, "reason": "empty payload — nothing ingestible"}

    agency_id = _inbox_agency()
    provider_message_id = str(fields.get("Message-ID") or "").strip() or None

    from spine_api.services import message_store
    from spine_api.services.work_intake import classify_and_record

    # B2 idempotency: email providers redeliver; one Message-ID lookup guards
    # the store row AND the work item (same contract as B1).
    if provider_message_id and message_store.find_by_provider_message_id(
        agency_id, provider_message_id
    ):
        return {"ok": True, "stored": 0, "duplicates_skipped": 1}

    trip_id = _bind_trip(
        {"trip_id": str(fields.get("trip_id") or ""), "subject": subject, "body": body},
        agency_id,
    )
    attachments = fields.get("attachments") or []
    extraction = {
        "amounts": _extract_amounts(f"{subject}\n{body}"),
        "unverified": True,
        "extracted_at": datetime.now(timezone.utc).isoformat(),
    }
    message_store.append_message(
        agency_id=agency_id,
        channel="vendor_email",
        direction="inbound",
        from_party=vendor_email or "unknown-vendor",
        to_party=str(fields.get("to") or agency_id),
        body=body or subject,
        trip_id=trip_id,
        mime="text/plain",
        filename=(attachments[0].get("filename") if attachments else None),
        provider_message_id=provider_message_id,
        received_at=None,
        metadata={
            "kind": "vendor_quote",
            "subject": subject,
            "vendor_email": vendor_email,
            "attachments": attachments,
            "extraction": extraction,
        },
    )

    # The reserved B2 door: origin=supply (the vendor's own document),
    # authority=explicit_user. Text deliberately None — a quote email is a
    # document, not an urgent message; urgency heuristics would misfire on
    # vendor phrasing, and PII heuristics add nothing (same reasoning as the
    # multimodal OCR leg).
    try:
        classify_and_record(
            "vendor_quote_inbox",
            agency_id=agency_id,
            text=None,
            contact=vendor_email or None,
            channel="vendor_email",
            trip_id=trip_id,
        )
    except Exception as exc:
        logger.debug("vendor_quote_inbox classification skipped: %s", exc)

    AuditStore.log_event(
        event_type="vendor_quote_ingested",
        user_id=agency_id,
        details={
            "vendor_email": vendor_email,
            "trip_id": trip_id,
            "provider_message_id": provider_message_id,
            "attachments": len(attachments),
            "amount_signals": len(extraction["amounts"]),
        },
    )
    return {
        "ok": True,
        "stored": 1,
        "trip_id": trip_id,
        "amount_signals": len(extraction["amounts"]),
        "attachments": len(attachments),
    }


@router.get("", summary="Operator view of the vendor quote inbox")
def list_vendor_quotes(
    agency_id: str = Depends(get_current_agency_id),
    limit: int = 100,
) -> Dict[str, Any]:
    """Vendor quotes received for this agency (channel=vendor_email), most
    recent first. Operators act on these through the existing quotes flow —
    the inbox is visibility + binding, not a quote source of truth."""
    from spine_api.services import message_store

    rows = message_store.list_for_agency(agency_id, channel="vendor_email", limit=max(1, min(limit, 500)))
    return {"ok": True, "quotes": rows, "total": len(rows)}
