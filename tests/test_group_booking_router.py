"""
tests/test_group_booking_router.py — Unit & Integration tests for Group Multi-Payer Split Deposit Engine.
"""

import os
import uuid

import pytest

os.environ["RUNNING_TESTS"] = "1"

from spine_api.persistence import TripStore


@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    monkeypatch.setenv("DATA_PRIVACY_MODE", "beta")
    monkeypatch.setenv("SPINE_API_DISABLE_AUTH", "1")
    monkeypatch.setenv("TRIPSTORE_BACKEND", "file")


def test_group_booking_lifecycle_end_to_end(session_client):
    """Test generating group invites, public attendee token lookup, attendee payment notification, and advisor manual override."""
    # 1. Create a trip
    inbound_res = session_client.post(
        "/api/v1/inbound/parse",
        json={
            "channel": "email",
            "raw_text": "Bachelorette weekend in Cabo for 4 guests. Total budget $8,000.",
            "customer_name": "Jessica Miller",
        },
        headers={"X-Agency-ID": "agency_group_test"},
    ).json()

    trip_id = inbound_res["trip_id"]

    # 2. Generate group invites with agency custom payment URL
    invite_res = session_client.post(
        f"/api/v1/group/{trip_id}/invites",
        json={
            "trip_id": trip_id,
            "total_deposit_cents": 100000,  # $1,000 total deposit
            "agency_payment_url": "https://stripe.com/pay/plink_cabo_group_123",
            "payment_instructions": "Pay via Stripe link or wire to Agency Bank AC# 98765",
            "passengers": [
                {"name": "Jessica Miller", "email": "jessica@example.com"},
                {"name": "Chloe Bennett", "email": "chloe@example.com"},
                {"name": "Amanda Vance", "email": "amanda@example.com"},
                {"name": "Sarah Jenkins", "email": "sarah@example.com"},
            ],
        },
        headers={"X-Agency-ID": "agency_group_test"},
    )

    assert invite_res.status_code == 200
    invite_data = invite_res.json()
    assert invite_data["ok"] is True
    assert invite_data["passenger_count"] == 4
    assert invite_data["deposit_per_passenger_cents"] == 25000  # $250 each
    assert invite_data["agency_payment_url"] == "https://stripe.com/pay/plink_cabo_group_123"
    assert len(invite_data["passenger_invites"]) == 4

    p1 = invite_data["passenger_invites"][0]
    p2 = invite_data["passenger_invites"][1]
    p1_token = p1["token"]
    assert p1_token.startswith("grp_")
    assert "/g/grp_" in p1["web_url"]

    # 3. Public unauthenticated attendee lookup via token
    public_lookup = session_client.get(f"/api/v1/group/token/{p1_token}")
    assert public_lookup.status_code == 200
    public_data = public_lookup.json()
    assert public_data["ok"] is True
    assert public_data["passenger_name"] == "Jessica Miller"
    assert public_data["deposit_share_cents"] == 25000
    assert public_data["agency_payment_url"] == "https://stripe.com/pay/plink_cabo_group_123"
    assert public_data["status"] == "UNPAID"

    # 4. Attendee notifies advisor of payment sent & records preferences
    pay_notify = session_client.post(
        f"/api/v1/group/token/{p1_token}/pay-share",
        json={
            "payment_reference": "TXN_STRIPE_998877",
            "dietary_requirements": "Gluten-free",
            "room_preference": "Ocean view suite",
            "passport_country": "USA",
        },
    )

    assert pay_notify.status_code == 200
    pay_data = pay_notify.json()
    assert pay_data["ok"] is True
    assert pay_data["status"] == "NOTIFIED_PAID"

    # Verify updated status via public lookup
    public_lookup_after = session_client.get(f"/api/v1/group/token/{p1_token}").json()
    assert public_lookup_after["status"] == "NOTIFIED_PAID"
    assert public_lookup_after["collected_preferences"]["dietary_requirements"] == "Gluten-free"

    # 5. Advisor manually overrides and confirms shares
    override_p1 = session_client.post(
        f"/api/v1/group/{trip_id}/manual-override",
        json={
            "trip_id": trip_id,
            "passenger_id": p1["passenger_id"],
            "status": "CONFIRMED",
            "advisor_note": "Verified Stripe settlement in bank account",
        },
        headers={"X-Agency-ID": "agency_group_test"},
    )
    assert override_p1.status_code == 200
    assert override_p1.json()["all_group_shares_satisfied"] is False

    # Confirm remaining 3 passengers
    for p in [p2] + invite_data["passenger_invites"][2:]:
        session_client.post(
            f"/api/v1/group/{trip_id}/manual-override",
            json={
                "trip_id": trip_id,
                "passenger_id": p["passenger_id"],
                "status": "CONFIRMED",
                "advisor_note": "Confirmed by advisor",
            },
            headers={"X-Agency-ID": "agency_group_test"},
        )

    # Final override check to verify all_group_shares_satisfied is True
    final_override = session_client.post(
        f"/api/v1/group/{trip_id}/manual-override",
        json={
            "trip_id": trip_id,
            "passenger_id": p2["passenger_id"],
            "status": "CONFIRMED",
        },
        headers={"X-Agency-ID": "agency_group_test"},
    )
    assert final_override.status_code == 200
    assert final_override.json()["all_group_shares_satisfied"] is True


def test_pay_share_fails_closed_for_legacy_trip_without_agency_id(session_client):
    """FND-0290: a matched invite whose trip record lacks agency attribution is
    rejected (409) instead of being silently attributed to the test agency."""
    token = f"grp_fnd0290_{uuid.uuid4().hex}"
    legacy_trip = {
        "id": f"trip_gb_legacy_{uuid.uuid4().hex[:8]}",
        "destination": "Lisbon",
        "stage": "discovery",
        "status": "active",
        # NOTE: no "agency_id" — legacy record shape the old fallback silently
        # re-attributed to TEST_AGENCY_ID.
        "group_booking": {
            "invites": [
                {
                    "passenger_id": "p_1_legacy",
                    "name": "Legacy Passenger",
                    "raw_token": token,
                    "deposit_share_cents": 25000,
                    "status": "UNPAID",
                }
            ]
        },
    }
    TripStore.save_trip(legacy_trip)  # no agency_id → none stamped

    resp = session_client.post(
        f"/api/v1/group/token/{token}/pay-share",
        json={"payment_reference": "TXN_LEGACY_001"},
    )
    assert resp.status_code == 409, resp.text
    assert "agency attribution" in resp.text

    # The legacy record is left un-mutated (no status flip, no tenant stamp).
    stored = TripStore.get_trip(legacy_trip["id"])
    assert stored["group_booking"]["invites"][0]["status"] == "UNPAID"
    assert not stored.get("agency_id")


def test_invite_creation_stores_hash_only_never_raw_token(session_client):
    """FND-0382 pin: the capability credential (raw invite token) is shown once
    in the creation response and must never be persisted in stored trip JSON —
    only its sha256 hash + prefix (FND-0219 discipline). The raw_token matcher
    fallback in the routers/persistence stays for legacy records (exercised by
    test_pay_share_fails_closed_for_legacy_trip_without_agency_id), but NEW
    invites must not create that shape."""
    inbound_res = session_client.post(
        "/api/v1/inbound/parse",
        json={
            "channel": "email",
            "raw_text": "Cabo group deposit collection for 2 travelers. Total budget $2,000.",
            "customer_name": "Jessica Miller",
        },
        headers={"X-Agency-ID": "agency_group_test"},
    ).json()
    trip_id = inbound_res["trip_id"]

    invite_res = session_client.post(
        f"/api/v1/group/{trip_id}/invites",
        json={
            "trip_id": trip_id,
            "total_deposit_cents": 50000,
            "passengers": [
                {"name": "Jessica Miller", "email": "jessica@example.com"},
                {"name": "Chloe Bennett", "email": "chloe@example.com"},
            ],
        },
        headers={"X-Agency-ID": "agency_group_test"},
    )
    assert invite_res.status_code == 200, invite_res.text
    invite_data = invite_res.json()

    # Raw material appears exactly once — in the creation response.
    raw_tokens = [p["token"] for p in invite_data["passenger_invites"]]
    assert len(raw_tokens) == 2 and all(t.startswith("grp_") for t in raw_tokens)

    stored = TripStore.get_trip(trip_id)
    invites = stored["group_booking"]["invites"]
    assert len(invites) == 2
    for inv in invites:
        assert "raw_token" not in inv, (
            "invite persisted the raw capability credential (FND-0382)"
        )
        assert inv["token_hash"]
        assert inv["token_hash_prefix"] == inv["token_hash"][:8]
        # Hash matches the response's raw material — link works via hash alone.
        import hashlib

        matching_raw = next(t for t in raw_tokens if hashlib.sha256(t.encode()).hexdigest() == inv["token_hash"])
        assert matching_raw
