from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from spine_api.routers import run_status


@pytest.fixture
def agency():
    return SimpleNamespace(id="agency-1")


def test_list_runs_scopes_to_agency(monkeypatch, agency):
    rows = [
        {"run_id": "r1", "agency_id": "agency-1"},
        {"run_id": "r2", "agency_id": "agency-2"},
        {"run_id": "r3", "agency_id": "agency-1"},
    ]

    monkeypatch.setattr(run_status.RunLedger, "list_runs", lambda **kwargs: rows)

    body = run_status.list_runs(trip_id=None, state=None, limit=50, agency=agency)

    assert body["total"] == 2
    assert [r["run_id"] for r in body["items"]] == ["r1", "r3"]


def test_get_run_status_missing_run_404(monkeypatch, agency):
    monkeypatch.setattr(run_status.RunLedger, "get_meta", lambda run_id: None)

    with pytest.raises(HTTPException) as exc:
        run_status.get_run_status("missing", agency=agency)

    assert exc.value.status_code == 404


def test_get_run_status_wrong_agency_404(monkeypatch, agency):
    monkeypatch.setattr(run_status.RunLedger, "get_meta", lambda run_id: {"run_id": run_id, "agency_id": "other", "state": "completed"})

    with pytest.raises(HTTPException) as exc:
        run_status.get_run_status("r1", agency=agency)

    assert exc.value.status_code == 404


def test_get_run_step_missing_step_404(monkeypatch, agency):
    monkeypatch.setattr(run_status.RunLedger, "get_meta", lambda run_id: {"run_id": run_id, "agency_id": "agency-1", "state": "completed"})
    monkeypatch.setattr(run_status.RunLedger, "get_step", lambda run_id, step_name: None)

    with pytest.raises(HTTPException) as exc:
        run_status.get_run_step("r1", "packet", agency=agency)

    assert exc.value.status_code == 404


def test_get_run_events_wrong_agency_404(monkeypatch, agency):
    monkeypatch.setattr(run_status.RunLedger, "get_meta", lambda run_id: {"run_id": run_id, "agency_id": "other", "state": "completed"})

    with pytest.raises(HTTPException) as exc:
        run_status.get_run_event_stream("r1", agency=agency)

    assert exc.value.status_code == 404


def test_get_run_events_success_shape(monkeypatch, agency):
    metas = iter([
        {"run_id": "r1", "agency_id": "agency-1", "state": "completed"},
        {"run_id": "r1", "agency_id": "agency-1", "state": "completed"},
    ])
    monkeypatch.setattr(run_status.RunLedger, "get_meta", lambda run_id: next(metas))
    monkeypatch.setattr(run_status, "get_run_events", lambda run_id: [{"event_type": "run_started"}, {"event_type": "run_completed"}])

    body = run_status.get_run_event_stream("r1", agency=agency)

    assert body["run_id"] == "r1"
    assert body["total"] == 2
    assert body["events"][0]["event_type"] == "run_started"
