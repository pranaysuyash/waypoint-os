"""
tests/test_journey_graph_hydration.py — Journey Graph trip endpoints (PA-01).

S2 state transitions (failed-before / passes-after):
- FAILED BEFORE: the old test pinned the fabricated-fallback path — an
  unauthenticated GET with an arbitrary trip id returned HTTP 200 plus a
  synthesized "confirmed" DAG (PNR772 / Amadeus NDC / Blacklane / Belmond).
- PASSES AFTER: the router never synthesizes. The public route requires a
  valid signed proposal share token encoding the exact trip id; a valid token
  with no stored graph returns the soft abstention envelope
  ``{"ok": true, "exists": false, "reality_tier": "unavailable"}``; the
  tenant route returns 404 when no stored graph exists; cross-tenant reads
  return 404; scoped-lookup infrastructure failures surface as 503 instead of
  fabricated data.

Data safety: trips created here use unique per-run ids and are deleted in
cleanup (never touching the canonical test agency's seeded trips).
"""

from __future__ import annotations

import uuid

import pytest

from spine_api.persistence import TEST_AGENCY_ID, TripStore
from spine_api.routers.public_proposals import (
    generate_signed_proposal_token,
    verify_proposal_token,
)
import spine_api.routers.public_proposals as _public_proposals


@pytest.fixture(autouse=True)
def _isolate_proposal_revocation_store(tmp_path, monkeypatch):
    """PT-05: point the durable revocation store at a temp file so tests never
    touch the repo's real data/proposals/revoked_tokens.json."""
    monkeypatch.setattr(
        _public_proposals, "_REVOCATIONS_PATH", tmp_path / "revoked_tokens.json"
    )
    monkeypatch.setattr(_public_proposals, "_REVOKED_TOKENS", {})


@pytest.fixture
def stored_trip_factory():
    """Create agency-scoped trips with unique ids; delete on teardown."""
    created: list[tuple[str, str]] = []

    def _create(agency_id: str, extra: dict | None = None) -> str:
        trip_id = f"trip_jgh_{uuid.uuid4().hex[:10]}"
        payload = {
            "id": trip_id,
            "source": "test_journey_graph_hydration",
            "agency_id": agency_id,
            "status": "assigned",
            "stage": "proposal",
            "extracted": {},
            "validation": {},
            "decision": {},
            "raw_input": {},
        }
        if extra:
            payload.update(extra)
        TripStore.save_trip(payload, agency_id=agency_id)
        created.append((trip_id, agency_id))
        return trip_id

    yield _create

    for trip_id, agency_id in created:
        try:
            TripStore.delete_trip_for_agency(trip_id, agency_id)
        except Exception:
            pass


def _tenant_get(client, trip_id: str, agency_id: str):
    return client.get(
        f"/api/v1/journey-graph/{trip_id}", headers={"X-Agency-ID": agency_id}
    )


def test_tenant_route_no_stored_graph_returns_404_not_fabrication(session_client):
    """PA-01 S2: no stored graph -> 404, never a synthesized confirmed DAG."""
    trip_id = f"trip_jgh_missing_{uuid.uuid4().hex[:8]}"
    resp = _tenant_get(session_client, trip_id, TEST_AGENCY_ID)
    assert resp.status_code == 404
    body = resp.json()
    assert "PNR" not in str(body)
    assert "Amadeus" not in str(body)


def test_tenant_route_stored_graph_served_verbatim(
    session_client, stored_trip_factory
):
    """A stored journey graph is served exactly as persisted."""
    stored_nodes = [
        {
            "node_id": "N_STORED_FLT_1",
            "node_type": "FLIGHT",
            "title": "Stored flight",
            "provider": "StoredProvider",
            "confirmation_code": "STORED01",
        }
    ]
    trip_id = stored_trip_factory(
        TEST_AGENCY_ID,
        {
            "destination": "Lisbon",
            "journey_graph_nodes": stored_nodes,
            "booking_confirmation": {"pnr_locator": "STORED01"},
        },
    )
    resp = _tenant_get(session_client, trip_id, TEST_AGENCY_ID)
    assert resp.status_code == 200
    data = resp.json()
    assert [n["node_id"] for n in data["nodes"]] == ["N_STORED_FLT_1"]
    assert data["destination"] == "Lisbon"
    assert data["booking_confirmation"] == {"pnr_locator": "STORED01"}


def test_tenant_route_stored_trip_without_graph_404(
    session_client, stored_trip_factory
):
    """Trip exists but has no journey_graph_nodes -> documented 404 abstention."""
    trip_id = stored_trip_factory(TEST_AGENCY_ID, {"destination": "Kyoto"})
    resp = _tenant_get(session_client, trip_id, TEST_AGENCY_ID)
    assert resp.status_code == 404
    assert resp.json()["detail"] == "no journey graph available for this trip"


def test_tenant_route_cross_tenant_404(
    session_client,
    stored_trip_factory,
    boundary_principal_factory,
    boundary_token_factory,
):
    """A trip owned by another agency is indistinguishable from missing -> 404.

    FND-0259 hardening: the foreign caller is now a REAL second-tenant JWT
    (conftest boundary seam) instead of a spoofed ``X-Agency-ID`` header —
    the 404 must come from JWT-membership scoping, not from the removed
    PYTEST header escape.
    """
    foreign_agency = "agency_jgh_foreign"
    foreign_user = "usr_jgh_foreign"
    boundary_principal_factory(foreign_user, foreign_agency)
    trip_id = stored_trip_factory(TEST_AGENCY_ID, {"destination": "Oslo"})
    resp = session_client.get(
        f"/api/v1/journey-graph/{trip_id}",
        headers={"Authorization": f"Bearer {boundary_token_factory(foreign_user, foreign_agency)}"},
    )
    assert resp.status_code == 404


def test_tenant_route_lookup_failure_503(session_client, monkeypatch):
    """PA-01 S2: scoped-lookup infrastructure failure -> 503, not fake data."""

    def _boom(trip_id, agency_id):
        raise RuntimeError("simulated DB outage")

    monkeypatch.setattr(TripStore, "get_trip_for_agency", _boom)
    resp = _tenant_get(session_client, "trip_jgh_any", TEST_AGENCY_ID)
    assert resp.status_code == 503


# ---------------------------------------------------------------------------
# Public traveler companion route — capability-token gated
# ---------------------------------------------------------------------------


def test_public_route_no_token_404(session_client, stored_trip_factory):
    """PA-01 S2: previously this returned 200 + fabricated DAG with NO token.

    Now an unauthenticated request with an arbitrary trip id must not reveal
    existence and must never fabricate an itinerary."""
    trip_id = stored_trip_factory(TEST_AGENCY_ID, {"destination": "Paris"})
    resp = session_client.get(f"/api/public/journey-graph/{trip_id}")
    assert resp.status_code == 404
    assert "PNR772" not in resp.text
    assert "Belmond" not in resp.text


def test_public_route_invalid_or_mismatched_token_404(
    session_client, stored_trip_factory
):
    trip_id = stored_trip_factory(TEST_AGENCY_ID, {"destination": "Paris"})
    tampered = generate_signed_proposal_token(
        trip_id=trip_id, agency_id=TEST_AGENCY_ID
    )[:-4] + "beef"

    for bad_token in ("", "not-a-token", tampered):
        resp = session_client.get(
            f"/api/public/journey-graph/{trip_id}", params={"token": bad_token}
        )
        assert resp.status_code == 404

    # A valid token for a DIFFERENT trip must not unlock this trip.
    other_token = generate_signed_proposal_token(
        trip_id="trip_jgh_other_trip", agency_id=TEST_AGENCY_ID
    )
    resp = session_client.get(
        f"/api/public/journey-graph/{trip_id}", params={"token": other_token}
    )
    assert resp.status_code == 404


def test_public_route_valid_token_no_graph_soft_abstention(
    session_client, stored_trip_factory
):
    """Valid token + no stored graph -> documented soft abstention envelope."""
    trip_id = stored_trip_factory(TEST_AGENCY_ID, {"destination": "Paris"})
    token = generate_signed_proposal_token(
        trip_id=trip_id, agency_id=TEST_AGENCY_ID
    )
    is_valid, _reason, resolved_trip = verify_proposal_token(token)
    assert is_valid is True and resolved_trip == trip_id

    resp = session_client.get(
        f"/api/public/journey-graph/{trip_id}", params={"token": token}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert data["exists"] is False
    assert data["reality_tier"] == "unavailable"
    assert "nodes" not in data


def test_public_route_valid_token_stored_graph_only(
    session_client, stored_trip_factory
):
    """PA-01 S2: valid token + stored graph -> the stored graph, nothing else."""
    stored_nodes = [
        {
            "node_id": "N_PUB_FLT_1",
            "node_type": "FLIGHT",
            "title": "Confirmed stored flight",
            "provider": "StoredCarrier",
            "confirmation_code": "PUB123",
        }
    ]
    trip_id = stored_trip_factory(
        TEST_AGENCY_ID,
        {
            "destination": "Rome",
            "journey_graph_nodes": stored_nodes,
            "booking_confirmation": {"pnr_locator": "PUB123"},
        },
    )
    token = generate_signed_proposal_token(
        trip_id=trip_id, agency_id=TEST_AGENCY_ID
    )
    resp = session_client.get(
        f"/api/public/journey-graph/{trip_id}", params={"token": token}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert [n["node_id"] for n in data["nodes"]] == ["N_PUB_FLT_1"]
    assert data["destination"] == "Rome"
    # Fabricated canonical providers must never appear.
    assert all(n.get("provider") != "Amadeus NDC" for n in data["nodes"])
    assert all(n.get("provider") != "Belmond Luxury Properties" for n in data["nodes"])


def test_co_terminal_buffers_endpoint(session_client):
    """Static config endpoint keeps working after the PA-01 rewrite."""
    resp = session_client.get("/api/v1/journey-graph/co-terminal-buffers")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert len(data["buffers"]) > 0
