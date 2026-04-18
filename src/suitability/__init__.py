"""
suitability — Activity suitability scoring module.

Tier 1: Deterministic tag-based scoring (scoring.py)
Tier 2: Day/trip coherence context rules (context_rules.py)
Confidence: Field-level confidence and missing-signal diagnostics (confidence.py)
Catalog: Static activity definitions (catalog.py)

Usage:
    from src.suitability import evaluate_activity, apply_tour_context_rules
    from src.suitability.models import ActivityDefinition, ParticipantRef, SuitabilityContext
    from src.suitability.catalog import get_activity, get_activities_by_tag
"""

from .models import (
    ActivityDefinition,
    ActivitySuitability,
    ParticipantRef,
    StructuredRisk,
    SuitabilityContext,
)
from .scoring import evaluate_activity
from .context_rules import apply_tour_context_rules
from .confidence import compute_confidence, collect_missing_signals
from .catalog import (
    get_activity,
    get_activities_by_tag,
    get_activities_by_intensity,
    get_activities_for_participant_age,
    STATIC_ACTIVITIES,
)
from .integration import (
    extract_participants_from_packet,
    generate_suitability_risks,
)

__all__ = [
    # Models
    "ActivityDefinition",
    "ActivitySuitability",
    "ParticipantRef",
    "StructuredRisk",
    "SuitabilityContext",
    # Scoring functions
    "evaluate_activity",
    "apply_tour_context_rules",
    "compute_confidence",
    "collect_missing_signals",
    # Catalog functions
    "get_activity",
    "get_activities_by_tag",
    "get_activities_by_intensity",
    "get_activities_for_participant_age",
    "STATIC_ACTIVITIES",
    # Integration functions
    "extract_participants_from_packet",
    "generate_suitability_risks",
]
