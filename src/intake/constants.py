"""
intake.constants — Canonical type definitions shared across NB01-NB03.

All modules that reference decision_state must import from here.
No local redefinitions of DECISION_STATES permitted.
"""

from __future__ import annotations

from typing import Literal, cast

DecisionState = Literal[
    "ASK_FOLLOWUP",
    "PROCEED_INTERNAL_DRAFT",
    "PROCEED_TRAVELER_SAFE",
    "BRANCH_OPTIONS",
    "STOP_NEEDS_REVIEW",
]

DECISION_STATES: tuple[str, ...] = (
    "ASK_FOLLOWUP",
    "PROCEED_INTERNAL_DRAFT",
    "PROCEED_TRAVELER_SAFE",
    "BRANCH_OPTIONS",
    "STOP_NEEDS_REVIEW",
)

DECISION_STATES_FROZENSET = frozenset(DECISION_STATES)


def assert_valid_decision_state(value: str) -> DecisionState:
    if value not in DECISION_STATES_FROZENSET:
        raise ValueError(
            f"Invalid decision_state={value!r}. Expected one of {DECISION_STATES}"
        )
    return cast(DecisionState, value)
