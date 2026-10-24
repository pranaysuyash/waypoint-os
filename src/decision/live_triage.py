"""
decision.live_triage — Sub-second live intake message triage service.

Provides real-time semantic analysis of inbound customer messages (WhatsApp,
web, email) for the agent /workbench in <500ms using TypeSafe System One (Jev).

Decisions evaluated:
  - Intent (Choice): new_booking, trip_modification, cancellation,
    general_inquiry, complaint, price_quote
  - Urgency (Noul): is travel imminent (<48h) or requires immediate operator intervention?
  - Frustration (Score / Choice): customer emotional temperature (calm, neutral, frustrated, angry)
  - Policy Risk (Noul): does the request violate standard travel policy (e.g. impossible lead time)?

Outputs clean UI badges and advisory chips with calibrated confidence.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from src.llm.typesafe_client import TypesafeJevClient

logger = logging.getLogger(__name__)

INTENT_OPTIONS = [
    "new_booking",
    "trip_modification",
    "cancellation",
    "general_inquiry",
    "complaint",
    "price_quote",
]

FRUSTRATION_LEVELS = ["calm", "neutral", "frustrated", "angry"]


@dataclass(slots=True)
class LiveTriageResult:
    """Triage assessment output for an inbound message."""
    intent: str
    is_urgent: bool
    urgency_probability: float
    frustration_level: str
    has_policy_risk: bool
    policy_risk_probability: float
    confidence: Optional[float]
    source: str = "jev"  # "jev" | "heuristic_fallback"
    # FND-0352 lane semantics (same contract as intake ambiguity): why the
    # heuristic served — "model_lane_unconfigured" (ADR-008 posture, no
    # credentials), "model_call_failed" (configured lane errored — ops should
    # see the degradation), or None when the model lane served.
    lane_status: Optional[str] = None
    advisory_chips: List[str] = field(default_factory=list)
    raw_probabilities: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "intent": self.intent,
            "is_urgent": self.is_urgent,
            "urgency_probability": round(self.urgency_probability, 3),
            "frustration_level": self.frustration_level,
            "has_policy_risk": self.has_policy_risk,
            "policy_risk_probability": round(self.policy_risk_probability, 3),
            "confidence": round(self.confidence, 3) if self.confidence is not None else None,
            "source": self.source,
            "lane_status": self.lane_status,
            "advisory_chips": self.advisory_chips,
        }


class LiveMessageTriageService:
    """Performs sub-second triage of messages for the workbench."""

    def __init__(
        self,
        client: Optional[TypesafeJevClient] = None,
        model: str = "jev-1.13.0",
    ):
        self.client = client or TypesafeJevClient(model=model)

    def triage(self, text: str, channel: str = "web") -> LiveTriageResult:
        """Triage an incoming message."""
        cleaned = (text or "").strip()
        if not cleaned:
            return LiveTriageResult(
                intent="general_inquiry",
                is_urgent=False,
                urgency_probability=0.0,
                frustration_level="neutral",
                has_policy_risk=False,
                policy_risk_probability=0.0,
                confidence=1.0,
                source="heuristic_fallback",
                lane_status="empty_input",
                advisory_chips=["Empty message"],
            )

        if self.client and self.client.is_available():
            try:
                return self._triage_with_jev(cleaned)
            except Exception as exc:
                logger.warning("LiveMessageTriageService: Jev triage failed (%s); using fallback", exc)
                return self._triage_fallback(cleaned, lane_status="model_call_failed")

        return self._triage_fallback(cleaned, lane_status="model_lane_unconfigured")

    def _triage_with_jev(self, text: str) -> LiveTriageResult:
        schema = {
            "type": "object",
            "properties": {
                "intent": {
                    "type": "string",
                    "enum": INTENT_OPTIONS,
                    "description": "Primary intent of the customer's message.",
                },
                "is_urgent": {
                    "type": "boolean",
                    "description": "Does this message require urgent intervention (e.g. departing today/tomorrow, stuck at airport)?",
                },
                "frustration_level": {
                    "type": "string",
                    "enum": FRUSTRATION_LEVELS,
                    "description": "Customer emotional tone.",
                },
                "policy_risk": {
                    "type": "boolean",
                    "description": "Does the request contain obvious policy friction (e.g., impossible turnaround, illegal request)?",
                },
            },
        }

        prompt = (
            "Analyze this inbound travel agency customer message:\n\n"
            f"'''{text}'''\n\n"
            "Criteria:\n"
            '- "new_booking": Customer wants to plan or book a new trip.\n'
            '- "trip_modification": Customer wants to change an existing booking (dates, hotel, flights).\n'
            '- "cancellation": Customer wants to cancel a booking.\n'
            '- "general_inquiry": Informational question about visa, weather, or destinations.\n'
            '- "complaint": Customer expressing dissatisfaction with service, flight, or hotel.\n'
            '- "price_quote": Customer asking for cost estimate or comparing prices.\n'
            '- "is_urgent": True if travel is within 48h or traveler is currently in transit with an issue.\n'
            '- "frustration_level": calm (polite/matter-of-fact), neutral (direct), frustrated (annoyed/impatient), angry (threatening escalation/demanding refund).\n'
            '- "policy_risk": True if requesting something unfeasible or violating standard agency rules.\n'
        )

        decision = self.client.decide(prompt=prompt, schema=schema)

        intent = str(decision.get("intent", "general_inquiry"))
        is_urgent = bool(decision.get("is_urgent", False))
        frustration = str(decision.get("frustration_level", "neutral"))
        policy_risk = bool(decision.get("policy_risk", False))
        confidence = decision.get("jev_confidence")
        probs = decision.get("jev_probabilities", {})
        # Noul answers carry the calibrated P(yes) but no native confidence —
        # surface the real probability instead of the thresholded bit.
        nouls = decision.get("jev_nouls", {})

        advisory_chips: List[str] = []
        if is_urgent:
            advisory_chips.append("URGENT: Imminent Travel")
        if frustration in ("frustrated", "angry"):
            advisory_chips.append(f"PRIORITY: High Friction ({frustration})")
        if intent == "cancellation":
            advisory_chips.append("ACTION: Cancellation Request")
        if policy_risk:
            advisory_chips.append("POLICY: Verify Feasibility")

        return LiveTriageResult(
            intent=intent,
            is_urgent=is_urgent,
            urgency_probability=float(nouls.get("is_urgent", 1.0 if is_urgent else 0.0)),
            frustration_level=frustration,
            has_policy_risk=policy_risk,
            policy_risk_probability=float(nouls.get("policy_risk", 1.0 if policy_risk else 0.0)),
            confidence=confidence,
            source="jev",
            advisory_chips=advisory_chips,
            raw_probabilities=probs,
        )

    def _triage_fallback(self, text: str, lane_status: str) -> LiveTriageResult:
        """Deterministic rule-based triage heuristic.

        ``lane_status`` records WHY the heuristic served (FND-0352 lane
        semantics): the model lane was unconfigured, or configured but the
        call failed. Same vocabulary as the intake ambiguity lane."""
        lower = text.lower()

        # Intent
        if any(w in lower for w in ["cancel", "refund", "call off"]):
            intent = "cancellation"
        elif any(w in lower for w in ["change", "reschedule", "modify", "postpone", "extend"]):
            intent = "trip_modification"
        elif any(w in lower for w in ["terrible", "worst", "unacceptable", "complaint", "fraud", "ridiculous"]):
            intent = "complaint"
        elif any(w in lower for w in ["how much", "cost", "price", "quote", "rate", "cheap"]):
            intent = "price_quote"
        elif any(w in lower for w in ["book", "planning", "trip to", "holiday", "package", "traveling to"]):
            intent = "new_booking"
        else:
            intent = "general_inquiry"

        # Urgency
        urgent_words = ["today", "tomorrow", "asap", "emergency", "stuck", "missed", "delayed", "urgent", "immediate"]
        is_urgent = any(w in lower for w in urgent_words)

        # Frustration
        if any(w in lower for w in ["furious", "disgusted", "lawyer", "scam", "worst service"]):
            frustration = "angry"
        elif any(w in lower for w in ["annoyed", "frustrated", "waiting for hours", "still not", "disappointed"]):
            frustration = "frustrated"
        elif any(w in lower for w in ["please", "thank you", "kindly", "appreciate", "hello", "hi"]):
            frustration = "calm"
        else:
            frustration = "neutral"

        # Policy risk
        policy_risk = bool(is_urgent and intent == "new_booking")

        chips = []
        if is_urgent:
            chips.append("URGENT: Imminent Travel")
        if frustration in ("frustrated", "angry"):
            chips.append(f"PRIORITY: High Friction ({frustration})")
        if intent == "cancellation":
            chips.append("ACTION: Cancellation Request")

        # The heuristic carries NO calibrated confidence — 0.80/0.9/0.1 here
        # are rule-contract constants (FND-0352 lane semantics: the dogfood
        # posture serves heuristics on purpose, and ops must be able to tell
        # an unconfigured lane from a failed one via lane_status).
        return LiveTriageResult(
            intent=intent,
            is_urgent=is_urgent,
            urgency_probability=0.9 if is_urgent else 0.1,
            frustration_level=frustration,
            has_policy_risk=policy_risk,
            policy_risk_probability=0.8 if policy_risk else 0.1,
            confidence=0.80,
            source="heuristic_fallback",
            lane_status=lane_status,
            advisory_chips=chips,
        )
