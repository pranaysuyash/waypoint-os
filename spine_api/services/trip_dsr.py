"""
spine_api.services.trip_dsr — Traveler data-subject rights for trips (T14, GDPR Art. 15/17/20).

Extends the memory-domain erasure pattern (src/memory/gdpr_engine.py) to the
trip record and channel messages:

- **Export** (Art. 15/20): assembles the traveler's personal data from the
  trip into a portable JSON envelope with field-level provenance.
- **Erasure** (Art. 17): scrubs personal fields from the trip record and
  tombstones the traveler's channel messages, preserving the audit chain and
  operational structure (row deletion would break append-only audit hashing —
  the doctrine-compliant erasure is a structural tombstone, mirroring the
  memory engine's tombstone semantics).

Security:
- Certificates are signed per the memory engine's scheme, but **fail-closed**:
  a signing key must exist (``GDPR_SIGNING_KEY`` falling back to
  ``ENCRYPTION_KEY``); the memory prototype's hard-coded default key is not
  carried forward.
- Erasure is tenant-scoped and audit-logged; the certificate records what was
  scrubbed without recording the personal content itself.
"""

from __future__ import annotations

import hashlib
import logging
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List

logger = logging.getLogger("spine_api.trip_dsr")

# Personal fields scrubbed at the trip top level (subset of the persistence
# PII taxonomy that actually appears on trip rows).
_TRIP_PII_FIELDS = (
    "contact_name",
    "contact_email",
    "contact_phone",
    "customer_name",
    "customer_email",
    "customer_phone",
    "customer_contact",
    "traveler_name",
    "lead_traveler_name",
    "traveler_email",
    "traveler_phone",
    "mobile",
    "full_name",
    "agent_notes",
    "owner_note",
    "raw_note",
)

# Packet-level personal keys (names/contact); non-personal planning facts
# (destination, budget, dates) survive erasure — they are the agency's
# operational record, not the traveler's identity.
_PACKET_PII_FIELDS = (
    "customer_name",
    "customer_contact",
    "contact_name",
    "contact_email",
    "contact_phone",
    "customer_email",
    "customer_phone",
    "traveler_name",
    "lead_traveler_name",
    "traveler_email",
    "traveler_phone",
)

REDACTION_MARKER = "[ERASED - GDPR ARTICLE 17]"


def _signing_key() -> str:
    import os

    key = (os.getenv("GDPR_SIGNING_KEY") or os.getenv("ENCRYPTION_KEY") or "").strip()
    if not key:
        raise RuntimeError(
            "GDPR erasure requires GDPR_SIGNING_KEY (or ENCRYPTION_KEY) to be configured; "
            "refusing to issue unsigned certificates."
        )
    return key


@dataclass(slots=True)
class TripErasureCertificate:
    """Trip-scope analog of the memory engine's GDPRForgetCertificate."""

    certificate_id: str
    agency_id: str
    trip_id: str
    scrubbed_fields: List[str] = field(default_factory=list)
    tombstoned_message_ids: List[str] = field(default_factory=list)
    erased_at: str = ""
    verification_signature: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _sign(cert_id: str, agency_id: str, trip_id: str, scrubbed_count: int, message_count: int, now_iso: str, key: str) -> str:
    raw = f"{cert_id}:{agency_id}:{trip_id}:{scrubbed_count}:{message_count}:{now_iso}:{key}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def export_trip_personal_data(trip: dict, agency_id: str) -> Dict[str, Any]:
    """Art. 15/20 portable export: everything personal the platform holds for
    this trip, plus structural context. Read-only; never mutates."""
    packet = trip.get("packet") or {}
    facts = (packet.get("extracted_facts") or packet.get("facts") or {})
    extracted = trip.get("extracted") or {}
    ext_facts = extracted.get("facts") if isinstance(extracted, dict) else {}

    personal: Dict[str, Any] = {}
    for key in _TRIP_PII_FIELDS:
        if trip.get(key) not in (None, ""):
            personal[key] = trip[key]
    for key in _PACKET_PII_FIELDS:
        if packet.get(key) not in (None, ""):
            personal[f"packet.{key}"] = packet[key]
    if isinstance(ext_facts, dict):
        for fk, fval in ext_facts.items():
            if fk in _PACKET_PII_FIELDS or any(sub in fk for sub in ("contact", "name", "email", "phone")):
                if isinstance(fval, dict) and fval.get("value") not in (None, ""):
                    personal[f"extracted.facts.{fk}"] = fval["value"]
                elif isinstance(fval, str) and fval:
                    personal[f"extracted.facts.{fk}"] = fval

    if trip.get("traveler_answers"):
        personal["traveler_answers"] = trip["traveler_answers"]

    if trip.get("passenger_claim"):
        claim = trip["passenger_claim"]
        claim_pax = {}
        for k in ("passenger_name", "passenger_email", "passenger_phone", "claimant_name", "passengers"):
            if claim.get(k):
                claim_pax[k] = claim[k]
        if claim_pax:
            personal["passenger_claim"] = claim_pax

    # Channel messages tied to this trip's phones or trip id.
    messages: List[dict] = []
    try:
        from spine_api.services import message_store

        phone_candidates = [
            str(trip.get(k) or packet.get(k) or "")
            for k in ("contact_phone", "customer_phone", "phone", "mobile", "customer_contact")
        ]
        if isinstance(ext_facts, dict):
            for fk in ("contact_phone", "customer_phone", "phone", "customer_contact"):
                fv = ext_facts.get(fk)
                if isinstance(fv, dict):
                    phone_candidates.append(str(fv.get("value") or ""))
                elif isinstance(fv, str):
                    phone_candidates.append(fv)

        phones = [message_store.normalize_phone(p) for p in phone_candidates]
        phones = [p for p in phones if p and len(p) >= 7]
        for m in message_store.list_for_agency(agency_id, trip_id=trip.get("id"), limit=500):
            messages.append(
                {
                    "message_id": m.get("message_id"),
                    "channel": m.get("channel"),
                    "direction": m.get("direction"),
                    "from_party": m.get("from_party"),
                    "body": m.get("body"),
                    "received_at": m.get("received_at"),
                }
            )
        if phones:
            for m in message_store.list_for_agency(agency_id, limit=500):
                fp = message_store.normalize_phone(str(m.get("from_party") or ""))
                tp = message_store.normalize_phone(str(m.get("to_party") or ""))
                if (fp in phones or tp in phones) and m.get("message_id") not in {x["message_id"] for x in messages}:
                    messages.append(
                        {
                            "message_id": m.get("message_id"),
                            "channel": m.get("channel"),
                            "direction": m.get("direction"),
                            "from_party": m.get("from_party"),
                            "body": m.get("body"),
                            "received_at": m.get("received_at"),
                        }
                    )
    except Exception as exc:
        logger.warning("DSR export: message section skipped: %s", exc)

    return {
        "dsr": "gdpr_article_15_20_portable_export",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "agency_id": agency_id,
        "trip_id": trip.get("id"),
        "created_at": trip.get("created_at"),
        "personal_data": personal,
        "planning_context": {
            "destination": packet.get("destination") or trip.get("destination"),
            "party_size": packet.get("party_size"),
            "start_date": packet.get("start_date"),
            "end_date": packet.get("end_date"),
        },
        "channel_messages": messages,
        "facts_summary": sorted(facts.keys()) if isinstance(facts, dict) else [],
    }


def erase_trip_personal_data(
    trip: dict,
    *,
    agency_id: str,
    update_trip: Any,
    tombstone_messages: Any,
) -> TripErasureCertificate:
    """Art. 17 structural erasure.

    ``update_trip(trip_id, agency_id, fields)`` and
    ``tombstone_messages(agency_id, phones)`` are injected so the engine stays
    storage-agnostic and testable. Returns the signed certificate.
    """
    key = _signing_key()
    trip_id = trip.get("id")
    now_iso = datetime.now(timezone.utc).isoformat()

    # Capture phone matchers BEFORE scrubbing — erasure redacts the very
    # fields the message tombstoning matches on.
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

    scrubbed_fields: List[str] = []
    trip_updates: Dict[str, Any] = {}

    # 1. Top-level PII fields
    for key_field in _TRIP_PII_FIELDS:
        if trip.get(key_field) not in (None, ""):
            trip_updates[key_field] = REDACTION_MARKER
            scrubbed_fields.append(key_field)

    # 2. Packet-level personal keys & facts
    packet = trip.get("packet")
    if isinstance(packet, dict):
        packet_copy = dict(packet)
        has_packet_scrub = False
        for k in _PACKET_PII_FIELDS:
            if packet_copy.get(k) not in (None, ""):
                packet_copy[k] = REDACTION_MARKER
                scrubbed_fields.append(f"packet.{k}")
                has_packet_scrub = True
        p_facts = packet_copy.get("extracted_facts") or packet_copy.get("facts")
        if isinstance(p_facts, dict):
            p_facts_copy = dict(p_facts)
            for fk in list(p_facts_copy.keys()):
                if fk in _PACKET_PII_FIELDS or any(sub in fk for sub in ("contact", "name", "email", "phone")):
                    if isinstance(p_facts_copy[fk], dict):
                        f_item = dict(p_facts_copy[fk])
                        f_item["value"] = REDACTION_MARKER
                        f_item["evidence_refs"] = []
                        p_facts_copy[fk] = f_item
                    else:
                        p_facts_copy[fk] = REDACTION_MARKER
                    scrubbed_fields.append(f"packet.facts.{fk}")
                    has_packet_scrub = True
            if "extracted_facts" in packet_copy:
                packet_copy["extracted_facts"] = p_facts_copy
            if "facts" in packet_copy:
                packet_copy["facts"] = p_facts_copy
        if has_packet_scrub:
            trip_updates["packet"] = packet_copy
            scrubbed_fields.append("packet")

    # 3. Extracted facts
    extracted = trip.get("extracted")
    if isinstance(extracted, dict):
        ext_copy = dict(extracted)
        has_ext_scrub = False
        for k in _PACKET_PII_FIELDS:
            if ext_copy.get(k) not in (None, ""):
                ext_copy[k] = REDACTION_MARKER
                scrubbed_fields.append(f"extracted.{k}")
                has_ext_scrub = True
        e_facts = ext_copy.get("facts") or ext_copy.get("extracted_facts")
        if isinstance(e_facts, dict):
            e_facts_copy = dict(e_facts)
            for fk in list(e_facts_copy.keys()):
                if fk in _PACKET_PII_FIELDS or any(sub in fk for sub in ("contact", "name", "email", "phone")):
                    if isinstance(e_facts_copy[fk], dict):
                        f_item = dict(e_facts_copy[fk])
                        f_item["value"] = REDACTION_MARKER
                        f_item["evidence_refs"] = []
                        e_facts_copy[fk] = f_item
                    else:
                        e_facts_copy[fk] = REDACTION_MARKER
                    scrubbed_fields.append(f"extracted.facts.{fk}")
                    has_ext_scrub = True
            if "facts" in ext_copy:
                ext_copy["facts"] = e_facts_copy
            if "extracted_facts" in ext_copy:
                ext_copy["extracted_facts"] = e_facts_copy
        if has_ext_scrub:
            trip_updates["extracted"] = ext_copy
            scrubbed_fields.append("extracted")

    # 4. Raw input
    if trip.get("raw_input") not in (None, ""):
        trip_updates["raw_input"] = {"erased_at": now_iso, "status": "tombstoned"}
        scrubbed_fields.append("raw_input")

    # 5. Bundles and booking data
    for b_field in ("traveler_bundle", "internal_bundle", "booking_data", "pending_booking_data"):
        if trip.get(b_field) not in (None, ""):
            trip_updates[b_field] = {"erased_at": now_iso, "status": "tombstoned"}
            scrubbed_fields.append(b_field)

    # 6. Traveler asks & answers
    if trip.get("traveler_answers") and isinstance(trip.get("traveler_answers"), list):
        scrubbed_answers = []
        for ans in trip["traveler_answers"]:
            ans_copy = dict(ans) if isinstance(ans, dict) else {}
            if "answer" in ans_copy:
                ans_copy["answer"] = REDACTION_MARKER
            if "respondent_name" in ans_copy:
                ans_copy["respondent_name"] = REDACTION_MARKER
            scrubbed_answers.append(ans_copy)
        trip_updates["traveler_answers"] = scrubbed_answers
        scrubbed_fields.append("traveler_answers")

    # 7. Passenger claim (preserve statutory framework/tier/amount while redacting pax details)
    if trip.get("passenger_claim") and isinstance(trip.get("passenger_claim"), dict):
        claim_copy = dict(trip["passenger_claim"])
        for pii_k in ("passenger_name", "passenger_email", "passenger_phone", "claimant_name", "claimant_email", "claimant_phone"):
            if claim_copy.get(pii_k) not in (None, ""):
                claim_copy[pii_k] = REDACTION_MARKER
        if isinstance(claim_copy.get("passengers"), list):
            scrubbed_pax = []
            for pax in claim_copy["passengers"]:
                pax_copy = dict(pax) if isinstance(pax, dict) else {}
                for pk in ("name", "first_name", "last_name", "email", "phone"):
                    if pax_copy.get(pk) not in (None, ""):
                        pax_copy[pk] = REDACTION_MARKER
                scrubbed_pax.append(pax_copy)
            claim_copy["passengers"] = scrubbed_pax
        trip_updates["passenger_claim"] = claim_copy
        scrubbed_fields.append("passenger_claim")

    # Pass the clean top-level scrubbed dict to update_trip
    if trip_updates:
        updated = update_trip(trip_id, agency_id, trip_updates)
        if updated is None:
            raise ValueError(f"Trip {trip_id} could not be updated for erasure")

    # Message tombstoning: pass phones and trip_id
    if phones or trip_id:
        try:
            tombstoned_ids = tombstone_messages(agency_id, phones, trip_id=trip_id)
        except TypeError:
            tombstoned_ids = tombstone_messages(agency_id, phones) if phones else []
    else:
        tombstoned_ids = []

    cert_id = f"cert_{uuid.uuid4().hex[:12]}"
    cert = TripErasureCertificate(
        certificate_id=cert_id,
        agency_id=agency_id,
        trip_id=trip_id,
        scrubbed_fields=sorted(set(scrubbed_fields)),
        tombstoned_message_ids=tombstoned_ids,
        erased_at=now_iso,
        verification_signature=_sign(
            cert_id, agency_id, trip_id, len(scrubbed_fields), len(tombstoned_ids), now_iso, key
        ),
    )
    return cert


def _norm(phone: str) -> str:
    return "".join(ch for ch in (phone or "") if ch.isdigit())
