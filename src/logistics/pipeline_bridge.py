"""
src/logistics/pipeline_bridge.py — Route Geometry & Connection Risk Pipeline Integration.

Integrates route geometry analysis (backtracking detection, 2-opt optimization,
open-jaw surface segment injection) and flight connection risk evaluation directly
into the intake and proposal compilation flow.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from src.logistics.connection_risk import ConnectionRiskScorer
from src.logistics.route_geometry import (
    GeodesicPathOptimizer,
    detect_backtracking,
    detect_open_jaw_surface_segments,
)


@dataclass(slots=True)
class RouteLogisticsAssessment:
    """Comprehensive route geometry and connection risk assessment for a trip."""
    has_backtracking: bool = False
    excess_distance_km: float = 0.0
    current_distance_km: float = 0.0
    optimized_distance_km: float = 0.0
    distance_savings_km: float = 0.0
    savings_percent: float = 0.0
    suggested_waypoint_order: List[str] = field(default_factory=list)
    has_open_jaw: bool = False
    open_jaw_surface_segments_count: int = 0
    total_surface_distance_km: float = 0.0
    legs_with_surface_segments: List[Dict[str, Any]] = field(default_factory=list)
    connection_evaluations: List[Dict[str, Any]] = field(default_factory=list)
    has_illegal_mct: bool = False
    has_high_misconnect_risk: bool = False
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class RouteAssessmentBridge:
    """
    Bridge connecting trip intake facts and proposal flight options to route geometry and MCT scorers.
    """

    @classmethod
    def evaluate_trip_route(
        cls,
        destinations: List[str],
        origin: Optional[str] = None,
        flights: Optional[List[Dict[str, Any]]] = None,
    ) -> RouteLogisticsAssessment:
        """
        Evaluates a complete trip itinerary for route efficiency, surface segments, and layover risks.
        """
        warnings: List[str] = []

        # 1. Construct stop list
        stops: List[Dict[str, Any]] = []
        if origin:
            stops.append({"airport_code": origin.strip().upper(), "city": origin.strip()})

        for d in destinations:
            stops.append({"airport_code": d.strip().upper(), "city": d.strip()})

        # Evaluate backtracking and 2-opt
        has_backtracking = False
        excess_dist = 0.0
        suggested_order: List[str] = []
        current_dist = 0.0
        opt_dist = 0.0
        savings_dist = 0.0
        savings_pct = 0.0

        if len(stops) >= 3:
            has_backtracking, excess_dist, suggested_order = detect_backtracking(stops)
            current_dist = GeodesicPathOptimizer.calculate_total_distance(stops, unit="km")
            opt_route = GeodesicPathOptimizer.optimize_waypoint_order(stops, fix_start=True, unit="km")
            opt_dist = GeodesicPathOptimizer.calculate_total_distance(opt_route, unit="km")
            savings_dist = max(0.0, current_dist - opt_dist)
            savings_pct = round((savings_dist / current_dist * 100.0), 1) if current_dist > 0 else 0.0

            if has_backtracking:
                warnings.append(
                    f"Suboptimal route sequence detected. Itinerary has +{round(excess_dist)} km excess flight distance. Suggested order: {' ➔ '.join(suggested_order)}."
                )

        # 2. Evaluate Open-Jaw surface segments if flight legs provided
        enriched_legs: List[Dict[str, Any]] = []
        has_open_jaw = False
        oj_count = 0
        surface_dist = 0.0

        if flights and len(flights) >= 2:
            enriched_legs = detect_open_jaw_surface_segments(flights)
            surface_segs = [leg for leg in enriched_legs if leg.get("segment_type") == "SURFACE"]
            has_open_jaw = len(surface_segs) > 0
            oj_count = len(surface_segs)
            surface_dist = sum(float(s.get("estimated_surface_distance_km") or 0.0) for s in surface_segs)

            if has_open_jaw:
                warnings.append(
                    f"Open-jaw surface connection detected ({oj_count} surface segments totaling {round(surface_dist)} km). Marked // in PNR."
                )

        # 3. Evaluate Connection Risks for multi-leg flights
        connection_evals: List[Dict[str, Any]] = []
        has_illegal = False
        has_high_risk = False

        if flights and len(flights) >= 2:
            for i in range(len(flights) - 1):
                leg1 = flights[i]
                leg2 = flights[i + 1]

                # Check if it is a connecting layover at same airport
                dest1 = str(leg1.get("destination") or "").strip().upper()
                orig2 = str(leg2.get("origin") or "").strip().upper()

                if dest1 and orig2 and dest1 == orig2:
                    layover_mins = int(leg2.get("layover_minutes") or leg1.get("layover_to_next_mins") or 90)
                    in_term = str(leg1.get("arrival_terminal") or leg1.get("inbound_terminal") or "T1")
                    out_term = str(leg2.get("departure_terminal") or leg2.get("outbound_terminal") or "T1")
                    is_self_transfer = bool(leg2.get("is_self_transfer") or leg1.get("is_self_transfer"))
                    requires_imm = bool(leg2.get("requires_immigration") or leg1.get("requires_immigration"))

                    eval_res = ConnectionRiskScorer.evaluate_connection(
                        connection_airport=dest1,
                        inbound_flight=str(leg1.get("flight_number") or "INBOUND"),
                        outbound_flight=str(leg2.get("flight_number") or "OUTBOUND"),
                        layover_minutes=layover_mins,
                        inbound_terminal=in_term,
                        outbound_terminal=out_term,
                        is_self_transfer=is_self_transfer,
                        requires_immigration_reclear=requires_imm,
                    )

                    res_dict = {
                        "connection_airport": eval_res.connection_airport,
                        "layover_minutes": eval_res.layover_minutes,
                        "required_mct_minutes": eval_res.required_mct_minutes,
                        "risk_level": eval_res.risk_level.value,
                        "recommendation": eval_res.recommendation,
                        "warnings": eval_res.warnings,
                    }
                    connection_evals.append(res_dict)

                    if eval_res.risk_level.value == "ILLEGAL_MCT_VIOLATION":
                        has_illegal = True
                        warnings.append(f"🚨 Illegal connection at {dest1}: {layover_mins}m is below MCT ({eval_res.required_mct_minutes}m).")
                    elif eval_res.risk_level.value == "HIGH_MISCONNECT_RISK":
                        has_high_risk = True
                        warnings.append(f"⚠️ High misconnect risk at {dest1}: {layover_mins}m layover vs {eval_res.required_mct_minutes}m required.")

        return RouteLogisticsAssessment(
            has_backtracking=has_backtracking,
            excess_distance_km=round(excess_dist, 2),
            current_distance_km=round(current_dist, 2),
            optimized_distance_km=round(opt_dist, 2),
            distance_savings_km=round(savings_dist, 2),
            savings_percent=savings_pct,
            suggested_waypoint_order=suggested_order,
            has_open_jaw=has_open_jaw,
            open_jaw_surface_segments_count=oj_count,
            total_surface_distance_km=round(surface_dist, 2),
            legs_with_surface_segments=enriched_legs,
            connection_evaluations=connection_evals,
            has_illegal_mct=has_illegal,
            has_high_misconnect_risk=has_high_risk,
            warnings=warnings,
        )
