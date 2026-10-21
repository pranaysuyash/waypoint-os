"""HTTP contract tests for the local agent-lease router.

These tests exercise the canonical router in isolation.  They prove request
validation and response/status mappings, plus the FND-0213 agency scoping
(JWT-derived tenant, lease agency stamp, cross-tenant 404), not the server's
auth dependency wiring or a durable SQL/worker integration.
"""

from __future__ import annotations

from typing import Optional

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import spine_api.routers.agent_lease as lease_router_module
from spine_api.routers.agent_lease import router
from src.orchestration.agent_lease import DurableAgentLeaseManager


class _StubTripStore:
    """Hermetic stand-in: any trip id exists in whatever agency asks (unit seam)."""

    @staticmethod
    def get_trip_for_agency(trip_id: str, agency_id: str) -> Optional[dict]:
        return {"trip_id": trip_id, "agency_id": agency_id}


def _make_client(agency_id: str, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[lease_router_module.get_current_agency_id] = lambda: agency_id
    app.dependency_overrides[lease_router_module.get_current_user] = lambda: None
    monkeypatch.setattr(lease_router_module, "TripStore", _StubTripStore)
    return TestClient(app)


@pytest.fixture(autouse=True)
def _isolated_lease_state():
    """Per-test isolation of the (class-level, process-global) lease backend."""
    DurableAgentLeaseManager.clear()
    yield
    DurableAgentLeaseManager.clear()


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    test_client = _make_client("agency-test", monkeypatch)
    with test_client:
        yield test_client


def test_acquire_and_inspect_return_canonical_lease_envelope(client: TestClient) -> None:
    response = client.post(
        "/api/v1/orchestration/leases/acquire",
        json={"trip_id": "trip-router-1", "holder_id": "worker-a"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "acquired"
    assert body["lease"]["trip_id"] == "trip-router-1"
    assert body["lease"]["holder_id"] == "worker-a"
    assert body["lease"]["fencing_token"] == 1

    inspected = client.get("/api/v1/orchestration/leases/trip-router-1")
    assert inspected.status_code == 200
    assert inspected.json()["status"] == "locked"
    assert inspected.json()["lease"]["lease_token"] == body["lease"]["lease_token"]


def test_contention_maps_to_conflict_and_invalid_ttl_maps_to_validation(client: TestClient) -> None:
    first = client.post(
        "/api/v1/orchestration/leases/acquire",
        json={"trip_id": "trip-router-2", "holder_id": "worker-a"},
    )
    assert first.status_code == 200

    contention = client.post(
        "/api/v1/orchestration/leases/acquire",
        json={"trip_id": "trip-router-2", "holder_id": "worker-b"},
    )
    assert contention.status_code == 409

    invalid = client.post(
        "/api/v1/orchestration/leases/acquire",
        json={"trip_id": "trip-router-3", "holder_id": "worker-a", "ttl_seconds": 301},
    )
    assert invalid.status_code == 422


def test_renew_release_and_fencing_statuses_are_explicit(client: TestClient) -> None:
    acquired = client.post(
        "/api/v1/orchestration/leases/acquire",
        json={"trip_id": "trip-router-4", "holder_id": "worker-a"},
    ).json()["lease"]
    token = acquired["lease_token"]
    fencing = acquired["fencing_token"]

    renewed = client.post(
        "/api/v1/orchestration/leases/renew",
        json={"trip_id": "trip-router-4", "lease_token": token},
    )
    assert renewed.status_code == 200
    assert renewed.json()["status"] == "renewed"

    assert client.post(
        "/api/v1/orchestration/leases/verify-fencing",
        json={"trip_id": "trip-router-4", "fencing_token": fencing},
    ).json() == {
        "status": "valid",
        "is_valid": True,
        "trip_id": "trip-router-4",
        "fencing_token": fencing,
    }

    released = client.post(
        "/api/v1/orchestration/leases/release",
        json={"trip_id": "trip-router-4", "lease_token": token},
    )
    assert released.status_code == 200
    assert released.json()["status"] == "released"
    assert released.json()["released"] is True

    stale_renew = client.post(
        "/api/v1/orchestration/leases/renew",
        json={"trip_id": "trip-router-4", "lease_token": token},
    )
    assert stale_renew.status_code == 404

    stale_fence = client.post(
        "/api/v1/orchestration/leases/verify-fencing",
        json={"trip_id": "trip-router-4", "fencing_token": fencing},
    )
    assert stale_fence.status_code == 200
    assert stale_fence.json()["status"] == "stale_or_invalid"
    assert stale_fence.json()["is_valid"] is False


def test_release_is_idempotent_and_missing_inspection_is_unlocked(client: TestClient) -> None:
    missing_release = client.post(
        "/api/v1/orchestration/leases/release",
        json={"trip_id": "trip-router-missing", "lease_token": "no-token"},
    )
    assert missing_release.status_code == 200
    assert missing_release.json()["status"] == "not_found"
    assert missing_release.json()["released"] is False

    inspected = client.get("/api/v1/orchestration/leases/trip-router-missing")
    assert inspected.status_code == 200
    assert inspected.json() == {
        "status": "unlocked",
        "trip_id": "trip-router-missing",
        "lease": None,
    }


# ---------------------------------------------------------------------------
# FND-0213: agency scoping
# ---------------------------------------------------------------------------


def test_acquire_stamps_authenticated_agency_and_client_cannot_override(client: TestClient) -> None:
    response = client.post(
        "/api/v1/orchestration/leases/acquire",
        json={
            "trip_id": "trip-agency-1",
            "holder_id": "worker-a",
            "metadata": {"agency_id": "agency-EVIL", "note": "hello"},
        },
    )
    assert response.status_code == 200
    lease = response.json()["lease"]
    assert lease["metadata"]["agency_id"] == "agency-test"  # authenticated tenant wins
    assert lease["metadata"]["note"] == "hello"  # unrelated metadata preserved


def test_cross_tenant_lease_operations_are_uniform_404(monkeypatch: pytest.MonkeyPatch) -> None:
    owner_client = _make_client("agency-owner", monkeypatch)
    with owner_client:
        acquired = owner_client.post(
            "/api/v1/orchestration/leases/acquire",
            json={"trip_id": "trip-cross-1", "holder_id": "worker-a"},
        )
        assert acquired.status_code == 200

    attacker_client = _make_client("agency-attacker", monkeypatch)
    with attacker_client:
        trip = "trip-cross-1"
        # Trip exists in the attacker's agency scope in this stub world, so any
        # 404 below comes from the lease agency stamp — the cross-tenant guard.
        renew = attacker_client.post(
            "/api/v1/orchestration/leases/renew",
            json={"trip_id": trip, "lease_token": "whatever"},
        )
        assert renew.status_code == 404

        release = attacker_client.post(
            "/api/v1/orchestration/leases/release",
            json={"trip_id": trip, "lease_token": "whatever"},
        )
        assert release.status_code == 404

        inspect = attacker_client.get(f"/api/v1/orchestration/leases/{trip}")
        assert inspect.status_code == 404

        verify = attacker_client.post(
            "/api/v1/orchestration/leases/verify-fencing",
            json={"trip_id": trip, "fencing_token": 1},
        )
        assert verify.status_code == 404

    # Owner retains full access.
    with owner_client:
        inspected = owner_client.get("/api/v1/orchestration/leases/trip-cross-1")
        assert inspected.status_code == 200
        assert inspected.json()["status"] == "locked"
