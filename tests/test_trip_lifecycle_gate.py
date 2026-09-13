"""Canonical trip-lifecycle gate — council-ratified contract tests.

Ratified 2026-09-14 by the persona council (PER-0450 lead, PER-0444,
PER-0453, PER-0369, PER-0274); decision record: blueprint Addendum 8.

Contract under test:
- 12 enforced-eligible states + 2 dormant model extensions (returned/archived)
- demotions: needs_information/feasibility_check/needs_revision are
  conditions/stages, never states
- staged enforcement: the proven invariant RAISES, machine-illegal pairs
  among non-proven classes LOG (never raise), unknown strings pass through
- financial ruling: ready_to_book NEVER classifies to approved
"""

import pytest

from spine_api.core import trip_lifecycle as tl
from spine_api.core.trip_status import (
    IllegalTripStatusTransition,
    enforce_status_transition,
)


# --- Model shape ------------------------------------------------------------

def test_twelve_enforced_eligible_states():
    assert tl.SPINE_STATES == {
        "intake", "planning", "awaiting_customer_approval", "approved",
        "booking_in_progress", "booked", "change_requested", "in_trip",
        "completed", "cancelled", "lost", "escalated",
    }


def test_demoted_states_are_not_states():
    for demoted in ("needs_information", "feasibility_check", "needs_revision"):
        assert demoted not in tl.SPINE_STATES
        assert demoted not in tl.DORMANT_MODEL_STATES


def test_returned_archived_dormant_in_model_not_enforced_set():
    assert tl.DORMANT_MODEL_STATES == {"returned", "archived"}
    assert not (tl.DORMANT_MODEL_STATES & tl.SPINE_STATES)


def test_cancelled_terminal_and_distinct_from_lost():
    assert "cancelled" in tl.SPINE_STATES
    assert "cancelled" in tl.TERMINAL_STATES
    assert "lost" in tl.TERMINAL_STATES


# --- Transition table -------------------------------------------------------

def test_spine_happy_path_is_legal():
    path = [
        "intake", "planning", "awaiting_customer_approval", "approved",
        "booking_in_progress", "booked", "in_trip", "completed",
    ]
    for old, new in zip(path, path[1:]):
        assert new in tl.legal_targets(old), f"{old} -> {new} must be legal"
        assert tl.assess_transition(old, new).verdict == "allow"


def test_change_requested_only_from_booked():
    assert "change_requested" in tl.legal_targets("booked")
    # escalated is exempt: its exits are operator-dynamic by ratified
    # semantics (any non-terminal return state, audited).
    for state in tl.SPINE_STATES - {"booked", "change_requested", "escalated"}:
        assert "change_requested" not in tl.legal_targets(state), state


def test_booked_cancellation_is_not_lost():
    assert "cancelled" in tl.legal_targets("booked")
    assert "lost" not in tl.legal_targets("booked")


def test_terminal_states_have_no_outgoing_edges():
    for state in ("completed", "cancelled", "lost"):
        assert tl.legal_targets(state) == set()


def test_escalated_exits_are_operator_dynamic():
    targets = tl.legal_targets("escalated")
    assert "planning" in targets
    assert "booked" in targets
    assert not (targets & tl.TERMINAL_STATES)
    assert "escalated" not in targets


def test_intake_blocked_to_quote_capable_one_hop_raises():
    # The one proven invariant, restated canonically — RAISE class.
    for blocked in ("incomplete", "needs_followup", "needs_clarification",
                    "awaiting_customer_details"):
        for capable in ("ready_to_quote", "quote_ready", "ready_to_book"):
            with pytest.raises(IllegalTripStatusTransition):
                enforce_status_transition(blocked, capable)


# --- Staged enforcement -----------------------------------------------------

def test_machine_illegal_pair_logs_and_never_raises():
    assessment = tl.assess_transition("new", "completed")  # intake -> completed
    assert assessment.verdict == "log"
    # and it genuinely does not raise:
    enforce_status_transition("new", "completed")


def test_unknown_strings_pass_through_as_allow():
    assessment = tl.assess_transition("weird_legacy_value", "in_trip")
    assert assessment.verdict == "allow"
    assert assessment.old_state is None  # unknown side never invents a position


def test_same_status_is_allow():
    assert tl.assess_transition("planning", "planning").verdict == "allow"


# --- Mapping rulings --------------------------------------------------------

def test_ready_to_book_never_maps_to_approved():
    # PER-0453 priority hazard: readiness is not authorization.
    c = tl.classify("ready_to_book")
    assert c is not None and c.state == "planning"
    assert c.state != "approved"


def test_escalated_maps_to_exception_state():
    assert tl.classify("escalated").state == "escalated"


def test_input_deficit_strings_carry_needs_information_condition():
    for raw in ("incomplete", "needs_clarification", "awaiting_customer_details"):
        c = tl.classify(raw)
        assert c.state == "planning"
        assert c.condition == "needs_information"


def test_unknown_string_classifies_to_none():
    assert tl.classify("totally_made_up") is None
    assert tl.classify(None) is None


def test_audit_gated_ambiguous_mappings_flagged():
    assert tl.classify("in_progress").audit_gated is True
    assert tl.classify("active").audit_gated is True
    assert tl.classify("new").audit_gated is False
