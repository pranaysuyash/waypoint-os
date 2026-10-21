"""
spine_api/routers/dsr.py — Data-subject rights endpoints for trips (T14).

  GET  /api/v1/trips/{trip_id}/data-export  — Art. 15/20 portable export
  POST /api/v1/trips/{trip_id}/erasure      — Art. 17 structural erasure

Both are agency-authenticated and tenant-scoped. Erasure is destructive:
requires ``trips:write`` permission and an explicit ``confirm: true`` body,
and is audit-logged with the signed certificate id (never the personal
content itself).
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from spine_api.core.auth import get_current_agency, require_permission
from spine_api.models.tenant import Agency
from spine_api.persistence import AuditStore, TripStore
from spine_api.services import message_store
from spine_api.services.trip_dsr import (
    _norm,
    erase_trip_personal_data,
    export_trip_personal_data,
)

logger = logging.getLogger("spine_api.dsr")

router = APIRouter(prefix="/api/v1/trips", tags=["data-subject-rights"])


def _load_trip(trip_id: str, agency_id: str) -> dict:
    trip = TripStore.get_trip_for_agency(trip_id, agency_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip


@router.get("/{trip_id}/data-export")
def get_trip_data_export(
    trip_id: str,
    agency: Agency = Depends(get_current_agency),
):
    """Art. 15/20: portable export of the traveler's personal data."""
    trip = _load_trip(trip_id, agency.id)
    envelope = export_trip_personal_data(trip, agency.id)
    AuditStore.log_event(
        event_type="dsr_data_exported",
        user_id=agency.id,
        details={"trip_id": trip_id},
    )
    return {"ok": True, **envelope}


class ErasureRequest(BaseModel):
    """Explicit confirmation gate: erasure never runs on an ambient call."""

    confirm: bool


def _tombstone_trip_messages(agency_id: str, phones: list, trip_id: Optional[str] = None) -> list:
    """Rewrite the agency message file, replacing bodies on records whose
    phone parties match the erased traveler or whose trip_id matches. Append-only
    is violated once, deliberately: legal erasure supersedes log immutability
    (documented in the store module). Returns the tombstoned message ids."""
    phone_set = set(phones or [])

    def rewrite(record: dict) -> dict:
        fp = _norm(str(record.get("from_party") or ""))
        tp = _norm(str(record.get("to_party") or ""))
        rec_trip = record.get("trip_id")
        matches = False
        if trip_id and rec_trip == trip_id:
            matches = True
        elif fp and fp in phone_set:
            matches = True
        elif tp and tp in phone_set:
            matches = True

        if matches:
            record["body"] = "[ERASED - GDPR ARTICLE 17]"
            if fp and fp in phone_set:
                record["from_party"] = "[ERASED - GDPR ARTICLE 17]"
            if tp and tp in phone_set:
                record["to_party"] = "[ERASED - GDPR ARTICLE 17]"
            record["gdpr_tombstone"] = True
        return record

    path = message_store._agency_path(agency_id)
    if not path.exists():
        return []
    tombstoned: list = []
    rewritten: list = []
    import json

    with message_store._WRITE_LOCK:
        with path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = rewrite(json.loads(line))
                except Exception:
                    continue
                if record.get("gdpr_tombstone"):
                    tombstoned.append(record.get("message_id"))
                rewritten.append(record)

        tmp = path.with_suffix(".tmp")
        with tmp.open("w", encoding="utf-8") as fh:
            for record in rewritten:
                fh.write(json.dumps(record, ensure_ascii=False) + "\n")
        tmp.replace(path)
    return tombstoned


@router.post("/{trip_id}/erasure")
def post_trip_erasure(
    trip_id: str,
    body: ErasureRequest,
    agency: Agency = Depends(get_current_agency),
    _perm=require_permission("trips:write"),
):
    """Art. 17: structurally erase the traveler's personal data."""
    if not body.confirm:
        raise HTTPException(
            status_code=422,
            detail="Erasure requires explicit confirm: true — it permanently scrubs personal data on this trip.",
        )
    trip = _load_trip(trip_id, agency.id)

    packet_pre = trip.get("packet") or {}
    extracted_pre = trip.get("extracted") or {}
    ext_facts_pre = extracted_pre.get("facts") if isinstance(extracted_pre, dict) else {}
    if not isinstance(ext_facts_pre, dict):
        ext_facts_pre = {}

    phone_candidates = [
        str(trip.get(k) or packet_pre.get(k) or "")
        for k in ("contact_phone", "customer_phone", "phone", "mobile", "customer_contact")
    ]
    for fk in ("contact_phone", "customer_phone", "phone", "customer_contact"):
        fv = ext_facts_pre.get(fk)
        if isinstance(fv, dict):
            phone_candidates.append(str(fv.get("value") or ""))
        elif isinstance(fv, str):
            phone_candidates.append(fv)

    phones = [_norm(c) for c in phone_candidates]
    phones = [p for p in phones if p and len(p) >= 7]
    seen_phones = set()
    dedup_phones = []
    for p in phones:
        if p not in seen_phones:
            seen_phones.add(p)
            dedup_phones.append(p)
    phones = dedup_phones

    def update_trip(trip_id_: str, agency_id_: str, fields: dict):
        return TripStore.update_trip_for_agency(trip_id_, agency_id_, fields)

    def tombstone_messages(agency_id_: str, phones_: list, trip_id_: Optional[str] = None):
        return _tombstone_trip_messages(agency_id_, phones_, trip_id=trip_id_ or trip_id)

    try:
        cert = erase_trip_personal_data(
            trip,
            agency_id=agency.id,
            update_trip=update_trip,
            tombstone_messages=tombstone_messages,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    # Cascade deletion to any draft attached to this trip
    try:
        from spine_api.draft_store import DraftStore
        for draft in DraftStore.list_by_agency(agency.id, limit=200):
            if draft.promoted_trip_id == trip_id or trip_id in (draft.linked_trip_ids or []):
                DraftStore.delete(draft.id)
    except Exception as exc:
        logger.warning("DSR erasure: draft deletion skipped: %s", exc)

    # Cascade erasure to memory store if matching customer profile exists
    try:
        from src.memory.store import MemoryStore
        mem_store = MemoryStore()
        for cust_key in ("user_id", "customer_id", "contact_email", "customer_email"):
            entity_id = trip.get(cust_key)
            if entity_id:
                mem_store.forget_entity_gdpr(agency.id, entity_id)
    except Exception as exc:
        logger.warning("DSR erasure: memory store scrub skipped: %s", exc)

    AuditStore.log_event(
        event_type="dsr_erasure_executed",
        user_id=agency.id,
        details={
            "trip_id": trip_id,
            "certificate_id": cert.certificate_id,
            "scrubbed_field_count": len(cert.scrubbed_fields),
            "tombstoned_message_count": len(cert.tombstoned_message_ids),
        },
    )
    return {"ok": True, "certificate": cert.to_dict()}
