"""
tests/test_trip_history_scoping.py — PA-15 S2 evidence (2026-09-06).

FAILED BEFORE: /api/v1/trips/{trip_id}/history/* had no agency dependency at
all — any authenticated caller could read or push checkpoints onto another
agency's history stacks, and the stacks were in-memory and unbounded.

PASSES AFTER:
- every history endpoint requires the authenticated agency and verifies trip
  ownership via TripStore.get_trip_for_agency (404 on missing/foreign);
- stacks are keyed per (agency_id, trip_id) — agency A can never see agency
  B's checkpoints for the same trip id;
- the per-trip stack is capped at 50 entries with drop-oldest eviction.

Data safety: trips created here use unique per-run ids and are deleted on
teardown; canonical test agency data is never destructively touched.
"""

from __future__ import annotations

import uuid

import pytest

from spine_api.persistence import TEST_AGENCY_ID, TripStore
from src.state.mutation_history_stack import TripMutationHistoryStack

_OTHER_AGENCY = "agency_hist_other"


@pytest.fixture(autouse=True)
def _clear_history_stack():
    TripMutationHistoryStack.clear()
    yield
    TripMutationHistoryStack.clear()


@pytest.fixture()
def scoped_trip_id():
    trip_id = f"trip_hist_scope_{uuid.uuid4().hex[:10]}"
    TripStore.save_trip(
        {
            "id": trip_id,
            "status": "assigned",
            "stage": "proposal",
        },
        agency_id=TEST_AGENCY_ID,
    )
    yield trip_id
    try:
        TripStore.delete_trip_for_agency(trip_id, TEST_AGENCY_ID)
    except Exception:
        pass


def _get(client, trip_id, agency_id, path="/history"):
    return client.get(
        f"/api/v1/trips/{trip_id}{path}", headers={"X-Agency-ID": agency_id}
    )


def _post(client, trip_id, agency_id, path, body):
    return client.post(
        f"/api/v1/trips/{trip_id}{path}",
        json=body,
        headers={"X-Agency-ID": agency_id},
    )


def test_history_requires_trip_in_agency(session_client, scoped_trip_id):
    """Foreign/missing trips are indistinguishable: 404, not the history."""
    resp_foreign = _get(session_client, scoped_trip_id, _OTHER_AGENCY)
    assert resp_foreign.status_code == 404

    resp_missing = _get(
        session_client, f"trip_hist_missing_{uuid.uuid4().hex[:6]}", TEST_AGENCY_ID
    )
    assert resp_missing.status_code == 404


def test_history_scoped_per_agency(session_client, scoped_trip_id):
    """Agency B cannot read checkpoints pushed by agency A for the same trip."""
    push = _post(
        session_client,
        scoped_trip_id,
        TEST_AGENCY_ID,
        "/history/checkpoint",
        {"state_payload": {"budget": 1}, "description": "A's checkpoint"},
    )
    assert push.status_code == 200

    mine = _get(session_client, scoped_trip_id, TEST_AGENCY_ID)
    assert mine.status_code == 200
    assert mine.json()["timeline"]["undo_count"] == 1

    theirs = _get(session_client, scoped_trip_id, _OTHER_AGENCY)
    # Ownership check fires first: agency B gets 404, never agency A's history.
    assert theirs.status_code == 404


def test_undo_redo_return_payload_semantics(session_client, scoped_trip_id):
    """Checkpoint/undo/redo round-trip: payload returned, trip never written here."""
    push = _post(
        session_client,
        scoped_trip_id,
        TEST_AGENCY_ID,
        "/history/checkpoint",
        {"state_payload": {"budget": 5000}, "description": "before change"},
    )
    assert push.status_code == 200

    trip_before = TripStore.get_trip_for_agency(scoped_trip_id, TEST_AGENCY_ID)

    undo = _post(
        session_client,
        scoped_trip_id,
        TEST_AGENCY_ID,
        "/history/undo",
        {"current_live_state": {"budget": 9000}},
    )
    assert undo.status_code == 200
    assert undo.json()["restored_state"] == {"budget": 5000}

    # The router itself must not have written the trip (single write path).
    trip_after = TripStore.get_trip_for_agency(scoped_trip_id, TEST_AGENCY_ID)
    assert trip_after == trip_before

    redo = _post(
        session_client,
        scoped_trip_id,
        TEST_AGENCY_ID,
        "/history/redo",
        {"current_live_state": {"budget": 5000}},
    )
    assert redo.status_code == 200
    assert redo.json()["restored_state"] == {"budget": 9000}


def test_stack_cap_drop_oldest():
    """PA-15 bounds: >50 checkpoints keep the newest 50 (drop-oldest)."""
    trip_id = "trip_hist_cap"
    for i in range(60):
        TripMutationHistoryStack.push_checkpoint(
            trip_id,
            {"seq": i},
            description=f"checkpoint {i}",
            agency_id=TEST_AGENCY_ID,
        )
    timeline = TripMutationHistoryStack.get_timeline(trip_id, agency_id=TEST_AGENCY_ID)
    assert timeline["undo_count"] == TripMutationHistoryStack.MAX_STACK_DEPTH == 50
    seqs = [c["state_payload"]["seq"] for c in timeline["checkpoints"]]
    assert seqs[0] == 10  # oldest ten evicted
    assert seqs[-1] == 59  # newest retained


def test_stack_unscoped_callers_still_work():
    """Legacy unscoped in-process API (existing tests) keeps its behavior."""
    chk = TripMutationHistoryStack.push_checkpoint("trip_hist_legacy", {"v": 1})
    assert chk.trip_id == "trip_hist_legacy"
    assert chk.agency_id == ""
    restored = TripMutationHistoryStack.undo("trip_hist_legacy", {"v": 2})
    assert restored == {"v": 1}
