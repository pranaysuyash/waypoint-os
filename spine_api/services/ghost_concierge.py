"""
spine_api.services.ghost_concierge — Autonomic in-trip disruption detection and recovery engine.

Monitors real-time flight telemetry, evaluates connection cascade risks,
and generates proactive recovery actions before travelers are stranded.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


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
    action_type: str  # "ALERT_AGENT" | "NOTIFY_HOTEL_LATE_CHECKIN" | "SEARCH_FALLBACK_FLIGHTS" | "DRAFT_EU261_CLAIM"
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
                    summary=f"Flight {f.flight_number} ({f.origin_iata}->{f.destination_iata}) has been CANCELLED.",
                    recommended_action="Hold alternative seats immediately on next available codeshare departure.",
                )
            )
            interventions.append(
                ConciergeIntervention(
                    action_type="DRAFT_EU261_CLAIM",
                    severity="INFO",
                    summary=f"Cancellation of {f.flight_number} may qualify for statutory regulatory compensation.",
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
