"""
suitability.models — Typed contracts for activity suitability scoring.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional


@dataclass
class ParticipantRef:
    """Reference to a traveler unit."""

    kind: Literal["group", "subgroup", "cohort", "person"]
    ref_id: str
    label: str
    age: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ActivityDefinition:
    """Normalized activity contract used by all scorers."""

    activity_id: str
    canonical_name: str
    source: Literal["static", "agency", "external_api"]
    source_ref: Optional[str] = None
    destination_keys: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    intensity: Literal["light", "moderate", "high", "extreme"] = "moderate"
    duration_hours: Optional[float] = None
    cost_per_person: Optional[int] = None
    cost_band: Optional[Literal["low", "mid", "high", "premium"]] = None
    accessibility_tags: List[str] = field(default_factory=list)
    min_age: Optional[int] = None
    max_age: Optional[int] = None
    max_weight_kg: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StructuredRisk:
    """Typed risk output used by tour-context suitability checks."""

    flag: str
    severity: Literal["low", "medium", "high", "critical"]
    category: Literal[
        "budget",
        "activity",
        "pacing",
        "logistics",
        "documents",
        "composition",
        "routing",
        "commercial",
        "seasonality",
    ]
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    affected_travelers: List[str] = field(default_factory=list)
    mitigation_suggestions: List[str] = field(default_factory=list)
    maturity: Literal["stub", "heuristic", "verified", "ml_assisted"] = "heuristic"
    rule_id: Optional[str] = None


@dataclass
class SuitabilityContext:
    """Scoring context including day/trip sequence awareness."""

    destination_keys: List[str]
    trip_duration_nights: Optional[int] = None
    pace_preference: Optional[Literal["relaxed", "balanced", "packed"]] = None
    day_activities: List[ActivityDefinition] = field(default_factory=list)
    trip_activities: List[ActivityDefinition] = field(default_factory=list)
    day_index: Optional[int] = None
    season_month: Optional[int] = None
    destination_climate: Optional[
        Literal[
            "tropical_humid",
            "arid_hot",
            "temperate",
            "cold",
            "alpine",
            "coastal_humid",
        ]
    ] = None
    budget_preference: Optional[Literal["low", "mid", "high", "premium"]] = None


@dataclass
class ActivitySuitability:
    """Assessment output for one activity and one participant."""

    activity_id: str
    participant: ParticipantRef
    compatible: bool
    score: float
    confidence: float
    tier: Literal[
        "exclude",
        "discourage",
        "neutral",
        "recommend",
        "strong_recommend",
    ] = "neutral"
    hard_exclusion_reasons: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    score_components: Dict[str, float] = field(default_factory=dict)
    missing_signals: List[str] = field(default_factory=list)
    generated_risks: List[StructuredRisk] = field(default_factory=list)
    scorer_id: str = "heuristic_v1"
    scorer_version: str = "1"
    source: Literal["rule", "llm", "cache", "default"] = "rule"

