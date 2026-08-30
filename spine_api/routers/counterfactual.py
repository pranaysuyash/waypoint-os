"""
spine_api/routers/counterfactual.py — Counterfactual 3-way IROPS replanning and Group Pareto consensus router.

Grounding doctrine:
- Travel Counterfactual Systems Architect: Deterministic multi-tier alternative recovery generation.
- Family/Group Travel Architect: Multi-party preference Pareto optimization.
"""

from __future__ import annotations

import logging
from dataclasses import asdict
from datetime import datetime, timezone
from fastapi import APIRouter

from spine_api.contract import (
    CounterfactualReplanningRequest,
    CounterfactualReplanningResponse,
    GroupConsensusRequest,
    GroupConsensusResponse,
)
from src.decision.counterfactual_recovery import CounterfactualReplanningEngine
from src.decision.group_consensus import (
    GroupConsensusOptimizer,
    ItineraryOptionProposal,
    TravelerPreferenceProfile,
)
from src.schemas.journey_graph import JourneyDependencyGraph, JourneyNode, NodeType

logger = logging.getLogger("spine_api.counterfactual")

router = APIRouter(prefix="/api/v1/counterfactual", tags=["counterfactual"])


@router.post("/replan-disruption", response_model=CounterfactualReplanningResponse)
def replan_disruption_endpoint(request: CounterfactualReplanningRequest) -> CounterfactualReplanningResponse:
    """
    Generate 3 ranked counterfactual recovery alternatives (Minimum Delay, Same Carrier, Premium Comfort).
    """
    now = datetime.now(timezone.utc)
    graph = JourneyDependencyGraph(trip_id=request.trip_id)
    graph.add_node(
        JourneyNode(
            node_id=request.disrupted_node_id,
            node_type=NodeType.FLIGHT,
            title="Scheduled Flight",
            start_time=now,
            end_time=now,
            location="Airport",
            provider="Air France",
        )
    )

    report = CounterfactualReplanningEngine.generate_alternatives(
        graph=graph,
        disrupted_node_id=request.disrupted_node_id,
        delay_minutes=request.delay_minutes,
    )

    alts = [asdict(a) for a in report.alternatives]
    for a in alts:
        a["strategy"] = a["strategy"].value if hasattr(a["strategy"], "value") else str(a["strategy"])

    return CounterfactualReplanningResponse(
        trip_id=report.trip_id,
        disrupted_node_id=report.disrupted_node_id,
        original_delay_hours=report.original_delay_hours,
        alternatives=alts,
        recommended_strategy=report.recommended_strategy.value,
        generated_at=report.generated_at,
    )


@router.post("/group-consensus", response_model=GroupConsensusResponse)
def group_consensus_endpoint(request: GroupConsensusRequest) -> GroupConsensusResponse:
    """
    Evaluate candidate group itineraries across individual traveler preference profiles using Pareto optimization.
    """
    travelers = [
        TravelerPreferenceProfile(
            traveler_id=t["traveler_id"],
            name=t["name"],
            max_budget_usd=float(t["max_budget_usd"]),
            preferred_pacing=t.get("preferred_pacing", "BALANCED"),
            priority_activities=t.get("priority_activities", []),
            requires_private_room=t.get("requires_private_room", True),
            dietary_restrictions=t.get("dietary_restrictions", []),
        )
        for t in request.travelers
    ]

    options = [
        ItineraryOptionProposal(
            option_id=o["option_id"],
            title=o["title"],
            total_cost_per_person_usd=float(o["total_cost_per_person_usd"]),
            pacing=o.get("pacing", "BALANCED"),
            included_activities=o.get("included_activities", []),
            rooming_configuration=o.get("rooming_configuration", "standard_double"),
        )
        for o in request.candidate_options
    ]

    scores = GroupConsensusOptimizer.evaluate_group_consensus(travelers, options)
    results = [asdict(s) for s in scores]

    return GroupConsensusResponse(
        results=results,
        total_options_evaluated=len(results),
    )
