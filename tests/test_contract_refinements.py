from src.intake.extractors import extract_flight_inclusiveness, _extract_trip_intent
from src.intake.geography import resolve_destination_hierarchy


def test_flight_inclusiveness_tri_state():
    """Verify extract_flight_inclusiveness accurately categorizes tri-state requirements."""
    # 1. Included
    assert extract_flight_inclusiveness("Please include flights from London to Paris") == "INCLUDE_FLIGHTS"
    assert extract_flight_inclusiveness("Need flights and 4-star hotel in Tokyo") == "INCLUDE_FLIGHTS"
    
    # 2. Excluded
    assert extract_flight_inclusiveness("We already have our own flights booked, need hotel only") == "EXCLUDE_FLIGHTS"
    assert extract_flight_inclusiveness("Land only package, no flights needed") == "EXCLUDE_FLIGHTS"
    
    # 3. Unspecified
    assert extract_flight_inclusiveness("Planning a 4-day trip to Rome for our anniversary") == "UNSPECIFIED_AMBIGUOUS"


def test_hard_constraint_negation_extraction():
    """Verify negated phrases are properly captured as negative constraints without false positive bleed."""
    text = "We want a relaxing vacation in Greece, but not interested in cruises and no overnight trains."
    res = _extract_trip_intent(text)
    hard = res.get("hard_constraints", [])
    assert len(hard) >= 1
    assert any("cruise" in c or "train" in c for c in hard)


def test_destination_hierarchy_country_vs_city():
    """Verify resolve_destination_hierarchy distinguishes country-level from city-level destinations."""
    italy_res = resolve_destination_hierarchy("Italy")
    assert italy_res["type"] == "country"
    assert italy_res["is_country_level"] is True
    assert "Rome" in italy_res["recommended_cities"]
    assert "FCO" in italy_res["primary_hubs"]
    
    paris_res = resolve_destination_hierarchy("Paris")
    assert paris_res["type"] == "city"
    assert paris_res["is_country_level"] is False
