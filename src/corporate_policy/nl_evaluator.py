"""Natural Language Corporate Policy Conformance Engine (Lane B1).

Audits prose corporate travel policy clauses against travel proposals/itineraries
using parallel Noul questions via TypesafeJevClient with confidence calibration.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from src.llm.typesafe_client import TypesafeJevClient

logger = logging.getLogger(__name__)

# "at least 14 days" / "minimum 3 days" — the numeric lead-time threshold in
# a policy clause description.
_LEAD_THRESHOLD_RE = re.compile(r"(?:at least|minimum|min\.?)\s+(\d+)\s*days?")
# "booked 21 days before departure" — the actual lead time stated in an itinerary.
_LEAD_ACTUAL_RE = re.compile(r"(\d+)\s*days?\s*before")

DEFAULT_POLICY_CLAUSES: List[PolicyClause] = []

@dataclass
class PolicyClause:
    clause_id: str
    description: str
    criticality: str = "mandatory"  # "mandatory" | "advisory"
    category: str = "expense"       # "expense" | "safety" | "booking_lead_time" | "sustainability"

@dataclass
class ClauseEvaluation:
    clause_id: str
    compliant: bool
    confidence: float
    probability: float
    criticality: str
    provenance: str = ""
    evaluated: bool = True  # False = heuristic could not evaluate this clause honestly

@dataclass
class NaturalLanguagePolicyAuditResult:
    ok: bool
    is_compliant: bool
    evaluated_clauses_count: int
    violations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    evaluations: List[ClauseEvaluation] = field(default_factory=list)
    average_confidence: float = 1.0
    low_confidence_clauses: List[str] = field(default_factory=list)
    model: str = "heuristic"
    unevaluated_clauses: List[str] = field(default_factory=list)
    all_clauses_evaluated: bool = True
    # FND-0352 lane semantics: why the heuristic served — "jev" when the
    # model lane ran, "model_lane_unconfigured" (no credentials), or
    # "model_call_failed" (configured lane errored mid-audit). Same
    # vocabulary as the intake ambiguity / live-triage lanes.
    lane_status: str = "jev"


class NaturalLanguagePolicyEngine:
    """Evaluates unstructured natural language travel policy clauses against itinerary proposals."""

    def __init__(
        self,
        jev_client: Optional[TypesafeJevClient] = None,
        confidence_threshold: float = 0.65,
    ) -> None:
        self.jev_client = jev_client
        self.confidence_threshold = confidence_threshold

    def audit(
        self,
        itinerary_text: str,
        clauses: List[PolicyClause],
    ) -> NaturalLanguagePolicyAuditResult:
        if not clauses:
            return NaturalLanguagePolicyAuditResult(
                ok=True,
                is_compliant=True,
                evaluated_clauses_count=0,
                violations=[],
                warnings=[],
                evaluations=[],
                average_confidence=1.0,
                model="none",
            )

        if self.jev_client and self.jev_client.is_available():
            return self._audit_with_jev(itinerary_text, clauses)
        return self._audit_heuristic(itinerary_text, clauses)

    def _audit_with_jev(
        self,
        itinerary_text: str,
        clauses: List[PolicyClause],
    ) -> NaturalLanguagePolicyAuditResult:
        questions: Dict[str, Dict[str, Any]] = {}
        for clause in clauses:
            # Query Jev Noul: "Does the itinerary comply with this corporate policy requirement?"
            # Noul questions require explicit `instructions` (the API rejects
            # question-text-only nouls with HTTP 400) — keep it rubric-explicit
            # per the G1 lesson: name the exact rule, demand clear satisfaction.
            questions[clause.clause_id] = {
                "type": "noul",
                "question": f"Does the proposed travel itinerary fully comply with this corporate travel policy rule: {clause.description}?",
                "instructions": (
                    f"Does the proposed travel itinerary fully comply with this corporate "
                    f"travel policy rule: \"{clause.description}\"? Answer yes only if the "
                    f"itinerary text clearly satisfies the rule; answer no if it violates, "
                    f"contradicts, or is silent about the rule where the rule applies."
                ),
            }

        try:
            resp = self.jev_client.raw_query(state=itinerary_text, questions=questions)
            answers = resp.get("answers", {})
            model = resp.get("model", self.jev_client.model)
        except Exception as e:
            logger.warning("Jev policy audit query failed (%s), falling back to heuristic", e)
            return self._audit_heuristic(
                itinerary_text, clauses, lane_status="model_call_failed"
            )

        evaluations: List[ClauseEvaluation] = []
        violations: List[str] = []
        warnings: List[str] = []
        low_conf_clauses: List[str] = []
        total_conf = 0.0

        for clause in clauses:
            ans = answers.get(clause.clause_id, {})
            # Noul answer gives probability [0.0, 1.0] of True/Yes
            noul_val = float(ans.get("noul", 0.5))
            native_conf = ans.get("confidence")
            if native_conf is not None:
                conf = float(native_conf)
            else:
                # Noul answers carry no native confidence field (verified live
                # 2026-10-25 against jev-1.13.0) — derive it as the calibrated
                # probability's distance from the act threshold so the review
                # gate only flags genuinely borderline clauses.
                conf = abs(noul_val - 0.5) * 2.0
            total_conf += conf

            # Is compliant if noul >= 0.5
            is_compliant = noul_val >= 0.5
            if conf < self.confidence_threshold:
                low_conf_clauses.append(clause.clause_id)

            eval_item = ClauseEvaluation(
                clause_id=clause.clause_id,
                compliant=is_compliant,
                confidence=conf,
                probability=noul_val,
                criticality=clause.criticality,
                provenance=f"jev noul={noul_val:.2f}, conf={conf:.2f}",
            )
            evaluations.append(eval_item)

            if not is_compliant:
                msg = f"[{clause.clause_id}] Policy violation: {clause.description}"
                if clause.criticality == "mandatory":
                    violations.append(msg)
                else:
                    warnings.append(f"[{clause.clause_id}] Policy advisory warning: {clause.description}")

        avg_conf = total_conf / len(clauses) if clauses else 1.0
        overall_compliant = len(violations) == 0

        return NaturalLanguagePolicyAuditResult(
            ok=True,
            is_compliant=overall_compliant,
            evaluated_clauses_count=len(clauses),
            violations=violations,
            warnings=warnings,
            evaluations=evaluations,
            average_confidence=avg_conf,
            low_confidence_clauses=low_conf_clauses,
            model=model,
            lane_status="jev",
        )

    def _audit_heuristic(
        self,
        itinerary_text: str,
        clauses: List[PolicyClause],
        lane_status: str = "model_lane_unconfigured",
    ) -> NaturalLanguagePolicyAuditResult:
        """Deterministic rule-based fallback when Jev is offline.

        ``lane_status`` records WHY the heuristic served (FND-0352 lane
        semantics): the model lane was unconfigured (ADR-008 posture) or
        configured but the call failed. Same vocabulary as the intake
        ambiguity / live-triage lanes.

        Honest-evaluation contract: a clause is marked evaluated only when the
        pattern check produces real evidence for its verdict (a detected
        violation, a prohibition whose banned artifact is provably absent, or
        a comparable numeric lead-time). Clauses the keywords cannot judge are
        returned as unevaluated for review — never silently asserted compliant
        (a false all-clear on a policy conformance surface is worse than an
        explicit gap).
        """
        text_lower = itinerary_text.lower()
        evaluations: List[ClauseEvaluation] = []
        violations: List[str] = []
        warnings: List[str] = []
        unevaluated: List[str] = []

        for clause in clauses:
            desc = clause.description.lower()
            compliant = True
            evaluated = False

            # Cabin-class restriction: "no <class>" / "<class> not permitted" bans
            # that class; "economy class only" bans everything above economy.
            # Presence of a banned class in the text is provable violation;
            # absence is positive evidence of compliance.
            banned_classes: List[str] = []
            if "economy class only" in desc or "economy only" in desc:
                banned_classes = ["business class", "first class", "first-class"]
            else:
                for banned in ("first class", "first-class", "business class"):
                    if banned in desc and ("no " in desc or "not permitted" in desc):
                        banned_classes = [banned]
                        break
            if banned_classes:
                evaluated = True
                if any(b in text_lower for b in banned_classes):
                    compliant = False

            # Lead-time rule with a numeric threshold: compare numbers when
            # both sides state them ("at least 14 days" vs "booked 2 days before").
            if not evaluated:
                desc_days = _LEAD_THRESHOLD_RE.search(desc)
                text_days = _LEAD_ACTUAL_RE.search(text_lower)
                if desc_days and text_days:
                    evaluated = True
                    compliant = int(text_days.group(1)) >= int(desc_days.group(1))
                elif "same-day booking" in text_lower or "last minute" in text_lower:
                    # Explicit bad marker detects a violation even without numbers.
                    evaluated = True
                    compliant = False

            eval_item = ClauseEvaluation(
                clause_id=clause.clause_id,
                compliant=compliant,
                confidence=0.8 if evaluated else 0.0,
                probability=1.0 if compliant else 0.0,
                criticality=clause.criticality,
                provenance=(
                    "heuristic deterministic pattern match" if evaluated
                    else "heuristic: no deterministic pattern applies — needs review"
                ),
                evaluated=evaluated,
            )
            evaluations.append(eval_item)

            if not evaluated:
                unevaluated.append(clause.clause_id)
            elif not compliant:
                msg = f"[{clause.clause_id}] Policy violation: {clause.description}"
                if clause.criticality == "mandatory":
                    violations.append(msg)
                else:
                    warnings.append(f"[{clause.clause_id}] Policy advisory warning: {clause.description}")

        return NaturalLanguagePolicyAuditResult(
            ok=True,
            is_compliant=len(violations) == 0,
            evaluated_clauses_count=len(clauses),
            violations=violations,
            warnings=warnings,
            evaluations=evaluations,
            average_confidence=0.8,
            low_confidence_clauses=[],
            model="heuristic",
            unevaluated_clauses=unevaluated,
            all_clauses_evaluated=len(unevaluated) == 0,
            lane_status=lane_status,
        )
