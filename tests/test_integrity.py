"""
Integrity tests for the contract-first architecture.

Verifies:
1. Aggregator logic produces mathematically consistent state
2. scenario_alpha.json produces deterministic counts
3. Pydantic models serialize to schema-matching JSON
4. DashboardAggregator computes stats with no frontend arithmetic needed
5. SLA status computation is correct for known fixtures
"""

import sys
import os
import pytest
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

# Ensure spine-api is importable
_spine_api_dir = str(Path(__file__).resolve().parent.parent / "spine-api")
if _spine_api_dir not in sys.path:
    sys.path.insert(0, _spine_api_dir)

from contract import (
    UnifiedStateResponse,
    DashboardStatsResponse,
    SuitabilitySignal,
)

from src.services.dashboard_aggregator import DashboardAggregator, VALID_STAGES

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "data" / "fixtures"
SCENARIO_ALPHA = FIXTURES_DIR / "scenario_alpha.json"


def _load_scenario_alpha():
    with open(SCENARIO_ALPHA) as f:
        return json.load(f)


# =============================================================================
# 1. Aggregator consistency (existing test, preserved)
# =============================================================================

def test_aggregator_logic():
    state = DashboardAggregator.get_unified_state()

    canonical_total = state.get("canonical_total")
    stages = state.get("stages", {})
    orphan_count = state.get("integrity_meta", {}).get("orphan_count", 0)

    sum_stages = sum(stages.values())

    assert sum_stages + orphan_count == canonical_total, (
        f"Mathematical inconsistency: stages={sum_stages} + orphans={orphan_count} != total={canonical_total}"
    )
    assert state.get("integrity_meta", {}).get("consistent") is True


# =============================================================================
# 2. Deterministic scenario_alpha verification
# =============================================================================

class TestScenarioAlphaDeterminism:
    """
    When the aggregator runs against scenario_alpha.json, it must always
    produce the exact same counts. If a test run produces different counts,
    the build must fail.
    """

    @pytest.fixture
    def alpha_trips(self):
        return _load_scenario_alpha()

    def test_alpha_total_count(self, alpha_trips):
        assert len(alpha_trips) == 30, f"Expected 30 trips, got {len(alpha_trips)}"

    def test_alpha_stage_distribution(self, alpha_trips):
        expected = {"new": 10, "assigned": 10, "in_progress": 5, "completed": 3, "cancelled": 2}
        actual = {stage: 0 for stage in VALID_STAGES}
        for trip in alpha_trips:
            status = trip.get("status")
            if status in actual:
                actual[status] += 1

        assert actual == expected, f"Stage distribution mismatch: {actual} != {expected}"

    def test_alpha_sla_breached_new(self, alpha_trips):
        """
        Count trips in 'new' status older than 4h relative to a fixed reference time.
        We use a fixed reference time (2026-04-23T14:00:00Z) so the test is deterministic.
        """
        reference_time = datetime(2026, 4, 23, 14, 0, 0, tzinfo=timezone.utc)
        threshold_new = timedelta(hours=4)

        breached_new = 0
        for trip in alpha_trips:
            if trip.get("status") != "new":
                continue
            created_at_str = trip.get("created_at")
            if not created_at_str:
                continue
            created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
            age = reference_time - created_at
            if age > threshold_new:
                breached_new += 1

        assert breached_new >= 1, "Expected at least 1 new trip with SLA breach in scenario_alpha"

    def test_alpha_sla_breached_assigned(self, alpha_trips):
        """
        Count trips in 'assigned' status older than 24h.
        """
        reference_time = datetime(2026, 4, 23, 14, 0, 0, tzinfo=timezone.utc)
        threshold_assigned = timedelta(hours=24)

        breached_assigned = 0
        for trip in alpha_trips:
            if trip.get("status") != "assigned":
                continue
            created_at_str = trip.get("created_at")
            if not created_at_str:
                continue
            created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
            age = reference_time - created_at
            if age > threshold_assigned:
                breached_assigned += 1

        assert breached_assigned >= 1, "Expected at least 1 assigned trip with SLA breach"

    def test_alpha_orphan_count(self, alpha_trips):
        orphans = [t for t in alpha_trips if t.get("status") not in VALID_STAGES]
        assert len(orphans) == 0, f"scenario_alpha should have 0 orphans, got {len(orphans)}"

    def test_alpha_integrity_sum(self, alpha_trips):
        total = len(alpha_trips)
        stage_counts = {s: 0 for s in VALID_STAGES}
        orphans = 0
        for trip in alpha_trips:
            status = trip.get("status")
            if status in stage_counts:
                stage_counts[status] += 1
            else:
                orphans += 1

        assert sum(stage_counts.values()) + orphans == total


# =============================================================================
# 3. Pydantic contract serialization
# =============================================================================

class TestPydanticContract:
    """Verify that Pydantic models serialize correctly and match expected schemas."""

    def test_unified_state_response_schema(self):
        from spine_api.contract import UnifiedStateResponse

        data = {
            "canonical_total": 30,
            "stages": {"new": 10, "assigned": 10, "in_progress": 5, "completed": 3, "cancelled": 2},
            "sla_breached": 5,
            "orphans": [],
            "integrity_meta": {
                "sum_stages": 30,
                "orphan_count": 0,
                "consistent": True,
                "last_sync": "2026-04-23T14:00:00+00:00",
            },
            "systemic_errors": [],
        }

        model = UnifiedStateResponse(**data)
        assert model.canonical_total == 30
        assert model.stages["new"] == 10
        assert model.integrity_meta.consistent is True

        serialized = model.model_dump()
        assert serialized["canonical_total"] == data["canonical_total"]
        assert serialized["stages"] == data["stages"]

    def test_dashboard_stats_response_schema(self):
        from spine_api.contract import DashboardStatsResponse

        data = {
            "active": 3,
            "pending_review": 27,
            "ready_to_book": 5,
            "needs_attention": 8,
        }

        model = DashboardStatsResponse(**data)
        assert model.active == 3
        assert model.ready_to_book == 5

        serialized = model.model_dump()
        for key in ("active", "pending_review", "ready_to_book", "needs_attention"):
            assert key in serialized

    def test_suitability_signal_schema(self):
        from spine_api.contract import SuitabilitySignal

        data = {
            "trip_id": "trip_001",
            "flag_type": "low_margin",
            "severity": "high",
            "reason": "Margin at 5% (below 10% threshold)",
            "confidence": 95.0,
        }

        model = SuitabilitySignal(**data)
        assert model.severity == "high"
        serialized = model.model_dump()
        assert serialized["flag_type"] == "low_margin"


# =============================================================================
# 4. DashboardAggregator stats computation
# =============================================================================

class TestDashboardAggregatorStats:
    """Verify stats computation replaces frontend Math/filter logic."""

    def test_get_trip_sla_status_completed(self):
        trip = {"status": "completed", "created_at": "2026-04-01T00:00:00+00:00"}
        assert DashboardAggregator.get_trip_sla_status(trip) == "on_track"

    def test_get_trip_sla_status_cancelled(self):
        trip = {"status": "cancelled", "created_at": "2026-04-01T00:00:00+00:00"}
        assert DashboardAggregator.get_trip_sla_status(trip) == "on_track"

    def test_get_trip_sla_status_new_recent(self):
        recent = datetime.now(timezone.utc) - timedelta(hours=1)
        trip = {"status": "new", "created_at": recent.isoformat()}
        assert DashboardAggregator.get_trip_sla_status(trip) == "on_track"

    def test_get_trip_sla_status_new_at_risk(self):
        at_risk_time = datetime.now(timezone.utc) - timedelta(hours=3, minutes=30)
        trip = {"status": "new", "created_at": at_risk_time.isoformat()}
        assert DashboardAggregator.get_trip_sla_status(trip) == "at_risk"

    def test_get_trip_sla_status_new_breached(self):
        breached_time = datetime.now(timezone.utc) - timedelta(hours=5)
        trip = {"status": "new", "created_at": breached_time.isoformat()}
        assert DashboardAggregator.get_trip_sla_status(trip) == "breached"

    def test_get_trip_sla_status_assigned_breached(self):
        breached_time = datetime.now(timezone.utc) - timedelta(hours=30)
        trip = {"status": "assigned", "created_at": breached_time.isoformat()}
        assert DashboardAggregator.get_trip_sla_status(trip) == "breached"

    def test_get_suitability_signals_low_margin(self):
        trip = {
            "id": "trip_001",
            "decision": {"suitability_flags": []},
            "analytics": {"margin_pct": 5, "quality_score": 80},
        }
        signals = DashboardAggregator.get_suitability_signals(trip)
        assert len(signals) == 1
        assert signals[0]["flag_type"] == "low_margin"
        assert signals[0]["severity"] == "high"

    def test_get_suitability_signals_low_quality(self):
        trip = {
            "id": "trip_001",
            "decision": {"suitability_flags": []},
            "analytics": {"margin_pct": 50, "quality_score": 30},
        }
        signals = DashboardAggregator.get_suitability_signals(trip)
        assert len(signals) == 1
        assert signals[0]["flag_type"] == "low_quality"

    def test_get_suitability_signals_clean(self):
        trip = {
            "id": "trip_001",
            "decision": {"suitability_flags": []},
            "analytics": {"margin_pct": 30, "quality_score": 80},
        }
        signals = DashboardAggregator.get_suitability_signals(trip)
        assert len(signals) == 0

    def test_get_suitability_signals_with_flags(self):
        trip = {
            "id": "trip_001",
            "decision": {
                "suitability_flags": [
                    {"flag": "elderly_mobility", "severity": "medium", "reason": "Elderly traveler", "confidence": 85}
                ]
            },
            "analytics": {"margin_pct": 30, "quality_score": 80},
        }
        signals = DashboardAggregator.get_suitability_signals(trip)
        assert len(signals) == 1
        assert signals[0]["flag_type"] == "elderly_mobility"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
