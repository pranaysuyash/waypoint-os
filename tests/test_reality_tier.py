"""
tests/test_reality_tier.py — Tests for the reality tier classification system.

Verifies:
  - Tier enum values are correct
  - Capability matrix is complete
  - Tier metadata generation works
  - Capability assertions work
  - Feature registry returns correct tiers
"""

import pytest
from fastapi import HTTPException

from spine_api.core.reality_tier import (
    RealityTier,
    TIER_CAPABILITIES,
    TierMetadata,
    assert_tier_capability,
)
from spine_api.core.feature_gates import (
    FEATURE_REGISTRY,
    get_feature_tier,
    get_feature_entry,
    get_all_features,
)


class TestRealityTierEnum:
    """Tier enum has all expected values."""

    def test_all_tiers_defined(self):
        assert RealityTier.REAL == "real"
        assert RealityTier.CONNECTED_SANDBOX == "connected_sandbox"
        assert RealityTier.DETERMINISTIC_PREVIEW == "deterministic_preview"
        assert RealityTier.DATA_DEPENDENT == "data_dependent"
        assert RealityTier.PLANNED == "planned"

    def test_all_tiers_have_capabilities(self):
        for tier in RealityTier:
            assert tier in TIER_CAPABILITIES, f"Missing capabilities for {tier}"

    def test_capability_keys_consistent(self):
        """All tiers define the same set of capability keys."""
        expected_keys = {
            "can_write_success_events",
            "can_appear_as_paid",
            "can_make_safety_claims",
            "can_make_financial_claims",
            "can_mutate_booking_state",
        }
        for tier, caps in TIER_CAPABILITIES.items():
            assert set(caps.keys()) == expected_keys, f"Inconsistent keys for {tier}"


class TestTierCapabilities:
    """Only REAL tier can make safety/financial claims and mutate booking state."""

    def test_real_has_all_capabilities(self):
        caps = TIER_CAPABILITIES[RealityTier.REAL]
        assert all(caps.values()), "REAL tier should have all capabilities"

    def test_planned_has_no_capabilities(self):
        caps = TIER_CAPABILITIES[RealityTier.PLANNED]
        assert not any(caps.values()), "PLANNED tier should have no capabilities"

    def test_preview_cannot_claim_safety(self):
        caps = TIER_CAPABILITIES[RealityTier.DETERMINISTIC_PREVIEW]
        assert not caps["can_make_safety_claims"]
        assert not caps["can_make_financial_claims"]
        assert not caps["can_mutate_booking_state"]

    def test_data_dependent_cannot_claim_safety(self):
        caps = TIER_CAPABILITIES[RealityTier.DATA_DEPENDENT]
        assert not caps["can_make_safety_claims"]
        assert not caps["can_make_financial_claims"]


class TestTierMetadata:
    """Metadata generation for API responses."""

    def test_basic_metadata(self):
        meta = TierMetadata.for_response(
            RealityTier.DETERMINISTIC_PREVIEW,
            "trust_scorecard",
        )
        assert meta["reality_tier"] == "deterministic_preview"
        assert meta["feature"] == "trust_scorecard"
        assert meta["data_sufficient"] is True
        assert "capabilities" in meta

    def test_insufficient_data(self):
        meta = TierMetadata.for_response(
            RealityTier.DATA_DEPENDENT,
            "concierge",
            data_sufficient=False,
        )
        assert meta["data_sufficient"] is False

    def test_computation_method(self):
        meta = TierMetadata.for_response(
            RealityTier.DETERMINISTIC_PREVIEW,
            "trust_scorecard",
            computation_method="packet_field_completeness",
        )
        assert meta["computation_method"] == "packet_field_completeness"

    def test_missing_for_upgrade(self):
        meta = TierMetadata.for_response(
            RealityTier.DATA_DEPENDENT,
            "supplier_management",
            missing_for_upgrade=["supplier_booking_api", "gds_integration"],
        )
        assert "supplier_booking_api" in meta["missing_for_upgrade"]


class TestTierCapabilityAssertions:
    """Capability assertion raises HTTPException when tier lacks capability."""

    def test_real_tier_passes_all(self):
        # Should not raise
        assert_tier_capability(RealityTier.REAL, "can_mutate_booking_state", "test")
        assert_tier_capability(RealityTier.REAL, "can_make_safety_claims", "test")

    def test_planned_tier_fails(self):
        with pytest.raises(HTTPException) as exc_info:
            assert_tier_capability(
                RealityTier.PLANNED,
                "can_mutate_booking_state",
                "test_feature",
            )
        assert exc_info.value.status_code == 403
        assert "test_feature" in str(exc_info.value.detail)


class TestFeatureRegistry:
    """Feature registry returns correct tiers and covers all features."""

    def test_core_features_are_real(self):
        """Core workflow features should be REAL tier."""
        assert get_feature_tier("intake_extraction") == RealityTier.REAL
        assert get_feature_tier("gap_detection") == RealityTier.REAL
        assert get_feature_tier("trip_persistence") == RealityTier.REAL

    def test_trust_scorecard_is_preview(self):
        assert get_feature_tier("trust_scorecard") == RealityTier.DETERMINISTIC_PREVIEW

    def test_unknown_feature_is_planned(self):
        assert get_feature_tier("nonexistent_feature") == RealityTier.PLANNED

    def test_all_entries_have_required_fields(self):
        for name, entry in FEATURE_REGISTRY.items():
            assert entry.name == name
            assert isinstance(entry.tier, RealityTier)
            assert len(entry.description) > 0
            assert len(entry.honest_status) > 0

    def test_get_feature_entry(self):
        entry = get_feature_entry("trust_scorecard")
        assert entry is not None
        assert entry.name == "trust_scorecard"

    def test_get_all_features(self):
        features = get_all_features()
        assert len(features) > 5
        assert "trust_scorecard" in features

    def test_no_fabricated_tier_exists(self):
        """Ensure we don't have a 'fabricated' or 'simulated' tier — that's the old world."""
        for tier in RealityTier:
            assert "fabricat" not in tier.value.lower()
            assert "simulat" not in tier.value.lower()
