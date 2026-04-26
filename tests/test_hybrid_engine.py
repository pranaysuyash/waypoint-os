"""
tests.test_hybrid_engine — Unit tests for hybrid decision engine.

Tests for HybridDecisionEngine orchestration, metrics, and decision flow.
"""

import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from src.decision.hybrid_engine import (
    HybridDecisionEngine,
    DecisionResult,
    EngineMetrics,
    create_hybrid_engine,
)
from src.decision.cache_storage import DecisionCacheStorage
from src.llm.base import BaseLLMClient, LLMUnavailableError


class MockLLMClient(BaseLLMClient):
    """Mock LLM client for testing."""

    def __init__(self, model="mock-model"):
        super().__init__(model, temperature=0.3, max_tokens=1024)
        self._available = True
        self._decisions = {}

    def set_available(self, available: bool):
        """Set availability status."""
        self._available = available

    def set_decision(self, decision: dict):
        """Set a mock decision."""
        self._decisions["default"] = decision

    def decide(self, prompt: str, schema: dict, temperature: float = None) -> dict:
        """Return mock decision."""
        if not self.is_available():
            raise LLMUnavailableError("Mock client not available")
        return self._decisions.get("default", {"result": "mock"})

    def is_available(self) -> bool:
        """Check availability."""
        return self._available


@pytest.fixture
def temp_cache_dir():
    """Create a temporary directory for cache files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_storage(temp_cache_dir):
    """Create a mock storage instance."""
    return DecisionCacheStorage(cache_dir=temp_cache_dir)


@pytest.fixture
def mock_llm():
    """Create a mock LLM client."""
    return MockLLMClient()


@pytest.fixture
def sample_packet():
    """Create a sample CanonicalPacket."""
    from src.intake.packet_models import CanonicalPacket, Slot

    return CanonicalPacket(
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
        derived_signals={
            "domestic_or_international": Slot(
                value="international",
                authority_level="derived_signal",
            ),
        },
    )


class TestDecisionResult:
    """Tests for DecisionResult dataclass."""

    def test_create_decision_result(self):
        """Test creating a decision result."""
        result = DecisionResult(
            decision={"risk_level": "low"},
            source="rule",
            confidence=0.9,
            decision_type="elderly_mobility_risk",
        )

        assert result.decision == {"risk_level": "low"}
        assert result.source == "rule"
        assert result.confidence == 0.9
        assert not result.cache_hit
        assert not result.llm_used

    def test_to_dict(self):
        """Test converting result to dictionary."""
        result = DecisionResult(
            decision={"risk_level": "low"},
            source="cache",
            confidence=0.95,
            cache_hit=True,
            decision_type="test_type",
        )

        d = result.to_dict()
        assert d["decision"] == {"risk_level": "low"}
        assert d["source"] == "cache"
        assert d["cache_hit"] is True


class TestEngineMetrics:
    """Tests for EngineMetrics dataclass."""

    def test_initial_metrics(self):
        """Test initial metrics are zero."""
        metrics = EngineMetrics()
        assert metrics.total_decisions == 0
        assert metrics.cache_hits == 0
        assert metrics.llm_calls == 0

    def test_calculate_rates(self):
        """Test hit rate calculation."""
        metrics = EngineMetrics(
            total_decisions=100,
            cache_hits=60,
            rule_hits=20,
            llm_calls=15,
        )

        metrics.calculate_rates()

        assert metrics.cache_hit_rate == 0.6
        assert metrics.rule_hit_rate == 0.2
        assert metrics.llm_call_rate == 0.15

    def test_to_dict(self):
        """Test converting metrics to dictionary."""
        metrics = EngineMetrics(
            total_decisions=100,
            cache_hits=60,
            total_cost_inr=10.50,
        )

        d = metrics.to_dict()
        assert d["total_decisions"] == 100
        assert d["cache_hits"] == 60
        assert d["cache_hit_rate"] == 0.6
        assert d["total_cost_inr"] == 10.5


class TestHybridDecisionEngine:
    """Tests for HybridDecisionEngine."""

    def test_initialization(self, mock_storage):
        """Test engine initialization."""
        engine = HybridDecisionEngine(
            cache_storage=mock_storage,
            enable_cache=True,
            enable_rules=True,
            enable_llm=False,
        )

        assert engine.enable_cache is True
        assert engine.enable_rules is True
        assert engine.enable_llm is False
        assert engine.metrics.total_decisions == 0

    def test_decide_with_cache_hit(self, mock_storage, sample_packet):
        """Test decision flow with cache hit."""
        from src.decision.cache_schema import CachedDecision

        # Pre-populate cache
        cached = CachedDecision(
            cache_key="test_key",
            decision_type="elderly_mobility_risk",
            decision={"risk_level": "low"},
            confidence=0.95,
            source="rule_engine",
            success_rate=0.9,
        )
        mock_storage.set(
            cache_key=cached.cache_key,
            decision_type=cached.decision_type,
            decision=cached,
        )

        # Create engine
        engine = HybridDecisionEngine(
            cache_storage=mock_storage,
            enable_cache=True,
            enable_rules=False,
            enable_llm=False,
        )

        # Mock the cache key generation to return our test key
        with patch("src.decision.hybrid_engine.generate_cache_key", return_value="test_key"):
            result = engine.decide("elderly_mobility_risk", sample_packet)

        assert result.source == "cache"
        assert result.cache_hit is True
        assert result.decision == {"risk_level": "low"}

    def test_decide_with_rule_hit(self, mock_storage, sample_packet, mock_llm):
        """Test decision flow with rule hit."""
        engine = HybridDecisionEngine(
            cache_storage=mock_storage,
            llm_client=mock_llm,
            enable_cache=False,  # Disable cache to test rule
            enable_rules=True,
            enable_llm=False,
        )

        # Clear built-in rules and register a mock rule
        engine._rules = {}
        def mock_rule(packet):
            return {"risk_level": "medium", "reason": "Rule decision"}

        engine.register_rule("elderly_mobility_risk", mock_rule)

        result = engine.decide("elderly_mobility_risk", sample_packet)

        assert result.source == "rule"
        assert result.rule_hit is True
        assert result.decision["risk_level"] == "medium"
        assert result.decision["reason"] == "Rule decision"

    def test_decide_with_llm_fallback(self, mock_storage, sample_packet, mock_llm):
        """Test decision flow with LLM fallback."""
        # Setup mock LLM
        mock_llm.set_decision({
            "risk_level": "high",
            "reasoning": "LLM decision",
        })

        engine = HybridDecisionEngine(
            cache_storage=mock_storage,
            llm_client=mock_llm,
            enable_cache=False,
            enable_rules=False,
            enable_llm=True,
        )

        result = engine.decide("elderly_mobility_risk", sample_packet)

        assert result.source == "llm"
        assert result.llm_used is True
        assert result.decision["risk_level"] == "high"
        assert result.decision["reasoning"] == "LLM decision"

    def test_decide_with_default_fallback(self, mock_storage, sample_packet):
        """Test decision flow with default fallback."""
        # Mock LLM that's unavailable
        mock_llm = MockLLMClient()
        mock_llm.set_available(False)

        engine = HybridDecisionEngine(
            cache_storage=mock_storage,
            llm_client=mock_llm,
            enable_cache=False,
            enable_rules=False,
            enable_llm=True,
        )

        result = engine.decide("elderly_mobility_risk", sample_packet)

        assert result.source == "default"
        assert "risk_level" in result.decision

    def test_register_rule(self, mock_storage):
        """Test registering a rule."""
        engine = HybridDecisionEngine(cache_storage=mock_storage, enable_rules=False)

        def mock_rule(packet):
            return {"result": "test"}

        engine.register_rule("test_decision", mock_rule)

        assert "test_decision" in engine._rules
        assert len(engine._rules["test_decision"]) == 1

    def test_metrics_tracking(self, mock_storage, sample_packet, mock_llm):
        """Test that metrics are tracked correctly."""
        mock_llm.set_decision({"risk_level": "low"})

        engine = HybridDecisionEngine(
            cache_storage=mock_storage,
            llm_client=mock_llm,
            enable_cache=False,
            enable_rules=False,
            enable_llm=True,
        )

        # Make a decision
        engine.decide("elderly_mobility_risk", sample_packet)

        metrics = engine.get_metrics()
        assert metrics.total_decisions == 1
        assert metrics.llm_calls == 1

    def test_get_cache_stats(self, mock_storage):
        """Test getting cache statistics."""
        from src.decision.cache_schema import CacheStats

        engine = HybridDecisionEngine(cache_storage=mock_storage)

        stats = engine.get_cache_stats()
        assert isinstance(stats, CacheStats)

    def test_unknown_decision_type_raises_error(self, mock_storage, sample_packet):
        """Test that unknown decision type raises error."""
        engine = HybridDecisionEngine(
            cache_storage=mock_storage,
            enable_cache=False,
            enable_rules=False,
            enable_llm=False,
        )

        with pytest.raises(ValueError, match="No schema available"):
            engine.decide("unknown_decision_type", sample_packet)


class TestCreateHybridEngine:
    """Tests for create_hybrid_engine factory function."""

    def test_create_engine_default(self, monkeypatch):
        """Test creating engine with default settings."""
        monkeypatch.setenv("USE_HYBRID_DECISION_ENGINE", "1")

        engine = create_hybrid_engine()
        assert engine.enable_cache is True
        assert engine.enable_rules is True
        assert engine.enable_llm is True

    def test_create_engine_disabled(self, monkeypatch):
        """Test creating engine with feature flag disabled."""
        monkeypatch.setenv("USE_HYBRID_DECISION_ENGINE", "0")

        engine = create_hybrid_engine()
        assert engine.enable_cache is False
        assert engine.enable_rules is True  # Rules still enabled
        assert engine.enable_llm is False

    def test_create_engine_with_options(self):
        """Test creating engine with specific options."""
        engine = create_hybrid_engine(
            enable_cache=False,
            enable_rules=True,
            enable_llm=False,
        )

        assert engine.enable_cache is False
        assert engine.enable_rules is True
        assert engine.enable_llm is False


class TestDecisionSchemas:
    """Tests for decision schema definitions."""

    def test_elderly_mobility_schema(self):
        """Test elderly mobility risk schema."""
        from src.decision.hybrid_engine import HybridDecisionEngine

        schema = HybridDecisionEngine.SCHEMAS["elderly_mobility_risk"]

        assert schema["type"] == "object"
        assert "risk_level" in schema["properties"]
        assert "low" in schema["properties"]["risk_level"]["enum"]
        assert "high" in schema["properties"]["risk_level"]["enum"]

    def test_budget_feasibility_schema(self):
        """Test budget feasibility schema."""
        from src.decision.hybrid_engine import HybridDecisionEngine

        schema = HybridDecisionEngine.SCHEMAS["budget_feasibility"]

        assert schema["type"] == "object"
        assert "feasible" in schema["properties"]
        assert schema["properties"]["feasible"]["type"] == "boolean"

    def test_default_decision_exists(self):
        """Test that default decisions exist for all types."""
        from src.decision.hybrid_engine import HybridDecisionEngine

        for decision_type in HybridDecisionEngine.SCHEMAS:
            assert decision_type in HybridDecisionEngine.DEFAULT_DECISIONS
            default = HybridDecisionEngine.DEFAULT_DECISIONS[decision_type]
            assert isinstance(default, dict)


class TestLLMUsageGuardIntegration:
    """Integration tests for LLM usage guard with hybrid engine."""

    def _make_packet(self):
        """Create a sample CanonicalPacket."""
        from src.intake.packet_models import CanonicalPacket, Slot

        return CanonicalPacket(
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
            derived_signals={
                "domestic_or_international": Slot(
                    value="international",
                    authority_level="derived_signal",
                ),
            },
        )

    def test_guard_allows_call_proceeds_normally(self, mock_storage, monkeypatch):
        """Allowed LLM call proceeds through hybrid engine."""
        from src.decision.hybrid_engine import HybridDecisionEngine
        from src.llm.usage_guard import LLMUsageGuard, reset_usage_guard

        reset_usage_guard()
        monkeypatch.setenv("LLM_GUARD_ENABLED", "1")
        monkeypatch.setenv("LLM_MAX_CALLS_PER_HOUR", "100")
        monkeypatch.setenv("LLM_DAILY_BUDGET", "1000")

        mock_llm = MockLLMClient()
        mock_llm.set_decision({"risk_level": "high", "reasoning": "LLM decision"})

        engine = HybridDecisionEngine(
            cache_storage=mock_storage,
            llm_client=mock_llm,
            enable_cache=False,
            enable_rules=False,
            enable_llm=True,
        )

        packet = self._make_packet()
        result = engine.decide("elderly_mobility_risk", packet)

        assert result.source == "llm"
        assert result.llm_used is True
        assert result.decision["risk_level"] == "high"

    def test_guard_disabled_allows_llm_without_guard(self, mock_storage, monkeypatch):
        """Guard disabled via env var allows all LLM calls."""
        from src.decision.hybrid_engine import HybridDecisionEngine
        from src.llm.usage_guard import reset_usage_guard

        reset_usage_guard()
        monkeypatch.setenv("LLM_GUARD_ENABLED", "0")
        monkeypatch.setenv("LLM_MAX_CALLS_PER_HOUR", "1")
        monkeypatch.setenv("LLM_DAILY_BUDGET", "0.01")

        mock_llm = MockLLMClient()
        mock_llm.set_decision({"risk_level": "high"})

        engine = HybridDecisionEngine(
            cache_storage=mock_storage,
            llm_client=mock_llm,
            enable_cache=False,
            enable_rules=False,
            enable_llm=True,
        )

        packet = self._make_packet()

        result = engine.decide("elderly_mobility_risk", packet)

        assert result.source == "llm"

    def test_guard_record_failure_on_llm_exception(self, mock_storage, monkeypatch):
        """LLM exception is recorded as failed call."""
        from src.decision.hybrid_engine import HybridDecisionEngine
        from src.llm.usage_guard import reset_usage_guard

        reset_usage_guard()
        monkeypatch.setenv("LLM_GUARD_ENABLED", "1")
        monkeypatch.setenv("LLM_MAX_CALLS_PER_HOUR", "100")
        monkeypatch.setenv("LLM_DAILY_BUDGET", "1000.0")

        class FailingLLM(MockLLMClient):
            def decide(self, prompt, schema, temperature=None):
                raise RuntimeError("LLM provider error")

        mock_llm = FailingLLM()

        engine = HybridDecisionEngine(
            cache_storage=mock_storage,
            llm_client=mock_llm,
            enable_cache=False,
            enable_rules=False,
            enable_llm=True,
        )

        packet = self._make_packet()
        result = engine.decide("elderly_mobility_risk", packet)

        assert result.source == "default"

    def test_guard_killswitch_stops_enforcement(self, mock_storage, monkeypatch):
        """LLM_GUARD_ENABLED=0 disables guard enforcement."""
        from src.decision.hybrid_engine import HybridDecisionEngine
        from src.llm.usage_guard import reset_usage_guard

        reset_usage_guard()
        monkeypatch.setenv("LLM_GUARD_ENABLED", "0")

        mock_llm = MockLLMClient()
        mock_llm.set_decision({"risk_level": "low"})

        engine = HybridDecisionEngine(
            cache_storage=mock_storage,
            llm_client=mock_llm,
            enable_cache=False,
            enable_rules=False,
            enable_llm=True,
        )

        packet = self._make_packet()
        result = engine.decide("elderly_mobility_risk", packet)

        assert result.source == "llm"
