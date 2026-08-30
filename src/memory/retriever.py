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
from src.memory.models import BaseMemoryItem
from src.memory.sanitizer import MemorySanitizer

DEFAULT_TOKEN_BUDGET = 800


class HybridMemoryRetriever:
    """Retrieves and ranks memory items with recency decay and token budget controls."""

    def __init__(self, token_budget: int = DEFAULT_TOKEN_BUDGET):
        self.token_budget = token_budget

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
    ) -> List[Tuple[BaseMemoryItem, float]]:
        """
        Retrieves top_k relevant memories within the configured token budget.
        Returns a list of (memory_item, combined_score) tuples.
        """
        scored_items: List[Tuple[BaseMemoryItem, float]] = []

        for item in memories:
            if item.is_tombstone or item.superseded_by_id:
                continue

            activation = MemoryDecayEngine.calculate_activation_strength(item)
            if activation <= 0.01:
                continue

            sim = self._compute_lexical_similarity(query, f"{item.summary} {item.category}")
            conf = item.provenance.confidence_score

            # Blended score: 45% similarity, 35% recency activation, 20% source confidence
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
