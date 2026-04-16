"""
decision — Hybrid decision engine with rules, caching, and LLM integration.

This module provides a cost-optimized decision engine that:
1. Checks cache first (₹0)
2. Tries rule engine (₹0)
3. Falls back to LLM only when needed (₹0.10-₹1 per decision)

Exports:
    - HybridDecisionEngine: Main decision orchestrator
    - DecisionResult: Result wrapper with metadata
    - EngineMetrics: Performance metrics tracking
    - CachedDecision: Cache entry schema
    - DecisionCacheStorage: Cache persistence layer
    - generate_cache_key: Cache key generation
"""

from .cache_schema import CachedDecision, CacheStats
from .cache_storage import DecisionCacheStorage, get_default_storage
from .cache_key import generate_cache_key
from .hybrid_engine import (
    HybridDecisionEngine,
    DecisionResult,
    EngineMetrics,
    create_hybrid_engine,
)

__all__ = [
    # Core engine
    "HybridDecisionEngine",
    "DecisionResult",
    "EngineMetrics",
    "create_hybrid_engine",
    # Cache
    "CachedDecision",
    "CacheStats",
    "DecisionCacheStorage",
    "get_default_storage",
    "generate_cache_key",
]
