"""
tests/test_booking_changes.py — FND-0410: booking-change ledger + traveler visibility.

Covers: operator report → durable trip ledger, validation contract (truth
taxonomy: no basis-free cancellation claims), same-window idempotency,
resolve-to-history (nothing deleted), honest traveler projection (Clara:
advisor-reported labels, minimum surface), and the proposal acceptance
stability contract (booking changes NEVER invalidate accepted revisions).
"""

import os

import pytest

os.environ["RUNNING_TESTS"] = "1"


@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    monkeypatch.setenv("DATA_PRIVACY_MODE", "beta")
    monkeypatch.setenv("SPINE_API_DISABLE_AUTH", "1")
    monkeypatch.setenv("TRIPSTORE_BACKEND", "file")


def _mk_trip(session_client, agency_id="agency_group_test", seed=None):
    # Unique customer per call: inbound-parse dedupe keys on
    # destination+customer, so identical pair would silently share one trip
    # across tests (and across runs).
    marker = seed or os.urandom(4).hex()
    inbound = session_client.post(
        "/api/v1/inbound/parse",
        json={
            "channel": "email",
            "raw_text": f"Rome family trip for 4 in June, hotel booked. Ref {marker}.",
            "customer_name": f"Test Booker {marker}",
        },
        headers={"X-Agency-ID": agency_id},
    ).json()
    return inbound["trip_id"]


def test_report_and_list_booking_change(session_client):
    trip_id = _mk_trip(session_client)
    headers = {"X-Agency-ID": "agency_group_test"}

    res = session_client.post(
        f"/api/v1/trips/{trip_id}/booking-changes",
        json={
            "change_kind": "overbook",
            "supplier": "hotel",
            "supplier_ref": "HTL-ROM-991",
            "basis_channel": "email",
            "basis_reference": "Hotel overbook notice",
            "notes": "Hotel claims overbook on June 12 night; relocations offered.",
            "affected_travelers": ["Test Booker"],
        },
        headers=headers,
    )
    assert res.status_code == 200
    row = res.json()["booking_change"]
    assert row["change_kind"] == "overbook"
    assert row["source"] == "operator_reported"  # D6: interim signal source
    assert row["status"] == "ACTIVE"
    assert row["idempotency_marker"].startswith("bkchg:")

    listed = session_client.get(f"/api/v1/trips/{trip_id}/booking-changes", headers=headers).json()
    assert len(listed["active"]) == 1
    assert listed["history"] == []


def test_duplicate_report_same_window_conflict(session_client):
    trip_id = _mk_trip(session_client)
    headers = {"X-Agency-ID": "agency_group_test"}
    body = {
        "change_kind": "overbook",
        "supplier": "hotel",
        "supplier_ref": "HTL-ROM-991",
        "notes": "Same report twice in one window.",
    }
    assert session_client.post(f"/api/v1/trips/{trip_id}/booking-changes", json=body, headers=headers).status_code == 200
    dup = session_client.post(f"/api/v1/trips/{trip_id}/booking-changes", json=body, headers=headers)
    assert dup.status_code == 409


def test_validation_contract(session_client):
    trip_id = _mk_trip(session_client)
    headers = {"X-Agency-ID": "agency_group_test"}

    bad_kind = session_client.post(
        f"/api/v1/trips/{trip_id}/booking-changes",
        json={"change_kind": "alien_invasion", "supplier": "hotel", "notes": "x"},
        headers=headers,
    )
    assert bad_kind.status_code == 422

    bad_supplier = session_client.post(
        f"/api/v1/trips/{trip_id}/booking-changes",
        json={"change_kind": "cancellation", "supplier": "moon_hotels", "notes": "x"},
        headers=headers,
    )
    assert bad_supplier.status_code == 422

    # Truth taxonomy: a cancellation claim with no basis text is refused.
    basis_free = session_client.post(
        f"/api/v1/trips/{trip_id}/booking-changes",
        json={"change_kind": "cancellation", "supplier": "hotel", "notes": "  "},
        headers=headers,
    )
    assert basis_free.status_code == 422


def test_resolve_archives_full_provenance(session_client):
    trip_id = _mk_trip(session_client)
    headers = {"X-Agency-ID": "agency_group_test"}
    row = session_client.post(
        f"/api/v1/trips/{trip_id}/booking-changes",
        json={"change_kind": "rate_change", "supplier": "hotel", "notes": "Rate adjusted post-confirmation."},
        headers=headers,
    ).json()["booking_change"]

    resolved = session_client.post(
        f"/api/v1/trips/{trip_id}/booking-changes/{row['change_id']}/resolve", headers=headers
    )
    assert resolved.status_code == 200
    listed = session_client.get(f"/api/v1/trips/{trip_id}/booking-changes", headers=headers).json()
    assert listed["active"] == []
    assert len(listed["history"]) == 1
    hist = listed["history"][0]
    assert hist["status"] == "RESOLVED"
    assert hist["change_id"] == row["change_id"]  # full provenance preserved


def test_traveler_shape_honest_labels_minimum_surface(session_client):
    """Clara constraint: traveler projection carries advisor-reported labeling
    and no operator identities or internal basis metadata."""
    trip_id = _mk_trip(session_client)
    headers = {"X-Agency-ID": "agency_group_test"}
    session_client.post(
        f"/api/v1/trips/{trip_id}/booking-changes",
        json={
            "change_kind": "cancellation",
            "supplier": "airline",
            "supplier_ref": "AI-101",
            "basis_channel": "phone",
            "basis_reference": "call with airline desk",
            "notes": "Airline canceled the June 12 leg.",
        },
        headers=headers,
    )
    view = session_client.get(
        f"/api/v1/trips/{trip_id}/booking-changes/traveler-view", headers=headers
    ).json()
    assert len(view["changes"]) == 1
    shape = view["changes"][0]
    assert shape["source_label"] == "Reported by your travel advisor"
    assert "reported_by" not in shape
    assert "basis_channel" not in shape
    assert "idempotency_marker" not in shape
    assert shape["change_kind"] == "cancellation"


def test_booking_changes_never_invalidate_accepted_revision():
    """The acceptance snapshot excludes booking_changes: reporting a change
    must NOT flip an accepted proposal into requires_reacceptance."""
    from spine_api.routers.public_proposals import PublicProposalView, _proposal_snapshot

    base = dict(
        token="prop_t",
        trip_id="trip_t",
        title="Rome",
        destination="Rome",
        duration_days=5,
        traveler_name="Traveler",
        base_price_usd=1000.0,
        selected_total_price_usd=1000.0,
    )
    view_without = PublicProposalView(**base)
    view_with = PublicProposalView(
        **base,
        booking_changes=[{"change_id": "bkchg_1", "change_kind": "overbook", "source": "operator_reported"}],
    )
    snap_without = _proposal_snapshot(view_without)
    snap_with = _proposal_snapshot(view_with)
    assert snap_without["revision_id"] == snap_with["revision_id"]
    assert "booking_changes" not in snap_with
