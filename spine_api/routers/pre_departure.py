"""
spine_api/routers/pre_departure.py — Pre-Departure Briefing Bundle API.

Exposes two endpoints for the pre-departure briefing package:

GET /api/v1/trips/{trip_id}/pre-departure-bundle
    Returns a structured JSON briefing packet for the companion app tab.
    Reads traveler and destination data from the TripStore; falls back to
    sane defaults when fields are absent.

GET /api/v1/trips/{trip_id}/pre-departure-bundle.pdf
    Streams a rendered PDF bundle covering all three cadence stages (D-7,
    D-3, D-1) as a downloadable file.

Reality boundary: all content is deterministic preview (cadence templates +
stored trip data). Missing-for-upgrade: live flight status, visa API, and
weather API integration.
"""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Response, status

from spine_api import persistence
from spine_api.core.auth import get_current_agency_id
from src.briefing.pre_departure_cadence import CadenceStage, PreDepartureCadenceEngine

router = APIRouter(prefix="/api/v1/trips", tags=["pre-departure"])

TripStore = persistence.TripStore

_MISSING_FOR_UPGRADE = [
    "Live flight status API (FlightAware / airline status API)",
    "Visa requirements API (Sherpa / IATA Timatic)",
    "Live weather forecast API (OpenWeatherMap / weather.gov)",
    "Travel insurance confirmation document pull",
]

_ALL_STAGES = [CadenceStage.D_MINUS_7, CadenceStage.D_MINUS_3, CadenceStage.D_MINUS_1]


def _build_packets(trip_id: str, trip: Dict[str, Any]) -> list:
    """Build one briefing packet per cadence stage from TripStore data."""
    traveler_name = str(
        trip.get("traveler_name")
        or trip.get("lead_traveler_name")
        or "Valued Traveler"
    )
    departure_date = str(trip.get("departure_date") or trip.get("start_date") or "TBD")
    # Try to extract a 2-letter country code for destination intel lookup
    country_code = str(trip.get("destination_country_code") or "DEFAULT").upper()
    flight_number = str(
        (trip.get("booking_confirmation") or {}).get("flight_number")
        or trip.get("flight_number")
        or "TBD"
    )
    hotel_name = str(trip.get("hotel_name") or "Your confirmed accommodation")

    packets = []
    for stage in _ALL_STAGES:
        packet = PreDepartureCadenceEngine.generate_briefing(
            trip_id=trip_id,
            traveler_name=traveler_name,
            departure_date=departure_date,
            destination_country_code=country_code,
            stage=stage,
            flight_number=flight_number,
            hotel_name=hotel_name,
        )
        packets.append(packet)
    return packets


@router.get(
    "/{trip_id}/pre-departure-bundle",
    summary="Pre-departure briefing bundle (JSON)",
)
def get_pre_departure_bundle_json(
    trip_id: str,
    agency_id: str = Depends(get_current_agency_id),
) -> Dict[str, Any]:
    """Return all three cadence stage briefings (D-7, D-3, D-1) as structured JSON.

    Used by the traveler companion app pre-departure tab.
    """
    trip = TripStore.get_trip_for_agency(trip_id, agency_id)
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "trip_not_found", "trip_id": trip_id},
        )

    packets = _build_packets(trip_id, trip)
    stages = []
    for p in packets:
        stages.append(
            {
                "stage": p.stage.value,
                "subject": p.subject,
                "headline": p.headline,
                "departure_date": p.departure_date,
                "destination": p.destination,
                "action_items": p.action_items,
                "key_highlights": p.key_highlights,
                "emergency_contacts": p.emergency_contacts,
                "formatted_message_body": p.formatted_message_body,
            }
        )

    return {
        "trip_id": trip_id,
        "reality_tier": "deterministic_preview",
        "provider_connected": False,
        "missing_for_upgrade": _MISSING_FOR_UPGRADE,
        "stages": stages,
    }


@router.get(
    "/{trip_id}/pre-departure-bundle.pdf",
    summary="Pre-departure briefing bundle (PDF download)",
    response_class=Response,
)
def get_pre_departure_bundle_pdf(
    trip_id: str,
    agency_id: str = Depends(get_current_agency_id),
) -> Response:
    """Stream a fully rendered PDF covering all three cadence stages.

    The PDF is generated on demand from stored trip data and cadence templates.
    Content-Disposition is set to attachment so browsers download it.
    """
    trip = TripStore.get_trip_for_agency(trip_id, agency_id)
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "trip_not_found", "trip_id": trip_id},
        )

    packets = _build_packets(trip_id, trip)

    try:
        from src.briefing.pdf_renderer import render_briefing_pdf
        pdf_bytes = render_briefing_pdf(packets)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "pdf_render_failed", "reason": str(exc)},
        ) from exc

    filename = f"pre-departure-{trip_id[:12]}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Reality-Tier": "deterministic_preview",
            "X-Provider-Connected": "false",
        },
    )
