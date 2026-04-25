"""
Tests for the timeline REST endpoint (GET /api/trips/{trip_id}/timeline).

Validates the FastAPI endpoint returns the correct JSONL events as JSON.
"""

import json
import pytest
from fastapi.testclient import TestClient

# We need to import and set up the FastAPI app
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "spine_api"))

from server import app


def test_timeline_endpoint_empty_when_no_file(session_client):
    """Test that endpoint returns empty events for nonexistent trip."""
    response = session_client.get("/api/trips/nonexistent-trip-12345/timeline")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["trip_id"] == "nonexistent-trip-12345"
    assert data["events"] == []


def test_timeline_endpoint_response_structure(session_client):
    """Test that the endpoint returns the correct response structure."""
    response = session_client.get("/api/trips/any-trip-id/timeline")
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify response structure
    assert "trip_id" in data
    assert "events" in data
    assert isinstance(data["trip_id"], str)
    assert isinstance(data["events"], list)


def test_timeline_endpoint_accepts_stage_filter(session_client):
    """Test that endpoint accepts stage query parameter."""
    response = session_client.get("/api/trips/test-trip/timeline?stage=decision")
    
    # Should not error
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)


def test_timeline_endpoint_valid_json(session_client):
    """Test that the endpoint returns valid JSON."""
    response = session_client.get("/api/trips/test-trip-json-check/timeline")
    
    assert response.status_code == 200
    
    # Should be parseable as JSON (already parsed by client.get)
    data = response.json()
    assert isinstance(data, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
