"""Fare-drop disposition ledger + options calculator — exploration topic 49 (2026-10-21).

HARD INVARIANT (owner constraint, identical to ``claim_disposition``): this system
NEVER initiates, holds, or receives money, and never contacts a supplier or a
traveler on its own. A fare drop on a booked trip is detected by
``TicketPriceWatchAgent`` (post-booking branch); this module records what the
advisor *decided* and what the supplier and client then did between
themselves. No payment processing, no gateways, no balances — ever. Guarded by
``tests/test_fare_drop_disposition.py::test_no_payment_code_paths``.

Why this exists: the practitioner playbook (r/travelagents, top thread of the
year) is "price dropped after booking → tell the client → offer a refund OR an
upgrade → absorb/offset the commission hit". Today that happens by accident and
by hand. The ledger makes the decision explicit and auditable; the options
calculator puts the two numbers in front of the advisor before they choose.

State machine (terminal state immutable):

    DETECTED  → PRESENTED | DISMISSED
    PRESENTED → REPRICED | UPGRADED | DEFERRED | DISMISSED
    DEFERRED  → PRESENTED | CLOSED          (a later observation re-presents it)
    REPRICED | UPGRADED | DISMISSED → CLOSED

``DEFERRED`` is deliberately not ``HELD``: the custody-sounding vocabulary
(ESCROW/FUNDS/HOLD/SETTLE) is forbidden by construction and asserted in tests.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from spine_api.services.commission_reconciliation import AGENCY_COMMISSION_RATE

# States describe the advisor's decision and its recorded outcome — never custody of funds.
FARE_DROP_DISPOSITION_STATES = (
    "DETECTED",
    "PRESENTED",
    "REPRICED",
    "UPGRADED",
    "DEFERRED",
    "DISMISSED",
    "CLOSED",
)

ALLOWED_TRANSITIONS: Dict[str, tuple] = {
    "DETECTED": ("PRESENTED", "DISMISSED"),
    "PRESENTED": ("REPRICED", "UPGRADED", "DEFERRED", "DISMISSED"),
    "DEFERRED": ("PRESENTED", "CLOSED"),
    "REPRICED": ("CLOSED",),
    "UPGRADED": ("CLOSED",),
    "DISMISSED": ("CLOSED",),
    "CLOSED": (),
}

TERMINAL_STATES = ("CLOSED",)

# Decision states that carry a recorded outcome (what the supplier and client did).
OUTCOME_STATES = ("REPRICED", "UPGRADED")

# Same forbidden list as claim_disposition — the vocabulary itself can never drift
# into implying funds handling.
_FORBIDDEN_STATE_SUBSTRINGS = ("ESCROW", "FUNDS", "HOLD", "SETTLE")

# Commission basis labels (FND-0268 provenance model: say where a number came from).
COMMISSION_BASIS_TRIP_RECORDED = "trip_recorded"
COMMISSION_BASIS_ESTIMATE = "estimate"


def transition_disposition(current: str, new: str) -> bool:
    """Return True iff ``current → new`` is a legal disposition transition."""
    if current not in ALLOWED_TRANSITIONS or new not in ALLOWED_TRANSITIONS:
        return False
    return new in ALLOWED_TRANSITIONS[current]


def is_terminal(state: str) -> bool:
    return state in TERMINAL_STATES


def new_disposition(
    detection_marker: str,
    initial_state: str = "DETECTED",
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Create a disposition record attached to a detected fare-drop signal."""
    if initial_state not in ALLOWED_TRANSITIONS:
        raise ValueError(f"unknown initial disposition state: {initial_state}")
    ts = (now or datetime.now(timezone.utc)).isoformat()
    return {
        "state": initial_state,
        "history": [{"state": initial_state, "at": ts, "by": "system", "note": "fare drop detected"}],
        "outcome": None,
        "detection_marker": detection_marker,
    }


def apply_transition(
    disposition: Dict[str, Any],
    new_state: str,
    by: str,
    note: str = "",
    outcome: Optional[Dict[str, Any]] = None,
    expected_state: Optional[str] = None,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Apply a validated transition; returns the updated disposition.

    Raises ValueError on illegal transitions or a failed ``expected_state``
    compare-and-set (router maps both to 409). ``outcome`` is plain recorded
    data — option chosen, client delta, supplier reference, who executed it —
    describing money that moved directly between supplier and client. The
    system itself moves nothing.
    """
    current = disposition.get("state")
    if expected_state is not None and current != expected_state:
        raise ValueError(f"disposition state changed: expected {expected_state}, found {current}")
    if is_terminal(current):
        raise ValueError(f"disposition is terminal ({current}); no further transitions")
    if not transition_disposition(current, new_state):
        raise ValueError(f"illegal transition: {current} → {new_state}")
    if new_state in OUTCOME_STATES and outcome is None:
        raise ValueError(f"{new_state} requires a recorded outcome (option, client_delta, executed_by)")
    ts = (now or datetime.now(timezone.utc)).isoformat()
    disposition["state"] = new_state
    disposition.setdefault("history", []).append({"state": new_state, "at": ts, "by": by, "note": note})
    if outcome is not None:
        disposition["outcome"] = {**outcome, "recorded_at": ts, "recorded_by": by}
    return disposition


def compute_fare_drop_options(
    booked_price: float,
    current_price: float,
    commission_pct: Optional[float] = None,
    commission_source: Optional[str] = None,
) -> Dict[str, Any]:
    """Quantify the two practitioner options for a detected drop.

    * **reprice** — the client is re-booked at the lower fare: the client saves
      the full drop; the agency's commission on that amount is gone.
    * **upgrade** — the client keeps the original spend and receives the drop as
      upgrade value (cabin, excursions, credits): commission is preserved on the
      recorded upgrade spend.

    ``commission_pct`` is a fraction (0.10 = 10%). When the trip carries a
    recorded commission the basis is ``trip_recorded``; otherwise the agency
    default rate is used and the result is labelled ``estimate`` so the card can
    badge it honestly (FND-0268 provenance rule). All figures are recorded
    arithmetic over two prices — nothing here touches a payment.
    """
    booked = float(booked_price)
    current = float(current_price)
    if booked <= 0 or current <= 0:
        raise ValueError("booked_price and current_price must be positive")
    if current >= booked:
        raise ValueError("no fare drop: current_price is not below booked_price")

    if commission_pct is None:
        pct = AGENCY_COMMISSION_RATE
        basis = COMMISSION_BASIS_ESTIMATE
        source = commission_source or "agency_default_rate"
    else:
        pct = float(commission_pct)
        if pct < 0 or pct > 1:
            raise ValueError("commission_pct must be a fraction between 0 and 1")
        basis = COMMISSION_BASIS_TRIP_RECORDED
        source = commission_source or "trip_contract"

    drop_amount = round(booked - current, 2)
    drop_percent = round((drop_amount / booked) * 100, 2)
    commission_loss = round(drop_amount * pct, 2)
    return {
        "booked_price": booked,
        "current_price": current,
        "drop_amount": drop_amount,
        "drop_percent": drop_percent,
        "reprice": {
            "client_saving": drop_amount,
            "commission_delta": -commission_loss,
        },
        "upgrade": {
            "upgrade_budget": drop_amount,
            "commission_delta": 0.0,
            "note": "commission preserved on recorded upgrade spend",
        },
        "commission": {"pct": pct, "basis": basis, "source": source},
        "basis": basis,
    }


def resolve_trip_commission(trip: Dict[str, Any]) -> tuple[Optional[float], Optional[str]]:
    """Find a recorded commission fraction on the trip, if any.

    Looks at the booking record first (what was actually contracted for this
    booking), then the fee record. Returns ``(None, None)`` when nothing is
    recorded so the caller falls back to the labelled estimate.
    """
    for container_key in ("booking_data", "fees"):
        container = trip.get(container_key)
        if not isinstance(container, dict):
            continue
        raw = container.get("commission_pct")
        if raw is None:
            continue
        try:
            value = float(raw)
        except (TypeError, ValueError):
            continue
        # Tolerate percentage-style storage (10 → 0.10) without guessing on ambiguous values.
        if value > 1:
            value = value / 100.0
        if 0 <= value <= 1:
            return value, f"{container_key}.commission_pct"
    return None, None


# Same label ghost_concierge uses for proposed-never-sent interventions: the
# operator reads, edits, and sends through their own channel. Nothing here
# dispatches anything.
DRAFT_STATUS = "DRAFT_AWAITING_OPERATOR"


def _format_amount(amount: float, currency: Optional[str]) -> str:
    rounded = int(round(amount)) if abs(amount - round(amount)) < 0.005 else round(amount, 2)
    text = f"{rounded:,}"
    return f"{currency} {text}" if currency else text


def compose_traveler_draft(
    signal: Dict[str, Any],
    options: Optional[Dict[str, Any]],
    traveler_name: Optional[str] = None,
    destination: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Draft the client message in the practitioner's consensus framing.

    "Great news, two ways to take advantage" — refund or upgrade. Uses only the
    verified drop amount; never mentions commission (internal), never invents a
    figure (no options → no draft). Returned with ``DRAFT_AWAITING_OPERATOR``;
    the advisor sends it through their own channel (E1 channel choice is a
    separate decision). This function never sends anything.
    """
    if not options:
        return None
    drop = options.get("drop_amount")
    if not isinstance(drop, (int, float)) or drop <= 0:
        return None
    currency = signal.get("booked_currency") or signal.get("current_currency")
    amount = _format_amount(float(drop), currency)
    greeting = f"Hi {traveler_name.strip()}," if traveler_name and traveler_name.strip() else "Hi,"
    where = f" to {destination}" if destination else ""
    body = (
        f"{greeting}\n\n"
        f"Great news — the fare for your trip{where} has come down by {amount} since you booked. "
        "There are two ways you can take advantage of it, and I'm happy to arrange either:\n\n"
        f"1. Refund the difference — you'd get {amount} back.\n"
        f"2. Put it towards an upgrade — the same {amount} as upgrade value (a better cabin, a nicer room, "
        "or an experience on the ground), with no extra outlay.\n\n"
        "Let me know which you'd prefer and I'll take care of it.\n"
    )
    return {
        "status": DRAFT_STATUS,
        "subject": "Good news about your trip fare",
        "body": body,
        "channel": "unsent",
        "based_on": {"drop_amount": float(drop), "currency": currency, "detection_marker": signal.get("detection_marker")},
    }
