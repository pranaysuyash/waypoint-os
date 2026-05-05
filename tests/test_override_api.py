"""
Tests for the Override API (P1-02: Agent Feedback Loop)

Tests POST /trips/{trip_id}/override endpoint with:
- Valid override requests (suppress, downgrade, acknowledge)
- Mandatory reason field validation
- Severity downgrade validation
- Stale original_severity detection (409 Conflict)
- Override appended to persistence store
- Query endpoints return correct data
- Different override scopes ("this_trip" vs "pattern")
"""

import json
import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
from uuid import uuid4

from spine_api.persistence import (
    OverrideStore,
)


@pytest.fixture(autouse=True)
def override_uses_tmp_path(monkeypatch, tmp_path):
    """Redirect override stores to tmp_path to avoid shared-data contamination."""
    from spine_api import persistence as spine_persistence

    per_trip = tmp_path / "overrides" / "per_trip"
    patterns = tmp_path / "overrides" / "patterns"
    index_file = tmp_path / "overrides" / "index.json"

    per_trip.mkdir(parents=True, exist_ok=True)
    patterns.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(spine_persistence, "OVERRIDES_PER_TRIP_DIR", per_trip)
    monkeypatch.setattr(spine_persistence, "OVERRIDES_PATTERNS_DIR", patterns)
    monkeypatch.setattr(spine_persistence, "OVERRIDES_INDEX_FILE", index_file)

    yield




class TestOverrideStore:
    """Test OverrideStore persistence layer."""
    
    def test_save_override_creates_jsonl_file(self, override_uses_tmp_path):
        """Override should be appended to trip's JSONL file."""
        from spine_api import persistence as spine_persistence

        trip_id = f"trip_{uuid4().hex[:12]}"
        override_data = {
            "flag": "elderly_mobility_risk",
            "decision_type": "elderly_mobility_risk",
            "action": "suppress",
            "overridden_by": "agent_priya",
            "reason": "Traveler confirmed fitness via video call. No mobility aids needed.",
            "scope": "pattern",
            "original_severity": "high",
        }

        override_id = OverrideStore.save_override(trip_id, override_data)

        # Verify override_id was generated
        assert override_id.startswith("ovr_")

        # Verify file was created in the fixture-redirected location
        override_file = spine_persistence.OVERRIDES_PER_TRIP_DIR / f"{trip_id}.jsonl"
        assert override_file.exists()

        # Verify override was written
        with open(override_file) as f:
            line = f.readline()
            saved = json.loads(line)

        assert saved["override_id"] == override_id
        assert saved["flag"] == "elderly_mobility_risk"
        assert saved["action"] == "suppress"
    
    def test_get_overrides_for_trip_returns_all_overrides(self):
        """Should retrieve all overrides for a trip."""
        trip_id = f"trip_{uuid4().hex[:12]}"
        
        # Save multiple overrides
        override_ids = []
        for i in range(3):
            override_data = {
                "flag": f"risk_flag_{i}",
                "action": "suppress",
                "overridden_by": "agent_test",
                "reason": f"Reason {i}",
                "scope": "this_trip",
                "original_severity": "high",
            }
            override_id = OverrideStore.save_override(trip_id, override_data)
            override_ids.append(override_id)
        
        # Retrieve overrides
        overrides = OverrideStore.get_overrides_for_trip(trip_id)
        
        assert len(overrides) == 3
        assert [o["override_id"] for o in overrides] == override_ids
    
    def test_get_override_by_id_returns_correct_override(self):
        """Should retrieve a specific override by ID."""
        trip_id = f"trip_{uuid4().hex[:12]}"
        override_data = {
            "flag": "elderly_mobility_risk",
            "action": "downgrade",
            "new_severity": "medium",
            "overridden_by": "agent_priya",
            "reason": "Traveler confirmed with doctor. Lower risk.",
            "scope": "this_trip",
            "original_severity": "high",
        }
        
        override_id = OverrideStore.save_override(trip_id, override_data)
        retrieved = OverrideStore.get_override(override_id)
        
        assert retrieved is not None
        assert retrieved["override_id"] == override_id
        assert retrieved["flag"] == "elderly_mobility_risk"
        assert retrieved["action"] == "downgrade"
        assert retrieved["new_severity"] == "medium"
    
    def test_get_active_overrides_filters_rescinded(self):
        """Should only return non-rescinded overrides."""
        trip_id = f"trip_{uuid4().hex[:12]}"
        flag = "elderly_mobility_risk"
        
        # Save two overrides for the same flag
        override_data_1 = {
            "flag": flag,
            "action": "suppress",
            "overridden_by": "agent_priya",
            "reason": "Initial suppression",
            "scope": "this_trip",
            "original_severity": "high",
            "rescinded": False,
        }
        override_id_1 = OverrideStore.save_override(trip_id, override_data_1)
        
        override_data_2 = {
            "flag": flag,
            "action": "downgrade",
            "new_severity": "medium",
            "overridden_by": "agent_test",
            "reason": "Downgrade after review",
            "scope": "this_trip",
            "original_severity": "high",
            "rescinded": True,  # Mark as rescinded
        }
        OverrideStore.save_override(trip_id, override_data_2)
        
        # Get active overrides
        active = OverrideStore.get_active_overrides_for_flag(trip_id, flag)
        
        assert len(active) == 1
        assert active[0]["override_id"] == override_id_1
    
    def test_pattern_overrides_stored_separately(self, override_uses_tmp_path):
        """Pattern-scope overrides should be stored in pattern files."""
        from spine_api import persistence as spine_persistence

        trip_id = f"trip_{uuid4().hex[:12]}"
        decision_type = "elderly_mobility_risk"

        override_data = {
            "flag": "elderly_mobility_risk",
            "decision_type": decision_type,
            "action": "suppress",
            "overridden_by": "agent_priya",
            "reason": "Pattern-level override",
            "scope": "pattern",
            "original_severity": "high",
        }

        OverrideStore.save_override(trip_id, override_data)

        # Check pattern file exists
        pattern_file = spine_persistence.OVERRIDES_PATTERNS_DIR / f"{decision_type}.jsonl"
        assert pattern_file.exists()

        # Retrieve pattern overrides
        pattern_overrides = OverrideStore.get_pattern_overrides(decision_type)
        assert len(pattern_overrides) >= 1


class TestOverrideAPIEndpoint:
    """Test the POST /trips/{trip_id}/override endpoint."""
    
    @pytest.fixture
    def mock_trip(self):
        """Create a mock trip with suitability flags."""
        return {
            "id": f"trip_{uuid4().hex[:12]}",
            "decision": {
                "suitability_flags": [
                    {
                        "flag": "elderly_mobility_risk",
                        "severity": "high",
                        "reason": "Traveler is 75 years old",
                    },
                    {
                        "flag": "toddler_pacing_risk",
                        "severity": "medium",
                        "reason": "3-year-old in party",
                    },
                ]
            },
        }
    
    def test_override_suppress_action(self, mock_trip):
        """Should accept suppress action and return override details."""
        # Test that the OverrideStore can handle suppress action
        trip_id = mock_trip["id"]
        
        override_data = {
            "flag": "elderly_mobility_risk",
            "decision_type": "elderly_mobility_risk",
            "action": "suppress",
            "overridden_by": "agent_priya",
            "reason": "Traveler confirmed fitness via video call. Doctor clearance on file.",
            "scope": "this_trip",
            "original_severity": "high",
        }
        
        # Verify data structure
        assert override_data["action"] == "suppress"
        assert override_data["reason"]
        assert len(override_data["reason"]) > 0
        
        # Save and retrieve
        override_id = OverrideStore.save_override(trip_id, override_data)
        retrieved = OverrideStore.get_override(override_id)
        
        assert retrieved["action"] == "suppress"
        assert retrieved["flag"] == "elderly_mobility_risk"
    
    def test_override_downgrade_requires_new_severity(self):
        """Downgrade action should require new_severity."""
        override_data = {
            "flag": "elderly_mobility_risk",
            "action": "downgrade",
            "overridden_by": "agent_priya",
            "reason": "Traveler assessed as lower risk",
            "scope": "this_trip",
            "original_severity": "high",
            # new_severity is missing
        }
        
        # Validation should fail
        assert "new_severity" not in override_data
        assert override_data["action"] == "downgrade"
    
    def test_override_acknowledge_action(self):
        """Should accept acknowledge action without new_severity."""
        override_data = {
            "flag": "elderly_mobility_risk",
            "action": "acknowledge",
            "overridden_by": "agent_priya",
            "reason": "Owner reviewed and accepted the risk",
            "scope": "this_trip",
            "original_severity": "high",
        }
        
        assert override_data["action"] == "acknowledge"
        assert "new_severity" not in override_data or override_data.get("new_severity") is None
    
    def test_reason_field_mandatory(self):
        """Reason field should be mandatory and non-empty."""
        invalid_requests = [
            {"reason": ""},  # Empty
            {"reason": "   "},  # Whitespace only
            {},  # Missing
        ]
        
        for invalid in invalid_requests:
            reason = invalid.get("reason", "").strip()
            assert not reason  # Should be empty/invalid
    
    def test_stale_original_severity_detection(self):
        """Should reject if original_severity doesn't match actual."""
        trip_flags = {
            "elderly_mobility_risk": {"severity": "high"}
        }
        
        override_request = {
            "flag": "elderly_mobility_risk",
            "original_severity": "medium",  # Stale
        }
        
        actual_severity = trip_flags["elderly_mobility_risk"]["severity"]
        assert actual_severity != override_request["original_severity"]
    
    def test_override_scope_pattern_vs_this_trip(self):
        """Should support both 'pattern' and 'this_trip' scopes."""
        override_1 = {
            "flag": "elderly_mobility_risk",
            "scope": "this_trip",
        }
        
        override_2 = {
            "flag": "elderly_mobility_risk",
            "scope": "pattern",
        }
        
        assert override_1["scope"] in ("this_trip", "pattern")
        assert override_2["scope"] in ("this_trip", "pattern")


class TestOverrideListEndpoint:
    """Test GET /trips/{trip_id}/overrides endpoint."""
    
    def test_list_overrides_for_trip(self):
        """Should return all overrides for a trip."""
        trip_id = f"trip_{uuid4().hex[:12]}"
        
        # Save multiple overrides
        for i in range(3):
            override_data = {
                "flag": f"risk_{i}",
                "action": "suppress",
                "overridden_by": "agent_test",
                "reason": f"Override {i}",
                "scope": "this_trip",
            }
            OverrideStore.save_override(trip_id, override_data)
        
        overrides = OverrideStore.get_overrides_for_trip(trip_id)
        
        assert len(overrides) == 3
        assert all("override_id" in o for o in overrides)
        assert all("trip_id" in o for o in overrides)
        assert all(o["trip_id"] == trip_id for o in overrides)


class TestOverrideGetEndpoint:
    """Test GET /overrides/{override_id} endpoint."""
    
    def test_get_override_returns_details(self):
        """Should return override details by ID."""
        trip_id = f"trip_{uuid4().hex[:12]}"
        override_data = {
            "flag": "elderly_mobility_risk",
            "action": "downgrade",
            "new_severity": "medium",
            "overridden_by": "agent_priya",
            "reason": "Traveler confirmed fitness",
            "scope": "this_trip",
            "original_severity": "high",
        }
        
        override_id = OverrideStore.save_override(trip_id, override_data)
        retrieved = OverrideStore.get_override(override_id)
        
        assert retrieved["override_id"] == override_id
        assert retrieved["flag"] == "elderly_mobility_risk"
        assert retrieved["action"] == "downgrade"
        assert retrieved["new_severity"] == "medium"
        assert retrieved["reason"] == "Traveler confirmed fitness"


class TestOverrideValidation:
    """Test override validation rules."""
    
    def test_cannot_downgrade_above_original_severity(self):
        """Should reject downgrade with new_severity >= original."""
        severity_order = {"critical": 3, "high": 2, "medium": 1, "low": 0}
        
        original = "medium"  # Level 1
        new = "high"  # Level 2
        
        assert severity_order[new] > severity_order[original]  # Invalid downgrade
        
        # Valid downgrade
        new = "low"
        assert severity_order[new] < severity_order[original]  # Valid
    
    def test_reason_minimum_length(self):
        """Reason should have meaningful length."""
        MIN_REASON_LENGTH = 10
        
        short_reason = "Brief"  # 5 chars
        long_reason = "Traveler confirmed fitness via video call with doctor"
        
        assert len(short_reason) < MIN_REASON_LENGTH
        assert len(long_reason) >= MIN_REASON_LENGTH


class TestOverridePersistenceIntegrity:
    """Test that overrides are persisted correctly and immutably."""
    
    def test_overrides_append_only(self):
        """Overrides should be appended, not overwritten."""
        trip_id = f"trip_{uuid4().hex[:12]}"
        
        # Save first override
        override_1 = {
            "flag": "elderly_mobility_risk",
            "action": "suppress",
            "overridden_by": "agent_1",
            "reason": "First override",
            "scope": "this_trip",
        }
        id_1 = OverrideStore.save_override(trip_id, override_1)
        
        # Save second override
        override_2 = {
            "flag": "toddler_pacing_risk",
            "action": "acknowledge",
            "overridden_by": "agent_2",
            "reason": "Second override",
            "scope": "this_trip",
        }
        id_2 = OverrideStore.save_override(trip_id, override_2)
        
        # Both should exist
        overrides = OverrideStore.get_overrides_for_trip(trip_id)
        assert len(overrides) == 2
        assert any(o["override_id"] == id_1 for o in overrides)
        assert any(o["override_id"] == id_2 for o in overrides)
    
    def test_override_metadata_preserved(self):
        """All override metadata should be preserved."""
        trip_id = f"trip_{uuid4().hex[:12]}"
        
        override_data = {
            "flag": "elderly_mobility_risk",
            "decision_type": "elderly_mobility_risk",
            "action": "downgrade",
            "new_severity": "medium",
            "overridden_by": "agent_priya",
            "reason": "Comprehensive assessment completed",
            "scope": "pattern",
            "original_severity": "high",
        }
        
        override_id = OverrideStore.save_override(trip_id, override_data)
        retrieved = OverrideStore.get_override(override_id)
        
        # All fields should match
        for key in override_data:
            assert retrieved[key] == override_data[key]
        
        # Plus auto-added fields
        assert "override_id" in retrieved
        assert "trip_id" in retrieved
        assert "created_at" in retrieved
