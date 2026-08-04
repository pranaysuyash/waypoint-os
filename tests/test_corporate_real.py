"""
tests/test_corporate_real.py — Tests for corporate duty-of-care and policy audit.

Verifies:
  - Policy audit checks per-diem caps and cabin class
  - Non-existent trip returns 404
  - Duty-of-care cockpit returns real agency trips
  - Includes reality tier metadata
"""

import pytest
from unittest.mock import patch
from fastapi import HTTPException

from spine_api.routers.corporate import (
    PolicyAuditRequest,
    audit_corporate_policy,
    get_duty_of_care_cockpit,
)
from spine_api.persistence import TripStore


@pytest.mark.asyncio
class TestCorporatePolicyAudit:
    """Test policy audit logic."""

    async def test_audit_nonexistent_trip_returns_404(self):
        req = PolicyAuditRequest(
            trip_id="nonexistent_123",
            hotel_rate_per_night=300.0,
        )
        with patch.object(TripStore, "get_trip_for_agency", return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                await audit_corporate_policy(req, agency_id="agency_1")
            assert exc_info.value.status_code == 404

    async def test_audit_compliant_trip(self):
        req = PolicyAuditRequest(
            trip_id="trip_123",
            city_code="LON",
            hotel_rate_per_night=300.0,  # Cap is 350
            cabin_class="ECONOMY",
            employee_grade="MANAGER",
        )
        trip_data = {"id": "trip_123", "agency_id": "agency_1"}
        with patch.object(TripStore, "get_trip_for_agency", return_value=trip_data):
            res = await audit_corporate_policy(req, agency_id="agency_1")
            assert res.ok is True
            assert res.is_compliant is True
            assert len(res.violations) == 0

    async def test_audit_exceeded_per_diem(self):
        req = PolicyAuditRequest(
            trip_id="trip_123",
            city_code="LON",
            hotel_rate_per_night=500.0,  # Cap is 350, exceeded by 150
            cabin_class="ECONOMY",
            employee_grade="MANAGER",
        )
        trip_data = {"id": "trip_123", "agency_id": "agency_1"}
        with patch.object(TripStore, "get_trip_for_agency", return_value=trip_data):
            res = await audit_corporate_policy(req, agency_id="agency_1")
            assert res.is_compliant is False
            assert len(res.violations) == 1
            assert res.violations[0].code == "PER_DIEM_EXCEEDED"
            assert res.violations[0].amount_exceeded == 150.0


@pytest.mark.asyncio
class TestDutyOfCareCockpit:
    """Test duty-of-care cockpit endpoint."""

    async def test_cockpit_returns_real_agency_trips(self):
        trips = [
            {"id": "trip_1", "agency_id": "agency_1", "traveler_name": "Alice Corp"},
            {"id": "trip_2", "agency_id": "agency_1", "traveler_name": "Bob Corp"},
        ]
        with patch.object(TripStore, "list_trips", return_value=trips):
            res = await get_duty_of_care_cockpit(agency_id="agency_1")
            assert res["ok"] is True
            assert res["total_active_travelers"] == 2
            assert res["travelers"][0]["traveler_name"] == "Alice Corp"
            assert "_meta" in res
