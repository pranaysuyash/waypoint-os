"""
GDS & Distribution Core Models (PER-950887, PER-950895, PER-0967).

Defines typed schemas for GDS PNRs, EDIFACT message segments, SSR/OSI items,
Ticketing Time Limits (TKTL), Fare Rules (Cat 16 Penalties, Cat 35 Negotiated),
and IATA NDC 21.3 Offer/Order structures.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class SegmentStatus(str, Enum):
    HK = "HK"  # Holds Confirmed
    TK = "TK"  # Schedule change confirmed
    UN = "UN"  # Unable / Flight cancelled
    NO = "NO"  # No action taken
    HL = "HL"  # Have listed (Waitlist)
    SS = "SS"  # Sold / Pending confirmation
    RR = "RR"  # Reconfirmed


class GDSSystem(str, Enum):
    AMADEUS = "amadeus"
    SABRE = "sabre"
    TRAVELPORT = "travelport"
    NDC_DIRECT = "ndc_direct"


class FareType(str, Enum):
    PUBLISHED = "published"
    NEGOTIATED_CAT35 = "negotiated_cat35"
    CORPORATE_PRIVATE = "corporate_private"
    TOUR_OPERATOR = "tour_operator"


@dataclass(slots=True)
class SSRItem:
    """Special Service Request (SSR) item."""
    code: str  # e.g., WCHR, VGML, BSCT
    carrier: str
    passenger_index: int
    text: str = ""
    status: str = "HK"


@dataclass(slots=True)
class OSIItem:
    """Other Service Information (OSI) item."""
    carrier: str
    text: str


@dataclass(slots=True)
class FlightSegment:
    """Flight segment in a GDS PNR or NDC Order."""
    segment_number: int
    carrier: str
    flight_number: str
    booking_class: str
    origin: str
    destination: str
    departure_datetime: str
    arrival_datetime: str
    status: SegmentStatus = SegmentStatus.HK
    aircraft_type: Optional[str] = None
    baggage_allowance: Optional[str] = "1PC"
    fare_basis: Optional[str] = None


@dataclass(slots=True)
class FareRuleSummary:
    """Fare rule analysis breakdown (Cat 16 / Cat 35)."""
    fare_basis: str
    fare_type: FareType = FareType.PUBLISHED
    is_refundable: bool = False
    cancellation_fee: float = 0.0
    change_fee: float = 0.0
    min_stay_days: int = 0
    max_stay_days: int = 365
    endorsement_text: str = ""
    cat35_markup_permitted: bool = True


@dataclass(slots=True)
class GDSPNRRecord:
    """Complete GDS PNR data structure."""
    record_locator: str
    gds_system: GDSSystem
    agency_pcc: str
    passengers: List[str]
    segments: List[FlightSegment]
    ticketing_time_limit: Optional[str] = None
    is_ticketed: bool = False
    ticket_numbers: List[str] = field(default_factory=list)
    ssrs: List[SSRItem] = field(default_factory=list)
    osis: List[OSIItem] = field(default_factory=list)
    fare_rules: List[FareRuleSummary] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "record_locator": self.record_locator,
            "gds_system": self.gds_system.value,
            "agency_pcc": self.agency_pcc,
            "passengers": self.passengers,
            "segments": [
                {
                    "segment_number": s.segment_number,
                    "carrier": s.carrier,
                    "flight_number": s.flight_number,
                    "booking_class": s.booking_class,
                    "origin": s.origin,
                    "destination": s.destination,
                    "departure_datetime": s.departure_datetime,
                    "arrival_datetime": s.arrival_datetime,
                    "status": s.status.value,
                    "aircraft_type": s.aircraft_type,
                    "baggage_allowance": s.baggage_allowance,
                    "fare_basis": s.fare_basis,
                }
                for s in self.segments
            ],
            "ticketing_time_limit": self.ticketing_time_limit,
            "is_ticketed": self.is_ticketed,
            "ticket_numbers": self.ticket_numbers,
            "ssrs": [{"code": s.code, "carrier": s.carrier, "text": s.text, "status": s.status} for s in self.ssrs],
            "osis": [{"carrier": o.carrier, "text": o.text} for o in self.osis],
            "fare_rules": [
                {
                    "fare_basis": f.fare_basis,
                    "fare_type": f.fare_type.value,
                    "is_refundable": f.is_refundable,
                    "cancellation_fee": f.cancellation_fee,
                    "change_fee": f.change_fee,
                    "min_stay_days": f.min_stay_days,
                    "max_stay_days": f.max_stay_days,
                    "endorsement_text": f.endorsement_text,
                    "cat35_markup_permitted": f.cat35_markup_permitted,
                }
                for f in self.fare_rules
            ],
            "created_at": self.created_at,
        }


@dataclass(slots=True)
class NDCOrder:
    """IATA NDC 21.3 Order representation."""
    order_id: str
    offer_id: str
    airline_code: str
    total_amount: float
    currency: str
    status: str = "CONFIRMED"
    pnr_reference: Optional[str] = None
    passengers: List[str] = field(default_factory=list)
    segments: List[FlightSegment] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "order_id": self.order_id,
            "offer_id": self.offer_id,
            "airline_code": self.airline_code,
            "total_amount": self.total_amount,
            "currency": self.currency,
            "status": self.status,
            "pnr_reference": self.pnr_reference,
            "passengers": self.passengers,
            "segments": [
                {
                    "segment_number": s.segment_number,
                    "carrier": s.carrier,
                    "flight_number": s.flight_number,
                    "booking_class": s.booking_class,
                    "origin": s.origin,
                    "destination": s.destination,
                    "departure_datetime": s.departure_datetime,
                    "arrival_datetime": s.arrival_datetime,
                    "status": s.status.value,
                }
                for s in self.segments
            ],
            "created_at": self.created_at,
        }
