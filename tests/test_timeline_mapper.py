"""
Unit tests for TimelineEventMapper.

Validates the transformation from AuditStore raw events to presentation-ready
TimelineEvent format that the frontend can consume.
"""

import pytest
from datetime import datetime, timezone
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "spine_api"))

from analytics.logger import TimelineEventMapper, TimelineEvent


class TestTimelineEventMapperBasics:
    """Test basic event mapping functionality."""
    
    def test_map_intake_event(self):
        """Test mapping an intake stage event."""
        audit_event = {
            "id": "evt_001",
            "type": "spine_stage_transition",
            "user_id": "agent",
            "timestamp": "2025-01-15T10:00:00+00:00",
            "details": {
                "trip_id": "trip_abc123",
                "stage": "intake",
                "state": "started",
                "description": "Intake phase initiated",
                "confidence": 0.95,
            }
        }
        
        event = TimelineEventMapper.map_event(audit_event)
        
        assert event is not None
        assert event.trip_id == "trip_abc123"
        assert event.stage == "intake"
        assert event.status == "started"
        assert event.timestamp == "2025-01-15T10:00:00+00:00"
        assert event.confidence == 0.95
    
    def test_map_packet_event(self):
        """Test mapping a packet stage event."""
        audit_event = {
            "id": "evt_002",
            "type": "spine_stage_transition",
            "user_id": "agent",
            "timestamp": "2025-01-15T10:15:00+00:00",
            "details": {
                "trip_id": "trip_abc123",
                "stage": "packet",
                "state": "in_progress",
                "description": "Processing trip packet",
            }
        }
        
        event = TimelineEventMapper.map_event(audit_event)
        
        assert event is not None
        assert event.stage == "packet"
        assert event.status == "in_progress"
    
    def test_map_decision_event_with_approval(self):
        """Test mapping a decision event with approval."""
        audit_event = {
            "id": "evt_003",
            "type": "spine_stage_transition",
            "user_id": "agent",
            "timestamp": "2025-01-15T10:30:00+00:00",
            "details": {
                "trip_id": "trip_abc123",
                "stage": "decision",
                "state": "completed",
                "decision_type": "approve",
                "reason": "All suitability checks passed",
                "confidence": 0.98,
            }
        }
        
        event = TimelineEventMapper.map_event(audit_event)
        
        assert event is not None
        assert event.stage == "decision"
        assert event.status == "approved"
        assert event.decision == "approve"
        assert event.reason == "All suitability checks passed"
        assert event.confidence == 0.98
    
    def test_map_decision_event_with_rejection(self):
        """Test mapping a decision event with rejection."""
        audit_event = {
            "id": "evt_004",
            "type": "spine_stage_transition",
            "user_id": "agent",
            "timestamp": "2025-01-15T10:45:00+00:00",
            "details": {
                "trip_id": "trip_xyz789",
                "stage": "decision",
                "state": "completed",
                "decision_type": "reject",
                "reason": "Safety concerns detected",
                "confidence": 0.85,
            }
        }
        
        event = TimelineEventMapper.map_event(audit_event)
        
        assert event is not None
        assert event.status == "rejected"
        assert event.decision == "reject"
    
    def test_map_strategy_event(self):
        """Test mapping a strategy stage event."""
        audit_event = {
            "id": "evt_005",
            "type": "spine_stage_transition",
            "user_id": "agent",
            "timestamp": "2025-01-15T11:00:00+00:00",
            "details": {
                "trip_id": "trip_abc123",
                "stage": "strategy",
                "state": "completed",
                "description": "Strategy formulated",
            }
        }
        
        event = TimelineEventMapper.map_event(audit_event)
        
        assert event is not None
        assert event.stage == "strategy"
        assert event.status == "completed"
    
    def test_map_safety_event(self):
        """Test mapping a safety stage event."""
        audit_event = {
            "id": "evt_006",
            "type": "spine_stage_transition",
            "user_id": "agent",
            "timestamp": "2025-01-15T11:15:00+00:00",
            "details": {
                "trip_id": "trip_abc123",
                "stage": "safety",
                "state": "completed",
                "description": "Safety check completed",
            }
        }
        
        event = TimelineEventMapper.map_event(audit_event)
        
        assert event is not None
        assert event.stage == "safety"


class TestTimelineEventMapperStateConversion:
    """Test pre_state/post_state to status conversion."""
    
    def test_status_from_decision_type_approve(self):
        """Test that decision_type=approve maps to status=approved."""
        audit_event = {
            "id": "evt_007",
            "type": "spine_stage_transition",
            "user_id": "agent",
            "timestamp": "2025-01-15T12:00:00+00:00",
            "details": {
                "trip_id": "trip_test",
                "stage": "decision",
                "state": "unknown",  # Missing explicit state
                "decision_type": "approve",  # Decision type should drive status
            }
        }
        
        event = TimelineEventMapper.map_event(audit_event)
        
        assert event is not None
        assert event.status == "approved"
        assert event.decision == "approve"
    
    def test_status_from_decision_type_reject(self):
        """Test that decision_type=reject maps to status=rejected."""
        audit_event = {
            "id": "evt_008",
            "type": "spine_stage_transition",
            "user_id": "agent",
            "timestamp": "2025-01-15T12:15:00+00:00",
            "details": {
                "trip_id": "trip_test",
                "stage": "decision",
                "state": "unknown",
                "decision_type": "reject",
            }
        }
        
        event = TimelineEventMapper.map_event(audit_event)
        
        assert event is not None
        assert event.status == "rejected"
    
    def test_state_snapshot_includes_confidence(self):
        """Test that state_snapshot includes confidence if available."""
        audit_event = {
            "id": "evt_009",
            "type": "spine_stage_transition",
            "user_id": "agent",
            "timestamp": "2025-01-15T12:30:00+00:00",
            "details": {
                "trip_id": "trip_test",
                "stage": "packet",
                "state": "in_progress",
                "confidence": 0.92,
            }
        }
        
        event = TimelineEventMapper.map_event(audit_event)
        
        assert event is not None
        assert event.state_snapshot["confidence"] == 0.92
    
    def test_state_snapshot_includes_description(self):
        """Test that state_snapshot includes description if available."""
        audit_event = {
            "id": "evt_010",
            "type": "spine_stage_transition",
            "user_id": "agent",
            "timestamp": "2025-01-15T12:45:00+00:00",
            "details": {
                "trip_id": "trip_test",
                "stage": "intake",
                "state": "started",
                "description": "Processing user request",
            }
        }
        
        event = TimelineEventMapper.map_event(audit_event)
        
        assert event is not None
        assert event.state_snapshot["description"] == "Processing user request"


class TestTimelineEventMapperEdgeCases:
    """Test edge cases and error handling."""
    
    def test_map_event_missing_trip_id(self):
        """Test that events without trip_id are rejected."""
        audit_event = {
            "id": "evt_011",
            "type": "spine_stage_transition",
            "user_id": "agent",
            "timestamp": "2025-01-15T13:00:00+00:00",
            "details": {
                # Missing trip_id!
                "stage": "intake",
                "state": "started",
            }
        }
        
        event = TimelineEventMapper.map_event(audit_event)
        
        # Should return None for invalid event
        assert event is None
    
    def test_map_event_missing_timestamp(self):
        """Test that events without timestamp are rejected."""
        audit_event = {
            "id": "evt_012",
            "type": "spine_stage_transition",
            "user_id": "agent",
            # Missing timestamp!
            "details": {
                "trip_id": "trip_test",
                "stage": "intake",
                "state": "started",
            }
        }
        
        event = TimelineEventMapper.map_event(audit_event)
        
        assert event is None
    
    def test_map_event_null_values(self):
        """Test that events with null optional fields are handled gracefully."""
        audit_event = {
            "id": "evt_013",
            "type": "spine_stage_transition",
            "user_id": "agent",
            "timestamp": "2025-01-15T13:15:00+00:00",
            "details": {
                "trip_id": "trip_test",
                "stage": "decision",
                "state": "completed",
                "decision_type": None,
                "reason": None,
                "confidence": None,
            }
        }
        
        event = TimelineEventMapper.map_event(audit_event)
        
        assert event is not None
        assert event.decision is None
        assert event.reason is None
        assert event.confidence is None
    
    def test_map_event_missing_details_object(self):
        """Test handling of missing details object."""
        audit_event = {
            "id": "evt_014",
            "type": "spine_stage_transition",
            "user_id": "agent",
            "timestamp": "2025-01-15T13:30:00+00:00",
            # Missing details!
        }
        
        event = TimelineEventMapper.map_event(audit_event)
        
        # Should return None because trip_id and stage would be missing
        assert event is None
    
    def test_map_event_case_insensitive_stage(self):
        """Test that stage names are normalized to lowercase."""
        audit_event = {
            "id": "evt_015",
            "type": "spine_stage_transition",
            "user_id": "agent",
            "timestamp": "2025-01-15T13:45:00+00:00",
            "details": {
                "trip_id": "trip_test",
                "stage": "INTAKE",  # Uppercase
                "state": "started",
            }
        }
        
        event = TimelineEventMapper.map_event(audit_event)
        
        assert event is not None
        assert event.stage == "intake"  # Should be lowercase


class TestTimelineEventMapperBatchProcessing:
    """Test batch event processing for entire trips."""
    
    def test_map_events_for_trip(self):
        """Test mapping multiple events for a trip."""
        audit_events = [
            {
                "id": "evt_016",
                "type": "spine_stage_transition",
                "user_id": "agent",
                "timestamp": "2025-01-15T14:00:00+00:00",
                "details": {
                    "trip_id": "trip_batch",
                    "stage": "intake",
                    "state": "started",
                }
            },
            {
                "id": "evt_017",
                "type": "spine_stage_transition",
                "user_id": "agent",
                "timestamp": "2025-01-15T14:15:00+00:00",
                "details": {
                    "trip_id": "trip_batch",
                    "stage": "packet",
                    "state": "in_progress",
                }
            },
            {
                "id": "evt_018",
                "type": "spine_stage_transition",
                "user_id": "agent",
                "timestamp": "2025-01-15T14:30:00+00:00",
                "details": {
                    "trip_id": "trip_batch",
                    "stage": "decision",
                    "state": "completed",
                    "decision_type": "approve",
                }
            },
        ]
        
        events = TimelineEventMapper.map_events_for_trip(audit_events)
        
        assert len(events) == 3
        assert events[0].stage == "intake"
        assert events[1].stage == "packet"
        assert events[2].stage == "decision"
        assert events[2].status == "approved"
    
    def test_map_events_with_stage_filter(self):
        """Test batch processing with stage filter."""
        audit_events = [
            {
                "id": "evt_019",
                "type": "spine_stage_transition",
                "user_id": "agent",
                "timestamp": "2025-01-15T14:45:00+00:00",
                "details": {
                    "trip_id": "trip_filter",
                    "stage": "intake",
                    "state": "started",
                }
            },
            {
                "id": "evt_020",
                "type": "spine_stage_transition",
                "user_id": "agent",
                "timestamp": "2025-01-15T15:00:00+00:00",
                "details": {
                    "trip_id": "trip_filter",
                    "stage": "packet",
                    "state": "in_progress",
                }
            },
            {
                "id": "evt_021",
                "type": "spine_stage_transition",
                "user_id": "agent",
                "timestamp": "2025-01-15T15:15:00+00:00",
                "details": {
                    "trip_id": "trip_filter",
                    "stage": "decision",
                    "state": "completed",
                    "decision_type": "approve",
                }
            },
        ]
        
        # Filter by decision stage
        events = TimelineEventMapper.map_events_for_trip(audit_events, stage_filter="decision")
        
        assert len(events) == 1
        assert events[0].stage == "decision"
        assert events[0].status == "approved"
    
    def test_map_events_preserves_chronological_order(self):
        """Test that mapped events maintain chronological order."""
        # Create events intentionally out of order
        audit_events = [
            {
                "id": "evt_022",
                "type": "spine_stage_transition",
                "user_id": "agent",
                "timestamp": "2025-01-15T15:45:00+00:00",
                "details": {
                    "trip_id": "trip_order",
                    "stage": "decision",
                    "state": "completed",
                }
            },
            {
                "id": "evt_023",
                "type": "spine_stage_transition",
                "user_id": "agent",
                "timestamp": "2025-01-15T15:15:00+00:00",
                "details": {
                    "trip_id": "trip_order",
                    "stage": "intake",
                    "state": "started",
                }
            },
            {
                "id": "evt_024",
                "type": "spine_stage_transition",
                "user_id": "agent",
                "timestamp": "2025-01-15T15:30:00+00:00",
                "details": {
                    "trip_id": "trip_order",
                    "stage": "packet",
                    "state": "in_progress",
                }
            },
        ]
        
        events = TimelineEventMapper.map_events_for_trip(audit_events)
        
        # Verify events are sorted by timestamp
        assert len(events) == 3
        assert events[0].timestamp == "2025-01-15T15:15:00+00:00"
        assert events[1].timestamp == "2025-01-15T15:30:00+00:00"
        assert events[2].timestamp == "2025-01-15T15:45:00+00:00"
    
    def test_map_events_ignores_invalid_events(self):
        """Test that invalid events are skipped in batch processing."""
        audit_events = [
            {
                "id": "evt_025",
                "type": "spine_stage_transition",
                "user_id": "agent",
                "timestamp": "2025-01-15T16:00:00+00:00",
                "details": {
                    "trip_id": "trip_mixed",
                    "stage": "intake",
                    "state": "started",
                }
            },
            {
                "id": "evt_026",
                "type": "spine_stage_transition",
                "user_id": "agent",
                # Missing timestamp!
                "details": {
                    "trip_id": "trip_mixed",
                    "stage": "packet",
                    "state": "in_progress",
                }
            },
            {
                "id": "evt_027",
                "type": "spine_stage_transition",
                "user_id": "agent",
                "timestamp": "2025-01-15T16:15:00+00:00",
                "details": {
                    "trip_id": "trip_mixed",
                    "stage": "decision",
                    "state": "completed",
                }
            },
        ]
        
        events = TimelineEventMapper.map_events_for_trip(audit_events)
        
        # Should only have 2 valid events
        assert len(events) == 2
        assert events[0].stage == "intake"
        assert events[1].stage == "decision"


class TestTimelineEventMapperStateSnapshot:
    """Test state_snapshot generation."""
    
    def test_state_snapshot_basic_structure(self):
        """Test that state_snapshot has the expected basic fields."""
        audit_event = {
            "id": "evt_028",
            "type": "spine_stage_transition",
            "user_id": "agent",
            "timestamp": "2025-01-15T16:30:00+00:00",
            "details": {
                "trip_id": "trip_snapshot",
                "stage": "packet",
                "state": "in_progress",
            }
        }
        
        event = TimelineEventMapper.map_event(audit_event)
        
        assert event is not None
        assert "stage" in event.state_snapshot
        assert "status" in event.state_snapshot
        assert event.state_snapshot["stage"] == "packet"
        assert event.state_snapshot["status"] == "in_progress"
    
    def test_state_snapshot_with_post_state_delta(self):
        """Test that state_snapshot includes info from post_state delta."""
        audit_event = {
            "id": "evt_029",
            "type": "spine_stage_transition",
            "user_id": "agent",
            "timestamp": "2025-01-15T16:45:00+00:00",
            "details": {
                "trip_id": "trip_snapshot",
                "stage": "decision",
                "state": "completed",
                "post_state": {
                    "state": "decision_made",
                    "reason": "All checks passed",
                }
            }
        }
        
        event = TimelineEventMapper.map_event(audit_event)
        
        assert event is not None
        assert "previous_state" in event.state_snapshot
        assert event.state_snapshot["previous_state"] == "decision_made"


class TestTimelineEventMapperIntegration:
    """Integration tests combining multiple features."""
    
    def test_complete_trip_timeline(self):
        """Test a complete trip timeline with all stages."""
        audit_events = [
            {
                "id": "evt_030",
                "type": "spine_stage_transition",
                "user_id": "agent",
                "timestamp": "2025-01-15T17:00:00+00:00",
                "details": {
                    "trip_id": "trip_complete",
                    "stage": "intake",
                    "state": "started",
                    "description": "Trip intake initiated",
                }
            },
            {
                "id": "evt_031",
                "type": "spine_stage_transition",
                "user_id": "agent",
                "timestamp": "2025-01-15T17:10:00+00:00",
                "details": {
                    "trip_id": "trip_complete",
                    "stage": "packet",
                    "state": "completed",
                    "description": "Packet processed",
                    "confidence": 0.95,
                }
            },
            {
                "id": "evt_032",
                "type": "spine_stage_transition",
                "user_id": "agent",
                "timestamp": "2025-01-15T17:20:00+00:00",
                "details": {
                    "trip_id": "trip_complete",
                    "stage": "decision",
                    "state": "completed",
                    "decision_type": "approve",
                    "reason": "Suitability confirmed",
                    "confidence": 0.98,
                }
            },
            {
                "id": "evt_033",
                "type": "spine_stage_transition",
                "user_id": "agent",
                "timestamp": "2025-01-15T17:30:00+00:00",
                "details": {
                    "trip_id": "trip_complete",
                    "stage": "strategy",
                    "state": "completed",
                    "description": "Strategy prepared",
                }
            },
            {
                "id": "evt_034",
                "type": "spine_stage_transition",
                "user_id": "agent",
                "timestamp": "2025-01-15T17:40:00+00:00",
                "details": {
                    "trip_id": "trip_complete",
                    "stage": "safety",
                    "state": "completed",
                    "description": "Safety check passed",
                }
            },
        ]
        
        events = TimelineEventMapper.map_events_for_trip(audit_events)
        
        assert len(events) == 5
        assert events[0].stage == "intake"
        assert events[0].status == "started"
        assert events[1].stage == "packet"
        assert events[2].stage == "decision"
        assert events[2].status == "approved"
        assert events[3].stage == "strategy"
        assert events[4].stage == "safety"
        
        # Verify chronological order
        for i in range(len(events) - 1):
            assert events[i].timestamp <= events[i + 1].timestamp


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
