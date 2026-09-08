"""S2 tests for travel next-best-action projection (E-NBA / AT-07).

Commercial CRM tokens stay on next_best_action. Trip-level operator_next_action
is an alias of the winning travel action; a weather tick cannot erase disruption.
"""

from src.agents.runtime import AgentSupervisor, AgentRegistry
from src.intake.decision import DecisionResult
from src.orchestration.travel_next_action import (
    NextActionAwareTripRepo,
    merge_next_action_updates,
    priority_for,
    travel_action_from_decision_state,
)


class _Repo:
    def __init__(self, trips):
        self.trips = {trip["id"]: dict(trip) for trip in trips}

    def list_active(self):
        return list(self.trips.values())

    def get_trip(self, trip_id: str):
        return self.trips.get(trip_id)

    def update_trip(self, trip_id: str, updates: dict):
        trip = self.trips.get(trip_id)
        if not trip:
            return None
        trip.update(updates)
        return trip

    def extra_method(self):
        return "proxied"


def test_travel_action_from_decision_state_is_not_crm():
    assert travel_action_from_decision_state("ASK_FOLLOWUP") == "collect_missing_facts"
    assert travel_action_from_decision_state("STOP_NEEDS_REVIEW") == "human_review"
    assert travel_action_from_decision_state("PROCEED_TRAVELER_SAFE") == "continue_proposal"
    assert travel_action_from_decision_state("BRANCH_OPTIONS") == "continue_proposal"
    assert travel_action_from_decision_state("PROCEED_INTERNAL_DRAFT") == "continue_proposal"


def test_crm_tokens_never_outrank_travel_actions():
    assert priority_for("SEND_FOLLOWUP") < priority_for("monitor_weather")
    assert priority_for("CLOSE_LOST") < priority_for("review_flight_disruption")
    assert priority_for("monitor_weather") < priority_for("review_flight_disruption")
    assert priority_for("review_weather_pivots") < priority_for("review_flight_disruption")
    assert priority_for("human_safety_review") > priority_for("review_flight_disruption")


def test_weather_cannot_clobber_disruption():
    repo = _Repo(
        [
            {
                "id": "trip_nba_1",
                "travel_next_action": "review_flight_disruption",
                "travel_next_action_priority": 90,
                "operator_next_action": "review_flight_disruption",
            }
        ]
    )
    merged = merge_next_action_updates(
        repo,
        "trip_nba_1",
        {
            "operator_next_action": "monitor_weather",
            "last_agent_action": "weather_pivot_agent",
        },
    )
    assert "operator_next_action" not in merged
    assert merged["last_agent_proposal"] == "monitor_weather"
    assert merged.get("travel_next_action") != "monitor_weather"


def test_higher_priority_travel_action_wins():
    repo = _Repo(
        [
            {
                "id": "trip_nba_2",
                "travel_next_action": "monitor_weather",
                "travel_next_action_priority": 20,
                "operator_next_action": "monitor_weather",
            }
        ]
    )
    merged = merge_next_action_updates(
        repo,
        "trip_nba_2",
        {
            "operator_next_action": "review_flight_disruption",
            "last_agent_action": "flight_status_agent",
        },
    )
    assert merged["operator_next_action"] == "review_flight_disruption"
    assert merged["travel_next_action"] == "review_flight_disruption"
    assert merged["travel_next_action_priority"] == 90
    assert merged["travel_next_action_source"] == "flight_status_agent"


def test_repo_proxy_enforces_priority_on_update():
    inner = _Repo(
        [
            {
                "id": "trip_nba_3",
                "travel_next_action": "review_flight_disruption",
                "travel_next_action_priority": 90,
                "operator_next_action": "review_flight_disruption",
            }
        ]
    )
    wrapped = NextActionAwareTripRepo(inner)
    wrapped.update_trip(
        "trip_nba_3",
        {"operator_next_action": "monitor_weather", "last_agent_action": "weather"},
    )
    stored = inner.get_trip("trip_nba_3")
    assert stored["operator_next_action"] == "review_flight_disruption"
    assert stored["travel_next_action"] == "review_flight_disruption"
    assert stored["last_agent_proposal"] == "monitor_weather"
    assert wrapped.extra_method() == "proxied"


def test_agent_supervisor_wraps_trip_repo():
    inner = _Repo([{"id": "trip_nba_4"}])
    supervisor = AgentSupervisor(AgentRegistry([]), inner, audit=None)
    assert isinstance(supervisor.trip_repo, NextActionAwareTripRepo)


def test_decision_result_keeps_commercial_and_travel_fields():
    result = DecisionResult(
        packet_id="pkt_nba",
        current_stage="discovery",
        operating_mode="standard",
        decision_state="ASK_FOLLOWUP",
        next_best_action="SEND_FOLLOWUP",
        commercial_next_action="SEND_FOLLOWUP",
        travel_next_action="collect_missing_facts",
    )
    assert result.next_best_action == "SEND_FOLLOWUP"
    assert result.commercial_next_action == "SEND_FOLLOWUP"
    assert result.travel_next_action == "collect_missing_facts"
    assert result.next_best_action != result.travel_next_action


class _RacyRepo(_Repo):
    """CAS repo that reproduces the Part-H P1 interleaving: a stale writer's
    lower-priority action lands right after ours, before verification."""

    def __init__(self, trips):
        super().__init__(trips)
        self.clobbered_once = False

    def update_trip_if_version(self, trip_id: str, updates: dict, expected_updated_at=None):
        trip = self.trips.get(trip_id)
        if not trip:
            return None
        if trip.get("updated_at") != expected_updated_at:
            return None
        trip.update(updates)
        if not self.clobbered_once:
            trip["travel_next_action"] = "monitor_weather"
            trip["travel_next_action_priority"] = 20
            trip["operator_next_action"] = "monitor_weather"
            self.clobbered_once = True
        return trip


def test_cas_proxy_heals_stale_lower_priority_clobber():
    """Part-H P1: a stale weather write landing after a disruption write must
    not stand — the CAS verify-and-heal loop re-applies the higher-priority
    action against the fresh state."""
    inner = _RacyRepo(
        [
            {
                "id": "trip_nba_race",
                "updated_at": "2026-09-07T00:00:00Z",
                "travel_next_action": "monitor_weather",
                "travel_next_action_priority": 20,
                "operator_next_action": "monitor_weather",
            }
        ]
    )
    wrapped = NextActionAwareTripRepo(inner)
    result = wrapped.update_trip(
        "trip_nba_race",
        {
            "operator_next_action": "review_flight_disruption",
            "last_agent_action": "flight_status_agent",
        },
    )
    assert result is not None
    stored = inner.get_trip("trip_nba_race")
    assert stored["travel_next_action"] == "review_flight_disruption"
    assert stored["travel_next_action_priority"] == 90
    assert stored["operator_next_action"] == "review_flight_disruption"


def test_persistent_cas_contention_never_clobbers_action():
    """Part-J #6: after exhausted CAS retries the proxy must fail CLOSED —
    the stale action/priority write is dropped, only contention-safe metadata
    lands, and the stored action is never downgraded."""
    inner = _AlwaysContendedRepo(
        [
            {
                "id": "trip_nba_cas",
                "updated_at": "2026-09-07T00:00:00Z",
                "travel_next_action": "monitor_weather",
                "travel_next_action_priority": 20,
                "operator_next_action": "monitor_weather",
            }
        ]
    )
    wrapped = NextActionAwareTripRepo(inner)
    wrapped.update_trip(
        "trip_nba_cas",
        {
            "operator_next_action": "review_flight_disruption",
            "last_agent_action": "flight_status_agent",
        },
    )
    stored = inner.get_trip("trip_nba_cas")
    assert stored["travel_next_action"] == "monitor_weather"
    assert stored["travel_next_action_priority"] == 20
    assert stored["last_agent_proposal"] == "review_flight_disruption"


class _AlwaysContendedRepo(_Repo):
    def update_trip_if_version(self, trip_id: str, updates: dict, expected_updated_at=None):
        return None
