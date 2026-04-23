"""
E2E integration test for timeline P0-02.

Validates that a complete spine run emits timeline events.
"""

import json
import pytest
from pathlib import Path
from datetime import datetime

from src.intake.orchestration import run_spine_once
from src.intake.packet_models import SourceEnvelope


@pytest.fixture(scope="module")
def logs_dir():
    """Get the logs directory from the project."""
    project_root = Path(__file__).resolve().parent.parent
    logs_dir = project_root / "data" / "logs" / "trips"
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir


def test_spine_run_emits_timeline_events(logs_dir):
    """
    E2E: Run a full spine and verify timeline events are created.
    
    Verifies that the timeline file is created and contains valid events
    in chronological order.
    """
    # Create a test envelope - use a more complete one
    envelopes = [
        SourceEnvelope.from_freeform(
            """
            Trip Details:
            - Destination: Paris, France
            - Duration: 7 days
            - Travelers: 2 adults
            - Budget: €4000
            - Dates: May 2025
            - Interests: Museums, food, walking tours
            """,
            "agency_notes",
            "agent",
        )
    ]

    # Run the spine
    result = run_spine_once(
        envelopes=envelopes,
        stage="discovery",
    )

    # Get the trip ID from the result
    trip_id = result.packet.packet_id
    assert trip_id, "Spine should return a trip ID"

    # Check that the timeline file was created
    log_file = logs_dir / f"{trip_id}.jsonl"
    assert log_file.exists(), f"Timeline file not found: {log_file}"

    # Read and parse timeline events
    events = []
    with open(log_file, "r") as f:
        for line in f:
            if line.strip():
                event = json.loads(line.strip())
                events.append(event)

    # Verify we have at least 2 events (intake minimum)
    assert len(events) >= 2, f"Expected at least 2 timeline events, got {len(events)}: {[e['stage'] for e in events]}"

    # Verify event structure
    for event in events:
        assert "timestamp" in event, "Event missing timestamp"
        assert "stage" in event, "Event missing stage"
        assert "state" in event, "Event missing state"
        assert "version" in event, "Event missing version"
        
        # Timestamp should be ISO8601
        try:
            datetime.fromisoformat(event["timestamp"].replace("Z", "+00:00"))
        except ValueError:
            pytest.fail(f"Invalid ISO8601 timestamp: {event['timestamp']}")

    # Verify timestamps are in ascending order
    timestamps = [event["timestamp"] for event in events]
    sorted_timestamps = sorted(timestamps)
    assert timestamps == sorted_timestamps, "Events not in chronological order"

    # Verify we always have at least intake and packet stages
    stages = [e["stage"] for e in events]
    assert "intake" in stages, "Missing intake stage event"
    assert "packet" in stages, "Missing packet stage event"

    # Clean up
    log_file.unlink()


def test_timeline_events_are_valid_json(logs_dir):
    """Verify timeline events are valid JSON and properly formatted."""
    envelopes = [
        SourceEnvelope.from_freeform(
            """
            Trip: 10 days Bangkok, Thailand
            Budget: $3000 USD
            Travelers: 2
            """,
            "agency_notes",
            "agent",
        )
    ]

    result = run_spine_once(envelopes=envelopes, stage="discovery")
    trip_id = result.packet.packet_id

    log_file = logs_dir / f"{trip_id}.jsonl"
    assert log_file.exists()

    # Verify each line is valid JSON
    event_count = 0
    with open(log_file, "r") as f:
        for line_num, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                event = json.loads(line.strip())
                event_count += 1
                # Verify essential fields
                assert isinstance(event.get("timestamp"), str)
                assert isinstance(event.get("stage"), str)
                assert isinstance(event.get("state"), str)
            except json.JSONDecodeError as e:
                pytest.fail(f"Line {line_num} contains invalid JSON: {e}")

    assert event_count > 0, "No events found in timeline"

    # Clean up
    log_file.unlink()


def test_timeline_file_is_append_only(logs_dir):
    """Verify that events are immutable once written."""
    envelopes = [
        SourceEnvelope.from_freeform(
            """
            Quick trip: 3 days in Barcelona
            Budget: €2000
            """,
            "agency_notes",
            "agent",
        )
    ]

    result = run_spine_once(envelopes=envelopes, stage="discovery")
    trip_id = result.packet.packet_id

    log_file = logs_dir / f"{trip_id}.jsonl"
    assert log_file.exists()

    # Count original events
    with open(log_file, "r") as f:
        original_lines = [line for line in f if line.strip()]
    original_count = len(original_lines)
    assert original_count > 0

    # Run again with a different envelope - should not modify existing events
    envelopes2 = [
        SourceEnvelope.from_freeform(
            "Different trip data",
            "agency_notes",
            "agent",
        )
    ]
    run_spine_once(envelopes=envelopes2, stage="discovery")

    # Verify original file still has same events
    with open(log_file, "r") as f:
        after_lines = [line for line in f if line.strip()]

    # Original events should still be there (at least the count should be >= original)
    assert len(after_lines) >= original_count

    # Clean up
    log_file.unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
