"""
Unit & Integration Tests for Booking Fulfillment Lifecycle (PER-FULFILL-OPS).

PA-02 / PA-05 update (2026-09-06): acceptance is now persisted durably on the
trip record and fulfillment verifies that durable field, persists
booking_confirmation, and read-back verifies it before claiming
FULFILLED_CONFIRMED. The previous version of this test passed without any
durable trip because the engine called nonexistent ``TripStore.get`` /
``TripStore.update`` and swallowed the AttributeError — fulfillment "succeeded"
with nothing persisted. Tests now seed durable per-test trip fixtures.
"""

import uuid

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from spine_api.persistence import TripStore
from spine_api.routers.fulfillment import router as fulfillment_router
from spine_api.routers.public_proposals import (
    AcceptProposalRequest,
    generate_signed_proposal_token,
    accept_proposal,
)
from src.orchestration.booking_fulfillment import BookingFulfillmentEngine


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("DATA_PRIVACY_MODE", "beta")
    monkeypatch.setenv("TRIPSTORE_BACKEND", "file")


def _seed_trip(prefix: str, destination: str = "Paris", cost: float = 4500.0) -> str:
    """Create an additive per-test durable trip fixture (unique id, never
    touching any pre-existing trip record)."""
    trip_id = f"trip_{prefix}_{uuid.uuid4().hex[:10]}"
    TripStore.save_trip(
        {
            "id": trip_id,
            "agency_id": "system",
            "status": "assigned",
            "destination": destination,
            "packet": {
                "destination": destination,
                "start_date": "2026-10-15",
                "end_date": "2026-10-22",
                "party_size": 2,
            },
            "strategy": {
                "recommended_option": {
                    "name": f"{destination} Luxury Escape",
                    "cost": cost,
                    "currency": "USD",
                }
            },
        },
        agency_id="system",
    )
    return trip_id


def _accept(token: str, signer: str, email: str):
    return accept_proposal(
        token=token,
        req=AcceptProposalRequest(
            signer_name=signer,
            signer_email=email,
            e_signature_consent=True,
        ),
    )


@pytest.mark.asyncio
async def test_acceptance_persists_durably_and_fulfillment_persists_with_readback():
    """PA-02 + PA-05 core proof:
    (i) acceptance writes the durable trip fields, and fulfillment persists
    booking_confirmation whose read-back matches the executed booking;
    (ii) the old code path could NOT do this — it never wrote the trip at all.
    """
    trip_id = _seed_trip("paf")
    token = generate_signed_proposal_token(trip_id=trip_id, agency_id="system")

    # 1. Acceptance must persist on the DURABLE trip record, not just the
    # process-local registry.
    accepted = _accept(token, "Sarah Connor", "sarah@sky.net")
    assert accepted.status == "accepted"

    stored = TripStore.get_trip(trip_id)
    assert stored is not None
    assert stored.get("proposal_accepted_at"), "acceptance must be durable on the trip"
    assert "Sarah Connor" in stored.get("proposal_accepted_by", "")
    assert stored.get("proposal_acceptance_token") == token
    assert stored.get("proposal_esign_consent") is True

    # 2. Fulfillment executes and persists booking_confirmation.
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
    # PA-05: sim-tier reality metadata on the result.
    assert result.reality_tier == "deterministic_preview"
    assert result.provider_connected is False

    # Read-back verification (PA-05): the trip record must carry the executed
    # booking — the old code returned FULFILLED_CONFIRMED with this absent.
    persisted = TripStore.get_trip(trip_id)
    confirmation = persisted.get("booking_confirmation") or {}
    assert confirmation.get("pnr_locator") == result.pnr_locator
    assert confirmation.get("e_ticket_number") == result.e_ticket_number
    assert confirmation.get("vcc_card_id") == result.vcc_card_id
    assert confirmation.get("total_charged_usd") == 4500.0
    # Part-H P1: the blob carries the reality gate so traveler UI can tell a
    # preview from a live booking.
    assert confirmation.get("reality_tier") == "deterministic_preview"
    assert confirmation.get("provider_connected") is False
    # Part-H P0: the side-effect-start marker + provider idempotency key
    # survive into the final confirmation.
    assert confirmation.get("side_effects_started_at")
    assert confirmation.get("fulfillment_provider_key")
    # AT-04: the SQL confirmation outcome is surfaced honestly (recorded when
    # a database session maker is configured; an explicit reason when not).
    assert isinstance(result.durable_confirmation, dict)
    assert result.durable_confirmation.get("recorded") in (True, False)

    # AT-01: the journey graph is persisted as the itinerary SSOT, not discarded.
    nodes = persisted.get("journey_graph_nodes") or []
    edges = persisted.get("journey_graph_edges") or []
    assert len(nodes) >= 1
    assert isinstance(edges, list)
    assert nodes[0].get("commitment_status") == "ticketed"
    assert nodes[0].get("confirmation_code") == result.pnr_locator
    assert result.idempotent_replay is False


@pytest.mark.asyncio
async def test_fulfillment_replays_existing_confirmation_without_second_vcc():
    """AT-03: a second fulfill must replay the stored PNR/VCC, not mint another."""
    trip_id = _seed_trip("once")
    token = generate_signed_proposal_token(trip_id=trip_id, agency_id="system")
    _accept(token, "Sarah Connor", "sarah@sky.net")

    first = await BookingFulfillmentEngine.fulfill_accepted_proposal(
        trip_id=trip_id,
        proposal_token=token,
        holder_id="test_advisor",
    )
    assert first.idempotent_replay is False
    first_pnr = first.pnr_locator
    first_vcc = first.vcc_card_id

    second = await BookingFulfillmentEngine.fulfill_accepted_proposal(
        trip_id=trip_id,
        proposal_token=token,
        holder_id="test_advisor",
    )
    assert second.idempotent_replay is True
    assert second.pnr_locator == first_pnr
    assert second.vcc_card_id == first_vcc
    assert second.status == "FULFILLED_CONFIRMED"

    persisted = TripStore.get_trip(trip_id)
    confirmation = persisted.get("booking_confirmation") or {}
    assert confirmation.get("pnr_locator") == first_pnr
    assert confirmation.get("vcc_card_id") == first_vcc


@pytest.mark.asyncio
async def test_fulfillment_rejected_without_durable_acceptance():
    """PA-02 negative proof: a registry-only acceptance (the OLD broken state —
    the registry row was flipped to accepted while the trip record stayed
    untouched) must not be fulfillable. The old code returned
    FULFILLED_CONFIRMED here because it never consulted the trip record."""
    from spine_api.routers.public_proposals import _get_or_create_proposal

    trip_id = _seed_trip("nacc")
    token = generate_signed_proposal_token(trip_id=trip_id, agency_id="system")

    # Build the registry row from the persisted trip, then simulate the old
    # registry-only acceptance: status flipped in-process, trip NOT updated.
    registry_proposal = _get_or_create_proposal(token)
    assert not TripStore.get_trip(trip_id).get("proposal_accepted_at")
    registry_proposal.status = "accepted"

    with pytest.raises(ValueError, match="not durably recorded"):
        await BookingFulfillmentEngine.fulfill_accepted_proposal(
            trip_id=trip_id,
            proposal_token=token,
            holder_id="test_advisor",
        )


@pytest.mark.asyncio
async def test_fulfillment_raises_when_tripstore_write_fails():
    """PA-05 fail-loud proof: a TripStore update failure must raise, not be
    swallowed into a 'successful' FULFILLED_CONFIRMED."""
    trip_id = _seed_trip("wrfail")
    token = generate_signed_proposal_token(trip_id=trip_id, agency_id="system")
    _accept(token, "Sarah Connor", "sarah@sky.net")

    def _boom(trip_id, updates):  # noqa: ARG001 - signature mirrors staticmethod call
        raise RuntimeError("simulated TripStore outage")

    original = TripStore.__dict__["update_trip"]
    try:
        TripStore.update_trip = staticmethod(_boom)
        # The raw store failure must propagate (fail loud). The old code
        # swallowed it with a warning and still returned FULFILLED_CONFIRMED.
        with pytest.raises(RuntimeError, match="simulated TripStore outage"):
            await BookingFulfillmentEngine.fulfill_accepted_proposal(
                trip_id=trip_id,
                proposal_token=token,
                holder_id="test_advisor",
            )
    finally:
        TripStore.update_trip = staticmethod(original)

    # Nothing may be claimed as persisted.
    stored = TripStore.get_trip(trip_id)
    assert not stored.get("booking_confirmation")


@pytest.mark.asyncio
async def test_fulfillment_rejected_for_unknown_trip():
    """PA-05: fulfillment against a trip that has no durable record must fail
    closed (the old code silently continued past the missing trip)."""
    from spine_api.routers.public_proposals import (
        PublicProposalView,
        _PROPOSAL_REGISTRY,
    )

    ghost_trip = f"trip_ghost_{uuid.uuid4().hex[:10]}"
    token = generate_signed_proposal_token(trip_id=ghost_trip, agency_id="system")

    # Registry-only accepted proposal for a trip that does not exist (stale
    # state). Since PA-02 acceptance now refuses to persist without a durable
    # trip, this row is seeded directly to represent that stale state.
    _PROPOSAL_REGISTRY[token] = PublicProposalView(
        token=token,
        trip_id=ghost_trip,
        title="Ghost Trip Proposal",
        destination="Nowhere",
        duration_days=5,
        traveler_name="Ghost Traveler",
        base_price_usd=1000.0,
        selected_total_price_usd=1000.0,
        currency="USD",
        status="accepted",
    )

    with pytest.raises(ValueError, match="no persisted record"):
        await BookingFulfillmentEngine.fulfill_accepted_proposal(
            trip_id=ghost_trip,
            proposal_token=token,
            holder_id="test_advisor",
        )


@pytest.fixture()
def client() -> TestClient:
    app = FastAPI()
    app.include_router(fulfillment_router)
    with TestClient(app) as test_client:
        yield test_client


def test_fulfillment_router_endpoint(client: TestClient):
    trip_id = _seed_trip("router", destination="London", cost=3500.0)
    token = generate_signed_proposal_token(trip_id=trip_id, agency_id="system")

    # Accept proposal (durable path)
    _accept(token, "John Connor", "john@res.org")

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
    # PA-05: the response truthfully labels the sim tier.
    assert fulfillment["reality_tier"] == "deterministic_preview"
    assert fulfillment["provider_connected"] is False

    # PA-05: the booking is durably persisted on the trip, not self-asserted.
    persisted = TripStore.get_trip(trip_id)
    assert (persisted.get("booking_confirmation") or {}).get("pnr_locator") == fulfillment["pnr_locator"]


def test_fulfillment_router_idempotency_key_replay(client: TestClient):
    """PA-40: a second fulfill with the same Idempotency-Key replays the
    original response instead of re-executing. The engine's once-booked guard
    (AT-03) makes a double-fulfill a no-op; the durable registry makes the
    retry observable and returns the first response verbatim."""
    trip_id = _seed_trip("router-idem", destination="London", cost=3500.0)
    token = generate_signed_proposal_token(trip_id=trip_id, agency_id="system")
    _accept(token, "Sarah Connor", "sarah@res.org")

    headers = {"Idempotency-Key": f"idem-{uuid.uuid4().hex[:8]}"}
    body = {
        "trip_id": trip_id,
        "proposal_token": token,
        "holder_id": "api_client_advisor",
    }

    first = client.post(
        "/api/v1/fulfillment/proposals/fulfill", json=body, headers=headers
    )
    assert first.status_code == 200
    first_payload = first.json()
    assert first_payload["status"] == "success"
    first_pnr = first_payload["fulfillment"]["pnr_locator"]
    # The original execution is not labeled as a replay.
    assert "idempotent_replay" not in first_payload

    second = client.post(
        "/api/v1/fulfillment/proposals/fulfill", json=body, headers=headers
    )
    assert second.status_code == 200
    second_payload = second.json()
    assert second_payload["idempotent_replay"] is True
    assert second_payload["fulfillment"]["pnr_locator"] == first_pnr
    assert (
        second_payload["fulfillment"]["vcc_card_id"]
        == first_payload["fulfillment"]["vcc_card_id"]
    )


def test_fulfillment_router_idempotency_key_body_mismatch(client: TestClient):
    """Part-H P2: the same Idempotency-Key with a DIFFERENT request body is a
    client error, not a replay — a key must never alias another request's
    confirmation."""
    trip_id = _seed_trip("router-idem-mismatch", destination="London", cost=3500.0)
    token = generate_signed_proposal_token(trip_id=trip_id, agency_id="system")
    _accept(token, "Kyle Reese", "kyle@res.org")

    headers = {"Idempotency-Key": f"idem-{uuid.uuid4().hex[:8]}"}
    first = client.post(
        "/api/v1/fulfillment/proposals/fulfill",
        json={"trip_id": trip_id, "proposal_token": token, "holder_id": "advisor_a"},
        headers=headers,
    )
    assert first.status_code == 200

    second = client.post(
        "/api/v1/fulfillment/proposals/fulfill",
        json={"trip_id": trip_id, "proposal_token": token, "holder_id": "advisor_b"},
        headers=headers,
    )
    assert second.status_code == 409
    assert second.json()["detail"]["reason"] == "idempotency_key_payload_mismatch"


@pytest.mark.asyncio
async def test_fulfillment_merges_confirmed_leg_into_existing_graph():
    """Part-H P1: fulfillment must not discard the compiler's persisted
    quoted sibling nodes — it merges the ticketed leg into the stored graph."""
    from datetime import datetime

    from src.schemas.journey_graph import (
        JourneyDependencyGraph,
        JourneyNode,
        NodeType,
    )

    trip_id = _seed_trip("graph-merge", destination="Rome", cost=5200.0)
    seed_graph = JourneyDependencyGraph(trip_id=trip_id)
    seed_graph.add_node(
        JourneyNode(
            node_id="N_HTL_QUOTED_1",
            node_type=NodeType.HOTEL_CHECKIN,
            title="Hotel Artemide (quoted)",
            start_time=datetime(2026, 10, 15, 15, 0),
            end_time=datetime(2026, 10, 15, 15, 0),
            location="Rome",
            provider="Demo Hotels",
            commitment_status="quoted",
        )
    )
    TripStore.update_trip(trip_id, seed_graph.to_stored_payload())

    token = generate_signed_proposal_token(trip_id=trip_id, agency_id="system")
    _accept(token, "Miles Dyson", "miles@cyberdyne.net")
    result = await BookingFulfillmentEngine.fulfill_accepted_proposal(
        trip_id=trip_id,
        proposal_token=token,
        holder_id="test_advisor",
    )
    assert result.status == "FULFILLED_CONFIRMED"

    persisted = TripStore.get_trip(trip_id)
    nodes = persisted.get("journey_graph_nodes") or []
    node_by_id = {n.get("node_id"): n for n in nodes}
    assert "N_HTL_QUOTED_1" in node_by_id, "quoted sibling node must survive fulfillment"
    assert node_by_id["N_HTL_QUOTED_1"]["commitment_status"] == "quoted"
    flight_nodes = [n for n in nodes if n.get("commitment_status") == "ticketed"]
    assert len(flight_nodes) == 1
    assert flight_nodes[0]["confirmation_code"] == result.pnr_locator


def test_amadeus_provider_idempotency_same_key_same_instruments():
    """Part-H P0: the sandbox GDS adapter derives instruments deterministically
    from the provider idempotency key, so crash-retry returns the same PNR."""
    from src.distribution.amadeus_sandbox_adapter import AmadeusSandboxAdapter

    first = AmadeusSandboxAdapter.create_flight_order(
        "OFF-1", "Test Traveler", idempotency_key="key-42"
    )
    second = AmadeusSandboxAdapter.create_flight_order(
        "OFF-1", "Test Traveler", idempotency_key="key-42"
    )
    other = AmadeusSandboxAdapter.create_flight_order(
        "OFF-1", "Test Traveler", idempotency_key="key-43"
    )
    assert first.pnr_locator == second.pnr_locator
    assert first.e_ticket_number == second.e_ticket_number
    assert first.booking_reference == second.booking_reference
    assert first.pnr_locator != other.pnr_locator
