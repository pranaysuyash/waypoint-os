"""Claim disposition ledger tests — T10 tranche (FND-0233, decided 2026-09-30).

The first test is the owner's hard invariant: this system never initiates,
holds, or receives money. Everything else is state-machine correctness.
"""

import pathlib

import pytest

from spine_api.services import claim_disposition as cd


# ---------------------------------------------------------------------------
# THE INVARIANT: no money movement, ever (owner constraint, 2026-09-30)
# ---------------------------------------------------------------------------

_PAYMENT_FORBIDDEN_PATTERNS = (
    "stripe",
    "paypal",
    "razorpay",
    "adyen",
    "squareup",
    "braintree",
    "checkout.com",
    "payment_intent",
    "PaymentIntent",
    "charge(",
    "create_charge",
    "payout",
    "bank_account",
    "iban",
    "card_number",
    "wallet_balance",
    "transfer_funds",
    "initiate_refund",
    "process_payment",
)


def test_no_payment_code_paths():
    """THE money-boundary invariant (owner hard constraint).

    The disposition lane must never import or invoke any payment processing,
    gateway, instrument, or funds-movement capability. Scans every module in
    the lane (service + router) for payment-vendor names and money-movement
    API shapes. This test is deliberately paranoid: if it ever fails, someone
    is about to turn a scorecard into a bank.
    """
    lane_files = [
        pathlib.Path("spine_api/services/claim_disposition.py"),
        pathlib.Path("spine_api/routers/passenger_rights.py"),
        pathlib.Path("spine_api/services/passenger_rights_claims.py"),
    ]
    for path in lane_files:
        assert path.exists(), f"invariant scope file missing: {path}"
        source = path.read_text().lower()
        for pattern in _PAYMENT_FORBIDDEN_PATTERNS:
            assert pattern.lower() not in source, (
                f"MONEY-BOUNDARY VIOLATION in {path}: found {pattern!r}. "
                f"The disposition ledger records outcomes of airline→traveler "
                f"payments; it never initiates, holds, or receives money."
            )


def test_disposition_states_never_imply_custody():
    """The state vocabulary itself must never suggest the system holds funds."""
    for state in cd.CLAIM_DISPOSITION_STATES:
        upper = state.upper()
        for forbidden in cd._FORBIDDEN_STATE_SUBSTRINGS:
            assert forbidden not in upper, (
                f"disposition state {state!r} implies funds custody (contains "
                f"{forbidden!r}) — vocabulary must describe outcomes, not holdings"
            )


# ---------------------------------------------------------------------------
# State machine correctness
# ---------------------------------------------------------------------------


def test_happy_path_to_closed():
    d = cd.new_disposition("claim_x")
    assert d["state"] == "DRAFTED"
    cd.apply_transition(d, "SUBMITTED", by="op1", note="letter sent")
    cd.apply_transition(d, "AIRLINE_ACCEPTED", by="op1", note="airline email")
    cd.apply_transition(
        d,
        "TRAVELER_PAID",
        by="op1",
        note="traveler confirmed bank receipt",
        outcome={"amount_eur": 400.0, "channel": "bank_transfer", "date": "2026-09-30"},
    )
    cd.apply_transition(d, "CLOSED", by="op1")
    assert cd.is_terminal(d["state"])
    # Full audit history preserved
    assert [h["state"] for h in d["history"]] == [
        "DRAFTED", "SUBMITTED", "AIRLINE_ACCEPTED", "TRAVELER_PAID", "CLOSED",
    ]


def test_rejected_goes_straight_to_closed():
    d = cd.new_disposition("claim_y")
    cd.apply_transition(d, "SUBMITTED", by="op1")
    cd.apply_transition(d, "AIRLINE_REJECTED", by="op1")
    cd.apply_transition(d, "CLOSED", by="op1")
    assert d["state"] == "CLOSED"


def test_illegal_transition_rejected():
    d = cd.new_disposition("claim_z")
    # DRAFTED → TRAVELER_PAID skips reality (nothing was even submitted)
    with pytest.raises(ValueError, match="illegal transition"):
        cd.apply_transition(d, "TRAVELER_PAID", by="op1")
    # State unchanged after the failed attempt
    assert d["state"] == "DRAFTED"
    assert len(d["history"]) == 1


def test_terminal_is_frozen():
    d = cd.new_disposition("claim_t")
    cd.apply_transition(d, "SUBMITTED", by="op1")
    cd.apply_transition(d, "AIRLINE_REJECTED", by="op1")
    cd.apply_transition(d, "CLOSED", by="op1")
    with pytest.raises(ValueError, match="terminal"):
        cd.apply_transition(d, "SUBMITTED", by="op1")


def test_escalation_path():
    d = cd.new_disposition("claim_e")
    cd.apply_transition(d, "SUBMITTED", by="op1")
    cd.apply_transition(d, "ESCALATED", by="op1", note="no reply in 30 days")
    cd.apply_transition(d, "AIRLINE_PARTIAL", by="op1")
    cd.apply_transition(d, "TRAVELER_PAID", by="op1", outcome={"amount_eur": 250.0})
    cd.apply_transition(d, "CLOSED", by="op1")
    assert d["state"] == "CLOSED"


def test_unknown_state_rejected():
    assert cd.transition_disposition("DRAFTED", "MONEY_HELD") is False
    assert cd.transition_disposition("NONEXISTENT", "SUBMITTED") is False


def test_compute_overdue_window():
    from datetime import datetime, timezone, timedelta

    now = datetime(2026, 9, 30, tzinfo=timezone.utc)
    fresh = (now - timedelta(days=5)).isoformat()
    stale = (now - timedelta(days=45)).isoformat()
    assert cd.compute_overdue(fresh, now=now) is False
    assert cd.compute_overdue(stale, now=now) is True
    assert cd.compute_overdue(None, now=now) is False
    assert cd.compute_overdue("garbage", now=now) is False


def test_new_disposition_rejects_unknown_initial_state():
    with pytest.raises(ValueError, match="unknown initial"):
        cd.new_disposition("claim_bad", initial_state="TELEPORTED")


# ---------------------------------------------------------------------------
# S3 mutation-sensitivity spot check: the router wiring must actually use
# this module (if the lane stops importing the ledger, the invariant scan
# and endpoint tests below would be guarding nothing).
# ---------------------------------------------------------------------------


def test_router_wires_the_disposition_module():
    router_src = pathlib.Path("spine_api/routers/passenger_rights.py").read_text()
    assert "claim_disposition" in router_src, (
        "passenger_rights router no longer uses the disposition ledger — "
        "the tranche has been unwired or bypassed"
    )
    assert "disposition" in router_src.lower()
