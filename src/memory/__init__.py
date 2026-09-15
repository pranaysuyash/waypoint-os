"""
src/memory — 5-Tier Agent Memory Engine for Waypoint OS.

Architected under PER-0717: Agent Memory Architect.
Provides typed Working, Episodic, Semantic, Procedural, and Preference memory tiers
with cryptographic provenance, write eligibility gates, temporal half-life decay,
supersession chains, and GDPR Article 17 Right-to-Erasure.
"""

from src.memory.models import (
    MemoryTier,
    MemorySourceType,
    BaseMemoryItem,
    WorkingMemoryItem,
    EpisodicMemoryRecord,
    SemanticMemoryFact,
    ProceduralRule,
    PreferenceProfile,
    MemoryProvenance,
    GDPRForgetCertificate,
    SourceTrustClass,
    SOURCE_TRUST_CLASS,
    TRUST_CLASS_WEIGHTS,
    clamp_confidence,
)
from src.memory.relationship_stages import (
    RelationshipStage,
    RelationshipRecord,
    validate_relationship_record,
    apply_trip_event,
    apply_decay,
    derived_signal,
)

__all__ = [
    "MemoryTier",
    "MemorySourceType",
    "BaseMemoryItem",
    "WorkingMemoryItem",
    "EpisodicMemoryRecord",
    "SemanticMemoryFact",
    "ProceduralRule",
    "PreferenceProfile",
    "MemoryProvenance",
    "GDPRForgetCertificate",
    "SourceTrustClass",
    "SOURCE_TRUST_CLASS",
    "TRUST_CLASS_WEIGHTS",
    "clamp_confidence",
    "RelationshipStage",
    "RelationshipRecord",
    "validate_relationship_record",
    "apply_trip_event",
    "apply_decay",
    "derived_signal",
]
