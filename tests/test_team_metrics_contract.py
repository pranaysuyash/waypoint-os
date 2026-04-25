"""
Regression tests for team metrics contract.

These tests verify that compute_team_metrics builds from the canonical roster
(not assignment records), uses real persisted evidence, and returns the correct
counts and conversion rates.
"""

import pytest
from src.analytics.metrics import compute_team_metrics
from src.analytics.models import TeamMemberMetrics


class FakeTeamStore:
    """Minimal stand-in for TeamStore.list_members() output."""
    @staticmethod
    def two_members():
        return [
            {
                "id": "agent_abc123",
                "name": "Alice",
                "role": "senior_agent",
                "capacity": 10,
                "active": True,
            },
            {
                "id": "agent_def456",
                "name": "Bob",
                "role": "junior_agent",
                "capacity": 5,
                "active": True,
            },
        ]


class TestTeamMetricsContract:
    """
    Regression: compute_team_metrics must use the canonical roster (members list)
    and real trip counts.
    
    This test catches the previous bug where compute_team_metrics tried to read
    user_id / name from assignment records (which actually store agent_id /
    agent_name), producing empty metrics when the key names mismatched.
    """

    def test_returns_metric_per_roster_member(self):
        """Every roster member gets an entry, even with zero trips."""
        members = FakeTeamStore.two_members()
        trips = []

        result = compute_team_metrics(trips, members)

        assert len(result) == 2
        assert {m.userId for m in result} == {"agent_abc123", "agent_def456"}

    def test_counts_active_and_completed_from_real_trips(self):
        """Active / completed counts must reflect the actual trip data."""
        members = FakeTeamStore.two_members()
        trips = [
            {"id": "t1", "assigned_to": "agent_abc123", "status": "new"},
            {"id": "t2", "assigned_to": "agent_abc123", "status": "completed"},
            {"id": "t3", "assigned_to": "agent_abc123", "status": "completed"},
            {"id": "t4", "assigned_to": "agent_def456", "status": "assigned"},
        ]

        result = compute_team_metrics(trips, members)
        by_id = {m.userId: m for m in result}

        assert by_id["agent_abc123"].activeTrips == 1
        assert by_id["agent_abc123"].completedTrips == 2
        assert by_id["agent_def456"].activeTrips == 1
        assert by_id["agent_def456"].completedTrips == 0

    def test_conversion_rate_is_real_not_random(self):
        """conversionRate must equal completed / total * 100 (not random)."""
        members = FakeTeamStore.two_members()
        trips = [
            {"id": "t1", "assigned_to": "agent_abc123", "status": "completed"},
            {"id": "t2", "assigned_to": "agent_abc123", "status": "completed"},
            {"id": "t3", "assigned_to": "agent_abc123", "status": "new"},
        ]

        result = compute_team_metrics(trips, members)
        alice = next(m for m in result if m.userId == "agent_abc123")

        assert alice.conversionRate == pytest.approx(66.7, abs=0.1)

    def test_zero_trips_gives_zero_conversion(self):
        """A member with no trips should show 0 conversion, not a random default."""
        members = FakeTeamStore.two_members()
        trips = []

        result = compute_team_metrics(trips, members)
        bob = next(m for m in result if m.userId == "agent_def456")

        assert bob.conversionRate == 0.0

    def test_avg_response_time_is_none(self):
        """avgResponseTime must be None until real response timing data exists."""
        members = FakeTeamStore.two_members()
        trips = []

        result = compute_team_metrics(trips, members)

        for m in result:
            assert m.avgResponseTime is None

    def test_workload_score_from_active_count(self):
        """workloadScore should be min(100, active_count * 6.0)."""
        members = FakeTeamStore.two_members()
        trips = [
            {"id": f"t{i}", "assigned_to": "agent_abc123", "status": "new"}
            for i in range(20)
        ]

        result = compute_team_metrics(trips, members)
        alice = next(m for m in result if m.userId == "agent_abc123")

        assert alice.workloadScore == 100.0  # capped at 100

    def test_unrelated_trips_are_ignored(self):
        """Trips with no assigned_to or unknown assignee must not affect stats."""
        members = FakeTeamStore.two_members()
        trips = [
            {"id": "t1", "assigned_to": None, "status": "new"},
            {"id": "t2", "assigned_to": "UNKNOWN_AGENT", "status": "completed"},
        ]

        result = compute_team_metrics(trips, members)

        for m in result:
            assert m.activeTrips == 0
            assert m.completedTrips == 0
