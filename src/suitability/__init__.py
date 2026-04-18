"""
suitability — Activity suitability scoring module.

Tier 1: Deterministic tag-based scoring (scoring.py)
Tier 2: Day/trip coherence context rules (context_rules.py)
Confidence: Field-level confidence and missing-signal diagnostics (confidence.py)

Usage:
    from src.suitability import evaluate_activity, apply_tour_context_rules
    from src.suitability.models import ActivityDefinition, ParticipantRef, SuitabilityContext
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
]
