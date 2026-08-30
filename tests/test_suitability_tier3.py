"""
Unit tests for Tier 3 LLM Contextual Suitability Scorer.
Tests triggering conditions, tour context caching, sequence fatigue, and offline fallback.
"""

from typing import Any
from src.suitability.models import (
    ActivityDefinition,
    ActivitySuitability,
    ParticipantRef,
    SuitabilityContext,
)
from src.suitability.llm_scorer import (
    LLMContextualScorer,
    compute_suitability_cache_key,
)


class MockCacheStorage:
    def __init__(self):
        self.store = {}

    def get(self, key: str, decision_type: str = "default"):
        return self.store.get(f"{decision_type}:{key}")

    def set(self, key: str, decision_type: str, decision: Any):
        self.store[f"{decision_type}:{key}"] = decision


class MockLLMClient:
    def __init__(self, mock_response: dict):
        self.mock_response = mock_response

    def generate(self, prompt: str):
        import json
        return json.dumps(self.mock_response)


def test_cache_key_incorporates_context():
    """Verify that different sequence contexts produce distinct cache keys."""
    activity = ActivityDefinition(activity_id="rafting", canonical_name="White Water Rafting", source="static")
    participant = ParticipantRef(kind="person", ref_id="p1", label="adult", age=30)
    
    context1 = SuitabilityContext(destination_keys=["costa_rica"], season_month=12)
    context2 = SuitabilityContext(
        destination_keys=["costa_rica"],
        season_month=12,
        day_activities=[ActivityDefinition(activity_id="hiking", canonical_name="Volcano Hike", source="static")],
    )

    key1 = compute_suitability_cache_key(activity, participant, context1)
    key2 = compute_suitability_cache_key(activity, participant, context2)

    assert key1 != key2
    assert key1.startswith("suitability_t3_rafting_adult_")


def test_tier3_trigger_conditions():
    """Verify trigger conditions for Tier 3 escalation."""
    scorer = LLMContextualScorer()
    
    activity = ActivityDefinition(activity_id="zipline", canonical_name="Zipline", source="static", intensity="high")
    participant = ParticipantRef(kind="person", ref_id="p1", label="elderly", age=70)
    
    # Low density context -> no trigger if tier1 is confident and clear
    context_low = SuitabilityContext(destination_keys=["bali"])
    tier1_res = ActivitySuitability(
        activity_id="zipline",
        participant=participant,
        compatible=True,
        score=0.75,
        confidence=0.9,
        tier="recommend",
    )
    assert not scorer.should_trigger_tier3(tier1_res, activity, participant, context_low)

    # High density context (3+ activities) with high intensity -> triggers Tier 3
    context_high = SuitabilityContext(
        destination_keys=["bali"],
        day_activities=[
            ActivityDefinition(activity_id="a1", canonical_name="A1", source="static"),
            ActivityDefinition(activity_id="a2", canonical_name="A2", source="static"),
            ActivityDefinition(activity_id="a3", canonical_name="A3", source="static"),
        ],
    )
    assert scorer.should_trigger_tier3(tier1_res, activity, participant, context_high)


def test_tier3_contextual_fatigue_evaluation():
    """Verify that contextual cumulative fatigue results in adjusted recommendations."""
    storage = MockCacheStorage()
    scorer = LLMContextualScorer(cache_storage=storage)

    activity = ActivityDefinition(
        activity_id="temple_walk",
        canonical_name="Temple Stair Walk",
        source="static",
        intensity="moderate",
        duration_hours=3.0,
    )
    participant = ParticipantRef(kind="person", ref_id="e1", label="elderly", age=75)

    # Day context with 8 hours of prior/other activities
    context_fatigued = SuitabilityContext(
        destination_keys=["kyoto"],
        day_activities=[
            ActivityDefinition(activity_id="hike1", canonical_name="Morning Hike", source="static", duration_hours=4.0),
            ActivityDefinition(activity_id="hike2", canonical_name="Garden Tour", source="static", duration_hours=4.0),
            ActivityDefinition(activity_id="temple_walk", canonical_name="Temple Stair Walk", source="static", duration_hours=3.0),
        ],
    )

    result = scorer.score(activity, participant, context_fatigued)

    assert result.source == "llm"
    assert any("fatigue" in w.lower() for w in result.warnings)
    assert result.tier == "discourage"


def test_tier3_cache_hit_and_reuse():
    """Verify that cached verdicts are retrieved without re-evaluating."""
    storage = MockCacheStorage()
    scorer = LLMContextualScorer(cache_storage=storage)

    activity = ActivityDefinition(
        activity_id="hot_springs",
        canonical_name="Hot Springs",
        source="static",
        intensity="light",
    )
    participant = ParticipantRef(kind="person", ref_id="p1", label="adult", metadata={"medical": "hypertension"})
    context = SuitabilityContext(destination_keys=["japan"])

    # First evaluation: evaluates and stores to cache
    res1 = scorer.score(activity, participant, context)
    assert res1.source == "llm"

    # Second evaluation: retrieved from cache
    res2 = scorer.score(activity, participant, context)
    assert res2.source == "cache"
    assert res2.activity_id == "hot_springs"
    assert res2.tier == res1.tier


def test_tier3_with_mock_llm_client():
    """Verify structured parsing when an LLM client returns custom contextual JSON."""
    storage = MockCacheStorage()
    mock_llm = MockLLMClient({
        "tier": "recommend",
        "score": 0.88,
        "confidence": 0.95,
        "warnings": ["Ensure adequate hydration"],
        "score_components": {"altitude_acclimatization": 0.9},
    })
    scorer = LLMContextualScorer(cache_storage=storage, llm_client=mock_llm)

    activity = ActivityDefinition(activity_id="machu_picchu", canonical_name="Machu Picchu Citadel", source="static", intensity="high")
    participant = ParticipantRef(kind="person", ref_id="p1", label="adult", age=35)
    context = SuitabilityContext(destination_keys=["peru"], destination_climate="alpine")

    result = scorer.score(activity, participant, context)

    assert result.source == "llm"
    assert result.score == 0.88
    assert result.tier == "recommend"
    assert "hydration" in result.warnings[0].lower()
