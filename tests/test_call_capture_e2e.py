"""
End-to-end integration tests for Unit-1 call-capture feature.

Phase 5: Test the full call-capture journey:
1. User captures a call via CaptureCallPanel
2. Form submission creates a trip with follow_up_due_date
3. Trip is persisted and retrievable via storage
4. User can PATCH follow_up_due_date later
5. Field persists across round-trips and multiple updates

This test suite validates:
- Trips can be created with follow_up_due_date via persistence layer
- Trips can be retrieved with follow_up_due_date in response
- PATCH can update follow_up_due_date
- follow_up_due_date values are ISO-8601 formatted timestamps
- Multiple trips can have independent follow_up_due_dates
- Field survives updates to other fields

Run: uv run python -m pytest tests/test_call_capture_e2e.py -v
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import pytest
import uuid


class TestCallCaptureFollowUpDueDate:
    """End-to-end tests for call-capture follow_up_due_date feature."""

    @staticmethod
    def _create_trip_directly(
        follow_up_due_date: Optional[str] = None,
        raw_note: str = "Customer called for Singapore family trip",
    ) -> str:
        """
        Helper to create a trip directly using the persistence layer.
        
        This simulates the flow:
        1. User captures call in CaptureCallPanel
        2. Form submission creates trip with follow_up_due_date
        3. Trip is persisted with all fields
        
        Returns the created trip_id.
        """
        from spine_api.persistence import save_processed_trip
        
        # Simulate minimal spine output (what would come from run_spine_once)
        spine_output = {
            "run_id": str(uuid.uuid4()),
            "packet": {
                "raw_input": raw_note,
                "traveler_name": "Ravi Patel",
                "destination": "Singapore",
                "trip_dates": "2026-06-01 to 2026-06-15",
            },
            "validation": {"valid": True},
            "decision": {"decision_type": "accept"},
            "meta": {"stage": "discovery"},
        }
        
        # Create trip with follow_up_due_date support
        trip_id = save_processed_trip(
            spine_output,
            source="intake_panel",
            agency_id="d1e3b2b6-5509-4c27-b123-4b1e02b0bf5b",
            follow_up_due_date=follow_up_due_date,
            trip_status="new"
        )
        
        return trip_id

    @staticmethod
    def _get_trip_from_disk(trip_id: str) -> Optional[Dict[str, Any]]:
        """Helper to retrieve a trip from disk."""
        from spine_api.persistence import TripStore
        return TripStore.get_trip(trip_id)

    @staticmethod
    def _update_trip_on_disk(trip_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Helper to update a trip on disk."""
        from spine_api.persistence import TripStore
        return TripStore.update_trip(trip_id, updates)

    def test_capture_call_creates_trip_with_follow_up_due_date(self, disable_audit_logging):
        """Test: Create trip with follow_up_due_date via call capture."""
        follow_up_time = datetime.now(timezone.utc) + timedelta(hours=48)
        follow_up_due_date = follow_up_time.isoformat()
        
        trip_id = self._create_trip_directly(
            follow_up_due_date=follow_up_due_date,
            raw_note="Customer Ravi called about Singapore trip. Promised follow-up in 48 hours.",
        )
        
        assert trip_id.startswith("trip_"), "Trip ID should be generated"
        
        trip = self._get_trip_from_disk(trip_id)
        assert trip is not None, "Trip should be retrievable"
        assert trip.get("follow_up_due_date") == follow_up_due_date
        assert trip.get("status") == "new"

    def test_captured_trip_retrieved_via_get(self, disable_audit_logging):
        """Test: Captured trip is retrievable and has correct fields."""
        follow_up_time = datetime.now(timezone.utc) + timedelta(hours=72)
        follow_up_due_date = follow_up_time.isoformat()
        raw_note = "Toddler-friendly Singapore itinerary needed"
        
        trip_id = self._create_trip_directly(
            follow_up_due_date=follow_up_due_date,
            raw_note=raw_note,
        )
        
        retrieved_trip = self._get_trip_from_disk(trip_id)
        assert retrieved_trip is not None
        assert retrieved_trip.get("id") == trip_id
        assert retrieved_trip.get("follow_up_due_date") == follow_up_due_date
        
        extracted = retrieved_trip.get("extracted", {})
        assert extracted.get("traveler_name") == "Ravi Patel"
        assert extracted.get("destination") == "Singapore"

    def test_patch_follow_up_due_date_on_existing_trip(self, disable_audit_logging):
        """Test: Can update follow_up_due_date on existing trip."""
        initial_time = datetime.now(timezone.utc) + timedelta(hours=48)
        initial_follow_up = initial_time.isoformat()
        
        trip_id = self._create_trip_directly(follow_up_due_date=initial_follow_up)
        
        trip = self._get_trip_from_disk(trip_id)
        assert trip.get("follow_up_due_date") == initial_follow_up
        
        new_time = datetime.now(timezone.utc) + timedelta(hours=72)
        new_follow_up = new_time.isoformat()
        
        patched_trip = self._update_trip_on_disk(trip_id, {"follow_up_due_date": new_follow_up})
        assert patched_trip.get("follow_up_due_date") == new_follow_up
        
        retrieved_trip = self._get_trip_from_disk(trip_id)
        assert retrieved_trip.get("follow_up_due_date") == new_follow_up

    def test_patch_follow_up_due_date_with_null_clears_field(self, disable_audit_logging):
        """Test: PATCH with null follow_up_due_date clears the field."""
        follow_up_time = datetime.now(timezone.utc) + timedelta(hours=48)
        follow_up_due_date = follow_up_time.isoformat()
        
        trip_id = self._create_trip_directly(follow_up_due_date=follow_up_due_date)
        
        trip = self._get_trip_from_disk(trip_id)
        assert trip.get("follow_up_due_date") == follow_up_due_date
        
        patched_trip = self._update_trip_on_disk(trip_id, {"follow_up_due_date": None})
        assert patched_trip.get("follow_up_due_date") is None
        
        retrieved_trip = self._get_trip_from_disk(trip_id)
        assert retrieved_trip.get("follow_up_due_date") is None

    def test_multiple_trips_can_have_different_follow_up_dates(self, disable_audit_logging):
        """Test: Multiple trips maintain independent follow_up_due_dates."""
        time_a = datetime.now(timezone.utc) + timedelta(hours=48)
        follow_up_a = time_a.isoformat()
        
        trip_a_id = self._create_trip_directly(
            follow_up_due_date=follow_up_a,
            raw_note="Trip A: Singapore family (48h follow-up)",
        )
        
        time_b = datetime.now(timezone.utc) + timedelta(hours=72)
        follow_up_b = time_b.isoformat()
        
        trip_b_id = self._create_trip_directly(
            follow_up_due_date=follow_up_b,
            raw_note="Trip B: Tokyo business (72h follow-up)",
        )
        
        trip_a = self._get_trip_from_disk(trip_a_id)
        assert trip_a.get("follow_up_due_date") == follow_up_a
        
        trip_b = self._get_trip_from_disk(trip_b_id)
        assert trip_b.get("follow_up_due_date") == follow_up_b
        
        assert follow_up_a != follow_up_b

    def test_follow_up_due_date_survives_round_trip(self, disable_audit_logging):
        """Test: follow_up_due_date survives full round-trip."""
        original_time = "2026-05-15T14:30:00+00:00"
        
        trip_id = self._create_trip_directly(follow_up_due_date=original_time)
        
        trip_1 = self._get_trip_from_disk(trip_id)
        value_1 = trip_1.get("follow_up_due_date")
        assert value_1 is not None
        
        patched = self._update_trip_on_disk(trip_id, {"follow_up_due_date": value_1})
        assert patched is not None
        
        trip_2 = self._get_trip_from_disk(trip_id)
        value_2 = trip_2.get("follow_up_due_date")
        
        assert value_2 == value_1

    def test_raw_note_and_follow_up_due_date_together(self, disable_audit_logging):
        """Test: raw_note and follow_up_due_date are both present and independent."""
        raw_note = "Customer Ravi called: Wants toddler-friendly itinerary for Singapore"
        follow_up_time = datetime.now(timezone.utc) + timedelta(hours=48)
        follow_up_due_date = follow_up_time.isoformat()
        
        trip_id = self._create_trip_directly(
            follow_up_due_date=follow_up_due_date,
            raw_note=raw_note,
        )
        
        trip_1 = self._get_trip_from_disk(trip_id)
        
        extracted_1 = trip_1.get("extracted", {})
        assert extracted_1.get("raw_input") == raw_note
        assert trip_1.get("follow_up_due_date") == follow_up_due_date
        
        new_follow_up_time = datetime.now(timezone.utc) + timedelta(hours=96)
        new_follow_up = new_follow_up_time.isoformat()
        
        patched = self._update_trip_on_disk(trip_id, {"follow_up_due_date": new_follow_up})
        assert patched is not None
        
        trip_2 = self._get_trip_from_disk(trip_id)
        
        extracted_2 = trip_2.get("extracted", {})
        assert extracted_2.get("raw_input") == raw_note
        assert trip_2.get("follow_up_due_date") == new_follow_up

    def test_follow_up_due_date_iso8601_format_validation(self, disable_audit_logging):
        """Test: follow_up_due_date accepts valid ISO-8601 formats."""
        valid_timestamps = [
            "2026-04-29T14:30:00+00:00",
            "2026-04-29T14:30:00Z",
            "2026-04-29T14:30:00.000000+00:00",
        ]
        
        for i, timestamp in enumerate(valid_timestamps):
            trip_id = self._create_trip_directly(
                follow_up_due_date=timestamp,
                raw_note=f"Test ISO format {i+1}",
            )
            
            trip = self._get_trip_from_disk(trip_id)
            assert trip is not None
            assert trip.get("follow_up_due_date") is not None

    def test_trip_creation_without_follow_up_due_date(self, disable_audit_logging):
        """Test: Trips can be created without follow_up_due_date (backward compatibility)."""
        trip_id = self._create_trip_directly(
            follow_up_due_date=None,
            raw_note="One-time inquiry, no follow-up needed",
        )
        
        trip = self._get_trip_from_disk(trip_id)
        assert trip is not None
        assert trip.get("id") == trip_id
        assert trip.get("follow_up_due_date") is None
        
        follow_up_time = datetime.now(timezone.utc) + timedelta(hours=48)
        follow_up_due_date = follow_up_time.isoformat()
        
        patched = self._update_trip_on_disk(trip_id, {"follow_up_due_date": follow_up_due_date})
        assert patched is not None
        
        trip_2 = self._get_trip_from_disk(trip_id)
        assert trip_2.get("follow_up_due_date") == follow_up_due_date
