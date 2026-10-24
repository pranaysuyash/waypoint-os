"""Question rendering grade/select — E2 Probe 1, productionized.

Jev cannot generate text, so traveler-voiced rendering works as a GRADE/SELECT
loop: the generative ladder (or template table) supplies candidate renderings
of an engine question, Jev scores each against the explicit E2 rubric (field
intent preserved, no new facts, traveler naturalness), and the best passing
candidate is selected. The engine's verbatim question is always the fallback —
the probe showed acceptance 0.917 with failures in the safe direction
(dropping a usable rendering), so fallback never regresses the shipped floor.

Activation is explicit: ``JEV_ASK_LOOP_ENABLED=1`` (default off per the
ADR-008 prod posture; G2 gates real traveler-context state).
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from src.llm.typesafe_client import TypesafeJevClient

logger = logging.getLogger(__name__)

ENABLED_ENV = "JEV_ASK_LOOP_ENABLED"

FIELD_PROMPT_NAMES: Dict[str, str] = {
    "destination_candidates": "destination(s) of the trip",
    "date_window": "travel dates or date range",
    "origin_city": "departure city",
    "party_size": "number of travellers",
    "budget_raw_text": "trip budget",
    "trip_purpose": "purpose of the trip",
    "passport_status": "passport validity",
    "visa_status": "visa status",
    "dietary_requirements": "dietary requirements",
}


def ask_loop_enabled() -> bool:
    return os.environ.get(ENABLED_ENV, "").strip().lower() in ("1", "true", "yes", "on")


@dataclass(slots=True)
class RenderingCandidate:
    text: str
    origin: str = "ladder"  # "ladder" | "template" | provenance label


@dataclass(slots=True)
class CandidateGrade:
    text: str
    origin: str
    noul_intent: Optional[float] = None
    noul_no_new_facts: Optional[float] = None
    naturalness: Optional[float] = None
    passes: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "origin": self.origin,
            "noul_intent": self.noul_intent,
            "noul_no_new_facts": self.noul_no_new_facts,
            "naturalness": self.naturalness,
            "passes": self.passes,
        }


@dataclass(slots=True)
class RenderSelection:
    """Always carries a question text — verbatim fallback is the floor."""

    selected: str
    selected_origin: str  # "jev_graded:<candidate origin>" | "verbatim_fallback" | "disabled"
    grades: List[CandidateGrade] = field(default_factory=list)
    # ``source`` names the lane that produced the SELECTED question — not
    # merely which lane ran. When the JEV lane graded but nothing passed the
    # rubric, the selection is the verbatim floor: source says so (2026-10-22
    # honesty fix; grades[] still carries the full JEV evidence).
    source: str = "jev"  # "jev" | "verbatim_fallback" | "disabled" | "unavailable"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "selected": self.selected,
            "selected_origin": self.selected_origin,
            "grades": [g.to_dict() for g in self.grades],
            "source": self.source,
        }


class QuestionRenderSelector:
    """Grades candidate renderings with Jev and selects the best passing one."""

    def __init__(
        self,
        client: Optional[TypesafeJevClient] = None,
        model: str = "jev-1.13.0",
    ):
        self.client = client or TypesafeJevClient(model=model)

    def select(
        self,
        field_name: str,
        engine_question: str,
        candidates: List[RenderingCandidate],
        packet_context: str = "",
    ) -> RenderSelection:
        """Grade candidates; return the best passing rendering or the verbatim
        engine question. Never raises on candidate quality — bad candidates
        simply fail the rubric and lose to the verbatim fallback."""
        if not ask_loop_enabled() or not candidates:
            return RenderSelection(
                selected=engine_question, selected_origin="disabled" if not ask_loop_enabled() else "verbatim_fallback",
                source="disabled" if not ask_loop_enabled() else "jev",
            )
        if not self.client.is_available():
            return RenderSelection(
                selected=engine_question, selected_origin="verbatim_fallback", source="unavailable",
            )

        asked = FIELD_PROMPT_NAMES.get(field_name, field_name.replace("_", " "))
        grades: List[CandidateGrade] = []
        for cand in candidates:
            grade = self._grade(cand, asked, engine_question, packet_context)
            grades.append(grade)

        passing = [g for g in grades if g.passes]
        if not passing:
            return RenderSelection(
                selected=engine_question, selected_origin="verbatim_fallback",
                grades=grades,
                # JEV ran but nothing passed the rubric — the SELECTION is the
                # verbatim floor, so source names the floor (grades[] above
                # still carries the full JEV evidence).
                source="verbatim_fallback",
            )
        best = max(passing, key=lambda g: (g.naturalness or 0.0))
        return RenderSelection(
            selected=best.text,
            selected_origin=f"jev_graded:{best.origin}",
            grades=grades,
            source="jev",
        )

    def _grade(
        self,
        cand: RenderingCandidate,
        asked: str,
        engine_question: str,
        packet_context: str,
    ) -> CandidateGrade:
        state = (
            f"The travel agency's system needs to ask the traveler about: {asked}.\n"
            f"Original system question: \"{engine_question}\"\n"
            + (f"Trip context: {packet_context}\n" if packet_context else "")
            + f"Proposed rephrasing to evaluate: \"{cand.text}\""
        )
        try:
            resp = self.client.raw_query(state, {
                "preserves_field_intent": {
                    "type": "noul",
                    "instructions": (
                        f"Does this proposed rephrasing ask the traveler about exactly "
                        f"{asked} — and not about some other trip detail?"
                    ),
                },
                "introduces_no_new_facts": {
                    "type": "noul",
                    "instructions": (
                        "Does the proposed rephrasing avoid introducing any specific "
                        "place, date, number, or assumption that is not present in the "
                        "original system question? Answer yes only if it adds zero new specifics."
                    ),
                },
                "traveler_naturalness": {
                    "type": "score",
                    "instructions": (
                        "How naturally does this rephrasing read to a traveler, "
                        "including Hinglish-speaking travelers? 1 = robotic or confusing, "
                        "5 = something a human travel agent would say."
                    ),
                    "criteria": [
                        {"label": "1", "description": "Robotic, system-like, or confusing to a traveler"},
                        {"label": "2", "description": "Understandable but stiff or jargon-heavy"},
                        {"label": "3", "description": "Acceptable plain question"},
                        {"label": "4", "description": "Natural, friendly agent phrasing"},
                        {"label": "5", "description": "Exactly how a warm human agent would ask"},
                    ],
                },
            })
        except Exception as exc:  # degraded Jev → candidate fails, fallback holds
            logger.warning("QuestionRenderSelector grading failed (%s); candidate rejected", exc)
            return CandidateGrade(text=cand.text, origin=cand.origin, passes=False)

        answers = resp.get("answers", {})
        n_intent = answers.get("preserves_field_intent", {}).get("noul")
        n_facts = answers.get("introduces_no_new_facts", {}).get("noul")
        naturalness = answers.get("traveler_naturalness", {}).get("score")
        passes = (
            n_intent is not None and float(n_intent) >= 0.5
            and n_facts is not None and float(n_facts) >= 0.5
        )
        return CandidateGrade(
            text=cand.text,
            origin=cand.origin,
            noul_intent=float(n_intent) if n_intent is not None else None,
            noul_no_new_facts=float(n_facts) if n_facts is not None else None,
            naturalness=float(naturalness) if naturalness is not None else None,
            passes=passes,
        )
