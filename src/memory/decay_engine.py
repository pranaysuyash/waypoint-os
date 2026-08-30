"""
src/memory/decay_engine.py — Temporal Decay & Half-Life Calculation Engine.

Calculates memory relevance and activation strength over time using exponential
decay models:
    A(t) = A_0 * 2^(-elapsed_days / half_life_days)

Permanent safety facts (e.g. food allergies) have an infinite half-life (no decay).
Transient preferences (e.g. seasonal vibes) decay over months.
"""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Optional

from src.memory.models import BaseMemoryItem


class MemoryDecayEngine:
    """Calculates temporal decay and current activation strength for memory items."""

    @staticmethod
    def calculate_activation_strength(
        memory_item: BaseMemoryItem,
        as_of: Optional[datetime] = None,
    ) -> float:
        """
        Calculates current activation strength [0.0 - 1.0].
        Base activation starts at provenance confidence score.
        """
        if memory_item.is_tombstone or memory_item.superseded_by_id:
            return 0.0

        as_of_dt = as_of or datetime.now(timezone.utc)
        base_confidence = memory_item.provenance.confidence_score

        # If no half_life is specified, memory does not decay
        if memory_item.half_life_days is None or memory_item.half_life_days <= 0:
            return base_confidence

        try:
            created_dt = datetime.fromisoformat(memory_item.created_at.replace("Z", "+00:00"))
        except Exception:
            created_dt = as_of_dt

        elapsed_seconds = (as_of_dt - created_dt).total_seconds()
        if elapsed_seconds <= 0:
            return base_confidence

        elapsed_days = elapsed_seconds / 86400.0
        decay_factor = math.pow(2.0, -elapsed_days / memory_item.half_life_days)
        activation = round(base_confidence * decay_factor, 4)

        return max(0.0, min(1.0, activation))

    @staticmethod
    def is_active(
        memory_item: BaseMemoryItem,
        activation_threshold: float = 0.25,
        as_of: Optional[datetime] = None,
    ) -> bool:
        """Determines if a memory item is currently active and above threshold."""
        if memory_item.is_tombstone or memory_item.superseded_by_id:
            return False

        # Check explicit valid_until
        if memory_item.valid_until:
            try:
                valid_until_dt = datetime.fromisoformat(memory_item.valid_until.replace("Z", "+00:00"))
                as_of_dt = as_of or datetime.now(timezone.utc)
                if as_of_dt > valid_until_dt:
                    return False
            except Exception:
                pass

        strength = MemoryDecayEngine.calculate_activation_strength(memory_item, as_of)
        return strength >= activation_threshold
