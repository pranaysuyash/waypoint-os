"""
src/memory/supersession.py — Conflict Resolution & Memory Supersession Engine.

Handles semantic contradiction detection, precedence conflict resolution,
and explicit supersession chains across agent memory records.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, Tuple

from src.memory.models import BaseMemoryItem, MemorySourceType, SOURCE_CONFIDENCE_WEIGHTS


class SupersessionEngine:
    """Detects and resolves contradictory memory facts, applying supersession chains."""

    @staticmethod
    def detect_conflict(
        existing_item: BaseMemoryItem,
        candidate_item: BaseMemoryItem,
    ) -> bool:
        """Determines if a candidate memory item conflicts with an existing item."""
        if existing_item.is_tombstone or existing_item.superseded_by_id:
            return False

        # Same entity and same specific key/category
        if existing_item.entity_id != candidate_item.entity_id:
            return False

        if existing_item.category != candidate_item.category:
            return False

        # Compare payload keys for overlapping but different values
        for key, val in candidate_item.payload.items():
            if key in existing_item.payload and existing_item.payload[key] != val:
                return True

        return False

    @staticmethod
    def resolve_supersession(
        existing_item: BaseMemoryItem,
        candidate_item: BaseMemoryItem,
    ) -> Tuple[bool, Optional[str]]:
        """
        Evaluates whether candidate_item should supersede existing_item.
        Returns: (should_supersede: bool, reason: str)
        """
        cand_weight = SOURCE_CONFIDENCE_WEIGHTS.get(
            candidate_item.provenance.source_type, 0.5
        )
        exist_weight = SOURCE_CONFIDENCE_WEIGHTS.get(
            existing_item.provenance.source_type, 0.5
        )

        # 1. Direct traveler input always supersedes older inferences or web data
        if candidate_item.provenance.source_type == MemorySourceType.TRAVELER_DIRECT:
            if existing_item.provenance.source_type != MemorySourceType.TRAVELER_DIRECT:
                return True, "Direct traveler instruction overrides inferred/legacy source"

        # 2. Compare confidence scores
        if candidate_item.provenance.confidence_score > existing_item.provenance.confidence_score + 0.15:
            return True, f"Candidate confidence ({candidate_item.provenance.confidence_score:.2f}) significantly exceeds existing ({existing_item.provenance.confidence_score:.2f})"

        # 3. If sources are equally authoritative, newer timestamp wins
        if cand_weight >= exist_weight:
            if candidate_item.created_at >= existing_item.created_at:
                return True, "More recent authoritative observation supersedes older record"

        return False, "Existing memory has higher authority/confidence"

    @staticmethod
    def apply_supersession(
        existing_item: BaseMemoryItem,
        candidate_item: BaseMemoryItem,
    ) -> None:
        """Links existing and candidate items into a supersession chain."""
        existing_item.superseded_by_id = candidate_item.memory_id
        existing_item.updated_at = datetime.now(timezone.utc).isoformat()
