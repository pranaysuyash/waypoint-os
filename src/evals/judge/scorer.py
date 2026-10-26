"""Scorer for LLM-as-judge agent output evaluation.

Evaluates agent execution results against rubric dimensions using
structured scoring. Supports both deterministic heuristic scoring
and LLM-assisted scoring via the existing BaseLLMClient interface.

GOVERNANCE NOTICE (PA-22 / FND-0159):
Default heuristic scoring evaluates structural output shape (field presence,
types, length bounds) and is uncalibrated against human ground truth. It is
designated as a developmental benchmark utility only and MUST NOT be used as
an automated production gating authority without human-calibrated test lanes.
"""


from __future__ import annotations

import json as _json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from src.llm.base import BaseLLMClient, LLMError

from .rubrics import AgentRubric, RubricDimension, build_default_rubrics

if TYPE_CHECKING:
    from src.llm.typesafe_client import TypesafeJevClient

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
    scoring_method: str = "heuristic"  # "llm" | "heuristic" | "mixed" | "jev_shadow"
    calibration_status: str = "uncalibrated_structural_heuristic"
    shadow_score: JudgeScore | None = None
    shadow_disagreement: float | None = None
    shadow_metrics: dict[str, Any] | None = None
    discrepancy_alert: bool = False
    # PA-34 / FND-0165: measured operational dimensions — accuracy alone is
    # not an eval. Extracted from run facts when present; every field is
    # honestly None when the run didn't record it (never fabricated).
    operational_metrics: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "agent_name": self.agent_name,
            "trip_id": self.trip_id,
            "overall_score": round(self.overall_score, 2),
            "passed": self.passed,
            "pass_threshold": self.pass_threshold,
            "verdict": self.verdict,
            "scoring_method": self.scoring_method,
            "calibration_status": self.calibration_status,
            "scored_at": self.scored_at,
            "dimension_scores": [d.to_dict() for d in self.dimension_scores],
        }
        if self.shadow_score is not None:
            data["shadow_score"] = self.shadow_score.to_dict()
        if self.shadow_disagreement is not None:
            data["shadow_disagreement"] = round(self.shadow_disagreement, 2)
            data["discrepancy_alert"] = self.discrepancy_alert
        if self.shadow_metrics is not None:
            data["shadow_metrics"] = self.shadow_metrics
        if self.operational_metrics is not None:
            data["operational_metrics"] = self.operational_metrics
        return data


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
        reasons = agent_output.get("reasons") or agent_output.get("escalation_reasons")
        if isinstance(reasons, list) and reasons:
            joined = " ".join(str(r) for r in reasons)
            if len(joined) > 15:
                return 8.0, f"Escalation has {len(reasons)} substantive reasons"
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
            # Check if destinations contain real intelligence or are empty unverified stubs
            has_details = any(
                isinstance(d, dict) and any(
                    k in d for k in ("seasonality", "notes", "status", "weather", "risk_level")
                    if d.get(k) and d.get(k) not in ("unverified", "unknown")
                )
                for d in dests
            )
            if has_details:
                return 7.5, f"Destination data present with intelligence ({len(dests)} entries)"
            return 4.0, "Destination entries present but unverified or lacking intelligence"
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
        "You are a quality evaluator for a travel agency AI agent system.",
        "",
        f"Agent: {agent_name}",
    ]
    if agent_description:
        lines.append(f"Agent purpose: {agent_description}")
    lines.extend([
        "",
        f"Scoring dimension: {dimension.name}",
        f"Description: {dimension.description}",
        f"Scoring guidance: {dimension.scoring_guidance}",
        f"Weight: {dimension.weight}",
        "",
        "Agent output to evaluate:",
        "```json",
        output_json,
        "```",
    ])
    if expected:
        expected_json = _json.dumps(expected, indent=2, default=str)
        lines.extend([
            "",
            "Expected/reference output:",
            "```json",
            expected_json,
            "```",
        ])
    lines.extend([
        "",
        "Score this dimension from 0 to 10 based on the scoring guidance.",
        "Provide a brief reasoning for the score.",
        "Respond with a JSON object containing 'score' (number) and 'reasoning' (string).",
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


def _score_with_jev(
    agent_name: str,
    trip_id: str,
    rubric: AgentRubric,
    agent_output: dict[str, Any],
    expected: dict[str, Any] | None,
    shadow_client: TypesafeJevClient,
) -> JudgeScore | None:
    """Score all rubric dimensions in parallel using TypeSafe/Jev Score primitive.

    Jev's Score question evaluates a text state against an ordered list of criteria
    levels (0 to N-1) and outputs a continuous calibrated position and confidence.
    """
    try:
        if not shadow_client.is_available():
            return None

        # Build prompt state representing output and context
        state_lines = [
            f"Agent Name: {agent_name}",
            f"Trip ID: {trip_id}",
            f"Agent Role/Description: {rubric.description}",
            f"Agent Execution Output:\n{_json.dumps(agent_output, indent=2, default=str)}",
        ]
        if expected:
            state_lines.append(f"Expected Output:\n{_json.dumps(expected, indent=2, default=str)}")
        state_text = "\n\n".join(state_lines)

        # Standard 4-tier rubric criteria levels (0 to 3)
        rubric_criteria = [
            "Level 0 (Fail / 0-2): Missing key components, severe hallucination, invalid schema, or unacceptable execution.",
            "Level 1 (Needs Review / 3-5): Partially addressed requirements, but notable omissions, inaccuracies, or weak quality.",
            "Level 2 (Pass / 6-8): Meets core requirements and expectations with minor defects or acceptable compromises.",
            "Level 3 (Exemplary / 9-10): Flawless, thorough, strictly adhering to constraints and high domain quality standards.",
        ]

        questions: dict[str, dict[str, Any]] = {}
        dim_map: dict[str, RubricDimension] = {}

        for idx, dim in enumerate(rubric.dimensions):
            qkey = f"q_dim_{idx}_{dim.name}"
            dim_map[qkey] = dim
            instructions = (
                f"Evaluate the agent's performance on dimension '{dim.name}' "
                f"({dim.description}). Guidance: {dim.scoring_guidance or 'Standard evaluation'}."
            )
            questions[qkey] = {
                "type": "score",
                "instructions": instructions,
                "criteria": rubric_criteria,
            }

        response = shadow_client.raw_query(state=state_text, questions=questions)
        answers = response.get("answers", {})

        dimension_scores: list[DimensionScore] = []
        total_weighted = 0.0
        total_weight = 0.0

        for qkey, dim in dim_map.items():
            ans = answers.get(qkey, {})
            raw_score = ans.get("score")
            conf = ans.get("confidence")
            if isinstance(raw_score, (int, float)):
                # Normalize raw 0-3 index scale onto standard 0-10 scale
                norm_score = max(0.0, min(10.0, (float(raw_score) / 3.0) * 10.0))
                reasoning = (
                    f"[jev-score] raw={round(float(raw_score), 2)}/3.0, conf={round(float(conf or 0.0), 2)}"
                )
            else:
                # Fallback to heuristic if dimension answer missing
                h_score, h_reason = _heuristic_score(dim, agent_output, expected)
                norm_score = h_score
                reasoning = f"[jev-fallback-heuristic] {h_reason}"

            ds = DimensionScore(
                dimension=dim.name,
                score=norm_score,
                weight=dim.weight,
                reasoning=reasoning,
            )
            dimension_scores.append(ds)
            total_weighted += ds.weighted_score
            total_weight += ds.weight

        overall = total_weighted / total_weight if total_weight > 0 else 0.0
        passed = overall >= rubric.pass_threshold

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
            scoring_method="jev_shadow",
            calibration_status="jev_calibrated_score_shadow",
        )
    except Exception as exc:
        logger.warning("Jev shadow scoring failed for %s/%s: %s", agent_name, trip_id, exc)
        return None


def _extract_operational_metrics(
    agent_output: dict[str, Any],
    verdict: str,
) -> dict[str, Any]:
    """PA-34 / FND-0165: measure the operational dimensions of one run.

    Sources (verified against the real run shapes):
    - latency: ``meta.execution_ms`` (RunMeta, spine run outputs)
    - LLM telemetry: ``meta.llm_calls`` when the run recorded call forensics
      (count + cost_estimate_inr sum); absent in most outputs today — None
    - human intervention: the run needed a human because it could not proceed
      autonomously — ESCALATE/STOP decision states, ESCALATED validation, or
      a needs_review verdict

    Every field is None when the run didn't record it — absence is reported
    as absence, never fabricated.
    """
    meta = agent_output.get("meta") if isinstance(agent_output.get("meta"), dict) else {}
    latency_ms = meta.get("execution_ms")
    llm_calls = meta.get("llm_calls") if isinstance(meta.get("llm_calls"), (list, dict)) else None
    llm_call_count: int | None = None
    total_cost_inr: float | None = None
    if isinstance(llm_calls, list):
        llm_call_count = len(llm_calls)
        costs = [
            c.get("cost_estimate_inr")
            for c in llm_calls
            if isinstance(c, dict) and isinstance(c.get("cost_estimate_inr"), (int, float))
        ]
        total_cost_inr = round(sum(costs), 6) if costs else None
    elif isinstance(llm_calls, dict):
        llm_call_count = len(llm_calls)

    decision = agent_output.get("decision") if isinstance(agent_output.get("decision"), dict) else {}
    validation = agent_output.get("validation") if isinstance(agent_output.get("validation"), dict) else {}

    reasons: list[str] = []
    state = str(decision.get("decision_state", "") or "")
    if state in ("ESCALATE", "STOP_NEEDS_REVIEW"):
        reasons.append(f"decision_state={state}")
    if str(validation.get("status", "") or "") == "ESCALATED":
        reasons.append("validation_status=ESCALATED")
    if verdict == "needs_review":
        reasons.append("judge_verdict=needs_review")

    return {
        "latency_ms": latency_ms if isinstance(latency_ms, (int, float)) else None,
        "llm_call_count": llm_call_count,
        "total_cost_inr": total_cost_inr,
        "human_intervention_required": bool(reasons),
        "human_intervention_reasons": reasons,
    }


def judge_agent_output(
    agent_name: str,
    trip_id: str,
    agent_output: dict[str, Any],
    expected: dict[str, Any] | None = None,
    rubrics: dict[str, AgentRubric] | None = None,
    llm_client: BaseLLMClient | None = None,
    shadow_judge_client: TypesafeJevClient | None = None,
) -> JudgeScore:
    """Score an agent execution result against its rubric.

    When ``llm_client`` is provided and available, uses LLM-assisted
    scoring for each dimension.  Falls back to deterministic heuristic
    scoring when the LLM is unavailable or fails.

    When ``shadow_judge_client`` is provided, evaluates the result in parallel
    using TypeSafe/Jev's Score primitive and attaches the shadow score and
    disagreement delta to the returned JudgeScore.

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
    shadow_judge_client
        Optional TypeSafe/Jev client for fast calibrated shadow scoring.
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

    # PA-34 / FND-0165: measured operational dimensions ride with every score.
    operational_metrics = _extract_operational_metrics(agent_output, verdict)

    primary_score = JudgeScore(
        agent_name=agent_name,
        trip_id=trip_id,
        dimension_scores=dimension_scores,
        overall_score=overall,
        passed=passed,
        pass_threshold=rubric.pass_threshold,
        scored_at=datetime.now(timezone.utc).isoformat(),
        verdict=verdict,
        scoring_method=scoring_method,
        operational_metrics=operational_metrics,
    )

    # If shadow judge client is provided, evaluate via Jev shadow lane
    if shadow_judge_client is not None:
        shadow_score = _score_with_jev(
            agent_name=agent_name,
            trip_id=trip_id,
            rubric=rubric,
            agent_output=agent_output,
            expected=expected,
            shadow_client=shadow_judge_client,
        )
        if shadow_score is not None:
            primary_score.shadow_score = shadow_score
            disagreement = abs(primary_score.overall_score - shadow_score.overall_score)
            primary_score.shadow_disagreement = disagreement
            primary_score.discrepancy_alert = disagreement >= 2.0
            primary_score.shadow_metrics = {
                "score_delta": round(disagreement, 2),
                "verdict_agreement": primary_score.verdict == shadow_score.verdict,
                "primary_verdict": primary_score.verdict,
                "shadow_verdict": shadow_score.verdict,
                "primary_method": primary_score.scoring_method,
                "shadow_method": shadow_score.scoring_method,
                "discrepancy_alert": primary_score.discrepancy_alert,
            }

    return primary_score


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
            "discrepant_evals": [],
            "operational_summary": {
                "runs_with_latency": 0,
                "mean_latency_ms": None,
                "runs_with_cost": 0,
                "total_cost_inr": None,
                "human_intervention_count": 0,
                "human_intervention_rate": 0.0,
            },
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

    discrepant_evals = [
        {
            "agent_name": s.agent_name,
            "trip_id": s.trip_id,
            "primary_score": round(s.overall_score, 2),
            "primary_verdict": s.verdict,
            "shadow_score": round(s.shadow_score.overall_score, 2) if s.shadow_score else None,
            "shadow_verdict": s.shadow_score.verdict if s.shadow_score else None,
            "score_delta": round(s.shadow_disagreement, 2) if s.shadow_disagreement is not None else None,
        }
        for s in scores
        if s.discrepancy_alert
    ]

    total_passed = sum(1 for s in scores if s.passed)

    # PA-34 / FND-0165: operational aggregation — cost, latency, and the
    # human-intervention rate across the scored runs. Runs without recorded
    # telemetry are excluded from the mean, never zero-filled.
    latencies = [
        s.operational_metrics["latency_ms"]
        for s in scores
        if s.operational_metrics and isinstance(s.operational_metrics.get("latency_ms"), (int, float))
    ]
    costs = [
        s.operational_metrics["total_cost_inr"]
        for s in scores
        if s.operational_metrics and isinstance(s.operational_metrics.get("total_cost_inr"), (int, float))
    ]
    interventions = [
        s for s in scores
        if s.operational_metrics and s.operational_metrics.get("human_intervention_required")
    ]
    operational_summary: dict[str, Any] = {
        "runs_with_latency": len(latencies),
        "mean_latency_ms": round(sum(latencies) / len(latencies), 1) if latencies else None,
        "runs_with_cost": len(costs),
        "total_cost_inr": round(sum(costs), 6) if costs else None,
        "human_intervention_count": len(interventions),
        "human_intervention_rate": round(len(interventions) / len(scores), 4) if scores else 0.0,
    }

    return {
        "total_scored": len(scores),
        "total_passed": total_passed,
        "pass_rate": round(total_passed / len(scores), 4),
        "average_score": round(sum(s.overall_score for s in scores) / len(scores), 2),
        "agents": agent_summaries,
        "discrepant_evals": discrepant_evals,
        "operational_summary": operational_summary,
    }


def compute_judge_shadow_agreement(
    primary_scores: list[JudgeScore],
    shadow_scores: list[JudgeScore] | None = None,
) -> dict[str, Any]:
    """Compute agreement metrics (including Cohen's kappa) between primary and shadow scores.

    If shadow_scores is None, extracts shadow scores from primary_scores.shadow_score.
    Calculates:
    - Observed accuracy / agreement rate: proportion of identical categorical verdicts
    - Expected agreement by chance: sum(p_primary(c) * p_shadow(c))
    - Cohen's kappa: (P_o - P_e) / (1 - P_e)
    - Mean absolute score delta across samples
    """
    paired: list[tuple[JudgeScore, JudgeScore]] = []

    if shadow_scores is not None:
        for p, s in zip(primary_scores, shadow_scores):
            paired.append((p, s))
    else:
        for p in primary_scores:
            if p.shadow_score is not None:
                paired.append((p, p.shadow_score))

    n = len(paired)
    if n == 0:
        return {
            "total_pairs": 0,
            "raw_agreement": 0.0,
            "cohens_kappa": 0.0,
            "mean_score_delta": 0.0,
            "interpretation": "no_data",
        }

    categories = ["pass", "needs_review", "fail"]
    primary_counts = {c: 0 for c in categories}
    shadow_counts = {c: 0 for c in categories}
    matrix = {c1: {c2: 0 for c2 in categories} for c1 in categories}

    score_deltas: list[float] = []

    for p, s in paired:
        pv = p.verdict if p.verdict in categories else "needs_review"
        sv = s.verdict if s.verdict in categories else "needs_review"
        primary_counts[pv] += 1
        shadow_counts[sv] += 1
        matrix[pv][sv] += 1
        score_deltas.append(abs(p.overall_score - s.overall_score))

    # Observed agreement P_o
    agreed_count = sum(matrix[c][c] for c in categories)
    p_o = agreed_count / n

    # Expected agreement by chance P_e
    p_e = sum((primary_counts[c] / n) * (shadow_counts[c] / n) for c in categories)

    # Cohen's kappa
    if abs(1.0 - p_e) < 1e-9:
        kappa = 1.0 if abs(1.0 - p_o) < 1e-9 else 0.0
    else:
        kappa = (p_o - p_e) / (1.0 - p_e)

    # Standard Landis & Koch (1977) interpretation
    if kappa < 0:
        interpretation = "poor"
    elif kappa <= 0.20:
        interpretation = "slight"
    elif kappa <= 0.40:
        interpretation = "fair"
    elif kappa <= 0.60:
        interpretation = "moderate"
    elif kappa <= 0.80:
        interpretation = "substantial"
    else:
        interpretation = "almost_perfect"

    return {
        "total_pairs": n,
        "raw_agreement": round(p_o, 4),
        "expected_chance_agreement": round(p_e, 4),
        "cohens_kappa": round(kappa, 4),
        "mean_score_delta": round(sum(score_deltas) / n, 2),
        "interpretation": interpretation,
        "confusion_matrix": matrix,
    }
