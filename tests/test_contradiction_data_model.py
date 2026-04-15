"""
Tests for data model changes in Block 1 of Spine Hardening Plan.

Tests:
- ContradictionValue dataclass
- add_contradiction() with structured format and backward compatibility
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
from intake.packet_models import (
    CanonicalPacket,
    ContradictionValue,
    Slot,
    AuthorityLevel,
)


class TestContradictionValue:
    """Tests for the new ContradictionValue dataclass."""

    def test_contradiction_value_creation(self):
        """Can create a ContradictionValue with all fields."""
        cv = ContradictionValue(
            value="3L",
            source="email",
            authority="explicit_user",
            timestamp="2026-04-15T10:00:00Z"
        )
        assert cv.value == "3L"
        assert cv.source == "email"
        assert cv.authority == "explicit_user"
        assert cv.timestamp == "2026-04-15T10:00:00Z"

    def test_contradiction_value_optional_timestamp(self):
        """Timestamp is optional."""
        cv = ContradictionValue(value="4L", source="chat", authority="explicit_user")
        assert cv.timestamp is None


class TestAddContradictionStructured:
    """Tests for add_contradiction() with structured ContradictionValue format."""

    def test_structured_contradiction_new_format(self):
        """New format: List[ContradictionValue] creates structured contradiction."""
        pkt = CanonicalPacket(packet_id="test_structured")
        
        structured_values = [
            ContradictionValue(value="3L", source="email", authority="explicit_user"),
            ContradictionValue(value="4L", source="whatsapp", authority="explicit_user"),
        ]
        
        pkt.add_contradiction("budget", structured_values)
        
        assert len(pkt.contradictions) == 1
        contradiction = pkt.contradictions[0]
        
        # Check field name
        assert contradiction["field_name"] == "budget"
        
        # Check structured values are preserved
        assert len(contradiction["values"]) == 2
        assert contradiction["values"][0].value == "3L"
        assert contradiction["values"][0].source == "email"
        assert contradiction["values"][1].value == "4L"
        assert contradiction["values"][1].source == "whatsapp"
        
        # Check backward-compatible sources list
        assert contradiction["sources"] == ["email", "whatsapp"]
        
        # Check values_legacy for backward compat
        assert contradiction["values_legacy"] == ["3L", "4L"]

    def test_structured_contradiction_has_detected_at(self):
        """Structured contradiction has detected_at timestamp."""
        pkt = CanonicalPacket(packet_id="test_timestamp")
        
        structured_values = [
            ContradictionValue(value="A", source="src1", authority="explicit_user"),
        ]
        
        pkt.add_contradiction("field", structured_values)
        
        assert "detected_at" in pkt.contradictions[0]
        # Should be ISO-8601 format
        assert "T" in pkt.contradictions[0]["detected_at"]


class TestAddContradictionBackwardCompat:
    """Tests for add_contradiction() backward compatibility with legacy format."""

    def test_legacy_format_still_works(self):
        """Legacy format: values list + sources list still works."""
        pkt = CanonicalPacket(packet_id="test_legacy")
        
        # Legacy call: values list, sources list
        pkt.add_contradiction("budget", ["3L", "4L"], ["email", "whatsapp"])
        
        assert len(pkt.contradictions) == 1
        contradiction = pkt.contradictions[0]
        
        # Legacy format should be converted to structured
        assert contradiction["field_name"] == "budget"
        assert len(contradiction["values"]) == 2
        
        # Values should be converted to ContradictionValue
        assert isinstance(contradiction["values"][0], ContradictionValue)
        assert contradiction["values"][0].value == "3L"
        assert contradiction["values"][0].source == "email"
        assert contradiction["values"][0].authority == "explicit_user"
        
        assert contradiction["values"][1].value == "4L"
        assert contradiction["values"][1].source == "whatsapp"
        
        # Backward compat fields
        assert contradiction["values_legacy"] == ["3L", "4L"]
        assert contradiction["sources"] == ["email", "whatsapp"]

    def test_legacy_format_mismatched_lengths(self):
        """Legacy format handles more values than sources gracefully."""
        pkt = CanonicalPacket(packet_id="test_mismatch")
        
        # 3 values, 2 sources - should handle gracefully
        pkt.add_contradiction("field", ["val1", "val2", "val3"], ["src1", "src2"])
        
        contradiction = pkt.contradictions[0]
        assert len(contradiction["values"]) == 3
        
        # Third value should get "unknown" source
        assert contradiction["values"][2].source == "unknown"
        
        # Sources list should match values count
        assert len(contradiction["sources"]) == 3
        assert contradiction["sources"][2] == "unknown"

    def test_legacy_format_no_sources(self):
        """Legacy format handles missing sources."""
        pkt = CanonicalPacket(packet_id="test_no_sources")
        
        pkt.add_contradiction("field", ["val1", "val2"])  # No sources
        
        contradiction = pkt.contradictions[0]
        assert len(contradiction["values"]) == 2
        
        # All values should get "unknown" source
        assert contradiction["values"][0].source == "unknown"
        assert contradiction["values"][1].source == "unknown"


class TestContradictionEventEmission:
    """Tests that contradiction events are emitted."""

    def test_contradiction_emits_event(self):
        """Adding a contradiction emits a contradiction_detected event."""
        pkt = CanonicalPacket(packet_id="test_event")
        
        structured_values = [
            ContradictionValue(value="X", source="src1", authority="explicit_user"),
        ]
        pkt.add_contradiction("field", structured_values)
        
        # Should have event in events list
        events = [e for e in pkt.events if e["event_type"] == "contradiction_detected"]
        assert len(events) == 1
        assert events[0]["details"]["field_name"] == "field"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])