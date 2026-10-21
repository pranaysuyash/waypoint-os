"""Ghost Concierge monitoring — T11b wiring (decided 2026-09-30).

Wires the previously-orphaned ``ghost_concierge`` engine as a COMPOSITION
layer: this module sources real flight-status facts, runs the engine's pure
evaluation, and on risk produces DRAFTED, gated interventions for the
operator plus irops_healer cascade linkage. It never sends anything and
never moves money (ADR-008 §7 decision-support rung; T10 invariant class).

Telemetry sources (decision pack §3):
1. Trip flight facts — operator-entered/extracted status on the trip record.
2. Traveler messages — inbound disruption reports via the T1/T6 ask loop.
3. Provider adapter — a live feed implements FlightStatusProvider once the
   B6/B7 quota gate opens (2026-10-06); until then the seam returns nothing.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Protocol

from spine_api.services.ghost_concierge import (
    FlightTelemetry,
    GhostConciergeReport,
    evaluate_flight_telemetry,
)

# Statuses an operator or traveler can report for a flight.
REPORTABLE_STATUSES = ("scheduled", "active", "delayed", "cancelled", "diverted")

# Inbound traveler phrases that count as first-party disruption telemetry.
_DISRUPTION_MESSAGE_MARKERS = ("cancel", "delay", "divert", "stranded", "missed my connect")


class FlightStatusProvider(Protocol):
    """Narrow seam for a live telemetry feed (B6/B7 gate, 2026-10-06).

    Implementations return telemetry for the given flight numbers; an empty
    list means "no data" — never fabricate. The operator-reported provider is
    the default until a live feed exists.
    """

    def get_telemetry(self, flight_numbers: List[str]) -> List[FlightTelemetry]: ...


class OperatorReportedProvider:
    """Sources telemetry from trip flight facts + traveler messages.

    This is the honest day-one provider: every fact is attributed to a human
    who reported it. Nothing here is simulated.
    """

    def get_telemetry(self, flight_numbers: List[str]) -> List[FlightTelemetry]:
        del flight_numbers  # facts are pulled per-trip by monitor_evaluate_trip
        return []


def telemetry_from_trip_facts(trip: Dict[str, Any]) -> List[FlightTelemetry]:
    """Build FlightTelemetry from operator-entered flight status on the trip.

    Reads ``trip["flight_status_updates"]`` — a list of operator-reported
    records: {flight_number, origin_iata, destination_iata, status,
    delay_minutes, reported_at}. Absent key ⇒ no telemetry (never guessed).
    """
    updates = trip.get("flight_status_updates")
    if not isinstance(updates, list):
        return []
    telemetry: List[FlightTelemetry] = []
    for u in updates:
        if not isinstance(u, dict) or not u.get("flight_number"):
            continue
        status = str(u.get("status", "scheduled")).lower()
        if status not in REPORTABLE_STATUSES:
            continue
        # FND-0319: when the flight-fact record carries no route, fall back to
        # the trip-level origin/destination so summaries never render a bare
        # "(->)" arrow. Both absent ⇒ empty strings (route omitted downstream).
        origin = u.get("origin_iata") or trip.get("origin") or ""
        destination = u.get("destination_iata") or trip.get("destination") or ""
        telemetry.append(
            FlightTelemetry(
                flight_number=str(u["flight_number"]),
                carrier=str(u.get("carrier", "")),
                origin_iata=str(origin),
                destination_iata=str(destination),
                scheduled_departure=str(u.get("scheduled_departure", "")),
                scheduled_arrival=str(u.get("scheduled_arrival", "")),
                delay_minutes=int(u.get("delay_minutes", 0) or 0),
                status=status,
            )
        )
    return telemetry


def traveler_disruption_signals(trip: Dict[str, Any]) -> List[Dict[str, Any]]:
    """First-party disruption telemetry from the traveler message store.

    A traveler saying "my flight was cancelled" through the ask loop is the
    most honest telemetry that exists. Returns matching messages (id, text,
    received_at) — evaluation callers may fold these into interventions;
    they are never invented here.
    """
    signals: List[Dict[str, Any]] = []
    try:
        from spine_api.services.message_store import MessageStore

        messages = MessageStore().list_messages(str(trip.get("id", "")))  # best-effort
    except Exception:
        return signals
    for m in messages or []:
        text = str(getattr(m, "text", "") or (m.get("text") if isinstance(m, dict) else "")).lower()
        if any(marker in text for marker in _DISRUPTION_MESSAGE_MARKERS):
            signals.append(
                {
                    "message_id": getattr(m, "id", None) or (m.get("id") if isinstance(m, dict) else None),
                    "text": text[:280],
                    "source": "traveler_message",
                }
            )
    return signals


def monitor_evaluate_trip(
    trip: Dict[str, Any],
    provider: Optional[FlightStatusProvider] = None,
) -> Optional[GhostConciergeReport]:
    """Run the ghost-concierge evaluation for one trip.

    Returns None when there is no telemetry at all (nothing to monitor —
    the engine is never fed invented data). Returns the report otherwise;
    callers chain irops_healer on DISRUPTED/DEGRADED and surface drafted
    interventions to the operator.
    """
    flight_numbers = [
        str(u.get("flight_number"))
        for u in (trip.get("flight_status_updates") or [])
        if isinstance(u, dict) and u.get("flight_number")
    ]
    telemetry = telemetry_from_trip_facts(trip)
    if provider is not None and flight_numbers:
        telemetry.extend(provider.get_telemetry(flight_numbers))
    if not telemetry:
        return None
    return evaluate_flight_telemetry(str(trip.get("id", "")), telemetry)


def workflow_from_report(report: GhostConciergeReport, agency_id: str) -> Dict[str, Any]:
    """Truth-up payload: a ghost workflow row created by a REAL evaluation.

    Replaces the fabricated PLANNED rows — this record carries the engine's
    actual output and advances in step with it.
    """
    return {
        "origin": "ghost_concierge_monitor",
        "trip_id": report.trip_id,
        "agency_id": agency_id,
        "overall_health": report.overall_health,
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "connection_risks": [
            {
                "inbound": r.inbound_flight,
                "outbound": r.outbound_flight,
                "airport": r.layover_airport,
                "risk_level": r.risk_level,
                "at_risk": r.is_at_risk,
            }
            for r in report.connection_risks
        ],
        # Interventions are DRAFTS for operator review — proposal, never send.
        "drafted_interventions": [
            {
                "action_type": i.action_type,
                "severity": i.severity,
                "summary": i.summary,
                "recommended_action": i.recommended_action,
                "status": "DRAFT_AWAITING_OPERATOR",
            }
            for i in report.interventions
        ],
        "reality_note": "evaluated from operator/traveler-reported flight facts; "
        "live provider feed pending B6/B7 gate (2026-10-06)",
    }


def _match_journey_node(trip: Dict[str, Any], flight_number: str) -> Optional[str]:
    """Map a disrupted flight to a stored journey-graph node id, if any."""
    for node in (trip.get("journey_graph_nodes") or []):
        blob = " ".join(str(node.get(k, "")) for k in ("id", "title", "confirmation_code"))
        if flight_number and flight_number.lower() in blob.lower():
            return node.get("id")
    return None


def run_ghost_concierge_for_trip(
    trip: Dict[str, Any],
    agency_id: str,
    provider: Optional[FlightStatusProvider] = None,
) -> Optional[Dict[str, Any]]:
    """Serving-path entry (T11b step 2): evaluate, persist truth-up, chain healer.

    Called when flight facts change or a traveler disruption message arrives.
    Persists the real-evaluation workflow on the trip record, chains
    irops_healer when the disrupted flight maps to a stored journey node (the
    healer abstains otherwise — by design it never synthesizes an itinerary),
    and always leaves interventions as operator-gated drafts.
    """
    report = monitor_evaluate_trip(trip, provider=provider)
    if report is None:
        return None

    wf = workflow_from_report(report, agency_id)

    disrupted = [
        t for t in report.flight_checks
        if t.status == "cancelled" or t.delay_minutes >= 120
    ]
    if disrupted and not (trip.get("journey_graph_nodes") or []):
        wf["healer_note"] = "healer not chained: trip has no stored journey graph"
    if disrupted and (trip.get("journey_graph_nodes") or []):
        try:
            from src.orchestration.irops_healer import IROPSAutoHealerEngine

            target = disrupted[0]
            node_id = _match_journey_node(trip, target.flight_number)
            if node_id:
                plan = IROPSAutoHealerEngine.execute_healing_protocol(
                    str(trip.get("id", "")),
                    node_id,
                    delay_minutes=max(120, target.delay_minutes or 120),
                )
                wf["healer_plan"] = plan.to_dict()
                wf["healer_note"] = "chained from ghost-concierge risk detection"
        except ValueError:
            # Healer abstained (no graph / node mismatch) — drafts stand alone.
            wf["healer_note"] = "healer abstained: no matching stored journey node"

    trip["ghost_concierge"] = wf
    try:
        from spine_api.persistence import TripStore, AuditStore

        TripStore.save_trip(trip, agency_id=agency_id)
        AuditStore.log_event(
            event_type="ghost_concierge_evaluated",
            user_id=agency_id,
            details={
                "trip_id": trip.get("id"),
                "overall_health": report.overall_health,
                "interventions": len(report.interventions),
            },
        )
    except Exception:
        # Observability/persistence side-effect must never crash the caller.
        pass
    return wf
