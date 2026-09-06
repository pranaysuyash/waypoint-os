"""S-05 (audit RT-03) regression — draft promote rejects cross-tenant trip_id.

POST /api/drafts/{draft_id}/promote previously stored any caller-supplied
trip_id without checking that the trip belongs to the draft's agency. A
foreign trip_id poisoned the draft -> trip link (downstream reprocess resolves
it via an unscoped get_trip) and forced a guaranteed-failed save or a silent
duplicate-trip fork.

These tests exercise the router seam directly with a fake agency-scoped trip
lookup, so no real trip rows (SQL) are written.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

import spine_api.draft_store as draft_store_module
import spine_api.routers.drafts as drafts_router
from spine_api.draft_store import DraftStore
from spine_api.routers.drafts import PromoteDraftRequest, promote_draft

AGENCY_A = "agency-a"
AGENCY_B = "agency-b"


class _AgencyScopedTripStore:
    """Fake TripStore: only agency-b owns trips; agency-a lookups miss."""

    owned_agency = AGENCY_B

    @staticmethod
    def get_trip_for_agency(trip_id: str, agency_id: str):
        if agency_id == _AgencyScopedTripStore.owned_agency:
            return {"id": trip_id, "agency_id": agency_id}
        return None


@pytest.fixture
def isolated_drafts(tmp_path, monkeypatch):
    """Keep draft JSON files inside tmp_path (never the repo data dir)."""
    monkeypatch.setattr(draft_store_module, "DRAFTS_DIR", tmp_path)
    monkeypatch.setattr(draft_store_module, "INDEX_FILE", tmp_path / "index.json")
    monkeypatch.setattr(drafts_router, "AuditStore", SimpleNamespace(log_event=MagicMock()))
    monkeypatch.setattr(drafts_router.persistence, "TripStore", _AgencyScopedTripStore)


def _agency(agency_id: str) -> SimpleNamespace:
    return SimpleNamespace(id=agency_id)


def _user(user_id: str) -> SimpleNamespace:
    return SimpleNamespace(id=user_id)


def test_promote_rejects_trip_from_other_agency(isolated_drafts):
    """Draft in agency A + trip visible only to agency B -> 404, draft unchanged."""
    draft = DraftStore.create(agency_id=AGENCY_A, created_by="user-1", name="Cross-tenant probe")

    with pytest.raises(HTTPException) as excinfo:
        promote_draft(
            draft.id,
            PromoteDraftRequest(trip_id="trip-b-1"),
            _agency(AGENCY_A),
            _user("user-1"),
        )

    assert excinfo.value.status_code == 404

    unchanged = DraftStore.get(draft.id)
    assert unchanged is not None
    assert unchanged.status == "open"
    assert unchanged.promoted_trip_id is None
    assert unchanged.promoted_at is None

    audit_log = drafts_router.AuditStore.log_event
    audit_log.assert_called_once_with(
        "draft_promote_denied",
        "user-1",
        {
            "draft_id": draft.id,
            "trip_id": "trip-b-1",
            "agency_id": AGENCY_A,
            "reason": "trip_not_in_agency",
        },
    )


def test_promote_succeeds_for_trip_in_own_agency(isolated_drafts):
    """Positive control: same-agency trip still promotes normally."""
    draft = DraftStore.create(agency_id=AGENCY_B, created_by="user-1", name="Same-tenant control")

    result = promote_draft(
        draft.id,
        PromoteDraftRequest(trip_id="trip-b-1"),
        _agency(AGENCY_B),
        _user("user-1"),
    )

    assert result["ok"] is True
    assert result["status"] == "promoted"
    promoted = DraftStore.get(draft.id)
    assert promoted is not None
    assert promoted.status == "promoted"
    assert promoted.promoted_trip_id == "trip-b-1"
    assert promoted.promoted_at is not None
