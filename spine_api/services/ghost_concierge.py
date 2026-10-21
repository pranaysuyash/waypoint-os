"""
spine_api.services.ghost_concierge — Autonomic in-trip disruption detection and recovery engine.

Monitors real-time flight telemetry, evaluates connection cascade risks,
and generates proactive recovery actions before travelers are stranded.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from spine_api.services.claim_framework import (
    AIRPORT_COUNTRY,
    MONTREAL_ARTICLE_19,
    resolve_carrier_country,
    resolve_framework,
)


@dataclass(slots=True)
class FlightTelemetry:
    flight_number: str
    carrier: str
    origin_iata: str
    destination_iata: str
    scheduled_departure: str  # ISO string
    scheduled_arrival: str  # ISO string
    actual_departure: Optional[str] = None
    actual_arrival: Optional[str] = None
    delay_minutes: int = 0
    status: str = "scheduled"  # "scheduled" | "active" | "delayed" | "cancelled" | "diverted"


@dataclass(slots=True)
class ConnectionRisk:
    inbound_flight: str
    outbound_flight: str
    layover_airport: str
    scheduled_layover_minutes: int
    effective_layover_minutes: int
    minimum_connection_time_minutes: int
    risk_level: str  # "LOW" | "MODERATE" | "CRITICAL_MISSED_CONNECTION"
    is_at_risk: bool


@dataclass(slots=True)
class ConciergeIntervention:
    action_type: str  # "ALERT_AGENT" | "NOTIFY_HOTEL_LATE_CHECKIN" | "SEARCH_FALLBACK_FLIGHTS" | "DRAFT_{EU261|UK261|US_DOT}_CLAIM" | "DRAFT_CLAIM" (no statutory regime)
    severity: str  # "INFO" | "WARNING" | "CRITICAL"
    summary: str
    recommended_action: str


@dataclass(slots=True)
class GhostConciergeReport:
    trip_id: str
    overall_health: str  # "STABLE" | "DEGRADED" | "DISRUPTED"
    flight_checks: List[FlightTelemetry]
    connection_risks: List[ConnectionRisk]
    interventions: List[ConciergeIntervention] = field(default_factory=list)


def _resolved_claim_framework(f: "FlightTelemetry") -> dict:
    """Resolve the statutory claim framework for one flight via the ONE
    canonical resolver (FND-0312) — the draft label can no longer claim
    EU261 for flights with no EU touchpoint."""
    carrier = resolve_carrier_country(f.carrier, f.flight_number)
    return resolve_framework(
        departure_country=AIRPORT_COUNTRY.get(f.origin_iata.upper()),
        arrival_country=AIRPORT_COUNTRY.get(f.destination_iata.upper()),
        carrier_country=carrier,
        distance_km=0.0,
        delay_hours=f.delay_minutes / 60.0,
        disruption_type=f.status.upper(),
    )


def _claim_action_label(f: "FlightTelemetry") -> str:
    """DRAFT_{framework}_CLAIM, or DRAFT_CLAIM when no statutory regime
    applies (NONE) — the frontend matches on nothing, it renders labels."""
    framework = _resolved_claim_framework(f)["framework"]
    return "DRAFT_CLAIM" if framework == "NONE" else f"DRAFT_{framework}_CLAIM"


def _claim_draft_summary(f: "FlightTelemetry") -> str:
    resolved = _resolved_claim_framework(f)
    framework = resolved["framework"]
    if framework == "NONE":
        return (
            f"Cancellation of {f.flight_number} is outside the EU261/UK261/US DOT "
            f"statutory scope — claimable under the {MONTREAL_ARTICLE_19} via the "
            "carrier's claims process."
        )
    return (
        f"Cancellation of {f.flight_number} may qualify for statutory compensation "
        f"under {framework}."
    )


def _flight_route_summary(f: "FlightTelemetry") -> str:
    """FND-0319: 'Flight TG318 (BKK->BOM)' when BOTH endpoints are known, else
    'Flight TG318' — never a bare or one-sided '(->)' arrow."""
    if f.origin_iata and f.destination_iata:
        return f"Flight {f.flight_number} ({f.origin_iata}->{f.destination_iata})"
    return f"Flight {f.flight_number}"


def evaluate_flight_telemetry(
    trip_id: str,
    flights: List[FlightTelemetry],
    minimum_connection_time_minutes: int = 60,
) -> GhostConciergeReport:
    """
    Evaluate flight telemetry stream and detect disruption cascades.
    """
    connection_risks: List[ConnectionRisk] = []
    interventions: List[ConciergeIntervention] = []
    is_disrupted = False
    is_degraded = False

    # 1. Analyze single flight delays and cancellations
    for f in flights:
        if f.status == "cancelled":
            is_disrupted = True
            interventions.append(
                ConciergeIntervention(
                    action_type="SEARCH_FALLBACK_FLIGHTS",
                    severity="CRITICAL",
                    # FND-0319: render the route only when both endpoints are
                    # known — never an empty "(->)" arrow.
                    summary=f"{_flight_route_summary(f)} has been CANCELLED.",
                    recommended_action="Hold alternative seats immediately on next available codeshare departure.",
                )
            )
            interventions.append(
                ConciergeIntervention(
                    action_type=_claim_action_label(f),
                    severity="INFO",
                    summary=_claim_draft_summary(f),
                    recommended_action="Trigger automated passenger rights claim filing.",
                )
            )
        elif f.delay_minutes >= 120:
            is_degraded = True
            interventions.append(
                ConciergeIntervention(
                    action_type="NOTIFY_HOTEL_LATE_CHECKIN",
                    severity="WARNING",
                    summary=f"Flight {f.flight_number} delayed by {f.delay_minutes} minutes.",
                    recommended_action="Transmit automated late arrival dispatch to destination hotel.",
                )
            )

    # 2. Analyze connection pairs
    for i in range(len(flights) - 1):
        f1 = flights[i]
        f2 = flights[i + 1]
        if f1.destination_iata == f2.origin_iata:
            scheduled_layover = 90  # default layover assumption
            effective_layover = max(0, scheduled_layover - f1.delay_minutes)
            is_at_risk = effective_layover < minimum_connection_time_minutes

            risk_level = "LOW"
            if is_at_risk:
                risk_level = "CRITICAL_MISSED_CONNECTION" if effective_layover <= 20 else "MODERATE"
                is_disrupted = True
                interventions.append(
                    ConciergeIntervention(
                        action_type="ALERT_AGENT",
                        severity="CRITICAL",
                        summary=f"Tight connection at {f1.destination_iata}: {effective_layover} min remaining (minimum required: {minimum_connection_time_minutes} min).",
                        recommended_action="Alert airport meet-and-greet fast-track or rebook second leg.",
                    )
                )

            connection_risks.append(
                ConnectionRisk(
                    inbound_flight=f1.flight_number,
                    outbound_flight=f2.flight_number,
                    layover_airport=f1.destination_iata,
                    scheduled_layover_minutes=scheduled_layover,
                    effective_layover_minutes=effective_layover,
                    minimum_connection_time_minutes=minimum_connection_time_minutes,
                    risk_level=risk_level,
                    is_at_risk=is_at_risk,
                )
            )

    overall_health = "DISRUPTED" if is_disrupted else ("DEGRADED" if is_degraded else "STABLE")

    return GhostConciergeReport(
        trip_id=trip_id,
        overall_health=overall_health,
        flight_checks=flights,
        connection_risks=connection_risks,
        interventions=interventions,
    )
