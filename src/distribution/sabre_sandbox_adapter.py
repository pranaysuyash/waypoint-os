"""
Sabre Dev Studio REST / SOAP Sandbox Adapter.

Provides Bargain Finder Max (BFM) flight search and Create Passenger Name Record (Enhanced Air Book).
"""

from __future__ import annotations

import uuid
from typing import List

from src.distribution.sandbox_models import (
    GDSSandboxBookingResult,
    GDSSandboxFlightOffer,
    GDSProvider,
)


class SabreSandboxAdapter:
    """Enterprise REST/SOAP adapter for Sabre Dev Studio Sandbox."""

    @classmethod
    def bargain_finder_max(
        cls,
        origin_iata: str,
        destination_iata: str,
        departure_date: str = "2026-10-15",
        cabin: str = "BUSINESS",
    ) -> List[GDSSandboxFlightOffer]:
        """Simulates Sabre Bargain Finder Max (BFM) 50-itinerary low-fare search."""
        return [
            GDSSandboxFlightOffer(
                offer_id=f"SBR-BFM-{uuid.uuid4().hex[:6].upper()}",
                provider=GDSProvider.SABRE,
                carrier_code="AA",
                flight_number="AA100",
                origin_iata=origin_iata.upper(),
                destination_iata=destination_iata.upper(),
                departure_time=f"{departure_date}T18:15:00Z",
                arrival_time=f"{departure_date}T06:20:00Z",
                cabin_class=cabin,
                total_price_usd=3490.0,
                fare_basis_code="INCR01",
                seats_available=6,
            ),
            GDSSandboxFlightOffer(
                offer_id=f"SBR-BFM-{uuid.uuid4().hex[:6].upper()}",
                provider=GDSProvider.SABRE,
                carrier_code="DL",
                flight_number="DL001",
                origin_iata=origin_iata.upper(),
                destination_iata=destination_iata.upper(),
                departure_time=f"{departure_date}T21:30:00Z",
                arrival_time=f"{departure_date}T09:40:00Z",
                cabin_class=cabin,
                total_price_usd=3550.0,
                fare_basis_code="ZPROMO26",
                seats_available=5,
            ),
        ]

    @classmethod
    def create_passenger_name_record(
        cls,
        offer_id: str,
        traveler_name: str = "Alex Morgan",
    ) -> GDSSandboxBookingResult:
        """Simulates Sabre PassengerDetails / EnhancedAirBook with ticketing."""
        return GDSSandboxBookingResult(
            booking_reference=f"1S-{uuid.uuid4().hex[:6].upper()}",
            provider=GDSProvider.SABRE,
            pnr_locator=uuid.uuid4().hex[:6].upper(),
            e_ticket_number=f"001-{uuid.uuid4().int % 10000000000:010d}",
            total_charged_usd=3490.0,
            status="TICKETED_CONFIRMED",
        )
