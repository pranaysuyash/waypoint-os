"""
spine_api/routers/fx_sentinel.py — deterministic FX risk preview (IDEA-125).

The local implementation has no connected market-data feed, treasury provider,
or executable hedge. It can still calculate illustrative exposure from the
reference table and persisted trip data, but the API must never present those
calculations as a live rate, a confirmed hedge, or a financial effect.
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Header, HTTPException

from spine_api.core.reality_tier import RealityTier, TierMetadata
from spine_api.persistence import TEST_AGENCY_ID, TripStore

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
    status: str = "PREVIEW_ONLY"
    reality_tier: str = RealityTier.DETERMINISTIC_PREVIEW.value
    evidence_status: str = "UNVERIFIED_REFERENCE_RATE"
    source: str = "local_reference_table"
    provider_connected: bool = False
    external_reference: Optional[str] = None
    effects: List[str] = Field(default_factory=list)
    metadata: Dict[str, object] = Field(default_factory=dict)


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
    risk_level: str  # UNKNOWN, LOW, WARNING, CRITICAL
    hedging_recommended: bool
    is_locked: bool = False
    status: str = "COMPUTED_PREVIEW"
    reality_tier: str = RealityTier.DETERMINISTIC_PREVIEW.value
    evidence_status: str = "UNVERIFIED_LOCAL_CALCULATION"
    provider_connected: bool = False
    external_reference: Optional[str] = None
    effects: List[str] = Field(default_factory=list)
    metadata: Dict[str, object] = Field(default_factory=dict)


class LockFxRateRequest(BaseModel):
    trip_id: str
    locked_rate: float
    notes: Optional[str] = None


class LockFxRateResponse(BaseModel):
    ok: bool = False
    trip_id: str
    locked_rate: float
    locked_at: Optional[str] = None
    status: str = "PREVIEW_ONLY"
    lock_applied: bool = False
    reality_tier: str = RealityTier.DETERMINISTIC_PREVIEW.value
    evidence_status: str = "NOT_EXECUTED"
    provider_connected: bool = False
    external_reference: Optional[str] = None
    effects: List[str] = Field(default_factory=list)
    metadata: Dict[str, object] = Field(default_factory=dict)


_FX_PREVIEW_MISSING = [
    "authenticated market-data or treasury provider",
    "freshness and quote-expiry policy",
    "authorized hedge execution provider",
    "external confirmation and reconciliation",
]


def _preview_metadata(feature_name: str, *, data_sufficient: bool = True) -> Dict[str, object]:
    """Build the canonical non-operational contract for local FX calculations."""
    metadata = TierMetadata.for_response(
        RealityTier.DETERMINISTIC_PREVIEW,
        feature_name,
        data_sufficient=data_sufficient,
        computation_method="local deterministic reference table and trip heuristic; no market-data or treasury call",
        missing_for_upgrade=_FX_PREVIEW_MISSING,
    )
    metadata.update(
        {
            "source": "local_deterministic_preview",
            "simulation": True,
            "provider_connected": False,
            "external_reference": None,
            "external_action": False,
            "operational_write": False,
            "effects": [],
        }
    )
    return metadata


@router.get("/rates", response_model=List[FxRateRecord])
def get_live_fx_rates():
    """Return deterministic reference rates; no live market feed is connected."""
    now_iso = datetime.now(timezone.utc).isoformat()
    metadata = _preview_metadata("fx_reference_rates")
    return [
        FxRateRecord(
            target_currency=curr,
            rate=rate,
            updated_at=now_iso,
            metadata=metadata,
        )
        for curr, rate in FX_RATES_TABLE.items()
    ]


@router.get("/exposures", response_model=List[TripFxExposure])
def list_fx_exposures(
    x_agency_id: Optional[str] = Header(None, alias="X-Agency-ID"),
):
    """Calculate illustrative exposure from local trip data and reference rates."""
    agency_id = x_agency_id or TEST_AGENCY_ID
    trips = TripStore.list_trips(agency_id=agency_id)

    exposures: List[TripFxExposure] = []

    for trip in trips:
        strategy = trip.get("strategy", {}) or {}
        rec_option = strategy.get("recommended_option", {}) or {}
        cost_value = rec_option.get("cost")
        has_cost = isinstance(cost_value, (int, float)) and cost_value > 0
        cost_usd = float(cost_value) if has_cost else 0.0

        dest = (trip.get("destination") or "").lower()
        supplier_curr = "EUR"
        if "tokyo" in dest or "japan" in dest:
            supplier_curr = "JPY"
        elif "london" in dest or "uk" in dest or "england" in dest:
            supplier_curr = "GBP"
        elif "sydney" in dest or "australia" in dest:
            supplier_curr = "AUD"

        current_rate = FX_RATES_TABLE.get(supplier_curr)
        if current_rate is None:
            current_rate = 0.0

        if has_cost and current_rate > 0:
            # The initial rate is a deterministic scenario input, not a prior
            # provider observation. Keep that distinction explicit in metadata.
            initial_rate = round(current_rate * 1.035, 4)
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
        else:
            initial_rate = 0.0
            supplier_amt = 0.0
            drift_pct = 0.0
            risk_cents = 0
            risk_lvl = "UNKNOWN"
            hedge_rec = False

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
                is_locked=False,
                evidence_status=(
                    "UNVERIFIED_LOCAL_CALCULATION" if has_cost else "INSUFFICIENT_TRIP_DATA"
                ),
                metadata=_preview_metadata(
                    "fx_trip_exposure",
                    data_sufficient=has_cost,
                ),
            )
        )

    return exposures


@router.post("/lock-rate/{trip_id}", response_model=LockFxRateResponse)
def lock_fx_rate_hedging(
    trip_id: str,
    body: LockFxRateRequest,
    x_agency_id: Optional[str] = Header(None, alias="X-Agency-ID"),
):
    """Preview a hedge request without mutating the trip or contacting a provider."""
    agency_id = x_agency_id or TEST_AGENCY_ID
    trip = TripStore.get_trip_for_agency(trip_id, agency_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    return LockFxRateResponse(
        ok=False,
        trip_id=trip_id,
        locked_rate=body.locked_rate,
        metadata=_preview_metadata("fx_rate_lock_request"),
    )
