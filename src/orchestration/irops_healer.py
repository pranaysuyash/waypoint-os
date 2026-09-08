"""
Live Irregular Operations (IROPS) Auto-Healer Engine (PER-IROPS-SIM).

Chains real-time disruption ripple cascade calculation, statutory passenger claims (EU261/US-DOT),
3-tier counterfactual alternative synthesis, emergency lodging VCC issuance,
and automated carrier fee waiver dispute generation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from src.fees.settlement_engine import FinancialSettlementEngine, VirtualCreditCard
from src.negotiation.fee_waiver_bot import FeeWaiverBot
from src.schemas.journey_graph import (
    DisruptionRippleReport,
    JourneyDependencyGraph,
)


@dataclass(slots=True)
class IROPSHealingPlan:
    """Complete multi-agent recovery plan for an irregular operation."""
    incident_id: str
    trip_id: str
    delayed_node_title: str
    delay_minutes: int
    ripple_report: DisruptionRippleReport
    statutory_compensation_amount_eur: float
    statutory_law_cited: str
    counterfactual_options: List[Dict[str, Any]]
    emergency_lodging_vcc: Optional[VirtualCreditCard]
    waiver_dispute_letter: str
    resolved_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "incident_id": self.incident_id,
            "trip_id": self.trip_id,
            "delayed_node_title": self.delayed_node_title,
            "delay_minutes": self.delay_minutes,
            "ripple_summary": self.ripple_report.operator_summary,
            "impacted_nodes_count": len(self.ripple_report.impacted_nodes),
            "statutory_compensation": {
                "amount_eur": self.statutory_compensation_amount_eur,
                "regulation": self.statutory_law_cited,
            },
            "counterfactual_options": self.counterfactual_options,
            "emergency_lodging_vcc": self.emergency_lodging_vcc.to_dict() if self.emergency_lodging_vcc else None,
            "waiver_dispute_letter": self.waiver_dispute_letter,
            "resolved_at": self.resolved_at,
        }


class IROPSAutoHealerEngine:
    """Simulates and executes automated self-healing recovery across disrupted journeys."""

    @classmethod
    def execute_healing_protocol(
        cls,
        trip_id: str,
        delayed_node_id: str,
        delay_minutes: int = 180,
        stored_graph: "JourneyDependencyGraph | None" = None,
    ) -> IROPSHealingPlan:
        # AT-06: operate on the traveler's stored journey, never a sample BA178 DAG.
        if stored_graph is not None and stored_graph.nodes:
            # Explicitly supplied graph (e.g. benchmarks): same contract as a
            # stored graph, minus the store round-trip.
            graph = stored_graph
        else:
            from spine_api.persistence import TripStore

            trip = TripStore.get_trip(trip_id) or {}
            stored_nodes = trip.get("journey_graph_nodes") or []
            stored_edges = trip.get("journey_graph_edges") or []
            graph = JourneyDependencyGraph.from_stored(trip_id, stored_nodes, stored_edges)
        if not graph.nodes:
            raise ValueError(
                f"No stored journey graph for trip '{trip_id}'. "
                "IROPS analysis abstains rather than synthesizing an itinerary."
            )

        # 2. Evaluate Disruption Ripple Cascade
        if delayed_node_id not in graph.nodes:
            raise ValueError(
                f"Node '{delayed_node_id}' is not in the stored journey graph for '{trip_id}'."
            )
        target_id = delayed_node_id
        ripple_report = graph.evaluate_disruption(target_id, delay_minutes=delay_minutes)

        # 3. Compute Statutory Passenger Rights Claim (EU261 long-haul >3500km, >3hr delay = €600)
        comp_amount = 600.0 if delay_minutes >= 180 else 300.0
        law_cited = "Regulation (EC) No 261/2004 (EU261 Long-Haul Tier 3)"

        # 4. Heuristic 3-tier alternatives — labeled preview, not live inventory.
        delayed = graph.nodes[target_id]
        delayed_title = delayed.title or delayed_node_id
        delayed_provider = delayed.provider or "Unknown carrier"
        delayed_ref = delayed.confirmation_code or trip_id
        counterfactuals = [
            {
                "tier": "OPTION_A_MIN_DELAY",
                "title": "Minimum-delay interline alternative (heuristic preview)",
                "arrival_delta_minutes": 45,
                "airline": None,
                "cabin_class": None,
                "additional_cost_usd": None,
                "status": "PREVIEW_ONLY",
                "provider_connected": False,
                "score_basis": "heuristic_hardcoded",
                "action": "REVIEW_ONLY — provider confirmation required",
            },
            {
                "tier": "OPTION_B_SAME_CARRIER",
                "title": f"Same-carrier revalidation for {delayed_provider} (heuristic preview)",
                "arrival_delta_minutes": 180,
                "airline": delayed_provider,
                "cabin_class": None,
                "additional_cost_usd": None,
                "status": "PREVIEW_ONLY",
                "provider_connected": False,
                "score_basis": "heuristic_hardcoded",
                "action": "REVIEW_ONLY — provider confirmation required",
            },
            {
                "tier": "OPTION_C_COMFORT_UPGRADE",
                "title": "Comfort-upgrade alternative (heuristic preview)",
                "arrival_delta_minutes": 90,
                "airline": None,
                "cabin_class": None,
                "additional_cost_usd": None,
                "status": "PREVIEW_ONLY",
                "provider_connected": False,
                "score_basis": "heuristic_hardcoded",
                "action": "REVIEW_ONLY — provider confirmation required",
            },
        ]

        # 5. Preview lodging VCC object (router strips before API; not a live instrument).
        vcc = FinancialSettlementEngine.issue_supplier_vcc(
            trip_id=trip_id,
            supplier_name="Preview lodging (not issued)",
            authorized_amount=350.0,
            currency="USD",
            validity_days=2,
        )

        # 6. Draft waiver against the delayed stored node, never a sample BA178.
        waiver_resp = FeeWaiverBot.generate_waiver_request(
            booking_ref=str(delayed_ref),
            supplier_name=delayed_provider,
            original_penalty_amount=250.0,
            reason="Inbound connection disruption on the stored journey graph",
            supplier_fault_incidents=[f"{delayed_title} delay > {delay_minutes} mins"],
        )
        waiver_letter = waiver_resp["waiver_letter"]

        return IROPSHealingPlan(
            incident_id=f"IROPS-{trip_id[-6:].upper()}",
            trip_id=trip_id,
            delayed_node_title=graph.nodes[target_id].title,
            delay_minutes=delay_minutes,
            ripple_report=ripple_report,
            statutory_compensation_amount_eur=comp_amount,
            statutory_law_cited=law_cited,
            counterfactual_options=counterfactuals,
            emergency_lodging_vcc=vcc,
            waiver_dispute_letter=waiver_letter,
        )
