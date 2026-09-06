"""
Epistemic Provenance & Conflict Arbiter API Router (PER-0922, PER-0923).

Provides endpoints for field-level provenance tracking, conflict detection across turns,
implicit/negative constraint extraction, and JSON-LD proof graph generation.
"""

from __future__ import annotations

from typing import Any, Dict, List
from fastapi import APIRouter
from pydantic import BaseModel, Field

from src.intake.epistemic_arbiter import (
    EpistemicArbiter,
    EpistemicStatus,
    ProvenanceSlot,
)

router = APIRouter(prefix="/api/v1/epistemic", tags=["epistemic"])


class SlotInput(BaseModel):
    slot_name: str
    value: Any
    epistemic_status: str = "EXTRACTED"
    confidence_score: float = 0.9
    source_turn_id: str = "TURN-1"
    extracted_snippet: str = ""


class ConflictDetectionRequest(BaseModel):
    slots_history: List[SlotInput]


class ImplicitExtractionRequest(BaseModel):
    text: str = Field(..., description="Customer conversational text or intake notes")


class ProofGraphRequest(BaseModel):
    trip_id: str
    slots: List[SlotInput]


@router.post("/conflicts/detect")
def detect_conversational_conflicts(payload: ConflictDetectionRequest) -> Dict[str, Any]:
    """Scans slot modifications across turns to find logical contradictions."""
    domain_slots = [
        ProvenanceSlot(
            slot_name=s.slot_name,
            value=s.value,
            epistemic_status=EpistemicStatus(s.epistemic_status) if s.epistemic_status in EpistemicStatus._value2member_map_ else EpistemicStatus.EXTRACTED,
            confidence_score=s.confidence_score,
            source_turn_id=s.source_turn_id,
            extracted_snippet=s.extracted_snippet,
        )
        for s in payload.slots_history
    ]
    conflicts = EpistemicArbiter.detect_conflicts(domain_slots)
    return {
        "status": "success",
        "conflicts_count": len(conflicts),
        "conflicts": [
            {
                "slot_name": c.slot_name,
                "turn_a_id": c.turn_a_id,
                "turn_a_value": c.turn_a_value,
                "turn_b_id": c.turn_b_id,
                "turn_b_value": c.turn_b_value,
                "description": c.conflict_description,
                "suggested_prompt": c.suggested_resolution_prompt,
            }
            for c in conflicts
        ],
    }


@router.post("/constraints/extract-implicit")
def extract_implicit_constraints(payload: ImplicitExtractionRequest) -> Dict[str, Any]:
    """Extracts implicit traveler needs and explicit negative exclusions."""
    res = EpistemicArbiter.extract_implicit_and_negative_constraints(payload.text)
    return {
        "status": "success",
        "result": res,
    }


@router.post("/proof-graph/generate")
def generate_proof_graph(payload: ProofGraphRequest) -> Dict[str, Any]:
    """Generates a W3C JSON-LD machine-readable epistemic proof graph."""
    domain_slots = [
        ProvenanceSlot(
            slot_name=s.slot_name,
            value=s.value,
            epistemic_status=EpistemicStatus(s.epistemic_status) if s.epistemic_status in EpistemicStatus._value2member_map_ else EpistemicStatus.FACT,
            confidence_score=s.confidence_score,
            source_turn_id=s.source_turn_id,
            extracted_snippet=s.extracted_snippet,
        )
        for s in payload.slots
    ]
    graph = EpistemicArbiter.generate_json_ld_proof_graph(payload.trip_id, domain_slots)
    return {
        "status": "success",
        "proof_graph": graph,
    }
