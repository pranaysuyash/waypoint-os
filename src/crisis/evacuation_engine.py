"""
Multi-Modal Crisis Evacuation Router (PER-950889, PER-950898).

Calculates multi-modal escape routes bypassing compromised airspaces
using emergency private charter aircraft, armored overland convoys,
and international high-speed rail.
"""

from __future__ import annotations

import uuid
from typing import List
from src.crisis.models import (
    CrisisIncident,
    CrisisSeverity,
    EvacuationManifest,
    EvacuationLeg,
    EvacuationMode,
)


class EvacuationRouter:
    """Calculates multi-modal escape corridors during crisis events."""

    @staticmethod
    def generate_evacuation_manifest(
        incident: CrisisIncident,
        trip_id: str,
        passengers: List[str],
        current_location: str,
        safe_destination: str = "LHR",
    ) -> EvacuationManifest:
        """Constructs an end-to-end multi-modal emergency evacuation plan."""
        manifest_id = f"EVAC-{uuid.uuid4().hex[:8].upper()}"
        consular_ref = f"DOS-EMERG-{uuid.uuid4().hex[:6].upper()}"

        legs: List[EvacuationLeg] = []
        total_cost = 0.0

        if incident.severity == CrisisSeverity.CRITICAL_EVACUATION:
            # Stage 1: Overland secure convoy to nearest operational airstrip
            convoy_cost = 1_800.0 * max(1, len(passengers) // 3)
            legs.append(
                EvacuationLeg(
                    leg_number=1,
                    mode=EvacuationMode.OVERLAND_CONVOY,
                    origin=current_location,
                    destination="Secondary Safe Regional Airfield (Tactical)",
                    departure_time="T+01:30 (Immediate)",
                    carrier_or_provider="Secure Ground Armored Logistics",
                    capacity_passengers=len(passengers),
                    estimated_cost_usd=convoy_cost,
                    status="DISPATCHED",
                )
            )
            total_cost += convoy_cost

            # Stage 2: Private charter air evacuation to regional neutral hub
            charter_cost = 18_500.0
            legs.append(
                EvacuationLeg(
                    leg_number=2,
                    mode=EvacuationMode.AIR_CHARTER,
                    origin="Secondary Safe Regional Airfield",
                    destination=safe_destination,
                    departure_time="T+04:00 (On-standby)",
                    carrier_or_provider="Air Charter Ops (Citation Latitude / VIP)",
                    capacity_passengers=max(8, len(passengers)),
                    estimated_cost_usd=charter_cost,
                    status="CONFIRMED_SLOT",
                )
            )
            total_cost += charter_cost

        else:
            # Moderate disruption: High-Speed Rail + Commercial Rebook
            rail_cost = 350.0 * len(passengers)
            legs.append(
                EvacuationLeg(
                    leg_number=1,
                    mode=EvacuationMode.HIGH_SPEED_RAIL,
                    origin=current_location,
                    destination="Neutral Border Transit Hub",
                    departure_time="T+02:00",
                    carrier_or_provider="International Express Rail",
                    capacity_passengers=len(passengers),
                    estimated_cost_usd=rail_cost,
                    status="TICKETED",
                )
            )
            total_cost += rail_cost

            flight_cost = 850.0 * len(passengers)
            legs.append(
                EvacuationLeg(
                    leg_number=2,
                    mode=EvacuationMode.COMMERCIAL_REBOOK,
                    origin="Neutral Border Hub Airport",
                    destination=safe_destination,
                    departure_time="T+06:00",
                    carrier_or_provider="Commercial Airline Rescue Flight",
                    capacity_passengers=len(passengers),
                    estimated_cost_usd=flight_cost,
                    status="REBOOKED_HK",
                )
            )
            total_cost += flight_cost

        return EvacuationManifest(
            manifest_id=manifest_id,
            incident_id=incident.incident_id,
            trip_id=trip_id,
            passengers=passengers,
            assembly_point=f"Hotel Main Lobby / Verified Safe Zone at {current_location}",
            evacuation_legs=legs,
            total_evacuation_cost=total_cost,
            is_charter_confirmed=incident.severity == CrisisSeverity.CRITICAL_EVACUATION,
            consular_case_number=consular_ref,
        )
