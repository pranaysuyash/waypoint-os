"""
IATA NDC 21.3 Protocol Engine (PER-950887).

Implements NDC Offer and Order lifecycle management, mapping between
NDC JSON/XML schemas (AirShopping, OfferPrice, OrderCreate, OrderChange)
and Waypoint OS trip segments.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional
from src.distribution.gds_models import (
    NDCOrder,
    FlightSegment,
    SegmentStatus,
)


class NDCProtocolEngine:
    """IATA NDC 21.3 Order Lifecycle Management."""

    @staticmethod
    def create_air_shopping_request(
        origin: str,
        destination: str,
        departure_date: str,
        passengers_count: int = 1,
        cabin_preference: str = "BUSINESS",
    ) -> Dict[str, Any]:
        """Builds an IATA NDC 21.3 AirShoppingRQ payload."""
        return {
            "AirShoppingRQ": {
                "Document": {"ReferenceVersion": "21.3"},
                "Party": {
                    "Sender": {
                        "TravelAgencySender": {
                            "AgencyID": "WAYPOINT-OS-HQ",
                            "IATA_Number": "01234567",
                        }
                    }
                },
                "CoreQuery": {
                    "OriginDest": [
                        {
                            "Origin": {"AirportCode": origin.upper()},
                            "Destination": {"AirportCode": destination.upper()},
                            "Departure": {"Date": departure_date},
                        }
                    ]
                },
                "Preference": {
                    "CabinType": {"CabinTypeCode": cabin_preference.upper()}
                },
                "DataLists": {
                    "PassengerList": [
                        {"PassengerID": f"PAX_{i+1}", "PTC": "ADT"}
                        for i in range(passengers_count)
                    ]
                },
            }
        }

    @staticmethod
    def process_offer_price(
        offer_id: str,
        base_fare: float,
        taxes: float,
        currency: str = "USD",
        ancillaries: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Processes OfferPriceRS and computes total guaranteed price with ancillaries."""
        ancillary_total = sum(item.get("price", 0.0) for item in (ancillaries or []))
        total = base_fare + taxes + ancillary_total

        return {
            "offer_id": offer_id,
            "currency": currency,
            "base_fare": base_fare,
            "taxes": taxes,
            "ancillary_total": ancillary_total,
            "total_guaranteed_price": round(total, 2),
            "price_guarantee_time_limit_minutes": 30,
            "ancillaries_included": ancillaries or [],
        }

    @staticmethod
    def execute_order_create(
        offer_id: str,
        airline_code: str,
        passengers: List[str],
        segments: List[Dict[str, Any]],
        total_amount: float,
        currency: str = "USD",
    ) -> NDCOrder:
        """Executes OrderCreateRQ and returns a confirmed NDCOrder."""
        order_id = f"ORD-NDC-{airline_code}-{uuid.uuid4().hex[:8].upper()}"
        pnr_ref = f"NDC{uuid.uuid4().hex[:3].upper()}"

        flight_segments = [
            FlightSegment(
                segment_number=idx,
                carrier=s.get("carrier", airline_code),
                flight_number=s.get("flight_number", "100"),
                booking_class=s.get("booking_class", "J"),
                origin=s.get("origin", "LHR"),
                destination=s.get("destination", "JFK"),
                departure_datetime=s.get("departure", "2026-10-15T11:00:00Z"),
                arrival_datetime=s.get("arrival", "2026-10-15T14:30:00Z"),
                status=SegmentStatus.HK,
            )
            for idx, s in enumerate(segments, 1)
        ]

        return NDCOrder(
            order_id=order_id,
            offer_id=offer_id,
            airline_code=airline_code,
            total_amount=total_amount,
            currency=currency,
            status="CONFIRMED",
            pnr_reference=pnr_ref,
            passengers=passengers,
            segments=flight_segments,
        )
