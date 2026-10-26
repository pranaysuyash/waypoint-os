"""T10 phase 1 (Recoveries Ledger): general entitlement tracking.

Covers: dual-backend create/list/transition, honesty-basis validation,
CAS lifecycle guards, tenant scoping, boundary vs claim_disposition
(disruption claims are NOT double-tracked here).

Memory backend is pinned so tests never touch the SQL ledger.
"""

import pytest
from starlette.testclient import TestClient

from spine_api.server import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    from types import SimpleNamespace

    monkeypatch.setenv("SPINE_API_DISABLE_AUTH", "1")
    monkeypatch.setenv("SPINE_API_RECOVERY_BACKEND", "memory")
    import spine_api.routers.recoveries as rec_router

    monkeypatch.setattr(
        rec_router.TripStore,
        "get_trip_for_agency",
        lambda trip_id, agency_id: TRIP if trip_id == "trip_rec_1" and agency_id == "agency_rec" else None,
    )
    original = dict(app.dependency_overrides)
    app.dependency_overrides[
        __import__("spine_api.core.auth", fromlist=["get_current_agency"]).get_current_agency
    ] = lambda: SimpleNamespace(id="agency_rec")
    try:
        yield
    finally:
        app.dependency_overrides = original


@pytest.fixture(autouse=True)
def _memory_store():
    from spine_api.services.recovery_store import RecoveryStore

    RecoveryStore._MEMORY_STORE.clear()
    yield


TRIP = {"id": "trip_rec_1", "agency_id": "agency_rec"}


def test_create_and_list_roundtrip():
    res = client.post(
        "/api/v1/trips/trip_rec_1/recoveries",
        json={
            "source_type": "price_drop",
            "counterparty": "IndiGo",
            "amount": 4200.0,
            "currency": "INR",
            "amount_basis": "modeled",
            "details": {"original_fare": 12000, "relock_fare": 7800},
        },
    )
    assert res.status_code == 201, res.text
    record = res.json()["recovery"]
    assert record["status"] == "detected"
    assert record["amount"] == 4200.0
    assert record["amount_basis"] == "modeled"

    feed = client.get("/api/v1/recoveries").json()
    assert feed["count"] == 1
    trip_scoped = client.get("/api/v1/trips/trip_rec_1/recoveries").json()
    assert trip_scoped["count"] == 1


def test_amount_basis_validation():
    res = client.post(
        "/api/v1/trips/trip_rec_1/recoveries",
        json={"source_type": "manual", "amount": 100.0, "amount_basis": None},
    )
    assert res.status_code == 422
    res = client.post(
        "/api/v1/trips/trip_rec_1/recoveries",
        json={"source_type": "manual", "amount_basis": "confirmed"},
    )
    assert res.status_code == 422
    res = client.post(
        "/api/v1/trips/trip_rec_1/recoveries",
        json={"source_type": "price_drop", "amount": 100.0, "amount_basis": "confirmed"},
    )
    assert res.status_code == 201


def test_cas_lifecycle_happy_path():
    created = client.post(
        "/api/v1/trips/trip_rec_1/recoveries",
        json={"source_type": "supplier_fault", "counterparty": "HotelPartner", "amount": 300.0, "amount_basis": "modeled"},
    ).json()["recovery"]
    rid = created["recovery_id"]

    # detected → filed → accepted → paid
    for step, payload in [
        ("filed", {}),
        ("accepted", {"amount": 250.0, "amount_basis": "confirmed"}),  # confirmed replaces model
        ("paid", {}),
    ]:
        res = client.post(f"/api/v1/recoveries/{rid}/transition", json={"to_status": step, **payload})
        assert res.status_code == 200, res.text
    final = client.get("/api/v1/recoveries").json()["recoveries"][0]
    assert final["status"] == "paid"
    assert final["amount"] == 250.0
    assert final["amount_basis"] == "confirmed"


def test_illegal_transition_rejected_422():
    created = client.post(
        "/api/v1/trips/trip_rec_1/recoveries",
        json={"source_type": "manual"},
    ).json()["recovery"]
    # detected → paid skips the lifecycle
    res = client.post(
        f"/api/v1/recoveries/{created['recovery_id']}/transition",
        json={"to_status": "paid"},
    )
    assert res.status_code == 422
    # Appeal path: rejected → filed is legal
    client.post(f"/api/v1/recoveries/{created['recovery_id']}/transition", json={"to_status": "filed"})
    res = client.post(
        f"/api/v1/recoveries/{created['recovery_id']}/transition",
        json={"to_status": "rejected"},
    )
    assert res.status_code == 200
    res = client.post(
        f"/api/v1/recoveries/{created['recovery_id']}/transition",
        json={"to_status": "filed"},  # re-file after rejection
    )
    assert res.status_code == 200


def test_disruption_claims_are_not_a_recovery_source():
    """Boundary vs claim_disposition: disruption claims have their own
    purpose-built 8-state machine; recording them here would double-track."""
    res = client.post(
        "/api/v1/trips/trip_rec_1/recoveries",
        json={"source_type": "disruption_claim"},
    )
    assert res.status_code == 422
    assert "Invalid source_type" in res.json()["detail"]


def test_cross_tenant_isolation():
    from spine_api.services.recovery_store import RecoveryStore

    RecoveryStore.create_recovery(
        agency_id="agency_other",
        source_type="manual",
        created_by="someone",
    )
    feed = client.get("/api/v1/recoveries").json()
    assert feed["count"] == 0  # tenant-scoped: agency_rec sees nothing
