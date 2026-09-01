"""Derived next-action contract for the NB02 -> NB03 planning boundary.

This module separates the action a plan proposes from the autonomy policy that
controls whether that action may proceed.  It is deliberately provider-neutral:
it can describe a future hold/reserve/commit action without claiming that a
provider, authorization, or external side effect exists.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Iterable, Optional, Tuple


class ActionType(str, Enum):
    """Canonical vocabulary for what the system may do next."""

    OBSERVE = "observe"
    SEARCH = "search"
    RECOMMEND = "recommend"
    PROPOSE = "propose"
    HOLD = "hold"
    RESERVE = "reserve"
    COMMIT = "commit"
    MESSAGE = "message"
    ESCALATE = "escalate"


class ActionAvailability(str, Enum):
    """Whether the projected action can be taken under current contracts."""

    AVAILABLE = "available"
    APPROVAL_REQUIRED = "approval_required"
    UNAVAILABLE = "unavailable"


_NEXT_ACTION_BY_DECISION: Dict[str, ActionType] = {
    "STOP_NEEDS_REVIEW": ActionType.ESCALATE,
    "ASK_FOLLOWUP": ActionType.MESSAGE,
    "BRANCH_OPTIONS": ActionType.RECOMMEND,
    "PROCEED_INTERNAL_DRAFT": ActionType.PROPOSE,
    "PROCEED_TRAVELER_SAFE": ActionType.RECOMMEND,
}

@dataclass(frozen=True, slots=True)
class ActionContract:
    """A conservative, serializable projection of the next permitted action."""

    next_action: ActionType
    availability: ActionAvailability
    approval_required: bool
    policy_action: str
    allowed_actions: Tuple[ActionType, ...]
    unavailable_actions: Tuple[ActionType, ...]
    reasons: Tuple[str, ...]

    def to_dict(self) -> Dict[str, Any]:
        """Return JSON-compatible values for internal plan serialization."""
        return {
            "next_action": self.next_action.value,
            "availability": self.availability.value,
            "approval_required": self.approval_required,
            "policy_action": self.policy_action,
            "allowed_actions": [action.value for action in self.allowed_actions],
            "unavailable_actions": [action.value for action in self.unavailable_actions],
            "reasons": list(self.reasons),
        }


def _unique(actions: Iterable[ActionType]) -> Tuple[ActionType, ...]:
    return tuple(dict.fromkeys(actions))


def derive_action_contract(
    decision_state: str,
    effective_action: Optional[str] = None,
) -> ActionContract:
    """Derive action vocabulary and permission from decision plus policy.

    ``effective_action`` is the D1 policy result (``auto``, ``review``, or
    ``block``).  When it is unavailable, the projection remains conservative
    and uses ``unknown`` rather than assuming automatic authority.
    """
    state = str(decision_state or "ASK_FOLLOWUP")
    policy = str(effective_action or "unknown")
    next_action = _NEXT_ACTION_BY_DECISION.get(state, ActionType.OBSERVE)

    if state == "STOP_NEEDS_REVIEW" or policy == "block":
        allowed = (ActionType.OBSERVE, ActionType.ESCALATE)
        availability = ActionAvailability.APPROVAL_REQUIRED
        approval_required = True
        reasons = ("Blocked decision state or autonomy policy permits observation and escalation only.",)
    else:
        allowed = _unique((ActionType.OBSERVE, ActionType.SEARCH, next_action))
        approval_required = policy != "auto" or next_action == ActionType.MESSAGE
        availability = (
            ActionAvailability.AVAILABLE
            if not approval_required
            else ActionAvailability.APPROVAL_REQUIRED
        )
        reasons = ()
        if policy == "unknown":
            reasons = ("Autonomy policy was not supplied; automatic side effects are not inferred.",)
        if next_action == ActionType.MESSAGE:
            reasons += ("Message dispatch remains approval-gated; this contract does not claim a send occurred.",)

    unavailable = tuple(action for action in ActionType if action not in allowed)
    return ActionContract(
        next_action=next_action,
        availability=availability,
        approval_required=approval_required,
        policy_action=policy,
        allowed_actions=allowed,
        unavailable_actions=unavailable,
        reasons=reasons,
    )
