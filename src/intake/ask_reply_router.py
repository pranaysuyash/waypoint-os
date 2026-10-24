"""Ask-reply routing — Option D substrate (E2 Probe 2, productionized).

Routes a traveler's free-text reply to the canonical packet field it answers,
using Jev's Choice primitive over the ``FIELD_REQUIRED_FOR`` vocabulary plus an
explicit ``unparsed`` marker (zero silent drops). This service proposes ROUTING
ONLY — extracted values remain the deterministic extractor stack's authority
(``src/intake/extractors.py`` re-validates anything a consumer feeds forward),
and nothing here writes to a packet.

Activation is explicit: ``JEV_ASK_LOOP_ENABLED=1`` (default off per the ADR-008
prod posture; real traveler text must not transit TypeSafe until G2 clears).
With the flag off or Jev unavailable the router answers honestly
(``needs_review=True``) instead of guessing.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from src.llm.typesafe_client import TypesafeJevClient

logger = logging.getLogger(__name__)

# Confidence at or below which a routed proposal goes to operator review
# instead of acting (E-11 validated: injected/ambiguous inputs collapse
# confidence; the 0.60 gate catches them).
ACT_CONFIDENCE_GATE = 0.60

ENABLED_ENV = "JEV_ASK_LOOP_ENABLED"

# Canonical descriptions for the Choice criteria — rubric-explicit per the G1
# lesson. Single source of truth (the E2 benchmark imports these).
FIELD_DESCRIPTIONS: Dict[str, str] = {
    "destination_candidates": "the place or places the traveler wants to visit",
    "date_window": "when they want to travel (dates or a date range)",
    "origin_city": "the city they will depart from",
    "party_size": "how many travellers are going",
    "budget_raw_text": "the amount of money they plan to spend on the trip",
    "trip_purpose": "why they are travelling (holiday, honeymoon, family visit, work)",
    "passport_status": "whether the travellers hold valid passports",
    "visa_status": "whether visa requirements have been checked or an application started",
    "dietary_requirements": "food restrictions or meal preferences",
}

UNPARSED_DESCRIPTION = (
    "the reply does not answer the question asked — pleasantries, a question "
    "back at the agent, unrelated content, or an explicit 'not decided yet'"
)


@dataclass(slots=True)
class ReplyRoutingProposal:
    """Routing proposal for one traveler reply. Never a packet write."""

    field_name: Optional[str]  # canonical field, or None when unparsed
    routed: bool
    unparsed: bool
    confidence: Optional[float]
    noul_contains_answer: Optional[float]
    needs_review: bool  # below act gate, or flag-off/unavailable: never auto-apply
    source: str  # "jev" | "disabled" | "unavailable"
    raw: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "field_name": self.field_name,
            "routed": self.routed,
            "unparsed": self.unparsed,
            "confidence": round(self.confidence, 3) if self.confidence is not None else None,
            "noul_contains_answer": (
                round(self.noul_contains_answer, 3) if self.noul_contains_answer is not None else None
            ),
            "needs_review": self.needs_review,
            "source": self.source,
        }


def ask_loop_enabled() -> bool:
    return os.environ.get(ENABLED_ENV, "").strip().lower() in ("1", "true", "yes", "on")


class AskReplyRouter:
    """Routes free-text replies to canonical ask fields. Proposal-only."""

    def __init__(
        self,
        client: Optional[TypesafeJevClient] = None,
        model: str = "jev-1.13.0",
        act_confidence_gate: float = ACT_CONFIDENCE_GATE,
    ):
        self.client = client or TypesafeJevClient(model=model)
        self.act_confidence_gate = act_confidence_gate

    def route(self, question: str, reply: str) -> ReplyRoutingProposal:
        """Route one reply against one asked question."""
        if not ask_loop_enabled():
            return ReplyRoutingProposal(
                field_name=None, routed=False, unparsed=True, confidence=None,
                noul_contains_answer=None, needs_review=True, source="disabled",
            )
        if not self.client.is_available():
            return ReplyRoutingProposal(
                field_name=None, routed=False, unparsed=True, confidence=None,
                noul_contains_answer=None, needs_review=True, source="unavailable",
            )

        try:
            resp = self.client.raw_query(
                state=(
                    f"The travel agency asked the traveler: \"{question}\"\n"
                    f"The traveler replied: \"{reply}\""
                ),
                questions={
                    "answered_field": {
                        "type": "choice",
                        "instructions": (
                            "Which piece of trip information does this reply actually answer? "
                            "If it answers none of them, choose 'unparsed'."
                        ),
                        "criteria": {**FIELD_DESCRIPTIONS, "unparsed": UNPARSED_DESCRIPTION},
                    },
                    "reply_contains_answer": {
                        "type": "noul",
                        "instructions": (
                            "Does the reply contain a usable answer to the question that was asked?"
                        ),
                    },
                },
            )
        except Exception as exc:
            # FND-0352 lane semantics: a CONFIGURED lane that failed is a
            # distinct state from "unavailable" (no credentials) — ops must be
            # able to tell degradation from posture. Proposal-only, needs_review
            # always: never auto-applied.
            logger.warning("AskReplyRouter: Jev routing failed (%s); needs_review fallback", exc)
            return ReplyRoutingProposal(
                field_name=None, routed=False, unparsed=True, confidence=None,
                noul_contains_answer=None, needs_review=True,
                source="model_call_failed",
            )
        answers = resp.get("answers", {})
        choice_ans = answers.get("answered_field", {})
        routed_to = choice_ans.get("choice")
        probs = choice_ans.get("probabilities", {}) or {}
        native_conf = choice_ans.get("confidence")
        if native_conf is not None:
            confidence = float(native_conf)
        elif routed_to and routed_to in probs:
            confidence = abs(float(probs[routed_to]) - 0.5) * 2.0
        else:
            confidence = None
        noul_ans = answers.get("reply_contains_answer", {}).get("noul")
        noul_val = float(noul_ans) if noul_ans is not None else None

        unparsed = routed_to == "unparsed" or not routed_to
        routed = not unparsed
        needs_review = confidence is None or confidence < self.act_confidence_gate

        return ReplyRoutingProposal(
            field_name=None if unparsed else routed_to,
            routed=routed,
            unparsed=unparsed,
            confidence=confidence,
            noul_contains_answer=noul_val,
            needs_review=needs_review,
            source="jev",
            raw={"probabilities": probs, "model": resp.get("model")},
        )
