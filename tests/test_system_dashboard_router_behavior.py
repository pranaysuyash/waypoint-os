from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from spine_api.routers import system_dashboard


@pytest.fixture
def agency():
    return SimpleNamespace(id="agency-1")


@pytest.mark.asyncio
async def test_get_unified_state_success_passes_agency_id(monkeypatch, agency):
    captured: dict[str, str] = {}

    def _get_unified_state(*, agency_id: str):
        captured["agency_id"] = agency_id
        return {"ok": True, "agency_id": agency_id}

    monkeypatch.setattr(system_dashboard.DashboardAggregator, "get_unified_state", _get_unified_state)

    body = await system_dashboard.get_unified_state(agency=agency)

    assert body == {"ok": True, "agency_id": "agency-1"}
    assert captured["agency_id"] == "agency-1"


@pytest.mark.asyncio
async def test_get_unified_state_failure_500_detail(monkeypatch, agency):
    def _raise(*, agency_id: str):
        raise RuntimeError("boom")

    monkeypatch.setattr(system_dashboard.DashboardAggregator, "get_unified_state", _raise)

    with pytest.raises(HTTPException) as exc:
        await system_dashboard.get_unified_state(agency=agency)

    assert exc.value.status_code == 500
    assert exc.value.detail == "Internal integrity error"


@pytest.mark.asyncio
async def test_get_integrity_issues_success_passes_agency_id(monkeypatch, agency):
    captured: dict[str, str] = {}

    def _list_integrity_issues(*, agency_id: str):
        captured["agency_id"] = agency_id
        return {"items": [], "total": 0}

    monkeypatch.setattr(system_dashboard.IntegrityService, "list_integrity_issues", _list_integrity_issues)

    body = await system_dashboard.get_integrity_issues(agency=agency)

    assert body == {"items": [], "total": 0}
    assert captured["agency_id"] == "agency-1"


@pytest.mark.asyncio
async def test_get_integrity_issues_failure_500_detail(monkeypatch, agency):
    def _raise(*, agency_id: str):
        raise RuntimeError("boom")

    monkeypatch.setattr(system_dashboard.IntegrityService, "list_integrity_issues", _raise)

    with pytest.raises(HTTPException) as exc:
        await system_dashboard.get_integrity_issues(agency=agency)

    assert exc.value.status_code == 500
    assert exc.value.detail == "Internal integrity error"


@pytest.mark.asyncio
async def test_get_dashboard_stats_success_passes_agency_id(monkeypatch, agency):
    captured: dict[str, str] = {}

    def _get_dashboard_stats(*, agency_id: str):
        captured["agency_id"] = agency_id
        return {
            "inbox": {"total": 0, "new": 0, "in_progress": 0, "review_required": 0, "blocked": 0, "ready_to_send": 0, "done": 0},
            "sla": {"breaching_soon": 0, "overdue": 0},
            "assignments": {"unassigned": 0, "assigned": 0},
            "reviews": {"pending": 0, "with_suitability_flags": 0},
            "capacity": {"active_agents": 0, "utilization_percent": 0.0},
            "autonomy": {"auto_dispatch_enabled": False, "threshold": 0.0},
            "freshness": {"last_updated": "2026-05-07T00:00:00+00:00"},
            "generated_at": "2026-05-07T00:00:00+00:00",
        }

    monkeypatch.setattr(system_dashboard.DashboardAggregator, "get_dashboard_stats", _get_dashboard_stats)

    body = await system_dashboard.get_dashboard_stats(agency=agency)

    assert body["inbox"]["total"] == 0
    assert captured["agency_id"] == "agency-1"


@pytest.mark.asyncio
async def test_get_dashboard_stats_failure_500_detail(monkeypatch, agency):
    def _raise(*, agency_id: str):
        raise RuntimeError("boom")

    monkeypatch.setattr(system_dashboard.DashboardAggregator, "get_dashboard_stats", _raise)

    with pytest.raises(HTTPException) as exc:
        await system_dashboard.get_dashboard_stats(agency=agency)

    assert exc.value.status_code == 500
    assert exc.value.detail == "Failed to compute dashboard stats"
