"""
Test suite for suitability module.

Tests Tier 1 deterministic scoring, Tier 2 context rules,
confidence calculation, and catalog functionality.
"""

import pytest
from src.suitability.models import (
    ActivityDefinition,
    ActivitySuitability,
    ParticipantRef,
    StructuredRisk,
    SuitabilityContext,
)
from src.suitability.scoring import evaluate_activity
from src.suitability.context_rules import apply_tour_context_rules
from src.suitability.confidence import compute_confidence, collect_missing_signals
from src.suitability.catalog import (
    get_activity,
    get_activities_by_tag,
    get_activities_by_intensity,
    get_activities_for_participant_age,
    STATIC_ACTIVITIES,
)


class TestModels:
    """Test data model integrity."""

    def test_participant_ref_creation(self):
        """Test ParticipantRef creation with all fields."""
        participant = ParticipantRef(
            kind="person",
            ref_id="p1",
            label="adult",
            age=35,
            metadata={"weight_kg": 75},
        )
        assert participant.kind == "person"
        assert participant.age == 35
        assert participant.metadata["weight_kg"] == 75

    def test_activity_definition_creation(self):
        """Test ActivityDefinition creation with all fields."""
        activity = ActivityDefinition(
            activity_id="test_activity",
            canonical_name="Test Activity",
            source="static",
            tags=["water_based", "physical_intense"],
            intensity="high",
            duration_hours=3.0,
            min_age=12,
            max_age=None,
            max_weight_kg=100,
        )
        assert activity.activity_id == "test_activity"
        assert activity.intensity == "high"
        assert activity.max_weight_kg == 100

    def test_suitability_context_creation(self):
        """Test SuitabilityContext creation."""
        context = SuitabilityContext(
            destination_keys=["Goa"],
            trip_duration_nights=5,
            pace_preference="balanced",
            day_activities=[],
            trip_activities=[],
            day_index=2,
            season_month=12,
            destination_climate="tropical_humid",
        )
        assert context.destination_keys == ["Goa"]
        assert context.season_month == 12


class TestTier1Scoring:
    """Test Tier 1 deterministic scoring."""

    def test_age_exclusion_below_minimum(self):
        """Test that participants below minimum age are excluded."""
        activity = ActivityDefinition(
            activity_id="scuba",
            canonical_name="Scuba Diving",
            source="static",
            tags=["water_based"],
            intensity="high",
            min_age=10,
        )
        participant = ParticipantRef(
            kind="person", ref_id="p1", label="child", age=8
        )
        context = SuitabilityContext(destination_keys=["Goa"])

        result = evaluate_activity(activity, participant, context)
        assert result.tier == "exclude"
        assert not result.compatible
        assert "below minimum age" in result.hard_exclusion_reasons[0]

    def test_age_exclusion_above_maximum(self):
        """Test that participants above maximum age are excluded."""
        activity = ActivityDefinition(
            activity_id="bungee",
            canonical_name="Bungee Jumping",
            source="static",
            tags=["height_required"],
            intensity="extreme",
            max_age=65,
        )
        participant = ParticipantRef(
            kind="person", ref_id="p1", label="elderly", age=70
        )
        context = SuitabilityContext(destination_keys=["Goa"])

        result = evaluate_activity(activity, participant, context)
        assert result.tier == "exclude"
        assert "exceeds maximum age" in result.hard_exclusion_reasons[0]

    def test_weight_exclusion(self):
        """Test weight-based exclusion."""
        activity = ActivityDefinition(
            activity_id="zip_line",
            canonical_name="Zip Line",
            source="static",
            tags=["height_required"],
            intensity="high",
            max_weight_kg=100,
        )
        participant = ParticipantRef(
            kind="person",
            ref_id="p1",
            label="adult",
            age=35,
            metadata={"weight_kg": 120},
        )
        context = SuitabilityContext(destination_keys=["Goa"])

        result = evaluate_activity(activity, participant, context)
        assert result.tier == "exclude"
        assert "exceeds maximum weight" in result.hard_exclusion_reasons[0]

    def test_tag_based_exclusion(self):
        """Test tag-based exclusion for toddlers."""
        activity = ActivityDefinition(
            activity_id="snorkeling",
            canonical_name="Snorkeling",
            source="static",
            tags=["water_based"],
            intensity="moderate",
            min_age=1,  # Set min_age low to test tag-based exclusion
        )
        participant = ParticipantRef(
            kind="person", ref_id="p1", label="toddler", age=3
        )
        context = SuitabilityContext(destination_keys=["Goa"])

        result = evaluate_activity(activity, participant, context)
        assert result.tier == "exclude"
        assert "unsafe for toddlers" in result.hard_exclusion_reasons[0]

    def test_tag_based_recommendation(self):
        """Test tag-based recommendation for elderly."""
        activity = ActivityDefinition(
            activity_id="temple_visit",
            canonical_name="Temple Visit",
            source="static",
            tags=["seated_show"],  # Only one tag to test recommendation
            intensity="light",
        )
        participant = ParticipantRef(
            kind="person", ref_id="p1", label="elderly", age=70
        )
        context = SuitabilityContext(destination_keys=["Goa"])

        result = evaluate_activity(activity, participant, context)
        # Should be recommend or strong_recommend based on intensity
        assert result.tier in ["recommend", "strong_recommend"]
        assert result.compatible
        assert result.score > 0.5

    def test_intensity_scoring_elderly(self):
        """Test intensity-based scoring for elderly participants."""
        # High intensity activity for elderly
        high_intensity = ActivityDefinition(
            activity_id="hiking_difficult",
            canonical_name="Difficult Hike",
            source="static",
            tags=["walking_heavy"],
            intensity="high",
        )
        # Light intensity activity for elderly
        light_intensity = ActivityDefinition(
            activity_id="temple_visit",
            canonical_name="Temple Visit",
            source="static",
            tags=["seated_show"],
            intensity="light",
        )
        
        participant = ParticipantRef(
            kind="person", ref_id="p1", label="elderly", age=70
        )
        context = SuitabilityContext(destination_keys=["Goa"])

        high_result = evaluate_activity(high_intensity, participant, context)
        light_result = evaluate_activity(light_intensity, participant, context)
        
        # Light activity should score higher for elderly
        assert light_result.score > high_result.score

    def test_confidence_calculation(self):
        """Test confidence calculation with complete data."""
        activity = ActivityDefinition(
            activity_id="test",
            canonical_name="Test Activity",
            source="static",
            tags=["water_based"],
            intensity="moderate",
            duration_hours=2.0,
            min_age=10,
            max_age=65,
            max_weight_kg=100,
        )
        participant = ParticipantRef(
            kind="person", ref_id="p1", label="adult", age=35
        )
        context = SuitabilityContext(destination_keys=["Goa"])

        result = evaluate_activity(activity, participant, context)
        assert result.confidence > 0.8  # High confidence with all data

    def test_missing_signals(self):
        """Test missing signals detection."""
        activity = ActivityDefinition(
            activity_id="test",
            canonical_name="Test Activity",
            source="static",
            tags=[],  # No tags
            intensity="unknown",  # Invalid intensity
            duration_hours=None,  # No duration
        )
        participant = ParticipantRef(
            kind="person", ref_id="p1", label="adult", age=35
        )
        context = SuitabilityContext(destination_keys=["Goa"])

        result = evaluate_activity(activity, participant, context)
        assert len(result.missing_signals) > 0
        assert "duration_hours" in result.missing_signals
        assert "intensity" in result.missing_signals


class TestTier2ContextRules:
    """Test Tier 2 day/trip coherence rules."""

    def test_cumulative_fatigue_risk(self):
        """Test cumulative fatigue risk detection."""
        # Create a high-intensity day
        day_activities = [
            ActivityDefinition(
                activity_id="hike1",
                canonical_name="Morning Hike",
                source="static",
                intensity="high",
                duration_hours=3.0,
            ),
            ActivityDefinition(
                activity_id="hike2",
                canonical_name="Afternoon Hike",
                source="static",
                intensity="high",
                duration_hours=4.0,
            ),
        ]
        
        activity = ActivityDefinition(
            activity_id="hike3",
            canonical_name="Evening Hike",
            source="static",
            tags=["walking_heavy"],
            intensity="high",
            duration_hours=2.0,
        )
        
        participant = ParticipantRef(
            kind="person", ref_id="p1", label="elderly", age=70
        )
        
        context = SuitabilityContext(
            destination_keys=["Goa"],
            day_activities=day_activities,
            destination_climate="tropical_humid",
        )
        
        base_result = evaluate_activity(activity, participant, context)
        final_result = apply_tour_context_rules(base_result, activity, participant, context)
        
        # Should have cumulative fatigue risk
        assert len(final_result.generated_risks) > 0
        risk_flags = [r.flag for r in final_result.generated_risks]
        assert "cumulative_fatigue_risk" in risk_flags

    def test_climate_amplified_exertion(self):
        """Test climate-amplified exertion risk."""
        activity = ActivityDefinition(
            activity_id="hike",
            canonical_name="Mountain Hike",
            source="static",
            tags=["walking_heavy"],
            intensity="high",
            duration_hours=4.0,
        )
        
        participant = ParticipantRef(
            kind="person", ref_id="p1", label="elderly", age=70
        )
        
        context = SuitabilityContext(
            destination_keys=["Goa"],
            destination_climate="tropical_humid",
        )
        
        base_result = evaluate_activity(activity, participant, context)
        final_result = apply_tour_context_rules(base_result, activity, participant, context)
        
        # Should have climate risk
        risk_flags = [r.flag for r in final_result.generated_risks]
        assert "climate_amplified_exertion" in risk_flags

    def test_back_to_back_strain(self):
        """Test back-to-back high-intensity activity risk."""
        # Create day with multiple high-intensity activities
        day_activities = [
            ActivityDefinition(
                activity_id="rafting",
                canonical_name="White Water Rafting",
                source="static",
                intensity="extreme",
                duration_hours=3.0,
            ),
            ActivityDefinition(
                activity_id="zip",
                canonical_name="Zip Line",
                source="static",
                intensity="high",
                duration_hours=2.0,
            ),
        ]
        
        activity = ActivityDefinition(
            activity_id="bungee",
            canonical_name="Bungee Jumping",
            source="static",
            tags=["height_required"],
            intensity="extreme",
            duration_hours=1.0,
        )
        
        participant = ParticipantRef(
            kind="person", ref_id="p1", label="elderly", age=70
        )
        
        context = SuitabilityContext(
            destination_keys=["Goa"],
            day_activities=day_activities,
        )
        
        base_result = evaluate_activity(activity, participant, context)
        final_result = apply_tour_context_rules(base_result, activity, participant, context)
        
        # Should have back-to-back strain risk
        risk_flags = [r.flag for r in final_result.generated_risks]
        assert "back_to_back_strain" in risk_flags


class TestCatalog:
    """Test activity catalog functionality."""

    def test_get_activity_by_id(self):
        """Test getting activity by ID."""
        activity = get_activity("snorkeling")
        assert activity is not None
        assert activity.activity_id == "snorkeling"
        assert "water_based" in activity.tags

    def test_get_activities_by_tag(self):
        """Test getting activities by tag."""
        water_activities = get_activities_by_tag("water_based")
        assert len(water_activities) > 0
        for activity in water_activities:
            assert "water_based" in activity.tags

    def test_get_activities_by_intensity(self):
        """Test getting activities by intensity."""
        light_activities = get_activities_by_intensity("light")
        assert len(light_activities) > 0
        for activity in light_activities:
            assert activity.intensity == "light"

    def test_get_activities_for_participant_age(self):
        """Test getting activities suitable for age."""
        # Activities for 8-year-old
        activities_8 = get_activities_for_participant_age(8)
        for activity in activities_8:
            if activity.min_age is not None:
                assert activity.min_age <= 8
            if activity.max_age is not None:
                assert activity.max_age >= 8

    def test_static_activities_count(self):
        """Test that we have a reasonable number of activities."""
        assert len(STATIC_ACTIVITIES) >= 15


class TestIntegration:
    """Test integration between scoring tiers."""

    def test_full_scoring_pipeline(self):
        """Test complete scoring from Tier 1 to Tier 2."""
        # Get an activity from catalog
        activity = get_activity("hiking_difficult")
        assert activity is not None
        
        # Create participant
        participant = ParticipantRef(
            kind="person", ref_id="p1", label="elderly", age=70
        )
        
        # Create context with day activities
        day_activities = [
            get_activity("hiking_easy"),
            get_activity("cooking_class"),
        ]
        
        context = SuitabilityContext(
            destination_keys=["Goa"],
            day_activities=day_activities,
            destination_climate="tropical_humid",
        )
        
        # Tier 1 scoring
        tier1_result = evaluate_activity(activity, participant, context)
        
        # Tier 2 context rules
        final_result = apply_tour_context_rules(tier1_result, activity, participant, context)
        
        # Verify results
        assert final_result.tier in ["exclude", "discourage", "neutral", "recommend", "strong_recommend"]
        assert 0.0 <= final_result.score <= 1.0
        assert 0.0 <= final_result.confidence <= 1.0


class TestConfidence:
    """Test confidence calculation functions."""

    def test_compute_confidence_empty(self):
        """Test confidence with empty field confidence."""
        confidence = compute_confidence({})
        assert confidence == 0.0

    def test_compute_confidence_normal(self):
        """Test confidence with normal values."""
        field_confidence = {
            "intensity": 0.95,
            "age_bounds": 0.8,
            "tags": 0.7,
        }
        confidence = compute_confidence(field_confidence)
        assert 0.7 <= confidence <= 0.95

    def test_collect_missing_signals(self):
        """Test missing signals collection."""
        activity = ActivityDefinition(
            activity_id="test",
            canonical_name="Test",
            source="static",
            tags=[],
            intensity="unknown",
            duration_hours=None,
        )
        context = SuitabilityContext(destination_keys=["Goa"])
        
        missing = collect_missing_signals(activity, context)
        assert "duration_hours" in missing
        assert "intensity" in missing


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
