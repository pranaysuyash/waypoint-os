"""
decision.cache_schema — CachedDecision dataclass for hybrid decision engine.

This module defines the schema for caching LLM decisions to avoid future API calls.
Cached decisions are persisted to disk and reused when the same inputs occur.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional


@dataclass(slots=True)
class CachedDecision:
    """
    A compiled decision that can be reused without LLM.

    Each cache entry represents:
    - A specific decision type (e.g., elderly_mobility_risk)
    - The inputs that led to this decision (hashed as cache_key)
    - The decision itself
    - Metadata about usage and success rate
    """

    # Cache identification
    cache_key: str
    decision_type: str

    # The decision (what the rule engine or LLM returned)
    decision: Dict[str, Any]
    confidence: float

    # Provenance
    source: str  # "rule_engine", "llm_compiled", "human_verified"
    llm_model_used: Optional[str] = None
    created_at: str = ""

    # Usage tracking
    last_used_at: str = ""
    use_count: int = 0

    # Learning metadata
    success_rate: float = 1.0
    feedback_count: int = 0

    def __post_init__(self):
        """Set timestamps if not provided."""
        now = datetime.now(timezone.utc).isoformat()
        if not self.created_at:
            self.created_at = now
        if not self.last_used_at:
            self.last_used_at = now

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "cache_key": self.cache_key,
            "decision_type": self.decision_type,
            "decision": self.decision,
            "confidence": self.confidence,
            "source": self.source,
            "llm_model_used": self.llm_model_used,
            "created_at": self.created_at,
            "last_used_at": self.last_used_at,
            "use_count": self.use_count,
            "success_rate": self.success_rate,
            "feedback_count": self.feedback_count,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CachedDecision":
        """Create from dictionary (loaded from JSON)."""
        return cls(
            cache_key=data["cache_key"],
            decision_type=data["decision_type"],
            decision=data["decision"],
            confidence=data.get("confidence", 1.0),
            source=data.get("source", "unknown"),
            llm_model_used=data.get("llm_model_used"),
            created_at=data.get("created_at", ""),
            last_used_at=data.get("last_used_at", ""),
            use_count=data.get("use_count", 0),
            success_rate=data.get("success_rate", 1.0),
            feedback_count=data.get("feedback_count", 0),
        )

    def mark_used(self) -> None:
        """Update usage tracking when this cached decision is used."""
        self.use_count += 1
        self.last_used_at = datetime.now(timezone.utc).isoformat()

    def record_feedback(self, success: bool) -> None:
        """
        Record user feedback to update success rate.

        Args:
            success: True if the decision was good, False otherwise
        """
        self.feedback_count += 1
        # Update success rate using exponential moving average
        alpha = 2 / (self.feedback_count + 1)  # Adaptive learning rate
        if self.feedback_count == 1:
            self.success_rate = 1.0 if success else 0.0
        else:
            self.success_rate = alpha * (1.0 if success else 0.0) + (1 - alpha) * self.success_rate

    def is_valid(self, max_age_days: int = 30, min_success_rate: float = 0.7) -> bool:
        """
        Check if this cached decision is still valid to use.

        Args:
            max_age_days: Maximum age in days (default 30)
            min_success_rate: Minimum success rate (default 0.7)

        Returns:
            True if the cache entry should be used
        """
        # Check success rate
        if self.success_rate < min_success_rate:
            return False

        # Check age
        if self.created_at:
            try:
                created = datetime.fromisoformat(self.created_at)
                age = (datetime.now(timezone.utc) - created).days
                if age > max_age_days:
                    return False
            except (ValueError, TypeError):
                pass

        return True


@dataclass(slots=True)
class CacheStats:
    """Statistics about cache performance."""

    total_lookups: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    llm_calls: int = 0

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        if self.total_lookups == 0:
            return 0.0
        return self.cache_hits / self.total_lookups

    @property
    def miss_rate(self) -> float:
        """Calculate cache miss rate."""
        if self.total_lookups == 0:
            return 0.0
        return self.cache_misses / self.total_lookups

    def record_hit(self) -> None:
        """Record a cache hit."""
        self.total_lookups += 1
        self.cache_hits += 1

    def record_miss(self) -> None:
        """Record a cache miss."""
        self.total_lookups += 1
        self.cache_misses += 1

    def record_llm_call(self) -> None:
        """Record an LLM call (from cache miss)."""
        self.llm_calls += 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_lookups": self.total_lookups,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "llm_calls": self.llm_calls,
            "hit_rate": self.hit_rate,
            "miss_rate": self.miss_rate,
        }