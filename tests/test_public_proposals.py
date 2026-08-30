from starlette.testclient import TestClient

from spine_api.routers.public_proposals import (
    generate_proposal_token,
)
from spine_api.server import app

client = TestClient(app)


def test_generate_proposal_token_deterministic():
    trip_id = "trip_2333bff6434d"
    token1 = generate_proposal_token(trip_id, "agency_1")
    token2 = generate_proposal_token(trip_id, "agency_1")
    assert token1 == token2
    assert token1.startswith("prop_")


def test_get_public_proposal_by_token():
    token = "prop_demo_italy_123"
    response = client.get(f"/api/public/proposals/{token}")
    assert response.status_code == 200
    data = response.json()
    assert data["token"] == token
    assert "destination" in data
    assert len(data["days"]) > 0
    assert len(data["available_options"]) > 0
    assert data["status"] == "open"


def test_calculate_proposal_options():
    token = "prop_calc_test_456"
    # First get proposal
    init_res = client.get(f"/api/public/proposals/{token}")
    assert init_res.status_code == 200
    base_price = init_res.json()["base_price_usd"]

    # Select hotel upgrade option
    calc_res = client.post(
        f"/api/public/proposals/{token}/calculate",
        json={"selected_option_ids": ["opt_hotel_upgrade"]},
    )
    assert calc_res.status_code == 200
    updated_data = calc_res.json()
    assert updated_data["selected_total_price_usd"] == round(base_price + 450.0, 2)


def test_accept_proposal_success_and_validation():
    token = "prop_accept_test_789"
    # Missing consent should fail with 400
    fail_res = client.post(
        f"/api/public/proposals/{token}/accept",
        json={
            "signer_name": "Priya Sharma",
            "signer_email": "priya@example.com",
            "selected_option_ids": [],
            "e_signature_consent": False,
        },
    )
    assert fail_res.status_code == 400

    # With consent should succeed
    success_res = client.post(
        f"/api/public/proposals/{token}/accept",
        json={
            "signer_name": "Priya Sharma",
            "signer_email": "priya@example.com",
            "selected_option_ids": ["opt_wine_tour"],
            "e_signature_consent": True,
        },
    )
    assert success_res.status_code == 200
    data = success_res.json()
    assert data["status"] == "accepted"
    assert "Priya Sharma" in data["accepted_by"]
    assert data["accepted_at"] is not None
