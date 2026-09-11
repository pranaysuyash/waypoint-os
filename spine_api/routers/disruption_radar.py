"""
spine_api/routers/disruption_radar.py — deterministic disruption preview surface.

The current implementation has no connected flight or booking provider. It
therefore returns deterministic previews and refuses to mutate booking state.
Provider-backed execution is a separate, evidence-gated integration.
"""

from datetime import datetime, timedelta, timezone
from typing import List, Optional

import logging

from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException

from spine_api.core.auth import get_current_agency_id
from spine_api.core.reality_tier import RealityTier, TierMetadata
from spine_api.persistence import TripStore

logger = logging.getLogger("spine_api.routers.disruption_radar")

router = APIRouter(prefix="/api/v1/disruptions", tags=["Real-Time Disruption Radar"])


class DisruptionAlert(BaseModel):
    disruption_id: str
    trip_id: str
    destination: str
    flight_number: str
    disruption_type: str  # CANCELLED, DELAYED, MISSED_CONNECTION
    urgency_level: str  # CRITICAL, WARNING, INFO
    delay_minutes: int
    impact_summary: str
    status: str = "ACTIVE"  # ACTIVE, REBOOKED, DISMISSED
    created_at: str
    reality_tier: str = RealityTier.DETERMINISTIC_PREVIEW.value
    provider_connected: bool = False
    effects: list[str] = Field(default_factory=list)


class ReBookOption(BaseModel):
    option_id: str
    airline: str
    flight_number: str
    departure_time: str
    arrival_time: str
    cabin_class: str
    price_difference_usd: float
    recommended: bool = False
    reality_tier: str = RealityTier.DETERMINISTIC_PREVIEW.value
    provider_connected: bool = False
    effects: list[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)


class ReBookRequest(BaseModel):
    trip_id: str
    disruption_id: str
    chosen_option_id: str
    advisor_note: Optional[str] = None


class ReBookResponse(BaseModel):
    ok: bool = False
    trip_id: str
    status: str = "DRAFT"
    new_flight_number: Optional[str] = None
    new_departure_time: Optional[str] = None
    rebooked_at: Optional[str] = None
    reality_tier: str = RealityTier.DETERMINISTIC_PREVIEW.value
    provider_connected: bool = False
    effects: list[str] = []
    metadata: dict = Field(default_factory=dict)


@router.get("/alerts", response_model=List[DisruptionAlert])
def list_disruption_alerts(
    agency_id: str = Depends(get_current_agency_id),
):
    """List preview alerts; no live feed is connected.

    Honesty rule (F-38): the radar surfaces only trips that HAVE stored
    disruption data (`active_disruption`). It no longer fabricates a default
    CRITICAL cancellation per trip — an empty result is the honest empty,
    and unscoped CRITICAL fabrication trains operators to ignore urgency.
    """
    trips = TripStore.list_trips(agency_id=agency_id)
    now_iso = datetime.now(timezone.utc).isoformat()

    alerts: List[DisruptionAlert] = []
    known_fields = set(DisruptionAlert.model_fields)

    for trip in trips:
        # Check if trip has active disruption data stored
        disruption_data = trip.get("active_disruption")
        if not disruption_data:
            continue
        # Tolerate legacy stored rows: filter unknown keys and backfill
        # created_at rather than 500-ing the whole surface on one bad row.
        sanitized = {k: v for k, v in disruption_data.items() if k in known_fields}
        if not sanitized.get("created_at"):
            sanitized["created_at"] = trip.get("updated_at") or now_iso
        try:
            alerts.append(DisruptionAlert(**sanitized))
        except Exception as e:
            logger.warning("Skipping malformed stored disruption for trip %s: %s", trip.get("id"), e)

    return alerts


@router.get("/{trip_id}/rebook-options", response_model=List[ReBookOption])
def get_rebook_options(
    trip_id: str,
    agency_id: str = Depends(get_current_agency_id),
):
    """Return deterministic alternatives for operator review, never a quote."""
    trip = TripStore.get_trip_for_agency(trip_id, agency_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    now = datetime.now(timezone.utc)
    dep_1 = (now + timedelta(hours=3)).isoformat()
    arr_1 = (now + timedelta(hours=11)).isoformat()
    dep_2 = (now + timedelta(hours=6)).isoformat()
    arr_2 = (now + timedelta(hours=14)).isoformat()

    metadata = TierMetadata.for_response(
        RealityTier.DETERMINISTIC_PREVIEW,
        "disruption_rebook_options",
        computation_method="local deterministic preview; no supplier availability check",
        missing_for_upgrade=["connected flight provider", "fresh availability", "fare quote", "booking reference"],
    )

    return [
        ReBookOption(
            option_id="opt_alt_1",
            airline="British Airways",
            flight_number="BA182",
            departure_time=dep_1,
            arrival_time=arr_1,
            cabin_class="Business",
            price_difference_usd=0.0,
            recommended=True,
            reality_tier=RealityTier.DETERMINISTIC_PREVIEW.value,
            provider_connected=False,
            effects=[],
            metadata=metadata,
        ),
        ReBookOption(
            option_id="opt_alt_2",
            airline="Virgin Atlantic",
            flight_number="VS020",
            departure_time=dep_2,
            arrival_time=arr_2,
            cabin_class="Business",
            price_difference_usd=150.0,
            recommended=False,
            reality_tier=RealityTier.DETERMINISTIC_PREVIEW.value,
            provider_connected=False,
            effects=[],
            metadata=metadata,
        ),
    ]


@router.post("/{trip_id}/rebook", response_model=ReBookResponse)
def execute_rebook(
    trip_id: str,
    body: ReBookRequest,
    agency_id: str = Depends(get_current_agency_id),
):
    """Refuse unverified rebooking; connected-provider execution is not wired."""
    trip = TripStore.get_trip_for_agency(trip_id, agency_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    # DETERMINISTIC_PREVIEW explicitly cannot mutate booking state. Keep the
    # capability assertion adjacent to the old mutation seam so a future
    # provider-backed implementation must opt into a higher, evidenced tier.
    from spine_api.core.reality_tier import assert_tier_capability

    assert_tier_capability(
        RealityTier.DETERMINISTIC_PREVIEW,
        "can_mutate_booking_state",
        "disruption_rebook",
    )

    # Defensive return for type checkers; assert_tier_capability always raises.
    return ReBookResponse(
        trip_id=trip_id,
        status="AWAITING_PROVIDER",
        metadata=TierMetadata.for_response(
            RealityTier.DETERMINISTIC_PREVIEW,
            "disruption_rebook",
            data_sufficient=False,
            computation_method="no mutation performed; provider confirmation required",
            missing_for_upgrade=["connected booking provider", "supplier confirmation", "idempotency key", "external booking reference"],
        ),
    )
