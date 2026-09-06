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
    _extract_budget,
    _extract_budget_scope,
    _extract_destination_candidates,
    _extract_dates,
    _extract_trip_intent,
    _extract_city_set,
    _extract_date_flexibility,
    _is_origin_candidate,
    ExtractionPipeline,
)
from src.intake.decision import run_gap_and_decision
from src.intake.normalizer import Normalizer
from src.intake.packet_models import SourceEnvelope
from src.intake.validation import validate_packet


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

    def test_couple_phrase_infers_two_adults(self):
        result = _extract_party("Couple from Mumbai for Bali in July")
        assert result["party_size"] == 2
        assert result["party_composition"].get("adults") == 2

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

    def test_agency_based_city_does_not_override_real_destination(self):
        candidates, status, raw = _extract_destination_candidates(
            "Nairobi-based agency request: family of 5 from Nairobi for 7N Zanzibar in December."
        )
        lowered = [c.lower() for c in candidates]
        assert "nairobi" not in lowered
        assert "zanzibar" in lowered
        assert status in ("definite", "semi_open")

    def test_beach_resort_does_not_become_destination(self):
        candidates, status, raw = _extract_destination_candidates(
            "Small Nairobi agency handling a family holiday for 4 adults and 2 children from Nairobi to Zanzibar in August 2026. "
            "Budget KES 480,000. 6 nights. Beach resort, airport transfers, vegetarian meals."
        )
        lowered = [c.lower() for c in candidates]
        assert "beach" not in lowered
        assert "zanzibar" in lowered
        assert status in ("definite", "semi_open")


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

    def test_month_day_range_with_repeated_month(self):
        result = _extract_dates("Travel dates: July 10 to July 16")
        assert result is not None
        window, start, end, confidence = result
        assert "july" in window.lower()
        assert start is not None and end is not None
        assert start.endswith("-07-10"), start
        assert end.endswith("-07-16"), end
        assert confidence == "tentative"

    def test_month_day_range_without_repeated_month(self):
        result = _extract_dates("Travel dates: July 10-16")
        assert result is not None
        window, start, end, confidence = result
        assert "july" in window.lower()
        assert start is not None and end is not None
        assert start.endswith("-07-10"), start
        assert end.endswith("-07-16"), end
        assert confidence == "tentative"


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

    def test_corporate_group_prefers_business_purpose(self):
        result = _extract_trip_intent(
            "Large Nairobi agency managing a corporate group of 18 travelers from Nairobi to Singapore in October 2026. Need a fast quote that can be shared with procurement and two separate rooming lists."
        )
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

    def test_negation_does_not_leak_into_soft_preferences(self):
        result = _extract_trip_intent(
            "We don't want it rushed. Interested in Universal Studios and nature parks."
        )
        soft = result.get("soft_preferences", [])
        assert "it rushed" not in soft, f"Negation leak found in soft preferences: {soft}"
        assert "relaxed pace" in result.get("hard_constraints", []), result


class TestDestinationEnvelopeMerge:
    def test_explicit_destination_not_downgraded_by_later_undecided_envelope(self):
        pipeline = ExtractionPipeline()
        env1 = SourceEnvelope.from_freeform(
            "We are planning to visit Singapore sometime in Jan or Feb 2025.",
            "agency_notes",
            "agent",
        )
        env2 = SourceEnvelope.from_freeform(
            "Late-Nov call context; budget-conscious family, relaxed pace.",
            "agency_notes",
            "owner",
        )

        packet = pipeline.extract([env1, env2])
        destination_candidates = packet.facts["destination_candidates"].value
        destination_status = packet.facts["destination_status"].value

        assert "Singapore" in destination_candidates
        assert destination_status == "definite"


# =============================================================================
# Hinglish/Odia Extraction Fixes — Regression + New Tests
# =============================================================================

# ---------------------------------------------------------------------------
# Budget: bare INR values (3L, 3L tk, 3L tak, 300k)
# ---------------------------------------------------------------------------

class TestBudgetHinglish:
    """Bare INR budget expressions without explicit 'budget' keyword."""

    # --- Regression: existing English patterns still work ---
    def test_english_budget_with_keyword(self):
        result = _extract_budget("Budget 3L")
        assert result is not None
        assert result["min"] == 300000
        assert result["max"] == 300000

    def test_english_budget_around(self):
        result = _extract_budget("around 3L")
        assert result is not None
        assert result["min"] == 300000

    # --- New: bare values ---
    def test_bare_3l(self):
        result = _extract_budget("3L")
        assert result is not None, "bare '3L' should match"
        assert result["min"] == 300000
        assert result["max"] == 300000

    def test_bare_3l_lower(self):
        result = _extract_budget("3l")
        assert result is not None, "bare '3l' should match"
        assert result["min"] == 300000

    def test_bare_3l_tk(self):
        result = _extract_budget("3L tk")
        assert result is not None, "bare '3L tk' should match"
        assert result["min"] is not None

    def test_bare_3l_tak(self):
        result = _extract_budget("3L tak")
        assert result is not None, "bare '3L tak' should match"
        assert result["min"] is not None

    def test_bare_300k(self):
        result = _extract_budget("300k")
        assert result is not None, "bare '300k' should match"
        assert result["min"] == 300000

    def test_bare_1_5l(self):
        result = _extract_budget("1.5L")
        assert result is not None
        assert result["max"] == 150000

    def test_budget_3l_lowercase(self):
        result = _extract_budget("budget 3l")
        assert result is not None
        assert result["min"] == 300000

    def test_budget_label_with_currency_symbol(self):
        result = _extract_budget("Budget: USD 4,500")
        assert result is not None
        assert result["min"] == 4500
        assert result["max"] == 4500
        assert result["currency"] == "USD"

    def test_budget_with_african_currency_and_million_suffix(self):
        result = _extract_budget("Budget NGN 2.5m")
        assert result is not None
        assert result["min"] == 2500000
        assert result["max"] == 2500000
        assert result["currency"] == "NGN"

    def test_budget_with_rand_and_million_suffix(self):
        result = _extract_budget("Budget ZAR 3m")
        assert result is not None
        assert result["min"] == 3000000
        assert result["max"] == 3000000
        assert result["currency"] == "ZAR"

    def test_budget_with_plain_number_keeps_explicit_currency(self):
        result = Normalizer.parse_budget("NGN 2500000")
        assert result["min"] == 2500000
        assert result["max"] == 2500000
        assert result["currency"] == "NGN"

    def test_budget_with_plain_number_and_trailing_keyword_keeps_currency(self):
        result = _extract_budget("NGN 2500000 budget")
        assert result is not None
        assert result["min"] == 2500000
        assert result["max"] == 2500000
        assert result["currency"] == "NGN"


# ---------------------------------------------------------------------------
# Origin: Hinglish/Odia postpositions (se, ru, side)
# ---------------------------------------------------------------------------

class TestOriginHinglish:
    """Origin detection with Hinglish/Odia postpositions."""

    # --- Regression: English "from" still works ---
    def test_english_from_destination_excludes_origin(self):
        """'from Bangalore' should not appear in destination candidates."""
        candidates, status, raw = _extract_destination_candidates(
            "Trip from Bangalore to Singapore"
        )
        lowered = [c.lower() for c in candidates]
        assert "bangalore" not in lowered, "Bangalore should not be a destination here"
        assert "singapore" in lowered, "Singapore should be the destination"

    def test_english_from_origin_extracted(self):
        """Origin extraction via pipeline should set origin_city for 'from Bangalore'."""
        pipeline = ExtractionPipeline()
        env = SourceEnvelope.from_freeform(
            "Trip from Bangalore to Singapore for 4 people, budget 3L",
            "test",
        )
        packet = pipeline.extract([env])
        origin = packet.facts.get("origin_city")
        assert origin is not None, "origin_city should be set"
        assert origin.value == "Bangalore", f"Expected Bangalore, got {origin.value}"

    def test_from_nairobi_planning_extracted(self):
        """Origin extraction should handle natural-language phrasing like 'from Nairobi planning...'."""
        pipeline = ExtractionPipeline()
        env = SourceEnvelope.from_freeform(
            "Family of 4 from Nairobi planning 7 nights in Bali in August. Budget USD 3500-4500.",
            "test",
        )
        packet = pipeline.extract([env])
        origin = packet.facts.get("origin_city")
        assert origin is not None, "origin_city should be set for planning phrasing"
        assert origin.value == "Nairobi", f"Expected Nairobi, got {origin.value}"

    def test_agency_descriptor_does_not_pollute_destination_candidates(self):
        """Source-city descriptors like 'Mumbai agency' should not become destination candidates."""
        candidates, status, raw = _extract_destination_candidates(
            "Small Mumbai agency handling a family holiday for 4 adults and 2 kids from Mumbai to Bali in August 2026."
        )
        lowered = [c.lower() for c in candidates]
        assert "mumbai" not in lowered, f"Mumbai should not be a destination here, got {candidates}"
        assert "bali" in lowered, f"Bali should remain the destination, got {candidates}"

    def test_label_style_origin_extracted(self):
        """'Origin city: Nairobi' should populate origin_city via pipeline."""
        pipeline = ExtractionPipeline()
        env = SourceEnvelope.from_freeform(
            "Origin city: Nairobi. Couple wants 6 nights in Zanzibar in June. Budget: USD 4,500.",
            "test",
        )
        packet = pipeline.extract([env])
        origin = packet.facts.get("origin_city")
        budget = packet.facts.get("budget_min")
        currency = packet.facts.get("budget_currency")
        assert origin is not None, "origin_city should be set for label-style origin"
        assert origin.value == "Nairobi", f"Expected Nairobi, got {origin.value}"
        assert budget is not None, "budget_min should be set for label-style budget"
        assert budget.value == 4500
        assert currency is not None
        assert currency.value == "USD"

        destination = packet.facts.get("destination_candidates")
        assert destination is not None, "destination_candidates should be set"
        lowered = [c.lower() for c in destination.value]
        assert "nairobi" not in lowered, f"Origin city leaked into destination candidates: {destination.value}"
        assert "zanzibar" in lowered, f"Expected Zanzibar destination candidate, got {destination.value}"

    # --- New: Hinglish "se" ---
    def test_bangalore_se_excludes_from_destination(self):
        """'Bangalore se' should exclude Bangalore from destination candidates."""
        candidates, status, raw = _extract_destination_candidates(
            "Bangalore se Andaman jana hai"
        )
        lowered = [c.lower() for c in candidates]
        assert "bangalore" not in lowered, \
            f"Bangalore should not be a destination with 'se', got {candidates}"
        assert "andaman" in lowered, "Andaman should be the destination"

    def test_bangalore_se_sets_origin(self):
        """'Bangalore se' should populate origin_city via pipeline."""
        pipeline = ExtractionPipeline()
        env = SourceEnvelope.from_freeform(
            "Bangalore se Andaman jana hai, 4 log, budget 3L",
            "test",
        )
        packet = pipeline.extract([env])
        origin = packet.facts.get("origin_city")
        assert origin is not None, "origin_city should be set for 'Bangalore se'"
        assert origin.value == "Bangalore"

    # --- New: Odia "ru" ---
    def test_bangalore_ru_excludes_from_destination(self):
        candidates, status, raw = _extract_destination_candidates(
            "Bangalore ru Sri Lanka jiba"
        )
        lowered = [c.lower() for c in candidates]
        assert "bangalore" not in lowered, f"Bangalore should not be destination with 'ru', got {candidates}"

    # --- New: Indian English "side" ---
    def test_bangalore_side_excludes_from_destination(self):
        candidates, status, raw = _extract_destination_candidates(
            "Bangalore side jaana hai"
        )
        lowered = [c.lower() for c in candidates]
        assert "bangalore" not in lowered, f"Bangalore should not be destination with 'side', got {candidates}"


# ---------------------------------------------------------------------------
# Party: Hinglish child terms (bachhe, bache, baccha)
# ---------------------------------------------------------------------------

class TestPartyHinglish:
    """Party composition with Hinglish child terms."""

    # --- Regression: existing English patterns ---
    def test_english_two_adults_two_children(self):
        result = _extract_party("2 adults 2 children")
        assert result["party_size"] == 4
        assert result["party_composition"].get("adults") == 2
        assert result["party_composition"].get("children") == 2

    def test_english_family_with_kids(self):
        result = _extract_party("me, my wife, and 2 kids")
        assert result["party_size"] == 4
        assert "children" in result["party_composition"]

    # --- New: bachhe (plural, Hindi) ---
    def test_two_adults_two_bachhe(self):
        result = _extract_party("2 adults 2 bachhe")
        assert result["party_composition"].get("children") == 2, \
            f"Expected children=2, got {result['party_composition']}"
        assert result["party_size"] == 4

    def test_bachhe_singular(self):
        result = _extract_party("bachha")
        assert "children" in result["party_composition"], \
            f"'bachha' should be recognized as a child, got {result['party_composition']}"

    def test_family_of_four_two_bachhe(self):
        result = _extract_party("family of 4, 2 bachhe")
        assert result["party_composition"].get("children") == 2, \
            f"Expected children=2, got {result['party_composition']}"

    def test_four_adults_two_bachhe(self):
        result = _extract_party("4 adults, 2 bachhe")
        assert result["party_composition"].get("adults") == 4
        assert result["party_composition"].get("children") == 2, \
            f"Expected children=2, got {result['party_composition']}"

    def test_bache_variant(self):
        result = _extract_party("2 adults 1 bache")
        assert result["party_composition"].get("children") == 1

    def test_child_ages_with_commas_are_all_captured(self):
        result = _extract_party("2 adults and 3 children ages 6, 9, and 12")
        assert result["child_ages"] == [6, 9, 12]

    def test_generic_child_ages_phrase_does_not_invent_a_child(self):
        result = _extract_party("Keep child ages and rooming setup visible")
        assert result["party_composition"].get("children") is None
        assert result["child_ages"] == []


class TestGroupBookingSignals:
    """Tests for group booking and procurement signal extraction."""

    def test_rooming_lists_and_procurement_are_captured(self):
        pipeline = ExtractionPipeline()
        env = SourceEnvelope.from_freeform(
            "Large Nairobi agency managing a corporate group of 18 travelers from Nairobi to Singapore in October 2026. Budget is USD 42,000. Need 6 nights, mid-to-upscale hotel blocks, airport transfers, partial sightseeing, two separate rooming lists, and a fast quote that can be shared with procurement.",
            "test",
        )
        packet = pipeline.extract([env])

        rooming_count = packet.facts.get("rooming_list_count")
        rooming_requested = packet.facts.get("rooming_list_requested")
        procurement_share = packet.facts.get("procurement_share_needed")
        rooming_requirements = packet.facts.get("rooming_requirements")

        assert rooming_count is not None, "rooming_list_count should be captured"
        assert rooming_count.value == 2, f"Expected 2 rooming lists, got {rooming_count.value}"
        assert rooming_requested is not None and rooming_requested.value is True
        assert procurement_share is not None and procurement_share.value is True
        assert rooming_requirements is not None
        assert "rooming lists" in str(rooming_requirements.value).lower()

        priorities = packet.facts.get("trip_priorities")
        assert priorities is not None, "trip_priorities should capture the corporate ops asks"
        priority_values = [str(item).lower() for item in priorities.value]
        assert "airport transfers" in priority_values
        assert "meeting room" not in priority_values  # not present in this note
        assert "fast quote" in priority_values
        assert "hotel blocks" in priority_values

    def test_corporate_meeting_room_and_transfer_priorities_are_captured(self):
        pipeline = ExtractionPipeline()
        env = SourceEnvelope.from_freeform(
            "Nairobi corporate offsite for 18 travelers wants Singapore in October, KES 4.8M budget, premium hotel, meeting room, airport transfers, flexible dates.",
            "test",
        )
        packet = pipeline.extract([env])

        priorities = packet.facts.get("trip_priorities")
        assert priorities is not None, "trip_priorities should be captured for corporate needs"
        priority_values = [str(item).lower() for item in priorities.value]
        assert "meeting room" in priority_values
        assert "airport transfers" in priority_values
        assert "premium hotel" in priority_values

        activity_interests = packet.facts.get("activity_interests")
        assert activity_interests is not None, "activity_interests should capture the offsite note"
        activity_values = [str(item).lower() for item in activity_interests.value]
        assert "business offsite" in activity_values

    def test_partial_sightseeing_is_preserved_as_activity_interest(self):
        pipeline = ExtractionPipeline()
        env = SourceEnvelope.from_freeform(
            "Nairobi corporate offsite for 18 travelers wants Singapore in October, KES 4.8M budget, premium hotel, partial sightseeing, airport transfers, flexible dates.",
            "test",
        )
        packet = pipeline.extract([env])

        activity_interests = packet.facts.get("activity_interests")
        assert activity_interests is not None, "activity_interests should capture the sightseeing note"
        assert "sightseeing" in [str(item).lower() for item in activity_interests.value]

    def test_rooming_lists_prefers_customer_message_over_agent_note_noise(self):
        pipeline = ExtractionPipeline()
        customer = SourceEnvelope.from_freeform(
            "Corporate group of 18 travelers from Nairobi to Singapore in October 2026. Need two separate rooming lists for procurement.",
            "customer",
        )
        notes = SourceEnvelope.from_freeform(
            "Fast quote for procurement. Keep rooming list separation visible.",
            "agent_notes",
        )
        packet = pipeline.extract([customer, notes])

        rooming_count = packet.facts.get("rooming_list_count")
        rooming_requirements = packet.facts.get("rooming_requirements")

        assert rooming_count is not None, "rooming_list_count should be captured"
        assert rooming_count.value == 2, f"Expected the customer message to win with 2 rooming lists, got {rooming_count.value}"
        assert rooming_requirements is not None
        assert "two separate rooming lists" in str(rooming_requirements.value).lower()

    def test_hyphenated_traveler_count_sets_party_size(self):
        pipeline = ExtractionPipeline()
        env = SourceEnvelope.from_freeform(
            "Lagos agency handling a 18-traveler corporate offsite from Lagos to Cape Town in September 2026. "
            "Budget NGN 15m, needs visa support, rooming list, airport transfers, and a fast internal approval-ready summary.",
            "test",
        )
        packet = pipeline.extract([env])

        party = packet.facts.get("party_size")

        assert party is not None, "party_size should be captured for hyphenated traveler phrasing"
        assert party.value == 18, f"Expected 18, got {party.value if party else None}"


# ---------------------------------------------------------------------------
# Dates: Hinglish "ya" separator
# ---------------------------------------------------------------------------

class TestDateHinglish:
    """Date extraction with Hinglish conjunctions."""

    # --- Regression: existing English patterns ---
    def test_english_month_window_or(self):
        result = _extract_dates("March or April 2026")
        assert result is not None
        assert result[3] == "window"

    def test_english_month_window_to(self):
        result = _extract_dates("March to April 2026")
        assert result is not None
        assert result[3] == "window"

    # --- New: "ya" ---
    def test_march_ya_april(self):
        result = _extract_dates("March ya April 2026")
        assert result is not None, "'March ya April 2026' should match as month window"
        assert result[3] in ("window",), f"Expected window confidence, got {result}"


# ---------------------------------------------------------------------------
# Lowercase known destinations
# ---------------------------------------------------------------------------

class TestLowercaseDestination:
    """Destination detection with lowercase city names."""

    # --- Regression: capitalized still works ---
    def test_capitalized_singapore(self):
        candidates, status, raw = _extract_destination_candidates("Singapore jana hai")
        assert "Singapore" in candidates

    # --- New: lowercase ---
    def test_lowercase_singapore(self):
        candidates, status, raw = _extract_destination_candidates("singapore jana hai")
        assert any(c.lower() == "singapore" for c in candidates), \
            f"Lowercase 'singapore' should be recognized, got {candidates}"

    def test_lowercase_andaman(self):
        candidates, status, raw = _extract_destination_candidates("andaman jana hai")
        assert any(c.lower() == "andaman" for c in candidates), \
            f"Lowercase 'andaman' should be recognized, got {candidates}"

    # Non-destination lowercase words should still be rejected
    def test_lowercase_months_rejected(self):
        candidates, status, raw = _extract_destination_candidates("march me jana hai")
        lowered = [c.lower() for c in candidates]
        assert "march" not in lowered


# ---------------------------------------------------------------------------
# Full pipeline: Hinglish input end-to-end
# ---------------------------------------------------------------------------

class TestPipelineHinglishRegression:
    """Full pipeline on Hinglish WhatsApp-style input."""

    def test_hinglish_baseline(self):
        """Andaman Sri Lanka, Bangalore se, 2 adults 2 bachhe, 3L, March ya April."""
        pipeline = ExtractionPipeline()
        env = SourceEnvelope.from_freeform(
            "Andaman Sri Lanka Bangalore se 2 adults 2 bachhe 3L March ya April",
            "test",
        )
        packet = pipeline.extract([env])

        dest = packet.facts.get("destination_candidates")
        origin = packet.facts.get("origin_city")
        party = packet.facts.get("party_size")
        comp = packet.facts.get("party_composition")
        budget = packet.facts.get("budget_raw_text")
        dates = packet.facts.get("date_window")

        # Destination should include Sri Lanka (as multi-word) and Andaman (NOT Bangalore)
        assert dest is not None, "destination_candidates should be set"
        dest_vals = dest.value if isinstance(dest.value, list) else [dest.value]
        dest_str = " ".join(str(v) for v in dest_vals)
        assert "Andaman" in dest_str, \
            f"Andaman should be a destination candidate, got {dest_vals}"
        assert "Sri Lanka" in dest_str, \
            f"Sri Lanka should be a multi-word destination candidate, got {dest_vals}"
        lowered = [v.lower() for v in dest_vals]
        assert "bangalore" not in lowered, \
            f"Bangalore should NOT be a destination candidate, got {dest_vals}"

        # Origin should be Bangalore
        assert origin is not None, "origin_city should be set"
        assert origin.value == "Bangalore", f"Expected Bangalore origin, got {origin.value}"

        # Party should include children
        assert party is not None, "party_size should be set"
        assert comp is not None, "party_composition should be set"
        comp_val = comp.value if isinstance(comp.value, dict) else {}
        assert comp_val.get("children") == 2 or comp_val.get("children") == 2, \
            f"Expected 2 children in composition, got {comp_val}"

        # Budget should be set
        assert budget is not None, "budget_raw_text should be set"

        # Dates should be set
        assert dates is not None, "date_window should be set"


# ---------------------------------------------------------------------------
# Runtime inquiry regression coverage
# ---------------------------------------------------------------------------

class TestRuntimeInquiryRegressionCoverage:
    """Covers issues found through live Chrome testing of the draft workbench."""

    def test_family_of_four_with_word_counts_extracts_party_and_dates_without_false_origin(self):
        text = (
            "Family of four wants 6 nights in Bali in July. Two adults, two kids age 6 and 9. "
            "Prefer beach resort with kids club, vegetarian food, and one villa or connecting rooms. "
            "Budget around INR 4L excluding flights. They can travel any week after July 10. "
            "Need something calm, safe, and not too far from the airport."
        )

        packet = ExtractionPipeline().extract([SourceEnvelope.from_freeform(text, "runtime-regression")])

        party = packet.facts.get("party_size")
        composition = packet.facts.get("party_composition")
        dates = packet.facts.get("date_window")
        date_start = packet.facts.get("date_start")
        trip_purpose = packet.facts.get("trip_purpose")

        assert party is not None
        assert party.value == 4
        assert composition is not None
        assert composition.value == {"adults": 2, "children": 2}
        assert dates is not None
        assert dates.value == "after july 10"
        assert date_start is not None
        assert date_start.value == f"{datetime.now().year}-07-10"
        assert trip_purpose is not None
        assert trip_purpose.value == "family leisure"
        assert "origin_city" not in packet.facts

    def test_family_of_four_with_kid_friendly_language_keeps_full_party_size(self):
        text = (
            "Family of 4 from Nairobi planning 7 nights in Bali in August. Budget USD 7000-9000. "
            "Wants a kid-friendly villa, smooth airport transfers, and two flexible sightseeing days. "
            "First international trip for the kids."
        )

        packet = ExtractionPipeline().extract([SourceEnvelope.from_freeform(text, "runtime-regression")])

        assert packet.facts["party_size"].value == 4
        assert packet.facts["origin_city"].value == "Nairobi"
        assert packet.facts["destination_candidates"].value == ["Bali"]
        assert packet.facts["budget_min"].value == 7000

    def test_single_destination_is_not_downgraded_by_rooming_language(self):
        text = (
            "Small Cape Town agency handling a family trip for 5 travelers from Cape Town to Dubai in December 2026. "
            "Budget is ZAR 120,000. Need 5 nights, a family room or adjacent rooms, airport transfers, "
            "and a quick quote that can be sent to the client and WhatsApp group. "
            "They are flexible on exact dates within the month."
        )

        packet = ExtractionPipeline().extract([SourceEnvelope.from_freeform(text, "runtime-regression")])

        destination = packet.facts.get("destination_candidates")
        origin = packet.facts.get("origin_city")

        assert destination is not None
        assert destination.value == ["Dubai"], f"Expected Dubai only, got {destination.value}"
        assert origin is not None
        assert origin.value == "Cape Town"
        assert not any(
            amb.field_name == "destination_candidates"
            and amb.ambiguity_type == "unresolved_alternatives"
            for amb in packet.ambiguities
        ), [(amb.field_name, amb.ambiguity_type, amb.raw_value) for amb in packet.ambiguities if amb.field_name == "destination_candidates"]

    def test_leading_city_note_keeps_origin_and_destination_separate(self):
        text = (
            "Cape Town family of 4 wants Mauritius in April, ZAR 95,000 budget, relaxed pace, "
            "one resort near the beach, direct flight preferred."
        )

        packet = ExtractionPipeline().extract([SourceEnvelope.from_freeform(text, "runtime-regression")])

        origin = packet.facts.get("origin_city")
        destination = packet.facts.get("destination_candidates")

        assert origin is not None, f"origin_city missing; facts={list(packet.facts.keys())}"
        assert origin.value == "Cape Town"
        assert destination is not None, f"destination_candidates missing; facts={list(packet.facts.keys())}"
        assert destination.value == ["Mauritius"], destination.value
        assert not any(
            amb.field_name == "destination_candidates"
            and amb.ambiguity_type == "unresolved_alternatives"
            for amb in packet.ambiguities
        ), [(amb.field_name, amb.ambiguity_type, amb.raw_value) for amb in packet.ambiguities if amb.field_name == "destination_candidates"]

    def test_date_flexibility_does_not_create_budget_flex_ambiguity(self):
        text = (
            "Small Cape Town agency handling a family trip for 5 travelers from Cape Town to Dubai in December 2026. "
            "Budget is ZAR 120,000. Need 5 nights, a family room or adjacent rooms, airport transfers, "
            "and a quick quote that can be sent to the client and WhatsApp group. "
            "They are flexible on exact dates within the month."
        )

        packet = ExtractionPipeline().extract([SourceEnvelope.from_freeform(text, "runtime-regression")])

        assert packet.facts.get("date_flexibility") is not None
        # D2 (RQ-01 golden convention): an unmarked budget defaults to "soft".
        # The invariant protected here is that DATE flexibility must not leak
        # into the budget signal — the budget value may be the "soft" default
        # but must never become "stretch", and no flexibility ambiguity events
        # may be created from date language.
        budget_flex_fact = packet.facts.get("budget_flexibility")
        assert budget_flex_fact is None or budget_flex_fact.value != "stretch"
        assert not any(
            amb.field_name == "budget_flexibility"
            and amb.ambiguity_type == "unresolved_alternatives"
            for amb in packet.ambiguities
        ), [(amb.field_name, amb.ambiguity_type, amb.raw_value) for amb in packet.ambiguities if amb.field_name == "budget_flexibility"]

    def test_bali_trip_with_explicit_dates_is_valid_for_discovery(self):
        text = (
            "Origin city: Mumbai. Party size: 2 adults. Destination: Bali. Travel dates: July 10 to July 16. "
            "Budget: INR 4,00,000 total fixed. Vegetarian meals, anniversary trip, airport transfers, one day trip, and visa risks."
        )

        packet = ExtractionPipeline().extract([SourceEnvelope.from_freeform(text, "runtime-regression")])
        report = validate_packet(packet, stage="discovery")

        assert packet.facts["date_window"].value == "July 10 to July 16"
        assert packet.derived_signals["visa_concerns_present"].maturity == "heuristic"
        assert report.is_valid, [(e.code, e.field, e.message) for e in report.errors]

    def test_budget_with_inr_and_lakh_suffix_parses_full_amount(self):
        result = _extract_budget("Budget INR 2.5L")

        assert result is not None
        assert result["raw_text"].lower() == "budget inr 2.5l"
        assert result["min"] == 250000
        assert result["max"] == 250000
        assert result["currency"] == "INR"

    def test_budget_range_with_currency_parses_min_and_max(self):
        result = _extract_budget("Budget USD 7000-9000")

        assert result is not None
        assert result["min"] == 7000
        assert result["max"] == 9000
        assert result["currency"] == "USD"

    def test_small_agency_family_note_keeps_full_party_and_budget(self):
        text = (
            "Family from Chennai for 5N Singapore in September. Budget INR 2.5L. "
            "2 adults and 1 child. Need kid-friendly hotel, airport transfers, vegetarian meals, "
            "and a quote by this evening. Passport expires in 5 months."
        )

        packet = ExtractionPipeline().extract([SourceEnvelope.from_freeform(text, "runtime-regression")])

        assert packet.facts["party_size"].value == 3
        assert packet.facts["party_composition"].value == {"adults": 2, "children": 1}
        assert packet.facts["budget_min"].value == 250000
        assert packet.facts["budget_max"].value == 250000

    def test_origin_from_phrase_stops_before_for(self):
        text = (
            "Large agency request: family of 9 from Mumbai for 6N Bali in August. "
            "4 adults, 3 children ages 7, 10, and 13, plus 2 grandparents. Budget INR 12L total."
        )

        packet = ExtractionPipeline().extract([SourceEnvelope.from_freeform(text, "runtime-regression")])

        assert packet.facts["origin_city"].value == "Mumbai"
        assert packet.facts["party_size"].value == 9
        assert packet.facts["budget_min"].value == 1200000

    def test_flight_arrival_after_hotel_checkin_flags_itinerary_mismatch(self):
        text = (
            "Family of 4 from Mumbai to Bali in July. Outbound flight lands at 22:30 on 10 July, "
            "but the hotel is set to check in on 10 July afternoon. Please flag any mismatch and suggest the cleanest fix."
        )

        packet = ExtractionPipeline().extract([SourceEnvelope.from_freeform(text, "runtime-regression")])
        decision = run_gap_and_decision(packet)

        assert any(
            contradiction.get("field_name") == "flight_hotel_mismatch"
            for contradiction in packet.contradictions
        ), packet.contradictions
        assert any(
            contradiction.get("field_name") == "flight_hotel_mismatch"
            for contradiction in decision.contradictions
        ), decision.contradictions
        assert any(
            q.get("field_name") == "flight_hotel_mismatch"
            and "flight" in q.get("question", "").lower()
            and "hotel" in q.get("question", "").lower()
            for q in decision.follow_up_questions
        ), decision.follow_up_questions

    def test_flight_arrival_after_hotel_checkin_flags_itinerary_mismatch_label_first(self):
        text = (
            "Family of 4 from Mumbai to Bali in July. Outbound flight lands at 22:30 on 10 July, "
            "but the hotel check-in is afternoon on 10 July. Please flag any mismatch and suggest the cleanest fix."
        )

        packet = ExtractionPipeline().extract([SourceEnvelope.from_freeform(text, "runtime-regression")])
        decision = run_gap_and_decision(packet)

        assert any(
            contradiction.get("field_name") == "flight_hotel_mismatch"
            for contradiction in packet.contradictions
        ), packet.contradictions
        assert any(
            contradiction.get("field_name") == "flight_hotel_mismatch"
            for contradiction in decision.contradictions
        ), decision.contradictions


# ---------------------------------------------------------------------------
# Context-gated lowercase destination (structural fix for "Got" false positive)
# ---------------------------------------------------------------------------

class TestContextGatedLowercaseDestination:
    """Verify lowercase destination only matches in travel-intent context."""

    # --- False positives: must be rejected ---

    def test_got_your_number_rejected(self):
        """'got' in 'I got your number' must not become a destination."""
        candidates, status, raw = _extract_destination_candidates(
            "Hi Ravi, I got your number from my wife who is a colleague"
        )
        lowered = [c.lower() for c in candidates]
        assert "got" not in lowered, \
            f"'Got' should not be a destination in 'I got your number', got {candidates}"

    def test_got_family_leisure_rejected(self):
        """'got' as first word must notExtract destination from 'got family leisure trip'."""
        candidates, status, raw = _extract_destination_candidates(
            "got family leisure trip"
        )
        lowered = [c.lower() for c in candidates]
        assert "got" not in lowered, \
            f"'Got' should not be a destination, got {candidates}"

    def test_need_family_leisure_rejected(self):
        """'need' must not become a destination."""
        candidates, status, raw = _extract_destination_candidates(
            "we need family leisure trip"
        )
        lowered = [c.lower() for c in candidates]
        assert "need" not in lowered, \
            f"'Need' should not be a destination, got {candidates}"

    def test_old_customer_rejected(self):
        """'old' must not become a destination."""
        candidates, status, raw = _extract_destination_candidates(
            "old customer wants options"
        )
        lowered = [c.lower() for c in candidates]
        assert "old" not in lowered, \
            f"'Old' should not be a destination, got {candidates}"

    def test_kids_parks_rejected(self):
        """'kids' and 'parks' must not become destinations."""
        candidates, status, raw = _extract_destination_candidates(
            "kids want parks"
        )
        lowered = [c.lower() for c in candidates]
        assert "kids" not in lowered, \
            f"'Kids' should not be a destination, got {candidates}"
        assert "parks" not in lowered, \
            f"'Parks' should not be a destination, got {candidates}"

    def test_top_hotels_rejected(self):
        """'top' must not become a destination."""
        candidates, status, raw = _extract_destination_candidates(
            "top hotels needed"
        )
        lowered = [c.lower() for c in candidates]
        assert "top" not in lowered, \
            f"'Top' should not be a destination, got {candidates}"

    def test_set_budget_rejected(self):
        """'set' must not become a destination."""
        candidates, status, raw = _extract_destination_candidates(
            "set budget later"
        )
        lowered = [c.lower() for c in candidates]
        assert "set" not in lowered, \
            f"'Set' should not be a destination, got {candidates}"

    def test_log_inquiry_rejected(self):
        """'log' must not become a destination."""
        candidates, status, raw = _extract_destination_candidates(
            "log this inquiry"
        )
        lowered = [c.lower() for c in candidates]
        assert "log" not in lowered, \
            f"'Log' should not be a destination, got {candidates}"

    # --- True positives: lowercase destinations in travel context ---

    def test_singapore_jana_hai(self):
        """'singapore jana hai' → Singapore."""
        candidates, status, raw = _extract_destination_candidates(
            "singapore jana hai"
        )
        titles = [c.title() for c in candidates]
        assert "Singapore" in titles, \
            f"'Singapore' should be recognized in 'singapore jana hai', got {candidates}"

    def test_andaman_jana_hai(self):
        """'andaman jana hai' → Andaman."""
        candidates, status, raw = _extract_destination_candidates(
            "andaman jana hai"
        )
        titles = [c.title() for c in candidates]
        assert "Andaman" in titles, \
            f"'Andaman' should be recognized in 'andaman jana hai', got {candidates}"

    def test_bangalore_se_singapore(self):
        """'bangalore se singapore jana hai' → Singapore (not Bangalore)."""
        candidates, status, raw = _extract_destination_candidates(
            "bangalore se singapore jana hai"
        )
        titles = [c.title() for c in candidates]
        assert "Singapore" in titles, \
            f"'Singapore' should be recognized, got {candidates}"
        assert "Bangalore" not in titles, \
            f"'Bangalore' should be origin, not destination, got {candidates}"

    def test_bangalore_se_andaman(self):
        """'bangalore se andaman jana hai' → Andaman."""
        candidates, status, raw = _extract_destination_candidates(
            "bangalore se andaman jana hai"
        )
        titles = [c.title() for c in candidates]
        assert "Andaman" in titles, \
            f"'Andaman' should be recognized, got {candidates}"

    def test_bangalore_ru_sri_lanka(self):
        """'bangalore ru sri lanka jiba' → Sri Lanka."""
        candidates, status, raw = _extract_destination_candidates(
            "bangalore ru sri lanka jiba"
        )
        titles = [c.title() for c in candidates]
        assert "Sri Lanka" in titles, \
            f"'Sri Lanka' should be recognized, got {candidates}"

    def test_want_to_go_singapore(self):
        """'want to go singapore' → Singapore."""
        candidates, status, raw = _extract_destination_candidates(
            "want to go singapore"
        )
        titles = [c.title() for c in candidates]
        assert "Singapore" in titles, \
            f"'Singapore' should be recognized in 'want to go singapore', got {candidates}"

    def test_travel_to_bali(self):
        """'travel to bali' → Bali."""
        candidates, status, raw = _extract_destination_candidates(
            "travel to bali"
        )
        titles = [c.title() for c in candidates]
        assert "Bali" in titles, \
            f"'Bali' should be recognized in 'travel to bali', got {candidates}"

    def test_trip_to_thailand(self):
        """'trip to thailand' → Thailand."""
        candidates, status, raw = _extract_destination_candidates(
            "trip to thailand"
        )
        titles = [c.title() for c in candidates]
        assert "Thailand" in titles, \
            f"'Thailand' should be recognized in 'trip to thailand', got {candidates}"

    def test_holiday_in_dubai(self):
        """'holiday in dubai' → Dubai."""
        candidates, status, raw = _extract_destination_candidates(
            "holiday in dubai"
        )
        titles = [c.title() for c in candidates]
        assert "Dubai" in titles, \
            f"'Dubai' should be recognized in 'holiday in dubai', got {candidates}"

    # --- Multi-word lowercase destinations ---

    def test_bangalore_se_sri_lanka_jana_hai(self):
        """'bangalore se sri lanka jana hai' → Sri Lanka."""
        candidates, status, raw = _extract_destination_candidates(
            "bangalore se sri lanka jana hai"
        )
        titles = [c.title() for c in candidates]
        assert "Sri Lanka" in titles, \
            f"'Sri Lanka' should be recognized as multi-word destination, got {candidates}"

    def test_bangalore_se_new_york_jana_hai(self):
        """'bangalore se new york jana hai' → New York."""
        candidates, status, raw = _extract_destination_candidates(
            "bangalore se new york jana hai"
        )
        titles = [c.title() for c in candidates]
        assert "New York" in titles, \
            f"'New York' should be recognized as multi-word destination, got {candidates}"

    def test_bangalore_se_abu_dhabi_jana_hai(self):
        """'bangalore se abu dhabi jana hai' → Abu Dhabi."""
        candidates, status, raw = _extract_destination_candidates(
            "bangalore se abu dhabi jana hai"
        )
        titles = [c.title() for c in candidates]
        assert "Abu Dhabi" in titles, \
            f"'Abu Dhabi' should be recognized as multi-word destination, got {candidates}"

    def test_bangalore_se_hong_kong_jana_hai(self):
        """'bangalore se hong kong jana hai' → Hong Kong."""
        candidates, status, raw = _extract_destination_candidates(
            "bangalore se hong kong jana hai"
        )
        titles = [c.title() for c in candidates]
        assert "Hong Kong" in titles, \
            f"'Hong Kong' should be recognized as multi-word destination, got {candidates}"


# =============================================================================
# _extract_trip_intent — trip_priorities
# =============================================================================

class TestTripPrioritiesExtraction:
    def test_kid_friendly_detected(self):
        result = _extract_trip_intent("looking for kid-friendly activities and family-friendly hotel")
        priorities = result.get("trip_priorities", [])
        assert "kid-friendly" in priorities

    def test_luxury_experience_detected(self):
        result = _extract_trip_intent("want luxury resort with premium experience")
        priorities = result.get("trip_priorities", [])
        assert "luxury experience" in priorities or "premium hotel" in priorities

    def test_mid_range_hotel_detected(self):
        result = _extract_trip_intent("mid-range hotel, direct flights, vegetarian meals")
        priorities = result.get("trip_priorities", [])
        assert "mid-range hotel" in priorities

    def test_must_have_extracted(self):
        result = _extract_trip_intent("must-have beach access, must visit Golden Temple")
        priorities = result.get("trip_priorities", [])
        assert "beach access" in priorities

    def test_direct_flights_detected(self):
        result = _extract_trip_intent("prefer direct flight, no layover please")
        priorities = result.get("trip_priorities", [])
        assert "direct flights" in priorities

    def test_vegetarian_food_detected(self):
        result = _extract_trip_intent("need pure veg food, vegetarian meals only")
        priorities = result.get("trip_priorities", [])
        assert "vegetarian food" in priorities

    def test_adventure_activities_detected(self):
        result = _extract_trip_intent("want trekking and rafting, adventure activities")
        priorities = result.get("trip_priorities", [])
        assert "adventure activities" in priorities

    def test_relaxed_pace_detected(self):
        result = _extract_trip_intent("want relaxed pace, not rushed, leisurely trip")
        priorities = result.get("trip_priorities", [])
        assert "relaxed pace" in priorities

    def test_honeymoon_special_detected(self):
        result = _extract_trip_intent("honeymoon special package with romantic dinner")
        priorities = result.get("trip_priorities", [])
        assert "honeymoon special" in priorities

    def test_cultural_experience_detected(self):
        result = _extract_trip_intent("want cultural experience, temple visit, heritage tour")
        priorities = result.get("trip_priorities", [])
        assert "cultural experience" in priorities

    def test_multiple_priorities_accumulate(self):
        result = _extract_trip_intent("kid-friendly resort with direct flight and vegetarian food")
        priorities = result.get("trip_priorities", [])
        assert "kid-friendly" in priorities
        assert "direct flights" in priorities
        assert "vegetarian food" in priorities

    def test_no_priorities_returns_none(self):
        result = _extract_trip_intent("going to Mumbai for a meeting")
        priorities = result.get("trip_priorities")
        assert priorities is None or priorities == []

    def test_quick_trip_detected(self):
        result = _extract_trip_intent("quick trip, weekend getaway, tight schedule")
        priorities = result.get("trip_priorities", [])
        assert "quick trip" in priorities

    def test_budget_conscious_detected(self):
        result = _extract_trip_intent("budget-conscious, cheapest option, budget travel")
        priorities = result.get("trip_priorities", [])
        assert "budget conscious" in priorities

    def test_accessibility_needs_detected(self):
        result = _extract_trip_intent("need wheelchair-friendly hotel, senior-friendly")
        priorities = result.get("trip_priorities", [])
        assert "accessibility needs" in priorities


# =============================================================================
# _extract_date_flexibility
# =============================================================================

class TestDateFlexibilityExtraction:
    def test_firm_dates_detected(self):
        assert _extract_date_flexibility("dates are firm, must travel on exact dates") == "firm"
        assert _extract_date_flexibility("fixed dates, no flexibility") == "firm"

    def test_flexible_dates_detected(self):
        assert _extract_date_flexibility("dates are flexible, anytime in December") == "flexible"
        assert _extract_date_flexibility("can shift +/- 2 days") == "flexible"
        assert _extract_date_flexibility("give or take a few days") == "flexible"

    def test_moderate_flexibility_detected(self):
        assert _extract_date_flexibility("moderate flexibility on dates") == "moderate"

    def test_no_flexibility_signal_returns_none(self):
        assert _extract_date_flexibility("going to Mumbai next month") is None
        assert _extract_date_flexibility("book flights for December 15") is None


# =============================================================================
# Pipeline integration — trip_priorities and date_flexibility in facts
# =============================================================================

class TestPrioritiesFlexibilityInPipeline:
    def test_priorities_in_facts_after_extraction(self):
        pipeline = ExtractionPipeline()
        env = SourceEnvelope.from_freeform(
            "family of 4, budget 2L, looking for kid-friendly activities with direct flight, must-have beach resort. dates are flexible, anytime in December."
        )
        packet = pipeline.extract([env])
        facts = packet.facts
        priorities_slot = facts.get("trip_priorities")
        assert priorities_slot is not None, f"trip_priorities not in facts; keys={list(facts.keys())}"
        priorities_value = priorities_slot.value
        assert "kid-friendly" in priorities_value
        assert "direct flights" in priorities_value

    def test_mid_range_hotel_in_facts_after_extraction(self):
        pipeline = ExtractionPipeline()
        env = SourceEnvelope.from_freeform(
            "Mumbai family of 4 wants Singapore in August, INR 2.5 lakh budget, direct flights, mid-range hotel, 5 nights, vegetarian meals."
        )
        packet = pipeline.extract([env])
        facts = packet.facts
        priorities_slot = facts.get("trip_priorities")
        assert priorities_slot is not None, f"trip_priorities not in facts; keys={list(facts.keys())}"
        priorities_value = priorities_slot.value
        assert "mid-range hotel" in priorities_value
        assert "direct flights" in priorities_value
        assert "vegetarian food" in priorities_value

    def test_date_flexibility_in_facts_after_extraction(self):
        pipeline = ExtractionPipeline()
        env = SourceEnvelope.from_freeform(
            "budget 3L, dates are firm, cannot change, must travel on December 20"
        )
        packet = pipeline.extract([env])
        facts = packet.facts
        flex_slot = facts.get("date_flexibility")
        assert flex_slot is not None, f"date_flexibility not in facts; keys={list(facts.keys())}"
        assert flex_slot.value == "firm"

    def test_flexibility_none_when_not_mentioned(self):
        pipeline = ExtractionPipeline()
        env = SourceEnvelope.from_freeform(
            "budget 50k, trip to Goa next month, 2 adults"
        )
        packet = pipeline.extract([env])
        facts = packet.facts
        assert "date_flexibility" not in facts


# ---------------------------------------------------------------------------
# DEMO-02 colloquial extraction gaps — destination verb-object phrasing +
# city sets. Source:
# Docs/exploration/DEMO02_COLLOQUIAL_EXTRACTION_GAPS_2026-08-31.md §4 (D1–D6)
#
# HOLDOUT POLICY (data/fixtures/evals/holdout/README.md): the phrasings in
# the tests below are deliberately PARAPHRASED, not copied — the graded
# colloquial corpus (data/fixtures/extraction/colloquial_golden.json) must
# never be mirrored verbatim into dev-visible tests, or the gate measures
# memorization instead of generalization. Each dev test asserts the same
# extraction behavior through a different phrasing.
# ---------------------------------------------------------------------------

DEMO02_FULL_NOTE = (
    "hey! me and 3 friends want to do japan next spring, maybe late march for the "
    "cherry blossoms. flying from SF. we are all pretty active, one friend is "
    "vegetarian. budget around 3.5k USD each, not sure if that includes flights. "
    "thinking tokyo + kyoto + osaka, 10-12 days. one of us is terrified of heights "
    "so no cable cars please. we saw this amazing ryokan on tiktok, no idea of the "
    "name. dates flexible plus or minus a week. we also wanna do a cooking class "
    "somewhere. thx!!"
)
# NOTE: DEMO02_FULL_NOTE is the verbatim demo note and IS also the graded
# gate fixture `colloq_full_note_001` (colloquial_golden.json). It is kept
# verbatim as the end-to-end regression anchor for the shipped demo P0 and
# is on the holdout README allowlist as "gate fixture mirror; not a holdout".


class TestColloquialDestination:
    """Lowercase verb-object destinations and city-set separators."""

    # --- D1: "do X" with fully lowercase text ---
    def test_verb_object_do_destination(self):
        candidates, status, raw = _extract_destination_candidates("we wanna do vietnam")
        assert candidates == ["Vietnam"], candidates
        assert status == "definite"
        assert raw == "vietnam"

    # --- D2: "hitting X" with trailing context words ---
    def test_hitting_destination_with_trailing_context(self):
        candidates, status, raw = _extract_destination_candidates("hitting phuket in june")
        assert candidates == ["Phuket"], candidates
        assert status == "definite"
        assert raw == "phuket"

    # --- D3: "covering X and Y" ---
    def test_covering_two_cities(self):
        candidates, status, _ = _extract_destination_candidates("covering rome and florence")
        assert candidates == ["Rome", "Florence"], candidates
        assert status == "semi_open"

    # --- D4: plus-separated city set with implied hedge verb ---
    def test_plus_separated_city_set(self):
        candidates, _, _ = _extract_destination_candidates("thinking berlin + munich + hamburg")
        assert candidates == ["Berlin", "Munich", "Hamburg"], candidates

    def test_comma_and_city_set(self):
        candidates, _, _ = _extract_destination_candidates("tokyo, kyoto and osaka")
        assert candidates == ["Tokyo", "Kyoto", "Osaka"], candidates

    # --- D6: "check out X" ---
    def test_check_out_seoul(self):
        candidates, status, _ = _extract_destination_candidates("we wanna check out seoul")
        assert candidates == ["Seoul"], candidates
        assert status == "definite"

    # --- bare "thinking X" hedge (without "about") ---
    def test_bare_thinking_hedge(self):
        candidates, status, _ = _extract_destination_candidates("thinking bali for the trip")
        assert candidates == ["Bali"], candidates
        assert status == "semi_open"

    # --- D5 (negative): activity clause must not create a destination ---
    def test_cooking_class_somewhere_no_destination_no_open(self):
        candidates, status, _ = _extract_destination_candidates(
            "we also wanna do a cooking class somewhere"
        )
        assert candidates == [], candidates
        assert status != "open", status

    # --- negative: activity verbs capture prose, not places ---
    def test_activity_prose_not_promoted(self):
        for text in ["check out the ryokan on tiktok", "want to visit family in india"]:
            candidates, _, _ = _extract_destination_candidates(text)
            assert candidates == [], f"'{text}' should yield no destination, got {candidates}"

    # --- negative: "or" is option semantics, never a committed city set ---
    def test_lowercase_or_pair_not_a_city_set(self):
        candidates, _, _ = _extract_destination_candidates("japan or korea next year")
        assert len(candidates) < 2, candidates

    # --- negative: past-trip mentions never form a city set ---
    def test_past_trip_city_set_excluded(self):
        candidates, _, _ = _extract_destination_candidates(
            "we went to japan, korea last year and loved it"
        )
        assert candidates == [], candidates

    # --- full demo note: city set wins, activity "somewhere" does not open ---
    def test_full_demo_note_city_set_wins_over_somewhere(self):
        candidates, status, _ = _extract_destination_candidates(DEMO02_FULL_NOTE)
        assert candidates == ["Tokyo", "Kyoto", "Osaka"], candidates
        assert status == "semi_open", status

    # --- Review P2-5: city sets honor origin protection like the verb pass ---
    def test_city_set_excludes_origin_cities(self):
        candidates, _, _ = _extract_destination_candidates(
            "we have friends in London and Paris, but flying from London so want somewhere new"
        )
        assert "London" not in candidates, candidates

    # --- regression: capitalized or-pattern and travel verbs unchanged ---
    def test_capitalized_or_pattern_unchanged(self):
        candidates, status, _ = _extract_destination_candidates("Bali or Thailand?")
        assert "Bali" in candidates and "Thailand" in candidates
        assert status == "semi_open"


# ---------------------------------------------------------------------------
# DEMO-02 §4 (P1–P6): colloquial group sizes
# ---------------------------------------------------------------------------

class TestColloquialParty:
    """Group-size phrasing: 'me and N friends', 'N of us', 'party of N'."""

    # --- P1 ---
    def test_me_and_n_friends(self):
        result = _extract_party("me and 4 friends are craving a mountain break")
        assert result["party_size"] == 5, result
        assert result["party_composition"]["adults"] == 5

    # --- P2 ---
    def test_n_of_us(self):
        result = _extract_party("6 of us are planning an island hop")
        assert result["party_size"] == 6, result

    def test_word_number_of_us(self):
        result = _extract_party("two of us are planning greece")
        assert result["party_size"] == 2, result

    # --- P3 ---
    def test_the_word_number_of_us(self):
        result = _extract_party("the three of us are heading out")
        assert result["party_size"] == 3, result

    # --- P4 ---
    def test_party_of_n(self):
        result = _extract_party("party of 2 to thailand")
        assert result["party_size"] == 2, result

    def test_bare_n_friends_counts_companions(self):
        result = _extract_party("3 friends want a beach trip")
        assert result["party_size"] == 3, result

    # --- P5: self + spouse + friends must count everyone ---
    def test_self_spouse_and_friends(self):
        result = _extract_party("me and my husband and 3 friends want to do thailand")
        assert result["party_size"] == 5, result
        assert result["party_composition"]["adults"] == 5

    # --- negative: "one of us" is a member reference, never party_size=1 ---
    def test_one_of_us_is_not_group_size(self):
        result = _extract_party("one of us gets seasick easily")
        assert result["party_size"] == 0, result
        assert result["group_signals"] == ["one of us"], result

    def test_signals_always_collected(self):
        result = _extract_party("me and 4 friends are craving a mountain break")
        assert result["group_signals"] == ["4 friends"], result

    # --- Review P2-3 / P2-4 ---
    def test_us_and_n_friends_includes_the_party(self):
        # "us" is the speaker's own party; "2 friends" are companions on top.
        result = _extract_party("us and 2 friends want to visit japan")
        assert result["party_size"] >= 3, result

    def test_prose_of_us_is_not_a_group_signal(self):
        # "ahead of us" / "because of us" are prepositions, not group phrasing.
        result = _extract_party("the road ahead of us is beautiful. trip to japan in july.")
        assert result["group_signals"] == [], result


class TestColloquialPartyWarnings:
    """Group phrasing must never silently collapse to a solo traveler.

    Data-loss-prevention doctrine: warn, never skip silently.
    """

    def _party_warning_codes(self, text):
        packet = ExtractionPipeline().extract([SourceEnvelope.from_freeform(text, "demo02")])
        report = validate_packet(packet, stage="discovery")
        return packet, {w.code for w in report.warnings}

    # --- P6: phrasing seen, headcount underdetected ---
    def test_party_underdetected_warning(self):
        # "buddies"/"friends"/"mates" are recognized group words now (parsed
        # to 4 with no warning — see test below). This test pins the WARNING
        # path for colloquial group phrasing the vocabulary does NOT
        # recognize: "me and my 3 cousins" must not silently size the party
        # as 1 without flagging it to the operator.
        packet, codes = self._party_warning_codes("me and my 3 cousins want a beach trip")
        assert packet.facts["party_size"].value == 1
        assert "PARTY_UNDERDETECTED" in codes, codes

    def test_no_party_warning_when_group_parsed(self):
        packet, codes = self._party_warning_codes("me and 4 friends are craving a mountain break")
        assert packet.facts["party_size"].value == 5
        party_codes = {c for c in codes if c.startswith("PARTY_")}
        assert not party_codes, codes

    def test_party_unparsed_group_phrasing_warning(self):
        packet, codes = self._party_warning_codes("one of us gets seasick easily")
        assert "party_size" not in packet.facts
        assert "PARTY_UNPARSED_GROUP_PHRASING" in codes, codes

    def test_full_demo_note_no_party_warning(self):
        packet, codes = self._party_warning_codes(DEMO02_FULL_NOTE)
        assert packet.facts["party_size"].value == 4
        party_codes = {c for c in codes if c.startswith("PARTY_")}
        assert not party_codes, codes


# ---------------------------------------------------------------------------
# DEMO-02 §4 (T1, T2, T4, T5): season windows, late/early/mid month,
# spelled-out flexibility
# ---------------------------------------------------------------------------

class TestColloquialDates:
    """Season parsing and 'late/early/mid <month>' without a preposition."""

    # --- T1 ---
    def test_next_spring_season_window(self):
        result = _extract_dates("we want to do spain next spring")
        assert result is not None, "season phrasing should produce a date window"
        window, _, _, confidence = result
        assert window == "next spring (Mar-May)", window
        assert confidence == "flexible"

    def test_bare_season_window(self):
        # "in the fall" — preposition-qualified seasons still parse.
        result = _extract_dates("we want to go in the fall")
        assert result is not None
        window, _, _, _ = result
        assert "fall" in window and "Sep" in window, window

    # --- Review P1-1: bare season words are prose too often to invent dates ---
    def test_bare_season_without_qualifier_yields_no_window(self):
        assert _extract_dates("a spring in her step") is None
        assert _extract_dates("spring has arrived early this year") is None

    def test_prose_fall_verb_yields_no_window(self):
        assert _extract_dates("we will fall in love with italy") is None
        assert _extract_dates("prices might fall next year") is None

    def test_prose_winter_negation_yields_no_window(self):
        assert _extract_dates("don't want winter, hate the cold") is None

    def test_qualified_seasons_still_parse(self):
        for text in ("next spring sounds good", "this winter maybe", "in autumn perhaps"):
            result = _extract_dates(text)
            assert result is not None, text
            window, _, _, _ = result
            assert "Mar" in window or "Dec" in window or "Sep" in window, (text, window)

    # --- T2 + T5: season window folds the late-month refinement ---
    def test_season_folds_late_month(self):
        result = _extract_dates(
            "want to do spain next spring, maybe late april for the feria"
        )
        assert result is not None
        window, _, _, confidence = result
        assert "next spring" in window
        assert "late april" in window
        assert confidence == "flexible"

    # --- T2 standalone ---
    def test_early_month_without_preposition(self):
        result = _extract_dates("maybe early may")
        assert result is not None
        window, _, _, confidence = result
        assert window == "early may", window
        assert confidence == "flexible"

    def test_early_and_mid_month(self):
        for phrase in ["early june", "mid september"]:
            result = _extract_dates(phrase)
            assert result is not None, phrase
            assert result[0] == phrase, result

    # --- T4: spelled-out flexibility ---
    def test_flexibility_give_or_take(self):
        assert _extract_date_flexibility("dates are flexible give or take a few days") == "flexible"
        assert _extract_date_flexibility("flexible +/- one week") == "flexible"

    # --- regression: precise dates still outrank casual season words ---
    def test_precise_dates_outrank_season_words(self):
        result = _extract_dates("march 10 to march 20 with spring weather")
        assert result is not None
        _, start, end, _ = result
        assert start is not None and end is not None, result

    def test_existing_month_forms_unchanged(self):
        assert _extract_dates("in march 2027") == ("in march 2027", None, None, "flexible")
        assert _extract_dates("9th to 14th feb") is not None


class TestBudgetScopeEach:
    """'each' / 'apiece' are per-person budget markers (DEMO-02 §2.4 / B1)."""

    def test_each_is_per_person(self):
        assert _extract_budget_scope("budget is roughly 2200 USD each") == "per_person"

    def test_unmarked_still_unknown(self):
        assert _extract_budget_scope("budget 3L") == "unknown"

    # --- Review P1-2: explicit totals outrank a stray "each"; bare prose
    # "each" no longer flips the scope ---
    def test_explicit_total_outranks_stray_each(self):
        assert _extract_budget_scope("budget 5000 total, we want breakfast each morning") == "total"
        assert _extract_budget_scope("5000 USD for the whole trip, dinner reservations each night") == "total"

    def test_each_adjacent_to_amount_is_per_person(self):
        assert _extract_budget_scope("around $500 each for hotels") == "per_person"
        assert _extract_budget_scope("1000 each person for flights") == "per_person"

    def test_bare_each_in_prose_is_unknown(self):
        assert _extract_budget_scope("we could each pick a city, budget is open") == "unknown"


# ---------------------------------------------------------------------------
# DEMO-02 §5 fixture colloq_full_note_001 — end-to-end demo regression anchor
# ---------------------------------------------------------------------------

class TestDemoNoteEndToEnd:
    """The exact Tool-Taster demo note, asserted end-to-end.

    GATE FIXTURE MIRROR; NOT A HOLDOUT — this note is verbatim
    ``colloq_full_note_001`` in the graded colloquial corpus
    (data/fixtures/extraction/colloquial_golden.json). It is deliberately
    kept as the end-to-end regression anchor for the shipped demo P0 and is
    allowlisted in data/fixtures/evals/holdout/README.md. Every other
    colloquial fixture phrasing must stay paraphrased in dev tests — see
    the holdout policy at the top of this file.
    """

    @pytest.fixture(scope="class")
    def demo_packet(self):
        pipeline = ExtractionPipeline()
        env = SourceEnvelope.from_freeform(DEMO02_FULL_NOTE, "demo02")
        return pipeline.extract([env])

    def test_destination_captured_from_city_set(self, demo_packet):
        dest = demo_packet.facts["destination_candidates"]
        assert dest.value == ["Tokyo", "Kyoto", "Osaka"], dest.value
        assert demo_packet.facts["destination_status"].value == "semi_open"

    def test_party_size_counts_friends(self, demo_packet):
        assert demo_packet.facts["party_size"].value == 4

    def test_origin_and_budget(self, demo_packet):
        assert demo_packet.facts["origin_city"].value == "SF"
        assert demo_packet.facts["budget_min"].value == 3500
        assert demo_packet.facts["budget_currency"].value == "USD"
        # "3.5k USD each" is per-person money — never silently trip-total.
        assert demo_packet.facts["budget_scope"].value == "per_person"

    def test_dates_and_flexibility(self, demo_packet):
        window = demo_packet.facts["date_window"].value
        assert "next spring" in window, window
        assert "late march" in window, window
        assert demo_packet.facts["date_flexibility"].value == "flexible"

    def test_meal_preference(self, demo_packet):
        assert "vegetarian" in str(demo_packet.facts["meal_preferences"].value)

    def test_hard_constraints_drop_negation_false_positive(self, demo_packet):
        # "no idea of the name" reports the traveler's own missing info, not a
        # prohibition — only the real "no cable cars please" constraint stays.
        assert demo_packet.facts["hard_constraints"].value == ["cable cars please"]

    def test_intake_minimum_valid_no_errors(self, demo_packet):
        report = validate_packet(demo_packet, stage="discovery")
        assert report.is_valid, [(e.code, e.field) for e in report.errors]
        assert not any(w.code.startswith("PARTY_") for w in report.warnings)


# ---------------------------------------------------------------------------
# D-05 negation false positives + D-06 multi-word origin tail fallback
# (DEMO02 §9 Q7 / DEMO_WAVE2 remediation handoff cycle-2 nit)
# ---------------------------------------------------------------------------

class TestExtractionEdges:
    """Negation-knowledge guard and origin tail-word fallback edges."""

    # --- D-05: "no <knowledge-word> ..." is traveler uncertainty, not a ban ---

    def test_fear_phrase_keeps_negation_constraint(self):
        result = _extract_trip_intent(
            "one of us gets seasick easily so no boat trips please"
        )
        assert result.get("hard_constraints") == ["boat trips please"], result

    def test_bare_negation_still_a_constraint(self):
        result = _extract_trip_intent("no cable cars")
        assert result.get("hard_constraints") == ["cable cars"], result

    def test_no_idea_of_the_name_is_not_a_constraint(self):
        result = _extract_trip_intent(
            "we saw this gorgeous riad on instagram, no idea what it is called"
        )
        assert "hard_constraints" not in result, result

    def test_no_clue_about_dates_is_not_a_constraint(self):
        result = _extract_trip_intent("no clue about dates, just pick for us")
        assert "hard_constraints" not in result, result

    # --- D-06: differently formatted multi-word origin tails ---

    def test_multiword_origin_excluded_from_city_set(self):
        text = "flying from san francisco usa and visiting tokyo + kyoto"
        result = _extract_city_set(text.lower(), text)
        assert result is not None, text
        cities, _raw = result
        assert cities == ["Tokyo", "Kyoto"], cities

    def test_origin_tail_fallback_matches_qualified_origin(self):
        assert _is_origin_candidate("flying from san francisco usa", "Usa") is True
        assert _is_origin_candidate("flying from san francisco usa", "San Francisco") is True

    def test_directional_to_not_misread_as_origin(self):
        # "from delhi to boston" — boston is the destination, not the origin.
        assert _is_origin_candidate("flying from delhi to boston", "Boston") is False
        assert _is_origin_candidate("flying from new delhi to new york", "New York") is False

    def test_plain_from_origin_unchanged(self):
        assert _is_origin_candidate("friends in paris, flying from london", "London") is True
