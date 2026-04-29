"""
Geography database tests.

Test the city recognition from combined GeoNames + world-cities.json datasets.
"""

import sys
import os

# Ensure src/ is on the path (consistent with other test files)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
import uuid


class TestCityRecognition:
    """Test that known cities are recognized."""

    def test_major_indian_cities_recognized(self):
        """Major Indian cities should be recognized."""
        from intake.geography import is_known_city

        major_cities = [
            "Bangalore", "Bengaluru", "Mumbai", "Delhi", "Chennai",
            "Hyderabad", "Kolkata", "Pune", "Jaipur", "Goa",
            "Ahmedabad", "Udaipur", "Mysore",
        ]

        for city in major_cities:
            assert is_known_city(city), f"{city} should be recognized"

    def test_major_international_destinations_recognized(self):
        """Popular international destinations should be recognized."""
        from intake.geography import is_known_city

        destinations = [
            "Singapore", "Bangkok", "Dubai", "Male",  # Male is capital of Maldives
            "Paris", "London", "New York", "Tokyo", "Bali",
            # Note: Thailand, Maldives are countries, not cities
        ]

        for city in destinations:
            assert is_known_city(city), f"{city} should be recognized"

    def test_smaller_indian_tourist_spots_recognized(self):
        """Smaller Indian tourist destinations (often missed by major-city lists)."""
        from intake.geography import is_known_city

        spots = [
            "Munnar", "Pushkar", "Hampi", "Ooty",
            "Rishikesh", "Leh",
            # Note: Coorg is a region (Kodagu district), not a city
            # Andaman/Ladakh are territories, not cities
        ]

        for spot in spots:
            assert is_known_city(spot), f"{spot} should be recognized (often missed by basic lists)"

    def test_blacklisted_terms_not_recognized_as_cities(self):
        """Common travel words should NOT be recognized as cities."""
        from intake.geography import is_known_city

        non_cities = [
            "from", "starting", "departing", "via", "next",
            "trip", "vacation", "holiday", "booking", "destination",
        ]

        for term in non_cities:
            assert not is_known_city(term), f"{term} should NOT be recognized as a city"

    def test_case_sensitive_recognition(self):
        """City lookup is case-insensitive because _build_union normalizes to lowercase.

        is_known_city() lowercases input and compares against a pre-lowered set,
        so both "Bangalore" and "bangalore" match. is_known_city_normalized()
        provides the same case-insensitive behavior with explicit documentation.
        """
        from intake.geography import is_known_city, is_known_city_normalized

        # Proper case works
        assert is_known_city("Singapore")
        assert is_known_city("Bangalore")
        assert is_known_city("Mumbai")

        # Lowercase also works (implementation normalizes to lowercase)
        assert is_known_city("bangalore")
        assert is_known_city("singapore")

        # Normalized version also works for any case
        assert is_known_city_normalized("bangalore")
        assert is_known_city_normalized("SINGAPORE")
        assert is_known_city_normalized("mumbai")


class TestAccumulatedCities:
    """Test the organic city accumulation feature."""

    def test_record_new_city_with_high_confidence(self):
        """New cities with high confidence should be added."""
        from intake.geography import is_known_city, record_seen_city
        from intake.geography import clear_cache

        clear_cache()  # Start fresh

        # Fake city not in baseline
        fake_city = f"TestCityAlpha123_{uuid.uuid4().hex[:10]}"
        assert not is_known_city(fake_city), "Fake city should not be known initially"

        # Record with high confidence
        added = record_seen_city(fake_city, 0.9)
        assert added, "City should be added with confidence > 0.7"

        # Now it should be known
        assert is_known_city(fake_city), "City should be known after recording"

        # Teardown: remove from accumulated
        import json
        from pathlib import Path
        acc_path = Path("data/accumulated_cities.json")
        if acc_path.exists():
            data = set(json.load(acc_path.open()))
            data.discard(fake_city)
            json.dump(sorted(data), acc_path.open("w"))
        clear_cache()

    def test_low_confidence_not_added(self):
        """Cities with low confidence should NOT be added."""
        from intake.geography import is_known_city, record_seen_city
        from intake.geography import clear_cache

        clear_cache()

        fake_city = f"TestCityBeta456_{uuid.uuid4().hex[:10]}"
        assert not is_known_city(fake_city)

        # Record with low confidence
        added = record_seen_city(fake_city, 0.3)
        assert not added, "City should NOT be added with confidence < 0.7"

        # Should still not be known
        assert not is_known_city(fake_city)

        clear_cache()


class TestDatasetInfo:
    """Test dataset info and statistics."""

    def test_dataset_info_returns_stats(self):
        """get_dataset_info should return statistics about loaded data."""
        from intake.geography import get_dataset_info

        info = get_dataset_info()

        assert "geonames_count" in info
        assert "worldcities_count" in info
        assert "accumulated_count" in info
        assert "total_unique" in info
        assert "blacklist_count" in info

        # Should have substantial coverage
        assert info["total_unique"] > 100000, "Should have at least 100k cities"
        assert info["blacklist_count"] > 0, "Should have blacklist terms"

    def test_attribution_notice_includes_geonames(self):
        """Attribution notice should mention GeoNames."""
        from intake.geography import get_attribution_notice

        notice = get_attribution_notice()
        assert "GeoNames" in notice
        assert "geonames.org" in notice


class TestAlternateNameSupport:
    """Test that alternate names work (e.g., Bangalore vs Bengaluru)."""

    def test_bangalore_and_bengaluru_both_recognized(self):
        """Both Bangalore and Bengaluru should be recognized (same city, different names)."""
        from intake.geography import is_known_city

        # This is the key test - Bangalore is an alternate name for Bengaluru
        assert is_known_city("Bangalore")
        assert is_known_city("Bengaluru")
