"""
tests/test_concierge_real.py — Tests for concierge disruption monitoring and rebooking.

Verifies:
  - Monitoring unknown trip returns 404
  - Monitoring matching agency trip returns status
  - Rebooking unknown trip returns 404
  - Listing disruptions filters strictly by agency_id with no demo fallbacks
"""

import pytest
from unittest.mock import patch
from fastapi import HTTPException

from spine_api.contract import AutoRebookRequest
from spine_api.routers.concierge import (
    monitor_trip_status,
    execute_auto_rebook,
    list_active_disruptions,
)
from spine_api.persistence import TripStore


@pytest.mark.asyncio
class TestConciergeEngine:
    """Test concierge disruption monitoring and rebooking."""

    async def test_monitor_unknown_trip_returns_404(self):
        with patch.object(TripStore, "get_trip_for_agency", return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                await monitor_trip_status("nonexistent_trip", agency_id="agency_1")
            assert exc_info.value.status_code == 404

    async def test_monitor_matching_trip(self):
        trip_data = {
            "id": "trip_1",
            "agency_id": "agency_1",
            "status": "active",
            "agent_notes": "Flight disruption reported",
        }
        with patch.object(TripStore, "get_trip_for_agency", return_value=trip_data):
            res = await monitor_trip_status("trip_1", agency_id="agency_1")
            assert res.ok is True
            assert res.disruption_detected is True

    async def test_rebook_unknown_trip_returns_404(self):
        req = AutoRebookRequest(trip_id="nonexistent_trip", disruption_event_id="evt_123")
        with patch.object(TripStore, "get_trip_for_agency", return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                await execute_auto_rebook("nonexistent_trip", req, agency_id="agency_1")
            assert exc_info.value.status_code == 404

    async def test_list_disruptions_no_demo_fallback(self):
        """When an agency has no trips, disruptions list is empty (no fake Priya Sharma)."""
        with patch.object(TripStore, "list_trips", return_value=[]):
            res = await list_active_disruptions(agency_id="agency_1")
            assert res["ok"] is True
            assert len(res["active_disruptions"]) == 0
            assert res["monitored_trips_count"] == 0
            assert "_meta" in res
