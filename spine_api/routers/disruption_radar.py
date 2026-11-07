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


# ---------------------------------------------------------------------------
# Operator-reported IRROPS signal ingestion (R2-H tranche, 2026-11-04)
# ---------------------------------------------------------------------------


class ReportDisruptionRequest(BaseModel):
    trigger_kind: str  # cancellation | delay | schedule_change | diversion | denial_of_boarding
    flight_ref: str
    notes: str = ""
    delay_minutes: Optional[int] = None


@router.post("/{trip_id}/report")
def report_disruption(
    trip_id: str,
    body: ReportDisruptionRequest,
    agency_id: str = Depends(get_current_agency_id),
):
    """Operator-reported disruption → stored ``active_disruption`` (R2-H).

    The honest interim signal source until provider feeds land (DP-04a):
    deterministic severity per the IRROPS semantics doc, operator_reported
    basis, idempotency marker. The existing /alerts surface renders stored
    rows and never fabricates on empty (F-38). Provider-observed rows will
    supersede by authority precedence when a feed lands.
    """
    from spine_api.services.irrops import IrropsReportError, evaluate_irrops_report
    from spine_api.persistence import AuditStore

    trip = TripStore.get_trip_for_agency(trip_id, agency_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    try:
        alert = evaluate_irrops_report(
            trip,
            trigger_kind=body.trigger_kind,
            flight_ref=body.flight_ref,
            notes=body.notes,
            delay_minutes=body.delay_minutes,
            operator_id=agency_id,
        )
    except IrropsReportError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    # Storage shape = the radar's DisruptionAlert contract (superset): the
    # report initially stored the raw IRROPS payload, whose keys
    # (flight_ref/trigger_kind/severity) don't match the alert model
    # (flight_number/disruption_type/urgency_level) — the /alerts surface
    # silently skipped every reported row (runtime-walk finding, 2026-11-06).
    # Write the alert-model keys PLUS the IRROPS provenance keys so both the
    # radar and the audit trail read one row.
    destination_name = str(trip.get("destination") or "Unknown")
    disruption_type = alert["trigger_kind"].upper()  # DELAY / CANCELLATION / ...
    radar_alert = {
        "disruption_id": f"irrops_{alert['idempotency_marker'].split(':')[-1]}_{abs(hash(alert['idempotency_marker'])) % 100000:05d}",
        "trip_id": trip_id,
        "destination": destination_name,
        "flight_number": alert["flight_ref"],
        "disruption_type": disruption_type,
        "urgency_level": alert["severity"].upper(),
        "delay_minutes": int(alert["delay_minutes"] or 0),
        "impact_summary": alert["notes"] or (
            f"Operator-reported {alert['trigger_kind'].replace('_', ' ')} on {alert['flight_ref']} "
            f"(source: operator_reported)"
        ),
        "status": "ACTIVE",
        "created_at": alert["created_at"],
        # IRROPS provenance superset (tolerated by the alert model filter):
        "trigger_kind": alert["trigger_kind"],
        "comp_relevant": alert["comp_relevant"],
        "source": alert["source"],
        "source_basis": alert["source_basis"],
        "reported_by": alert["reported_by"],
        "idempotency_marker": alert["idempotency_marker"],
    }
    updated = TripStore.update_trip_for_agency(trip_id, agency_id, {"active_disruption": radar_alert})
    if updated is None:
        raise HTTPException(status_code=404, detail="Trip not found")

    AuditStore.log_event(
        event_type="irrops_disruption_reported",
        user_id=agency_id,
        details={
            "trip_id": trip_id,
            "trigger_kind": alert["trigger_kind"],
            "flight_ref": alert["flight_ref"],
            "severity": alert["severity"],
            "source": alert["source"],
            "idempotency_marker": alert["idempotency_marker"],
        },
    )
    return {"ok": True, "trip_id": trip_id, "disruption": alert}


@router.post("/{trip_id}/resolve")
def resolve_disruption(
    trip_id: str,
    agency_id: str = Depends(get_current_agency_id),
):
    """Resolve the trip's active disruption (FND-0405): archive it to
    ``disruption_history`` and clear ``active_disruption`` so the radar
    reflects reality. The full IRROPS provenance row is preserved in the
    history entry — nothing is deleted."""
    from datetime import datetime as _dt
    from spine_api.persistence import AuditStore as _AuditStore

    trip = TripStore.get_trip_for_agency(trip_id, agency_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    active = trip.get("active_disruption")
    if not active:
        raise HTTPException(status_code=409, detail="Trip has no active disruption to resolve")

    resolved = dict(active)
    resolved["status"] = "RESOLVED"
    resolved["resolved_at"] = _dt.now(timezone.utc).isoformat()
    resolved["resolved_by"] = agency_id

    history = trip.get("disruption_history")
    if not isinstance(history, list):
        history = []
    history.append(resolved)

    updated = TripStore.update_trip_for_agency(
        trip_id, agency_id,
        {"active_disruption": None, "disruption_history": history},
    )
    if updated is None:
        raise HTTPException(status_code=404, detail="Trip not found")

    _AuditStore.log_event(
        event_type="irrops_disruption_resolved",
        user_id=agency_id,
        details={"trip_id": trip_id, "idempotency_marker": active.get("idempotency_marker")},
    )
    return {"ok": True, "trip_id": trip_id, "resolved": resolved.get("disruption_type") or resolved.get("trigger_kind")}
