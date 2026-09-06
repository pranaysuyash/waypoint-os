"""
GDS Sandbox Connectivity Models (Amadeus & Sabre).

Defines typed schemas for live GDS sandbox flight offers, PNR creation, and ticketing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict


class GDSProvider(str, Enum):
    AMADEUS = "amadeus"
    SABRE = "sabre"


@dataclass(slots=True)
class GDSSandboxFlightOffer:
    """Standardized flight offer returned from Amadeus or Sabre sandbox."""
    offer_id: str
    provider: GDSProvider
    carrier_code: str
    flight_number: str
    origin_iata: str
    destination_iata: str
    departure_time: str
    arrival_time: str
    cabin_class: str
    total_price_usd: float
    fare_basis_code: str
    seats_available: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "offer_id": self.offer_id,
            "provider": self.provider.value,
            "carrier_code": self.carrier_code,
            "flight_number": self.flight_number,
            "origin_iata": self.origin_iata,
            "destination_iata": self.destination_iata,
            "departure_time": self.departure_time,
            "arrival_time": self.arrival_time,
            "cabin_class": self.cabin_class,
            "total_price_usd": self.total_price_usd,
            "fare_basis_code": self.fare_basis_code,
            "seats_available": self.seats_available,
        }


@dataclass(slots=True)
class GDSSandboxBookingResult:
    """PNR creation result from GDS Sandbox."""
    booking_reference: str
    provider: GDSProvider
    pnr_locator: str
    e_ticket_number: str
    total_charged_usd: float
    status: str = "TICKETED_CONFIRMED"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "booking_reference": self.booking_reference,
            "provider": self.provider.value,
            "pnr_locator": self.pnr_locator,
            "e_ticket_number": self.e_ticket_number,
            "total_charged_usd": self.total_charged_usd,
            "status": self.status,
            "created_at": self.created_at,
        }
