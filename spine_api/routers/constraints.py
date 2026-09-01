"""
spine_api/routers/constraints.py — Spatial-Temporal & Regulatory Constraint Satisfaction Router.

Endpoints:
  GET  /api/v1/constraints/rules              — Active deterministic rules catalog (PER-0711)
  POST /api/v1/constraints/evaluate/{trip_id} — Feasibility evaluation of trip itinerary graph (PER-0711/0706)
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import List, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from spine_api.contract import (
    ConstraintEvaluationResponse,
    ConstraintRuleItem,
    ConstraintRulesResponse,
    ConstraintViolationModel,
)
from spine_api.core.auth import get_current_agency_id

try:
    from spine_api import persistence
except (ImportError, ValueError):
    import persistence

TripStore = persistence.TripStore

from src.decision.constraint_engine import ConstraintEngine  # noqa: E402
from src.schemas.journey_graph import JourneyDependencyGraph, JourneyNode, NodeType  # noqa: E402

router = APIRouter(prefix="/api/v1/constraints", tags=["constraints"])


ACTIVE_RULES_CATALOG: List[ConstraintRuleItem] = [
    ConstraintRuleItem(
        rule_id="RULE_TEMPORAL_MCT",
        category="TEMPORAL_MCT",
        constraint_type="HARD",
        title="Minimum Connect Time (MCT)",
        description="Enforces minimum transfer buffers between connecting flights and transit legs.",
        threshold_info="Domestic >= 45m, International >= 90m",
    ),
    ConstraintRuleItem(
        rule_id="RULE_SPATIAL_CONTINUITY",
        category="SPATIAL_CONTINUITY",
        constraint_type="HARD",
        title="Spatial Continuity & Anti-Teleportation",
        description="Prohibits overlapping events across disjoint geographic locations.",
        threshold_info="Departure time must be strictly after prior leg arrival",
    ),
    ConstraintRuleItem(
        rule_id="RULE_REGULATORY_PASSPORT",
        category="REGULATORY_PASSPORT",
        constraint_type="HARD",
        title="Passport 6-Month Validity Rule",
        description="Requires traveler passport expiry to be at least 180 days after trip return date.",
        threshold_info=">= 180 days remaining from return date",
    ),
    ConstraintRuleItem(
        rule_id="RULE_REGULATORY_SCHENGEN",
        category="REGULATORY_VISA_SCHENGEN",
        constraint_type="HARD",
        title="Schengen 90/180-Day Maximum Stay Rule",
        description="Caps cumulative short-stay tourist visits in the Schengen Area at 90 days per 180-day window.",
        threshold_info="Max 90 days in rolling 180-day window",
    ),
    ConstraintRuleItem(
        rule_id="RULE_TEMPORAL_PACING",
        category="TEMPORAL_PACING",
        constraint_type="SOFT",
        title="Transit Layover Pacing",
        description="Advises when layovers meet legal MCT but leave minimal comfort buffer for traveler.",
        threshold_info="Warns if buffer < MCT + 30m",
    ),
]


@router.get("/rules", response_model=ConstraintRulesResponse)
def list_constraint_rules(
    agency_id: str = Depends(get_current_agency_id),
) -> ConstraintRulesResponse:
    """List all active deterministic constraint satisfaction rules and threshold criteria."""
    return ConstraintRulesResponse(
        active_rules=ACTIVE_RULES_CATALOG,
        total_rules=len(ACTIVE_RULES_CATALOG),
    )


@router.post("/evaluate/{trip_id}", response_model=ConstraintEvaluationResponse)
def evaluate_trip_constraints(
    trip_id: str,
    agency_id: str = Depends(get_current_agency_id),
) -> ConstraintEvaluationResponse:
    """
    Evaluate spatial-temporal and regulatory constraint feasibility for a trip.

    Constructs a JourneyDependencyGraph from the trip packet and itinerary options,
    runs the deterministic ConstraintEngine, and returns hard/soft violations and relaxation hierarchy.
    """
    trip = TripStore.get_trip_for_agency(trip_id, agency_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    packet = trip.get("packet") or {}
    travelers = (trip.get("booking_data") or {}).get("travelers") or []

    # Construct JourneyDependencyGraph from trip legs or default flight nodes
    graph = JourneyDependencyGraph(trip_id)

    legs = trip.get("itinerary_legs") or []
    if not legs:
        # Fallback to packet dates or dummy default nodes if not yet populated
        start_date_str = packet.get("start_date") or "2026-11-01T10:00:00"
        end_date_str = packet.get("end_date") or "2026-11-08T18:00:00"
        dest = packet.get("destination") or "Destination"
        origin = packet.get("origin") or "Origin"

        try:
            t0 = datetime.fromisoformat(start_date_str.replace("Z", "+00:00"))
        except Exception:
            t0 = datetime(2026, 11, 1, 10, 0)
        try:
            t1 = datetime.fromisoformat(end_date_str.replace("Z", "+00:00"))
        except Exception:
            t1 = datetime(2026, 11, 8, 18, 0)

        flight_node = JourneyNode(
            node_id=f"{trip_id}_leg_outbound",
            node_type=NodeType.FLIGHT,
            title=f"Outbound Flight: {origin} -> {dest}",
            start_time=t0,
            end_time=t1,
            location=dest,
        )
        graph.add_node(flight_node)
    else:
        for idx, leg in enumerate(legs):
            node_type = NodeType.FLIGHT if leg.get("type") == "flight" else NodeType.ACTIVITY
            st = datetime.fromisoformat(leg.get("start_time", "2026-11-01T10:00:00"))
            et = datetime.fromisoformat(leg.get("end_time", "2026-11-01T14:00:00"))
            node = JourneyNode(
                node_id=leg.get("id") or f"{trip_id}_node_{idx}",
                node_type=node_type,
                title=leg.get("title") or f"Leg {idx + 1}",
                start_time=st,
                end_time=et,
                location=leg.get("location") or "Destination",
            )
            graph.add_node(node)

    report = ConstraintEngine.evaluate_itinerary_graph(
        graph=graph,
        travelers=travelers,
        budget_cents=packet.get("budget_cents"),
    )

    return ConstraintEvaluationResponse(
        trip_id=trip_id,
        is_feasible=report.is_feasible,
        hard_violations=[
            ConstraintViolationModel(
                constraint_id=v.constraint_id,
                name=v.name,
                category=v.category.value,
                constraint_type=v.constraint_type.value,
                severity=v.severity,
                affected_elements=v.affected_elements,
                description=v.description,
                relaxation_option=v.relaxation_option,
                metadata=v.metadata,
            )
            for v in report.hard_violations
        ],
        soft_violations=[
            ConstraintViolationModel(
                constraint_id=v.constraint_id,
                name=v.name,
                category=v.category.value,
                constraint_type=v.constraint_type.value,
                severity=v.severity,
                affected_elements=v.affected_elements,
                description=v.description,
                relaxation_option=v.relaxation_option,
                metadata=v.metadata,
            )
            for v in report.soft_violations
        ],
        relaxation_hierarchy=report.relaxation_hierarchy,
        evaluated_at=report.evaluated_at or datetime.now(timezone.utc).isoformat(),
    )


class SchengenRollingRequest(BaseModel):
    historical_stays: List[Tuple[date, date]] = Field(default_factory=list, description="Past Schengen trips (start_date, end_date)")
    planned_stay: Tuple[date, date] = Field(..., description="Upcoming Schengen trip (start_date, end_date)")


class TerminalMCTRequest(BaseModel):
    airport_code: str = Field("LHR", description="3-letter IATA airport code")
    from_terminal: Optional[str] = Field("T2", description="Inbound arrival terminal")
    to_terminal: Optional[str] = Field("T5", description="Outbound departure terminal")
    is_international: bool = True


class PassportValidityRequest(BaseModel):
    passport_expiry: date
    trip_return_date: date
    destination_country: str = "GLOBAL"
    blank_pages: int = 2


SchengenRollingRequest.model_rebuild()
TerminalMCTRequest.model_rebuild()
PassportValidityRequest.model_rebuild()


@router.post("/schengen/rolling-eval")
def evaluate_schengen_rolling_window(payload: SchengenRollingRequest):
    """Calculates day-by-day rolling 90/180 Schengen stay accumulation."""
    return ConstraintEngine.calculate_schengen_rolling_90_180(
        historical_stays=payload.historical_stays,
        planned_stay=payload.planned_stay,
    )


@router.post("/terminal-mct/lookup")
def lookup_terminal_mct(payload: TerminalMCTRequest):
    """Looks up exact terminal-to-terminal minimum connect time in minutes."""
    mct = ConstraintEngine.get_terminal_mct(
        airport_code=payload.airport_code,
        from_terminal=payload.from_terminal,
        to_terminal=payload.to_terminal,
        is_international=payload.is_international,
    )
    return {
        "airport_code": payload.airport_code,
        "from_terminal": payload.from_terminal,
        "to_terminal": payload.to_terminal,
        "min_connect_time_minutes": mct,
        "is_terminal_change": payload.from_terminal != payload.to_terminal,
    }


@router.post("/passport-validity/check")
def check_passport_validity(payload: PassportValidityRequest):
    """Validates passport 6-month validity and blank visa pages against return date."""
    days_remaining = (payload.passport_expiry - payload.trip_return_date).days
    is_valid = days_remaining >= 180 and payload.blank_pages >= 2
    return {
        "is_valid": is_valid,
        "days_remaining_post_return": days_remaining,
        "required_days": 180,
        "blank_pages_available": payload.blank_pages,
        "required_blank_pages": 2,
        "status": "VALID" if is_valid else "NON_COMPLIANT",
        "action_required": (
            "Passport meets all international entry rules."
            if is_valid
            else "Passport renewal or emergency booklet required prior to international departure."
        ),
    }
