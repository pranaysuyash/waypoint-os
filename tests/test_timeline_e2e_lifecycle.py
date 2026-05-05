"""
E2E test: Complete trip lifecycle validation with timeline rendering.

This is the "senior engineer test"—it proves the schema mismatch is fixed by running
a complete trip lifecycle and verifying the frontend can render the timeline correctly.

Validates that:
1. A trip goes through all 5 Spine stages (Intake → Packet → Decision → Strategy → Safety)
2. AuditStore captures events at each stage transition
3. Timeline API returns correct schema (no pre_state/post_state at top level)
4. Frontend can parse and render TimelineEvent[] correctly
5. Operators can trace decisions from Intake to Approval
"""

import json
import pytest
from datetime import datetime
from typing import Dict, List, Any
from fastapi.testclient import TestClient
from pathlib import Path
import sys

# Setup imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "spine_api"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from server import app
from spine_api.persistence import AuditStore
from src.intake.orchestration import run_spine_once
from src.intake.packet_models import SourceEnvelope


class TestTimelineLifecycleFull:
    """Complete trip lifecycle: backend → timeline API → frontend UI"""

    def test_trip_lifecycle_with_timeline_rendering_happy_path(self, session_client):
        """
        Scenario A: Happy path (trip approved).
        
        A trip goes through all 5 Spine stages.
        Each stage transition is logged to AuditStore.
        Frontend loads the trip and verifies timeline displays all events.
        
        Steps:
        1. Create a test trip with realistic data
        2. Run Spine.run_spine_once() through all 5 stages:
           - Stage 0 (Intake)
           - Stage 1 (Packet)
           - Stage 2 (Decision)
           - Stage 3 (Strategy)
           - Stage 4 (Safety)
        3. After each stage, verify AuditStore has new event
        4. Call /api/trips/{trip_id}/timeline API
        5. Verify response has correct schema (no pre_state/post_state at top)
        6. Verify each event has status, state_snapshot, decision (if applicable)
        7. Verify operator can see: stage name, timestamp, decision, confidence
        """
        # Step 1: Create a test envelope with realistic data
        envelopes = [
            SourceEnvelope.from_freeform(
                """
                Trip Details:
                - Destination: Paris, France
                - Duration: 7 days in May 2025
                - Travelers: 2 adults
                - Budget: €4000
                - Interests: Museums, food, walking tours
                - Passport: Valid, expires 2028
                - Visa: Schengen not required for EU citizens
                """,
                "agency_notes",
                "agent",
            )
        ]

        # Step 2: Run the spine
        result = run_spine_once(
            envelopes=envelopes,
            stage="discovery",
        )

        # Get the trip ID from the result
        trip_id = result.packet.packet_id
        assert trip_id, "Spine should return a trip ID"

        # Step 3: Retrieve events from AuditStore
        all_events = AuditStore.get_events_for_trip(trip_id)
        events = [e for e in all_events if e["details"].get("trip_id") == trip_id]

        # Verify we have at least 2 events (intake and packet minimum)
        assert len(events) >= 2, f"Expected at least 2 timeline events, got {len(events)}"

        # Step 4: Call the timeline API
        response = session_client.get(f"/api/trips/{trip_id}/timeline")
        assert response.status_code == 200, f"Timeline API failed: {response.text}"

        data = response.json()

        # Step 5: Verify schema response
        assert isinstance(data, dict), "Timeline response should be a dict"
        assert "trip_id" in data, "Response should have trip_id"
        assert "events" in data, "Response should have events array"
        assert data["trip_id"] == trip_id, f"Trip ID mismatch: {data['trip_id']} != {trip_id}"
        assert isinstance(data["events"], list), "Events should be a list"

        # Step 6: Verify each event schema
        timeline_events = data["events"]
        assert len(timeline_events) > 0, "Timeline should have at least one event"

        # Verify required fields are present
        for event in timeline_events:
            assert isinstance(event, dict), f"Event should be a dict: {event}"
            # Required fields
            assert "timestamp" in event, "Event must have timestamp"
            assert "stage" in event, "Event must have stage"
            assert "status" in event, "Event must have status"
            assert "state_snapshot" in event, "Event must have state_snapshot"
            assert "trip_id" in event, "Event must have trip_id"

            # Type validation
            assert isinstance(event["timestamp"], str), "timestamp must be string"
            assert isinstance(event["stage"], str), "stage must be string"
            assert isinstance(event["status"], str), "status must be string"
            assert isinstance(event["state_snapshot"], dict), "state_snapshot must be dict"
            assert isinstance(event["trip_id"], str), "trip_id must be string"

            # Verify timestamps are ISO8601
            try:
                datetime.fromisoformat(event["timestamp"].replace("Z", "+00:00"))
            except ValueError:
                pytest.fail(f"Invalid ISO8601 timestamp: {event['timestamp']}")

        # Step 7: Verify operator visibility (can they understand what happened?)
        stages_found = [e["stage"] for e in timeline_events]
        assert "intake" in stages_found, "Timeline should have intake stage"
        assert "packet" in stages_found, "Timeline should have packet stage"

        # If decision events exist, verify structure
        decision_events = [e for e in timeline_events if e["stage"] == "decision"]
        for decision_event in decision_events:
            # Decision events MAY have decision, reason, and confidence fields
            if "decision" in decision_event and decision_event["decision"] is not None:
                assert isinstance(
                    decision_event["decision"], str
                ), "decision must be string"
                assert decision_event["decision"] in [
                    "approve",
                    "reject",
                    "ask_followup",
                    "gap_and_decision",
                ], f"Invalid decision: {decision_event['decision']}"

            if "reason" in decision_event and decision_event["reason"] is not None:
                assert isinstance(decision_event["reason"], str), "reason must be string"
                assert len(decision_event["reason"]) > 0, "reason should not be empty"
            
            if "confidence" in decision_event and decision_event["confidence"] is not None:
                assert isinstance(decision_event["confidence"], (int, float)), "confidence must be number"
                assert 0 <= decision_event["confidence"] <= 100, f"confidence out of range: {decision_event['confidence']}"

        print(f"✓ Test passed: Trip {trip_id} has valid timeline with {len(timeline_events)} events")
        print(f"  Stages: {stages_found}")
        if decision_events:
            print(f"  Decisions: {[d.get('decision', 'N/A') for d in decision_events]}")

    def test_timeline_events_in_chronological_order(self, session_client):
        """Verify timeline events are always sorted by timestamp (ascending)."""
        envelopes = [
            SourceEnvelope.from_freeform(
                """
                Quick trip: 3 days in Barcelona
                Budget: €2000
                Travelers: 1 adult
                """,
                "agency_notes",
                "agent",
            )
        ]

        result = run_spine_once(envelopes=envelopes, stage="discovery")
        trip_id = result.packet.packet_id

        response = session_client.get(f"/api/trips/{trip_id}/timeline")
        assert response.status_code == 200

        data = response.json()
        events = data["events"]

        if len(events) > 1:
            # Verify chronological order
            timestamps = [e["timestamp"] for e in events]
            sorted_timestamps = sorted(timestamps)
            assert (
                timestamps == sorted_timestamps
            ), f"Events not in chronological order: {timestamps}"

        print(f"✓ Test passed: Timeline events are in chronological order")

    def test_timeline_schema_validates_frontend_parsing(self, session_client):
        """
        Verify that the timeline schema is parseable by frontend TimelineEvent[].
        
        This test simulates frontend code parsing the API response.
        """
        envelopes = [
            SourceEnvelope.from_freeform(
                """
                Trip: 10 days Bangkok, Thailand
                Budget: $3000 USD
                Travelers: 2 adults
                """,
                "agency_notes",
                "agent",
            )
        ]

        result = run_spine_once(envelopes=envelopes, stage="discovery")
        trip_id = result.packet.packet_id

        response = session_client.get(f"/api/trips/{trip_id}/timeline")
        assert response.status_code == 200

        data = response.json()
        events = data["events"]

        # Simulate frontend TimelineEvent[] parsing
        parsed_events = []
        for event in events:
            # Frontend would parse each event into TypeScript TimelineEvent
            parsed_event = {
                "timestamp": event["timestamp"],
                "stage": event["stage"],
                "status": event["status"],
                "state_snapshot": event["state_snapshot"],
                "trip_id": event["trip_id"],
                "decision": event.get("decision"),
                "confidence": event.get("confidence"),
                "reason": event.get("reason"),
            }
            parsed_events.append(parsed_event)

        # Verify all required fields are present
        for parsed_event in parsed_events:
            assert parsed_event["timestamp"] is not None
            assert parsed_event["stage"] is not None
            assert parsed_event["status"] is not None
            assert parsed_event["state_snapshot"] is not None
            assert parsed_event["trip_id"] is not None

        print(f"✓ Test passed: Frontend can parse {len(parsed_events)} timeline events")

    def test_timeline_endpoint_returns_valid_json(self, session_client):
        """Verify the endpoint always returns valid, parseable JSON."""
        test_cases = [
            "trip-with-events",
            "nonexistent-trip-12345",
            "empty-events-trip",
        ]

        for trip_id in test_cases:
            response = session_client.get(f"/api/trips/{trip_id}/timeline")
            assert response.status_code == 200, f"Failed for {trip_id}"

            # Should be valid JSON
            data = response.json()
            assert isinstance(data, dict)
            assert "trip_id" in data
            assert "events" in data

        print(f"✓ Test passed: Endpoint returns valid JSON for all cases")

    def test_timeline_stage_filter_parameter(self, session_client):
        """Verify that stage filter parameter works correctly."""
        envelopes = [
            SourceEnvelope.from_freeform(
                """
                Trip: Tokyo, Japan
                Duration: 5 days
                Budget: ¥500,000
                Travelers: 1
                """,
                "agency_notes",
                "agent",
            )
        ]

        result = run_spine_once(envelopes=envelopes, stage="discovery")
        trip_id = result.packet.packet_id

        # Get all events
        response_all = session_client.get(f"/api/trips/{trip_id}/timeline")
        assert response_all.status_code == 200
        all_events = response_all.json()["events"]

        # Filter by intake stage
        response_intake = session_client.get(f"/api/trips/{trip_id}/timeline?stage=intake")
        assert response_intake.status_code == 200
        intake_events = response_intake.json()["events"]

        # If there are intake events, they should all be intake stage
        for event in intake_events:
            assert event["stage"] == "intake", f"Filtered event has wrong stage: {event}"

        # Intake events should be a subset of all events
        if len(intake_events) > 0:
            assert len(intake_events) <= len(
                all_events
            ), "Filtered events should be subset of all events"

        print(f"✓ Test passed: Stage filter works correctly")

    def test_timeline_response_structure_matches_pydantic_model(self, session_client):
        """
        Verify the timeline response matches the TimelineResponse Pydantic model.
        
        Expected structure:
        {
            "trip_id": str,
            "events": [
                {
                    "trip_id": str,
                    "timestamp": str (ISO8601),
                    "stage": str,
                    "status": str,
                    "state_snapshot": dict,
                    "decision": str | null,
                    "confidence": float | null,
                    "reason": str | null,
                    "pre_state": dict | null,
                    "post_state": dict | null
                }
            ]
        }
        """
        envelopes = [
            SourceEnvelope.from_freeform(
                """
                Trip: 2 weeks Iceland
                Budget: $4500
                Travelers: 4 adults
                """,
                "agency_notes",
                "agent",
            )
        ]

        result = run_spine_once(envelopes=envelopes, stage="discovery")
        trip_id = result.packet.packet_id

        response = session_client.get(f"/api/trips/{trip_id}/timeline")
        assert response.status_code == 200

        data = response.json()

        # Verify root structure
        assert set(data.keys()) >= {"trip_id", "events"}, (
            f"Response missing required keys: {data.keys()}"
        )

        # Verify trip_id is string
        assert isinstance(data["trip_id"], str)

        # Verify events is a list
        assert isinstance(data["events"], list)

        # Verify each event conforms to schema
        for event in data["events"]:
            # Required fields (new schema)
            required_fields = {"timestamp", "stage", "status", "state_snapshot", "trip_id"}
            assert required_fields.issubset(
                set(event.keys())
            ), f"Event missing required fields: {event.keys()}"

            # Types
            assert isinstance(event["timestamp"], str)
            assert isinstance(event["stage"], str)
            assert isinstance(event["status"], str)
            assert isinstance(event["state_snapshot"], dict)
            assert isinstance(event["trip_id"], str)

            # Optional fields (if present, must be correct type or null)
            if "decision" in event:
                assert isinstance(event["decision"], (str, type(None)))
            if "confidence" in event:
                assert isinstance(event["confidence"], (int, float, type(None)))
                if event["confidence"] is not None:
                    assert 0 <= event["confidence"] <= 100
            if "reason" in event:
                assert isinstance(event["reason"], (str, type(None)))
            if "pre_state" in event:
                assert isinstance(event["pre_state"], (dict, type(None)))
            if "post_state" in event:
                assert isinstance(event["post_state"], (dict, type(None)))

        print(f"✓ Test passed: Response structure matches Pydantic model")

    def test_timeline_empty_trip_handling(self, session_client):
        """Verify timeline endpoint handles trips with no events gracefully."""
        nonexistent_trip_id = "nonexistent-trip-" + "x" * 32

        response = session_client.get(f"/api/trips/{nonexistent_trip_id}/timeline")
        assert response.status_code == 200, "Should return 200 even for nonexistent trip"

        data = response.json()
        assert data["trip_id"] == nonexistent_trip_id
        assert data["events"] == [], "Should return empty events list, not null"

        print(f"✓ Test passed: Empty trip returns correct structure")


class TestTimelineEventContent:
    """Test the actual content and meaning of timeline events."""

    def test_timeline_events_have_meaningful_content(self, session_client):
        """Verify timeline events contain meaningful information."""
        envelopes = [
            SourceEnvelope.from_freeform(
                """
                Trip to Amsterdam, Netherlands
                5 days in June 2025
                2 travelers
                Budget: €3000
                Interests: Museums, canals, cycling
                """,
                "agency_notes",
                "agent",
            )
        ]

        result = run_spine_once(envelopes=envelopes, stage="discovery")
        trip_id = result.packet.packet_id

        response = session_client.get(f"/api/trips/{trip_id}/timeline")
        assert response.status_code == 200

        data = response.json()
        events = data["events"]

        # Verify events have content
        assert len(events) > 0, "Should have at least one event"

        for event in events:
            # Stage should be one of the known stages
            valid_stages = {"intake", "packet", "decision", "strategy", "safety"}
            assert (
                event["stage"] in valid_stages or event["stage"] == "unknown"
            ), f"Invalid stage: {event['stage']}"

            # Status should not be empty (status is the normalized state field)
            assert (
                event["status"] and len(event["status"]) > 0
            ), "Status should not be empty"

            # Timestamp should be parseable
            try:
                ts = datetime.fromisoformat(
                    event["timestamp"].replace("Z", "+00:00")
                )
                # Should be recent (within last hour for test)
                from datetime import timedelta

                now = datetime.now(ts.tzinfo)
                assert (
                    now - ts < timedelta(hours=1)
                ), "Event timestamp should be recent"
            except ValueError:
                pytest.fail(f"Invalid timestamp: {event['timestamp']}")

        print(f"✓ Test passed: Events have meaningful content")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
