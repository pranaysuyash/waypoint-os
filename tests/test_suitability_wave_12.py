"""
Wave 12: Suitability Engine Foundation — Regression Tests.
Verifies Tier 1 Hardening and Tier 2 Itinerary Coherence.
"""

import pytest
from src.suitability.models import (
    ActivityDefinition,
    ParticipantRef,
    SuitabilityContext,
)
from src.suitability.scoring import evaluate_activity
from src.suitability.integration import evaluate_itinerary_coherence, generate_suitability_risks

class MockSlot:
    def __init__(self, value):
        self.value = value

class MockPacket:
    def __init__(self, facts=None):
        self.facts = facts or {}

def test_tier1_elderly_extreme_exclusion():
    """Verify that extreme intensity activities are now hard exclusions for elderly."""
    activity = ActivityDefinition(
        activity_id="extreme_trek",
        canonical_name="Extreme Trek",
        source="static",
        intensity="extreme",
        tags=["physical_intense", "extreme_intensity"]
    )
    participant = ParticipantRef(
        kind="person",
        ref_id="e1",
        label="elderly"
    )
    context = SuitabilityContext(destination_keys=["nepal"])
    
    result = evaluate_activity(activity, participant, context)
    
    assert result.tier == "exclude"
    # Rule uses "extreme_intensity" tag, or intensity-based downgrade
    # Let's check if the reason comes from the TAG_RULES
    assert any("Extreme physical intensity is unsafe" in reason for reason in result.hard_exclusion_reasons)

def test_tier1_toddler_late_night_exclusion():
    """Verify that late night activities are hard exclusions for toddlers."""
    activity = ActivityDefinition(
        activity_id="late_show",
        canonical_name="Midnight Show",
        source="static",
        tags=["late_night"]
    )
    participant = ParticipantRef(
        kind="person",
        ref_id="t1",
        label="toddler"
    )
    context = SuitabilityContext(destination_keys=["london"])
    
    result = evaluate_activity(activity, participant, context)
    
    assert result.tier == "exclude"
    assert "late night" in result.hard_exclusion_reasons[0].lower()

def test_tier1_budget_luxury_alignment():
    """Verify that luxury activities are discouraged for budget-conscious travelers."""
    activity = ActivityDefinition(
        activity_id="luxury_spa",
        canonical_name="Luxury Spa",
        source="static",
        tags=["luxury"]
    )
    participant = ParticipantRef(
        kind="person",
        ref_id="b1",
        label="adult"
    )
    # Budget preference is in context
    context = SuitabilityContext(
        destination_keys=["bali"],
        budget_preference="low"
    )
    
    result = evaluate_activity(activity, participant, context)
    
    assert result.tier == "discourage"
    assert "Luxury-tier activity exceeds" in result.warnings[0]

def test_tier2_elderly_overload():
    """Verify Tier 2 detection of elderly activity overload."""
    activities = [
        ActivityDefinition(activity_id="a1", canonical_name="A1", source="static", intensity="high"),
        ActivityDefinition(activity_id="a2", canonical_name="A2", source="static", intensity="high"),
    ]
    participants = [
        ParticipantRef(kind="person", ref_id="e1", label="elderly")
    ]
    context = SuitabilityContext(destination_keys=["xyz"])
    
    risks = evaluate_itinerary_coherence(activities, participants, context)
    
    assert any(r["flag"] == "suitability_overload_elderly" for r in risks)
    assert any("Potential overload" in r["message"] for r in risks)

def test_tier2_toddler_pacing():
    """Verify Tier 2 detection of toddler pacing issues."""
    activities = [
        ActivityDefinition(activity_id="a1", canonical_name="A1", source="static"),
        ActivityDefinition(activity_id="a2", canonical_name="A2", source="static"),
        ActivityDefinition(activity_id="a3", canonical_name="A3", source="static"),
        ActivityDefinition(activity_id="a4", canonical_name="A4", source="static"),
    ]
    participants = [
        ParticipantRef(kind="person", ref_id="t1", label="toddler")
    ]
    context = SuitabilityContext(destination_keys=["xyz"])
    
    risks = evaluate_itinerary_coherence(activities, participants, context)
    
    assert any(r["flag"] == "suitability_pacing_toddler" for r in risks)

def test_generate_risks_integration():
    """Verify full integration in generate_suitability_risks."""
    packet = MockPacket(facts={
        "party_composition": MockSlot({"elderly": 1}),
        "budget_preference": MockSlot("low"),
        "destination_candidates": MockSlot(["Paris"])
    })
    
    # Mocking activities - we'll just check if it runs without error and returns risks
    # Since STATIC_ACTIVITIES[:5] will be checked
    risks = generate_suitability_risks(packet)
    
    assert isinstance(risks, list)
    # The first few static activities usually include some that might trigger rules
    print(f"Generated {len(risks)} risks")
