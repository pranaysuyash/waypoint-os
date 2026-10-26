"""
spine_api.services.message_store — Durable inbound channel message store (T6, FND-0305).

The messaging webhook previously processed delivery statuses and concierge
replies but never persisted the traveler's actual message anywhere queryable —
operators had no way to consume WhatsApp/SMS content that the system claims to
ingest (FND-0305). This store is the durable record.

Design:
- Append-only JSONL, one file per agency (``{dir}/{agency_id}.jsonl``),
  directory overridable via ``WAYPOINT_MESSAGES_DIR`` (default ``data/messages``).
  Mirrors the run-ledger durability pattern; crash-safe appends.
- Records carry ``direction`` (inbound|outbound), channel, phone parties, body,
  optional media metadata, and a ``trip_id`` when a trip could be resolved.
- Trip resolution is digit-normalized phone matching against the trip's
  contact fields (contact_phone/customer_phone) — explicit, bounded, and
  never guesses: an unmatched message keeps ``trip_id: null`` and stays
  visible in the agency feed.
"""

from __future__ import annotations

import json
import logging
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

logger = logging.getLogger("spine_api.message_store")

_WRITE_LOCK = threading.Lock()


def messages_dir() -> Path:
    override = os.getenv("WAYPOINT_MESSAGES_DIR", "").strip()
    base = Path(override) if override else Path("data/messages")
    base.mkdir(parents=True, exist_ok=True)
    return base


def _agency_path(agency_id: str) -> Path:
    safe = "".join(ch for ch in agency_id if ch.isalnum() or ch in "-_") or "unknown"
    return messages_dir() / f"{safe}.jsonl"


def normalize_phone(phone: str) -> str:
    """Digits only — the stable comparison form across + prefixes and spaces."""
    return "".join(ch for ch in (phone or "") if ch.isdigit())


def append_message(
    *,
    agency_id: str,
    channel: str,
    direction: str,
    from_party: str,
    to_party: str,
    body: str,
    trip_id: Optional[str] = None,
    mime: Optional[str] = None,
    filename: Optional[str] = None,
    provider_message_id: Optional[str] = None,
    reply_to_provider_message_id: Optional[str] = None,
    received_at: Optional[str] = None,
) -> Dict[str, Any]:
    """Persist one channel message. Returns the stored record."""
    record: Dict[str, Any] = {
        "message_id": f"msg_{uuid4().hex[:12]}",
        "provider_message_id": provider_message_id,
        "reply_to_provider_message_id": reply_to_provider_message_id,
        "agency_id": agency_id,
        "trip_id": trip_id,
        "channel": channel,
        "direction": direction,
        "from_party": from_party,
        "to_party": to_party,
        "body": (body or "")[:8000],
        "mime": mime,
        "filename": filename,
        "received_at": received_at or datetime.now(timezone.utc).isoformat(),
    }
    path = _agency_path(agency_id)
    with _WRITE_LOCK:
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record


def list_for_agency(
    agency_id: str,
    *,
    trip_id: Optional[str] = None,
    channel: Optional[str] = None,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """Most-recent-first message list for an agency, optionally filtered."""
    path = _agency_path(agency_id)
    if not path.exists():
        return []
    out: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if trip_id is not None and rec.get("trip_id") != trip_id:
                continue
            if channel is not None and rec.get("channel") != channel:
                continue
            out.append(rec)
    out.sort(key=lambda r: r.get("received_at") or "", reverse=True)
    return out[: max(1, limit)]


def find_by_provider_message_id(agency_id: str, provider_message_id: str) -> Optional[Dict[str, Any]]:
    """Most recent stored message row for a provider message id, or None.

    The B1 idempotency anchor: Meta redelivers webhooks at-least-once, so the
    webhook orchestration checks here before storing, classifying, or replying
    — one lookup protects all three downstream consumers from duplicates.
    """
    if not provider_message_id:
        return None
    path = _agency_path(agency_id)
    if not path.exists():
        return None
    found: Optional[Dict[str, Any]] = None
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("provider_message_id") == provider_message_id:
                found = rec  # appends are chronological; last write wins
    return found


def apply_provider_status(
    agency_id: str,
    provider_message_id: str,
    status: str,
    *,
    error: Optional[str] = None,
) -> Dict[str, Any]:
    """Attach provider delivery truth (sent/delivered/read/failed) to the
    stored OUTBOUND row for ``provider_message_id``. Statuses describe messages
    the business sent, so matching is pinned to direction="outbound" — reply
    rows that thread via reply_to_provider_message_id never collide. Rewrites
    that one line under the store lock (bounded, same durability pattern as
    work_intake.record_outcome). Returns ``{"updated": bool}`` — an unmatched
    id is honest (the outbound went through another path); callers log and
    move on, never fabricate a row."""
    if not provider_message_id or not status:
        return {"updated": False}
    path = _agency_path(agency_id)
    if not path.exists():
        return {"updated": False}
    updated = False
    with _WRITE_LOCK:
        lines: List[str] = []
        with path.open("r", encoding="utf-8") as fh:
            for line in fh:
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    rec = json.loads(stripped)
                except json.JSONDecodeError:
                    lines.append(stripped)
                    continue
                if (
                    rec.get("provider_message_id") == provider_message_id
                    and rec.get("direction") == "outbound"
                ):
                    rec["delivery_status"] = status
                    rec["delivery_detail"] = error
                    rec["delivery_status_at"] = datetime.now(timezone.utc).isoformat()
                    updated = True
                lines.append(json.dumps(rec, ensure_ascii=False))
        if updated:
            with path.open("w", encoding="utf-8") as fh:
                for line in lines:
                    fh.write(line + "\n")
    return {"updated": updated}


def match_trip_by_phone(agency_id: str, phone: str) -> Optional[str]:
    """Resolve a trip for an inbound phone via digit-normalized contact match.

    One bounded scan (200 rows); covers top-level, packet, extracted facts,
    and customer_contact fields. Conservative: no phone match means no trip
    linkage, never a guess.
    """
    try:
        from spine_api.persistence import TripStore

        wanted = normalize_phone(phone)
        if not wanted:
            return None
        for trip in TripStore.list_trips(limit=200, agency_id=agency_id):
            packet = trip.get("packet") or {}
            extracted = trip.get("extracted") or {}
            facts = extracted.get("facts") if isinstance(extracted, dict) else {}
            if not isinstance(facts, dict):
                facts = {}
            for source in (trip, packet, extracted):
                if not isinstance(source, dict):
                    continue
                for field in ("contact_phone", "customer_phone", "phone", "mobile", "customer_contact"):
                    val = source.get(field)
                    if isinstance(val, str):
                        trip_phone = normalize_phone(val)
                        if trip_phone and trip_phone == wanted:
                            return trip.get("id")
            for fact_key in ("customer_contact", "contact_phone", "customer_phone", "phone"):
                fact = facts.get(fact_key)
                if isinstance(fact, dict):
                    val = fact.get("value")
                    if isinstance(val, str):
                        trip_phone = normalize_phone(val)
                        if trip_phone and trip_phone == wanted:
                            return trip.get("id")
    except Exception as exc:
        logger.warning("message_store trip phone match failed: %s", exc)
    return None
