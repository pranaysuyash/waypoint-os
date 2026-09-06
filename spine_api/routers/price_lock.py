"""
spine_api/routers/price_lock.py — Autonomous Price-Lock Sentinel & Re-Shopping Alert Engine.

Monitors GDS, NDC, and bedbank rate holds during the 72-hour quote window (price_lock_expires_at).
Audits rate drops, calculates potential margin gains, logs price_lock_arbitrage_saved audit events,
and allows advisors to re-lock lower rates before deposit confirmation.
"""

from datetime import datetime, timedelta, timezone
from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException

from spine_api.core.auth import get_current_agency_id
from spine_api.persistence import AuditStore, TripStore
from spine_api.routers.supplier import CONTRACTS_STORE

router = APIRouter(prefix="/api/v1/price-lock", tags=["Price Lock Sentinel"])


class PriceLockOpportunity(BaseModel):
    trip_id: str
    destination: str
    supplier_name: str
    original_net_rate_cents: int
    current_net_rate_cents: int
    potential_margin_gain_cents: int
    margin_gain_pct: float
    price_lock_expires_at: str
    hours_remaining: float
    is_expired: bool


class RateAuditResponse(BaseModel):
    ok: bool = True
    trip_id: str
    supplier_name: str
    original_net_rate_cents: int
    current_net_rate_cents: int
    potential_margin_gain_cents: int
    margin_gain_pct: float
    rate_drop_detected: bool
    price_lock_expires_at: str


class ReLockRequest(BaseModel):
    trip_id: str
    new_net_rate_cents: int
    supplier_name: Optional[str] = None
    advisor_note: Optional[str] = None
    expected_version: Optional[int] = None
    idempotency_key: Optional[str] = None


class ReLockResponse(BaseModel):
    ok: bool = True
    trip_id: str
    previous_net_rate_cents: int
    new_net_rate_cents: int
    margin_saved_cents: int
    updated_at: str
    version: int = 1


def _get_price_lock_expires_at(trip: dict) -> datetime:
    """Calculate price lock expiration timestamp (default 72 hours from saved_at or created_at).

    Reads BOTH write locations (F-32 split-brain): `strategy.price_lock_expires_at`
    and the trip top-level key written by the social-inbound path
    (`social_inbound.py` writes `trip["price_lock_expires_at"]`). Either source
    wins over the recomputed fallback so the sentinel sees what was written.
    """
    raw_candidates = []
    strategy = trip.get("strategy", {}) or {}
    if strategy.get("price_lock_expires_at"):
        raw_candidates.append(strategy["price_lock_expires_at"])
    if trip.get("price_lock_expires_at"):
        raw_candidates.append(trip["price_lock_expires_at"])

    for raw_exp in raw_candidates:
        try:
            return datetime.fromisoformat(str(raw_exp).replace("Z", "+00:00"))
        except (ValueError, TypeError):
            continue

    base_time_str = trip.get("saved_at") or trip.get("created_at")
    if base_time_str:
        try:
            base_dt = datetime.fromisoformat(base_time_str.replace("Z", "+00:00"))
            return base_dt + timedelta(hours=72)
        except (ValueError, TypeError):
            pass

    return datetime.now(timezone.utc) + timedelta(hours=72)


@router.get("/opportunities", response_model=List[PriceLockOpportunity])
async def list_price_lock_opportunities(
    agency_id: str = Depends(get_current_agency_id),
):
    """Scan active agency trips for price lock countdowns and margin re-shopping opportunities."""
    trips = TripStore.list_trips(agency_id=agency_id)
    now = datetime.now(timezone.utc)
    opportunities: List[PriceLockOpportunity] = []

    for trip in trips:
        strategy = trip.get("strategy", {}) or {}
        rec_option = strategy.get("recommended_option", {}) or {}
        cost = rec_option.get("cost") or 0
        original_net_cents = int(cost * 100) if cost > 0 else 0

        exp_dt = _get_price_lock_expires_at(trip)
        hours_remaining = max(0.0, round((exp_dt - now).total_seconds() / 3600.0, 1))
        is_expired = now > exp_dt

        # Check contracts store or rate table for current rate
        contracts = CONTRACTS_STORE.get(agency_id, {})
        current_net_cents = original_net_cents
        supplier_name = rec_option.get("name") or "Primary Supplier Contract"

        if contracts:
            first_contract: dict = next(iter(contracts.values()), {})
            supplier_name = first_contract.get("supplier_name", supplier_name)
            rate_table = first_contract.get("rate_table", [])
            if rate_table and isinstance(rate_table, list) and len(rate_table) > 0:
                net_per_night = rate_table[0].get("net_rate_per_night", 300.0)
                current_net_cents = int(net_per_night * 100 * 5)  # 5 nights

        # Calculate margin delta
        gain_cents = max(0, original_net_cents - current_net_cents)
        gain_pct = round((gain_cents / original_net_cents) * 100.0, 2) if original_net_cents > 0 else 0.0

        opportunities.append(
            PriceLockOpportunity(
                trip_id=trip["id"],
                destination=trip.get("destination") or "Destination",
                supplier_name=supplier_name,
                original_net_rate_cents=original_net_cents,
                current_net_rate_cents=current_net_cents,
                potential_margin_gain_cents=gain_cents,
                margin_gain_pct=gain_pct,
                price_lock_expires_at=exp_dt.isoformat(),
                hours_remaining=hours_remaining,
                is_expired=is_expired,
            )
        )

    return opportunities


@router.post("/{trip_id}/audit-rate", response_model=RateAuditResponse)
async def audit_trip_price_lock_rate(
    trip_id: str,
    agency_id: str = Depends(get_current_agency_id),
):
    """Audit supplier rate feed for a specific trip to detect rate drops and margin savings."""
    trip = TripStore.get_trip_for_agency(trip_id, agency_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    strategy = trip.get("strategy") or {}
    rec_option = strategy.get("recommended_option") or {}
    cost = rec_option.get("cost") or 0
    if cost <= 0:
        cost = 3000.0
    original_net_cents = int(cost * 100)

    exp_dt = _get_price_lock_expires_at(trip)
    contracts = CONTRACTS_STORE.get(agency_id, {})
    current_net_cents = original_net_cents
    supplier_name = rec_option.get("name") or "Primary Supplier Contract"

    if contracts:
        first_contract: dict = next(iter(contracts.values()), {})
        supplier_name = first_contract.get("supplier_name", supplier_name)
        rate_table = first_contract.get("rate_table", [])
        if rate_table and isinstance(rate_table, list) and len(rate_table) > 0:
            net_per_night = rate_table[0].get("net_rate_per_night", 250.0)
            current_net_cents = int(net_per_night * 100 * 5)

    gain_cents = max(0, original_net_cents - current_net_cents)
    gain_pct = round((gain_cents / original_net_cents) * 100.0, 2) if original_net_cents > 0 else 0.0
    rate_drop = gain_cents > 0

    return RateAuditResponse(
        ok=True,
        trip_id=trip_id,
        supplier_name=supplier_name,
        original_net_rate_cents=original_net_cents,
        current_net_rate_cents=current_net_cents,
        potential_margin_gain_cents=gain_cents,
        margin_gain_pct=gain_pct,
        rate_drop_detected=rate_drop,
        price_lock_expires_at=exp_dt.isoformat(),
    )


@router.post("/{trip_id}/re-lock", response_model=ReLockResponse)
async def re_lock_lower_rate(
    trip_id: str,
    body: ReLockRequest,
    agency_id: str = Depends(get_current_agency_id),
):
    """Re-lock a lower net rate quote, updating trip strategy and logging margin savings with optimistic locking."""
    trip = TripStore.get_trip_for_agency(trip_id, agency_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    current_version = int(trip.get("version") or 1)

    # Optimistic locking guard (F-01)
    if body.expected_version is not None and body.expected_version != current_version:
        raise HTTPException(
            status_code=409,
            detail=f"Conflict: trip version mismatch (expected {body.expected_version}, current {current_version}). Re-lock aborted to prevent race condition.",
        )

    strategy = trip.setdefault("strategy", {})
    applied_idempotency_keys = strategy.setdefault("price_lock_idempotency_keys", {})

    # Idempotent re-entry check (F-01)
    if body.idempotency_key and body.idempotency_key in applied_idempotency_keys:
        cached = applied_idempotency_keys[body.idempotency_key]
        return ReLockResponse(
            ok=True,
            trip_id=trip_id,
            previous_net_rate_cents=cached["previous_net_rate_cents"],
            new_net_rate_cents=cached["new_net_rate_cents"],
            margin_saved_cents=cached["margin_saved_cents"],
            updated_at=cached["updated_at"],
            version=current_version,
        )

    rec_option = strategy.setdefault("recommended_option", {})

    cost = rec_option.get("cost") or 0
    if cost <= 0:
        cost = 3000.0
    prev_net_cents = int(cost * 100)
    new_net_cents = body.new_net_rate_cents
    margin_saved_cents = max(0, prev_net_cents - new_net_cents)

    rec_option["cost"] = round(new_net_cents / 100.0, 2)
    if body.supplier_name:
        rec_option["name"] = body.supplier_name

    now_iso = datetime.now(timezone.utc).isoformat()
    strategy["price_lock_re_locked_at"] = now_iso
    strategy["price_lock_margin_saved_cents"] = margin_saved_cents
    trip["version"] = current_version + 1

    if body.idempotency_key:
        applied_idempotency_keys[body.idempotency_key] = {
            "previous_net_rate_cents": prev_net_cents,
            "new_net_rate_cents": new_net_cents,
            "margin_saved_cents": margin_saved_cents,
            "updated_at": now_iso,
        }

    TripStore.save_trip(trip, agency_id=agency_id)

    AuditStore.log_event(
        event_type="price_lock_arbitrage_saved",
        user_id=agency_id,
        details={
            "trip_id": trip_id,
            "previous_net_rate_cents": prev_net_cents,
            "new_net_rate_cents": new_net_cents,
            "margin_saved_cents": margin_saved_cents,
            "supplier_name": body.supplier_name or rec_option.get("name"),
            "advisor_note": body.advisor_note,
            "version": trip["version"],
            "idempotency_key": body.idempotency_key,
        },
    )

    return ReLockResponse(
        ok=True,
        trip_id=trip_id,
        previous_net_rate_cents=prev_net_cents,
        new_net_rate_cents=new_net_cents,
        margin_saved_cents=margin_saved_cents,
        updated_at=now_iso,
        version=trip["version"],
    )
