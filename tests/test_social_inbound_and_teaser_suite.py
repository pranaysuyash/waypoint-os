import os

os.environ["SPINE_API_DISABLE_AUTH"] = "1"
os.environ["DATA_PRIVACY_MODE"] = "beta"

import pytest
from fastapi.testclient import TestClient

from spine_api.server import app

client = TestClient(app)


def test_parse_social_inbound_success():
    payload = {
        "raw_text": "Hey! Looking to book Marrakech with 3 friends for my 30th birthday in November, budget is $4k/person. Want a 5-star riad and private desert tour.",
        "source": "instagram_dm",
        "creator_id": "creator_sarah",
        "client_name": "Jessica Vance",
        "deposit_amount": 25.0,
    }

    res = client.post("/api/v1/inbox/parse_social", json=payload)
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    data = res.json()

    assert data["ok"] is True
    assert data["stage"] == "STAGE_1_TEASER"
    assert data["destination"] == "Marrakech"
    assert data["is_masked"] is True
    assert data["suitability_score"] == 96
    assert "/proposals/trip_" in data["teaser_url"]


def test_parse_social_inbound_empty_text():
    payload = {
        "raw_text": "   ",
        "source": "direct_link",
    }
    res = client.post("/api/v1/inbox/parse_social", json=payload)
    assert res.status_code == 400


def test_unmask_teaser_proposal_flow():
    # 1. Create a teaser
    parse_payload = {
        "raw_text": "Need a Paris luxury trip for 2 people in October, budget $6,000.",
        "source": "extension",
        "creator_id": "creator_alex",
        "client_name": "Mark R.",
    }
    parse_res = client.post("/api/v1/inbox/parse_social", json=parse_payload)
    assert parse_res.status_code == 200
    parse_data = parse_res.json()

    trip_id = parse_data["trip_id"]
    teaser_url = parse_data["teaser_url"]
    token = teaser_url.split("token=")[1]

    # 2. Unmask teaser
    unmask_payload = {
        "trip_id": trip_id,
        "token": token,
        "deposit_payment_ref": "pay_test_25_dollar_hold",
    }
    unmask_res = client.post("/api/v1/inbox/unmask_teaser", json=unmask_payload)
    assert unmask_res.status_code == 200
    unmask_data = unmask_res.json()

    assert unmask_data["ok"] is True
    assert unmask_data["stage"] == "STAGE_2_DEPOSIT_PAID"
    assert unmask_data["is_masked"] is False
    assert "hotel_name" in unmask_data["unmasked_supplier_details"]


def test_corporate_policy_audit_compliant():
    audit_payload = {
        "trip_id": "trip_london_01",
        "destination": "London",
        "city_code": "LON",
        "hotel_rate_per_night": 320.0,  # Below London £350 cap
        "cabin_class": "ECONOMY",
        "employee_grade": "MANAGER",
    }
    res = client.post("/api/v1/corporate/policy-audit", json=audit_payload)
    assert res.status_code == 200
    data = res.json()

    assert data["ok"] is True
    assert data["is_compliant"] is True
    assert data["requires_approval"] is False
    assert len(data["violations"]) == 0


def test_corporate_policy_audit_violations():
    audit_payload = {
        "trip_id": "trip_london_02",
        "destination": "London",
        "city_code": "LON",
        "hotel_rate_per_night": 420.0,  # Exceeds £350 cap by £70
        "cabin_class": "BUSINESS",      # Violation for JUNIOR
        "employee_grade": "JUNIOR",
    }
    res = client.post("/api/v1/corporate/policy-audit", json=audit_payload)
    assert res.status_code == 200
    data = res.json()

    assert data["ok"] is True
    assert data["is_compliant"] is False
    assert data["requires_approval"] is True
    assert len(data["violations"]) >= 2
    codes = [v["code"] for v in data["violations"]]
    assert "PER_DIEM_EXCEEDED" in codes
    assert "CABIN_CLASS_DISCREPANCY" in codes


def test_corporate_duty_of_care_cockpit():
    res = client.get("/api/v1/corporate/duty-of-care/cockpit?company_id=comp_techcorp_01")
    assert res.status_code == 200
    data = res.json()

    assert data["ok"] is True
    assert data["company_id"] == "comp_techcorp_01"
    assert data["total_active_travelers"] >= 3
    assert data["disrupted_count"] >= 1
