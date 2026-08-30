"""
Autonomous B2B Bargaining Engine (PER-950888, PER-20690).

Executes game-theoretic multi-round concession bargaining with DMCs,
wholesalers, and hotel groups based on agency volume leverage.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional
from src.negotiation.models import (
    NegotiationSession,
    NegotiationStatus,
    ConcessionItem,
    ConcessionType,
    VolumeTier,
)


class BargainingEngine:
    """Multi-Round Automated Supplier Negotiation Bot."""

    # Agency supplier volume tiers
    VOLUME_TIERS: Dict[str, VolumeTier] = {
        "TITANIUM": VolumeTier("Titanium", annual_volume_usd=1_000_000, base_commission_rate=0.18, eligible_discount_percent=0.12),
        "PLATINUM": VolumeTier("Platinum", annual_volume_usd=500_000, base_commission_rate=0.15, eligible_discount_percent=0.08),
        "GOLD": VolumeTier("Gold", annual_volume_usd=200_000, base_commission_rate=0.12, eligible_discount_percent=0.05),
        "STANDARD": VolumeTier("Standard", annual_volume_usd=50_000, base_commission_rate=0.10, eligible_discount_percent=0.02),
    }

    @classmethod
    def start_session(
        cls,
        trip_id: str,
        supplier_id: str,
        supplier_name: str,
        initial_quote: float,
        target_budget: float,
        agency_tier_name: str = "PLATINUM",
    ) -> NegotiationSession:
        """Initiates an automated bargaining session."""
        session_id = f"NEG-{uuid.uuid4().hex[:8].upper()}"
        tier = cls.VOLUME_TIERS.get(agency_tier_name.upper(), cls.VOLUME_TIERS["STANDARD"])

        # Target discount calculation
        gap = initial_quote - target_budget
        max_discount_allowed = initial_quote * tier.eligible_discount_percent
        initial_discount_ask = min(gap, max_discount_allowed)

        concessions = [
            ConcessionItem(
                concession_type=ConcessionType.NET_RATE_DISCOUNT,
                requested_value=round(initial_discount_ask, 2),
                description=f"Volume Tier ({tier.tier_name}) Rate Adjustment",
            ),
            ConcessionItem(
                concession_type=ConcessionType.COMPLIMENTARY_UPGRADE,
                requested_value=1.0,
                description="Complimentary Room Category Upgrade / VIP Amenity",
            ),
        ]

        history = [
            {
                "round": 1,
                "actor": "waypoint_agent",
                "action": "PROPOSE_DISCOUNT",
                "requested_discount": initial_discount_ask,
                "target_quote": initial_quote - initial_discount_ask,
                "justification": f"Waypoint OS accounts for USD {tier.annual_volume_usd:,.0f} annual volume with {supplier_name}.",
            }
        ]

        return NegotiationSession(
            session_id=session_id,
            trip_id=trip_id,
            supplier_id=supplier_id,
            supplier_name=supplier_name,
            initial_quote=initial_quote,
            target_budget=target_budget,
            current_offered_quote=initial_quote - initial_discount_ask,
            status=NegotiationStatus.INITIATED,
            round_number=1,
            concessions=concessions,
            history=history,
        )

    @classmethod
    def evaluate_supplier_counter(
        cls,
        session: NegotiationSession,
        supplier_counter_quote: float,
        supplier_granted_concessions: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Evaluates supplier counter-offer and decides whether to ACCEPT, COUNTER, or REJECT."""
        gap = supplier_counter_quote - session.target_budget
        is_acceptable = gap <= (session.initial_quote * 0.03)  # Within 3% tolerance

        if is_acceptable:
            session.status = NegotiationStatus.ACCEPTED
            session.current_offered_quote = supplier_counter_quote
            decision = "ACCEPT"
            rationale = "Counter-offer is within agency profit tolerance and budget threshold."
        elif session.round_number >= session.max_rounds:
            session.status = NegotiationStatus.REJECTED
            decision = "ESCALATE_TO_HUMAN"
            rationale = f"Max negotiation rounds ({session.max_rounds}) reached. Escalate to senior procurement."
        else:
            session.round_number += 1
            session.status = NegotiationStatus.COUNTER_OFFERED
            # Split difference for next round
            next_offer = (session.current_offered_quote + supplier_counter_quote) / 2.0
            session.current_offered_quote = round(next_offer, 2)
            decision = "COUNTER_SPLIT_DIFFERENCE"
            rationale = f"Splitting gap: proposing USD {session.current_offered_quote:.2f} with complimentary upgrade concession."

        session.history.append({
            "round": session.round_number,
            "actor": "waypoint_evaluation",
            "decision": decision,
            "supplier_counter": supplier_counter_quote,
            "rationale": rationale,
        })

        return {
            "session": session.to_dict(),
            "decision": decision,
            "rationale": rationale,
        }
