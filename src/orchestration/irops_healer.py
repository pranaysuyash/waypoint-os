"""
Live Irregular Operations (IROPS) Auto-Healer Engine (PER-IROPS-SIM).

Chains real-time disruption ripple cascade calculation, statutory passenger claims (EU261/US-DOT),
3-tier counterfactual alternative synthesis, emergency lodging VCC issuance,
and automated carrier fee waiver dispute generation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from src.fees.settlement_engine import FinancialSettlementEngine, VirtualCreditCard
from src.negotiation.fee_waiver_bot import FeeWaiverBot
from src.schemas.journey_graph import (
    DependencyRelation,
    DisruptionRippleReport,
    JourneyDependencyGraph,
    JourneyNode,
    NodeType,
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
    ) -> IROPSHealingPlan:
        # 1. Build Journey Graph Sample
        t0 = datetime(2026, 10, 15, 11, 40)
        graph = JourneyDependencyGraph(trip_id=trip_id)
        n1 = JourneyNode("N_FLT_178", NodeType.FLIGHT, "BA 178 (LHR -> JFK)", t0, t0 + timedelta(hours=8), "LHR", provider="British Airways")
        n2 = JourneyNode("N_FLT_490", NodeType.FLIGHT, "DL 490 (JFK -> SFO)", t0 + timedelta(hours=9, minutes=30), t0 + timedelta(hours=15), "JFK", provider="Delta")
        n3 = JourneyNode("N_HTL_SF", NodeType.HOTEL_CHECKIN, "San Francisco Luxury Hotel", t0 + timedelta(hours=16), t0 + timedelta(days=3), "SFO", provider="Four Seasons")

        graph.add_node(n1)
        graph.add_node(n2)
        graph.add_node(n3)
        graph.add_edge("N_FLT_178", "N_FLT_490", DependencyRelation.TRANSFER_CONNECTS, min_connection_minutes=90)
        graph.add_edge("N_FLT_490", "N_HTL_SF", DependencyRelation.HOTEL_NIGHT_FOR, min_connection_minutes=60)

        # 2. Evaluate Disruption Ripple Cascade
        target_id = delayed_node_id if delayed_node_id in graph.nodes else "N_FLT_178"
        ripple_report = graph.evaluate_disruption(target_id, delay_minutes=delay_minutes)

        # 3. Compute Statutory Passenger Rights Claim (EU261 long-haul >3500km, >3hr delay = €600)
        comp_amount = 600.0 if delay_minutes >= 180 else 300.0
        law_cited = "Regulation (EC) No 261/2004 (EU261 Long-Haul Tier 3)"

        # 4. Synthesize 3-Tier Counterfactual Re-routing Alternatives
        counterfactuals = [
            {
                "tier": "OPTION_A_MIN_DELAY",
                "title": "Air France AF022 Re-Route via CDG",
                "arrival_delta_minutes": 45,
                "airline": "Air France",
                "cabin_class": "Business",
                "additional_cost_usd": 0.0,
                "action": "Immediate Interline Endorsement",
            },
            {
                "tier": "OPTION_B_SAME_CARRIER",
                "title": "Next British Airways Direct Flight BA182",
                "arrival_delta_minutes": 180,
                "airline": "British Airways",
                "cabin_class": "Business (Club World)",
                "additional_cost_usd": 0.0,
                "action": "Automatic PNR Re-validation",
            },
            {
                "tier": "OPTION_C_COMFORT_UPGRADE",
                "title": "Virgin Atlantic Upper Class VS003 + Heathrow Clubhouse Access",
                "arrival_delta_minutes": 90,
                "airline": "Virgin Atlantic",
                "cabin_class": "Upper Class Suite",
                "additional_cost_usd": 150.0,
                "action": "Client 1-Click Approval Request",
            },
        ]

        # 5. Issue Emergency Accommodation Virtual Card
        vcc = FinancialSettlementEngine.issue_supplier_vcc(
            trip_id=trip_id,
            supplier_name="TWA Hotel at JFK Airport",
            authorized_amount=350.0,
            currency="USD",
            validity_days=2,
        )

        # 6. Generate Automated Fee Waiver Dispute Letter
        waiver_resp = FeeWaiverBot.generate_waiver_request(
            booking_ref="6XY7ZQ",
            supplier_name="British Airways",
            original_penalty_amount=250.0,
            reason="Inbound connection cancellation due to mechanical ground stop",
            supplier_fault_incidents=["BA178 Mechanical Delay > 180 mins"],
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
