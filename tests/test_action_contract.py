"""Focused tests for the derived decision-to-action contract."""

from src.intake.action_contract import (
    ActionAvailability,
    ActionType,
    derive_action_contract,
)


def test_traveler_safe_progress_projects_recommendation_without_side_effects():
    contract = derive_action_contract("PROCEED_TRAVELER_SAFE", "auto")

    assert contract.next_action is ActionType.RECOMMEND
    assert contract.availability is ActionAvailability.AVAILABLE
    assert contract.approval_required is False
    assert ActionType.COMMIT in contract.unavailable_actions
    assert ActionType.RESERVE in contract.unavailable_actions
    assert ActionType.COMMIT not in contract.allowed_actions


def test_followup_projects_message_but_keeps_dispatch_gated():
    contract = derive_action_contract("ASK_FOLLOWUP", "auto")

    assert contract.next_action is ActionType.MESSAGE
    assert contract.availability is ActionAvailability.APPROVAL_REQUIRED
    assert contract.approval_required is True
    assert any("dispatch" in reason for reason in contract.reasons)


def test_stop_state_cannot_be_widened_by_auto_policy():
    contract = derive_action_contract("STOP_NEEDS_REVIEW", "auto")

    assert contract.next_action is ActionType.ESCALATE
    assert contract.availability is ActionAvailability.APPROVAL_REQUIRED
    assert contract.allowed_actions == (ActionType.OBSERVE, ActionType.ESCALATE)
    assert ActionType.PROPOSE not in contract.allowed_actions


def test_missing_policy_is_conservative_and_serializable():
    contract = derive_action_contract("PROCEED_INTERNAL_DRAFT")
    payload = contract.to_dict()

    assert contract.policy_action == "unknown"
    assert contract.approval_required is True
    assert payload["next_action"] == "propose"
    assert payload["availability"] == "approval_required"
    assert isinstance(payload["allowed_actions"], list)
