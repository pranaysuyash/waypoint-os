"""
src/decision/constraint_engine.py — Spatial-Temporal & Regulatory Constraint Satisfaction Engine.

Authoritative implementation of PER-0711 (Constraint-Satisfaction Designer) & PER-0706.
Guarantees that physical, temporal, regulatory, and capacity feasibility strictly precedes
optimization and client presentation.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from src.schemas.constraints import (
    ConstraintCategory,
    ConstraintEvaluationReport,
    ConstraintType,
    ConstraintViolation,
)
from src.schemas.journey_graph import JourneyDependencyGraph, NodeType

# Recognised Schengen area countries and major gateway destinations
SCHENGEN_DESTINATIONS = {
    "france", "paris", "nice", "lyon",
    "italy", "rome", "florence", "venice", "milan", "amalfi",
    "spain", "barcelona", "madrid", "seville", "mallorca",
    "germany", "berlin", "munich", "frankfurt",
    "greece", "athens", "santorini", "mykonos", "crete",
    "switzerland", "zurich", "geneva", "interlaken",
    "austria", "vienna", "salzburg",
    "portugal", "lisbon", "porto",
    "netherlands", "amsterdam",
    "belgium", "brussels", "bruges",
    "norway", "oslo", "sweden", "stockholm", "denmark", "copenhagen",
    "finland", "helsinki", "iceland", "reykjavik",
    "czech republic", "prague", "hungary", "budapest",
    "poland", "warsaw", "krakow",
}


class ConstraintEngine:
    """Deterministic Constraint Satisfaction Engine for Travel Itineraries."""

    @classmethod
    def evaluate_itinerary_graph(
        cls,
        graph: JourneyDependencyGraph,
        travelers: Optional[List[Dict[str, Any]]] = None,
        budget_cents: Optional[int] = None,
        hard_budget_ceiling: bool = False,
    ) -> ConstraintEvaluationReport:
        """Evaluate all hard and soft constraints across a JourneyDependencyGraph."""
        trip_id = graph.trip_id
        hard_violations: List[ConstraintViolation] = []
        soft_violations: List[ConstraintViolation] = []
        relaxation_hierarchy: List[Dict[str, Any]] = []

        now_iso = datetime.now(timezone.utc).isoformat()

        # Sort nodes chronologically
        sorted_nodes = sorted(graph.nodes.values(), key=lambda n: n.start_time)

        # 1. Temporal MCT & Connection Feasibility Checks
        for i in range(len(sorted_nodes) - 1):
            curr_node = sorted_nodes[i]
            next_node = sorted_nodes[i + 1]

            # If adjacent nodes are connecting flights or flight -> transfer
            if curr_node.node_type == NodeType.FLIGHT and next_node.node_type in (NodeType.FLIGHT, NodeType.TRANSFER):
                buffer_minutes = int((next_node.start_time - curr_node.end_time).total_seconds() / 60.0)
                is_international = "international" in curr_node.title.lower() or "international" in next_node.title.lower()
                min_mct = 90 if is_international else 45

                if buffer_minutes < 0:
                    # Impossible overlap (teleportation)
                    hard_violations.append(
                        ConstraintViolation(
                            constraint_id=f"SPATIAL_OVERLAP_{curr_node.node_id}_{next_node.node_id}",
                            name="Impossible Temporal/Spatial Overlap",
                            category=ConstraintCategory.SPATIAL_CONTINUITY,
                            constraint_type=ConstraintType.HARD,
                            severity="blocking",
                            affected_elements=[curr_node.node_id, next_node.node_id],
                            description=(
                                f"Departure of {next_node.title} ({next_node.start_time.strftime('%H:%M')}) "
                                f"occurs before arrival of {curr_node.title} ({curr_node.end_time.strftime('%H:%M')})."
                            ),
                            relaxation_option=f"Shift {next_node.title} to start at least {min_mct}m after {curr_node.end_time.strftime('%H:%M')}.",
                        )
                    )
                elif buffer_minutes < min_mct:
                    # MCT deficit
                    deficit = min_mct - buffer_minutes
                    hard_violations.append(
                        ConstraintViolation(
                            constraint_id=f"MCT_DEFICIT_{curr_node.node_id}_{next_node.node_id}",
                            name="Minimum Connect Time (MCT) Deficit",
                            category=ConstraintCategory.TEMPORAL_MCT,
                            constraint_type=ConstraintType.HARD,
                            severity="blocking",
                            affected_elements=[curr_node.node_id, next_node.node_id],
                            description=(
                                f"Layover between {curr_node.title} and {next_node.title} is {buffer_minutes}m, "
                                f"which is {deficit}m below the required {min_mct}m minimum connect time."
                            ),
                            relaxation_option=f"Re-book connection on next departure at least {deficit}m later.",
                        )
                    )
                elif buffer_minutes < min_mct + 30:
                    # Soft warning for tight layover
                    soft_violations.append(
                        ConstraintViolation(
                            constraint_id=f"TIGHT_LAYOVER_{curr_node.node_id}",
                            name="Tight Connection Layover",
                            category=ConstraintCategory.TEMPORAL_PACING,
                            constraint_type=ConstraintType.SOFT,
                            severity="warning",
                            affected_elements=[curr_node.node_id, next_node.node_id],
                            description=f"Layover is {buffer_minutes}m. Meets legal MCT ({min_mct}m) but leaves minimal buffer for gate transfers.",
                            relaxation_option="Consider booking flight with >= 2hr buffer for comfortable transit.",
                        )
                    )

        # 2. Regulatory Passport Validity & Schengen Rules
        trip_start: Optional[datetime] = sorted_nodes[0].start_time if sorted_nodes else None
        trip_end: Optional[datetime] = sorted_nodes[-1].end_time if sorted_nodes else None

        if travelers and trip_end:
            for idx, traveler in enumerate(travelers):
                trav_name = traveler.get("name") or f"Traveler #{idx + 1}"
                passport_exp = traveler.get("passport_expiry")
                if passport_exp:
                    exp_date = (
                        datetime.fromisoformat(passport_exp).date()
                        if isinstance(passport_exp, str)
                        else passport_exp
                    )
                    days_remaining = (exp_date - trip_end.date()).days
                    if days_remaining < 180:
                        hard_violations.append(
                            ConstraintViolation(
                                constraint_id=f"PASSPORT_EXPIRY_{idx}",
                                name="Passport 6-Month Validity Rule Violation",
                                category=ConstraintCategory.REGULATORY_PASSPORT,
                                constraint_type=ConstraintType.HARD,
                                severity="blocking",
                                affected_elements=[trav_name],
                                description=(
                                    f"{trav_name}'s passport expires on {exp_date} ({days_remaining} days after return date {trip_end.date()}). "
                                    "International immigration requires >= 6 months (180 days) validity from return date."
                                ),
                                relaxation_option=f"Traveler must renew passport prior to departure or advance trip dates before {exp_date}.",
                            )
                        )

        # 3. Schengen 90/180-Day Rule
        if trip_start and trip_end:
            dest_locations = [n.location.lower() for n in sorted_nodes if n.location]
            is_schengen = any(
                any(schengen in loc for schengen in SCHENGEN_DESTINATIONS)
                for loc in dest_locations
            )
            if is_schengen:
                trip_duration_days = (trip_end.date() - trip_start.date()).days + 1
                if trip_duration_days > 90:
                    hard_violations.append(
                        ConstraintViolation(
                            constraint_id="SCHENGEN_90_DAY_LIMIT",
                            name="Schengen 90/180-Day Maximum Stay Violation",
                            category=ConstraintCategory.REGULATORY_VISA_SCHENGEN,
                            constraint_type=ConstraintType.HARD,
                            severity="blocking",
                            affected_elements=["itinerary_dates"],
                            description=(
                                f"Total stay in Schengen Area is {trip_duration_days} days. Short-stay tourist entry "
                                "strictly caps visits at 90 days within any rolling 180-day window."
                            ),
                            relaxation_option=f"Shorten Schengen itinerary by {trip_duration_days - 90} days or apply for National Long-Stay Visa (Type D).",
                        )
                    )

        # 4. Passport Blank Visa Pages & Vaccination Checks
        if travelers:
            for t in travelers:
                t_name = t.get("name", "Traveler")
                blank_pages = t.get("blank_visa_pages")
                if blank_pages is not None and blank_pages < 2:
                    hard_violations.append(
                        ConstraintViolation(
                            constraint_id="PASSPORT_BLANK_PAGES_DEFICIT",
                            name=f"Insufficient Blank Visa Pages for {t_name}",
                            category=ConstraintCategory.REGULATORY_PASSPORT_VALIDITY,
                            constraint_type=ConstraintType.HARD,
                            severity="blocking",
                            affected_elements=[f"traveler:{t_name}"],
                            description=f"Passport has only {blank_pages} blank visa pages. International transit requires >= 2 blank pages.",
                            relaxation_option="Traveler must obtain a renewed passport booklet with blank pages prior to travel.",
                        )
                    )

                # Driver Age Check for Car Rentals
                has_car_rental = any(n.node_type == NodeType.TRANSFER and "car" in n.title.lower() for n in sorted_nodes)
                driver_age = t.get("age")
                if has_car_rental and driver_age is not None and driver_age < 21:
                    hard_violations.append(
                        ConstraintViolation(
                            constraint_id="DRIVER_UNDERAGE_VIOLATION",
                            name=f"Underage Driver ({driver_age} yrs) for Car Rental",
                            category=ConstraintCategory.COMMERCIAL_SUPPLIER_POLICY,
                            constraint_type=ConstraintType.HARD,
                            severity="blocking",
                            affected_elements=[f"traveler:{t_name}"],
                            description=f"Driver age {driver_age} violates minimum supplier rental requirement of 21 years.",
                            relaxation_option="Designate an alternative traveler >= 21 years old as primary driver or switch to private chauffeur transfers.",
                        )
                    )

        # 5. Synthesize Relaxation Hierarchy
        for hv in hard_violations:
            if hv.relaxation_option:
                relaxation_hierarchy.append({
                    "priority": 1,
                    "constraint_id": hv.constraint_id,
                    "violation": hv.name,
                    "action": hv.relaxation_option,
                })
        for sv in soft_violations:
            if sv.relaxation_option:
                relaxation_hierarchy.append({
                    "priority": 2,
                    "constraint_id": sv.constraint_id,
                    "violation": sv.name,
                    "action": sv.relaxation_option,
                })

        is_feasible = len(hard_violations) == 0

        return ConstraintEvaluationReport(
            trip_id=trip_id,
            is_feasible=is_feasible,
            hard_violations=hard_violations,
            soft_violations=soft_violations,
            relaxation_hierarchy=relaxation_hierarchy,
            evaluated_at=now_iso,
        )
