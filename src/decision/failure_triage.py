"""Run-Failure Triage Second Opinion (Lane A5).

Provides a calibrated second opinion on ambiguous or unclassified pipeline failures
using Jev's Choice primitive over the canonical PA-07 FailureClass taxonomy,
paired with a Score question for failure severity.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional

from spine_api.failure_taxonomy import FailureClass
from src.llm.typesafe_client import TypesafeJevClient

logger = logging.getLogger(__name__)

# Canonical FailureClass criteria descriptions for Jev Choice
FAILURE_CLASS_CRITERIA: Dict[str, str] = {
    FailureClass.MODEL.value: "LLM provider or inference error, generation failure, token overflow, or model API outage.",
    FailureClass.TOOL.value: "Network request, HTTP client timeout, socket disconnect, or external tool failure.",
    FailureClass.ENVIRONMENT.value: "Infrastructure, disk exhaustion, OS resource limit, or execution environment failure.",
    FailureClass.STATE.value: "Database, persistence layer divergence, ledger concurrency, or storage corruption.",
    FailureClass.VERIFICATION.value: "Assertion error, postcondition failure, schema violation, or test invariant failure.",
    FailureClass.AUTHORITY.value: "Permission denied, missing API scopes, forbidden resource, or role authorization fault.",
    FailureClass.POLICY_BLOCK.value: "Safety policy violation, PII leakage block, prompt injection filter, or duty-of-care gate.",
    FailureClass.UNCLASSIFIED.value: "Generic or unknown error that does not clearly match any defined category.",
}


@dataclass
class FailureTriageOpinion:
    recommended_class: FailureClass
    confidence: float
    probabilities: Dict[str, float]
    severity_score: float  # 0.0 to 10.0
    requires_human_escalation: bool
    is_requeueable: bool
    reasoning: str
    model: str
    # FND-0352 lane semantics: "jev" when the model lane ran,
    # "model_lane_unconfigured" (no credentials — heuristic by posture), or
    # "model_call_failed" (configured lane errored — heuristic fallback).
    # Same vocabulary as the intake ambiguity / live-triage / NL-policy lanes.
    lane_status: str = "jev"


class FailureTriageEngine:
    """Evaluates ambiguous or unclassified failure traces and advises the recovery agent."""

    def __init__(
        self,
        jev_client: Optional[TypesafeJevClient] = None,
        confidence_threshold: float = 0.65,
    ) -> None:
        self.jev_client = jev_client
        self.confidence_threshold = confidence_threshold

    def evaluate_failure(
        self,
        error_message: str,
        traceback_text: str,
        stage: Optional[str] = None,
    ) -> FailureTriageOpinion:
        state = f"""Stage: {stage or 'unknown'}
Error: {error_message}
Traceback:
{traceback_text}"""

        if self.jev_client and self.jev_client.is_available():
            return self._evaluate_with_jev(state)
        # Unconfigured lane (no credentials) vs call-failed is distinguished
        # inside _evaluate_with_jev's own exception path (FND-0352).
        return self._evaluate_heuristic(
            error_message, traceback_text, lane_status="model_lane_unconfigured"
        )

    def _evaluate_with_jev(self, state: str) -> FailureTriageOpinion:
        questions: Dict[str, Dict[str, Any]] = {
            "failure_class": {
                "type": "choice",
                "question": "Which operational failure category most accurately describes the root cause of this execution failure?",
                "criteria": FAILURE_CLASS_CRITERIA,
            },
            "severity": {
                "type": "score",
                "question": "How severe is this system failure on a scale of 0 (negligible/transient) to 3 (critical/corrupting/unrecoverable)?",
                # Jev score primitives require explicit criteria (API 422 without
                # them — the Jev path silently degraded to heuristic before this).
                "criteria": [
                    {"label": "0", "description": "Negligible or transient: retry succeeds, no state affected"},
                    {"label": "1", "description": "Minor: one step failed, no data corruption, recoverable"},
                    {"label": "2", "description": "Major: pipeline blocked, state inconsistency or data loss risk"},
                    {"label": "3", "description": "Critical: corrupting or unrecoverable, affects multiple trips or agencies"},
                ],
            },
        }

        try:
            resp = self.jev_client.raw_query(state=state, questions=questions)
            answers = resp.get("answers", {})
            model = resp.get("model", self.jev_client.model)
        except Exception as e:
            logger.warning("Jev failure triage query failed (%s), using heuristic", e)
            return self._evaluate_heuristic(
                state, "", lane_status="model_call_failed"
            )

        fc_answer = answers.get("failure_class", {})
        sev_answer = answers.get("severity", {})

        chosen_name = fc_answer.get("choice", FailureClass.UNCLASSIFIED.value)
        try:
            recommended_class = FailureClass(chosen_name)
        except ValueError:
            recommended_class = FailureClass.UNCLASSIFIED

        # Contract: a Jev answer without a calibrated confidence is treated as
        # 0.5 — deliberately BELOW ``confidence_threshold`` (0.65) so the
        # missing calibration forces ``requires_human_escalation`` rather
        # than silently passing as trustworthy. Never raise this default.
        conf = float(fc_answer.get("confidence", 0.5))
        probs = fc_answer.get("probabilities", {})

        # Jev score is on 0-3 scale; normalize to 0-10
        raw_score = float(sev_answer.get("score", 1.0))
        normalized_severity = round(min(10.0, max(0.0, (raw_score / 3.0) * 10.0)), 2)

        # Policy & escalation rules
        is_requeueable = recommended_class in {
            FailureClass.TOOL,
            FailureClass.MODEL,
            FailureClass.ENVIRONMENT,
        }
        requires_escalation = (
            recommended_class in {FailureClass.STATE, FailureClass.VERIFICATION, FailureClass.AUTHORITY}
            or recommended_class == FailureClass.POLICY_BLOCK
            or conf < self.confidence_threshold
            or normalized_severity >= 7.0
        )

        reasoning = (
            f"Jev classified failure as '{recommended_class.value}' with confidence {conf:.2f}. "
            f"Estimated severity: {normalized_severity:.1f}/10."
        )

        return FailureTriageOpinion(
            recommended_class=recommended_class,
            confidence=conf,
            probabilities=probs,
            severity_score=normalized_severity,
            requires_human_escalation=requires_escalation,
            is_requeueable=is_requeueable,
            reasoning=reasoning,
            model=model,
            lane_status="jev",
        )

    def _evaluate_heuristic(
        self,
        error_message: str,
        traceback_text: str,
        lane_status: str = "model_lane_unconfigured",
    ) -> FailureTriageOpinion:
        """Deterministic keyword classification.

        ``lane_status`` records WHY the heuristic served (FND-0352 lane
        semantics): the model lane was unconfigured (no credentials —
        posture) or configured but the call failed. Same vocabulary as the
        intake ambiguity / live-triage / NL-policy lanes."""
        combined = f"{error_message} {traceback_text}".lower()
        if "leakage" in combined or "pii" in combined or "blocked by policy" in combined:
            fc = FailureClass.POLICY_BLOCK
            severity = 9.0
        elif "permission" in combined or "unauthorized" in combined or "forbidden" in combined:
            fc = FailureClass.AUTHORITY
            severity = 8.0
        elif "assert" in combined or "validationerror" in combined:
            fc = FailureClass.VERIFICATION
            severity = 7.0
        elif "sqlite" in combined or "database" in combined or "integrityerror" in combined:
            fc = FailureClass.STATE
            severity = 8.0
        elif "rate limit" in combined or "quota" in combined or "model" in combined or "openai" in combined:
            fc = FailureClass.MODEL
            severity = 5.0
        elif "timeout" in combined or "connection" in combined or "httperror" in combined:
            fc = FailureClass.TOOL
            severity = 4.0
        else:
            fc = FailureClass.UNCLASSIFIED
            severity = 5.0

        is_requeueable = fc in {FailureClass.TOOL, FailureClass.MODEL, FailureClass.ENVIRONMENT}
        requires_escalation = fc in {FailureClass.STATE, FailureClass.VERIFICATION, FailureClass.AUTHORITY, FailureClass.POLICY_BLOCK}

        return FailureTriageOpinion(
            recommended_class=fc,
            confidence=0.8,
            probabilities={fc.value: 1.0},
            severity_score=severity,
            requires_human_escalation=requires_escalation,
            is_requeueable=is_requeueable,
            reasoning=f"Heuristic classified failure as '{fc.value}'.",
            model="heuristic",
            lane_status=lane_status,
        )
