"""
Negotiation & Dynamic Margin API Router (PER-950888, PER-20690, PER-0482).

Provides REST endpoints for B2B supplier concession bargaining,
real-time margin curve optimization, and automated fee waiver generation.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter
from pydantic import BaseModel

from src.negotiation.bargaining_engine import BargainingEngine
from src.negotiation.margin_optimizer import MarginOptimizer
from src.negotiation.fee_waiver_bot import FeeWaiverBot
from src.negotiation.models import NegotiationSession, NegotiationStatus
from spine_api.core.feature_gates import get_feature_tier
from spine_api.core.reality_tier import TierMetadata

router = APIRouter(prefix="/api/v1/negotiation", tags=["negotiation"])


class StartSessionRequest(BaseModel):
    trip_id: str
    supplier_id: str
    supplier_name: str
    initial_quote: float
    target_budget: float
    agency_tier: str = "PLATINUM"


class CounterOfferRequest(BaseModel):
    session_id: str
    trip_id: str
    supplier_id: str
    supplier_name: str
    initial_quote: float
    target_budget: float
    current_offered_quote: float
    round_number: int = 1
    supplier_counter_quote: float


class OptimizeMarginRequest(BaseModel):
    net_supplier_cost: float
    lead_time_days: int
    is_peak_season: bool = False
    customer_price_sensitivity: float = 0.5


class FeeWaiverRequest(BaseModel):
    booking_ref: str
    supplier_name: str
    penalty_amount: float
    reason: str
    supplier_fault_incidents: Optional[List[str]] = None


@router.post("/sessions/start")
def start_negotiation_session(payload: StartSessionRequest) -> Dict[str, Any]:
    """Starts an autonomous multi-round negotiation session with a supplier."""
    session = BargainingEngine.start_session(
        trip_id=payload.trip_id,
        supplier_id=payload.supplier_id,
        supplier_name=payload.supplier_name,
        initial_quote=payload.initial_quote,
        target_budget=payload.target_budget,
        agency_tier_name=payload.agency_tier,
    )
    return {
        "status": "success",
        "session": session.to_dict(),
        "_meta": TierMetadata.for_response(
            get_feature_tier("supplier_negotiation"),
            "supplier_negotiation",
            computation_method="local game-theoretic bargaining simulation",
        ),
    }


@router.post("/sessions/evaluate-counter")
def evaluate_supplier_counter(payload: CounterOfferRequest) -> Dict[str, Any]:
    """Evaluates a supplier's counter-offer in an active negotiation round."""
    session = NegotiationSession(
        session_id=payload.session_id,
        trip_id=payload.trip_id,
        supplier_id=payload.supplier_id,
        supplier_name=payload.supplier_name,
        initial_quote=payload.initial_quote,
        target_budget=payload.target_budget,
        current_offered_quote=payload.current_offered_quote,
        round_number=payload.round_number,
        status=NegotiationStatus.COUNTER_OFFERED,
    )
    res = BargainingEngine.evaluate_supplier_counter(
        session=session,
        supplier_counter_quote=payload.supplier_counter_quote,
    )
    return {
        "status": "success",
        "evaluation": res,
        "_meta": TierMetadata.for_response(
            get_feature_tier("supplier_negotiation"),
            "supplier_negotiation",
            computation_method="local game-theoretic counter-offer evaluation",
        ),
    }


@router.post("/margins/optimize")
def optimize_dynamic_margin(payload: OptimizeMarginRequest) -> Dict[str, Any]:
    """Calculates dynamic take-rate margin based on lead time and elasticity."""
    result = MarginOptimizer.calculate_optimal_margin(
        net_supplier_cost=payload.net_supplier_cost,
        lead_time_days=payload.lead_time_days,
        is_peak_season=payload.is_peak_season,
        customer_price_sensitivity=payload.customer_price_sensitivity,
    )
    return {
        "status": "success",
        "_meta": TierMetadata.for_response(
            get_feature_tier("supplier_negotiation"),
            "supplier_negotiation",
            computation_method="deterministic margin optimization over supplied parameters",
        ),
        "margin_result": {
            "net_supplier_cost": result.net_supplier_cost,
            "optimized_selling_price": result.optimized_selling_price,
            "effective_margin_percent": result.effective_margin_percent,
            "gross_profit_usd": result.gross_profit_usd,
            "urgency_multiplier": result.urgency_multiplier,
            "lead_time_days": result.lead_time_days,
            "elasticity_score": result.elasticity_score,
            "rationale": result.recommendation_rationale,
        },
    }


@router.post("/waivers/generate")
def generate_supplier_fee_waiver(payload: FeeWaiverRequest) -> Dict[str, Any]:
    """Generates an automated contractual fee waiver letter for supplier desks."""
    res = FeeWaiverBot.generate_waiver_request(
        booking_ref=payload.booking_ref,
        supplier_name=payload.supplier_name,
        original_penalty_amount=payload.penalty_amount,
        reason=payload.reason,
        supplier_fault_incidents=payload.supplier_fault_incidents,
    )
    return {
        "status": "success",
        "waiver": res,
        "_meta": TierMetadata.for_response(
            get_feature_tier("supplier_waiver"),
            "supplier_waiver",
            computation_method="deterministic waiver letter drafting; nothing sent to suppliers",
        ),
    }
