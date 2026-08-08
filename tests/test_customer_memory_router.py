"""
tests/test_customer_memory_router.py — Unit & Integration tests for Cross-Trip Customer Relationship Memory.
"""

import os
import pytest

os.environ["RUNNING_TESTS"] = "1"


@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    monkeypatch.setenv("DATA_PRIVACY_MODE", "beta")
    monkeypatch.setenv("SPINE_API_DISABLE_AUTH", "1")
    monkeypatch.setenv("TRIPSTORE_BACKEND", "file")


def test_customer_memory_lifecycle_end_to_end(session_client):
    """Test indexing customer preferences, searching relationship memory by email/phone, and auto-hydrating a new trip packet."""

    # 1. Remember preferences for repeat customer "Eleanor Vance"
    remember_res = session_client.post(
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
        headers={"X-Agency-ID": "agency_custmem_test"},
    )

    assert remember_res.status_code == 200
    remember_data = remember_res.json()
    assert remember_data["name"] == "Eleanor Vance"
    assert remember_data["email"] == "eleanor.vance@example.com"
    assert remember_data["dietary_requirements"] == "Strict Vegan & Nut-Free"
    assert "trip_past_001" in remember_data["source_trip_ids"]

    # 2. Lookup customer memory by email and phone
    email_lookup = session_client.get(
        "/api/v1/customers/memory?email=ELEANOR.VANCE@EXAMPLE.COM",
        headers={"X-Agency-ID": "agency_custmem_test"},
    )
    assert email_lookup.status_code == 200
    assert email_lookup.json()["customer_id"] == remember_data["customer_id"]

    phone_lookup = session_client.get(
        "/api/v1/customers/memory?phone=5550192834",
        headers={"X-Agency-ID": "agency_custmem_test"},
    )
    assert phone_lookup.status_code == 200
    assert phone_lookup.json()["customer_id"] == remember_data["customer_id"]

    # 3. Create a new inbound trip for Eleanor Vance
    inbound_res = session_client.post(
        "/api/v1/inbound/parse",
        json={
            "channel": "email",
            "raw_text": "Safari in Tanzania in August for 2 people. Budget $15,000.",
            "customer_name": "Eleanor Vance",
            "customer_email": "eleanor.vance@example.com",
        },
        headers={"X-Agency-ID": "agency_custmem_test"},
    ).json()

    trip_id = inbound_res["trip_id"]

    # 4. Auto-hydrate the new trip packet with Eleanor's remembered preferences
    hydrate_res = session_client.post(
        f"/api/v1/customers/hydrate-trip/{trip_id}",
        headers={"X-Agency-ID": "agency_custmem_test"},
    )

    assert hydrate_res.status_code == 200
    hydrate_data = hydrate_res.json()
    assert hydrate_data["ok"] is True
    assert hydrate_data["memory_found"] is True
    assert hydrate_data["customer_name"] == "Eleanor Vance"
    assert "dietary_requirements" in hydrate_data["hydrated_fields"]
    assert hydrate_data["preferences"]["dietary_requirements"] == "Strict Vegan & Nut-Free"
    assert hydrate_data["preferences"]["room_preference"] == "High-floor quiet corner suite"
