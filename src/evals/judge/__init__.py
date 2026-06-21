"""LLM-as-judge module for scoring agent output quality.

Provides rubric-based evaluation of agent execution results against
expected outcomes, using the existing LLM client infrastructure.
"""

from .rubrics import AgentRubric, RubricDimension, build_default_rubrics
from .scorer import DimensionScore, JudgeScore, judge_agent_output, build_judge_report

__all__ = [
    "AgentRubric",
    "RubricDimension",
    "build_default_rubrics",
    "DimensionScore",
    "JudgeScore",
    "judge_agent_output",
    "build_judge_report",
]
