"""
tests.test_decision_cache — Unit tests for decision cache module.

Tests cache schema, storage, and key generation.
"""

import json
import pytest
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from src.decision.cache_schema import CachedDecision, CacheStats
from src.decision.cache_storage import DecisionCacheStorage
from src.decision.cache_key import generate_cache_key, make_test_key


class TestCachedDecision:
    """Tests for CachedDecision dataclass."""

    def test_create_cached_decision(self):
        """Test creating a cached decision."""
        decision = CachedDecision(
            cache_key="test123",
            decision_type="test_decision",
            decision={"result": "yes"},
            confidence=0.9,
            source="rule_engine",
        )

        assert decision.cache_key == "test123"
        assert decision.decision_type == "test_decision"
        assert decision.decision == {"result": "yes"}
        assert decision.confidence == 0.9
        assert decision.source == "rule_engine"
        assert decision.use_count == 0
        assert decision.success_rate == 1.0

    def test_cached_decision_with_metadata(self):
        """Test creating a cached decision with metadata."""
        now = datetime.now(ZoneInfo("UTC"))
        decision = CachedDecision(
            cache_key="test123",
            decision_type="test_decision",
            decision={"result": "yes"},
            confidence=0.9,
            source="llm_compiled",
            llm_model_used="gemini-1.5-flash",
            created_at=now.isoformat(),
            last_used_at=now.isoformat(),
            use_count=5,
            success_rate=0.85,
            feedback_count=10,
        )

        assert decision.llm_model_used == "gemini-1.5-flash"
        assert decision.use_count == 5
        assert decision.success_rate == 0.85
        assert decision.feedback_count == 10


class TestCacheStats:
    """Tests for CacheStats dataclass."""

    def test_create_cache_stats(self):
        """Test creating cache stats."""
        stats = CacheStats(
            total_lookups=100,
            cache_hits=60,
            cache_misses=40,
            llm_calls=10,
        )

        assert stats.total_lookups == 100
        assert stats.cache_hits == 60
        assert stats.cache_misses == 40
        assert stats.llm_calls == 10
        assert stats.hit_rate == 0.6
        assert stats.miss_rate == 0.4


class TestDecisionCacheStorage:
    """Tests for DecisionCacheStorage."""

    @pytest.fixture
    def temp_cache_dir(self):
        """Create a temporary directory for cache files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def storage(self, temp_cache_dir):
        """Create a storage instance with temp directory."""
        return DecisionCacheStorage(cache_dir=temp_cache_dir)

    @pytest.fixture
    def sample_decision(self):
        """Create a sample cached decision."""
        return CachedDecision(
            cache_key="test_key_123",
            decision_type="elderly_mobility_risk",
            decision={
                "risk_level": "low",
                "reasoning": "Destination is elderly-friendly",
            },
            confidence=0.95,
            source="rule_engine",
        )

    def test_storage_initialization(self, temp_cache_dir):
        """Test storage initialization creates directory."""
        storage = DecisionCacheStorage(cache_dir=temp_cache_dir)
        assert storage.cache_dir == temp_cache_dir

    def test_put_and_get(self, storage, sample_decision):
        """Test putting and getting a decision."""
        # Put decision
        storage.set(
            cache_key=sample_decision.cache_key,
            decision_type=sample_decision.decision_type,
            decision=sample_decision,
        )

        # Get decision
        retrieved = storage.get(
            sample_decision.cache_key,
            sample_decision.decision_type,
        )

        assert retrieved is not None
        assert retrieved.cache_key == sample_decision.cache_key
        assert retrieved.decision_type == sample_decision.decision_type
        assert retrieved.decision == sample_decision.decision

    def test_get_nonexistent(self, storage):
        """Test getting a nonexistent decision returns None."""
        result = storage.get("unknown_key", "unknown_type")
        assert result is None

    def test_put_updates_use_count(self, storage, sample_decision):
        """Test that getting a decision updates use count."""
        storage.set(
            cache_key=sample_decision.cache_key,
            decision_type=sample_decision.decision_type,
            decision=sample_decision,
        )

        # First get
        first = storage.get(sample_decision.cache_key, sample_decision.decision_type)
        assert first.use_count == 1

        # Second get
        second = storage.get(sample_decision.cache_key, sample_decision.decision_type)
        assert second.use_count == 2

    def test_delete(self, storage, sample_decision):
        """Test deleting a decision."""
        storage.set(
            cache_key=sample_decision.cache_key,
            decision_type=sample_decision.decision_type,
            decision=sample_decision,
        )
        assert storage.get(sample_decision.cache_key, sample_decision.decision_type) is not None

        storage.delete(sample_decision.cache_key, sample_decision.decision_type)
        assert storage.get(sample_decision.cache_key, sample_decision.decision_type) is None

    def test_list_all(self, storage, sample_decision):
        """Test listing all decisions for a type."""
        storage.set(
            cache_key=sample_decision.cache_key,
            decision_type=sample_decision.decision_type,
            decision=sample_decision,
        )

        # Add another decision
        decision2 = CachedDecision(
            cache_key="another_key",
            decision_type="elderly_mobility_risk",
            decision={"risk_level": "high"},
            confidence=0.8,
            source="llm_compiled",
        )
        storage.set(
            cache_key=decision2.cache_key,
            decision_type=decision2.decision_type,
            decision=decision2,
        )

        # List all
        decisions = storage.get_all_for_type("elderly_mobility_risk")
        assert len(decisions) == 2

    def test_get_stats(self, storage, sample_decision):
        """Test getting cache statistics."""
        storage.set(
            cache_key=sample_decision.cache_key,
            decision_type=sample_decision.decision_type,
            decision=sample_decision,
        )

        # Stats are updated when get() is called
        storage.get(sample_decision.cache_key, sample_decision.decision_type)

        stats = storage.get_stats()
        assert stats is not None
        assert stats.total_lookups > 0

    def test_cleanup_expired(self, storage, sample_decision):
        """Test cleanup of expired entries."""
        # Create an old decision
        old_date = (datetime.now(ZoneInfo("UTC")) - timedelta(days=40)).isoformat()
        old_decision = CachedDecision(
            cache_key="old_key",
            decision_type="test_type",
            decision={"result": "old"},
            confidence=0.8,
            source="rule_engine",
            created_at=old_date,
        )
        storage.set(
            cache_key=old_decision.cache_key,
            decision_type=old_decision.decision_type,
            decision=old_decision,
        )

        # Create a recent decision
        storage.set(
            cache_key=sample_decision.cache_key,
            decision_type=sample_decision.decision_type,
            decision=sample_decision,
        )

        # Clear type (cleanup all for a type)
        count = storage.clear_type("test_type")

        # Old decision should be removed
        assert storage.get("old_key", "test_type") is None
        # Sample decision should still exist
        assert storage.get(
            sample_decision.cache_key,
            sample_decision.decision_type,
        ) is not None


class TestCacheKeyGeneration:
    """Tests for cache key generation."""

    def test_make_test_key(self):
        """Test creating a test cache key."""
        key1 = make_test_key("test_type", {"a": 1, "b": 2})
        key2 = make_test_key("test_type", {"a": 1, "b": 2})
        key3 = make_test_key("test_type", {"a": 1, "b": 3})

        # Same inputs should produce same key
        assert key1 == key2
        assert len(key1) == 32

        # Different inputs should produce different key
        assert key1 != key3

    def test_make_test_key_order_independence(self):
        """Test that key order doesn't affect the key."""
        key1 = make_test_key("test_type", {"a": 1, "b": 2, "c": 3})
        key2 = make_test_key("test_type", {"c": 3, "a": 1, "b": 2})

        assert key1 == key2

    def test_generate_cache_key_with_context(self):
        """Test cache key with additional context."""
        from src.intake.packet_models import CanonicalPacket, Slot

        packet = CanonicalPacket(
            packet_id="test-packet",
            facts={
                "destination_candidates": Slot(
                    value=["Paris"],
                    authority_level="explicit_user",
                ),
                "party_composition": Slot(
                    value={"elderly": 1},
                    authority_level="explicit_user",
                ),
            },
            derived_signals={},
        )

        key1 = generate_cache_key(
            "elderly_mobility_risk",
            packet,
        )

        key2 = generate_cache_key(
            "elderly_mobility_risk",
            packet,
            context={"extra": "data"},
        )

        # Context should affect the key
        assert key1 != key2
