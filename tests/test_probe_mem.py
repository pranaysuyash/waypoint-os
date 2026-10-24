"""Temporary probe (deleted after diagnosis): capture the writer of extracted.dietary."""

import pytest


@pytest.fixture(autouse=True)
def _probe_env(monkeypatch):
    monkeypatch.setenv("DATA_PRIVACY_MODE", "beta")
    monkeypatch.setenv("SPINE_API_DISABLE_AUTH", "1")
    monkeypatch.setenv("TRIPSTORE_BACKEND", "file")


def test_probe_mem_steps(session_client, boundary_principal_factory, monkeypatch):
    import json as _json
    import traceback

    boundary_principal_factory("usr_custmem_lifecycle", "agency_custmem_test")

    real_dump = _json.dump

    def spying_dump(obj, f, *a, **kw):
        try:
            if isinstance(obj, dict):
                extracted = obj.get("extracted")
                if isinstance(extracted, dict) and extracted.get("dietary"):
                    print("=== dietary FILE-WRITE ===")
                    traceback.print_stack()
                    print("=== end ===")
        except Exception:
            pass
        return real_dump(obj, f, *a, **kw)

    monkeypatch.setattr("spine_api.persistence.json.dump", spying_dump)

    H = {"X-Agency-ID": "agency_custmem_test"}
    r = session_client.post(
        "/api/v1/customers/remember",
        json={
            "name": "Eleanor Vance",
            "email": "eleanor.vance@example.com",
            "phone": "+1-555-019-2834",
            "dietary_requirements": "Strict Vegan & Nut-Free",
            "room_preference": "High-floor quiet corner suite",
            "seating_preference": "Window seat forward cabin",
            "passport_country": "United States",
            "passport_expiry": "2031-10-15",
            "source_trip_id": "trip_past_001",
        },
        headers=H,
    )
    assert r.status_code == 200, r.text

    p = session_client.post(
        "/api/v1/inbound/parse",
        json={
            "channel": "email",
            "raw_text": "Safari in Tanzania in August for 2 people. Budget $15,000.",
            "customer_name": "Eleanor Vance",
            "customer_email": "eleanor.vance@example.com",
        },
        headers=H,
    ).json()
    print("TRIP:", p.get("trip_id"))
