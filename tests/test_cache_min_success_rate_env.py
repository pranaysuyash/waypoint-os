"""
tests.test_cache_min_success_rate_env — Tests for DECISION_CACHE_MIN_SUCCESS_RATE env var override.

Verifies that:
- Default value (0.7) is used when env var is absent
- Valid float in [0.0, 1.0] overrides the default
- Non-parseable string falls back to default with warning
- Out-of-range value falls back to default with warning
- is_valid() respects the resolved constant
"""

import os
import importlib

import pytest

from src.decision import cache_schema


def _reload_with_env(env_value):
    """Reload cache_schema with a specific env var value and return the resolved constant."""
    # Clear the lru_cache so the resolver re-reads the env var
    cache_schema._resolve_cache_min_success_rate.cache_clear()

    if env_value is None:
        os.environ.pop("DECISION_CACHE_MIN_SUCCESS_RATE", None)
    else:
        os.environ["DECISION_CACHE_MIN_SUCCESS_RATE"] = env_value

    try:
        result = cache_schema._resolve_cache_min_success_rate()
    finally:
        # Clean up env var after reading
        os.environ.pop("DECISION_CACHE_MIN_SUCCESS_RATE", None)

    return result


class TestCacheMinSuccessRateEnvOverride:
    """Tests for DECISION_CACHE_MIN_SUCCESS_RATE env var override."""

    def test_default_when_env_absent(self):
        """Default 0.7 is used when env var is not set."""
        result = _reload_with_env(None)
        assert result == 0.7

    def test_valid_float_overrides_default(self):
        """Valid float in [0.0, 1.0] overrides the default."""
        result = _reload_with_env("0.8")
        assert result == 0.8

    def test_boundary_zero(self):
        """0.0 is accepted (disables success rate filtering)."""
        result = _reload_with_env("0.0")
        assert result == 0.0

    def test_boundary_one(self):
        """1.0 is accepted (only perfect scores pass)."""
        result = _reload_with_env("1.0")
        assert result == 1.0

    def test_integer_string_parsed(self):
        """Integer string '1' is parsed as float 1.0."""
        result = _reload_with_env("1")
        assert result == 1.0

    def test_non_parseable_falls_back(self):
        """Non-parseable string falls back to default 0.7."""
        result = _reload_with_env("not-a-number")
        assert result == 0.7

    def test_empty_string_falls_back(self):
        """Empty string falls back to default 0.7."""
        result = _reload_with_env("")
        assert result == 0.7

    def test_out_of_range_high_falls_back(self):
        """Value > 1.0 falls back to default 0.7."""
        result = _reload_with_env("1.5")
        assert result == 0.7

    def test_out_of_range_negative_falls_back(self):
        """Negative value falls back to default 0.7."""
        result = _reload_with_env("-0.1")
        assert result == 0.7

    def test_whitespace_value_falls_back(self):
        """Whitespace-only string falls back to default 0.7."""
        result = _reload_with_env("  ")
        assert result == 0.7


class TestIsValidRespectsEnvOverride:
    """Tests that CachedDecision.is_valid() uses the resolved CACHE_MIN_SUCCESS_RATE."""

    def test_is_valid_uses_resolved_constant(self):
        """is_valid() default parameter uses the module-level CACHE_MIN_SUCCESS_RATE."""
        from src.decision.cache_schema import CachedDecision

        # Create a decision with success_rate=0.6 (below default 0.7)
        decision = CachedDecision(
            cache_key="test",
            decision_type="test",
            decision={"result": "yes"},
            confidence=0.9,
            source="rule_engine",
            success_rate=0.6,
        )

        # With default threshold (0.7), should be invalid
        assert decision.is_valid() is False

        # Explicitly passing a lower threshold should make it valid
        assert decision.is_valid(min_success_rate=0.5) is True

    def test_is_valid_high_success_rate_always_valid(self):
        """Decision with success_rate=1.0 is always valid regardless of threshold."""
        from src.decision.cache_schema import CachedDecision

        decision = CachedDecision(
            cache_key="test",
            decision_type="test",
            decision={"result": "yes"},
            confidence=0.9,
            source="rule_engine",
            success_rate=1.0,
        )

        assert decision.is_valid() is True
        assert decision.is_valid(min_success_rate=0.99) is True
