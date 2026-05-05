"""
intake.regional_risk — deterministic regional disruption heuristics.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class RegionalRiskAssessment:
    risk_level: str
    signals: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)


CONFLICT_ZONE_DESTINATIONS = {
    "ukraine",
    "israel",
    "haiti",
}

HIGH_FRICTION_EUROPE_HUBS = {"CDG", "FRA", "LHR", "AMS", "FCO"}


def assess_regional_disruption(
    *,
    destinations: list[str],
    month: int | None,
    route_hubs: list[str] | None = None,
    flight_legs: int = 0,
) -> RegionalRiskAssessment:
    normalized_destinations = {d.strip().lower() for d in destinations if d}
    hubs = {h.strip().upper() for h in (route_hubs or []) if h}
    signals: list[str] = []
    recommendations: list[str] = []
    risk_level = "low"

    if normalized_destinations.intersection(CONFLICT_ZONE_DESTINATIONS):
        risk_level = "high"
        signals.append("active_regional_security_advisory")
        recommendations.append("Require human safety review and alternate routing before confirmation.")

    # Summer period where European hub disruptions (ATC/staffing/strikes) are
    # historically more frequent; modeled as operational pressure signal.
    if month in {6, 7, 8, 9} and hubs.intersection(HIGH_FRICTION_EUROPE_HUBS):
        if risk_level != "high":
            risk_level = "medium"
        signals.append("europe_summer_hub_pressure")
        recommendations.append("Add operational buffers for intra-Europe connections during peak disruption windows.")

    if flight_legs >= 4 and hubs.intersection(HIGH_FRICTION_EUROPE_HUBS):
        if risk_level == "low":
            risk_level = "medium"
        signals.append("multi_leg_hub_compound_risk")
        recommendations.append("Reduce legs or add longer layovers at high-friction hubs.")

    return RegionalRiskAssessment(
        risk_level=risk_level,
        signals=signals,
        recommendations=recommendations,
        details={
            "destinations": sorted(normalized_destinations),
            "route_hubs": sorted(hubs),
            "flight_legs": flight_legs,
            "month": month,
        },
    )

