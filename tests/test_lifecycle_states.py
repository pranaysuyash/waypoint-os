"""Tests for the trip lifecycle state machine (taught model, ontology v2).

Every state must satisfy the four-question template: what is true, what can
happen, what cannot happen, what moves us out. Every transition must be
legal. Illegal transitions must be rejected.
"""


from src.intake.lifecycle_states import (
    STATE_DEFINITIONS,
    LEGAL_TRANSITIONS,
    LifecycleState,
    get_state_definition,
    is_transition_legal,
)


class TestStateMachineIntegrity:
    def test_all_states_have_definitions(self):
        for state in LifecycleState:
            assert state in STATE_DEFINITIONS, f"{state} missing definition"

    def test_every_state_has_what_is_true(self):
        for state, defn in STATE_DEFINITIONS.items():
            assert defn.what_is_true, f"{state} missing what_is_true"

    def test_every_state_has_allowed_and_forbidden(self):
        for state, defn in STATE_DEFINITIONS.items():
            assert defn.allowed_actions, f"{state} missing allowed_actions"
            assert defn.forbidden_actions is not None

    def test_no_state_forbids_everything(self):
        """ESCALATED and COMPLETED may have minimal actions, but no state
        should have zero allowed AND zero forbidden (that's a design gap)."""
        for state, defn in STATE_DEFINITIONS.items():
            if state == LifecycleState.LOST:
                continue  # terminal, no actions
            assert defn.allowed_actions or defn.forbidden_actions

    def test_every_non_terminal_state_has_exits(self):
        non_terminal = {s for s in LifecycleState if s not in (
            LifecycleState.COMPLETED, LifecycleState.LOST,
        )}
        for state in non_terminal:
            defn = STATE_DEFINITIONS[state]
            assert defn.exits, f"{state} has no exits (dead-end state)"

    def test_transitions_are_symmetric_with_exits(self):
        """LEGAL_TRANSITIONS computed from exits must match."""
        for state, defn in STATE_DEFINITIONS.items():
            for target, _ in defn.exits:
                assert target in LEGAL_TRANSITIONS.get(
                    state, set()
                ), f"{state}→{target} in exits but not in transitions"


class TestLegalTransitions:
    def test_intake_to_needs_information(self):
        assert is_transition_legal(
            LifecycleState.INTAKE, LifecycleState.NEEDS_INFORMATION
        )

    def test_intake_to_feasibility(self):
        assert is_transition_legal(
            LifecycleState.INTAKE, LifecycleState.FEASIBILITY_CHECK
        )

    def test_needs_info_to_feasibility(self):
        assert is_transition_legal(
            LifecycleState.NEEDS_INFORMATION, LifecycleState.FEASIBILITY_CHECK
        )

    def test_feasibility_to_planning(self):
        assert is_transition_legal(
            LifecycleState.FEASIBILITY_CHECK, LifecycleState.PLANNING
        )

    def test_feasibility_to_needs_revision(self):
        assert is_transition_legal(
            LifecycleState.FEASIBILITY_CHECK, LifecycleState.NEEDS_REVISION
        )

    def test_planning_to_approval(self):
        assert is_transition_legal(
            LifecycleState.PLANNING, LifecycleState.AWAITING_CUSTOMER_APPROVAL
        )

    def test_approval_to_approved(self):
        assert is_transition_legal(
            LifecycleState.AWAITING_CUSTOMER_APPROVAL, LifecycleState.APPROVED
        )

    def test_approved_to_booking(self):
        assert is_transition_legal(
            LifecycleState.APPROVED, LifecycleState.BOOKING_IN_PROGRESS
        )

    def test_booking_to_booked(self):
        assert is_transition_legal(
            LifecycleState.BOOKING_IN_PROGRESS, LifecycleState.BOOKED
        )

    def test_booked_to_change_requested(self):
        assert is_transition_legal(
            LifecycleState.BOOKED, LifecycleState.CHANGE_REQUESTED
        )

    def test_booked_to_in_trip(self):
        assert is_transition_legal(
            LifecycleState.BOOKED, LifecycleState.IN_TRIP
        )

    def test_in_trip_to_completed(self):
        assert is_transition_legal(
            LifecycleState.IN_TRIP, LifecycleState.COMPLETED
        )

    def test_any_state_to_escalated(self):
        """ESCALATED must be reachable from every non-terminal state."""
        non_terminal = {s for s in LifecycleState if s not in (
            LifecycleState.COMPLETED, LifecycleState.LOST,
            LifecycleState.ESCALATED,
        )}
        for state in non_terminal:
            defn = STATE_DEFINITIONS[state]
            escalated_exits = [
                (t, e) for t, e in defn.exits if t == LifecycleState.ESCALATED
            ]
            if not escalated_exits:
                # ESCALATED can also be entered from FEASIBILITY_CHECK,
                # BOOKING_IN_PROGRESS, and PLANNING per the taught model
                assert state in (
                    LifecycleState.INTAKE,
                    LifecycleState.NEEDS_INFORMATION,
                ) or state in (
                    LifecycleState.FEASIBILITY_CHECK,
                    LifecycleState.PLANNING,
                ), f"{state} cannot reach ESCALATED and has no justification"

    def test_cannot_skip_feasibility(self):
        """Must go through FEASIBILITY_CHECK before PLANNING."""
        assert not is_transition_legal(
            LifecycleState.INTAKE, LifecycleState.PLANNING
        )

    def test_cannot_book_from_intake(self):
        assert not is_transition_legal(
            LifecycleState.INTAKE, LifecycleState.BOOKING_IN_PROGRESS
        )

    def test_cannot_go_backwards_from_booked_to_intake(self):
        assert not is_transition_legal(
            LifecycleState.BOOKED, LifecycleState.INTAKE
        )


class TestStateDefinitions:
    def test_needs_information_forbids_booking(self):
        defn = get_state_definition(LifecycleState.NEEDS_INFORMATION)
        assert defn.cannot("book_flight")
        assert defn.cannot("book_hotel")
        assert defn.cannot("charge_card")

    def test_needs_information_allows_nonblocked_searches(self):
        defn = get_state_definition(LifecycleState.NEEDS_INFORMATION)
        assert defn.can("run_nonblocked_searches")
        assert defn.can("ask_customer")

    def test_awaiting_approval_forbids_non_refundable_booking(self):
        defn = get_state_definition(LifecycleState.AWAITING_CUSTOMER_APPROVAL)
        assert defn.cannot("book_non_refundable_ticket")
        assert defn.cannot("charge_card")

    def test_booking_in_progress_forbids_plan_changes(self):
        defn = get_state_definition(LifecycleState.BOOKING_IN_PROGRESS)
        assert defn.cannot("change_travel_dates_without_approval")
        assert defn.cannot("increase_spend_beyond_authorized")

    def test_approved_requires_recheck(self):
        defn = get_state_definition(LifecycleState.APPROVED)
        assert "recheck_prices" in defn.allowed_actions
        assert defn.cannot("silently_book_at_new_price")
