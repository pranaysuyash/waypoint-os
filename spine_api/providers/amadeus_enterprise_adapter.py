"""Sandbox Amadeus Enterprise GDS & NDC Adapter for Waypoint OS.

Provides a simulated OAuth2-style credential flow (no authentication is
performed), flight offers search, and PNR booking creation. All results are
deterministic fixtures; there is no multi-host failover.
"""

# SIMULATED: deterministic in-process adapter. No network calls. Replace with
# a real client + credentials before production use.

from __future__ import annotations

import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass(slots=True)
class AmadeusFlightOffer:
    offer_id: str
    carrier_code: str
    flight_number: str
    origin: str
    destination: str
    departure_time: str
    arrival_time: str
    cabin_class: str
    fare_basis: str
    price_cents: int
    currency: str
    is_ndc: bool
    seats_available: int


class AmadeusEnterpriseAdapter:
    """Sandbox Amadeus GDS / NDC adapter.

    No token lifecycle management is performed; searches and bookings return
    canned deterministic responses regardless of credentials.
    """

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        hostname: Optional[str] = None,
    ) -> None:
        self.client_id = client_id or os.getenv("AMADEUS_CLIENT_ID", "")
        self.client_secret = client_secret or os.getenv("AMADEUS_CLIENT_SECRET", "")
        self.hostname = hostname or os.getenv("AMADEUS_HOSTNAME", "production.amadeus.com")
        self.is_production = "production" in self.hostname

    async def search_flight_offers(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        adults: int = 1,
        travel_class: str = "BUSINESS",
    ) -> List[AmadeusFlightOffer]:
        """Search flight offers across Amadeus GDS 1A and NDC feeds."""
        return [
            AmadeusFlightOffer(
                offer_id=f"1A-{uuid.uuid4().hex[:8]}",
                carrier_code="BA",
                flight_number="178",
                origin=origin.upper(),
                destination=destination.upper(),
                departure_time=f"{departure_date}T11:40:00Z",
                arrival_time=f"{departure_date}T14:25:00Z",
                cabin_class=travel_class,
                fare_basis="JFFLEX26",
                price_cents=362000,
                currency="USD",
                is_ndc=False,
                seats_available=4,
            ),
            AmadeusFlightOffer(
                offer_id=f"NDC-BA-{uuid.uuid4().hex[:8]}",
                carrier_code="BA",
                flight_number="178",
                origin=origin.upper(),
                destination=destination.upper(),
                departure_time=f"{departure_date}T11:40:00Z",
                arrival_time=f"{departure_date}T14:25:00Z",
                cabin_class=travel_class,
                fare_basis="JNDCDIRECT",
                price_cents=345000,
                currency="USD",
                is_ndc=True,
                seats_available=6,
            ),
        ]

    async def create_pnr_order(
        self, offer_id: str, passenger_details: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Issue confirmed PNR in Amadeus GDS / NDC."""
        pnr = f"1A{uuid.uuid4().hex[:4].upper()}"
        return {
            "pnr": pnr,
            "status": "CONFIRMED",
            "offer_id": offer_id,
            "passengers": [
                f"{p.get('last_name', 'DOE').upper()}/{p.get('first_name', 'JOHN').upper()}"
                for p in passenger_details
            ],
            "ticket_time_limit": "24H",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
