"""Trip lifecycle state machine — the single source of truth for trip states.

Ontology foundation: INTAKE_ONTOLOGY_STATES_EVENTS_ACTIONS_2026-09-13.md.
Reconciled with the taught lifecycle model (Pranay's systems-training
sessions) in LIFECYCLE_RECONCILIATION_TO1_2026-09-14.md.

A state is where the trip currently is. An event is something that happened.
A transition is an event moving the trip from one state to another.

For any state, four things:
  What is true?       (state.invariants)
  What can happen?    (state.allowed_actions)
  What cannot happen? (state.forbidden_actions)
  What moves us out?  (transitions where `from` = this state)
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, FrozenSet, List, Set, Tuple


class LifecycleState(str, Enum):
    """Canonical trip lifecycle states (taught model, reconciled)."""

    INTAKE = "intake"
    NEEDS_INFORMATION = "needs_information"
    FEASIBILITY_CHECK = "feasibility_check"
    NEEDS_REVISION = "needs_revision"
    PLANNING = "planning"
    AWAITING_CUSTOMER_APPROVAL = "awaiting_customer_approval"
    APPROVED = "approved"
    BOOKING_IN_PROGRESS = "booking_in_progress"
    BOOKED = "booked"
    CHANGE_REQUESTED = "change_requested"
    IN_TRIP = "in_trip"
    COMPLETED = "completed"
    ESCALATED = "escalated"
    LOST = "lost"


@dataclass(frozen=True)
class StateDefinition:
    """The four-question template for a lifecycle state."""

    state: LifecycleState
    what_is_true: str
    allowed_actions: FrozenSet[str]
    forbidden_actions: FrozenSet[str]
    exits: FrozenSet[Tuple["LifecycleState", str]]  # (target, event)

    def can(self, action: str) -> bool:
        return action in self.allowed_actions

    def cannot(self, action: str) -> bool:
        return action in self.forbidden_actions


# ——— State definitions ———

STATE_DEFINITIONS: Dict[LifecycleState, StateDefinition] = {
    LifecycleState.INTAKE: StateDefinition(
        state=LifecycleState.INTAKE,
        what_is_true="Customer contacted us; structured trip brief not yet reliable.",
        allowed_actions=frozenset({
            "receive_message", "classify_source", "ocr", "transcribe",
            "fetch_url", "extract", "normalize", "merge_into_state",
            "detect_missing", "run_nonblocked_searches",
        }),
        forbidden_actions=frozenset({"book_flight", "book_hotel", "charge_card", "generate_itinerary"}),
        exits=frozenset({
            (LifecycleState.NEEDS_INFORMATION, "blocking_gaps_detected"),
            (LifecycleState.FEASIBILITY_CHECK, "enough_data"),
            (LifecycleState.ESCALATED, "processing_problem"),
        }),
    ),
    LifecycleState.NEEDS_INFORMATION: StateDefinition(
        state=LifecycleState.NEEDS_INFORMATION,
        what_is_true="Trip understood well enough to continue eventually, but required information is missing for the next intended step.",
        allowed_actions=frozenset({
            "ask_customer", "receive_response", "send_reminder",
            "parse_new_message", "update_trip_state",
            "operator_add_information", "recalculate_deadlines",
            "run_nonblocked_searches",
        }),
        forbidden_actions=frozenset({
            "book_flight", "book_hotel", "charge_card",
            "generate_itinerary", "submit_visa",
        }),
        exits=frozenset({
            (LifecycleState.FEASIBILITY_CHECK, "blockers_resolved"),
            (LifecycleState.LOST, "customer_stopped_responding"),
            (LifecycleState.ESCALATED, "contradictory_information"),
        }),
    ),
    LifecycleState.FEASIBILITY_CHECK: StateDefinition(
        state=LifecycleState.FEASIBILITY_CHECK,
        what_is_true="Checking whether the trip can plausibly work (entry, visa, budget, dates, availability).",
        allowed_actions=frozenset({
            "check_entry_requirements", "check_visa_lead_time",
            "rough_flight_feasibility", "rough_hotel_feasibility",
            "check_major_date_constraints", "check_availability",
        }),
        forbidden_actions=frozenset({"book_flight", "book_hotel", "charge_card"}),
        exits=frozenset({
            (LifecycleState.PLANNING, "feasible"),
            (LifecycleState.NEEDS_REVISION, "not_feasible_recoverable"),
            (LifecycleState.ESCALATED, "fundamentally_infeasible"),
        }),
    ),
    LifecycleState.NEEDS_REVISION: StateDefinition(
        state=LifecycleState.NEEDS_REVISION,
        what_is_true="The current plan is infeasible, but the customer goal may still be achievable with different parameters.",
        allowed_actions=frozenset({
            "propose_alternative_dates", "propose_alternative_destinations",
            "ask_customer", "recalculate",
        }),
        forbidden_actions=frozenset({"book_flight", "book_hotel", "charge_card"}),
        exits=frozenset({
            (LifecycleState.FEASIBILITY_CHECK, "revision_submitted"),
            (LifecycleState.LOST, "customer_declined_alternatives"),
            (LifecycleState.ESCALATED, "revision_requires_specialist"),
        }),
    ),
    LifecycleState.PLANNING: StateDefinition(
        state=LifecycleState.PLANNING,
        what_is_true="Trip is feasible; optimizing flight options, sequencing, hotels, activities, budget allocation.",
        allowed_actions=frozenset({
            "search_flights", "search_hotels", "search_activities",
            "optimize_route", "allocate_budget", "generate_itinerary_options",
        }),
        forbidden_actions=frozenset({"book_flight", "book_hotel", "charge_card"}),
        exits=frozenset({
            (LifecycleState.AWAITING_CUSTOMER_APPROVAL, "proposal_ready"),
            (LifecycleState.NEEDS_INFORMATION, "new_gap_detected"),
            (LifecycleState.ESCALATED, "planning_deadlock"),
        }),
    ),
    LifecycleState.AWAITING_CUSTOMER_APPROVAL: StateDefinition(
        state=LifecycleState.AWAITING_CUSTOMER_APPROVAL,
        what_is_true="A specific proposal has been sent to the customer; awaiting accept/reject/modify.",
        allowed_actions=frozenset({
            "send_reminder", "receive_response", "answer_questions",
            "operator_discusses_options",
        }),
        forbidden_actions=frozenset({
            "charge_card", "book_non_refundable_ticket",
            "book_flight", "book_hotel", "change_itinerary",
        }),
        exits=frozenset({
            (LifecycleState.APPROVED, "customer_accepted"),
            (LifecycleState.PLANNING, "customer_rejected"),
            (LifecycleState.NEEDS_REVISION, "customer_changed_constraints"),
            (LifecycleState.LOST, "customer_stopped_responding"),
            (LifecycleState.ESCALATED, "customer_dispute"),
        }),
    ),
    LifecycleState.APPROVED: StateDefinition(
        state=LifecycleState.APPROVED,
        what_is_true="Customer approved a specific plan; prices/inventory must be rechecked before booking.",
        allowed_actions=frozenset({
            "recheck_prices", "recheck_inventory", "recheck_rules",
            "proceed_to_booking", "return_to_customer_with_update",
        }),
        forbidden_actions=frozenset({
            "silently_book_at_new_price", "skip_recheck",
        }),
        exits=frozenset({
            (LifecycleState.BOOKING_IN_PROGRESS, "recheck_passed"),
            (LifecycleState.AWAITING_CUSTOMER_APPROVAL, "material_change_detected"),
            (LifecycleState.ESCALATED, "recheck_reveals_infeasibility"),
        }),
    ),
    LifecycleState.BOOKING_IN_PROGRESS: StateDefinition(
        state=LifecycleState.BOOKING_IN_PROGRESS,
        what_is_true="Irreversible or externally visible booking actions are underway.",
        allowed_actions=frozenset({
            "book_flight", "book_hotel", "reserve_transfer",
            "purchase_attraction", "submit_payment",
            "verify_confirmation", "record_booking_reference",
            "retry_safe_operation",
        }),
        forbidden_actions=frozenset({
            "change_travel_dates_without_approval",
            "switch_hotel_because_ai_prefers",
            "increase_spend_beyond_authorized",
            "add_traveler", "change_flight_class",
            "retry_uncertain_payment_blindly",
        }),
        exits=frozenset({
            (LifecycleState.BOOKED, "all_components_confirmed"),
            (LifecycleState.ESCALATED, "booking_exception"),
        }),
    ),
    LifecycleState.BOOKED: StateDefinition(
        state=LifecycleState.BOOKED,
        what_is_true="All required bookings confirmed; trip management mode active.",
        allowed_actions=frozenset({
            "monitor_changes", "send_documents", "remind_visa",
            "remind_checkin", "surface_disruptions", "handle_changes",
        }),
        forbidden_actions=frozenset({"run_planning_agent", "requote"}),
        exits=frozenset({
            (LifecycleState.CHANGE_REQUESTED, "customer_requested_change"),
            (LifecycleState.IN_TRIP, "travel_started"),
            (LifecycleState.ESCALATED, "booking_dispute"),
        }),
    ),
    LifecycleState.CHANGE_REQUESTED: StateDefinition(
        state=LifecycleState.CHANGE_REQUESTED,
        what_is_true="Customer requested a post-booking change; calculating affected bookings, penalties, and dependencies.",
        allowed_actions=frozenset({
            "calculate_penalties", "calculate_price_differences",
            "identify_affected_bookings", "propose_change_options",
        }),
        forbidden_actions=frozenset({
            "mutate_original_booking_invisibly", "cancel_without_approval",
        }),
        exits=frozenset({
            (LifecycleState.PLANNING, "change_requires_replanning"),
            (LifecycleState.BOOKED, "change_rejected_or_not_needed"),
            (LifecycleState.ESCALATED, "penalty_dispute"),
        }),
    ),
    LifecycleState.IN_TRIP: StateDefinition(
        state=LifecycleState.IN_TRIP,
        what_is_true="Travel has started; trip-management and emergency-assistance mode.",
        allowed_actions=frozenset({
            "monitor_flight_delays", "assist_missed_connection",
            "handle_hotel_issue", "emergency_assistance",
        }),
        forbidden_actions=frozenset({"run_planning_agent", "requote"}),
        exits=frozenset({
            (LifecycleState.COMPLETED, "trip_ended"),
            (LifecycleState.ESCALATED, "emergency"),
        }),
    ),
    LifecycleState.COMPLETED: StateDefinition(
        state=LifecycleState.COMPLETED,
        what_is_true="Trip is over; collecting feedback, resolving claims, extracting preferences.",
        allowed_actions=frozenset({
            "collect_feedback", "record_outcomes", "resolve_claims",
            "extract_preferences", "close_tasks", "update_customer_memory",
        }),
        forbidden_actions=frozenset(set()),
        exits=frozenset(set()),
    ),
    LifecycleState.ESCALATED: StateDefinition(
        state=LifecycleState.ESCALATED,
        what_is_true="Human operator has taken control; the system is paused for this trip.",
        allowed_actions=frozenset({
            "operator_review", "operator_resolve", "return_to_state",
        }),
        forbidden_actions=frozenset({"resume_automated_pipeline"}),
        # Exits are operator-dynamic (return to any prior state), not
        # declared statically — the operator chooses the return state.
        exits=frozenset({(LifecycleState.PLANNING, "operator_resolved")}),
    ),
    LifecycleState.LOST: StateDefinition(
        state=LifecycleState.LOST,
        what_is_true="Customer stopped responding or explicitly declined; lead is closed.",
        allowed_actions=frozenset({"record_outcome"}),
        forbidden_actions=frozenset({"contact_customer", "requote", "book"}),
        exits=frozenset(set()),
    ),
}


def _build_transitions() -> Dict[LifecycleState, Set[LifecycleState]]:
    """Compute legal transitions from state definitions."""
    transitions: Dict[LifecycleState, Set[LifecycleState]] = {}
    for state, defn in STATE_DEFINITIONS.items():
        targets = {target for target, _ in defn.exits}
        transitions[state] = targets
    return transitions


LEGAL_TRANSITIONS: Dict[LifecycleState, Set[LifecycleState]] = _build_transitions()


def is_transition_legal(
    current: LifecycleState, target: LifecycleState
) -> bool:
    """Check whether a state transition is legal."""
    return target in LEGAL_TRANSITIONS.get(current, set())


def get_state_definition(state: LifecycleState) -> StateDefinition:
    """Get the four-question template for a state."""
    return STATE_DEFINITIONS[state]


def get_legal_targets(current: LifecycleState) -> List[LifecycleState]:
    """List the states this state can legally transition to."""
    return sorted(LEGAL_TRANSITIONS.get(current, set()), key=lambda s: s.value)
