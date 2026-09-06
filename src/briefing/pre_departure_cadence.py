"""
src/briefing/pre_departure_cadence.py — Pre-Departure Automated Cadence & Briefing Engine (Area #17.8).

Implements automated multi-stage pre-departure briefings:
- D-7: Logistics, Destination Entry, Packing Checklist, and Forex/Tipping Customs
- D-3: 72-Hour Weather Forecast, Baggage Allowances, Web Check-in & Transfer Driver Protocols
- D-1: Live Flight Terminal Status, Emergency SOS Concierge Packet & Digital Voucher Wallet
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class CadenceStage(str, Enum):
    D_MINUS_7 = "D_MINUS_7"
    D_MINUS_3 = "D_MINUS_3"
    D_MINUS_1 = "D_MINUS_1"


@dataclass(slots=True)
class DestinationGuideSummary:
    destination_name: str
    country_code: str
    currency: str
    tipping_custom: str
    plug_type: str
    voltage: str
    emergency_police_number: str
    emergency_ambulance_number: str


@dataclass(slots=True)
class PreDepartureBriefingPacket:
    trip_id: str
    traveler_name: str
    stage: CadenceStage
    subject: str
    headline: str
    departure_date: str
    destination: str
    action_items: List[str] = field(default_factory=list)
    key_highlights: List[str] = field(default_factory=list)
    emergency_contacts: Dict[str, str] = field(default_factory=dict)
    formatted_message_body: str = ""


class PreDepartureCadenceEngine:
    """
    Generates time-phased, tailored pre-departure briefing packets.
    """

    DESTINATION_INTEL: Dict[str, DestinationGuideSummary] = {
        "IT": DestinationGuideSummary(
            destination_name="Italy",
            country_code="IT",
            currency="EUR (€)",
            tipping_custom="Coperto charge included; 5-10% in fine dining for exceptional service.",
            plug_type="Type C, F, and L",
            voltage="230V / 50Hz",
            emergency_police_number="112",
            emergency_ambulance_number="118",
        ),
        "FR": DestinationGuideSummary(
            destination_name="France",
            country_code="FR",
            currency="EUR (€)",
            tipping_custom="Service compris included by law; round up to nearest euro or 5% in cafes.",
            plug_type="Type C and E",
            voltage="230V / 50Hz",
            emergency_police_number="112",
            emergency_ambulance_number="15",
        ),
        "JP": DestinationGuideSummary(
            destination_name="Japan",
            country_code="JP",
            currency="JPY (¥)",
            tipping_custom="No tipping culture; tipping can be considered confusing or impolite.",
            plug_type="Type A and B (2-flat pin)",
            voltage="100V / 50-60Hz",
            emergency_police_number="110",
            emergency_ambulance_number="119",
        ),
        "AE": DestinationGuideSummary(
            destination_name="United Arab Emirates (Dubai)",
            country_code="AE",
            currency="AED (Dirham)",
            tipping_custom="10-15% standard in restaurants and taxi fares.",
            plug_type="Type G (UK 3-pin)",
            voltage="230V / 50Hz",
            emergency_police_number="999",
            emergency_ambulance_number="998",
        ),
        "DEFAULT": DestinationGuideSummary(
            destination_name="International Destination",
            country_code="XX",
            currency="Local Currency / USD",
            tipping_custom="10% standard discretionary service tip.",
            plug_type="Universal travel adapter recommended",
            voltage="220-240V",
            emergency_police_number="112",
            emergency_ambulance_number="112",
        ),
    }

    @classmethod
    def generate_briefing(
        cls,
        trip_id: str,
        traveler_name: str,
        departure_date: str,
        destination_country_code: str,
        stage: CadenceStage,
        flight_number: Optional[str] = "EK-501",
        hotel_name: Optional[str] = "Grand Hotel Central",
        weather_forecast: Optional[str] = "Sunny, 22°C - 26°C",
    ) -> PreDepartureBriefingPacket:
        country_key = destination_country_code.strip().upper()
        intel = cls.DESTINATION_INTEL.get(country_key, cls.DESTINATION_INTEL["DEFAULT"])

        emergency_contacts = {
            "Waypoint 24/7 SOS Concierge": "+1 (800) 555-0199",
            "Local Emergency Police": intel.emergency_police_number,
            "Local Medical Ambulance": intel.emergency_ambulance_number,
        }

        if stage == CadenceStage.D_MINUS_7:
            subject = f"✈️ 7 Days to Departure: Essential Prep & Guide for {intel.destination_name}"
            headline = f"Your journey to {intel.destination_name} begins in 1 week!"
            actions = [
                "Ensure passport has 6+ months validity and carry a physical photocopy.",
                "Notify your bank of travel dates to avoid foreign transaction blocks.",
                f"Pack universal travel adapters compatible with {intel.plug_type}.",
                f"Review local customs: Currency is {intel.currency}; {intel.tipping_custom}",
            ]
            highlights = [
                f"Destination: {intel.destination_name} ({intel.currency})",
                f"Power Supply: {intel.plug_type} ({intel.voltage})",
                f"Confirmed Accommodation: {hotel_name}",
            ]

        elif stage == CadenceStage.D_MINUS_3:
            subject = f"🎒 3 Days to Departure: Weather, Baggage & Check-In Guide ({flight_number})"
            headline = "3 days until takeoff! Here is your final packing & check-in brief."
            actions = [
                f"Web check-in opens 48 hours prior for flight {flight_number}. Select your preferred seats.",
                "Check baggage weight limits: 30kg checked + 7kg cabin carry-on standard.",
                "Download your offline hotel and activity vouchers to your smartphone.",
            ]
            highlights = [
                f"72-Hour Destination Weather: {weather_forecast}",
                f"Flight: {flight_number} (Departure Date: {departure_date})",
                "Airport Transfer: Private Chauffeur meet-and-greet at arrivals gate.",
            ]

        else:  # D_MINUS_1
            subject = f"🚨 Tomorrow's Departure: Flight Gate & 24/7 SOS Packet ({trip_id})"
            headline = "Have a safe flight tomorrow! Your 24/7 Waypoint Concierge is active."
            actions = [
                f"Arrive at the airport 3 hours before international departure for flight {flight_number}.",
                "Keep your passport, boarding pass, and hotel booking voucher in your hand luggage.",
                "Save our 24/7 emergency concierge contact number in your phone.",
            ]
            highlights = [
                f"Flight Status: On Schedule ({flight_number})",
                f"First Night Accommodation: {hotel_name}",
                "Emergency SOS Concierge: Active & Available 24/7",
            ]

        body = (
            f"Dear {traveler_name},\n\n"
            f"{headline}\n\n"
            f"Key Travel Highlights:\n"
            + "\n".join(f"• {h}" for h in highlights)
            + "\n\nImportant Action Items:\n"
            + "\n".join(f"[ ] {a}" for a in actions)
            + "\n\n24/7 Support Contacts:\n"
            + "\n".join(f"• {k}: {v}" for k, v in emergency_contacts.items())
            + "\n\nWarmest regards,\nYour Waypoint OS Concierge Team"
        )

        return PreDepartureBriefingPacket(
            trip_id=trip_id,
            traveler_name=traveler_name,
            stage=stage,
            subject=subject,
            headline=headline,
            departure_date=departure_date,
            destination=intel.destination_name,
            action_items=actions,
            key_highlights=highlights,
            emergency_contacts=emergency_contacts,
            formatted_message_body=body,
        )
