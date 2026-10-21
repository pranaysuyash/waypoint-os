"""Claim disposition ledger — T10 tranche (FND-0233, decided 2026-09-30).

HARD INVARIANT (owner constraint): this system NEVER initiates, holds, or
receives money. The disposition ledger records the outcomes of money that
moved directly between the airline and the traveler (EU261: the airline pays
the passenger, not the agency). No payment processing, no gateways, no
payment instruments, no balances — ever. Guarded by
``tests/test_claim_disposition.py::test_no_payment_code_paths``.

State machine (terminal states immutable):

    DRAFTED → SUBMITTED → AIRLINE_ACCEPTED | AIRLINE_PARTIAL | AIRLINE_REJECTED | ESCALATED
    ESCALATED → AIRLINE_ACCEPTED | AIRLINE_PARTIAL | AIRLINE_REJECTED
    AIRLINE_ACCEPTED | AIRLINE_PARTIAL → TRAVELER_PAID → CLOSED
    AIRLINE_REJECTED → CLOSED
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional

# States describe *outcomes and progress*, never custody of funds.
CLAIM_DISPOSITION_STATES = (
    "DRAFTED",
    "SUBMITTED",
    "ESCALATED",
    "AIRLINE_ACCEPTED",
    "AIRLINE_PARTIAL",
    "AIRLINE_REJECTED",
    "TRAVELER_PAID",
    "CLOSED",
)

ALLOWED_TRANSITIONS: Dict[str, tuple] = {
    "DRAFTED": ("SUBMITTED",),
    "SUBMITTED": ("AIRLINE_ACCEPTED", "AIRLINE_PARTIAL", "AIRLINE_REJECTED", "ESCALATED"),
    "ESCALATED": ("AIRLINE_ACCEPTED", "AIRLINE_PARTIAL", "AIRLINE_REJECTED"),
    "AIRLINE_ACCEPTED": ("TRAVELER_PAID",),
    "AIRLINE_PARTIAL": ("TRAVELER_PAID",),
    "AIRLINE_REJECTED": ("CLOSED",),
    "TRAVELER_PAID": ("CLOSED",),
    "CLOSED": (),
}

TERMINAL_STATES = ("CLOSED",)

# Operator-follow-up threshold: an airline that hasn't replied within this
# window floats the claim to the top of the operator's list. Pure read-time
# computation — no background jobs.
AIRLINE_RESPONSE_WINDOW_DAYS = 30

# Custody-sounding states are forbidden by construction; asserted in tests so
# the vocabulary itself can never drift into implying funds handling.
_FORBIDDEN_STATE_SUBSTRINGS = ("ESCROW", "FUNDS", "HOLD", "SETTLE")


def transition_disposition(current: str, new: str) -> bool:
    """Return True iff ``current → new`` is a legal disposition transition."""
    if current not in ALLOWED_TRANSITIONS or new not in ALLOWED_TRANSITIONS:
        return False
    return new in ALLOWED_TRANSITIONS[current]


def is_terminal(state: str) -> bool:
    return state in TERMINAL_STATES


def compute_overdue(submitted_at_iso: Optional[str], now: Optional[datetime] = None) -> bool:
    """True when the airline has had the claim longer than the response window."""
    if not submitted_at_iso:
        return False
    try:
        submitted = datetime.fromisoformat(str(submitted_at_iso))
    except ValueError:
        return False
    if submitted.tzinfo is None:
        submitted = submitted.replace(tzinfo=timezone.utc)
    now = now or datetime.now(timezone.utc)
    return (now - submitted).days > AIRLINE_RESPONSE_WINDOW_DAYS


def new_disposition(
    claim_id: str,
    initial_state: str = "DRAFTED",
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Create a disposition record attached to a generated claim."""
    if initial_state not in ALLOWED_TRANSITIONS:
        raise ValueError(f"unknown initial disposition state: {initial_state}")
    ts = (now or datetime.now(timezone.utc)).isoformat()
    return {
        "state": initial_state,
        "history": [{"state": initial_state, "at": ts, "by": "system", "note": "claim generated"}],
        "outcome": None,
        "overdue": False,
        "claim_id": claim_id,
    }


def apply_transition(
    disposition: Dict[str, Any],
    new_state: str,
    by: str,
    note: str = "",
    outcome: Optional[Dict[str, Any]] = None,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Apply a validated transition; returns the updated disposition.

    Raises ValueError on illegal transitions (router maps to 409). ``outcome``
    is plain recorded data (amount, channel, date) describing money that moved
    directly between airline and traveler — the system itself moves nothing.
    """
    current = disposition.get("state")
    if is_terminal(current):
        raise ValueError(f"disposition is terminal ({current}); no further transitions")
    if not transition_disposition(current, new_state):
        raise ValueError(f"illegal transition: {current} → {new_state}")
    ts = (now or datetime.now(timezone.utc)).isoformat()
    disposition["state"] = new_state
    disposition["history"].append({"state": new_state, "at": ts, "by": by, "note": note})
    if outcome is not None:
        disposition["outcome"] = outcome
    return disposition
