"""
PA-38: escalation split-brain regression tests.

Recovery-agent escalations used to write only ``trips.review_status`` while
the escalated queue reads ``TripRoutingState.status`` — two surfaces that
never converged. The adapter now mirrors system escalations onto the
canonical routing surface via ``routing_service.system_escalate``.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

spine_api_dir = Path(__file__).parent.parent / "spine_api"
if str(spine_api_dir) not in sys.path:
    sys.path.insert(0, str(spine_api_dir))

from spine_api.services.routing_service import system_escalate  # noqa: E402
from tests.test_routing_state_machine import _make_db, _make_routing_state  # noqa: E402


# ── system_escalate (canonical surface) ──────────────────────────────────────


@pytest.mark.asyncio
async def test_system_escalate_transitions_unassigned_state():
    """Recovery must be able to escalate a trip with no assignment (PA-38)."""
    state = _make_routing_state(trip_id="trip-9", status="unassigned")
    db = _make_db(existing_state=state)

    result = await system_escalate(db, "trip-9", "agy-1", reason="stuck 72h")

    assert result["status"] == "escalated"
    assert result["escalated_at"] is not None
    assert state.handoff_history[-1]["action"] == "system_escalate"
    assert state.handoff_history[-1]["reason"] == "stuck 72h"
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_system_escalate_is_idempotent_when_already_escalated():
    state = _make_routing_state(trip_id="trip-1", status="escalated")
    db = _make_db(existing_state=state)

    result = await system_escalate(db, "trip-1", "agy-1")

    assert result["status"] == "escalated"
    db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_system_escalate_works_from_assigned_state():
    state = _make_routing_state(trip_id="trip-2", status="assigned")
    db = _make_db(existing_state=state)

    result = await system_escalate(db, "trip-2", "agy-1", reason="recovery")

    assert result["status"] == "escalated"


# ── adapter mirror ───────────────────────────────────────────────────────────


class _FakeSessionCM:
    async def __aenter__(self):
        return object()

    async def __aexit__(self, *args):
        return False


def _fake_session_maker():
    return _FakeSessionCM()


def _run(coro):
    return asyncio.run(coro)


def _make_adapter(monkeypatch, captured, trip_agency="agy-1"):
    """Build a TripStoreAdapter with TripStore + session-maker + escalate patched."""
    from spine_api.services import agent_runtime_adapters as adapters

    store = MagicMock()
    store.update_trip = MagicMock(return_value={"trip_id": "trip-1", "agency_id": trip_agency})
    monkeypatch.setattr(adapters.TripStoreAdapter, "_resolve_sync", lambda self, value: _run(value) if asyncio.iscoroutine(value) else value)
    monkeypatch.setattr("spine_api.persistence.TripStore", store)
    monkeypatch.setattr("spine_api.core.database.async_session_maker", _fake_session_maker)

    async def _capture_system_escalate(db, trip_id, agency_id, reason=None):
        captured.append({"trip_id": trip_id, "agency_id": agency_id, "reason": reason})
        return {"trip_id": trip_id, "status": "escalated"}

    monkeypatch.setattr(
        "spine_api.services.routing_service.system_escalate", _capture_system_escalate
    )
    return adapters.TripStoreAdapter()


def test_adapter_mirrors_escalation_to_routing_state(monkeypatch):
    captured: list = []
    adapter = _make_adapter(monkeypatch, captured)

    adapter.set_review_status("trip-1", "escalated")

    assert len(captured) == 1
    assert captured[0]["trip_id"] == "trip-1"
    assert captured[0]["agency_id"] == "agy-1"


def test_adapter_skips_mirror_for_non_escalated_status(monkeypatch):
    captured: list = []
    adapter = _make_adapter(monkeypatch, captured)

    adapter.set_review_status("trip-1", "assigned")

    assert captured == []


def test_adapter_mirror_requires_agency_id(monkeypatch):
    captured: list = []
    adapter = _make_adapter(monkeypatch, captured, trip_agency=None)

    with pytest.raises(ValueError, match="no agency_id"):
        adapter.set_review_status("trip-1", "escalated")

    assert captured == []
