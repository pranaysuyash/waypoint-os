"""
spine_api/routers/customer_memory.py — 5-Tier Agent Memory & CRM Graph Engine.

Implements enterprise REST endpoints for PER-0717 Agent Memory Architect:
- 5-Tier Memory Ingestion (Working, Episodic, Semantic, Procedural, Preference)
- Write Eligibility Gate and Source Hierarchy Scoring
- Cryptographic Provenance Lineage Tracking
- Temporal Half-Life Decay and Activation Scoring
- GDPR Article 17 Right-to-Erasure with Cryptographic Certificates
- Trip On-File Memory Display (E-D slot 2: display-only, never packet writes)
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select

from spine_api.core.auth import get_current_agency_id
from spine_api.core.rls import rls_session
from spine_api.models.tenant import CustomerMemoryProfile
from spine_api.persistence import AuditStore, TripStore
from src.memory.feedback_bridge import traveler_entity_for
from src.memory.models import (
    MemorySourceType,
    MemoryTier,
)
from src.memory.slot_candidates import memory_on_file_facts
from src.memory.store import get_memory_store

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/customers", tags=["Customer Relationship Memory"])

# Shared process-wide memory store — one instance per process is a data-integrity
# requirement (whole-file rewrite from cache; separate instances lose writes).
_MEMORY_STORE = get_memory_store()

# FND-0060 residual closed: the legacy process-local CUSTOMER_MEMORY_STORE dict
# is superseded by the durable, agency-scoped SQL table
# ``customer_memory_profiles`` (RLS-isolated; survives restarts; safe under
# multiple workers). S-08 tenant partitioning is now enforced by the database
# (agency_id FK + row-level security) instead of dict-key discipline. Passport
# fields remain deliberately non-durable (30-day PASSPORT_MRZ retention SLA).
# Supersession analysis: Docs/exploration/
# CUSTOMER_MEMORY_DURABLE_STORE_EXPLORATION_2026-09-15.md.


async def _find_customer_profile_db(
    db,
    agency_id: str,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    name: Optional[str] = None,
) -> Optional[CustomerMemoryProfile]:
    """Find a customer profile scoped to ``agency_id`` (S-08 tenant partition).

    ``agency_id`` is intentionally a required positional argument so no caller
    can accidentally scan cross-tenant rows without an agency context. Match
    priority mirrors the original dict scan: normalized email, then phone,
    then lowercased name. RLS additionally confines every query to the
    caller's agency.
    """
    norm_e = _normalize_email(email)
    norm_p = _normalize_phone(phone)
    norm_n = name.strip().lower() if name and name.strip() else None

    base = select(CustomerMemoryProfile).where(
        CustomerMemoryProfile.agency_id == agency_id
    )
    if norm_e:
        row = (
            await db.scalars(
                base.where(CustomerMemoryProfile.normalized_email == norm_e)
            )
        ).first()
        if row:
            return row
    if norm_p:
        row = (
            await db.scalars(
                base.where(CustomerMemoryProfile.normalized_phone == norm_p)
            )
        ).first()
        if row:
            return row
    if norm_n:
        rows = (await db.scalars(base)).all()
        for row in rows:
            if (row.name or "").strip().lower() == norm_n:
                return row
    return None


# ---------------------------------------------------------------------------
# Schema Models
# ---------------------------------------------------------------------------

class CustomerPreferenceProfile(BaseModel):
    customer_id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    dietary_requirements: Optional[str] = None
    room_preference: Optional[str] = None
    seating_preference: Optional[str] = None
    passport_country: Optional[str] = None
    passport_expiry: Optional[str] = None
    source_trip_ids: List[str] = Field(default_factory=list)
    last_confirmed_at: str


class RememberPreferenceRequest(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    dietary_requirements: Optional[str] = None
    room_preference: Optional[str] = None
    seating_preference: Optional[str] = None
    passport_country: Optional[str] = None
    passport_expiry: Optional[str] = None
    source_trip_id: Optional[str] = None


class HydrateTripRequest(BaseModel):
    trip_id: str
    email: Optional[str] = None
    phone: Optional[str] = None


class HydrateTripResponse(BaseModel):
    ok: bool = True
    trip_id: str
    memory_found: bool
    customer_name: Optional[str] = None
    customer_id: Optional[str] = None
    hydrated_fields: List[str] = Field(default_factory=list)
    preferences: Dict[str, Any] = Field(default_factory=dict)
    # E-D slot 2 (display-only): per-fact provenance chips — never trip data.
    # source: "memory" (durable store) | "memory:profile" (registry fallback).
    facts: List[Dict[str, Any]] = Field(default_factory=list)


class IngestMemoryRequest(BaseModel):
    entity_id: str
    raw_text: str
    source_type: str = "traveler_direct"
    category_hint: Optional[str] = None
    explicit_confidence: Optional[float] = None
    is_safety_critical: bool = False
    payload: Optional[Dict[str, Any]] = None
    source_ref_id: Optional[str] = None


class IngestMemoryResponse(BaseModel):
    ok: bool
    message: str
    memory_id: Optional[str] = None
    tier: Optional[str] = None
    category: Optional[str] = None
    confidence_score: Optional[float] = None
    integrity_hash: Optional[str] = None


class QueryMemoryResponse(BaseModel):
    query: str
    result_count: int
    results: List[Dict[str, Any]]


class GDPRForgetRequest(BaseModel):
    customer_id: str


class GDPRForgetResponse(BaseModel):
    ok: bool = True
    certificate: Dict[str, Any]


# ---------------------------------------------------------------------------
# Normalization Helpers
# ---------------------------------------------------------------------------

def _normalize_email(email: Optional[str]) -> Optional[str]:
    return email.strip().lower() if email and email.strip() else None


def _normalize_phone(phone: Optional[str]) -> Optional[str]:
    if not phone:
        return None
    digits = "".join(c for c in phone if c.isdigit())
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    return digits if digits else None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

_PROFILES_TABLE_READY = False


async def _ensure_profiles_table() -> None:
    """Additive-only safety net for environments that have not run the
    alembic migration yet (mirrors proposal_token_store/SqlIdempotencyBackend);
    the alembic migration (add_customer_memory_profiles) remains the canonical
    schema path and is what adds the RLS policies. checkfirst keeps this
    idempotent — never drops or rewrites existing data."""
    global _PROFILES_TABLE_READY
    if _PROFILES_TABLE_READY:
        return
    from spine_api.core.database import Base, async_session_maker

    async with async_session_maker() as session:
        conn = await session.connection()
        await conn.run_sync(
            lambda sync_conn: Base.metadata.create_all(
                sync_conn, tables=[CustomerMemoryProfile.__table__], checkfirst=True
            )
        )
        # Postgres DDL is transactional: without an explicit commit the
        # CREATE TABLE above is rolled back when the session closes.
        await session.commit()
    _PROFILES_TABLE_READY = True


@router.get("/memory", response_model=Optional[CustomerPreferenceProfile])
async def get_customer_memory(
    email: Optional[str] = None,
    phone: Optional[str] = None,
    name: Optional[str] = None,
    agency_id: str = Depends(get_current_agency_id),
):
    """Lookup repeat customer memory by email, phone number, or name."""
    if not any([email, phone, name]):
        raise HTTPException(status_code=400, detail="Must provide email, phone, or name for memory lookup")

    await _ensure_profiles_table()
    async with rls_session(agency_id) as db:
        profile_row = await _find_customer_profile_db(
            db, agency_id, email=email, phone=phone, name=name
        )
    if not profile_row:
        return None

    return CustomerPreferenceProfile(
        customer_id=profile_row.customer_id,
        name=profile_row.name,
        email=profile_row.email,
        phone=profile_row.phone,
        dietary_requirements=profile_row.dietary_requirements,
        room_preference=profile_row.room_preference,
        seating_preference=profile_row.seating_preference,
        # passport_country / passport_expiry are intentionally absent from
        # the durable row (30-day PASSPORT_MRZ retention SLA).
        source_trip_ids=profile_row.source_trip_ids or [],
        last_confirmed_at=(
            profile_row.last_confirmed_at.isoformat()
            if profile_row.last_confirmed_at
            else datetime.now(timezone.utc).isoformat()
        ),
    )


@router.post("/remember", response_model=CustomerPreferenceProfile)
async def remember_customer_preference(
    req: RememberPreferenceRequest,
    agency_id: str = Depends(get_current_agency_id),
):
    """Index or update customer preference profile with verified provenance."""
    norm_e = _normalize_email(req.email)
    norm_p = _normalize_phone(req.phone)

    if not norm_e and not norm_p and not req.name:
        raise HTTPException(status_code=400, detail="Must provide email, phone, or name to index customer memory")

    await _ensure_profiles_table()
    async with rls_session(agency_id) as db:
        profile_row = await _find_customer_profile_db(
            db, agency_id, email=req.email, phone=req.phone, name=req.name
        )
        now = datetime.now(timezone.utc)

        if profile_row:
            cust_id = profile_row.customer_id
        else:
            cust_id = f"cust_{norm_e or norm_p or req.name.lower().replace(' ', '_')}"
            profile_row = CustomerMemoryProfile(
                id=str(uuid.uuid4()),
                agency_id=agency_id,
                customer_id=cust_id,
                name=req.name,
            )

        # Update profile fields. Passport fields are deliberately NOT
        # persisted (30-day PASSPORT_MRZ retention SLA) — they are echoed on
        # this response only, request-scoped.
        if req.email:
            profile_row.email = req.email
            profile_row.normalized_email = norm_e
        if req.phone:
            profile_row.phone = req.phone
            profile_row.normalized_phone = norm_p
        if req.dietary_requirements:
            profile_row.dietary_requirements = req.dietary_requirements
        if req.room_preference:
            profile_row.room_preference = req.room_preference
        if req.seating_preference:
            profile_row.seating_preference = req.seating_preference
        # Passport fields: echoed on this response only, never persisted
        # (30-day PASSPORT_MRZ retention SLA).
        passport_echo_country = req.passport_country
        passport_echo_expiry = req.passport_expiry
        if req.source_trip_id:
            trips = profile_row.source_trip_ids or []
            if req.source_trip_id not in trips:
                trips.append(req.source_trip_id)
                profile_row.source_trip_ids = trips

        profile_row.last_confirmed_at = now
        db.add(profile_row)
        await db.commit()
        await db.refresh(profile_row)

    # Also ingest structured facts into the 5-tier durable MemoryStore
    if req.dietary_requirements:
        _MEMORY_STORE.ingest_memory(
            agency_id=agency_id,
            entity_id=cust_id,
            raw_text=f"Dietary requirement: {req.dietary_requirements}",
            source_type=MemorySourceType.TRAVELER_DIRECT,
            category_hint="dietary",
            is_safety_critical=True,
            source_ref_id=req.source_trip_id,
        )

    if req.seating_preference:
        _MEMORY_STORE.ingest_memory(
            agency_id=agency_id,
            entity_id=cust_id,
            raw_text=f"Seating preference: {req.seating_preference}",
            source_type=MemorySourceType.TRAVELER_DIRECT,
            category_hint="seating",
            source_ref_id=req.source_trip_id,
        )

    if req.room_preference:
        _MEMORY_STORE.ingest_memory(
            agency_id=agency_id,
            entity_id=cust_id,
            raw_text=f"Room preference: {req.room_preference}",
            source_type=MemorySourceType.TRAVELER_DIRECT,
            category_hint="room_preference",
            source_ref_id=req.source_trip_id,
        )

    # Deliberately NOT durably ingested: passport_country / passport_expiry.
    # Passport data carries a 30-day post-trip retention SLA
    # (RetentionCategory.PASSPORT_MRZ); persisting it into long-half-life
    # memory would create a retention violation by design. It stays in the
    # process-local registry view only.

    AuditStore.log_event(
        event_type="customer_memory_updated",
        user_id=agency_id,
        details={
            "customer_id": cust_id,
            "name": req.name,
            "updated_fields": [k for k in ["dietary_requirements", "room_preference", "seating_preference"] if getattr(req, k, None)],
            "source_trip_id": req.source_trip_id,
        },
    )

    return CustomerPreferenceProfile(
        customer_id=profile_row.customer_id,
        name=profile_row.name,
        email=profile_row.email,
        phone=profile_row.phone,
        dietary_requirements=profile_row.dietary_requirements,
        room_preference=profile_row.room_preference,
        seating_preference=profile_row.seating_preference,
        passport_country=passport_echo_country,
        passport_expiry=passport_echo_expiry,
        source_trip_ids=profile_row.source_trip_ids or [],
        last_confirmed_at=profile_row.last_confirmed_at.isoformat(),
    )


@router.post("/hydrate-trip/{trip_id}", response_model=HydrateTripResponse)
async def hydrate_trip_with_customer_memory(
    trip_id: str,
    req: HydrateTripRequest | None = None,
    agency_id: str = Depends(get_current_agency_id),
):
    """Return the traveler's on-file memory facts for display (E-D slot 2).

    DISPLAY-ONLY by ratified contract (ADR-008 §7 row 4 / E-D §3 slot 2):
    facts come back labeled with provenance for "On file from <date>" chips.
    They are never written into the trip packet, never rendered as confirmed
    trip data, and never satisfy a gate — the former packet-mutating
    behavior was the memory→packet influence path E-D forbids.

    Durable store is the canonical source (survives restarts; one freshness
    policy shared with the slot-1 read via ``memory_on_file_facts``); the
    process-local profile registry is a fallback for entries not yet
    durably ingested, labeled ``memory:profile``.
    """
    req = req or HydrateTripRequest(trip_id=trip_id)

    trip = TripStore.get_trip_for_agency(trip_id, agency_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    # Resolve the customer identity from the request body if provided, else from
    # the trip's customer fields. This lets a body-less hydrate still match the
    # remembered profile for the trip's customer.
    packet = trip.get("packet", {}) or {}
    trip_email = (
        req.email
        or packet.get("customer_email")
        or trip.get("customer_email")
        or trip.get("email")
        or trip.get("client_email")
    )
    trip_phone = (
        req.phone
        or packet.get("customer_phone")
        or trip.get("customer_phone")
        or trip.get("phone")
        or trip.get("client_phone")
    )
    trip_name = packet.get("customer_name") or trip.get("customer_name") or trip.get("client_name")

    # The canonical contact field on an inbound trip is `customer_contact`
    # (free-form string — email or phone). Probe it after the structured
    # fields; "@" marks an email, otherwise treat it as a phone reference.
    trip_contact = str(trip.get("customer_contact") or packet.get("customer_contact") or "").strip()
    if trip_contact and not trip_email and "@" in trip_contact:
        trip_email = trip_contact
    if trip_contact and not trip_phone and "@" not in trip_contact:
        trip_phone = trip_contact

    # _find_customer_profile_db matches by email, then phone, then normalized name,
    # so passing all three makes a body-less hydrate robust to whichever field
    # the trip carries. Scoped to the caller's agency (S-08).
    await _ensure_profiles_table()
    async with rls_session(agency_id) as db:
        profile_row = await _find_customer_profile_db(
            db, agency_id, email=trip_email, phone=trip_phone, name=trip_name
        )
    profile = None
    if profile_row is not None:
        profile = {
            "customer_id": profile_row.customer_id,
            "name": profile_row.name,
            "dietary_requirements": profile_row.dietary_requirements,
            "seating_preference": profile_row.seating_preference,
            "room_preference": profile_row.room_preference,
            "last_confirmed_at": (
                profile_row.last_confirmed_at.isoformat()
                if profile_row.last_confirmed_at
                else ""
            ),
        }

    # Durable-store read (canonical). Entity id: the registered customer id
    # when a profile exists, else the canonical cust_ convention derived
    # from the trip's contact identity (same convention as the feedback
    # bridge, so writes and reads resolve to the same entity).
    entity_id = (profile or {}).get("customer_id") or traveler_entity_for(
        trip_email, trip_phone, trip_id
    )
    durable_facts = memory_on_file_facts(_MEMORY_STORE, agency_id, entity_id)

    # Registry fallback chips for structured fields not covered durably.
    # Coverage is by field name OR content (the gate assigns its own
    # categories, so a durably-ingested room preference may carry a generic
    # category while its summary still holds the structured fact).
    durable_fields = {f["field_name"] for f in durable_facts if f["field_name"]}
    durable_values_lower = [f["value"].lower() for f in durable_facts]
    observed_at = (profile or {}).get("last_confirmed_at") or ""
    profile_fields = [
        ("dietary_requirements", (profile or {}).get("dietary_requirements")),
        ("seating_preference", (profile or {}).get("seating_preference")),
        ("room_preference", (profile or {}).get("room_preference")),
    ]
    registry_facts = [
        {
            "field_name": name,
            "value": value,
            "observed_at": observed_at,
            "source": "memory:profile",
        }
        for name, value in profile_fields
        if value
        and name not in durable_fields
        and value.lower() not in " ".join(durable_values_lower)
    ]

    facts = durable_facts + registry_facts
    if not facts:
        return HydrateTripResponse(
            trip_id=trip_id,
            memory_found=False,
            hydrated_fields=[],
            preferences={},
        )

    # Structured preferences stay registry-sourced when present (legacy
    # CustomerPreferenceProfile contract); facts is the ratified payload.
    prefs = {name: value for name, value in profile_fields if value}
    hydrated = [f["field_name"] or "preference" for f in facts]

    AuditStore.log_event(
        event_type="memory_on_file_displayed",
        user_id=agency_id,
        details={
            "trip_id": trip_id,
            "customer_id": entity_id,
            "durable_facts": len(durable_facts),
            "registry_facts": len(registry_facts),
        },
    )

    return HydrateTripResponse(
        trip_id=trip_id,
        memory_found=True,
        customer_name=(profile or {}).get("name"),
        customer_id=entity_id,
        hydrated_fields=hydrated,
        preferences=prefs,
        facts=facts,
    )


# ---------------------------------------------------------------------------
# Advanced 5-Tier Engine Endpoints
# ---------------------------------------------------------------------------

@router.post("/memory/ingest", response_model=IngestMemoryResponse)
async def ingest_memory_item(
    req: IngestMemoryRequest,
    agency_id: str = Depends(get_current_agency_id),
):
    """Ingests a memory item through the Write Eligibility Gate and Provenance Engine."""
    try:
        source_enum = MemorySourceType(req.source_type)
    except Exception:
        source_enum = MemorySourceType.TRAVELER_DIRECT

    item, msg = _MEMORY_STORE.ingest_memory(
        agency_id=agency_id,
        entity_id=req.entity_id,
        raw_text=req.raw_text,
        source_type=source_enum,
        payload=req.payload,
        source_ref_id=req.source_ref_id,
        actor_id=agency_id,
        category_hint=req.category_hint,
        explicit_confidence=req.explicit_confidence,
        is_safety_critical=req.is_safety_critical,
    )

    if not item:
        return IngestMemoryResponse(
            ok=False,
            message=msg,
        )

    return IngestMemoryResponse(
        ok=True,
        message=msg,
        memory_id=item.memory_id,
        tier=item.tier.value,
        category=item.category,
        confidence_score=item.provenance.confidence_score,
        integrity_hash=item.provenance.integrity_hash,
    )


@router.get("/memory/query", response_model=QueryMemoryResponse)
async def query_memory_items(
    query: str = Query(..., min_length=1),
    entity_id: Optional[str] = Query(None),
    tier: Optional[str] = Query(None),
    top_k: int = Query(10, ge=1, le=50),
    agency_id: str = Depends(get_current_agency_id),
):
    """Executes a hybrid recency-weighted search over agent memory facts."""
    tier_enum = None
    if tier:
        try:
            tier_enum = MemoryTier(tier)
        except Exception:
            pass

    scored_items = _MEMORY_STORE.query_memories(
        agency_id=agency_id,
        query=query,
        entity_id=entity_id,
        tier=tier_enum,
        top_k=top_k,
    )

    results = []
    for item, score in scored_items:
        d = item.to_dict()
        d["relevance_score"] = score
        results.append(d)

    return QueryMemoryResponse(
        query=query,
        result_count=len(results),
        results=results,
    )


@router.get("/memory/entity/{entity_id}")
async def list_entity_memory_items(
    entity_id: str,
    include_superseded: bool = Query(False),
    agency_id: str = Depends(get_current_agency_id),
):
    """Lists all active 5-tier memory records for an entity."""
    items = _MEMORY_STORE.list_entity_memories(
        agency_id=agency_id,
        entity_id=entity_id,
        include_superseded=include_superseded,
    )
    return {
        "entity_id": entity_id,
        "count": len(items),
        "memories": [i.to_dict() for i in items],
    }


@router.post("/memory/forget", response_model=GDPRForgetResponse)
async def forget_customer_gdpr(
    req: GDPRForgetRequest,
    agency_id: str = Depends(get_current_agency_id),
):
    """Executes GDPR Article 17 Right-to-Erasure and returns a cryptographic certificate."""
    cert = _MEMORY_STORE.forget_entity_gdpr(
        agency_id=agency_id,
        entity_id=req.customer_id,
    )

    # Also remove durable profile rows — scoped to the caller's agency (S-08),
    # so agency B cannot erase agency A's profile by guessing the customer id.
    #
    # X-14 propagation fix (ADR-008 council, Addendum 9): a customer may exist
    # under MORE than one customer_id with the same contact identity (profile
    # re-created under a fresh id). Forgetting only the exact id left
    # duplicates hydratable by email/phone/name — a GDPR leak. Remove every
    # profile in this agency whose contact identity matches the forgotten
    # entity's stored contact fields.
    propagated_removals: list[list[str]] = []
    await _ensure_profiles_table()
    async with rls_session(agency_id) as db:
        rows = (
            await db.execute(
                select(CustomerMemoryProfile).where(
                    CustomerMemoryProfile.agency_id == agency_id
                )
            )
        ).scalars().all()
        forgotten = next(
            (r for r in rows if r.customer_id == req.customer_id), None
        )
        match_fields = {
            getattr(forgotten, k)
            for k in ("normalized_email", "normalized_phone")
            if forgotten is not None and getattr(forgotten, k)
        }
        _forgotten_name = (
            (forgotten.name or "").strip().lower() if forgotten else None
        )
        doomed: list[CustomerMemoryProfile] = []
        for row in rows:
            contact_match = (
                getattr(row, "normalized_email", None) in match_fields
                or getattr(row, "normalized_phone", None) in match_fields
            )
            name_match = (
                _forgotten_name
                and (row.name or "").strip().lower() == _forgotten_name
            )
            if row.customer_id == req.customer_id or contact_match or name_match:
                doomed.append(row)
        for row in doomed:
            propagated_removals.append([agency_id, row.customer_id])
            await db.delete(row)
        if doomed:
            await db.commit()
    if propagated_removals:
        AuditStore.log_event(
            event_type="gdpr_memory_erased",
            user_id=agency_id,
            details={
                "customer_id": req.customer_id,
                "certificate_id": cert.certificate_id,
                "propagated_removals": propagated_removals,
            },
        )

    AuditStore.log_event(
        event_type="gdpr_memory_erased",
        user_id=agency_id,
        details={
            "customer_id": req.customer_id,
            "certificate_id": cert.certificate_id,
            "tombstones_created": cert.tombstone_count,
        },
    )

    return GDPRForgetResponse(
        ok=True,
        certificate=cert.to_dict(),
    )
