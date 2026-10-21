"""
spine_api/routers/messages.py — Channel message read model (T6, FND-0305).

Serves what the webhook persisted so operators can finally consume inbound
WhatsApp/SMS content:

- GET /api/v1/messages                — agency-wide feed (newest first)
- GET /api/v1/trips/{trip_id}/messages — trip-scoped (records linked to the
  trip at write time, plus digit-normalized phone matches against the trip's
  contact fields)

Auth: JWT agency scope, same as the rest of the operator surface.
"""

from __future__ import annotations

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from spine_api.core.auth import get_current_agency
from spine_api.models.tenant import Agency
from spine_api.persistence import TripStore
from spine_api.services import message_store

logger = logging.getLogger("spine_api.messages")

router = APIRouter(prefix="/api/v1", tags=["messages"])


def _trip_phones(trip: dict) -> List[str]:
    phones: List[str] = []
    packet = trip.get("packet") or {}
    for source in (trip, packet):
        for field in ("contact_phone", "customer_phone", "phone"):
            raw = source.get(field)
            normalized = message_store.normalize_phone(str(raw or "")) if raw else ""
            if normalized and normalized not in phones:
                phones.append(normalized)
    return phones


@router.get("/messages")
def list_agency_messages(
    channel: Optional[str] = None,
    limit: int = Query(default=100, ge=1, le=500),
    agency: Agency = Depends(get_current_agency),
) -> dict:
    """Agency-wide inbound/outbound channel message feed (newest first)."""
    messages = message_store.list_for_agency(agency.id, channel=channel, limit=limit)
    return {"ok": True, "messages": messages, "count": len(messages)}


@router.get("/trips/{trip_id}/messages")
def list_trip_messages(
    trip_id: str,
    limit: int = Query(default=100, ge=1, le=500),
    agency: Agency = Depends(get_current_agency),
) -> dict:
    """Messages for one trip: explicit trip_id records + phone-matched records."""
    trip = TripStore.get_trip_for_agency(trip_id, agency.id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    explicit = message_store.list_for_agency(agency.id, trip_id=trip_id, limit=limit)
    explicit_ids = {m.get("message_id") for m in explicit}

    matched: List[dict] = []
    trip_phones = _trip_phones(trip)
    if trip_phones:
        for message in message_store.list_for_agency(agency.id, limit=500):
            if message.get("message_id") in explicit_ids:
                continue
            from_norm = message_store.normalize_phone(str(message.get("from_party") or ""))
            to_norm = message_store.normalize_phone(str(message.get("to_party") or ""))
            if from_norm in trip_phones or to_norm in trip_phones:
                matched.append(message)

    combined = sorted(
        explicit + matched,
        key=lambda m: m.get("received_at") or "",
        reverse=True,
    )[:limit]
    return {"ok": True, "trip_id": trip_id, "messages": combined, "count": len(combined)}
