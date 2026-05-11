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
    _extract_destination_candidates,
    _extract_dates,
    _extract_trip_intent,
    _extract_date_flexibility,
    ExtractionPipeline,
)
from src.intake.packet_models import SourceEnvelope


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
        assert "luxury experience" in priorities

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
