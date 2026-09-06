"""
Epistemic Provenance & Conversational Conflict Arbiter (PER-0922, PER-0923).

Tracks field-level confidence, historical conversational provenance, detects
multi-turn conflicting statements, extracts implicit needs and negative exclusions,
and builds machine-readable JSON-LD epistemic proof graphs.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List


class EpistemicStatus(str, Enum):
    FACT = "FACT"                  # Authoritatively verified by traveler or document
    ASSUMED = "ASSUMED"            # Default assumption or inferred from context
    EXTRACTED = "EXTRACTED"        # Extracted from customer raw input with confidence score
    CONFLICTED = "CONFLICTED"      # Contradictory statements detected across turns
    UNKNOWN = "UNKNOWN"            # Unspecified parameter


@dataclass(slots=True)
class ProvenanceSlot:
    """Field-level epistemic slot with cryptographic provenance hash."""
    slot_name: str
    value: Any
    epistemic_status: EpistemicStatus
    confidence_score: float  # 0.0 to 1.0
    source_turn_id: str
    extracted_snippet: str
    provenance_hash: str = ""
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self) -> None:
        if not self.provenance_hash:
            raw = f"{self.slot_name}:{str(self.value)}:{self.source_turn_id}:{self.extracted_snippet}"
            self.provenance_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "slot_name": self.slot_name,
            "value": self.value,
            "epistemic_status": self.epistemic_status.value,
            "confidence_score": round(self.confidence_score, 2),
            "source_turn_id": self.source_turn_id,
            "extracted_snippet": self.extracted_snippet,
            "provenance_hash": self.provenance_hash,
            "updated_at": self.updated_at,
        }


@dataclass(slots=True)
class EpistemicConflict:
    """Detected conflict between two conversational turns."""
    slot_name: str
    turn_a_id: str
    turn_a_value: Any
    turn_b_id: str
    turn_b_value: Any
    conflict_description: str
    suggested_resolution_prompt: str


class EpistemicArbiter:
    """Arbitrates knowledge states, detects conflicts, and generates JSON-LD proof graphs."""

    @staticmethod
    def detect_conflicts(slots_history: List[ProvenanceSlot]) -> List[EpistemicConflict]:
        """Scans slot history across turns to find direct logical contradictions."""
        conflicts: List[EpistemicConflict] = []
        by_slot: Dict[str, List[ProvenanceSlot]] = {}
        for s in slots_history:
            by_slot.setdefault(s.slot_name, []).append(s)

        for slot_name, items in by_slot.items():
            if len(items) > 1:
                # Compare sequential values
                for i in range(len(items) - 1):
                    s1 = items[i]
                    s2 = items[i + 1]
                    if s1.value != s2.value and s1.source_turn_id != s2.source_turn_id:
                        conflicts.append(
                            EpistemicConflict(
                                slot_name=slot_name,
                                turn_a_id=s1.source_turn_id,
                                turn_a_value=s1.value,
                                turn_b_id=s2.source_turn_id,
                                turn_b_value=s2.value,
                                conflict_description=(
                                    f"Contradiction in '{slot_name}': Turn {s1.source_turn_id} specified '{s1.value}', "
                                    f"but Turn {s2.source_turn_id} specified '{s2.value}'."
                                ),
                                suggested_resolution_prompt=(
                                    f"Please confirm whether you prefer '{s1.value}' or '{s2.value}' for {slot_name}."
                                ),
                            )
                        )
        return conflicts

    @staticmethod
    def extract_implicit_and_negative_constraints(text: str) -> Dict[str, Any]:
        """Extracts implicit constraints (e.g. infant -> bassinet) and negative exclusions."""
        lower = text.lower()
        implicit_needs: List[str] = []
        excluded_preferences: List[str] = []

        # Implicit constraints
        if "infant" in lower or "baby" in lower or "6-month" in lower or "1-year" in lower:
            implicit_needs.append("requires_infant_bassinet")
            implicit_needs.append("avoid_tight_connections_under_90m")
        if "wheelchair" in lower or "reduced mobility" in lower or "step-free" in lower:
            implicit_needs.append("requires_step_free_access")
            implicit_needs.append("ground_floor_or_elevator_room")
        if "honeymoon" in lower or "anniversary" in lower:
            implicit_needs.append("vip_amenity_champagne_on_arrival")
            implicit_needs.append("guaranteed_king_bed")

        # Negative exclusions
        if "no boeing 737 max" in lower or "avoid 737 max" in lower or "no max" in lower:
            excluded_preferences.append("AIRCRAFT_EXCLUDE:B737_MAX")
        if "no ryanair" in lower or "avoid ryanair" in lower:
            excluded_preferences.append("AIRLINE_EXCLUDE:FR")
        if "no ground floor" in lower or "no ground-floor" in lower:
            excluded_preferences.append("ROOM_EXCLUDE:GROUND_FLOOR")
        if "no red-eye" in lower or "no overnight" in lower:
            excluded_preferences.append("FLIGHT_EXCLUDE:OVERNIGHT_RED_EYE")

        return {
            "implicit_needs": implicit_needs,
            "excluded_preferences": excluded_preferences,
        }

    @staticmethod
    def generate_json_ld_proof_graph(trip_id: str, slots: List[ProvenanceSlot]) -> Dict[str, Any]:
        """Generates a standard W3C JSON-LD machine-readable epistemic proof graph."""
        entities = []
        for s in slots:
            entities.append({
                "@type": "EpistemicFactAssertion",
                "slot": s.slot_name,
                "value": s.value,
                "status": s.epistemic_status.value,
                "confidence": s.confidence_score,
                "sourceTurn": s.source_turn_id,
                "evidenceSnippet": s.extracted_snippet,
                "proofHash": s.provenance_hash,
            })

        return {
            "@context": {
                "@vocab": "https://waypointos.com/schema/epistemic#",
                "xsd": "http://www.w3.org/2001/XMLSchema#",
            },
            "@id": f"urn:waypoint:trip:{trip_id}:epistemic-proof",
            "@type": "EpistemicProofGraph",
            "tripId": trip_id,
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "assertions": entities,
        }
