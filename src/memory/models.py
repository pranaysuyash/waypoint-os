"""
src/memory/models.py — 5-Tier Agent Memory Models.

Defines the five canonical memory tiers:
1. Working Memory (in-flight context, active scratchpad, token-budgeted tool state)
2. Episodic Memory (trip milestones, disruption handling, historical interaction logs)
3. Semantic Memory (traveler profile affinities, loyalty IDs, dietary restrictions, family/companion entities)
4. Procedural Memory (agency policy rules, markup limits, supplier negotiation playbooks)
5. Preference / Autonomy Memory (explicit agency settings, agent autonomy gates, communication style)

Each memory unit includes cryptographic provenance, write eligibility metadata,
supersession linkage, and temporal half-life parameters.
"""

from __future__ import annotations

import enum
import hashlib
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class MemoryTier(str, enum.Enum):
    WORKING = "working"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"
    PREFERENCE = "preference"


class MemorySourceType(str, enum.Enum):
    TRAVELER_DIRECT = "traveler_direct"       # Highest authority (1.0)
    VERIFIED_DOCUMENT = "verified_document"   # High authority (0.95)
    AGENT_MANUAL = "agent_manual"             # High authority (0.90)
    GDS_IMPORT = "gds_import"                 # Authoritative external feed (0.90)
    SYSTEM_INFERRED = "system_inferred"       # Probabilistic extraction (0.75)
    THIRD_PARTY_WEB = "third_party_web"       # Low confidence baseline (0.60)


SOURCE_CONFIDENCE_WEIGHTS: Dict[MemorySourceType, float] = {
    MemorySourceType.TRAVELER_DIRECT: 1.0,
    MemorySourceType.VERIFIED_DOCUMENT: 0.95,
    MemorySourceType.AGENT_MANUAL: 0.90,
    MemorySourceType.GDS_IMPORT: 0.90,
    MemorySourceType.SYSTEM_INFERRED: 0.75,
    MemorySourceType.THIRD_PARTY_WEB: 0.60,
}


class SourceTrustClass(str, enum.Enum):
    """FND-0230 / E-D: coarse trust classes every memory write records.

    Memory influence must be proportional to trust, so the read seam
    (slot_candidates) and any audit surface can reason over four
    canonical classes instead of six fine-grained source types:
    - explicit_user:   the traveler stated it (or a verified document says so)
    - derived:         extracted/derived from an authoritative feed or system inference
    - agent_inferred:  an agent authored it from judgment, not traveler speech
    - system_default:  low-authority external/default material
    """

    EXPLICIT_USER = "explicit_user"
    DERIVED = "derived"
    AGENT_INFERRED = "agent_inferred"
    SYSTEM_DEFAULT = "system_default"


SOURCE_TRUST_CLASS: Dict[MemorySourceType, SourceTrustClass] = {
    MemorySourceType.TRAVELER_DIRECT: SourceTrustClass.EXPLICIT_USER,
    MemorySourceType.VERIFIED_DOCUMENT: SourceTrustClass.EXPLICIT_USER,
    MemorySourceType.AGENT_MANUAL: SourceTrustClass.AGENT_INFERRED,
    MemorySourceType.GDS_IMPORT: SourceTrustClass.DERIVED,
    MemorySourceType.SYSTEM_INFERRED: SourceTrustClass.DERIVED,
    MemorySourceType.THIRD_PARTY_WEB: SourceTrustClass.SYSTEM_DEFAULT,
}

# Relative influence weight per trust class (E-D: influence proportional to
# trust; only explicit_user-class memories carry full authority).
TRUST_CLASS_WEIGHTS: Dict[SourceTrustClass, float] = {
    SourceTrustClass.EXPLICIT_USER: 1.0,
    SourceTrustClass.DERIVED: 0.6,
    SourceTrustClass.AGENT_INFERRED: 0.4,
    SourceTrustClass.SYSTEM_DEFAULT: 0.2,
}


def clamp_confidence(value: Any, *, label: str = "confidence") -> float:
    """Clamp a trust/confidence signal into [0.0, 1.0] — never skip.

    Data-loss-prevention pattern (AGENTS.md): an out-of-range trust signal is
    clamped and logged, never silently dropped or passed through distorted
    (an unclamped 2.7 previously blended into a persisted confidence > 1.0).
    """
    try:
        num = float(value)
    except (TypeError, ValueError):
        logger.warning(
            "memory trust signal %s=%r not numeric; clamping to 0.0", label, value
        )
        return 0.0
    if num != num:  # NaN
        logger.warning("memory trust signal %s=NaN; clamping to 0.0", label)
        return 0.0
    clamped = max(0.0, min(1.0, num))
    if clamped != num:
        logger.warning(
            "memory trust signal %s=%r out of range; clamped to %.2f", label, value, clamped
        )
    return round(clamped, 4)


@dataclass(slots=True)
class MemoryProvenance:
    """Cryptographic provenance record for an individual memory unit."""
    provenance_id: str = field(default_factory=lambda: f"prov_{uuid.uuid4().hex[:12]}")
    source_type: MemorySourceType = MemorySourceType.TRAVELER_DIRECT
    source_ref_id: Optional[str] = None     # e.g., trip_id, doc_id, message_id
    actor_id: Optional[str] = None          # e.g., user_id, agent_id, customer_id
    confidence_score: float = 1.0           # 0.0 - 1.0
    recorded_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    integrity_hash: str = ""

    def compute_integrity_hash(self, payload_dict: Dict[str, Any]) -> str:
        payload_str = json.dumps(payload_dict, sort_keys=True, default=str)
        raw = f"{self.provenance_id}:{self.source_type.value}:{self.source_ref_id}:{self.actor_id}:{self.recorded_at}:{payload_str}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()


@dataclass(slots=True)
class BaseMemoryItem:
    """Base dataclass for all memory items across the 5 tiers."""
    memory_id: str = field(default_factory=lambda: f"mem_{uuid.uuid4().hex[:12]}")
    agency_id: str = "default_agency"
    tier: MemoryTier = MemoryTier.SEMANTIC
    entity_id: str = ""                     # traveler_id, trip_id, agency_id, or session_id
    category: str = "general"               # dietary, seating, loyalty, disruption, policy, etc.
    summary: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    provenance: MemoryProvenance = field(default_factory=MemoryProvenance)
    valid_from: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    valid_until: Optional[str] = None
    half_life_days: Optional[float] = None  # None = never decays (infinite half-life)
    superseded_by_id: Optional[str] = None
    is_tombstone: bool = False              # True if forgotten via GDPR Article 17
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "memory_id": self.memory_id,
            "agency_id": self.agency_id,
            "tier": self.tier.value if isinstance(self.tier, MemoryTier) else self.tier,
            "entity_id": self.entity_id,
            "category": self.category,
            "summary": self.summary,
            "payload": self.payload,
            "provenance": {
                "provenance_id": self.provenance.provenance_id,
                "source_type": self.provenance.source_type.value if isinstance(self.provenance.source_type, MemorySourceType) else self.provenance.source_type,
                "source_ref_id": self.provenance.source_ref_id,
                "actor_id": self.provenance.actor_id,
                "confidence_score": self.provenance.confidence_score,
                "recorded_at": self.provenance.recorded_at,
                "integrity_hash": self.provenance.integrity_hash,
            },
            "valid_from": self.valid_from,
            "valid_until": self.valid_until,
            "half_life_days": self.half_life_days,
            "superseded_by_id": self.superseded_by_id,
            "is_tombstone": self.is_tombstone,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> BaseMemoryItem:
        prov_data = data.get("provenance", {})
        prov = MemoryProvenance(
            provenance_id=prov_data.get("provenance_id", f"prov_{uuid.uuid4().hex[:12]}"),
            source_type=MemorySourceType(prov_data.get("source_type", MemorySourceType.TRAVELER_DIRECT.value)),
            source_ref_id=prov_data.get("source_ref_id"),
            actor_id=prov_data.get("actor_id"),
            confidence_score=float(prov_data.get("confidence_score", 1.0)),
            recorded_at=prov_data.get("recorded_at", datetime.now(timezone.utc).isoformat()),
            integrity_hash=prov_data.get("integrity_hash", ""),
        )
        return cls(
            memory_id=data["memory_id"],
            agency_id=data.get("agency_id", "default_agency"),
            tier=MemoryTier(data.get("tier", MemoryTier.SEMANTIC.value)),
            entity_id=data.get("entity_id", ""),
            category=data.get("category", "general"),
            summary=data.get("summary", ""),
            payload=data.get("payload", {}),
            provenance=prov,
            valid_from=data.get("valid_from", datetime.now(timezone.utc).isoformat()),
            valid_until=data.get("valid_until"),
            half_life_days=data.get("half_life_days"),
            superseded_by_id=data.get("superseded_by_id"),
            is_tombstone=data.get("is_tombstone", False),
            created_at=data.get("created_at", datetime.now(timezone.utc).isoformat()),
            updated_at=data.get("updated_at", datetime.now(timezone.utc).isoformat()),
        )


@dataclass(slots=True)
class WorkingMemoryItem(BaseMemoryItem):
    """Tier 1: Short-term scratchpad & in-flight reasoning state."""
    session_id: str = ""
    step_name: str = ""
    token_cost: int = 0
    expires_at_run_end: bool = True

    def __post_init__(self):
        self.tier = MemoryTier.WORKING
        if self.half_life_days is None:
            self.half_life_days = 0.05  # Decay rapidly in working memory (~1 hr)


@dataclass(slots=True)
class EpisodicMemoryRecord(BaseMemoryItem):
    """Tier 2: Discrete historical trip interaction and disruption resolution."""
    trip_id: str = ""
    event_type: str = "interaction"         # disruption_resolved, booking_modified, escalation
    outcome_sentiment: str = "positive"     # positive, neutral, negative
    remediation_applied: Optional[str] = None

    def __post_init__(self):
        self.tier = MemoryTier.EPISODIC
        if self.half_life_days is None:
            self.half_life_days = 365.0  # 1 year half-life for episodic recall


@dataclass(slots=True)
class SemanticMemoryFact(BaseMemoryItem):
    """Tier 3: Enduring traveler profile affinities, loyalty IDs, dietary/medical safety constraints."""
    customer_id: str = ""
    fact_key: str = ""                      # e.g., "dietary_requirement", "loyalty_delta", "seating"
    fact_value: Any = None
    is_safety_critical: bool = False        # Medical / food allergy = infinite half-life

    def __post_init__(self):
        self.tier = MemoryTier.SEMANTIC
        if self.is_safety_critical:
            self.half_life_days = None      # Never decays
        elif self.half_life_days is None:
            self.half_life_days = 730.0     # 2 year default half-life


@dataclass(slots=True)
class ProceduralRule(BaseMemoryItem):
    """Tier 4: Agency policy rules, supplier negotiation tactics, escalation playbooks."""
    rule_name: str = ""
    conditions: Dict[str, Any] = field(default_factory=dict)
    actions: Dict[str, Any] = field(default_factory=dict)
    precedence: int = 100

    def __post_init__(self):
        self.tier = MemoryTier.PROCEDURAL
        self.half_life_days = None          # Procedural policies don't decay automatically


@dataclass(slots=True)
class PreferenceProfile(BaseMemoryItem):
    """Tier 5: Agency operating preferences, autonomy thresholds, communication tone."""
    autonomy_level: str = "human_in_the_loop"
    notification_cadence: str = "daily"
    risk_tolerance: str = "conservative"

    def __post_init__(self):
        self.tier = MemoryTier.PREFERENCE
        self.half_life_days = None


@dataclass(slots=True)
class GDPRForgetCertificate:
    """Cryptographic certificate proving complete Right-to-Erasure compliance."""
    certificate_id: str = field(default_factory=lambda: f"gdpr_cert_{uuid.uuid4().hex[:12]}")
    agency_id: str = ""
    customer_id: str = ""
    erased_memory_ids: List[str] = field(default_factory=list)
    tombstone_count: int = 0
    erased_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    verification_signature: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "certificate_id": self.certificate_id,
            "agency_id": self.agency_id,
            "customer_id": self.customer_id,
            "erased_memory_ids": self.erased_memory_ids,
            "tombstone_count": self.tombstone_count,
            "erased_at": self.erased_at,
            "verification_signature": self.verification_signature,
        }
