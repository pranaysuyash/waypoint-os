"""
Negotiation & Revenue Optimization Models (PER-950888, PER-20690, PER-0482).

Defines typed schemas for B2B supplier concession offers, multi-round bargaining,
volume discount tiers, dynamic margin take-rates, and automated fee waivers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List


class NegotiationStatus(str, Enum):
    INITIATED = "initiated"
    COUNTER_OFFERED = "counter_offered"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"


class ConcessionType(str, Enum):
    NET_RATE_DISCOUNT = "net_rate_discount"
    COMMISSION_OVERRIDE = "commission_override"
    COMPLIMENTARY_UPGRADE = "complimentary_upgrade"
    FEE_WAIVER = "fee_waiver"
    FREE_BREAKFAST_OR_TRANSFER = "free_breakfast_or_transfer"


@dataclass(slots=True)
class VolumeTier:
    """Agency historical booking volume tier with supplier."""
    tier_name: str  # e.g., Titanium, Platinum, Gold, Silver
    annual_volume_usd: float
    base_commission_rate: float
    eligible_discount_percent: float


@dataclass(slots=True)
class ConcessionItem:
    """Specific concession requested or offered."""
    concession_type: ConcessionType
    requested_value: float
    granted_value: float = 0.0
    description: str = ""
    is_granted: bool = False


@dataclass(slots=True)
class NegotiationSession:
    """Multi-round negotiation interaction state."""
    session_id: str
    trip_id: str
    supplier_id: str
    supplier_name: str
    initial_quote: float
    target_budget: float
    current_offered_quote: float
    status: NegotiationStatus = NegotiationStatus.INITIATED
    round_number: int = 1
    max_rounds: int = 3
    concessions: List[ConcessionItem] = field(default_factory=list)
    history: List[Dict[str, Any]] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "trip_id": self.trip_id,
            "supplier_id": self.supplier_id,
            "supplier_name": self.supplier_name,
            "initial_quote": self.initial_quote,
            "target_budget": self.target_budget,
            "current_offered_quote": self.current_offered_quote,
            "status": self.status.value,
            "round_number": self.round_number,
            "max_rounds": self.max_rounds,
            "concessions": [
                {
                    "concession_type": c.concession_type.value,
                    "requested_value": c.requested_value,
                    "granted_value": c.granted_value,
                    "description": c.description,
                    "is_granted": c.is_granted,
                }
                for c in self.concessions
            ],
            "history": self.history,
            "created_at": self.created_at,
        }


@dataclass(slots=True)
class MarginOptimizationResult:
    """Dynamic margin calculation result."""
    net_supplier_cost: float
    optimized_selling_price: float
    effective_margin_percent: float
    gross_profit_usd: float
    urgency_multiplier: float
    lead_time_days: int
    elasticity_score: float
    recommendation_rationale: str
