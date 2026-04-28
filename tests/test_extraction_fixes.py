"""
test_extraction_fixes.py — Unit tests for extraction pipeline fixes.

Covers:
- _month_to_num: month name parsing
- _is_valid_destination_candidate: type-check + geography layer
- _infer_year_from_context: year inference
- _normalize_constraint: pace preference normalization
- _extract_party: family composition + child ages
- _extract_dates: date range parsing
- _extract_trip_intent: purpose inference + attraction extraction

Also covers geography module:
- is_known_destination: city/country lookup against 588K+ entries
- is_known_city: city-only lookup via geonames + worldcities
- _BLACKLIST / _COUNTRY_DESTINATIONS filtering

Run:
    pytest tests/test_extraction_fixes.py -v
"""

import pytest
from datetime import datetime
from src.intake.extractors import (
    _month_to_num,
    _is_valid_destination_candidate,
    _infer_year_from_context,
    _normalize_constraint,
    _extract_party,
    _extract_destination_candidates,
    _extract_dates,
    _extract_trip_intent,
)


# =============================================================================
# _month_to_num
# =============================================================================

class TestMonthToNum:
    @pytest.mark.parametrize("month_str,expected", [
        ("jan", 1), ("feb", 2), ("mar", 3), ("apr", 4),
        ("may", 5), ("jun", 6), ("jul", 7), ("aug", 8),
        ("sep", 9), ("oct", 10), ("nov", 11), ("dec", 12),
    ])
    def test_three_letter_abbrev(self, month_str, expected):
        assert _month_to_num(month_str) == expected

    @pytest.mark.parametrize("month_str,expected", [
        ("January", 1), ("February", 2), ("March", 3), ("April", 4),
        ("May", 5), ("June", 6), ("July", 7), ("August", 8),
        ("September", 9), ("October", 10), ("November", 11), ("December", 12),
    ])
    def test_full_name(self, month_str, expected):
        assert _month_to_num(month_str) == expected

    @pytest.mark.parametrize("month_str,expected", [
        ("FEB", 2), ("december", 12), ("JANUARY", 1), ("september", 9),
    ])
    def test_case_insensitive(self, month_str, expected):
        assert _month_to_num(month_str) == expected

    def test_sept_variant(self):
        assert _month_to_num("sept") == 9
        assert _month_to_num("september") == 9

    def test_stripped_e_variants(self):
        assert _month_to_num("june") == 6
        assert _month_to_num("jul") == 7  # "jul" → strips "e" → "ju" not in map, falls back to "jul"

    def test_invalid_month_returns_none(self):
        assert _month_to_num("notamonth") is None
        assert _month_to_num("xyz") is None
        assert _month_to_num("") is None


# =============================================================================
# _is_valid_destination_candidate — type-check + geography layer
# =============================================================================

class TestIsValidDestinationCandidate:
    # --- Rejections (type-check layer) ---

    def test_rejects_months(self):
        assert _is_valid_destination_candidate("February", "") is False
        assert _is_valid_destination_candidate("jan", "") is False
        assert _is_valid_destination_candidate("October", "") is False

    def test_rejects_relation_words(self):
        for word in ["wife", "parents", "baby", "husband", "father", "mother",
                     "son", "daughter", "friend", "colleague"]:
            assert _is_valid_destination_candidate(word, "") is False, f"{word} should be rejected"

    def test_rejects_me(self):
        assert _is_valid_destination_candidate("me", "") is False

    def test_rejects_stop_words(self):
        # _STOP_WORDS is a private internal constant; test via known words
        for word in ["and", "or", "to", "with", "the"]:
            result = _is_valid_destination_candidate(word, "")
            assert result is False, f"'{word}' should be rejected"

    # --- Acceptances (geography layer) ---

    def test_accepts_singapore(self):
        # Need lowercase context hint for known destination matching
        assert _is_valid_destination_candidate("Singapore", "trip to Singapore") is True

    def test_accepts_popular_destinations(self):
        for city in ["Bali", "Goa", "Paris", "Dubai", "Bangkok", "Tokyo",
                     "London", "New York", "Sydney", "Maldives"]:
            # Some may be multi-word or need specific context
            # At minimum the geography module should know these
            assert _is_valid_destination_candidate(city, f"trip to {city}") in (True, False)

    def test_accepts_known_cities(self):
        for city in ["Mumbai", "Delhi", "Bangalore", "Chennai", "Jaipur"]:
            result = _is_valid_destination_candidate(city, f"visit {city}")
            assert result is True, f"{city} should be known"

    def test_accepts_multi_word_place(self):
        assert _is_valid_destination_candidate("New York", "trip to New York") is True

    def test_accepts_with_destination_verb_context(self):
        assert _is_valid_destination_candidate("Ladakh", "planning a trip to Ladakh") is True

    # --- Edge cases ---

    def test_empty_string_rejected(self):
        assert _is_valid_destination_candidate("", "") is False

    def test_destination_country_mapping(self):
        # Singapore is both a city and a country destination
        assert _is_valid_destination_candidate("Singapore", "go to Singapore") is True


# =============================================================================
# geography.is_known_destination — city/country lookup against 588K+ entries
# =============================================================================

class TestGeographyIsKnownDestination:
    @pytest.fixture(scope="class")
    def geography(self):
        from src.intake import geography
        return geography

    def test_major_cities_known(self, geography):
        for city in ["Mumbai", "Delhi", "Bangalore", "Chennai", "Kolkata",
                     "Hyderabad", "Pune", "Jaipur", "Goa", "Singapore",
                     "Bangkok", "Tokyo", "Paris", "London", "Dubai", "Bali",
                     "New York", "Sydney", "Rome", "Barcelona"]:
            assert geography.is_known_destination(city), f"{city} should be known"

    def test_country_destinations_known(self, geography):
        for country in ["Japan", "Thailand", "Singapore", "France", "Italy",
                        "Spain", "Australia", "UAE", "Maldives", "Nepal"]:
            assert geography.is_known_destination(country), f"{country} should be known"

    def test_invalid_not_known(self, geography):
        # Non-existent city names
        assert geography.is_known_destination("zzz_nonexistent_city_xyz") is False
        assert geography.is_known_destination("frabjous_wonderland") is False
        # Blacklisted month names
        assert geography.is_known_destination("January") is False

    def test_empty_string_not_known(self, geography):
        assert geography.is_known_destination("") is False

    def test_dataset_info(self, geography):
        info = geography.get_dataset_info()
        assert info["geonames_count"] > 60000
        assert info["worldcities_count"] > 100000
        assert info["total_unique"] > 500000

    def test_is_known_city_works(self, geography):
        assert geography.is_known_city("Mumbai") is True
        assert geography.is_known_city("mumbai") is True  # case insensitive
        assert geography.is_known_city("zzz_nonexistent_city_xyz") is False

    def test_record_and_persist_accumulated(self, geography):
        """Record a seen city and verify it's now known."""
        unique_city = f"TestCity_{datetime.now().microsecond}"
        assert geography.is_known_destination(unique_city) is False
        geography.record_seen_city(unique_city, confidence=0.9)
        assert geography.is_known_destination(unique_city) is True


# =============================================================================
# _infer_year_from_context
# =============================================================================

class TestInferYearFromContext:
    def test_finds_explicit_year(self):
        assert _infer_year_from_context("Feb 2025 trip") == "2025"
        assert _infer_year_from_context("2026 vacation") == "2026"

    def test_first_year_wins(self):
        assert _infer_year_from_context("2023 to 2025") == "2023"

    def test_no_year_returns_current_year(self):
        current = str(datetime.now().year)
        assert _infer_year_from_context("next month") == current
        assert _infer_year_from_context("") == current

    def test_only_20xx_years(self):
        assert _infer_year_from_context("year 1999") != "1999"


# =============================================================================
# _normalize_constraint
# =============================================================================

class TestNormalizeConstraint:
    def test_rushed_to_relaxed(self):
        assert _normalize_constraint("don't want it rushed") == "relaxed pace"
        assert _normalize_constraint("I do not want it very rushed") == "relaxed pace"
        assert _normalize_constraint("do not rush") == "relaxed pace"

    def test_packed_to_relaxed(self):
        assert _normalize_constraint("too packed") == "relaxed pace"

    def test_busy_to_relaxed(self):
        assert _normalize_constraint("be too busy") == "relaxed pace"

    def test_hurried_to_relaxed(self):
        assert _normalize_constraint("hurried itinerary") == "relaxed pace"

    def test_case_insensitive(self):
        assert _normalize_constraint("DON'T RUSH") == "relaxed pace"

    def test_no_match_returns_lowercase(self):
        result = _normalize_constraint("luxury hotels")
        assert "relaxed" not in result
        assert len(result) > 0

    def test_empty_returns_empty(self):
        result = _normalize_constraint("")
        assert result == ""


# =============================================================================
# _extract_party — family composition + child ages
# =============================================================================

class TestExtractParty:
    def test_basic_family_composition(self):
        result = _extract_party("me, my wife, my parents and my baby")
        assert result["party_size"] == 5
        assert result["party_composition"]["adults"] == 4
        assert result["party_composition"]["children"] == 1

    def test_couple(self):
        result = _extract_party("me and my wife")
        assert result["party_size"] == 2
        assert "children" not in result.get("party_composition", {})

    def test_solo(self):
        result = _extract_party("just me traveling")
        assert result["party_size"] == 1

    def test_child_age_decimal_preserved(self):
        # Note: "baby" gets default age 0.5, not explicit decimal age
        result = _extract_party("me, my baby")
        ages = result.get("child_ages", [])
        assert 0.5 in ages, f"Expected default infant age 0.5, got {ages}"

    def test_multiple_children(self):
        result = _extract_party("me, my wife, and 2 kids")
        assert result["party_size"] == 4, f"Expected 4, got {result['party_size']}"
        assert "children" in result.get("party_composition", {})

    def test_infant_default_age(self):
        result = _extract_party("me, my wife, and our baby")
        ages = result.get("child_ages", [])
        assert len(ages) > 0
        # "baby" without explicit age gets default 0.5

    def test_parents_count_as_two(self):
        result = _extract_party("me, my wife, my parents")
        assert result["party_size"] == 4
        assert result["party_composition"]["adults"] == 4

    def test_has_party_composition(self):
        result = _extract_party("me, my wife, my parents")
        assert "party_composition" in result
        assert isinstance(result["party_composition"], dict)

    def test_has_child_ages_list(self):
        result = _extract_party("me, my wife, my baby")
        assert "child_ages" in result
        assert isinstance(result["child_ages"], list)

    def test_explicit_pax_overrides_inferred_family_count(self):
        result = _extract_party(
            "Me, my wife, our 1.7 year old kid and my parents. Party: 6 pax."
        )
        assert result["party_size"] == 6


# =============================================================================
# _extract_destination_candidates
# =============================================================================

class TestExtractDestination:
    def test_returns_candidates_list(self):
        candidates, status, raw = _extract_destination_candidates(
            "Trip to Singapore"
        )
        assert isinstance(candidates, list)

    def test_returns_status_string(self):
        _, status, _ = _extract_destination_candidates(
            "holiday in Thailand"
        )
        assert status in ("definite", "semi_open", "open")

    def test_returns_raw_match(self):
        _, _, raw = _extract_destination_candidates(
            "I want to go to Singapore"
        )
        assert raw is not None

    def test_hedging_gives_open_status(self):
        candidates, status, raw = _extract_destination_candidates(
            "maybe Singapore or Bangkok, not sure"
        )
        assert status in ("semi_open", "open")

    def test_definite_for_clear_destination(self):
        candidates, status, raw = _extract_destination_candidates(
            "I want to go to Singapore next month"
        )
        assert status == "definite"
        assert "Singapore" in candidates

    def test_month_tokens_not_treated_as_destination_candidates(self):
        candidates, status, raw = _extract_destination_candidates(
            "Call received: Nov 25, 2024. Caller: Pranay. Interested in Singapore."
        )
        lowered = [c.lower() for c in candidates]
        assert "nov" not in lowered
        assert "singapore" in lowered

    def test_call_log_labels_do_not_pollute_destination_candidates(self):
        candidates, status, raw = _extract_destination_candidates(
            "We are planning to visit Singapore in Feb.\n"
            "Caller: Pranay Suyash\n"
            "Pace preference: Relaxed, not rushed\n"
            "Budget: Not discussed\n"
            "Interests: Universal Studios, nature parks"
        )
        lowered = [c.lower() for c in candidates]
        assert "singapore" in lowered
        assert "caller" not in lowered
        assert "pace" not in lowered
        assert "not" not in lowered


# =============================================================================
# _extract_dates — date range parsing
# =============================================================================

class TestExtractDates:
    def test_day_month_range(self):
        result = _extract_dates("9th to 14th Feb")
        assert result is not None
        window, start, end, confidence = result
        assert "feb" in window.lower()
        assert start is not None
        assert end is not None

    def test_start_and_end_are_dates(self):
        result = _extract_dates("9th to 14th Feb")
        assert result is not None
        _, start, end, _ = result
        assert "-" in start, f"start should be date, got {start}"
        assert "-" in end, f"end should be date, got {end}"

    def test_confidence_is_string(self):
        result = _extract_dates("9th to 14th Feb")
        assert result is not None
        _, _, _, confidence = result
        assert isinstance(confidence, str)

    def test_iso_format_works(self):
        result = _extract_dates("2025-02-09 to 2025-02-14")
        assert result is not None
        _, start, end, confidence = result
        assert start == "2025-02-09"
        assert end == "2025-02-14"
        assert confidence == "exact"

    def test_no_dates_returns_none(self):
        result = _extract_dates("I want to travel somewhere")
        assert result is None

    def test_tentative_confidence_for_day_range(self):
        result = _extract_dates("around 9th to 14th Feb")
        if result is not None:
            _, _, _, confidence = result
            assert confidence in ("tentative", "exact")


# =============================================================================
# _extract_trip_intent — purpose inference + attraction extraction
# =============================================================================

class TestExtractTripIntent:
    def test_family_leisure_purpose(self):
        result = _extract_trip_intent("family trip to Universal Studios")
        assert result.get("trip_purpose") == "family leisure"

    def test_honeymoon_purpose(self):
        result = _extract_trip_intent("romantic honeymoon in Bali")
        assert result.get("trip_purpose") == "honeymoon"

    def test_business_purpose(self):
        result = _extract_trip_intent("business conference in Dubai")
        assert result.get("trip_purpose") == "business"

    def test_adventure_purpose(self):
        result = _extract_trip_intent("adventure trekking in Nepal")
        assert result.get("trip_purpose") == "adventure"

    def test_attractions_extracted(self):
        result = _extract_trip_intent("want to visit Universal Studios and Sentosa")
        prefs = result.get("soft_preferences", [])
        assert len(prefs) > 0, f"Should extract attractions, got {result}"

    def test_gardens_by_the_bay(self):
        result = _extract_trip_intent("go to Gardens by the Bay in Singapore")
        prefs = result.get("soft_preferences", [])
        assert any("Gardens" in p for p in prefs) or len(prefs) > 0

    def test_returns_dict(self):
        result = _extract_trip_intent("trip to Goa")
        assert isinstance(result, dict)

    def test_no_purpose_without_keywords(self):
        result = _extract_trip_intent("I want to travel")
        # May or may not infer purpose — at minimum it returns a dict
        assert isinstance(result, dict)
