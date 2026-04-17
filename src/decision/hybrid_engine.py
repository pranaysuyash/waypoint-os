"""
decision.hybrid_engine — Hybrid decision engine orchestration.

Implements the cost-optimized decision flow:
1. Check cache (₹0)
2. Try rule engine (₹0)
3. Fall back to LLM (₹0.10-₹1) and cache the result

This enables "learning" - successful LLM decisions become cached rules.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from intake.packet_models import CanonicalPacket
from decision.cache_schema import CachedDecision, CacheStats
from decision.cache_storage import DecisionCacheStorage, get_default_storage
from decision.cache_key import generate_cache_key

try:
    from llm import BaseLLMClient, create_llm_client
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class DecisionResult:
    """
    Result from the hybrid decision engine.

    Combines the decision with metadata about how it was reached.
    """
    decision: Dict[str, Any]
    source: str  # "cache", "rule", "llm", "default"
    confidence: float
    cache_hit: bool = False
    rule_hit: bool = False
    llm_used: bool = False
    llm_model: Optional[str] = None
    cost_inr: float = 0.0
    decision_type: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "decision": self.decision,
            "source": self.source,
            "confidence": self.confidence,
            "cache_hit": self.cache_hit,
            "rule_hit": self.rule_hit,
            "llm_used": self.llm_used,
            "llm_model": self.llm_model,
            "cost_inr": self.cost_inr,
            "decision_type": self.decision_type,
        }


@dataclass
class EngineMetrics:
    """
    Metrics tracking for the hybrid engine.
    """
    total_decisions: int = 0
    cache_hits: int = 0
    rule_hits: int = 0
    llm_calls: int = 0
    default_fallbacks: int = 0
    total_cost_inr: float = 0.0

    cache_hit_rate: float = 0.0
    rule_hit_rate: float = 0.0
    llm_call_rate: float = 0.0

    def calculate_rates(self) -> None:
        """Calculate hit rates from totals."""
        if self.total_decisions > 0:
            self.cache_hit_rate = self.cache_hits / self.total_decisions
            self.rule_hit_rate = self.rule_hits / self.total_decisions
            self.llm_call_rate = self.llm_calls / self.total_decisions

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        self.calculate_rates()
        return {
            "total_decisions": self.total_decisions,
            "cache_hits": self.cache_hits,
            "rule_hits": self.rule_hits,
            "llm_calls": self.llm_calls,
            "default_fallbacks": self.default_fallbacks,
            "total_cost_inr": round(self.total_cost_inr, 2),
            "cache_hit_rate": round(self.cache_hit_rate, 3),
            "rule_hit_rate": round(self.rule_hit_rate, 3),
            "llm_call_rate": round(self.llm_call_rate, 3),
        }


class HybridDecisionEngine:
    """
    Hybrid decision engine combining cache, rules, and LLM.

    Decision flow:
    1. Generate cache key from inputs
    2. Check cache → return if hit
    3. Try registered rules → cache and return if match
    4. Call LLM → cache and return result
    5. Fallback to safe default if all else fails

    Usage:
        engine = HybridDecisionEngine()
        result = engine.decide(
            decision_type="elderly_mobility_risk",
            packet=packet,
            schema={"type": "object", "properties": {...}},
        )
    """

    # Decision schema templates
    SCHEMAS = {
        "elderly_mobility_risk": {
            "type": "object",
            "properties": {
                "risk_level": {"type": "string", "enum": ["low", "medium", "high"]},
                "reasoning": {"type": "string"},
                "recommendations": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["risk_level", "reasoning"],
        },
        "toddler_pacing_risk": {
            "type": "object",
            "properties": {
                "risk_level": {"type": "string", "enum": ["low", "medium", "high"]},
                "reasoning": {"type": "string"},
                "recommendations": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["risk_level", "reasoning"],
        },
        "budget_feasibility": {
            "type": "object",
            "properties": {
                "feasible": {"type": "boolean"},
                "risk_level": {"type": "string", "enum": ["low", "medium", "high"]},
                "reasoning": {"type": "string"},
                "estimated_cost_range": {"type": "string"},
            },
            "required": ["feasible", "risk_level", "reasoning"],
        },
        "visa_timeline_risk": {
            "type": "object",
            "properties": {
                "risk_level": {"type": "string", "enum": ["low", "medium", "high"]},
                "reasoning": {"type": "string"},
                "visa_lead_time_days": {"type": "integer"},
            },
            "required": ["risk_level", "reasoning"],
        },
        "composition_risk": {
            "type": "object",
            "properties": {
                "risk_level": {"type": "string", "enum": ["low", "medium", "high"]},
                "concerns": {"type": "array", "items": {"type": "string"}},
                "recommendations": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["risk_level"],
        },
    }

    # Default fallback decisions
    DEFAULT_DECISIONS = {
        "elderly_mobility_risk": {
            "risk_level": "medium",
            "reasoning": "Unable to assess - defaulting to medium risk",
            "recommendations": ["Verify mobility requirements with traveler"],
        },
        "toddler_pacing_risk": {
            "risk_level": "medium",
            "reasoning": "Unable to assess - defaulting to medium risk",
            "recommendations": ["Consider stroller accessibility", "Plan for frequent breaks"],
        },
        "budget_feasibility": {
            "feasible": True,
            "risk_level": "medium",
            "reasoning": "Unable to assess - manual review recommended",
            "estimated_cost_range": "unknown",
        },
        "visa_timeline_risk": {
            "risk_level": "medium",
            "reasoning": "Unable to assess - verify visa requirements",
            "visa_lead_time_days": 30,
        },
        "composition_risk": {
            "risk_level": "low",
            "concerns": ["Unable to assess"],
            "recommendations": ["Manual review recommended"],
        },
    }

    def __init__(
        self,
        cache_storage: Optional[DecisionCacheStorage] = None,
        llm_client: Optional[BaseLLMClient] = None,
        enable_cache: bool = True,
        enable_rules: bool = True,
        enable_llm: bool = True,
    ):
        """
        Initialize the hybrid decision engine.

        Args:
            cache_storage: Cache storage backend (uses default if not provided)
            llm_client: LLM client (creates default if not provided)
            enable_cache: Whether to check cache
            enable_rules: Whether to use rule engine
            enable_llm: Whether to use LLM fallback
        """
        self.cache_storage = cache_storage or get_default_storage()
        self.llm_client = llm_client
        self.enable_cache = enable_cache
        self.enable_rules = enable_rules
        self.enable_llm = enable_llm

        self.metrics = EngineMetrics()
        self._rules: Dict[str, List[Callable]] = {}

        # Register built-in rules if rules enabled
        if enable_rules:
            self._register_builtin_rules()

    def _register_builtin_rules(self) -> None:
        """Register built-in decision rules."""
        try:
            from decision.rules import (
                rule_elderly_mobility_risk,
                rule_toddler_pacing_risk,
                rule_budget_feasibility,
                rule_visa_timeline_risk,
                rule_composition_risk,
            )

            self.register_rule("elderly_mobility_risk", rule_elderly_mobility_risk)
            self.register_rule("toddler_pacing_risk", rule_toddler_pacing_risk)
            self.register_rule("budget_feasibility", rule_budget_feasibility)
            self.register_rule("visa_timeline_risk", rule_visa_timeline_risk)
            self.register_rule("composition_risk", rule_composition_risk)

            logger.debug("Registered 5 built-in decision rules")
        except ImportError as e:
            logger.warning(f"Failed to import built-in rules: {e}")

    def register_rule(
        self,
        decision_type: str,
        rule_fn: Callable[[CanonicalPacket], Optional[Dict[str, Any]]],
    ) -> None:
        """
        Register a rule function for a decision type.

        Rule function signature:
            def rule_fn(packet: CanonicalPacket) -> Optional[Dict[str, Any]]:
                # Returns None if rule cannot handle this case
                # Returns decision dict if rule can handle it
                ...

        Args:
            decision_type: Type of decision (e.g., "elderly_mobility_risk")
            rule_fn: Rule function that returns decision or None
        """
        if decision_type not in self._rules:
            self._rules[decision_type] = []
        self._rules[decision_type].append(rule_fn)
        logger.debug(f"Registered rule for {decision_type}")

    def decide(
        self,
        decision_type: str,
        packet: CanonicalPacket,
        schema: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> DecisionResult:
        """
        Make a decision using the hybrid engine.

        Decision flow: cache → rules → LLM → default

        Args:
            decision_type: Type of decision to make
            packet: CanonicalPacket with decision inputs
            schema: JSON schema for decision output (uses default if not provided)
            context: Additional context for decision

        Returns:
            DecisionResult with decision and metadata
        """
        self.metrics.total_decisions += 1

        # Use default schema if not provided
        schema = schema or self.SCHEMAS.get(decision_type)
        if not schema:
            raise ValueError(f"No schema available for decision type: {decision_type}")

        # Generate cache key
        cache_key = generate_cache_key(decision_type, packet, context)

        # Step 1: Check cache
        if self.enable_cache:
            cached = self._check_cache(decision_type, cache_key)
            if cached:
                self.metrics.cache_hits += 1
                return DecisionResult(
                    decision=cached.decision,
                    source="cache",
                    confidence=cached.confidence,
                    cache_hit=True,
                    decision_type=decision_type,
                )

        # Step 2: Try rules
        if self.enable_rules:
            rule_result = self._try_rules(decision_type, packet)
            if rule_result:
                self.metrics.rule_hits += 1
                # Cache the rule decision
                self._cache_decision(
                    decision_type=decision_type,
                    cache_key=cache_key,
                    decision=rule_result,
                    source="rule_engine",
                )
                return DecisionResult(
                    decision=rule_result,
                    source="rule",
                    confidence=0.9,  # Rules have high confidence
                    rule_hit=True,
                    decision_type=decision_type,
                )

        # Step 3: Call LLM
        if self.enable_llm:
            llm_result = self._call_llm(decision_type, packet, schema)
            if llm_result:
                self.metrics.llm_calls += 1
                # Cache the LLM decision
                self._cache_decision(
                    decision_type=decision_type,
                    cache_key=cache_key,
                    decision=llm_result["decision"],
                    source="llm_compiled",
                    llm_model=llm_result["model"],
                    cost=llm_result["cost"],
                )
                return DecisionResult(
                    decision=llm_result["decision"],
                    source="llm",
                    confidence=llm_result.get("confidence", 0.8),
                    llm_used=True,
                    llm_model=llm_result["model"],
                    cost_inr=llm_result["cost"],
                    decision_type=decision_type,
                )

        # Step 4: Fallback to default
        self.metrics.default_fallbacks += 1
        default = self.DEFAULT_DECISIONS.get(decision_type, {})
        logger.warning(f"Using default decision for {decision_type}")
        return DecisionResult(
            decision=default,
            source="default",
            confidence=0.5,
            decision_type=decision_type,
        )

    def _check_cache(
        self,
        decision_type: str,
        cache_key: str,
    ) -> Optional[CachedDecision]:
        """Check cache for a decision."""
        try:
            cached = self.cache_storage.get(cache_key, decision_type)

            # Validate cache entry meets requirements
            if cached:
                min_success_rate = 0.7  # Default minimum success rate
                if cached.success_rate >= min_success_rate:
                    logger.debug(f"Cache hit for {decision_type}: {cache_key[:8]}...")
                    return cached

        except Exception as e:
            logger.warning(f"Cache check failed: {e}")

        return None

    def _try_rules(
        self,
        decision_type: str,
        packet: CanonicalPacket,
    ) -> Optional[Dict[str, Any]]:
        """Try registered rules for a decision."""
        rules = self._rules.get(decision_type, [])

        for rule_fn in rules:
            try:
                result = rule_fn(packet)
                if result is not None:
                    logger.debug(f"Rule hit for {decision_type}: {rule_fn.__name__}")
                    return result
            except Exception as e:
                logger.warning(f"Rule {rule_fn.__name__} failed: {e}")

        return None

    def _call_llm(
        self,
        decision_type: str,
        packet: CanonicalPacket,
        schema: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """Call LLM for a decision."""
        if not LLM_AVAILABLE:
            logger.warning("LLM not available")
            return None

        try:
            # Create LLM client if not exists
            if not self.llm_client:
                self.llm_client = create_llm_client()

            if not self.llm_client.is_available():
                logger.warning("LLM client not available")
                return None

            # Build prompt
            prompt = self._build_llm_prompt(decision_type, packet)

            # Call LLM
            decision = self.llm_client.decide(
                prompt=prompt,
                schema=schema,
            )

            # Estimate cost
            prompt_tokens = self.llm_client.count_tokens(prompt)
            # Estimate response tokens (rough approximation)
            completion_tokens = self.llm_client.count_tokens(json.dumps(decision))
            cost = self.llm_client.estimate_cost(prompt_tokens, completion_tokens)

            self.metrics.total_cost_inr += cost

            logger.info(
                f"LLM call for {decision_type}: "
                f"model={self.llm_client.model}, cost=₹{cost:.2f}"
            )

            return {
                "decision": decision,
                "model": self.llm_client.model,
                "cost": cost,
                "confidence": 0.8,
            }

        except Exception as e:
            logger.error(f"LLM call failed for {decision_type}: {e}")
            return None

    def _build_llm_prompt(
        self,
        decision_type: str,
        packet: CanonicalPacket,
    ) -> str:
        """Build LLM prompt for a decision type."""
        # Extract relevant information from packet
        context = self._extract_packet_context(packet)

        prompts = {
            "elderly_mobility_risk": f"""You are a travel advisor assessing mobility risk for elderly travelers.

Context:
{context}

Assess the mobility risk level and provide recommendations.
- "low" risk: No significant mobility challenges
- "medium" risk: Some mobility challenges but manageable
- "high" risk: Significant mobility challenges, recommend alternative""",
            "toddler_pacing_risk": f"""You are a travel advisor assessing pacing risk for toddlers.

Context:
{context}

Assess the pacing risk level for toddlers.
- "low" risk: Trip is well-paced for young children
- "medium" risk: Some concerns about pacing
- "high" risk: Too fast-paced, needs major adjustments""",
            "budget_feasibility": f"""You are a travel advisor assessing budget feasibility.

Context:
{context}

Assess if the budget is feasible for this trip.
Consider destination costs, duration, and party size.
Provide a rough cost estimate range.""",
            "visa_timeline_risk": f"""You are a travel advisor assessing visa timeline risk.

Context:
{context}

Assess the visa timeline risk.
- "low" risk: Plenty of time for visa processing
- "medium" risk: Tight timeline but possible
- "high" risk: Insufficient time, recommend alternative""",
            "composition_risk": f"""You are a travel advisor assessing composition-related risks.

Context:
{context}

Assess any risks related to the party composition.
Consider age diversity, mobility requirements, and special needs.""",
        }

        return prompts.get(
            decision_type,
            f"Make a decision for {decision_type} based on:\n{context}"
        )

    def _extract_packet_context(self, packet: CanonicalPacket) -> str:
        """Extract readable context from packet for LLM prompts."""
        lines = []

        # Facts
        if packet.facts:
            lines.append("Facts:")
            for key, value in packet.facts.items():
                lines.append(f"  - {key}: {value}")

        # Derived signals
        if packet.derived_signals:
            lines.append("\nDerived Signals:")
            for key, value in packet.derived_signals.items():
                lines.append(f"  - {key}: {value}")

        return "\n".join(lines)

    def _cache_decision(
        self,
        decision_type: str,
        cache_key: str,
        decision: Dict[str, Any],
        source: str,
        llm_model: Optional[str] = None,
        cost: float = 0.0,
    ) -> None:
        """Cache a decision for future use."""
        try:
            now = datetime.now().isoformat()

            cached = CachedDecision(
                cache_key=cache_key,
                decision_type=decision_type,
                decision=decision,
                confidence=0.9 if source == "rule_engine" else 0.8,
                source=source,
                llm_model_used=llm_model,
                created_at=now,
                last_used_at=now,
                use_count=1,
                success_rate=1.0,
                feedback_count=0,
            )

            self.cache_storage.set(
                cache_key=cache_key,
                decision_type=decision_type,
                decision=cached,
            )
            logger.debug(f"Cached decision for {decision_type}: {cache_key[:8]}...")

        except Exception as e:
            logger.warning(f"Failed to cache decision: {e}")

    def get_metrics(self) -> EngineMetrics:
        """Get current engine metrics."""
        return self.metrics

    def get_cache_stats(self) -> CacheStats:
        """Get cache statistics."""
        return self.cache_storage.get_stats()


def create_hybrid_engine(
    enable_cache: bool = True,
    enable_rules: bool = True,
    enable_llm: bool = True,
) -> HybridDecisionEngine:
    """
    Factory function to create a hybrid decision engine.

    Reads configuration from environment variables.

    Environment variables:
        USE_HYBRID_DECISION_ENGINE: 0 or 1 (default: 1)
        LLM_PROVIDER: gemini, openai, local (default: gemini)
        DECISION_CACHE_TTL_DAYS: Cache TTL in days (default: 30)

    Args:
        enable_cache: Whether to use cache
        enable_rules: Whether to use rules
        enable_llm: Whether to use LLM

    Returns:
        Configured HybridDecisionEngine instance
    """
    import os

    enabled = os.environ.get("USE_HYBRID_DECISION_ENGINE", "1") == "1"

    if not enabled:
        # Return engine with only rules enabled
        return HybridDecisionEngine(
            enable_cache=False,
            enable_rules=True,
            enable_llm=False,
        )

    return HybridDecisionEngine(
        enable_cache=enable_cache,
        enable_rules=enable_rules,
        enable_llm=enable_llm,
    )
