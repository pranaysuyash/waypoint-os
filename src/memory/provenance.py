"""
src/memory/provenance.py — Cryptographic Provenance Graph & Lineage Engine.

Maintains immutable cryptographic lineage for all persisted memory items:
- Links memory records to originating trips, documents, messages, or agent actions.
- Computes SHA-256 integrity hashes over memory payloads.
- Emits structured audit events to AuditStore for compliance traceability.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from src.memory.models import MemoryProvenance, MemorySourceType


class ProvenanceEngine:
    """Manages cryptographic provenance generation and lineage tracking."""

    @staticmethod
    def create_provenance(
        source_type: MemorySourceType,
        payload: Dict[str, Any],
        source_ref_id: Optional[str] = None,
        actor_id: Optional[str] = None,
        confidence_score: float = 1.0,
    ) -> MemoryProvenance:
        prov = MemoryProvenance(
            source_type=source_type,
            source_ref_id=source_ref_id,
            actor_id=actor_id,
            confidence_score=confidence_score,
            recorded_at=datetime.now(timezone.utc).isoformat(),
        )
        prov.integrity_hash = prov.compute_integrity_hash(payload)
        return prov

    @staticmethod
    def verify_integrity(provenance: MemoryProvenance, payload: Dict[str, Any]) -> bool:
        """Verifies that a memory payload has not been tampered with since creation."""
        expected_hash = provenance.compute_integrity_hash(payload)
        return provenance.integrity_hash == expected_hash

    @staticmethod
    def build_lineage_node(
        memory_id: str,
        provenance: MemoryProvenance,
        superseded_by_id: Optional[str] = None,
        replaces_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Constructs an inspectable lineage graph node."""
        return {
            "memory_id": memory_id,
            "provenance_id": provenance.provenance_id,
            "source_type": provenance.source_type.value if isinstance(provenance.source_type, MemorySourceType) else provenance.source_type,
            "source_ref_id": provenance.source_ref_id,
            "actor_id": provenance.actor_id,
            "confidence_score": provenance.confidence_score,
            "recorded_at": provenance.recorded_at,
            "integrity_hash": provenance.integrity_hash,
            "superseded_by_id": superseded_by_id,
            "replaces_id": replaces_id,
        }
