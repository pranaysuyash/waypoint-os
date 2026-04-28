"""
Tests for the Suitability API endpoint (Phase 3)

Tests GET /trips/{trip_id}/suitability endpoint with:
- Fetching suitability flags for a trip
- Confidence score conversion (0-1 to 0-100)
- Tier classification (critical, high, medium, low)
- Missing trip handling (404)
- Empty suitability flags response
- Multiple flags with different severity levels
"""

import json
import pytest
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
from uuid import uuid4

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "spine_api"))
sys.path.insert(0, str(PROJECT_ROOT))

# Set privacy mode to test to allow saving synthetic data
os.environ["DATA_PRIVACY_MODE"] = "test"

from spine_api.persistence import TripStore, TRIPS_DIR
import shutil


@pytest.fixture(autouse=True)
def setup_test_db():
    """Setup test database and cleanup."""
    # Create fresh database
    if TRIPS_DIR.exists():
        shutil.rmtree(TRIPS_DIR)
    TRIPS_DIR.mkdir(parents=True, exist_ok=True)
    
    yield
    
    # Cleanup after test
    if TRIPS_DIR.exists():
        shutil.rmtree(TRIPS_DIR)


def make_trip_data(trip_id: str, agency_id: str, **overrides) -> dict:
    """Create a valid trip data dict with synthetic fixture marker."""
    data = {
        "id": trip_id,
        "agency_id": agency_id,
        "status": "new",
        "raw_input": {
            "fixture_id": f"test_fixture_{uuid4().hex[:8]}",
        },
        "decision_output": None,
        "created_at": "2026-04-23T10:00:00Z",
    }
    data.update(overrides)
    return data


class TestGetTripSuitabilityEndpoint:
    """Test GET /trips/{trip_id}/suitability endpoint."""
    
    def test_get_suitability_returns_empty_flags_for_new_trip(self, session_client):
        """Test fetching suitability flags for a trip with no decision output."""
        trip_id = f"trip_{uuid4().hex[:12]}"
        agency_id = "d1e3b2b6-5509-4c27-b123-4b1e02b0bf5b"  # From conftest
        
        # Create a trip with no decision output
        trip_data = make_trip_data(trip_id, agency_id)
        TripStore.save_trip(trip_data)
        
        response = session_client.get(f"/trips/{trip_id}/suitability")
        
        assert response.status_code == 200
        data = response.json()
        assert data["trip_id"] == trip_id
        assert data["suitability_flags"] == []
    
    def test_get_suitability_returns_404_for_missing_trip(self, session_client):
        """Test fetching suitability flags for non-existent trip."""
        trip_id = "trip_nonexistent_12345"
        
        response = session_client.get(f"/trips/{trip_id}/suitability")
        
        assert response.status_code == 404
        assert "Trip not found" in response.json()["detail"]
    
    def test_get_suitability_returns_single_flag(self, session_client):
        """Test fetching suitability flags with a single flag."""
        trip_id = f"trip_{uuid4().hex[:12]}"
        agency_id = "d1e3b2b6-5509-4c27-b123-4b1e02b0bf5b"
        
        # Create a trip with decision output containing a suitability flag
        trip_data = make_trip_data(
            trip_id,
            agency_id,
            status="in_progress",
            decision_output={
                "suitability_flags": [
                    {
                        "flag_type": "elderly_mobility_risk",
                        "severity": "critical",
                        "reason": "Parent age >70 with high-intensity trekking",
                        "confidence": 0.85,
                    }
                ]
            }
        )
        TripStore.save_trip(trip_data)
        
        response = session_client.get(f"/trips/{trip_id}/suitability")
        
        assert response.status_code == 200
        data = response.json()
        assert data["trip_id"] == trip_id
        assert len(data["suitability_flags"]) == 1
        
        flag = data["suitability_flags"][0]
        assert flag["name"] == "elderly_mobility_risk"
        assert flag["tier"] == "critical"
        assert flag["confidence"] == 85  # 0.85 * 100 = 85
        assert "Parent age >70" in flag["reason"]
    
    def test_get_suitability_converts_confidence_to_percentage(self, session_client):
        """Test that confidence is converted from 0-1 to 0-100."""
        trip_id = f"trip_{uuid4().hex[:12]}"
        agency_id = "d1e3b2b6-5509-4c27-b123-4b1e02b0bf5b"
        
        trip_data = make_trip_data(
            trip_id,
            agency_id,
            status="in_progress",
            decision_output={
                "suitability_flags": [
                    {
                        "flag_type": "visa_risk",
                        "severity": "high",
                        "reason": "5 nationalities",
                        "confidence": 0.6,
                    }
                ]
            }
        )
        TripStore.save_trip(trip_data)
        
        response = session_client.get(f"/trips/{trip_id}/suitability")
        
        assert response.status_code == 200
        data = response.json()
        flag = data["suitability_flags"][0]
        assert flag["confidence"] == 60  # 0.6 * 100
    
    def test_get_suitability_returns_multiple_flags(self, session_client):
        """Test fetching multiple suitability flags."""
        trip_id = f"trip_{uuid4().hex[:12]}"
        agency_id = "d1e3b2b6-5509-4c27-b123-4b1e02b0bf5b"
        
        trip_data = make_trip_data(
            trip_id,
            agency_id,
            status="in_progress",
            decision_output={
                "suitability_flags": [
                    {
                        "flag_type": "elderly_mobility_risk",
                        "severity": "critical",
                        "reason": "Elderly traveler",
                        "confidence": 0.85,
                    },
                    {
                        "flag_type": "visa_processing_risk",
                        "severity": "high",
                        "reason": "Multiple nationalities",
                        "confidence": 0.60,
                    },
                    {
                        "flag_type": "child_safety_concern",
                        "severity": "medium",
                        "reason": "Young child",
                        "confidence": 0.50,
                    },
                ]
            }
        )
        TripStore.save_trip(trip_data)
        
        response = session_client.get(f"/trips/{trip_id}/suitability")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["suitability_flags"]) == 3
        
        # Verify flags are in correct order and have correct data
        flags = data["suitability_flags"]
        assert flags[0]["name"] == "elderly_mobility_risk"
        assert flags[0]["confidence"] == 85
        assert flags[1]["name"] == "visa_processing_risk"
        assert flags[1]["confidence"] == 60
        assert flags[2]["name"] == "child_safety_concern"
        assert flags[2]["confidence"] == 50
    
    def test_get_suitability_tier_classification(self, session_client):
        """Test that tier is correctly set from severity."""
        trip_id = f"trip_{uuid4().hex[:12]}"
        agency_id = "d1e3b2b6-5509-4c27-b123-4b1e02b0bf5b"
        
        trip_data = make_trip_data(
            trip_id,
            agency_id,
            status="in_progress",
            decision_output={
                "suitability_flags": [
                    {
                        "flag_type": "critical_flag",
                        "severity": "critical",
                        "reason": "Critical",
                        "confidence": 0.95,
                    },
                    {
                        "flag_type": "high_flag",
                        "severity": "high",
                        "reason": "High",
                        "confidence": 0.80,
                    },
                    {
                        "flag_type": "medium_flag",
                        "severity": "medium",
                        "reason": "Medium",
                        "confidence": 0.70,
                    },
                    {
                        "flag_type": "low_flag",
                        "severity": "low",
                        "reason": "Low",
                        "confidence": 0.50,
                    },
                ]
            }
        )
        TripStore.save_trip(trip_data)
        
        response = session_client.get(f"/trips/{trip_id}/suitability")
        
        assert response.status_code == 200
        data = response.json()
        flags = data["suitability_flags"]
        
        assert flags[0]["tier"] == "critical"
        assert flags[1]["tier"] == "high"
        assert flags[2]["tier"] == "medium"
        assert flags[3]["tier"] == "low"
    
    def test_get_suitability_includes_trip_id_in_each_flag(self, session_client):
        """Test that each flag includes the trip_id."""
        trip_id = f"trip_{uuid4().hex[:12]}"
        agency_id = "d1e3b2b6-5509-4c27-b123-4b1e02b0bf5b"
        
        trip_data = make_trip_data(
            trip_id,
            agency_id,
            status="in_progress",
            decision_output={
                "suitability_flags": [
                    {
                        "flag_type": "test_flag",
                        "severity": "high",
                        "reason": "Test",
                        "confidence": 0.75,
                    }
                ]
            }
        )
        TripStore.save_trip(trip_data)
        
        response = session_client.get(f"/trips/{trip_id}/suitability")
        
        assert response.status_code == 200
        data = response.json()
        flag = data["suitability_flags"][0]
        assert flag["trip_id"] == trip_id
    
    def test_get_suitability_includes_created_at_timestamp(self, session_client):
        """Test that suitability flags include created_at timestamp."""
        trip_id = f"trip_{uuid4().hex[:12]}"
        agency_id = "d1e3b2b6-5509-4c27-b123-4b1e02b0bf5b"
        created_at = "2026-04-23T10:00:00Z"
        
        trip_data = make_trip_data(
            trip_id,
            agency_id,
            status="in_progress",
            created_at=created_at,
            decision_output={
                "suitability_flags": [
                    {
                        "flag_type": "test_flag",
                        "severity": "high",
                        "reason": "Test",
                        "confidence": 0.75,
                    }
                ]
            }
        )
        TripStore.save_trip(trip_data)
        
        response = session_client.get(f"/trips/{trip_id}/suitability")
        
        assert response.status_code == 200
        data = response.json()
        flag = data["suitability_flags"][0]
        assert flag["created_at"] == created_at


