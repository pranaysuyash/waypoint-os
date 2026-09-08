"""
Amadeus Enterprise & Self-Service REST Sandbox Adapter.

Provides flight offers search (v2/shopping/flight-offers) and order creation (v1/booking/flight-orders).
"""

from __future__ import annotations

import hashlib
import uuid
from typing import List, Optional

from src.distribution.sandbox_models import (
    GDSSandboxBookingResult,
    GDSSandboxFlightOffer,
    GDSProvider,
)


class AmadeusSandboxAdapter:
    """Enterprise REST adapter for Amadeus Travel Innovation Sandbox."""

    @classmethod
    def search_flight_offers(
        cls,
        origin_iata: str,
        destination_iata: str,
        departure_date: str = "2026-10-15",
        cabin: str = "BUSINESS",
    ) -> List[GDSSandboxFlightOffer]:
        """Simulates real-time Amadeus v2 Flight Offers Search."""
        return [
            GDSSandboxFlightOffer(
                offer_id=f"AMD-OFF-{uuid.uuid4().hex[:6].upper()}",
                provider=GDSProvider.AMADEUS,
                carrier_code="AF",
                flight_number="AF022",
                origin_iata=origin_iata.upper(),
                destination_iata=destination_iata.upper(),
                departure_time=f"{departure_date}T08:30:00Z",
                arrival_time=f"{departure_date}T16:45:00Z",
                cabin_class=cabin,
                total_price_usd=3850.0,
                fare_basis_code="JFFLEX26",
                seats_available=4,
            ),
            GDSSandboxFlightOffer(
                offer_id=f"AMD-OFF-{uuid.uuid4().hex[:6].upper()}",
                provider=GDSProvider.AMADEUS,
                carrier_code="BA",
                flight_number="BA178",
                origin_iata=origin_iata.upper(),
                destination_iata=destination_iata.upper(),
                departure_time=f"{departure_date}T11:40:00Z",
                arrival_time=f"{departure_date}T14:25:00Z",
                cabin_class=cabin,
                total_price_usd=3620.0,
                fare_basis_code="RCPROMO",
                seats_available=2,
            ),
        ]

    @classmethod
    def create_flight_order(
        cls,
        offer_id: str,
        traveler_name: str = "Alex Morgan",
        idempotency_key: Optional[str] = None,
    ) -> GDSSandboxBookingResult:
        """Simulates Amadeus v1 Flight Order Creation with instant ticket issuance.

        ``idempotency_key`` (Part-H P0, 2026-09-07): when provided, the PNR,
        e-ticket, and booking reference are derived deterministically from it,
        so re-issuing the same order — e.g. after a crash between the provider
        call and durable persistence — returns the SAME instruments instead of
        minting a second set. Live GDS idempotency follows this contract.
        """
        if idempotency_key:
            digest = hashlib.sha256(
                f"{idempotency_key}:{offer_id}:{traveler_name}".encode("utf-8")
            ).hexdigest().upper()
            pnr_locator = digest[:6]
            e_ticket_number = f"057-{int(digest[6:16], 16) % 10_000_000_000:010d}"
            booking_reference = f"1A-{digest[16:22]}"
        else:
            pnr_locator = uuid.uuid4().hex[:6].upper()
            e_ticket_number = f"057-{uuid.uuid4().int % 10000000000:010d}"
            booking_reference = f"1A-{uuid.uuid4().hex[:6].upper()}"
        return GDSSandboxBookingResult(
            booking_reference=booking_reference,
            provider=GDSProvider.AMADEUS,
            pnr_locator=pnr_locator,
            e_ticket_number=e_ticket_number,
            total_charged_usd=3850.0,
            status="TICKETED_CONFIRMED",
        )
