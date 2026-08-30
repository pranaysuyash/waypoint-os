"""
src/intake/epistemic_engine.py — Epistemic truth, provenance tracking, and conflict arbitration engine.

Grounding doctrine:
- PER-0922 & PER-0923 (Epistemic & Evidence Architects): Ground truth discrimination, confidence decay, and conflict detection.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger("src.intake.epistemic_engine")


class EpistemicCategory(str, Enum):
    FACT = "FACT"                  # Direct, unambiguous customer or document statement
    INFERRED = "INFERRED"          # Logically derived from facts (e.g. Paris -> CDG)
    ASSUMED = "ASSUMED"            # Default placeholder requiring customer confirmation
    UNKNOWN = "UNKNOWN"            # Unspecified parameter


@dataclass(slots=True)
class ProvenanceSlot:
    """A single extracted parameter with full epistemic provenance."""
    field_name: str
    value: Any
    category: EpistemicCategory
    confidence: float              # 0.0 to 1.0
    source_turn_id: Optional[str] = None
    extracted_snippet: Optional[str] = None
    last_verified_at: float = field(default_factory=time.time)
    decay_rate_per_day: float = 0.05  # 5% confidence loss per day for volatile attributes


@dataclass(slots=True)
class EpistemicConflict:
    """Detected contradiction between two conversational turns or data sources."""
    field_name: str
    previous_value: Any
    previous_source: str
    new_value: Any
    new_source: str
    severity: str                  # BLOCKING, WARNING
    resolution_status: str         # UNRESOLVED, OPERATOR_RESOLVED, CLIENT_RESOLVED


class EpistemicEngine:
    """Orchestrates truth classification, confidence decay, and conflict arbitration."""

    @staticmethod
    def calculate_decayed_confidence(slot: ProvenanceSlot, current_time: Optional[float] = None) -> float:
        """Apply temporal confidence decay based on elapsed days since last verification."""
        now = current_time or time.time()
        elapsed_days = (now - slot.last_verified_at) / 86400.0
        decay = max(0.0, elapsed_days * slot.decay_rate_per_day)
        return max(0.05, round(slot.confidence - decay, 3))

    @staticmethod
    def detect_conflicts(
        existing_slots: Dict[str, ProvenanceSlot],
        new_slots: Dict[str, ProvenanceSlot],
    ) -> List[EpistemicConflict]:
        """Detect direct contradictions between existing ground truth and newly extracted slots."""
        conflicts: List[EpistemicConflict] = []
        for key, new_slot in new_slots.items():
            if key in existing_slots:
                old_slot = existing_slots[key]
                if old_slot.value != new_slot.value and old_slot.category in (EpistemicCategory.FACT, EpistemicCategory.INFERRED):
                    conflicts.append(
                        EpistemicConflict(
                            field_name=key,
                            previous_value=old_slot.value,
                            previous_source=old_slot.source_turn_id or "prior_state",
                            new_value=new_slot.value,
                            new_source=new_slot.source_turn_id or "new_turn",
                            severity="BLOCKING",
                            resolution_status="UNRESOLVED",
                        )
                    )
        return conflicts

    @staticmethod
    def extract_implicit_constraints(text: str) -> Dict[str, Any]:
        """Infer implicit domain requirements from conversational hints."""
        implicit: Dict[str, Any] = {}
        t_lower = text.lower()
        if "infant" in t_lower or "baby" in t_lower or "6-month" in t_lower or "toddler" in t_lower:
            implicit["requires_infant_bassinet"] = True
            implicit["avoid_tight_connections"] = True
            implicit["pacing_constraint"] = "RELAXED"

        if "elderly" in t_lower or "wheelchair" in t_lower or "mobility" in t_lower:
            implicit["requires_wheelchair_assistance"] = True
            implicit["ground_floor_rooms_only"] = True

        if "honeymoon" in t_lower or "anniversary" in t_lower:
            implicit["romantic_amenities"] = True
            implicit["king_bed_guaranteed"] = True

        return implicit

    @staticmethod
    def generate_json_ld_proof_graph(trip_id: str, slots: Dict[str, ProvenanceSlot]) -> Dict[str, Any]:
        """Generate machine-readable JSON-LD proof graph showing epistemic grounding."""
        items = []
        for name, slot in slots.items():
            items.append({
                "@type": "EpistemicClaim",
                "claimProperty": name,
                "claimValue": str(slot.value),
                "epistemicCategory": slot.category.value,
                "confidence": slot.confidence,
                "citation": slot.extracted_snippet or "derived",
                "sourceTurn": slot.source_turn_id or "system",
            })
        return {
            "@context": "https://waypoint-os.org/contexts/epistemic-v1.jsonld",
            "@type": "TripEpistemicManifest",
            "tripId": trip_id,
            "claims": items,
        }
