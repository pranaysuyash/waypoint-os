"""
End-to-End Autonomous Proposal Compiler Tests (PER-INT-E2E).

PA-25 update (2026-09-06): the compiled package is synthetic (sandbox air
offers plus fabricated Belmond/Blacklane-style providers), so it carries
reality-tier metadata and share-token minting is BLOCKED by default. The
previous assertion pinned the old dishonest behavior — the compiler minted a
signed share token for fabricated inventory — so that assertion was rewritten
to pin the honesty contract instead.
"""

from datetime import date, timedelta

import pytest

from src.orchestration.proposal_compiler import AutonomousProposalCompiler


@pytest.fixture(autouse=True)
def _file_store(monkeypatch):
    monkeypatch.setenv("DATA_PRIVACY_MODE", "beta")
    monkeypatch.setenv("TRIPSTORE_BACKEND", "file")


def _compile(**overrides):
    dep_date = date.today() + timedelta(days=60)
    ret_date = dep_date + timedelta(days=7)
    params = dict(
        trip_id="TRIP-COMPILER-001",
        raw_intake_text="We want a luxury 7-day trip to Paris with private chauffeur transfers. No ground floor rooms.",
        destination="Paris",
        departure_date=dep_date,
        return_date=ret_date,
        traveler_count=2,
        price_sensitivity=0.1,  # Luxury
        peak_season=True,
    )
    params.update(overrides)
    return AutonomousProposalCompiler.compile_from_intake(**params)


def test_autonomous_proposal_compilation():
    package = _compile()

    assert package.trip_id == "TRIP-COMPILER-001"
    assert package.destination == "Paris"
    assert package.is_feasibility_passed is True
    assert package.journey_graph_node_count >= 3
    assert package.net_supplier_cost_usd > 0
    assert package.gross_customer_price_usd > package.net_supplier_cost_usd
    assert package.gross_margin_usd > 0


def test_compiled_package_labels_simulated_reality_and_blocks_share_by_default():
    """PA-25: synthetic inventory is labeled, and no signed share credential is
    minted for it by default."""
    package = _compile()

    assert package.reality_tier == "deterministic_preview"
    assert package.provider_connected is False
    # Share minting blocked for simulated inventory.
    assert package.share_token is None
    assert package.proposal_share_url is None
    assert package.share_blocked_reason == "simulated_inventory"

    as_dict = package.to_dict()
    assert as_dict["share_token"] is None
    assert as_dict["share_blocked_reason"] == "simulated_inventory"
    assert as_dict["reality_tier"] == "deterministic_preview"
    assert as_dict["provider_connected"] is False


def test_compiler_persists_quoted_graph_on_existing_trip_only():
    """AT-01: compile writes quoted nodes onto an existing trip, never invents one."""
    import uuid

    from spine_api.persistence import TripStore

    trip_id = f"trip_compiler_{uuid.uuid4().hex[:8]}"
    TripStore.save_trip(
        {"id": trip_id, "agency_id": "system", "destination": "Paris", "status": "assigned"},
        agency_id="system",
    )
    package = _compile(trip_id=trip_id)
    assert package.journey_graph_node_count >= 3

    stored = TripStore.get_trip(trip_id)
    nodes = stored.get("journey_graph_nodes") or []
    edges = stored.get("journey_graph_edges") or []
    assert len(nodes) >= 3
    assert len(edges) >= 1
    assert all(n.get("commitment_status") == "quoted" for n in nodes)
    assert all(n.get("metadata", {}).get("provider_connected") is False for n in nodes)


def test_compiler_does_not_overwrite_ticketed_nodes():
    """AT-02: a ticketed itinerary is locked against compiler re-quote."""
    import uuid
    from datetime import datetime, timezone

    from spine_api.persistence import TripStore
    from src.schemas.journey_graph import JourneyDependencyGraph, JourneyNode, NodeType

    trip_id = f"trip_compiler_lock_{uuid.uuid4().hex[:8]}"
    now = datetime.now(timezone.utc)
    graph = JourneyDependencyGraph(trip_id=trip_id)
    graph.add_node(
        JourneyNode(
            node_id="N_LOCKED",
            node_type=NodeType.FLIGHT,
            title="Already ticketed",
            start_time=now,
            end_time=now,
            location="CDG",
            provider="Air France",
            confirmation_code="LOCKED1",
            commitment_status="ticketed",
        )
    )
    TripStore.save_trip(
        {
            "id": trip_id,
            "agency_id": "system",
            "destination": "Paris",
            **graph.to_stored_payload(),
        },
        agency_id="system",
    )
    _compile(trip_id=trip_id)
    stored = TripStore.get_trip(trip_id)
    nodes = stored.get("journey_graph_nodes") or []
    assert len(nodes) == 1
    assert nodes[0]["node_id"] == "N_LOCKED"
    assert nodes[0]["commitment_status"] == "ticketed"
    assert nodes[0]["confirmation_code"] == "LOCKED1"


def test_share_minting_requires_explicit_simulated_opt_in():
    """PA-25: only an explicit allow_share_for_simulated=True mints a share
    token for synthetic inventory."""
    package = _compile(allow_share_for_simulated=True)

    assert package.share_blocked_reason is None
    assert package.share_token
    assert package.proposal_share_url
    assert "https://proposals.waypointos.com/view/" in package.proposal_share_url
