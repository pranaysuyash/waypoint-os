"""Deterministic GDS preview endpoints (Amadeus and Sabre-shaped)."""

from __future__ import annotations

from typing import Any, Dict
from fastapi import APIRouter
from pydantic import BaseModel, Field

from src.distribution.amadeus_sandbox_adapter import AmadeusSandboxAdapter
from src.distribution.sabre_sandbox_adapter import SabreSandboxAdapter
from src.distribution.sandbox_models import GDSProvider
from spine_api.core.reality_tier import RealityTier, TierMetadata

router = APIRouter(prefix="/api/v1/gds-sandbox", tags=["gds-sandbox"])


class GDSSearchRequest(BaseModel):
    provider: GDSProvider = Field(GDSProvider.AMADEUS, description="GDS Provider (amadeus or sabre)")
    origin_iata: str = Field("JFK", description="Origin IATA airport code")
    destination_iata: str = Field("LHR", description="Destination IATA airport code")
    departure_date: str = Field("2026-10-15", description="Departure date YYYY-MM-DD")
    cabin_class: str = Field("BUSINESS", description="Cabin class")


class GDSBookRequest(BaseModel):
    provider: GDSProvider = Field(GDSProvider.AMADEUS, description="GDS Provider (amadeus or sabre)")
    offer_id: str = Field(..., description="Selected flight offer ID")
    traveler_name: str = Field("Sample Traveler", description="Preview traveler name; no provider order is created")


def _preview_metadata(feature_name: str) -> Dict[str, Any]:
    return {
        **TierMetadata.for_response(
            RealityTier.DETERMINISTIC_PREVIEW,
            feature_name,
            computation_method="deterministic sandbox adapter; no network call",
            missing_for_upgrade=[
                "provider credentials and authenticated session",
                "offer/order reconciliation and idempotency",
                "supplier confirmation or ticketing evidence",
            ],
        ),
        "provider_connected": False,
        "external_reference": None,
        "effects": [],
    }


@router.post("/search")
def search_gds_offers(payload: GDSSearchRequest) -> Dict[str, Any]:
    """Compute deterministic offer previews; no Amadeus/Sabre network call occurs."""
    if payload.provider == GDSProvider.AMADEUS:
        offers = AmadeusSandboxAdapter.search_flight_offers(
            origin_iata=payload.origin_iata,
            destination_iata=payload.destination_iata,
            departure_date=payload.departure_date,
            cabin=payload.cabin_class,
        )
    else:
        offers = SabreSandboxAdapter.bargain_finder_max(
            origin_iata=payload.origin_iata,
            destination_iata=payload.destination_iata,
            departure_date=payload.departure_date,
            cabin=payload.cabin_class,
        )

    return {
        "status": "PREVIEW_ONLY",
        "reality": _preview_metadata("gds_offer_search"),
        "provider": payload.provider.value,
        "offers_count": len(offers),
        "flight_offers": [o.to_dict() for o in offers],
    }


@router.post("/book")
def book_gds_order(payload: GDSBookRequest) -> Dict[str, Any]:
    """Return an unconfirmed booking preview; no PNR, ticket, charge, or mutation occurs."""
    if payload.provider == GDSProvider.AMADEUS:
        result = AmadeusSandboxAdapter.create_flight_order(
            offer_id=payload.offer_id,
            traveler_name=payload.traveler_name,
        )
    else:
        result = SabreSandboxAdapter.create_passenger_name_record(
            offer_id=payload.offer_id,
            traveler_name=payload.traveler_name,
        )

    booking_result = result.to_dict()
    booking_result.update(
        {
            "status": "PREVIEW_ONLY",
            "booking_reference": None,
            "pnr_locator": None,
            "e_ticket_number": None,
            "total_charged_usd": None,
            "provider_confirmation": None,
        }
    )
    return {
        "status": "PREVIEW_ONLY",
        "reality": _preview_metadata("gds_order_preview"),
        "booking_result": booking_result,
    }
