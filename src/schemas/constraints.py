"""
src/schemas/constraints.py — Formal Constraint Satisfaction Models for Waypoint OS.

Grounding per PER-0711 (Constraint-Satisfaction Designer) & PER-0706 (Agent Planning Systems Engineer).
Distinguishes between HARD (non-negotiable physical/regulatory) and SOFT (elastic/preference) constraints.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ConstraintType(str, Enum):
    """Classification of constraint enforcement rigidity."""
    HARD = "HARD"  # Non-negotiable: violating makes the itinerary physically or legally impossible
    SOFT = "SOFT"  # Negotiable: preference or advisory boundary that can be relaxed


class ConstraintCategory(str, Enum):
    """Categorical domain of the constraint."""
    TEMPORAL_MCT = "TEMPORAL_MCT"                        # Minimum Connect Time between connecting flights/transfers
    SPATIAL_CONTINUITY = "SPATIAL_CONTINUITY"            # Travel between locations must be physically possible
    REGULATORY_PASSPORT = "REGULATORY_PASSPORT"          # Passport validity >= 6 months from return date
    REGULATORY_PASSPORT_VALIDITY = "REGULATORY_PASSPORT_VALIDITY"  # Blank pages & format validity
    REGULATORY_VISA_SCHENGEN = "REGULATORY_VISA_SCHENGEN"# Schengen 90/180-day rolling stay limits
    # DORMANT (VA-05, 2026-09-09 visa audit): no producer currently emits
    # this category — constraint_engine.py carries tier handling for it, but
    # no rule or extractor constructs a vaccination constraint. Kept (not
    # deleted) as the schema home for the future health-declaration lane;
    # see findings-register item VA-05 / exploration VE-02 before wiring a
    # producer.
    REGULATORY_HEALTH_VACCINATION = "REGULATORY_HEALTH_VACCINATION"  # Mandatory vaccinations (Yellow Fever / ICVP)
    COMMERCIAL_SUPPLIER_POLICY = "COMMERCIAL_SUPPLIER_POLICY"  # Age limits, car rental rules
    FINANCIAL_BOUND = "FINANCIAL_BOUND"                  # Hard budget ceilings vs soft targets
    CAPACITY_ROOMING = "CAPACITY_ROOMING"                # Hotel room occupancy / passenger capacity limits
    TEMPORAL_PACING = "TEMPORAL_PACING"                  # Rest buffers between high-intensity activities


@dataclass(slots=True)
class ConstraintViolation:
    """Individual constraint violation detected during itinerary or packet evaluation."""
    constraint_id: str
    name: str
    category: ConstraintCategory
    constraint_type: ConstraintType
    severity: str  # "blocking" (for HARD) | "warning" | "advisory" (for SOFT)
    affected_elements: List[str]  # IDs of legs, nodes, travelers, or fields
    description: str
    relaxation_option: Optional[str] = None  # Actionable proposal to resolve the conflict
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "constraint_id": self.constraint_id,
            "name": self.name,
            "category": self.category.value,
            "constraint_type": self.constraint_type.value,
            "severity": self.severity,
            "affected_elements": self.affected_elements,
            "description": self.description,
            "relaxation_option": self.relaxation_option,
            "metadata": self.metadata,
        }


@dataclass(slots=True)
class ConstraintEvaluationReport:
    """Complete diagnostic report of constraint evaluation across an itinerary or trip packet."""
    trip_id: str
    is_feasible: bool  # True iff len(hard_violations) == 0
    hard_violations: List[ConstraintViolation] = field(default_factory=list)
    soft_violations: List[ConstraintViolation] = field(default_factory=list)
    relaxation_hierarchy: List[Dict[str, Any]] = field(default_factory=list)
    evaluated_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trip_id": self.trip_id,
            "is_feasible": self.is_feasible,
            "hard_violations": [v.to_dict() for v in self.hard_violations],
            "soft_violations": [v.to_dict() for v in self.soft_violations],
            "relaxation_hierarchy": self.relaxation_hierarchy,
            "evaluated_at": self.evaluated_at,
        }
