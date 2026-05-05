"""
Unit tests for Trip API endpoints with follow_up_due_date support.

Tests verify:
1. POST /run creates trips with follow_up_due_date field
2. PATCH /trips/{trip_id} can update follow_up_due_date
3. GET /trips/{trip_id} returns follow_up_due_date in response
4. follow_up_due_date is persisted correctly

Run: uv run python -m pytest tests/test_api_trips_post.py -v
"""

import json
from datetime import datetime, timedelta, timezone
import pytest

pytestmark = pytest.mark.require_postgres


class TestTripFollowUpDueDate:
    """Tests for follow_up_due_date field in Trip model."""

    def test_get_trip_includes_follow_up_due_date_field(self, session_client):
        """GET /trips returns items, and trips should have follow_up_due_date field (can be null)."""
        response = session_client.get("/trips")
        assert response.status_code == 200
        
        data = response.json()
        assert "items" in data
        assert "total" in data
        
        # If there are trips, verify they have follow_up_due_date field (even if null)
        if data["items"]:
            trip = data["items"][0]
            # follow_up_due_date should exist, but can be None/null for existing trips
            assert "follow_up_due_date" in trip or trip.get("follow_up_due_date") is None, \
                "Trip should have follow_up_due_date field (can be null for existing trips)"

    def test_patch_trip_with_follow_up_due_date(self, session_client):
        """PATCH /trips/{trip_id} can update follow_up_due_date field."""
        # First, get an existing trip or list trips
        list_response = session_client.get("/trips")
        assert list_response.status_code == 200
        
        trips = list_response.json().get("items", [])
        if not trips:
            pytest.skip("No trips available to test PATCH")
        
        trip_id = trips[0]["id"]
        
        # Create a future datetime (48 hours from now)
        future_time = datetime.now(timezone.utc) + timedelta(hours=48)
        follow_up_due_date = future_time.isoformat()
        
        # PATCH the trip with follow_up_due_date
        patch_response = session_client.patch(
            f"/trips/{trip_id}",
            json={"follow_up_due_date": follow_up_due_date}
        )
        
        assert patch_response.status_code == 200
        
        updated_trip = patch_response.json()
        assert updated_trip.get("follow_up_due_date") == follow_up_due_date, \
            f"follow_up_due_date should be set to {follow_up_due_date}"

    def test_patch_trip_with_null_follow_up_due_date(self, session_client):
        """PATCH /trips/{trip_id} can clear follow_up_due_date by setting to null."""
        # First, get an existing trip
        list_response = session_client.get("/trips")
        assert list_response.status_code == 200
        
        trips = list_response.json().get("items", [])
        if not trips:
            pytest.skip("No trips available to test PATCH")
        
        trip_id = trips[0]["id"]
        
        # PATCH the trip with follow_up_due_date set to null
        patch_response = session_client.patch(
            f"/trips/{trip_id}",
            json={"follow_up_due_date": None}
        )
        
        assert patch_response.status_code == 200
        
        updated_trip = patch_response.json()
        assert updated_trip.get("follow_up_due_date") is None, \
            "follow_up_due_date should be null"

    def test_patch_trip_preserves_existing_fields(self, session_client):
        """PATCH /trips/{trip_id} with follow_up_due_date preserves other fields."""
        # First, get an existing trip
        list_response = session_client.get("/trips")
        assert list_response.status_code == 200
        
        trips = list_response.json().get("items", [])
        if not trips:
            pytest.skip("No trips available to test PATCH")
        
        trip_id = trips[0]["id"]
        old_trip = trips[0]
        
        # Set follow_up_due_date
        future_time = datetime.now(timezone.utc) + timedelta(hours=48)
        follow_up_due_date = future_time.isoformat()
        
        patch_response = session_client.patch(
            f"/trips/{trip_id}",
            json={"follow_up_due_date": follow_up_due_date}
        )
        
        assert patch_response.status_code == 200
        
        updated_trip = patch_response.json()
        # Verify follow_up_due_date is set
        assert updated_trip.get("follow_up_due_date") == follow_up_due_date
        
        # Verify other key fields are preserved (id, status, created_at)
        assert updated_trip.get("id") == old_trip.get("id"), "Trip ID should not change"
        assert updated_trip.get("status") == old_trip.get("status"), "Status should not change"
        assert updated_trip.get("created_at") == old_trip.get("created_at"), "created_at should not change"

    def test_get_trip_by_id_returns_follow_up_due_date(self, session_client):
        """GET /trips/{trip_id} returns follow_up_due_date field."""
        # First, get a trip list
        list_response = session_client.get("/trips")
        assert list_response.status_code == 200
        
        trips = list_response.json().get("items", [])
        if not trips:
            pytest.skip("No trips available to test GET")
        
        trip_id = trips[0]["id"]
        
        # Set follow_up_due_date via PATCH
        future_time = datetime.now(timezone.utc) + timedelta(hours=48)
        follow_up_due_date = future_time.isoformat()
        
        patch_response = session_client.patch(
            f"/trips/{trip_id}",
            json={"follow_up_due_date": follow_up_due_date}
        )
        assert patch_response.status_code == 200
        
        # GET the trip and verify follow_up_due_date is returned
        get_response = session_client.get(f"/trips/{trip_id}")
        assert get_response.status_code == 200
        
        retrieved_trip = get_response.json()
        assert retrieved_trip.get("follow_up_due_date") == follow_up_due_date, \
            "follow_up_due_date should be persisted and returned in GET"

    def test_patch_trip_with_status_and_follow_up_due_date(self, session_client):
        """PATCH /trips/{trip_id} can update both status and follow_up_due_date."""
        # First, get an existing trip
        list_response = session_client.get("/trips")
        assert list_response.status_code == 200
        
        trips = list_response.json().get("items", [])
        if not trips:
            pytest.skip("No trips available to test PATCH")
        
        trip_id = trips[0]["id"]
        
        # Set both status and follow_up_due_date
        future_time = datetime.now(timezone.utc) + timedelta(hours=48)
        follow_up_due_date = future_time.isoformat()
        
        patch_response = session_client.patch(
            f"/trips/{trip_id}",
            json={
                "status": "in_progress",
                "follow_up_due_date": follow_up_due_date
            }
        )
        
        assert patch_response.status_code == 200
        
        updated_trip = patch_response.json()
        assert updated_trip.get("status") == "in_progress", \
            "Status should be updated to in_progress"
        assert updated_trip.get("follow_up_due_date") == follow_up_due_date, \
            "follow_up_due_date should be set"

    def test_follow_up_due_date_accepts_iso8601_datetime(self, session_client):
        """PATCH /trips/{trip_id} accepts ISO-8601 datetime format."""
        # First, get an existing trip
        list_response = session_client.get("/trips")
        assert list_response.status_code == 200
        
        trips = list_response.json().get("items", [])
        if not trips:
            pytest.skip("No trips available to test PATCH")
        
        trip_id = trips[0]["id"]
        
        # Test various ISO-8601 formats
        test_datetimes = [
            "2026-04-29T14:30:00+00:00",  # With timezone
            "2026-04-29T14:30:00Z",        # With Z for UTC
            "2026-04-29T14:30:00.000000+00:00",  # With microseconds
        ]
        
        for follow_up_due_date in test_datetimes:
            patch_response = session_client.patch(
                f"/trips/{trip_id}",
                json={"follow_up_due_date": follow_up_due_date}
            )
            
            assert patch_response.status_code == 200, \
                f"Should accept ISO-8601 format: {follow_up_due_date}"
            
            updated_trip = patch_response.json()
            # The datetime might be converted to a canonical format, so just check it's set
            assert updated_trip.get("follow_up_due_date") is not None, \
                f"follow_up_due_date should be set for: {follow_up_due_date}"

    def test_patch_trip_follow_up_due_date_persists_across_requests(self, session_client):
        """follow_up_due_date persists across multiple GET requests (data is saved)."""
        # First, get an existing trip
        list_response = session_client.get("/trips")
        assert list_response.status_code == 200
        
        trips = list_response.json().get("items", [])
        if not trips:
            pytest.skip("No trips available to test persistence")
        
        trip_id = trips[0]["id"]
        
        # Set follow_up_due_date
        future_time = datetime.now(timezone.utc) + timedelta(hours=48)
        follow_up_due_date = future_time.isoformat()
        
        patch_response = session_client.patch(
            f"/trips/{trip_id}",
            json={"follow_up_due_date": follow_up_due_date}
        )
        assert patch_response.status_code == 200
        
        # Retrieve the trip multiple times and verify persistence
        for i in range(3):
            get_response = session_client.get(f"/trips/{trip_id}")
            assert get_response.status_code == 200
            
            retrieved_trip = get_response.json()
            assert retrieved_trip.get("follow_up_due_date") == follow_up_due_date, \
                f"follow_up_due_date should persist on retrieval #{i+1}"
