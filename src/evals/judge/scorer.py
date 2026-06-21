"""Scorer for LLM-as-judge agent output evaluation.

Evaluates agent execution results against rubric dimensions using
structured scoring.  Supports both deterministic heuristic scoring
and LLM-assisted scoring via the existing BaseLLMClient interface.
"""

from __future__ import annotations

import json as _json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from src.llm.base import BaseLLMClient, LLMError

from .rubrics import AgentRubric, RubricDimension, build_default_rubrics

logger = logging.getLogger("evals.judge")


@dataclass(slots=True)
class DimensionScore:
    """Score for a single rubric dimension."""

    dimension: str
    score: float  # 0-10
    weight: float
    reasoning: str = ""

    @property
    def weighted_score(self) -> float:
        return self.score * self.weight

    def to_dict(self) -> dict[str, Any]:
        return {
            "dimension": self.dimension,
            "score": round(self.score, 2),
            "weight": self.weight,
            "weighted_score": round(self.weighted_score, 2),
            "reasoning": self.reasoning,
        }


@dataclass(slots=True)
class JudgeScore:
    """Aggregated judge score for an agent execution result."""

    agent_name: str
    trip_id: str
    dimension_scores: list[DimensionScore] = field(default_factory=list)
    overall_score: float = 0.0
    passed: bool = False
    pass_threshold: float = 7.0
    scored_at: str = ""
    verdict: str = ""  # "pass" | "fail" | "needs_review"
    scoring_method: str = "heuristic"  # "llm" | "heuristic" | "mixed"

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_name": self.agent_name,
            "trip_id": self.trip_id,
            "overall_score": round(self.overall_score, 2),
            "passed": self.passed,
            "pass_threshold": self.pass_threshold,
            "verdict": self.verdict,
            "scoring_method": self.scoring_method,
            "scored_at": self.scored_at,
            "dimension_scores": [d.to_dict() for d in self.dimension_scores],
        }


def _heuristic_score(
    dimension: RubricDimension,
    agent_output: dict[str, Any],
    expected: dict[str, Any] | None = None,
) -> tuple[float, str]:
    """Compute a heuristic score for a dimension based on agent output shape.

    This is a deterministic baseline scorer that evaluates structural
    completeness without requiring an LLM call.  For production use,
    the LLM-assisted scorer should be used.
    """
    name = dimension.name

    # --- classification accuracy ---
    if name == "classification_accuracy":
        has_assessment = bool(agent_output.get("front_door_assessment") or agent_output.get("is_real_lead"))
        if has_assessment:
            return 8.0, "Agent produced a front_door_assessment with classification"
        return 3.0, "No front_door_assessment found in output"

    # --- priority correctness ---
    if name == "priority_correctness":
        priority = agent_output.get("priority") or agent_output.get("lead_priority")
        if priority in {"urgent", "high", "normal", "low"}:
            return 7.0, f"Priority set to '{priority}' — plausible value"
        return 2.0, "No valid priority found in output"

    # --- missing fields ---
    if name == "missing_fields_identified":
        missing = agent_output.get("missing_fields") or agent_output.get("missing_facts")
        if isinstance(missing, list) and missing:
            return 8.0, f"Identified {len(missing)} missing fields"
        if isinstance(missing, list) and not missing:
            return 7.0, "No missing fields reported (may be correct or missed)"
        return 3.0, "Missing fields not structured as list"

    # --- acknowledgment ---
    if name == "acknowledgment_quality":
        ack = agent_output.get("acknowledgment_draft")
        if isinstance(ack, str) and len(ack) > 20:
            return 8.0, "Acknowledgment draft present and substantive"
        return 4.0, "Acknowledgment draft missing or too short"

    # --- checklist completeness ---
    if name == "checklist_completeness":
        items = agent_output.get("items") or agent_output.get("checklist")
        if isinstance(items, list) and len(items) >= 3:
            return 8.0, f"Checklist has {len(items)} items"
        return 3.0, f"Checklist has {len(items) if isinstance(items, list) else 0} items (too few)"

    # --- risk calibration ---
    if name == "risk_calibration":
        risk = agent_output.get("risk_level") or agent_output.get("document_risk_level")
        if risk in {"high", "medium", "low", "unknown"}:
            return 7.0, f"Risk level set to '{risk}' — valid value"
        return 3.0, "No valid risk level found"

    # --- blocker detection ---
    if name == "blocker_detection":
        hard = agent_output.get("hard_blockers") or agent_output.get("feasibility_hard_blockers")
        if isinstance(hard, list):
            return 7.0, f"Hard blockers list present ({len(hard)} items)"
        return 3.0, "Hard blockers not structured as list"

    # --- escalation accuracy ---
    if name == "escalation_accuracy":
        status = agent_output.get("review_status") or agent_output.get("escalation_reason")
        if status:
            return 8.0, "Escalation status/reason present in output"
        return 5.0, "No explicit escalation status in output"

    # --- follow_up_timing ---
    if name == "follow_up_timing":
        due = agent_output.get("follow_up_due_date")
        if due:
            return 8.0, "Follow-up due date scheduled"
        return 3.0, "No follow-up due date found"

    # --- signal detection ---
    if name == "signal_detection":
        signals = agent_output.get("signals") or agent_output.get("destinations")
        if isinstance(signals, list) and signals:
            return 7.0, f"Signal/destination data present ({len(signals)} entries)"
        return 3.0, "No signals detected in output"

    # --- recommendation relevance ---
    if name == "recommendation_relevance":
        recs = agent_output.get("recommendations")
        if isinstance(recs, list) and recs:
            return 7.0, f"Recommendations present ({len(recs)} items)"
        return 3.0, "No recommendations in output"

    # --- soft constraint detection ---
    if name == "soft_constraint_detection":
        soft = agent_output.get("soft_constraints") or agent_output.get("feasibility_soft_constraints")
        if isinstance(soft, list):
            return 7.0, f"Soft constraints list present ({len(soft)} items)"
        return 4.0, "Soft constraints not found"

    # --- missing facts ---
    if name == "missing_facts_identified":
        facts = agent_output.get("missing_facts") or agent_output.get("feasibility_missing_facts")
        if isinstance(facts, list):
            return 7.0, f"Missing facts list present ({len(facts)} items)"
        return 4.0, "Missing facts not found"

    # --- severity calibration ---
    if name == "severity_calibration":
        status = agent_output.get("feasibility_status") or agent_output.get("status")
        if status in {"feasible", "blocked", "needs_review", "conditional"}:
            return 7.0, f"Feasibility status set to '{status}'"
        return 4.0, "No clear feasibility status"

    # --- reason quality ---
    if name == "reason_quality":
        reason = agent_output.get("escalation_reason") or agent_output.get("reason")
        if isinstance(reason, str) and len(reason) > 10:
            return 7.0, "Reason is substantive"
        return 3.0, "Reason missing or too brief"

    # --- draft quality ---
    if name == "draft_quality":
        draft = agent_output.get("follow_up_draft")
        if isinstance(draft, str) and len(draft) > 20:
            return 8.0, "Draft present and substantive"
        return 3.0, "Draft missing or too short"

    # --- utility detection ---
    if name == "utility_detection":
        flags = agent_output.get("findings") or []
        if isinstance(flags, list):
            return 6.0, "Findings list present (heuristic baseline)"
        return 3.0, "No findings in output"

    # --- wasted spend detection ---
    if name == "wasted_spend_detection":
        total = agent_output.get("total_amount") or agent_output.get("wasted_spend")
        if total is not None:
            return 7.0, "Wasted spend data present"
        return 4.0, "Wasted spend not found"

    # --- destination accuracy ---
    if name == "destination_accuracy":
        dests = agent_output.get("destinations")
        if isinstance(dests, list) and dests:
            return 7.0, f"Destination data present ({len(dests)} entries)"
        return 3.0, "No destination data"

    # --- must_confirm_coverage ---
    if name == "must_confirm_coverage":
        mc = agent_output.get("must_confirm")
        if isinstance(mc, list) and mc:
            return 7.0, f"Must-confirm list present ({len(mc)} items)"
        return 3.0, "Must-confirm list missing"

    # Fallback: neutral score
    return 5.0, f"No heuristic rule for dimension '{name}'"


# ---------------------------------------------------------------------------
# LLM-assisted scoring
# ---------------------------------------------------------------------------

# JSON schema that BaseLLMClient.decide() must produce per dimension.
_DIMENSION_SCORE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "score": {
            "type": "number",
            "description": "Score from 0 to 10 for this dimension.",
        },
        "reasoning": {
            "type": "string",
            "description": "Brief explanation of the score.",
        },
    },
    "required": ["score", "reasoning"],
}


def _build_dimension_prompt(
    agent_name: str,
    dimension: RubricDimension,
    agent_output: dict[str, Any],
    expected: dict[str, Any] | None = None,
    agent_description: str = "",
) -> str:
    """Build an LLM prompt for scoring a single rubric dimension."""
    output_json = _json.dumps(agent_output, indent=2, default=str)
    lines = [
        f"You are a quality evaluator for a travel agency AI agent system.",
        f"",
        f"Agent: {agent_name}",
    ]
    if agent_description:
        lines.append(f"Agent purpose: {agent_description}")
    lines.extend([
        f"",
        f"Scoring dimension: {dimension.name}",
        f"Description: {dimension.description}",
        f"Scoring guidance: {dimension.scoring_guidance}",
        f"Weight: {dimension.weight}",
        f"",
        f"Agent output to evaluate:",
        f"```json",
        output_json,
        f"```",
    ])
    if expected:
        expected_json = _json.dumps(expected, indent=2, default=str)
        lines.extend([
            f"",
            f"Expected/reference output:",
            f"```json",
            expected_json,
            f"```",
        ])
    lines.extend([
        f"",
        f"Score this dimension from 0 to 10 based on the scoring guidance.",
        f"Provide a brief reasoning for the score.",
        f"Respond with a JSON object containing 'score' (number) and 'reasoning' (string).",
    ])
    return "\n".join(lines)


def _llm_score_dimension(
    llm_client: BaseLLMClient,
    agent_name: str,
    dimension: RubricDimension,
    agent_output: dict[str, Any],
    expected: dict[str, Any] | None = None,
    agent_description: str = "",
) -> tuple[float, str] | None:
    """Score a dimension using the LLM.  Returns (score, reasoning) or None on failure."""
    prompt = _build_dimension_prompt(
        agent_name=agent_name,
        dimension=dimension,
        agent_output=agent_output,
        expected=expected,
        agent_description=agent_description,
    )
    try:
        result = llm_client.decide(
            prompt=prompt,
            schema=_DIMENSION_SCORE_SCHEMA,
            temperature=0.2,
        )
    except (LLMError, Exception) as exc:
        logger.warning(
            "LLM scoring failed for %s/%s: %s — falling back to heuristic",
            agent_name,
            dimension.name,
            exc,
        )
        return None

    score = result.get("score")
    reasoning = str(result.get("reasoning") or "")
    if not isinstance(score, (int, float)):
        return None
    # Clamp to valid range
    clamped = max(0.0, min(10.0, float(score)))
    return clamped, reasoning


def judge_agent_output(
    agent_name: str,
    trip_id: str,
    agent_output: dict[str, Any],
    expected: dict[str, Any] | None = None,
    rubrics: dict[str, AgentRubric] | None = None,
    llm_client: BaseLLMClient | None = None,
) -> JudgeScore:
    """Score an agent execution result against its rubric.

    When ``llm_client`` is provided and available, uses LLM-assisted
    scoring for each dimension.  Falls back to deterministic heuristic
    scoring when the LLM is unavailable, unavailable, or fails.

    Parameters
    ----------
    agent_name
        Name of the agent whose output is being scored.
    trip_id
        Trip identifier for the execution being scored.
    agent_output
        The agent's execution result output dict.
    expected
        Optional expected output for comparison-based scoring.
    rubrics
        Optional custom rubric set.  Falls back to defaults.
    llm_client
        Optional LLM client for assisted scoring.  When ``None`` or
        unavailable, heuristic scoring is used.
    """
    if rubrics is None:
        rubrics = build_default_rubrics()

    rubric = rubrics.get(agent_name)
    if rubric is None:
        return JudgeScore(
            agent_name=agent_name,
            trip_id=trip_id,
            overall_score=0.0,
            passed=False,
            pass_threshold=7.0,
            scored_at=datetime.now(timezone.utc).isoformat(),
            verdict="needs_review",
        )

    # Determine whether LLM is usable
    use_llm = False
    if llm_client is not None:
        try:
            use_llm = llm_client.is_available()
        except Exception:
            use_llm = False

    dimension_scores: list[DimensionScore] = []
    total_weighted = 0.0
    total_weight = 0.0
    llm_count = 0
    heuristic_count = 0

    for dim in rubric.dimensions:
        llm_result: tuple[float, str] | None = None
        if use_llm:
            llm_result = _llm_score_dimension(
                llm_client=llm_client,  # type: ignore[arg-type]
                agent_name=agent_name,
                dimension=dim,
                agent_output=agent_output,
                expected=expected,
                agent_description=rubric.description,
            )
        if llm_result is not None:
            score, reasoning = llm_result
            llm_count += 1
        else:
            score, reasoning = _heuristic_score(dim, agent_output, expected)
            heuristic_count += 1

        ds = DimensionScore(
            dimension=dim.name,
            score=score,
            weight=dim.weight,
            reasoning=reasoning,
        )
        dimension_scores.append(ds)
        total_weighted += ds.weighted_score
        total_weight += ds.weight

    overall = total_weighted / total_weight if total_weight > 0 else 0.0
    passed = overall >= rubric.pass_threshold

    # Determine scoring_method from actual per-dimension counts
    if use_llm and llm_count > 0 and heuristic_count == 0:
        scoring_method = "llm"
    elif use_llm and llm_count > 0 and heuristic_count > 0:
        scoring_method = "mixed"
    else:
        scoring_method = "heuristic"

    if overall >= rubric.pass_threshold:
        verdict = "pass"
    elif overall >= rubric.pass_threshold - 2.0:
        verdict = "needs_review"
    else:
        verdict = "fail"

    return JudgeScore(
        agent_name=agent_name,
        trip_id=trip_id,
        dimension_scores=dimension_scores,
        overall_score=overall,
        passed=passed,
        pass_threshold=rubric.pass_threshold,
        scored_at=datetime.now(timezone.utc).isoformat(),
        verdict=verdict,
        scoring_method=scoring_method,
    )


def build_judge_report(
    scores: list[JudgeScore],
) -> dict[str, Any]:
    """Build an aggregated judge report from individual scores.

    Returns a JSON-serialisable summary suitable for the D6 gate snapshot
    or operational dashboards.
    """
    if not scores:
        return {
            "total_scored": 0,
            "pass_rate": 0.0,
            "average_score": 0.0,
            "agents": {},
        }

    by_agent: dict[str, list[JudgeScore]] = {}
    for s in scores:
        by_agent.setdefault(s.agent_name, []).append(s)

    agent_summaries: dict[str, Any] = {}
    for agent_name, agent_scores in by_agent.items():
        passed = sum(1 for s in agent_scores if s.passed)
        total = len(agent_scores)
        avg = sum(s.overall_score for s in agent_scores) / total if total else 0.0
        agent_summaries[agent_name] = {
            "total_scored": total,
            "passed": passed,
            "pass_rate": round(passed / total, 4) if total else 0.0,
            "average_score": round(avg, 2),
            "worst_score": round(min(s.overall_score for s in agent_scores), 2),
            "verdicts": {
                "pass": sum(1 for s in agent_scores if s.verdict == "pass"),
                "needs_review": sum(1 for s in agent_scores if s.verdict == "needs_review"),
                "fail": sum(1 for s in agent_scores if s.verdict == "fail"),
            },
        }

    total_passed = sum(1 for s in scores if s.passed)
    return {
        "total_scored": len(scores),
        "total_passed": total_passed,
        "pass_rate": round(total_passed / len(scores), 4),
        "average_score": round(sum(s.overall_score for s in scores) / len(scores), 2),
        "agents": agent_summaries,
    }
