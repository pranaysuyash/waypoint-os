"""
intake.plan_candidate — Pass 2A: Structured intermediate planning artifact.

This bridges NB03 strategy and output bundles. It is NOT full itinerary
generation and NOT NB04 TravelerProposal yet. PlanCandidate is the internal
canonical planning snapshot consumed by downstream rendering, QA, and replay.

Safety: PlanCandidate contains internal commercial state. It must NEVER
be passed raw to the traveler-safe builder. Use to_traveler_safe_dict().
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional

from .constants import DecisionState
from .packet_models import CanonicalPacket, Slot


def _safe_get_fact(packet: CanonicalPacket, field_name: str) -> Any:
    slot = packet.facts.get(field_name)
    return slot.value if slot is not None else None


_READINESS_MAP: Dict[str, str] = {
    "STOP_NEEDS_REVIEW": "blocked",
    "ASK_FOLLOWUP": "blocked",
    "BRANCH_OPTIONS": "internal_draft",
    "PROCEED_INTERNAL_DRAFT": "internal_draft",
    "PROCEED_TRAVELER_SAFE": "traveler_safe",
}

# Traveler-safe status: maps internal decision_state to customer-facing labels.
# These are the ONLY values exposed in to_traveler_safe_dict().
_TRAVELER_STATUS_MAP: Dict[str, str] = {
    "STOP_NEEDS_REVIEW": "being_reviewed",
    "ASK_FOLLOWUP": "needs_more_details",
    "BRANCH_OPTIONS": "ready_to_share",
    "PROCEED_INTERNAL_DRAFT": "being_reviewed",
    "PROCEED_TRAVELER_SAFE": "ready_to_share",
}

# Traveler-safe summary: deterministic copy per decision state.
# No internal terms, no strategy_goal reuse.
_TRAVELER_SUMMARY_MAP: Dict[str, str] = {
    "ASK_FOLLOWUP": "A few details are needed before options can be prepared.",
    "STOP_NEEDS_REVIEW": "This request needs review before options are shared.",
    "PROCEED_TRAVELER_SAFE": "Trip options can be prepared from the confirmed details.",
    "BRANCH_OPTIONS": "A few route or budget options can be compared.",
    "PROCEED_INTERNAL_DRAFT": "The plan is being prepared for review.",
}

_INTERNAL_ONLY_RISK_CATEGORIES = frozenset({
    "margin", "commercial", "operational_complexity",
})

_INTERNAL_ONLY_RISK_TERMS = frozenset({
    "hypothesis", "contradiction", "blocker",
    "owner_constraint", "internal_only", "agency_note",
    "confidence", "decision_state", "next_action",
    "operator_review", "owner_review", "traveler-facing",
    "escalate", "senior review",
})

TRAVELER_SAFE_FACT_FIELDS = frozenset({
    "destination_candidates",
    "resolved_destination",
    "origin_city",
    "date_window",
    "party_size",
    "party_composition",
    "trip_purpose",
    "pace_preference",
    "soft_preferences",
})

_TRAVELER_SAFE_RISK_CATEGORIES = frozenset({
    "budget", "activity", "pacing", "logistics",
    "documents", "routing", "seasonality",
})


@dataclass(slots=True)
class TravelerSnapshot:
    destination_candidates: List[str] = field(default_factory=list)
    resolved_destination: Optional[str] = None
    origin_city: Optional[str] = None
    date_window: Optional[str] = None
    party_size: Optional[int] = None
    party_composition: Dict[str, Any] = field(default_factory=dict)
    budget_min: Optional[int] = None
    trip_purpose: Optional[str] = None
    pace_preference: Optional[str] = None


@dataclass(slots=True)
class PlanningConstraint:
    field: str
    value: Any
    source: Literal["fact", "derived_signal", "decision", "strategy", "fee", "suitability"]
    traveler_safe: bool
    reason: str = ""


@dataclass(slots=True)
class PlanningRisk:
    flag: str
    severity: str
    category: str
    message: str
    traveler_safe: bool = False
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class CommercialSnapshot:
    fees: Optional[Dict[str, Any]] = None
    budget_breakdown: Optional[Dict[str, Any]] = None
    commercial_decision: str = "NONE"
    intent_scores: Dict[str, float] = field(default_factory=dict)


@dataclass(slots=True)
class PlanCandidate:
    plan_id: str
    packet_id: str
    decision_state: DecisionState
    operating_mode: str
    stage: str

    traveler_snapshot: TravelerSnapshot = field(default_factory=TravelerSnapshot)
    constraints: List[PlanningConstraint] = field(default_factory=list)
    risks: List[PlanningRisk] = field(default_factory=list)
    commercial: CommercialSnapshot = field(default_factory=CommercialSnapshot)

    strategy_goal: str = ""
    priority_sequence: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)

    suitability_flags: List[Dict[str, Any]] = field(default_factory=list)
    readiness: Literal["blocked", "internal_draft", "traveler_safe"] = "blocked"
    missing_inputs: List[str] = field(default_factory=list)
    next_action: DecisionState = field(default="ASK_FOLLOWUP")  # type: ignore[arg-type]

    created_at: str = ""
    schema_version: str = "0.1"

    def to_internal_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "packet_id": self.packet_id,
            "decision_state": self.decision_state,
            "operating_mode": self.operating_mode,
            "stage": self.stage,
            "traveler_snapshot": asdict(self.traveler_snapshot),
            "constraints": [asdict(c) for c in self.constraints],
            "risks": [asdict(r) for r in self.risks],
            "commercial": asdict(self.commercial),
            "strategy_goal": self.strategy_goal,
            "priority_sequence": self.priority_sequence,
            "assumptions": self.assumptions,
            "suitability_flags": self.suitability_flags,
            "readiness": self.readiness,
            "missing_inputs": self.missing_inputs,
            "next_action": self.next_action,
            "created_at": self.created_at,
            "schema_version": self.schema_version,
        }

    def _any_term_in_text(self, text: str) -> bool:
        lower = text.lower()
        return any(t in lower for t in _INTERNAL_ONLY_RISK_TERMS)

    def to_traveler_safe_dict(self) -> Dict[str, Any]:
        # Risks: only include if explicitly traveler_safe, not internal category,
        # and no internal terms in flag or message.
        safe_risks = [
            {
                "flag": r.flag,
                "severity": r.severity,
                "category": r.category,
                "message": r.message,
            }
            for r in self.risks
            if r.traveler_safe
               and r.category not in _INTERNAL_ONLY_RISK_CATEGORIES
               and not self._any_term_in_text(r.flag)
               and not self._any_term_in_text(r.message)
        ]

        # Constraints: only those explicitly marked traveler_safe
        safe_constraints = [
            {"field": c.field, "value": c.value, "source": c.source}
            for c in self.constraints if c.traveler_safe
        ]

        # Suitability: exclude critical severity, filter internal terms
        safe_suitability = [
            f for f in self.suitability_flags
            if str(f.get("severity", "")) not in ("critical",)
               and not self._any_term_in_text(str(f.get("reason", "")))
               and not self._any_term_in_text(str(f.get("flag_type", "")))
        ]

        # Map internal decision_state to traveler-safe status
        traveler_status = _TRAVELER_STATUS_MAP.get(
            self.decision_state, "needs_more_details"
        )

        # Deterministic traveler-facing summary — never raw strategy_goal
        traveler_summary = _TRAVELER_SUMMARY_MAP.get(
            self.decision_state, "We are reviewing your trip request."
        )

        return {
            "plan_id": self.plan_id,
            "stage": self.stage,
            "traveler_snapshot": asdict(self.traveler_snapshot),
            "constraints": safe_constraints,
            "risks": safe_risks,
            "suitability_flags": safe_suitability,
            "traveler_status": traveler_status,
            "traveler_summary": traveler_summary,
            "schema_version": self.schema_version,
        }


def _fact_is_traveler_safe(field_name: str) -> bool:
    return field_name in TRAVELER_SAFE_FACT_FIELDS


def _suitability_severity_is_traveler_safe(severity: str) -> bool:
    return severity not in ("critical",)


def build_plan_candidate(
    packet: CanonicalPacket,
    decision: Any,  # DecisionResult
    strategy: Any,  # SessionStrategy
    fees: Optional[Dict[str, Any]] = None,
) -> PlanCandidate:
    party_composition = _safe_get_fact(packet, "party_composition")
    if not isinstance(party_composition, dict):
        party_composition = {}

    snapshot = TravelerSnapshot(
        destination_candidates=_safe_get_fact(packet, "destination_candidates") or [],
        resolved_destination=_safe_get_fact(packet, "resolved_destination"),
        origin_city=_safe_get_fact(packet, "origin_city"),
        date_window=_safe_get_fact(packet, "date_window"),
        party_size=_safe_get_fact(packet, "party_size"),
        party_composition=party_composition,
        budget_min=_safe_get_fact(packet, "budget_min"),
        trip_purpose=_safe_get_fact(packet, "trip_purpose"),
        pace_preference=_safe_get_fact(packet, "pace_preference"),
    )

    constraints: List[PlanningConstraint] = []
    for field_name, slot in packet.facts.items():
        if slot.value is not None and slot.value != "" and slot.value != []:
            constraints.append(PlanningConstraint(
                field=field_name,
                value=slot.value,
                source="fact",
                traveler_safe=_fact_is_traveler_safe(field_name),
            ))
    for field_name, slot in packet.derived_signals.items():
        if slot.value is not None:
            constraints.append(PlanningConstraint(
                field=field_name,
                value=slot.value,
                source="derived_signal",
                traveler_safe=field_name in ("domestic_or_international",),
            ))

    for blocker in getattr(decision, "hard_blockers", []) or []:
        constraints.append(PlanningConstraint(
            field=blocker,
            value=None,
            source="decision",
            traveler_safe=False,
            reason="hard blocker",
        ))
    for blocker in getattr(decision, "soft_blockers", []) or []:
        constraints.append(PlanningConstraint(
            field=blocker,
            value=None,
            source="decision",
            traveler_safe=False,
            reason="soft blocker",
        ))

    # Decision risk_flags: default to traveler_safe=False.
    # Only explicitly safe categories get traveler_safe=True.
    risks: List[PlanningRisk] = []
    for r in getattr(decision, "risk_flags", []) or []:
        if isinstance(r, dict):
            category = str(r.get("category", r.get("source", "decision")))
            message = str(r.get("message", ""))
            flag = str(r.get("flag", ""))
            # Default False; only True if category is in the safe set AND
            # neither the message nor flag contains internal terms
            is_safe = (
                category in _TRAVELER_SAFE_RISK_CATEGORIES
                and not any(t in message.lower() for t in _INTERNAL_ONLY_RISK_TERMS)
                and not any(t in flag.lower() for t in _INTERNAL_ONLY_RISK_TERMS)
            )
            risks.append(PlanningRisk(
                flag=flag,
                severity=str(r.get("severity", "medium")),
                category=category,
                message=message,
                traveler_safe=is_safe,
                details=r.get("details", {}) if isinstance(r.get("details"), dict) else {},
            ))

    for f in getattr(packet, "suitability_flags", []) or []:
        if hasattr(f, "severity"):
            severity = getattr(f, "severity", "medium")
            risks.append(PlanningRisk(
                flag=getattr(f, "flag_type", "suitability"),
                severity=severity,
                category="suitability",
                message=getattr(f, "reason", ""),
                traveler_safe=_suitability_severity_is_traveler_safe(severity),
                details=getattr(f, "details", {}) if hasattr(f, "details") else {},
            ))

    commercial = CommercialSnapshot(
        fees=fees,
        budget_breakdown=(
            asdict(getattr(decision, "budget_breakdown", None))
            if getattr(decision, "budget_breakdown") and getattr(decision, "budget_breakdown", None) is not None
            and hasattr(getattr(decision, "budget_breakdown"), "__dict__")
            else None
        ),
        commercial_decision=getattr(decision, "commercial_decision", "NONE") or "NONE",
        intent_scores=dict(getattr(decision, "intent_scores", {}) or {}),
    )

    decision_state: DecisionState = getattr(decision, "decision_state", "ASK_FOLLOWUP")
    readiness = _READINESS_MAP.get(decision_state, "blocked")

    missing_inputs: List[str] = []
    for field_name in ("origin_city", "destination_candidates",
                        "date_window", "party_size", "budget_min"):
        val = _safe_get_fact(packet, field_name)
        if val is None or val == "" or val == []:
            missing_inputs.append(field_name)

    suitability_dicts: List[Dict[str, Any]] = []
    for f in getattr(packet, "suitability_flags", []) or []:
        if hasattr(f, "flag_type"):
            suitability_dicts.append({
                "flag_type": getattr(f, "flag_type", ""),
                "severity": getattr(f, "severity", "medium"),
                "reason": getattr(f, "reason", ""),
                "confidence": getattr(f, "confidence", 0.0),
            })
        elif isinstance(f, dict):
            suitability_dicts.append(f)

    return PlanCandidate(
        plan_id=f"plan_{packet.packet_id}",
        packet_id=packet.packet_id,
        decision_state=decision_state,
        operating_mode=getattr(decision, "operating_mode", "normal_intake") or "normal_intake",
        stage=getattr(packet, "stage", "discovery") or "discovery",
        traveler_snapshot=snapshot,
        constraints=constraints,
        risks=risks,
        commercial=commercial,
        strategy_goal=getattr(strategy, "session_goal", "") or "",
        priority_sequence=list(getattr(strategy, "priority_sequence", []) or []),
        assumptions=list(getattr(strategy, "assumptions", []) or []),
        suitability_flags=suitability_dicts,
        readiness=readiness,
        missing_inputs=missing_inputs,
        next_action=decision_state,
        created_at=datetime.now(timezone.utc).isoformat(),
    )
