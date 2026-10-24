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


@pytest.fixture(autouse=True)
def materialize_custmem_tenant(boundary_principal_factory):
    """FND-0060 residual: profiles are now durable SQL rows whose agency_id
    is an FK to agencies.id, so the test tenant must exist in SQL before the
    lifecycle runs. Additive only (ON CONFLICT DO NOTHING)."""
    boundary_principal_factory("usr_custmem_lifecycle", "agency_custmem_test")


def test_customer_memory_lifecycle_end_to_end(session_client):
    """Test indexing customer preferences, searching relationship memory by email/phone, and auto-hydrating a new trip packet."""
    # Per-run identity (test-isolation, FND-0366 architecture follow-up): the
    # inbound door resolves leads by email/phone/name (FND-0334), so a fixed
    # "Eleanor Vance" matches STALE leads accumulated in the shared file store
    # — including pre-ADR-008 trips whose packet still carries memory facts —
    # and the display-only invariant then asserts against the wrong trip. A
    # unique identity per run guarantees the lifecycle exercises only trips
    # this test created, regardless of store history.
    import uuid as _uuid

    _suffix = _uuid.uuid4().hex[:8]
    cust_name = f"Eleanor Vance {_suffix}"
    cust_email = f"eleanor.vance.{_suffix}@example.com"
    cust_phone = f"+1-555-019-{int(_suffix[:4], 16) % 10000:04d}"
    cust_phone_digits = cust_phone.replace("-", "").replace("+", "")

    # 1. Remember preferences for repeat customer "Eleanor Vance"
    remember_res = session_client.post(
        "/api/v1/customers/remember",
        json={
            "name": cust_name,
            "email": cust_email,
            "phone": cust_phone,
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
    assert remember_data["name"] == cust_name
    assert remember_data["email"] == cust_email
    assert remember_data["dietary_requirements"] == "Strict Vegan & Nut-Free"
    assert "trip_past_001" in remember_data["source_trip_ids"]

    # 2. Lookup customer memory by email and phone
    email_lookup = session_client.get(
        "/api/v1/customers/memory?email=" + cust_email.upper(),
        headers={"X-Agency-ID": "agency_custmem_test"},
    )
    assert email_lookup.status_code == 200
    assert email_lookup.json()["customer_id"] == remember_data["customer_id"]

    phone_lookup = session_client.get(
        "/api/v1/customers/memory?phone=" + cust_phone_digits,
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
            "customer_name": cust_name,
            "customer_email": cust_email,
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
    assert hydrate_data["customer_name"] == cust_name
    assert "dietary_requirements" in hydrate_data["hydrated_fields"]
    assert hydrate_data["preferences"]["dietary_requirements"] == "Strict Vegan & Nut-Free"
    assert hydrate_data["preferences"]["room_preference"] == "High-floor quiet corner suite"

    # 5. E-D slot 2 display contract: durable facts are primary (source
    # "memory", gate-categorized, freshness-horizoned), registry is fallback.
    assert hydrate_data["facts"], "on-file facts must carry provenance"
    assert hydrate_data["customer_id"] == remember_data["customer_id"]
    dietary_fact = next(
        f for f in hydrate_data["facts"] if f["field_name"] == "dietary_requirements"
    )
    assert "Vegan" in dietary_fact["value"]
    assert dietary_fact["source"] == "memory"
    assert dietary_fact["observed_at"]
    seating_fact = next(
        f for f in hydrate_data["facts"] if f["field_name"] == "seating_preference"
    )
    assert seating_fact["source"] == "memory"
    # Room is durably ingested under a gate-assigned generic category; its
    # chip must still surface (field-less) and suppress the registry double.
    assert any("quiet corner suite" in f["value"].lower() for f in hydrate_data["facts"])
    assert not [
        f for f in hydrate_data["facts"]
        if f["source"] == "memory:profile" and f["field_name"] == "room_preference"
    ]

    # 6. Display-only invariant: memory facts never enter the trip packet
    # (ADR-008 §7 row 4 — the former hydrate packet-write was the
    # memory→packet influence path E-D forbids).
    from spine_api.persistence import TripStore

    stored_trip = TripStore.get_trip_for_agency(trip_id, "agency_custmem_test")
    extracted = (stored_trip or {}).get("extracted") or {}
    assert not extracted.get("dietary"), "hydrate must not write memory facts into the packet"
    assert "customer_memory_applied" not in (stored_trip or {})

    # 7. X-14 purge propagation through the HTTP seam: after GDPR forget,
    # the display surface returns nothing for that traveler.
    forget_res = session_client.post(
        "/api/v1/customers/memory/forget",
        json={"customer_id": remember_data["customer_id"]},
        headers={"X-Agency-ID": "agency_custmem_test"},
    )
    assert forget_res.status_code == 200
    assert forget_res.json()["ok"] is True

    post_forget = session_client.post(
        f"/api/v1/customers/hydrate-trip/{trip_id}",
        headers={"X-Agency-ID": "agency_custmem_test"},
    )
    assert post_forget.status_code == 200
    assert post_forget.json()["memory_found"] is False
    assert post_forget.json()["facts"] == []
