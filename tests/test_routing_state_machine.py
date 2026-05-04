"""
Tests for the routing state machine (routing_service.py) and SLA service.

All tests use mock AsyncSession — no live DB needed.
Tests cover:
- assign, claim, escalate, reassign, return_for_changes, unassign transitions
- Invalid transitions (RoutingError raised)
- handoff_history entries are appended correctly
- SLA status classification (on_track, at_risk, breached)
"""

import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

spine_api_dir = Path(__file__).parent.parent / "spine_api"
if str(spine_api_dir) not in sys.path:
    sys.path.insert(0, str(spine_api_dir))


# ── Helpers ──────────────────────────────────────────────────────────────────

def _make_routing_state(
    trip_id="trip-1",
    agency_id="agy-1",
    status="unassigned",
    primary_assignee_id=None,
    escalation_owner_id=None,
    assigned_at=None,
    escalated_at=None,
    handoff_history=None,
):
    from spine_api.models.routing import TripRoutingState
    s = TripRoutingState.__new__(TripRoutingState)
    s.id = "rts-1"
    s.trip_id = trip_id
    s.agency_id = agency_id
    s.status = status
    s.primary_assignee_id = primary_assignee_id
    s.reviewer_id = None
    s.escalation_owner_id = escalation_owner_id
    s.assigned_at = assigned_at
    s.escalated_at = escalated_at
    s.handoff_history = handoff_history if handoff_history is not None else []
    s.created_at = datetime.now(timezone.utc)
    s.updated_at = datetime.now(timezone.utc)
    return s


def _make_db(existing_state=None):
    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none = MagicMock(return_value=existing_state)
    db.execute = AsyncMock(return_value=result)
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    return db


# ── assign ────────────────────────────────────────────────────────────────────

class TestAssignTrip:

    @pytest.mark.asyncio
    async def test_unassigned_to_assigned(self):
        from spine_api.services.routing_service import assign_trip

        state = _make_routing_state(status="unassigned")
        db = _make_db(existing_state=state)

        result = await assign_trip(db, "trip-1", "agy-1", "usr-agent", "usr-admin")

        assert result["status"] == "assigned"
        assert result["primary_assignee_id"] == "usr-agent"
        assert len(result["handoff_history"]) == 1
        assert result["handoff_history"][0]["action"] == "assign"
        assert result["handoff_history"][0]["to_user_id"] == "usr-agent"

    @pytest.mark.asyncio
    async def test_already_assigned_raises(self):
        from spine_api.services.routing_service import assign_trip, RoutingError

        state = _make_routing_state(status="assigned", primary_assignee_id="usr-1")
        db = _make_db(existing_state=state)

        with pytest.raises(RoutingError, match="Cannot assign"):
            await assign_trip(db, "trip-1", "agy-1", "usr-2", "usr-admin")


# ── claim ─────────────────────────────────────────────────────────────────────

class TestClaimTrip:

    @pytest.mark.asyncio
    async def test_self_assign_unassigned(self):
        from spine_api.services.routing_service import claim_trip

        state = _make_routing_state(status="unassigned")
        db = _make_db(existing_state=state)

        result = await claim_trip(db, "trip-1", "agy-1", "usr-senior")

        assert result["status"] == "assigned"
        assert result["primary_assignee_id"] == "usr-senior"
        assert result["handoff_history"][0]["action"] == "claim"

    @pytest.mark.asyncio
    async def test_claim_assigned_raises(self):
        from spine_api.services.routing_service import claim_trip, RoutingError

        state = _make_routing_state(status="assigned")
        db = _make_db(existing_state=state)

        with pytest.raises(RoutingError, match="Cannot claim"):
            await claim_trip(db, "trip-1", "agy-1", "usr-senior")


# ── escalate ──────────────────────────────────────────────────────────────────

class TestEscalateTrip:

    @pytest.mark.asyncio
    async def test_assigned_to_escalated(self):
        from spine_api.services.routing_service import escalate_trip

        state = _make_routing_state(status="assigned", primary_assignee_id="usr-junior")
        db = _make_db(existing_state=state)

        result = await escalate_trip(db, "trip-1", "agy-1", "usr-senior", "usr-junior", reason="needs help")

        assert result["status"] == "escalated"
        assert result["escalation_owner_id"] == "usr-senior"
        assert result["primary_assignee_id"] == "usr-junior"  # preserved
        assert result["handoff_history"][0]["reason"] == "needs help"

    @pytest.mark.asyncio
    async def test_escalate_unassigned_raises(self):
        from spine_api.services.routing_service import escalate_trip, RoutingError

        state = _make_routing_state(status="unassigned")
        db = _make_db(existing_state=state)

        with pytest.raises(RoutingError, match="Cannot escalate"):
            await escalate_trip(db, "trip-1", "agy-1", "usr-senior", "usr-admin")


# ── reassign ──────────────────────────────────────────────────────────────────

class TestReassignTrip:

    @pytest.mark.asyncio
    async def test_reassign_clears_escalation(self):
        from spine_api.services.routing_service import reassign_trip

        state = _make_routing_state(
            status="escalated",
            primary_assignee_id="usr-old",
            escalation_owner_id="usr-escalation",
        )
        db = _make_db(existing_state=state)

        result = await reassign_trip(db, "trip-1", "agy-1", "usr-new", "usr-admin", reason="bandwidth")

        assert result["status"] == "assigned"
        assert result["primary_assignee_id"] == "usr-new"
        assert result["escalation_owner_id"] is None
        assert result["handoff_history"][0]["from_user_id"] == "usr-old"
        assert result["handoff_history"][0]["to_user_id"] == "usr-new"

    @pytest.mark.asyncio
    async def test_reassign_from_unassigned_raises(self):
        from spine_api.services.routing_service import reassign_trip, RoutingError

        state = _make_routing_state(status="unassigned")
        db = _make_db(existing_state=state)

        with pytest.raises(RoutingError, match="Cannot reassign"):
            await reassign_trip(db, "trip-1", "agy-1", "usr-new", "usr-admin")


# ── return_for_changes ────────────────────────────────────────────────────────

class TestReturnForChanges:

    @pytest.mark.asyncio
    async def test_escalated_to_returned(self):
        from spine_api.services.routing_service import return_for_changes

        state = _make_routing_state(
            status="escalated",
            primary_assignee_id="usr-junior",
            escalation_owner_id="usr-senior",
        )
        db = _make_db(existing_state=state)

        result = await return_for_changes(db, "trip-1", "agy-1", "usr-senior", reason="missing docs")

        assert result["status"] == "returned"
        assert result["escalation_owner_id"] is None
        assert result["handoff_history"][0]["action"] == "return_for_changes"

    @pytest.mark.asyncio
    async def test_return_from_unassigned_raises(self):
        from spine_api.services.routing_service import return_for_changes, RoutingError

        state = _make_routing_state(status="unassigned")
        db = _make_db(existing_state=state)

        with pytest.raises(RoutingError, match="Cannot return"):
            await return_for_changes(db, "trip-1", "agy-1", "usr-reviewer")


# ── unassign ──────────────────────────────────────────────────────────────────

class TestUnassignTrip:

    @pytest.mark.asyncio
    async def test_unassign_clears_all(self):
        from spine_api.services.routing_service import unassign_trip

        state = _make_routing_state(
            status="escalated",
            primary_assignee_id="usr-a",
            escalation_owner_id="usr-b",
        )
        db = _make_db(existing_state=state)

        result = await unassign_trip(db, "trip-1", "agy-1", "usr-admin")

        assert result["status"] == "unassigned"
        assert result["primary_assignee_id"] is None
        assert result["escalation_owner_id"] is None
        assert result["handoff_history"][0]["from_user_id"] == "usr-a"


# ── handoff_history accumulation ─────────────────────────────────────────────

class TestHandoffHistoryAccumulation:

    @pytest.mark.asyncio
    async def test_history_entries_accumulate(self):
        from spine_api.services.routing_service import assign_trip, escalate_trip

        # Start unassigned
        state = _make_routing_state(status="unassigned")
        db = _make_db(existing_state=state)
        await assign_trip(db, "trip-1", "agy-1", "usr-junior", "usr-admin")

        # Now escalate
        state.status = "assigned"
        state.primary_assignee_id = "usr-junior"
        db2 = _make_db(existing_state=state)
        result = await escalate_trip(db2, "trip-1", "agy-1", "usr-senior", "usr-junior")

        # The handoff_history on the state should now have an escalate entry
        assert any(h["action"] == "escalate" for h in result["handoff_history"])


# ── SLA service ───────────────────────────────────────────────────────────────

class TestSlaService:

    def _state(self, assigned_at=None, escalated_at=None):
        return {
            "assigned_at": assigned_at.isoformat() if assigned_at else None,
            "escalated_at": escalated_at.isoformat() if escalated_at else None,
        }

    def test_not_assigned_returns_not_started(self):
        from spine_api.services.sla_service import compute_sla

        result = compute_sla(self._state())
        assert result["ownership"]["status"] == "not_started"
        assert result["escalation"]["status"] == "not_started"
        assert result["worst"] == "not_started"

    def test_recent_assignment_is_on_track(self):
        from spine_api.services.sla_service import compute_sla

        recent = datetime.now(timezone.utc) - timedelta(minutes=30)
        result = compute_sla(self._state(assigned_at=recent), ownership_warn_hrs=4)
        assert result["ownership"]["status"] == "on_track"

    def test_old_assignment_is_at_risk(self):
        from spine_api.services.sla_service import compute_sla

        old = datetime.now(timezone.utc) - timedelta(hours=5)
        result = compute_sla(self._state(assigned_at=old), ownership_warn_hrs=4, ownership_breach_hrs=24)
        assert result["ownership"]["status"] == "at_risk"

    def test_very_old_assignment_is_breached(self):
        from spine_api.services.sla_service import compute_sla

        very_old = datetime.now(timezone.utc) - timedelta(hours=30)
        result = compute_sla(self._state(assigned_at=very_old), ownership_warn_hrs=4, ownership_breach_hrs=24)
        assert result["ownership"]["status"] == "breached"

    def test_escalation_breach_dominates_worst(self):
        from spine_api.services.sla_service import compute_sla

        recent_assign = datetime.now(timezone.utc) - timedelta(minutes=10)
        old_escalate = datetime.now(timezone.utc) - timedelta(hours=10)
        result = compute_sla(
            self._state(assigned_at=recent_assign, escalated_at=old_escalate),
            ownership_warn_hrs=4,
            ownership_breach_hrs=24,
            escalation_warn_hrs=2,
            escalation_breach_hrs=8,
        )
        assert result["worst"] == "breached"
        assert result["ownership"]["status"] == "on_track"

    def test_hours_elapsed_returned(self):
        from spine_api.services.sla_service import compute_sla

        two_hours_ago = datetime.now(timezone.utc) - timedelta(hours=2)
        result = compute_sla(self._state(assigned_at=two_hours_ago))
        hrs = result["ownership"]["hours_elapsed"]
        assert hrs is not None
        assert 1.9 < hrs < 2.1
