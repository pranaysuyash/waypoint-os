"""
tests/test_resilience_router.py — Router tests for PER-0924/0925 Resilience & Quarantine Endpoints.
"""

import os
import pytest

os.environ["RUNNING_TESTS"] = "1"


@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    monkeypatch.setenv("DATA_PRIVACY_MODE", "beta")
    monkeypatch.setenv("SPINE_API_DISABLE_AUTH", "1")
    monkeypatch.setenv("TRIPSTORE_BACKEND", "file")


def test_get_circuits_list(session_client):
    """Verify listing all active integration circuit breakers."""
    response = session_client.get(
        "/api/v1/resilience/circuits",
        headers={"X-Agency-ID": "agency_resilience_test"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_circuits"] >= 4
    circuit_names = [c["name"] for c in data["circuits"]]
    assert "supplier_ndc" in circuit_names
    assert "payment_gateway" in circuit_names


def test_reset_circuit(session_client):
    """Verify manually resetting a circuit breaker."""
    response = session_client.post(
        "/api/v1/resilience/circuits/supplier_ndc/reset",
        headers={"X-Agency-ID": "agency_resilience_test"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["circuit_name"] == "supplier_ndc"
    assert data["reset_successful"] is True
    assert data["state"] == "CLOSED"


def test_quarantine_intake_payload(session_client):
    """Verify isolating a poisoned intake payload via API."""
    response = session_client.post(
        "/api/v1/resilience/quarantine",
        json={
            "raw_input": "MALFORMED_PROMPT_INJECTION_BODY",
            "reason": "Suspicious directive override detected",
            "metadata": {"source_ip": "203.0.113.19"},
        },
        headers={"X-Agency-ID": "agency_resilience_test"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "QUARANTINED"
    assert data["incident_id"].startswith("inc_")

    # Verify incident appears in incident list
    inc_res = session_client.get(
        "/api/v1/resilience/incidents",
        headers={"X-Agency-ID": "agency_resilience_test"},
    )
    assert inc_res.status_code == 200
    incidents = inc_res.json()["incidents"]
    matching = [i for i in incidents if i["incident_id"] == data["incident_id"]]
    assert len(matching) == 1
    assert matching[0]["domain"] == "INTAKE_INGESTION"


def test_compensate_transaction_endpoint(session_client):
    """Verify triggering commercial rollback / compensation hold."""
    response = session_client.post(
        "/api/v1/resilience/compensate",
        json={
            "trip_id": "trip_test_compensate",
            "payment_id": "pi_live_9921",
            "amount": 2500.0,
            "reason": "Amadeus NDC ticketing connection timeout after payment",
        },
        headers={"X-Agency-ID": "agency_resilience_test"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "COMPENSATING_HOLD_INITIATED"
    assert data["refund_amount"] == 2500.0
    assert data["incident_id"].startswith("inc_")
