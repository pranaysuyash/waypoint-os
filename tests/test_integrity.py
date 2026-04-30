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
from fastapi.routing import APIRoute

# Ensure spine_api is importable
_spine_api_dir = str(Path(__file__).resolve().parent.parent / "spine_api")
if _spine_api_dir not in sys.path:
    sys.path.insert(0, _spine_api_dir)

from spine_api.contract import (
    IntegrityIssue,
    IntegrityIssuesResponse,
    UnifiedStateResponse,
    DashboardStatsResponse,
    SuitabilitySignal,
)
from spine_api.server import app

from src.services.dashboard_aggregator import DashboardAggregator, VALID_STAGES
from src.services.integrity_service import IntegrityService

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
        expected = {"new": 10, "assigned": 10, "in_progress": 5, "completed": 3, "cancelled": 2, "incomplete": 0}
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

    def test_integrity_issue_response_schema(self):
        detected_at = "2026-04-30T07:00:00+00:00"
        data = {
            "items": [
                {
                    "id": "integrity_orphaned_record_trip_123",
                    "entity_id": "trip_123",
                    "entity_type": "unknown",
                    "issue_type": "orphaned_record",
                    "severity": "medium",
                    "reason": "Record is detached from normal inbox/workspace routing.",
                    "current_status": "mystery",
                    "created_at": "2026-04-29T10:00:00+00:00",
                    "detected_at": detected_at,
                    "allowed_actions": [],
                }
            ],
            "total": 1,
        }

        model = IntegrityIssuesResponse(**data)
        assert model.total == 1
        assert model.items[0].issue_type == "orphaned_record"
        assert model.items[0].allowed_actions == []

        serialized = model.model_dump()
        assert serialized["items"][0]["entity_id"] == "trip_123"

    def test_unified_state_response_schema(self):
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


class TestIntegrityClassification:
    def test_incomplete_lead_counts_as_known_lifecycle_work_not_orphan(self):
        trips = [
            {
                "id": "trip_incomplete_lead",
                "status": "incomplete",
                "created_at": "2026-04-29T20:02:40.764703+00:00",
            }
        ]

        with patch("src.services.dashboard_aggregator.TripStore.list_trips", return_value=trips):
            state = DashboardAggregator.get_unified_state(agency_id="agency_123")

        assert state["canonical_total"] == 1
        assert state["stages"]["incomplete"] == 1
        assert state["orphans"] == []
        assert state["integrity_meta"]["orphan_count"] == 0

    def test_integrity_service_excludes_incomplete_leads_from_system_check(self):
        trips = [
            {
                "id": "trip_incomplete_lead",
                "status": "incomplete",
                "created_at": "2026-04-29T20:02:40.764703+00:00",
            }
        ]

        with patch("src.services.dashboard_aggregator.TripStore.list_trips", return_value=trips):
            response = IntegrityService.list_integrity_issues(agency_id="agency_123")

        assert response["items"] == []
        assert response["total"] == 0

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


class TestIntegrityIssues:
    def test_orphan_maps_to_integrity_issue(self):
        detected_at = "2026-04-30T07:00:00+00:00"

        issue = IntegrityService.map_orphan_to_issue(
            {
                "id": "trip_123",
                "status": "mystery",
                "created_at": "2026-04-29T10:00:00+00:00",
            },
            detected_at=detected_at,
        )

        assert isinstance(issue, IntegrityIssue)
        assert issue.id == "integrity_orphaned_record_trip_123"
        assert issue.entity_id == "trip_123"
        assert issue.entity_type == "unknown"
        assert issue.issue_type == "orphaned_record"
        assert issue.severity == "medium"
        assert (
            issue.reason
            == "Record is detached from normal inbox/workspace routing."
        )
        assert issue.current_status == "mystery"
        assert issue.created_at == "2026-04-29T10:00:00+00:00"
        assert issue.detected_at == detected_at
        assert issue.allowed_actions == []

    def test_only_orphans_become_integrity_issues(self):
        trips = [
            {
                "id": "trip_routable",
                "status": "new",
                "created_at": "2026-04-29T09:00:00+00:00",
            },
            {
                "id": "trip_orphan",
                "status": "mystery",
                "created_at": "2026-04-29T10:00:00+00:00",
            },
        ]

        with patch(
            "src.services.integrity_service.TripStore.list_trips",
            return_value=trips,
        ):
            result = IntegrityService.list_integrity_issues(agency_id="agency-123")

        assert result["total"] == 1
        assert len(result["items"]) == 1
        assert result["items"][0].entity_id == "trip_orphan"

    def test_detected_at_uses_last_sync_when_available(self):
        detected_at = "2026-04-30T07:00:00+00:00"
        unified_state = {
            "orphans": [
                {
                    "id": "trip_orphan",
                    "status": "mystery",
                    "created_at": "2026-04-29T10:00:00+00:00",
                }
            ],
            "integrity_meta": {
                "last_sync": detected_at,
            },
        }

        with patch(
            "src.services.integrity_service.DashboardAggregator.get_unified_state",
            return_value=unified_state,
        ):
            result = IntegrityService.list_integrity_issues(agency_id="agency-123")

        assert result["items"][0].detected_at == detected_at

    def test_integrity_endpoint_returns_items_and_total(self, session_client):
        response = session_client.get("/api/system/integrity/issues")

        assert response.status_code == 200
        body = response.json()
        assert set(body.keys()) == {"items", "total"}
        assert isinstance(body["items"], list)
        assert isinstance(body["total"], int)

    def test_integrity_endpoint_passes_current_agency_scope(self, session_client):
        with patch(
            "spine_api.server.IntegrityService.list_integrity_issues",
            return_value={"items": [], "total": 0},
        ) as mocked_list:
            response = session_client.get("/api/system/integrity/issues")

        assert response.status_code == 200
        mocked_list.assert_called_once_with(
            agency_id="d1e3b2b6-5509-4c27-b123-4b1e02b0bf5b"
        )

    def test_no_repair_route_is_exposed(self):
        get_route = None
        repair_route = None

        for route in app.routes:
            if not isinstance(route, APIRoute):
                continue
            if route.path == "/api/system/integrity/issues" and "GET" in route.methods:
                get_route = route
            if route.path == "/api/system/integrity/issues/{issue_id}/repair":
                repair_route = route

        assert get_route is not None
        assert repair_route is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
