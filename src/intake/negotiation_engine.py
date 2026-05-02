"""
intake.negotiation_engine — Agentic negotiation logic for Waypoint OS.

This service identifies opportunities to negotiate better prices or upgrades
with suppliers and manages the lifecycle of these 'haggles'.
"""

from __future__ import annotations
import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

from .packet_models import CanonicalPacket
from .decision import DecisionResult

logger = logging.getLogger("orchestration.negotiation")

@dataclass(slots=True)
class NegotiationOpportunity:
    supplier_name: str
    original_price: float
    target_price: float
    reason: str
    priority: int = 1  # 1 (High) to 5 (Low)

class NegotiationEngine:
    """
    Core engine for identifying and executing supplier negotiations.
    """

    def __init__(self):
        self.active_haggles: Dict[str, Dict[str, Any]] = {}

    def analyze_and_trigger(self, packet: CanonicalPacket, decision: DecisionResult) -> List[Dict[str, Any]]:
        """
        Analyzes a trip packet and decision to identify negotiation opportunities.
        """
        opportunities = self._identify_opportunities(packet, decision)
        logs = []

        for opp in opportunities:
            haggle_id = f"haggle_{packet.packet_id}_{opp.supplier_name.lower().replace(' ', '_')}"
            
            # Simulate trigger
            log_entry = {
                "id": haggle_id,
                "supplier_name": opp.supplier_name,
                "status": "NEGOTIATING",
                "best_bid": opp.target_price,
                "original_price": opp.original_price,
                "savings": opp.original_price - opp.target_price,
                "next_action": "Wait for supplier response",
                "last_message": f"Sent automated RFP for {opp.reason}"
            }
            logs.append(log_entry)
            logger.info(f"Negotiation triggered for {opp.supplier_name}: {haggle_id}")

        return logs

    def _identify_opportunities(self, packet: CanonicalPacket, decision: DecisionResult) -> List[NegotiationOpportunity]:
        """
        Internal logic to find where we can squeeze margin or add value.
        """
        opportunities = []
        
        # 1. High-Value Group Opportunity
        pax_count = packet.facts.get("pax_count", 1)
        if isinstance(pax_count, int) and pax_count >= 8:
            # Look for un-negotiated hotel candidates
            dest = packet.facts.get("resolved_destination", "Generic Destination")
            opportunities.append(NegotiationOpportunity(
                supplier_name=f"Grand {dest} Hotel",
                original_price=1200.0,
                target_price=950.0,
                reason="Group volume discount (8+ pax)"
            ))

        # 2. Luxury Upgrade Opportunity
        trip_purpose = str(packet.facts.get("trip_purpose", "")).lower()
        if "honeymoon" in trip_purpose or "anniversary" in trip_purpose:
            opportunities.append(NegotiationOpportunity(
                supplier_name="Premium Lounge Services",
                original_price=250.0,
                target_price=0.0,
                reason="Complimentary honeymoon upgrade"
            ))

        # 3. Budget Gap Negotiation
        # If the decision shows a budget blocker, try to negotiate down
        if "budget_excessive" in decision.hard_blockers:
            opportunities.append(NegotiationOpportunity(
                supplier_name="Local Tour Operator",
                original_price=500.0,
                target_price=420.0,
                reason="Budget alignment for conversion"
            ))

        return opportunities

# Singleton instance
negotiation_service = NegotiationEngine()
