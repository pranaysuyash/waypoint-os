"""
spine_api/routers/customer_memory.py — Cross-Trip Relationship Memory & Repeat Traveler CRM Graph Engine.

Indexes customer preferences (dietary, room, seating, passport metadata) by normalized email/phone,
auto-hydrates new trip packets with confirmed historical client memory, and tracks preference provenance.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Header, HTTPException

from spine_api.persistence import TEST_AGENCY_ID, AuditStore, TripStore

router = APIRouter(prefix="/api/v1/customers", tags=["Customer Relationship Memory"])

# In-memory customer memory store keyed by customer_id
CUSTOMER_MEMORY_STORE: Dict[str, Dict[str, Any]] = {}


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
    hydrated_fields: List[str] = Field(default_factory=list)
    preferences: Dict[str, Any] = Field(default_factory=dict)


def _normalize_email(email: Optional[str]) -> Optional[str]:
    return email.strip().lower() if email and email.strip() else None


def _normalize_phone(phone: Optional[str]) -> Optional[str]:
    if not phone:
        return None
    digits = "".join(c for c in phone if c.isdigit())
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    return digits if digits else None


def _find_customer_profile(
    email: Optional[str] = None,
    phone: Optional[str] = None,
    name: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    norm_e = _normalize_email(email)
    norm_p = _normalize_phone(phone)
    norm_n = name.strip().lower() if name and name.strip() else None

    for profile in CUSTOMER_MEMORY_STORE.values():
        if norm_e and profile.get("normalized_email") == norm_e:
            return profile
        if norm_p and profile.get("normalized_phone") == norm_p:
            return profile
        if norm_n and profile.get("name", "").strip().lower() == norm_n:
            return profile

    return None


@router.get("/memory", response_model=Optional[CustomerPreferenceProfile])
def get_customer_memory(
    email: Optional[str] = None,
    phone: Optional[str] = None,
    name: Optional[str] = None,
    x_agency_id: Optional[str] = Header(None, alias="X-Agency-ID"),
):
    """Lookup repeat customer memory by email, phone number, or name."""
    if not email and not phone and not name:
        raise HTTPException(status_code=400, detail="Must provide email, phone, or name for memory lookup")

    profile = _find_customer_profile(email, phone, name)
    if not profile:
        return None

    return CustomerPreferenceProfile(
        customer_id=profile["customer_id"],
        name=profile["name"],
        email=profile.get("email"),
        phone=profile.get("phone"),
        dietary_requirements=profile.get("dietary_requirements"),
        room_preference=profile.get("room_preference"),
        seating_preference=profile.get("seating_preference"),
        passport_country=profile.get("passport_country"),
        passport_expiry=profile.get("passport_expiry"),
        source_trip_ids=profile.get("source_trip_ids", []),
        last_confirmed_at=profile.get("last_confirmed_at", datetime.now(timezone.utc).isoformat()),
    )


@router.post("/remember", response_model=CustomerPreferenceProfile)
def remember_customer_preferences(
    body: RememberPreferenceRequest,
    x_agency_id: Optional[str] = Header(None, alias="X-Agency-ID"),
):
    """Save or update customer relationship preferences across trips."""
    agency_id = x_agency_id or TEST_AGENCY_ID
    norm_e = _normalize_email(body.email)
    norm_p = _normalize_phone(body.phone)

    if not norm_e and not norm_p and not body.name:
        raise HTTPException(status_code=400, detail="Must provide email, phone, or name to index customer memory")

    profile = _find_customer_profile(body.email, body.phone, body.name)
    now_iso = datetime.now(timezone.utc).isoformat()

    if not profile:
        cust_id = f"cust_{datetime.now().strftime('%Y%m%d%H%M%S')}_{hash((norm_e or norm_p or body.name or '')[:8]) & 0xffff}"
        profile = {
            "customer_id": cust_id,
            "name": body.name,
            "email": body.email,
            "phone": body.phone,
            "normalized_email": norm_e,
            "normalized_phone": norm_p,
            "source_trip_ids": [],
        }
        CUSTOMER_MEMORY_STORE[cust_id] = profile

    profile["name"] = body.name or profile["name"]
    if body.email:
        profile["email"] = body.email
        profile["normalized_email"] = norm_e
    if body.phone:
        profile["phone"] = body.phone
        profile["normalized_phone"] = norm_p

    if body.dietary_requirements:
        profile["dietary_requirements"] = body.dietary_requirements
    if body.room_preference:
        profile["room_preference"] = body.room_preference
    if body.seating_preference:
        profile["seating_preference"] = body.seating_preference
    if body.passport_country:
        profile["passport_country"] = body.passport_country
    if body.passport_expiry:
        profile["passport_expiry"] = body.passport_expiry

    if body.source_trip_id and body.source_trip_id not in profile["source_trip_ids"]:
        profile["source_trip_ids"].append(body.source_trip_id)

    profile["last_confirmed_at"] = now_iso

    AuditStore.log_event(
        event_type="customer_memory_updated",
        user_id=agency_id,
        details={
            "customer_id": profile["customer_id"],
            "name": profile["name"],
            "has_email": bool(norm_e),
            "has_phone": bool(norm_p),
            "source_trip_id": body.source_trip_id,
        },
    )

    return CustomerPreferenceProfile(
        customer_id=profile["customer_id"],
        name=profile["name"],
        email=profile.get("email"),
        phone=profile.get("phone"),
        dietary_requirements=profile.get("dietary_requirements"),
        room_preference=profile.get("room_preference"),
        seating_preference=profile.get("seating_preference"),
        passport_country=profile.get("passport_country"),
        passport_expiry=profile.get("passport_expiry"),
        source_trip_ids=profile.get("source_trip_ids", []),
        last_confirmed_at=profile["last_confirmed_at"],
    )


@router.post("/hydrate-trip/{trip_id}", response_model=HydrateTripResponse)
def hydrate_trip_with_customer_memory(
    trip_id: str,
    x_agency_id: Optional[str] = Header(None, alias="X-Agency-ID"),
):
    """Auto-hydrate a trip packet with matching customer memory based on customer email, phone, or name."""
    agency_id = x_agency_id or TEST_AGENCY_ID
    trip = TripStore.get_trip_for_agency(trip_id, agency_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    packet = trip.setdefault("packet", {})
    customer_name = packet.get("customer_name") or trip.get("customer_name") or trip.get("client_name")
    email = packet.get("customer_email") or trip.get("customer_email") or trip.get("email") or trip.get("client_email")
    phone = packet.get("customer_phone") or trip.get("customer_phone") or trip.get("phone") or trip.get("client_phone")

    profile = _find_customer_profile(email=email, phone=phone, name=customer_name)
    if not profile:
        return HydrateTripResponse(
            ok=True,
            trip_id=trip_id,
            memory_found=False,
            hydrated_fields=[],
            preferences={},
        )

    hydrated_fields = []
    preferences = {}

    if profile.get("dietary_requirements"):
        packet["dietary_requirements"] = profile["dietary_requirements"]
        preferences["dietary_requirements"] = profile["dietary_requirements"]
        hydrated_fields.append("dietary_requirements")

    if profile.get("room_preference"):
        packet["room_preference"] = profile["room_preference"]
        preferences["room_preference"] = profile["room_preference"]
        hydrated_fields.append("room_preference")

    if profile.get("seating_preference"):
        packet["seating_preference"] = profile["seating_preference"]
        preferences["seating_preference"] = profile["seating_preference"]
        hydrated_fields.append("seating_preference")

    if profile.get("passport_country"):
        packet["passport_country"] = profile["passport_country"]
        preferences["passport_country"] = profile["passport_country"]
        hydrated_fields.append("passport_country")

    packet["customer_memory_applied"] = True
    packet["customer_memory_id"] = profile["customer_id"]

    TripStore.save_trip(trip, agency_id=agency_id)

    AuditStore.log_event(
        event_type="customer_memory_hydrated",
        user_id=agency_id,
        details={
            "trip_id": trip_id,
            "customer_id": profile["customer_id"],
            "hydrated_fields": hydrated_fields,
        },
    )

    return HydrateTripResponse(
        ok=True,
        trip_id=trip_id,
        memory_found=True,
        customer_name=profile["name"],
        hydrated_fields=hydrated_fields,
        preferences=preferences,
    )
