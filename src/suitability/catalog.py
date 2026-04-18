"""
suitability.catalog — Static activity catalog for common travel activities.

This provides a baseline set of activity definitions for suitability scoring.
Activities can be extended via agency-specific catalogs or external API ingestion.
"""

from .models import ActivityDefinition

# Common travel activities with suitability tags
# Based on architecture: D4/D6 suitability matrix
STATIC_ACTIVITIES = [
    # Water-based activities
    ActivityDefinition(
        activity_id="snorkeling",
        canonical_name="Snorkeling",
        source="static",
        tags=["water_based", "physical_moderate"],
        intensity="moderate",
        duration_hours=2.0,
        min_age=6,
        max_age=None,
        accessibility_tags=["water_confidence_required"],
    ),
    ActivityDefinition(
        activity_id="scuba_diving",
        canonical_name="Scuba Diving",
        source="static",
        tags=["water_based", "physical_intense", "height_required"],
        intensity="high",
        duration_hours=4.0,
        min_age=10,
        max_age=None,
        accessibility_tags=["certification_required", "medical_clearance"],
    ),
    ActivityDefinition(
        activity_id="white_water_rafting",
        canonical_name="White Water Rafting",
        source="static",
        tags=["water_based", "physical_intense", "height_required"],
        intensity="extreme",
        duration_hours=3.0,
        min_age=12,
        max_age=None,
        accessibility_tags=["swimming_required"],
    ),
    
    # Land-based physical activities
    ActivityDefinition(
        activity_id="hiking_easy",
        canonical_name="Easy Hiking Trail",
        source="static",
        tags=["walking_heavy"],
        intensity="moderate",
        duration_hours=2.5,
        min_age=None,
        max_age=None,
        accessibility_tags=["mobility_required"],
    ),
    ActivityDefinition(
        activity_id="hiking_difficult",
        canonical_name="Difficult Mountain Hike",
        source="static",
        tags=["walking_heavy", "physical_intense", "height_required"],
        intensity="high",
        duration_hours=6.0,
        min_age=12,
        max_age=None,
        accessibility_tags=["good_fitness_required"],
    ),
    ActivityDefinition(
        activity_id="zip_line",
        canonical_name="Zip Line Adventure",
        source="static",
        tags=["height_required", "physical_moderate"],
        intensity="high",
        duration_hours=1.5,
        min_age=8,
        max_age=None,
        max_weight_kg=120,
        accessibility_tags=["weight_limit"],
    ),
    
    # Cultural/Seated activities
    ActivityDefinition(
        activity_id="temple_visit",
        canonical_name="Temple/Cultural Site Visit",
        source="static",
        tags=["seated_show", "cultural"],
        intensity="light",
        duration_hours=2.0,
        min_age=None,
        max_age=None,
        accessibility_tags=["wheelchair_accessible"],
    ),
    ActivityDefinition(
        activity_id="cooking_class",
        canonical_name="Local Cooking Class",
        source="static",
        tags=["seated_show", "cultural"],
        intensity="light",
        duration_hours=3.0,
        min_age=6,
        max_age=None,
        accessibility_tags=["seated_activity"],
    ),
    ActivityDefinition(
        activity_id="boat_cruise",
        canonical_name="Scenic Boat Cruise",
        source="static",
        tags=["seated_show"],
        intensity="light",
        duration_hours=2.0,
        min_age=None,
        max_age=None,
        accessibility_tags=["wheelchair_accessible"],
    ),
    
    # Adventure activities
    ActivityDefinition(
        activity_id="bungee_jumping",
        canonical_name="Bungee Jumping",
        source="static",
        tags=["height_required", "physical_intense"],
        intensity="extreme",
        duration_hours=1.0,
        min_age=18,
        max_age=None,
        max_weight_kg=120,
        accessibility_tags=["weight_limit", "medical_clearance"],
    ),
    ActivityDefinition(
        activity_id="skydiving",
        canonical_name="Tandem Skydiving",
        source="static",
        tags=["height_required", "physical_intense"],
        intensity="extreme",
        duration_hours=3.0,
        min_age=18,
        max_age=None,
        max_weight_kg=100,
        accessibility_tags=["weight_limit", "medical_clearance"],
    ),
    
    # Wildlife/Nature
    ActivityDefinition(
        activity_id="safari_drive",
        canonical_name="Wildlife Safari Drive",
        source="static",
        tags=["seated_show"],
        intensity="light",
        duration_hours=3.0,
        min_age=None,
        max_age=None,
        accessibility_tags=["vehicle_based"],
    ),
    ActivityDefinition(
        activity_id="elephant_sanctuary",
        canonical_name="Elephant Sanctuary Visit",
        source="static",
        tags=["walking_heavy"],
        intensity="moderate",
        duration_hours=4.0,
        min_age=6,
        max_age=None,
        accessibility_tags=["mobility_required"],
    ),
    
    # Urban/City activities
    ActivityDefinition(
        activity_id="city_walking_tour",
        canonical_name="City Walking Tour",
        source="static",
        tags=["walking_heavy"],
        intensity="moderate",
        duration_hours=3.0,
        min_age=None,
        max_age=None,
        accessibility_tags=["mobility_required"],
    ),
    ActivityDefinition(
        activity_id="museum_visit",
        canonical_name="Museum Visit",
        source="static",
        tags=["seated_show", "cultural"],
        intensity="light",
        duration_hours=2.5,
        min_age=None,
        max_age=None,
        accessibility_tags=["wheelchair_accessible"],
    ),
    
    # Rest/Relaxation
    ActivityDefinition(
        activity_id="spa_treatment",
        canonical_name="Spa Treatment",
        source="static",
        tags=["seated_show"],
        intensity="light",
        duration_hours=2.0,
        min_age=16,
        max_age=None,
        accessibility_tags=["seated_activity"],
    ),
    ActivityDefinition(
        activity_id="beach_relaxation",
        canonical_name="Beach Relaxation",
        source="static",
        tags=["seated_show"],
        intensity="light",
        duration_hours=4.0,
        min_age=None,
        max_age=None,
        accessibility_tags=["wheelchair_accessible_beach"],
    ),
]

# Index by activity_id for fast lookup
ACTIVITY_BY_ID = {a.activity_id: a for a in STATIC_ACTIVITIES}

# Index by tags for filtering
ACTIVITIES_BY_TAG: dict[str, list[ActivityDefinition]] = {}
for activity in STATIC_ACTIVITIES:
    for tag in activity.tags:
        ACTIVITIES_BY_TAG.setdefault(tag, []).append(activity)


def get_activity(activity_id: str) -> ActivityDefinition | None:
    """Get activity by ID."""
    return ACTIVITY_BY_ID.get(activity_id)


def get_activities_by_tag(tag: str) -> list[ActivityDefinition]:
    """Get all activities with a specific tag."""
    return ACTIVITIES_BY_TAG.get(tag, [])


def get_activities_by_intensity(intensity: str) -> list[ActivityDefinition]:
    """Get all activities with a specific intensity level."""
    return [a for a in STATIC_ACTIVITIES if a.intensity == intensity]


def get_activities_for_participant_age(age: int) -> list[ActivityDefinition]:
    """Get activities suitable for a specific age."""
    suitable = []
    for activity in STATIC_ACTIVITIES:
        if activity.min_age is not None and age < activity.min_age:
            continue
        if activity.max_age is not None and age > activity.max_age:
            continue
        suitable.append(activity)
    return suitable
