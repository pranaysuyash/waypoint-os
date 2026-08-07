"""
tests/test_concierge_router.py — Unit & Integration tests for Autonomic Ghost Concierge Engine.
"""

import os
from unittest.mock import patch
import pytest

from spine_api.contract import AutoRebookRequest
from spine_api.persistence import TEST_AGENCY_ID, TripStore
from spine_api.routers.concierge import execute_auto_rebook, monitor_trip_status

os.environ["RUNNING_TESTS"] = "1"



@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    monkeypatch.setenv("DATA_PRIVACY_MODE", "beta")
    monkeypatch.setenv("TRIPSTORE_BACKEND", "file")


@pytest.mark.asyncio
async def test_monitor_trip_status_success():
    """Verify actively monitoring trip flight status for disruptions."""
    trip_data = {
        "id": "trip_concierge_1",
        "agency_id": TEST_AGENCY_ID,
        "destination": "Paris",
        "status": "active",
        "agent_notes": "Client flight delay expected due to strike",
    }
    with patch.object(TripStore, "get_trip_for_agency", return_value=trip_data):
        res = await monitor_trip_status("trip_concierge_1", agency_id=TEST_AGENCY_ID)
        assert res.ok is True
        assert res.trip_id == "trip_concierge_1"
        assert res.disruption_detected is True
        assert res.disruption_type == "FLIGHT_DELAY"


@pytest.mark.asyncio
async def test_execute_auto_rebook_blocks_when_tier_lacks_capability():
    """Verify execute_auto_rebook raises 403 when concierge tier is DATA_DEPENDENT."""
    from fastapi import HTTPException

    trip_data = {
        "id": "trip_concierge_2",
        "agency_id": TEST_AGENCY_ID,
        "destination": "Paris",
        "status": "active",
    }
    req = AutoRebookRequest(trip_id="trip_concierge_2", disruption_event_id="evt_delay_9921")
    with patch.object(TripStore, "get_trip_for_agency", return_value=trip_data):
        with pytest.raises(HTTPException) as exc_info:
            await execute_auto_rebook("trip_concierge_2", req, agency_id=TEST_AGENCY_ID)
        assert exc_info.value.status_code == 403
        assert "can_mutate_booking_state" in exc_info.value.detail
