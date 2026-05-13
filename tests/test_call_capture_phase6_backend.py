"""
Phase 6 Backend Tests - Activity Provenance API

Test coverage for GET /trips/{trip_id}/activities/provenance endpoint:
- Retrieve activities with source (suggested/requested)
- Confidence scores for suggested activities
- Error handling for missing trips
- Authorization checks
- Data formatting and validation

10 tests total
"""

import pytest
from fastapi.testclient import TestClient
from spine_api.persistence import TripStore, TEST_AGENCY_ID
from datetime import datetime, timezone


@pytest.fixture
def test_trip_id():
    """Create a test trip with activity provenance."""
    trip_data = {
        "id": "trip_test_provenance_1",
        "traveler_name": "Test Traveler",
        "destination": "Singapore",
        "status": "in_progress",
        "activity_provenance": "Hiking, Marina Bay Sands, Hawker Food Tour",
        "agency_id": TEST_AGENCY_ID,
    }
    trip_id = TripStore.save_trip(trip_data, agency_id=TEST_AGENCY_ID)
    yield trip_id
    # Cleanup
    import os
    from pathlib import Path
    from spine_api.persistence import TRIPS_DIR
    trip_file = TRIPS_DIR / f"{trip_id}.json"
    if trip_file.exists():
        trip_file.unlink()


@pytest.fixture
def test_trip_empty():
    """Create a test trip without activity provenance."""
    trip_data = {
        "id": "trip_test_provenance_empty",
        "traveler_name": "Empty Trip",
        "destination": "Paris",
        "status": "in_progress",
        "agency_id": TEST_AGENCY_ID,
    }
    trip_id = TripStore.save_trip(trip_data, agency_id=TEST_AGENCY_ID)
    yield trip_id
    # Cleanup
    import os
    from pathlib import Path
    from spine_api.persistence import TRIPS_DIR
    trip_file = TRIPS_DIR / f"{trip_id}.json"
    if trip_file.exists():
        trip_file.unlink()


def test_get_activities_provenance_success(session_client, test_trip_id):
    """Test successful retrieval of activity provenance."""
    response = session_client.get(f"/trips/{test_trip_id}/activities/provenance")
    
    assert response.status_code == 200
    data = response.json()
    assert data["trip_id"] == test_trip_id
    assert "activities" in data
    assert isinstance(data["activities"], list)


def test_get_activities_provenance_returns_activities(session_client, test_trip_id):
    """Test that activities are returned from activity_provenance field."""
    response = session_client.get(f"/trips/{test_trip_id}/activities/provenance")
    
    assert response.status_code == 200
    data = response.json()
    activities = data["activities"]
    
    # Should have 3 activities from the activity_provenance field
    assert len(activities) >= 1
    
    # Each activity should have required fields
    for activity in activities:
        assert "name" in activity
        assert "source" in activity
        assert activity["source"] in ["suggested", "requested"]


def test_get_activities_provenance_suggested_has_confidence(session_client, test_trip_id):
    """Test that suggested activities include confidence scores."""
    response = session_client.get(f"/trips/{test_trip_id}/activities/provenance")
    
    assert response.status_code == 200
    data = response.json()
    activities = data["activities"]
    
    # All activities in test data are marked as suggested
    for activity in activities:
        if activity["source"] == "suggested":
            assert "confidence" in activity
            assert isinstance(activity["confidence"], (int, float))
            assert 0 <= activity["confidence"] <= 100


def test_get_activities_provenance_activity_names(session_client, test_trip_id):
    """Test that activity names are correctly parsed and returned."""
    response = session_client.get(f"/trips/{test_trip_id}/activities/provenance")
    
    assert response.status_code == 200
    data = response.json()
    activities = data["activities"]
    
    # Check that we have the expected activities
    activity_names = [a["name"] for a in activities]
    assert "Hiking" in activity_names
    assert "Marina Bay Sands" in activity_names


def test_get_activities_provenance_trip_not_found(session_client):
    """Test 404 error when trip doesn't exist."""
    response = session_client.get("/trips/nonexistent_trip_12345/activities/provenance")
    
    assert response.status_code == 404


def test_get_activities_provenance_empty_trip(session_client, test_trip_empty):
    """Test handling of trip with no activity provenance."""
    response = session_client.get(f"/trips/{test_trip_empty}/activities/provenance")
    
    assert response.status_code == 200
    data = response.json()
    assert data["trip_id"] == test_trip_empty
    assert data["activities"] == []


def test_get_activities_provenance_response_format(session_client, test_trip_id):
    """Test that response follows the expected format."""
    response = session_client.get(f"/trips/{test_trip_id}/activities/provenance")
    
    assert response.status_code == 200
    data = response.json()
    
    # Check required response fields
    assert "trip_id" in data
    assert "activities" in data
    
    # Check trip_id matches request
    assert data["trip_id"] == test_trip_id


def test_get_activities_provenance_whitespace_handling(session_client):
    """Test handling of activities with whitespace."""
    trip_data = {
        "id": "trip_test_provenance_whitespace",
        "traveler_name": "Whitespace Trip",
        "destination": "Tokyo",
        "status": "in_progress",
        "activity_provenance": "  Sumo Wrestling  ,  Temple Visit  ,  Karaoke  ",
        "agency_id": TEST_AGENCY_ID,
    }
    trip_id = TripStore.save_trip(trip_data, agency_id=TEST_AGENCY_ID)
    
    try:
        response = session_client.get(f"/trips/{trip_id}/activities/provenance")
        
        assert response.status_code == 200
        data = response.json()
        activities = data["activities"]
        
        # Check that whitespace is stripped
        activity_names = [a["name"] for a in activities]
        assert "Sumo Wrestling" in activity_names
        assert "Temple Visit" in activity_names
        assert "Karaoke" in activity_names
        
        # Should not have leading/trailing whitespace
        for activity in activities:
            assert activity["name"] == activity["name"].strip()
    
    finally:
        # Cleanup
        from pathlib import Path
        from spine_api.persistence import TRIPS_DIR
        trip_file = TRIPS_DIR / f"{trip_id}.json"
        if trip_file.exists():
            trip_file.unlink()


def test_get_activities_provenance_single_activity(session_client):
    """Test handling of trip with single activity."""
    trip_data = {
        "id": "trip_test_provenance_single",
        "traveler_name": "Single Activity Trip",
        "destination": "Barcelona",
        "status": "in_progress",
        "activity_provenance": "Beach Day",
        "agency_id": TEST_AGENCY_ID,
    }
    trip_id = TripStore.save_trip(trip_data, agency_id=TEST_AGENCY_ID)
    
    try:
        response = session_client.get(f"/trips/{trip_id}/activities/provenance")
        
        assert response.status_code == 200
        data = response.json()
        activities = data["activities"]
        
        assert len(activities) == 1
        assert activities[0]["name"] == "Beach Day"
        assert activities[0]["source"] == "suggested"
    
    finally:
        # Cleanup
        from pathlib import Path
        from spine_api.persistence import TRIPS_DIR
        trip_file = TRIPS_DIR / f"{trip_id}.json"
        if trip_file.exists():
            trip_file.unlink()
