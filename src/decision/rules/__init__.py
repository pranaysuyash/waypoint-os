"""
decision.rules — Rule-based decision functions for the hybrid engine.

These rules provide fast, deterministic decisions without LLM calls.
Each rule returns None if it cannot handle the case, or a decision dict if it can.

Rules are registered with HybridDecisionEngine and are tried before LLM calls.
"""

from .elderly_mobility import rule_elderly_mobility_risk
from .toddler_pacing import rule_toddler_pacing_risk
from .budget_feasibility import rule_budget_feasibility
from .visa_timeline import rule_visa_timeline_risk
from .composition_risk import rule_composition_risk
from .not_applicable import (
    rule_elderly_not_applicable,
    rule_toddler_not_applicable,
    rule_visa_not_applicable,
    rule_composition_not_applicable,
)

__all__ = [
    "rule_elderly_mobility_risk",
    "rule_toddler_pacing_risk",
    "rule_budget_feasibility",
    "rule_visa_timeline_risk",
    "rule_composition_risk",
    "rule_elderly_not_applicable",
    "rule_toddler_not_applicable",
    "rule_visa_not_applicable",
    "rule_composition_not_applicable",
    "register_all_rules",
]


def register_all_rules(engine) -> None:
    """
    Register all built-in rules with a HybridDecisionEngine.

    Not-applicable rules are registered first to handle negative cases
    before the main rules are tried.

    Args:
        engine: HybridDecisionEngine instance
    """
    # Register not-applicable rules (handle "no risk" cases)
    engine.register_rule("elderly_mobility_risk", rule_elderly_not_applicable)
    engine.register_rule("toddler_pacing_risk", rule_toddler_not_applicable)
    engine.register_rule("visa_timeline_risk", rule_visa_not_applicable)
    engine.register_rule("composition_risk", rule_composition_not_applicable)

    # Register main rules (handle actual risk assessments)
    engine.register_rule("elderly_mobility_risk", rule_elderly_mobility_risk)
    engine.register_rule("toddler_pacing_risk", rule_toddler_pacing_risk)
    engine.register_rule("budget_feasibility", rule_budget_feasibility)
    engine.register_rule("visa_timeline_risk", rule_visa_timeline_risk)
    engine.register_rule("composition_risk", rule_composition_risk)
