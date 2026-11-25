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


# ---------------------------------------------------------------------------
# FND-0409 — group payment collection: schedules, observed payments, reminders
# ---------------------------------------------------------------------------


def _mk_group_trip(session_client, agency_id="agency_group_test"):
    inbound_res = session_client.post(
        "/api/v1/inbound/parse",
        json={
            "channel": "email",
            "raw_text": "Amalfi coast group trip for 3 guests, spring.",
            "customer_name": "Chloe Bennett",
        },
        headers={"X-Agency-ID": agency_id},
    ).json()
    return inbound_res["trip_id"]


def test_equal_split_preserves_total_no_lost_cents(session_client):
    """FND-0409: the old total//count split silently dropped remainder cents
    (10001/3 lost a cent). Shares must always sum to the deposit total."""
    trip_id = _mk_group_trip(session_client)
    res = session_client.post(
        f"/api/v1/group/{trip_id}/invites",
        json={
            "trip_id": trip_id,
            "total_deposit_cents": 10001,
            "passengers": [{"name": "A"}, {"name": "B"}, {"name": "C"}],
        },
        headers={"X-Agency-ID": "agency_group_test"},
    )
    assert res.status_code == 200
    shares = [p["deposit_share_cents"] for p in res.json()["passenger_invites"]]
    assert sum(shares) == 10001
    assert shares == [3334, 3334, 3333]  # remainder spread, never lost


def test_custom_share_sum_mismatch_rejected(session_client):
    """FND-0409: itemized custom shares that do not balance to the deposit
    total are a money-truth fault — 422, never a silently unbalanced ledger."""
    trip_id = _mk_group_trip(session_client)
    res = session_client.post(
        f"/api/v1/group/{trip_id}/invites",
        json={
            "trip_id": trip_id,
            "total_deposit_cents": 100000,
            "passengers": [
                {"name": "Suite", "custom_share_cents": 60000, "share_note": "Master suite supplement"},
                {"name": "Budget", "custom_share_cents": 20000},
            ],
        },
        headers={"X-Agency-ID": "agency_group_test"},
    )
    assert res.status_code == 422


def test_custom_itemized_shares_with_note_flow_to_portal(session_client):
    """FND-0409 (Chloe JTBD): itemized shares + supplement note reach the
    traveler portal without exposing email (Clara constraint)."""
    trip_id = _mk_group_trip(session_client)
    res = session_client.post(
        f"/api/v1/group/{trip_id}/invites",
        json={
            "trip_id": trip_id,
            "total_deposit_cents": 100000,
            "passengers": [
                {"name": "Suite Guest", "custom_share_cents": 60000, "share_note": "Master suite supplement"},
                {"name": "Budget Guest", "custom_share_cents": 40000},
            ],
        },
        headers={"X-Agency-ID": "agency_group_test"},
    )
    assert res.status_code == 200
    raw_token = res.json()["passenger_invites"][0]["token"]
    portal = session_client.get(f"/api/v1/group/token/{raw_token}").json()
    assert portal["deposit_share_cents"] == 60000
    assert portal["share_note"] == "Master suite supplement"
    assert portal["outstanding_cents"] == 60000
    assert "email" not in portal  # minimal traveler PII


def test_schedule_set_and_derived_statuses(session_client):
    """FND-0409: group schedule set post-invite derives overdue/due_soon/
    upcoming per milestone — computed, never fabricated."""
    from datetime import datetime, timedelta, timezone

    trip_id = _mk_group_trip(session_client)
    invite_res = session_client.post(
        f"/api/v1/group/{trip_id}/invites",
        json={"trip_id": trip_id, "total_deposit_cents": 90000, "passengers": [{"name": "A"}, {"name": "B"}, {"name": "C"}]},
        headers={"X-Agency-ID": "agency_group_test"},
    )
    p1 = invite_res.json()["passenger_invites"][0]
    now = datetime.now(timezone.utc)
    sched_res = session_client.post(
        f"/api/v1/group/{trip_id}/schedule",
        json={
            "milestones": [
                {"label": "Deposit", "due_at": (now - timedelta(days=2)).isoformat()},
                {"label": "Final", "due_at": (now + timedelta(days=3)).isoformat()},
                {"label": "Extras", "due_at": (now + timedelta(days=40)).isoformat()},
            ]
        },
        headers={"X-Agency-ID": "agency_group_test"},
    )
    assert sched_res.status_code == 200

    summary = session_client.get(
        f"/api/v1/group/{trip_id}", headers={"X-Agency-ID": "agency_group_test"}
    ).json()
    view = next(p for p in summary["passengers"] if p["passenger_id"] == p1["passenger_id"])
    statuses = [m["status"] for m in view["schedule"]]
    assert statuses == ["overdue", "due_soon", "upcoming"]
    assert view["settlement"] == "unpaid"
    assert view["outstanding_cents"] == 30000


def test_record_payment_partial_then_settled(session_client):
    """FND-0409: observed payments track partial then full settlement;
    outstanding math is exact and money truth flows to the portal payload."""
    trip_id = _mk_group_trip(session_client)
    invite_res = session_client.post(
        f"/api/v1/group/{trip_id}/invites",
        json={"trip_id": trip_id, "total_deposit_cents": 50000, "passengers": [{"name": "A"}, {"name": "B"}]},
        headers={"X-Agency-ID": "agency_group_test"},
    )
    p1 = invite_res.json()["passenger_invites"][0]
    headers = {"X-Agency-ID": "agency_group_test"}

    rec1 = session_client.post(
        f"/api/v1/group/{trip_id}/record-payment",
        json={"passenger_id": p1["passenger_id"], "amount_cents": 10000, "method": "UPI", "reference": "UPI-1"},
        headers=headers,
    )
    assert rec1.status_code == 200
    assert rec1.json()["paid_cents"] == 10000
    assert rec1.json()["outstanding_cents"] == 15000  # 25000 share − 10000

    rec2 = session_client.post(
        f"/api/v1/group/{trip_id}/record-payment",
        json={"passenger_id": p1["passenger_id"], "amount_cents": 15000, "method": "BANK_TRANSFER"},
        headers=headers,
    )
    assert rec2.json()["paid_cents"] == 25000
    assert rec2.json()["outstanding_cents"] == 0

    summary = session_client.get(f"/api/v1/group/{trip_id}", headers=headers).json()
    view = next(p for p in summary["passengers"] if p["passenger_id"] == p1["passenger_id"])
    assert view["settlement"] == "paid"
    assert len(view["recorded_payments"]) == 2

    portal = session_client.get(f"/api/v1/group/token/{p1['token']}").json()
    assert portal["paid_cents"] == 25000
    assert portal["outstanding_cents"] == 0
    assert portal["settlement"] == "paid"


def test_reminder_drafts_overdue_only_and_log_send(session_client):
    """FND-0409: drafts derive only for outstanding shares with a real trigger;
    dispatch_channel is honestly operator_manual (DP-04b gate); logged sends
    append to the passenger's reminder history; settled passengers get none."""
    from datetime import datetime, timedelta, timezone

    trip_id = _mk_group_trip(session_client)
    invite_res = session_client.post(
        f"/api/v1/group/{trip_id}/invites",
        json={
            "trip_id": trip_id,
            "total_deposit_cents": 50000,
            "payment_instructions": "Wire to AC# 12345",
            "passengers": [{"name": "A"}, {"name": "B"}],
        },
        headers={"X-Agency-ID": "agency_group_test"},
    )
    p1, p2 = invite_res.json()["passenger_invites"]
    headers = {"X-Agency-ID": "agency_group_test"}
    now = datetime.now(timezone.utc)

    # No schedule yet → no fabricated urgency
    empty = session_client.get(f"/api/v1/group/{trip_id}/reminder-drafts", headers=headers).json()
    assert empty["drafts"] == []

    session_client.post(
        f"/api/v1/group/{trip_id}/schedule",
        json={"milestones": [{"label": "Deposit", "due_at": (now - timedelta(days=1)).isoformat()}]},
        headers=headers,
    )

    drafts = session_client.get(f"/api/v1/group/{trip_id}/reminder-drafts", headers=headers).json()["drafts"]
    assert len(drafts) == 2
    d1 = next(d for d in drafts if d["passenger_id"] == p1["passenger_id"])
    assert d1["trigger"] == "overdue"
    assert d1["dispatch_channel"] == "operator_manual"
    assert "Wire to AC# 12345" in d1["draft_text"]

    # Settle p1 — drafts must exclude settled passengers
    session_client.post(
        f"/api/v1/group/{trip_id}/record-payment",
        json={"passenger_id": p1["passenger_id"], "amount_cents": 25000, "method": "CASH"},
        headers=headers,
    )
    session_client.post(
        f"/api/v1/group/{trip_id}/manual-override",
        json={"trip_id": trip_id, "passenger_id": p1["passenger_id"], "status": "CONFIRMED"},
        headers=headers,
    )
    drafts_after = session_client.get(f"/api/v1/group/{trip_id}/reminder-drafts", headers=headers).json()["drafts"]
    assert [d["passenger_id"] for d in drafts_after] == [p2["passenger_id"]]

    # Operator logs a real send over their own channel
    logged = session_client.post(
        f"/api/v1/group/{trip_id}/log-reminder",
        json={"passenger_id": p2["passenger_id"], "channel": "whatsapp_manual", "note": "Sent via WA Web"},
        headers=headers,
    )
    assert logged.status_code == 200
    summary = session_client.get(f"/api/v1/group/{trip_id}", headers=headers).json()
    p2_view = next(p for p in summary["passengers"] if p["passenger_id"] == p2["passenger_id"])
    assert len(p2_view["reminders"]) == 1
    assert p2_view["reminders"][0]["channel"] == "whatsapp_manual"
