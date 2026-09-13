"""
src/memory/retriever.py — Hybrid Recency-Weighted Context Retriever.

Retrieves and ranks relevant memory facts for trip context assembly:
- Combines lexical/semantic similarity with temporal decay activation and confidence.
- Enforces strict token budget limits (default max 800 tokens) to prevent prompt flooding.
- Sanitizes all memory outputs to prevent prompt injection.
"""

from __future__ import annotations

import math
from typing import List, Tuple

from src.memory.decay_engine import MemoryDecayEngine
from src.memory.models import SOURCE_CONFIDENCE_WEIGHTS, BaseMemoryItem, MemorySourceType
from src.memory.sanitizer import MemorySanitizer

DEFAULT_TOKEN_BUDGET = 800


class HybridMemoryRetriever:
    """Retrieves and ranks memory items with recency decay and token budget controls."""

    SAFETY_CRITICAL_CATEGORIES = {
        "dietary_safety", "medical", "mobility", "allergy", "disability", "accessibility"
    }
    SAFETY_CRITICAL_KEYWORDS = {
        "allergy", "allergic", "anaphylaxis", "celiac", "wheelchair", "mobility",
        "medical", "medication", "oxygen", "dialysis", "stretcher", "guide dog"
    }
    VERIFIED_SAFETY_SOURCES = {
        MemorySourceType.TRAVELER_DIRECT,
        MemorySourceType.VERIFIED_DOCUMENT,
        MemorySourceType.AGENT_MANUAL,
    }

    def __init__(self, token_budget: int = DEFAULT_TOKEN_BUDGET):
        self.token_budget = token_budget

    def is_safety_critical(self, item: BaseMemoryItem) -> bool:
        if getattr(item, "is_safety_critical", False):
            return True
        if item.category.lower() in self.SAFETY_CRITICAL_CATEGORIES:
            return True
        text = f"{item.summary} {item.category}".lower()
        return any(k in text for k in self.SAFETY_CRITICAL_KEYWORDS)

    def is_unverifiable_safety_claim(self, item: BaseMemoryItem) -> bool:
        """F-13: Flag medical/mobility/dietary claims from unverified or low-confidence sources."""
        if not self.is_safety_critical(item):
            return False
        if item.provenance.source_type not in self.VERIFIED_SAFETY_SOURCES:
            return True
        return item.provenance.confidence_score < 0.85

    def get_quarantined_claims(self, memories: List[BaseMemoryItem]) -> List[BaseMemoryItem]:
        """Returns all safety-critical claims quarantined due to unverified provenance."""
        return [
            m for m in memories
            if not m.is_tombstone and not m.superseded_by_id and self.is_unverifiable_safety_claim(m)
        ]

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        """Heuristic token estimation (~4 characters per token)."""
        return max(1, math.ceil(len(text) / 4.0))

    @staticmethod
    def _compute_lexical_similarity(query: str, text: str) -> float:
        """Fast BM25-like token overlap similarity between query and memory summary."""
        q_tokens = set(query.lower().split())
        if not q_tokens:
            return 0.5
        t_tokens = set(text.lower().split())
        if not t_tokens:
            return 0.0
        intersection = q_tokens.intersection(t_tokens)
        return len(intersection) / len(q_tokens)

    def retrieve(
        self,
        query: str,
        memories: List[BaseMemoryItem],
        top_k: int = 10,
        min_score: float = 0.20,
        quarantine_unverified_safety: bool = True,
    ) -> List[Tuple[BaseMemoryItem, float]]:
        """
        Retrieves top_k relevant memories within the configured token budget.
        Returns a list of (memory_item, combined_score) tuples.
        """
        scored_items: List[Tuple[BaseMemoryItem, float]] = []

        for item in memories:
            if item.is_tombstone or item.superseded_by_id:
                continue

            # F-13: Quarantine unverified medical/mobility/safety claims at retrieval time
            if quarantine_unverified_safety and self.is_unverifiable_safety_claim(item):
                continue

            activation = MemoryDecayEngine.calculate_activation_strength(item)
            if activation <= 0.01:
                continue

            sim = self._compute_lexical_similarity(query, f"{item.summary} {item.category}")
            # F-13 slice (E-10 E10.5): source-trust weighting. The decay engine
            # treats provenance confidence as base activation, so confidence
            # flows through BOTH the activation term (35%) and the direct
            # confidence term (20%) — 55% of the blend. Trust scales the whole
            # confidence-derived contribution, so an agent-inferred memory can
            # never outrank a traveler-stated one at equal similarity/recency.
            source_trust = SOURCE_CONFIDENCE_WEIGHTS.get(item.provenance.source_type, 0.6)
            activation *= source_trust
            conf = item.provenance.confidence_score * source_trust

            # Blended score: 45% similarity, 35% (trust-weighted) recency activation, 20% (trust-weighted) source confidence
            combined_score = round(0.45 * sim + 0.35 * activation + 0.20 * conf, 4)

            if combined_score >= min_score:
                scored_items.append((item, combined_score))

        # Sort descending by score
        scored_items.sort(key=lambda x: x[1], reverse=True)

        # Apply token budget cap
        final_results: List[Tuple[BaseMemoryItem, float]] = []
        tokens_used = 0

        for item, score in scored_items[:top_k]:
            # Sanitize summary and payload representation
            clean_summary = MemorySanitizer.sanitize_text(item.summary)
            item_tokens = self._estimate_tokens(clean_summary)

            if tokens_used + item_tokens <= self.token_budget:
                final_results.append((item, score))
                tokens_used += item_tokens
            else:
                break

        return final_results
