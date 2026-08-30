"""
spine_api.services.pass_generator — Apple Wallet (.pkpass) and mobile pass manifest generator.

Produces standard PassKit JSON definitions for:
- Flight Boarding Passes (boardingPass)
- Hotel Confirmation Cards (eventTicket / generic)
- 24/7 Emergency Assistance & Agency Concierge Passes
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(slots=True)
class PassField:
    key: str
    label: str
    value: str
    change_message: Optional[str] = None


@dataclass(slots=True)
class ApplePassManifest:
    pass_type_identifier: str
    serial_number: str
    description: str
    organization_name: str
    team_identifier: str
    format_version: int = 1
    background_color: str = "rgb(13, 17, 23)"
    foreground_color: str = "rgb(255, 255, 255)"
    label_color: str = "rgb(139, 148, 158)"
    barcode: Dict[str, str] = field(default_factory=dict)
    primary_fields: List[PassField] = field(default_factory=list)
    secondary_fields: List[PassField] = field(default_factory=list)
    auxiliary_fields: List[PassField] = field(default_factory=list)
    back_fields: List[PassField] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "formatVersion": self.format_version,
            "passTypeIdentifier": self.pass_type_identifier,
            "serialNumber": self.serial_number,
            "teamIdentifier": self.team_identifier,
            "organizationName": self.organization_name,
            "description": self.description,
            "backgroundColor": self.background_color,
            "foregroundColor": self.foreground_color,
            "labelColor": self.label_color,
            "barcode": self.barcode,
            "generic": {
                "primaryFields": [{"key": f.key, "label": f.label, "value": f.value} for f in self.primary_fields],
                "secondaryFields": [{"key": f.key, "label": f.label, "value": f.value} for f in self.secondary_fields],
                "auxiliaryFields": [{"key": f.key, "label": f.label, "value": f.value} for f in self.auxiliary_fields],
                "backFields": [{"key": f.key, "label": f.label, "value": f.value} for f in self.back_fields],
            },
        }


def generate_hotel_pass_manifest(
    trip_id: str,
    traveler_name: str,
    hotel_name: str,
    confirmation_number: str,
    check_in_date: str,
    check_out_date: str,
    address: str,
    agency_name: str = "Waypoint OS Luxury Travel",
) -> ApplePassManifest:
    """
    Generate an Apple Wallet pass manifest for a luxury hotel reservation.
    """
    return ApplePassManifest(
        pass_type_identifier="pass.com.waypoint.hotel",
        serial_number=f"HTL-{trip_id}-{confirmation_number}",
        description=f"Hotel Reservation: {hotel_name}",
        organization_name=agency_name,
        team_identifier="WAYPOINT99",
        barcode={
            "format": "PKBarcodeFormatQR",
            "message": f"WAYPOINT:HTL:{confirmation_number}",
            "messageEncoding": "iso-8859-1",
        },
        primary_fields=[
            PassField(key="hotel", label="HOTEL", value=hotel_name),
        ],
        secondary_fields=[
            PassField(key="guest", label="GUEST", value=traveler_name),
            PassField(key="conf", label="CONFIRMATION", value=confirmation_number),
        ],
        auxiliary_fields=[
            PassField(key="checkin", label="CHECK-IN", value=check_in_date),
            PassField(key="checkout", label="CHECK-OUT", value=check_out_date),
        ],
        back_fields=[
            PassField(key="address", label="Hotel Address", value=address),
            PassField(key="support", label="24/7 Agency Hotline", value="+1-800-555-WAYPOINT"),
            PassField(key="trip", label="Trip Reference", value=trip_id),
        ],
    )
