"""
src/memory/gdpr_engine.py — GDPR Article 17 Right-to-Erasure Engine.

Executes compliant customer memory erasure:
- Performs cascading deletion across all memory items linked to a customer/entity.
- Replaces active records with cryptographically signed tombstone receipts.
- Strips all PII while generating an auditable GDPRForgetCertificate.
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
import os
from typing import List, Optional, Tuple

from src.memory.models import BaseMemoryItem, GDPRForgetCertificate


class GDPRMemoryEngine:
    """Executes Right-to-Erasure workflows and issues cryptographic certificates."""

    @staticmethod
    def erase_entity_memories(
        memories: List[BaseMemoryItem],
        agency_id: str,
        entity_id: str,
        secret_key: Optional[str] = None,
    ) -> Tuple[List[BaseMemoryItem], GDPRForgetCertificate]:
        """
        Erases all PII from memories belonging to entity_id within agency_id.
        Tombstones the records and returns a verifiable GDPRForgetCertificate.
        """
        resolved_key = (
            secret_key
            or os.getenv("GDPR_SIGNING_KEY")
            or os.getenv("ENCRYPTION_KEY")
            or ""
        ).strip()
        if not resolved_key:
            env = (os.getenv("ENVIRONMENT") or os.getenv("WAYPOINT_ENV") or "").lower()
            if env in ("production", "staging"):
                raise RuntimeError(
                    "GDPR erasure requires GDPR_SIGNING_KEY or ENCRYPTION_KEY in production/staging; "
                    "refusing to issue unsigned certificates."
                )
            resolved_key = "waypoint-gdpr-secret-key-2026"

        erased_ids = []
        updated_memories = []

        now_iso = datetime.now(timezone.utc).isoformat()

        for item in memories:
            if item.agency_id == agency_id and item.entity_id == entity_id:
                erased_ids.append(item.memory_id)
                # Tombstone the item
                item.is_tombstone = True
                item.summary = "[REDACTED - GDPR ARTICLE 17 ERASURE]"
                item.payload = {"erased_at": now_iso, "status": "tombstoned"}
                item.updated_at = now_iso
                updated_memories.append(item)
            else:
                updated_memories.append(item)

        cert_id = f"cert_{uuid.uuid4().hex[:12]}"
        raw_sig = f"{cert_id}:{agency_id}:{entity_id}:{len(erased_ids)}:{now_iso}:{secret_key}"
        sig_hash = hashlib.sha256(raw_sig.encode("utf-8")).hexdigest()

        cert = GDPRForgetCertificate(
            certificate_id=cert_id,
            agency_id=agency_id,
            customer_id=entity_id,
            erased_memory_ids=erased_ids,
            tombstone_count=len(erased_ids),
            erased_at=now_iso,
            verification_signature=sig_hash,
        )

        return updated_memories, cert
