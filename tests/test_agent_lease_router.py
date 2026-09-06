"""HTTP contract tests for the local agent-lease router.

These tests exercise the canonical router in isolation.  They prove request
validation and response/status mappings, not the server's auth dependency or a
durable SQL/worker integration.
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from spine_api.routers.agent_lease import router
from src.orchestration.agent_lease import DurableAgentLeaseManager


@pytest.fixture()
def client() -> TestClient:
    app = FastAPI()
    app.include_router(router)
    DurableAgentLeaseManager.clear()
    with TestClient(app) as test_client:
        yield test_client
    DurableAgentLeaseManager.clear()


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
