"""
src/memory/store.py — Durable Multi-Tenant Memory Store.

Implements RLS-isolated, file-backed durable persistence for 5-Tier Agent Memory.
Integrates:
- Write Eligibility Gate
- Provenance & Cryptographic Lineage Engine
- Conflict Detection & Supersession Engine
- Temporal Half-Life Decay Engine
- GDPR Article 17 Right-to-Erasure Engine
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from src.memory.eligibility_gate import MemoryEligibilityGate
from src.memory.gdpr_engine import GDPRMemoryEngine
from src.memory.models import (
    BaseMemoryItem,
    GDPRForgetCertificate,
    MemorySourceType,
    MemoryTier,
)
from src.memory.provenance import ProvenanceEngine
from src.memory.retriever import HybridMemoryRetriever
from src.memory.sanitizer import MemorySanitizer
from src.memory.supersession import SupersessionEngine

logger = logging.getLogger(__name__)


class MemoryStore:
    """Tenant-isolated, durable store managing 5-Tier Agent Memory."""

    DATA_DIR = Path("data/memory")
    STORE_FILE = DATA_DIR / "memory_store.jsonl"

    def __init__(self, data_file: Optional[Path] = None):
        from src.security.path_guard import validate_filename

        self.file_path = data_file or self.STORE_FILE
        # Canonical filename containment guard for the store file.
        validate_filename(self.file_path.name, label="memory store file")
        self._memory_cache: Dict[str, List[BaseMemoryItem]] = {}  # agency_id -> items
        self.eligibility_gate = MemoryEligibilityGate()
        self.retriever = HybridMemoryRetriever()
        self._load()

    def _load(self) -> None:
        """Loads memories from JSONL file into tenant-indexed memory cache."""
        self._memory_cache.clear()
        if not self.file_path.exists():
            return

        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        item = BaseMemoryItem.from_dict(data)
                        agency = item.agency_id
                        if agency not in self._memory_cache:
                            self._memory_cache[agency] = []
                        self._memory_cache[agency].append(item)
                    except Exception as err:
                        logger.warning("Failed to parse memory record: %s", err)
        except Exception as e:
            logger.error("Failed to load memory store from %s: %s", self.file_path, e)

    def _save(self) -> None:
        """Persists memory cache atomically to JSONL file."""
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        temp_file = self.file_path.with_suffix(".tmp")
        try:
            with open(temp_file, "w", encoding="utf-8") as f:
                for items in self._memory_cache.values():
                    for item in items:
                        f.write(json.dumps(item.to_dict()) + "\n")
            temp_file.replace(self.file_path)
        except Exception as e:
            logger.error("Failed to save memory store: %s", e)
            if temp_file.exists():
                temp_file.unlink()

    def ingest_memory(
        self,
        agency_id: str,
        entity_id: str,
        raw_text: str,
        source_type: MemorySourceType,
        payload: Optional[Dict[str, Any]] = None,
        source_ref_id: Optional[str] = None,
        actor_id: Optional[str] = None,
        category_hint: Optional[str] = None,
        explicit_confidence: Optional[float] = None,
        is_safety_critical: bool = False,
        half_life_days: Optional[float] = None,
    ) -> Tuple[Optional[BaseMemoryItem], str]:
        """
        Ingests a candidate fact through the Write Eligibility Gate, checks for
        supersession conflicts, and persists the memory item.

        Write-time hygiene (E-10): raw_text and payload are prompt-injection
        sanitized BEFORE gate evaluation and hashing, so persisted summaries
        and provenance hashes always describe sanitized content.

        half_life_days: optional per-write decay override. When None, the
        tier default applies (SEMANTIC → 730d, else never/episodic default).
        Event-class bridges (e.g. feedback outcomes) pass explicit values —
        a single mechanism (decay curve) then enforces "implicit signals need
        repetition to matter" without a separate suppression system.
        """

        raw_text = MemorySanitizer.sanitize_text(raw_text or "")
        sanitized_payload = MemorySanitizer.sanitize_payload(payload or {})
        payload = sanitized_payload if payload is not None else None

        eval_res = self.eligibility_gate.evaluate(
            raw_text=raw_text,
            source_type=source_type,
            explicit_confidence=explicit_confidence,
            category_hint=category_hint,
            entity_id=entity_id,
        )

        if not eval_res.is_eligible:
            return None, f"Rejected: {eval_res.rejection_reason}"

        payload_dict = payload or {"raw_text": raw_text}

        # Build provenance
        prov = ProvenanceEngine.create_provenance(
            source_type=source_type,
            payload=payload_dict,
            source_ref_id=source_ref_id,
            actor_id=actor_id,
            confidence_score=eval_res.confidence_score,
        )

        # Build memory item
        candidate = BaseMemoryItem(
            agency_id=agency_id,
            tier=eval_res.tier,
            entity_id=entity_id,
            category=eval_res.extracted_category,
            summary=MemorySanitizer.sanitize_text(eval_res.sanitized_summary),
            payload=payload_dict,
            provenance=prov,
            half_life_days=(
                half_life_days
                if half_life_days is not None
                else None if is_safety_critical
                else (730.0 if eval_res.tier == MemoryTier.SEMANTIC else None)
            ),
        )

        # Check supersession against existing memories for this entity
        existing_items = self._memory_cache.get(agency_id, [])
        for item in existing_items:
            if item.entity_id == entity_id and SupersessionEngine.detect_conflict(item, candidate):
                should_supersede, reason = SupersessionEngine.resolve_supersession(item, candidate)
                if should_supersede:
                    SupersessionEngine.apply_supersession(item, candidate)
                    logger.info("Superseded memory %s: %s", item.memory_id, reason)

        if agency_id not in self._memory_cache:
            self._memory_cache[agency_id] = []
        self._memory_cache[agency_id].append(candidate)
        self._save()

        return candidate, "Persisted successfully"

    def query_memories(
        self,
        agency_id: str,
        query: str,
        entity_id: Optional[str] = None,
        tier: Optional[MemoryTier] = None,
        top_k: int = 10,
    ) -> List[Tuple[BaseMemoryItem, float]]:
        """Queries memories for a specific agency using hybrid recency retrieval."""
        items = self._memory_cache.get(agency_id, [])
        if entity_id:
            items = [i for i in items if i.entity_id == entity_id]
        if tier:
            items = [i for i in items if i.tier == tier]

        return self.retriever.retrieve(query=query, memories=items, top_k=top_k)

    def list_entity_memories(
        self,
        agency_id: str,
        entity_id: str,
        include_superseded: bool = False,
    ) -> List[BaseMemoryItem]:
        """Lists active memories for an entity within an agency."""
        items = self._memory_cache.get(agency_id, [])
        result = []
        for item in items:
            if item.entity_id == entity_id:
                if not include_superseded and (item.superseded_by_id or item.is_tombstone):
                    continue
                result.append(item)
        return result

    def forget_entity_gdpr(
        self,
        agency_id: str,
        entity_id: str,
    ) -> GDPRForgetCertificate:
        """Executes GDPR Article 17 Right-to-Erasure for an entity."""
        items = self._memory_cache.get(agency_id, [])
        updated_items, cert = GDPRMemoryEngine.erase_entity_memories(
            memories=items,
            agency_id=agency_id,
            entity_id=entity_id,
        )
        self._memory_cache[agency_id] = updated_items
        self._save()
        return cert
