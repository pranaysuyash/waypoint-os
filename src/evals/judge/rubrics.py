"""Per-agent rubric definitions for LLM-as-judge scoring.

Each agent type has a rubric with scored dimensions that the judge
evaluates against. Dimensions are scored 0-10 and mapped to severity.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class RubricDimension:
    """A single scored dimension within an agent rubric."""

    name: str
    weight: float = 1.0
    description: str = ""
    scoring_guidance: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "weight": self.weight,
            "description": self.description,
            "scoring_guidance": self.scoring_guidance,
        }


@dataclass(slots=True)
class AgentRubric:
    """Rubric for evaluating a specific agent type's output quality."""

    agent_name: str
    dimensions: list[RubricDimension] = field(default_factory=list)
    pass_threshold: float = 7.0
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_name": self.agent_name,
            "pass_threshold": self.pass_threshold,
            "description": self.description,
            "dimensions": [d.to_dict() for d in self.dimensions],
        }


# ---------------------------------------------------------------------------
# Default rubrics per agent type
# ---------------------------------------------------------------------------

_FRONT_DOOR_DIMENSIONS = [
    RubricDimension(
        name="classification_accuracy",
        weight=2.0,
        description="Is the inquiry correctly classified (real lead vs noise)?",
        scoring_guidance="10 = perfect classification, 0 = misclassified",
    ),
    RubricDimension(
        name="priority_correctness",
        weight=1.5,
        description="Is the priority level appropriate given the trip context?",
        scoring_guidance="10 = priority matches urgency signals, 0 = wrong priority",
    ),
    RubricDimension(
        name="missing_fields_identified",
        weight=1.0,
        description="Are all missing fields correctly identified?",
        scoring_guidance="10 = all missing fields found, 0 = major fields missed",
    ),
    RubricDimension(
        name="acknowledgment_quality",
        weight=1.0,
        description="Is the acknowledgment draft professional and helpful?",
        scoring_guidance="10 = clear, professional, actionable draft",
    ),
]

_DOCUMENT_READINESS_DIMENSIONS = [
    RubricDimension(
        name="checklist_completeness",
        weight=2.0,
        description="Does the checklist cover all relevant document categories?",
        scoring_guidance="10 = visa, passport, insurance, transit all covered",
    ),
    RubricDimension(
        name="risk_calibration",
        weight=1.5,
        description="Are risk levels appropriately assigned to each item?",
        scoring_guidance="10 = risk levels match real-world document requirements",
    ),
    RubricDimension(
        name="destination_accuracy",
        weight=1.5,
        description="Are destination-specific rules correctly applied?",
        scoring_guidance="10 = correct rules for each destination/passport combo",
    ),
    RubricDimension(
        name="must_confirm_coverage",
        weight=1.0,
        description="Does the must-confirm list capture all critical items?",
        scoring_guidance="10 = nothing critical is missing from must-confirm",
    ),
]

_DESTINATION_INTELLIGENCE_DIMENSIONS = [
    RubricDimension(
        name="risk_assessment_accuracy",
        weight=2.0,
        description="Is the destination risk level correctly assessed?",
        scoring_guidance="10 = risk matches actual conditions, 0 = wrong risk",
    ),
    RubricDimension(
        name="signal_detection",
        weight=1.5,
        description="Are material weather signals correctly detected?",
        scoring_guidance="10 = all relevant signals found, no false signals",
    ),
    RubricDimension(
        name="recommendation_relevance",
        weight=1.5,
        description="Are recommendations actionable and relevant?",
        scoring_guidance="10 = every recommendation is actionable and appropriate",
    ),
]

_CONSTRAINT_FEASIBILITY_DIMENSIONS = [
    RubricDimension(
        name="blocker_detection",
        weight=2.0,
        description="Are hard blockers correctly identified?",
        scoring_guidance="10 = all genuine hard blockers found, no false blockers",
    ),
    RubricDimension(
        name="soft_constraint_detection",
        weight=1.5,
        description="Are soft constraints appropriately flagged?",
        scoring_guidance="10 = soft constraints match real constraints",
    ),
    RubricDimension(
        name="missing_facts_identified",
        weight=1.0,
        description="Are missing facts correctly listed?",
        scoring_guidance="10 = all missing facts identified",
    ),
    RubricDimension(
        name="severity_calibration",
        weight=1.5,
        description="Are hard/soft distinctions correctly made?",
        scoring_guidance="10 = no hard/soft misclassifications",
    ),
]

_QUALITY_ESCALATION_DIMENSIONS = [
    RubricDimension(
        name="escalation_accuracy",
        weight=2.0,
        description="Is escalation triggered for the right trips?",
        scoring_guidance="10 = no false escalations, no missed escalations",
    ),
    RubricDimension(
        name="reason_quality",
        weight=1.0,
        description="Is the escalation reason clear and specific?",
        scoring_guidance="10 = reason is actionable for the human reviewer",
    ),
]

_SALES_ACTIVATION_DIMENSIONS = [
    RubricDimension(
        name="follow_up_timing",
        weight=2.0,
        description="Is the follow-up scheduled at the right time?",
        scoring_guidance="10 = timing matches stage SLA and lead temperature",
    ),
    RubricDimension(
        name="draft_quality",
        weight=1.5,
        description="Is the follow-up draft appropriate for the stage?",
        scoring_guidance="10 = draft is stage-appropriate and professional",
    ),
]

_ACTIVITY_DIMENSIONS = [
    RubricDimension(
        name="utility_detection",
        weight=2.0,
        description="Are low-utility activities correctly detected?",
        scoring_guidance="10 = all low-utility activities found, no false positives",
    ),
    RubricDimension(
        name="wasted_spend_detection",
        weight=1.5,
        description="Is wasted spend correctly calculated?",
        scoring_guidance="10 = amount and affected participants match",
    ),
]


def build_default_rubrics() -> dict[str, AgentRubric]:
    """Build the default rubric set for all known agent types.

    Returns a dict keyed by agent name, suitable for use by the judge scorer.
    """
    return {
        "front_door_agent": AgentRubric(
            agent_name="front_door_agent",
            dimensions=_FRONT_DOOR_DIMENSIONS,
            pass_threshold=7.0,
            description="Classifies fresh or incomplete inquiries so every lead gets a next operational step.",
        ),
        "document_readiness_agent": AgentRubric(
            agent_name="document_readiness_agent",
            dimensions=_DOCUMENT_READINESS_DIMENSIONS,
            pass_threshold=7.0,
            description="Creates passport, visa, insurance, and transit readiness checklists.",
        ),
        "destination_intelligence_agent": AgentRubric(
            agent_name="destination_intelligence_agent",
            dimensions=_DESTINATION_INTELLIGENCE_DIMENSIONS,
            pass_threshold=7.0,
            description="Attaches destination weather/risk intelligence with freshness-aware evidence.",
        ),
        "constraint_feasibility_agent": AgentRubric(
            agent_name="constraint_feasibility_agent",
            dimensions=_CONSTRAINT_FEASIBILITY_DIMENSIONS,
            pass_threshold=7.0,
            description="Detects impossible or risky budget/date/document/weather/pace combinations.",
        ),
        "quality_escalation_agent": AgentRubric(
            agent_name="quality_escalation_agent",
            dimensions=_QUALITY_ESCALATION_DIMENSIONS,
            pass_threshold=8.0,
            description="Escalates high-risk or blocked trips to human review.",
        ),
        "sales_activation_agent": AgentRubric(
            agent_name="sales_activation_agent",
            dimensions=_SALES_ACTIVATION_DIMENSIONS,
            pass_threshold=7.0,
            description="Keeps qualified leads moving by scheduling stage-aware follow-up tasks.",
        ),
        "activity_analyzer": AgentRubric(
            agent_name="activity_analyzer",
            dimensions=_ACTIVITY_DIMENSIONS,
            pass_threshold=7.0,
            description="Evaluates itinerary activity utility and wasted spend.",
        ),
    }
