"""
spine_api/routers/fx_sentinel.py — Multi-Currency Dynamic FX Risk & Hedging Sentinel Engine (IDEA-125).

Monitors foreign currency exchange rates for international trip quotes (EUR, GBP, JPY, AUD), tracks margin exposure,
alerts advisors when FX drift exceeds agency risk thresholds, and supports 1-click rate hedging lock-ins.
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Header, HTTPException

from spine_api.persistence import TEST_AGENCY_ID, AuditStore, TripStore

router = APIRouter(prefix="/api/v1/fx", tags=["Multi-Currency FX Sentinel"])

# Simulated Live FX Rates relative to USD (1 USD = X target currency)
FX_RATES_TABLE: Dict[str, float] = {
    "USD": 1.0,
    "EUR": 0.92,
    "GBP": 0.78,
    "JPY": 155.0,
    "AUD": 1.52,
    "CAD": 1.36,
    "CHF": 0.90,
}


class FxRateRecord(BaseModel):
    base_currency: str = "USD"
    target_currency: str
    rate: float
    updated_at: str


class TripFxExposure(BaseModel):
    trip_id: str
    destination: str
    quoted_currency: str
    supplier_currency: str
    quoted_amount_cents: int
    supplier_amount_in_supplier_curr: float
    initial_rate: float
    current_rate: float
    fx_drift_pct: float
    margin_risk_cents: int
    risk_level: str  # LOW, WARNING, CRITICAL
    hedging_recommended: bool
    is_locked: bool = False


class LockFxRateRequest(BaseModel):
    trip_id: str
    locked_rate: float
    notes: Optional[str] = None


class LockFxRateResponse(BaseModel):
    ok: bool = True
    trip_id: str
    locked_rate: float
    locked_at: str


@router.get("/rates", response_model=List[FxRateRecord])
def get_live_fx_rates():
    """Retrieve current live foreign exchange rate table."""
    now_iso = datetime.now(timezone.utc).isoformat()
    return [
        FxRateRecord(target_currency=curr, rate=rate, updated_at=now_iso)
        for curr, rate in FX_RATES_TABLE.items()
    ]


@router.get("/exposures", response_model=List[TripFxExposure])
def list_fx_exposures(
    x_agency_id: Optional[str] = Header(None, alias="X-Agency-ID"),
):
    """Scan active trips for foreign currency margin exposure and FX drift risks."""
    agency_id = x_agency_id or TEST_AGENCY_ID
    trips = TripStore.list_trips(agency_id=agency_id)

    exposures: List[TripFxExposure] = []

    for trip in trips:
        strategy = trip.get("strategy", {}) or {}
        rec_option = strategy.get("recommended_option", {}) or {}
        cost_usd = rec_option.get("cost") or 3000.0

        dest = (trip.get("destination") or "").lower()
        supplier_curr = "EUR"
        if "tokyo" in dest or "japan" in dest:
            supplier_curr = "JPY"
        elif "london" in dest or "uk" in dest or "england" in dest:
            supplier_curr = "GBP"
        elif "sydney" in dest or "australia" in dest:
            supplier_curr = "AUD"

        current_rate = FX_RATES_TABLE.get(supplier_curr, 0.92)
        # Simulate initial rate slightly higher/lower
        initial_rate = round(current_rate * 1.035, 4)  # 3.5% drift

        supplier_amt = round(cost_usd * initial_rate, 2)
        current_cost_usd = round(supplier_amt / current_rate, 2)
        drift_pct = round(((current_cost_usd - cost_usd) / cost_usd) * 100.0, 2)
        risk_cents = max(0, int((current_cost_usd - cost_usd) * 100))

        if drift_pct >= 4.0:
            risk_lvl = "CRITICAL"
            hedge_rec = True
        elif drift_pct >= 2.0:
            risk_lvl = "WARNING"
            hedge_rec = True
        else:
            risk_lvl = "LOW"
            hedge_rec = False

        is_locked = strategy.get("fx_locked", False)

        exposures.append(
            TripFxExposure(
                trip_id=trip["id"],
                destination=trip.get("destination") or "Destination",
                quoted_currency="USD",
                supplier_currency=supplier_curr,
                quoted_amount_cents=int(cost_usd * 100),
                supplier_amount_in_supplier_curr=supplier_amt,
                initial_rate=initial_rate,
                current_rate=current_rate,
                fx_drift_pct=drift_pct,
                margin_risk_cents=risk_cents,
                risk_level=risk_lvl,
                hedging_recommended=hedge_rec,
                is_locked=is_locked,
            )
        )

    return exposures


@router.post("/lock-rate/{trip_id}", response_model=LockFxRateResponse)
def lock_fx_rate_hedging(
    trip_id: str,
    body: LockFxRateRequest,
    x_agency_id: Optional[str] = Header(None, alias="X-Agency-ID"),
):
    """Lock in FX exchange rate hedging for a trip to protect against currency drift."""
    agency_id = x_agency_id or TEST_AGENCY_ID
    trip = TripStore.get_trip_for_agency(trip_id, agency_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    strategy = trip.setdefault("strategy", {})
    now_iso = datetime.now(timezone.utc).isoformat()

    strategy["fx_locked"] = True
    strategy["fx_locked_rate"] = body.locked_rate
    strategy["fx_locked_at"] = now_iso

    TripStore.save_trip(trip, agency_id=agency_id)

    AuditStore.log_event(
        event_type="fx_rate_locked",
        user_id=agency_id,
        details={
            "trip_id": trip_id,
            "locked_rate": body.locked_rate,
            "notes": body.notes,
        },
    )

    return LockFxRateResponse(
        ok=True,
        trip_id=trip_id,
        locked_rate=body.locked_rate,
        locked_at=now_iso,
    )
