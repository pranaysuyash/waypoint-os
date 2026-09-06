"""
Unit & Integration Tests for Booking Fulfillment Lifecycle (PER-FULFILL-OPS).
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from spine_api.routers.fulfillment import router as fulfillment_router
from spine_api.routers.public_proposals import (
    AcceptProposalRequest,
    PublicProposalView,
    _PROPOSAL_REGISTRY,
    accept_proposal,
    generate_signed_proposal_token,
)
from src.orchestration.booking_fulfillment import BookingFulfillmentEngine


@pytest.fixture()
def client() -> TestClient:
    app = FastAPI()
    app.include_router(fulfillment_router)
    with TestClient(app) as test_client:
        yield test_client


@pytest.mark.asyncio
async def test_booking_fulfillment_engine_lifecycle():
    trip_id = "TRIP-FULFILL-991"
    token = generate_signed_proposal_token(trip_id=trip_id, agency_id="system")

    # Seed the proposal registry with an open proposal
    proposal = PublicProposalView(
        token=token,
        trip_id=trip_id,
        title="Luxury Paris Escape",
        destination="Paris",
        duration_days=7,
        traveler_name="Sarah Connor",
        base_price_usd=4500.0,
        selected_total_price_usd=4500.0,
        currency="USD",
        status="open",
    )
    _PROPOSAL_REGISTRY[token] = proposal

    # 1. Proposal starts in open status -> fulfillment must reject
    with pytest.raises(ValueError, match="Only accepted proposals can be fulfilled"):
        await BookingFulfillmentEngine.fulfill_accepted_proposal(
            trip_id=trip_id,
            proposal_token=token,
            holder_id="test_advisor",
        )

    # 2. Client e-signs and accepts proposal
    accept_req = AcceptProposalRequest(
        signer_name="Sarah Connor",
        signer_email="sarah@sky.net",
        e_signature_consent=True,
    )
    accepted_prop = accept_proposal(token=token, req=accept_req)
    assert accepted_prop.status == "accepted"

    # 3. Fulfillment engine executes successfully
    result = await BookingFulfillmentEngine.fulfill_accepted_proposal(
        trip_id=trip_id,
        proposal_token=token,
        holder_id="test_advisor",
    )

    assert result.status == "FULFILLED_CONFIRMED"
    assert result.trip_id == trip_id
    assert len(result.pnr_locator) >= 5
    assert result.e_ticket_number.startswith("057-")
    assert result.vcc_card_id.startswith("ic_")
    assert result.total_charged_usd == 4500.0
    assert len(result.confirmed_journey_node_ids) > 0


def test_fulfillment_router_endpoint(client: TestClient):
    trip_id = "TRIP-ROUTER-772"
    token = generate_signed_proposal_token(trip_id=trip_id, agency_id="system")

    # Seed proposal
    proposal = PublicProposalView(
        token=token,
        trip_id=trip_id,
        title="London Roadshow",
        destination="London",
        duration_days=5,
        traveler_name="John Connor",
        base_price_usd=3500.0,
        selected_total_price_usd=3500.0,
        currency="USD",
        status="open",
    )
    _PROPOSAL_REGISTRY[token] = proposal

    # Accept proposal
    accept_req = AcceptProposalRequest(
        signer_name="John Connor",
        signer_email="john@res.org",
        e_signature_consent=True,
    )
    accept_proposal(token=token, req=accept_req)

    # Post to fulfillment router
    response = client.post(
        "/api/v1/fulfillment/proposals/fulfill",
        json={
            "trip_id": trip_id,
            "proposal_token": token,
            "holder_id": "api_client_advisor",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    fulfillment = data["fulfillment"]
    assert fulfillment["status"] == "FULFILLED_CONFIRMED"
    assert fulfillment["pnr_locator"] is not None
    assert fulfillment["vcc_card_id"] is not None
    assert fulfillment["total_charged_usd"] == 3500.0
