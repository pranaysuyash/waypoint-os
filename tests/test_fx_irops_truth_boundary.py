"""Truth-boundary checks for deterministic FX and IROPS API previews.

These tests intentionally exercise the router contracts rather than only the
lower-level calculators. The latter may retain deterministic fixture behavior;
the API is where a consumer could otherwise mistake a calculation for a live
financial or operational effect.
"""

from spine_api.persistence import TripStore
from spine_api.routers.fx_sentinel import (
    LockFxRateRequest,
    get_live_fx_rates,
    list_fx_exposures,
    lock_fx_rate_hedging,
)
from spine_api.routers.irops_healer import HealDisruptionRequest, heal_disrupted_journey


def _assert_preview_metadata(metadata: dict) -> None:
    assert metadata["reality_tier"] == "deterministic_preview"
    assert metadata["source"] == "local_deterministic_preview"
    assert metadata["simulation"] is True
    assert metadata["provider_connected"] is False
    assert metadata["external_reference"] is None
    assert metadata["external_action"] is False
    assert metadata["operational_write"] is False
    assert metadata["effects"] == []


def test_fx_rates_are_reference_previews_not_live_quotes() -> None:
    rates = get_live_fx_rates()

    assert len(rates) >= 5
    for rate in rates:
        assert rate.status == "PREVIEW_ONLY"
        assert rate.reality_tier == "deterministic_preview"
        assert rate.evidence_status == "UNVERIFIED_REFERENCE_RATE"
        assert rate.source == "local_reference_table"
        assert rate.provider_connected is False
        assert rate.external_reference is None
        assert rate.effects == []
        _assert_preview_metadata(rate.metadata)


def test_fx_exposure_does_not_invent_amount_when_trip_cost_is_missing(monkeypatch) -> None:
    monkeypatch.setattr(
        TripStore,
        "list_trips",
        lambda agency_id: [{"id": "TRIP-UNKNOWN", "destination": "Tokyo", "strategy": {}}],
    )

    exposures = list_fx_exposures("agency-preview")

    assert len(exposures) == 1
    exposure = exposures[0]
    assert exposure.risk_level == "UNKNOWN"
    assert exposure.evidence_status == "INSUFFICIENT_TRIP_DATA"
    assert exposure.quoted_amount_cents == 0
    assert exposure.supplier_amount_in_supplier_curr == 0.0
    assert exposure.hedging_recommended is False
    assert exposure.is_locked is False
    _assert_preview_metadata(exposure.metadata)
    assert exposure.metadata["data_sufficient"] is False


def test_fx_lock_preview_never_persists_or_reports_a_lock(monkeypatch) -> None:
    monkeypatch.setattr(
        TripStore,
        "get_trip_for_agency",
        lambda trip_id, agency_id: {"id": trip_id, "strategy": {}},
    )

    def fail_if_persisted(*args, **kwargs):
        raise AssertionError("preview hedge must not persist trip state")

    monkeypatch.setattr(TripStore, "save_trip", fail_if_persisted)
    response = lock_fx_rate_hedging(
        "TRIP-LOCK-PREVIEW",
        LockFxRateRequest(trip_id="TRIP-LOCK-PREVIEW", locked_rate=155.0),
        "agency-preview",
    )

    assert response.ok is False
    assert response.status == "PREVIEW_ONLY"
    assert response.lock_applied is False
    assert response.locked_at is None
    assert response.reality_tier == "deterministic_preview"
    assert response.provider_connected is False
    assert response.external_reference is None
    assert response.effects == []
    _assert_preview_metadata(response.metadata)


def test_irops_recovery_plan_abstains_without_stored_graph() -> None:
    response = heal_disrupted_journey(
        HealDisruptionRequest(
            trip_id="TRIP-IROPS-PREVIEW",
            delayed_node_id="N_FLT_178",
            delay_minutes=180,
        )
    )

    assert response["status"] == "PREVIEW_ONLY"
    assert response["reality_tier"] == "deterministic_preview"
    assert response["simulation"] is True
    assert response["provider_connected"] is False
    assert response["external_action"] is False
    assert response["operational_write"] is False
    assert response["effects"] == []
    _assert_preview_metadata(response["metadata"])

    plan = response["healing_plan"]
    assert plan["analysis_status"] == "ABSTAIN_NO_STORED_GRAPH"
    assert plan["evidence_status"] == "NO_STORED_JOURNEY_GRAPH"
    assert plan["emergency_lodging_vcc"] is None
    assert plan["counterfactual_options"] == []
    assert plan["statutory_compensation"]["amount_eur"] is None
    assert plan["statutory_compensation"]["estimated_amount_eur"] is None


def test_irops_recovery_plan_is_analysis_only_and_scrubs_effects(monkeypatch) -> None:
    from datetime import datetime, timezone

    from src.schemas.journey_graph import JourneyDependencyGraph, JourneyNode, NodeType

    trip_id = "TRIP-IROPS-STORED"
    node_id = "N_FLT_STORED"
    now = datetime.now(timezone.utc)
    graph = JourneyDependencyGraph(trip_id=trip_id)
    graph.add_node(
        JourneyNode(
            node_id=node_id,
            node_type=NodeType.FLIGHT,
            title="Stored delayed flight",
            start_time=now,
            end_time=now,
            location="JFK",
            provider="StoredCarrier",
            confirmation_code="STORED1",
            commitment_status="ticketed",
        )
    )
    stored = {"id": trip_id, **graph.to_stored_payload()}
    monkeypatch.setattr(
        TripStore, "get_trip", lambda tid, *args, **kwargs: stored if tid == trip_id else None
    )

    response = heal_disrupted_journey(
        HealDisruptionRequest(
            trip_id=trip_id,
            delayed_node_id=node_id,
            delay_minutes=180,
        )
    )

    assert response["status"] == "PREVIEW_ONLY"
    assert response["reality_tier"] == "deterministic_preview"
    assert response["simulation"] is True
    assert response["provider_connected"] is False
    assert response["external_action"] is False
    assert response["operational_write"] is False
    assert response["effects"] == []
    _assert_preview_metadata(response["metadata"])

    plan = response["healing_plan"]
    assert plan["incident_id"].startswith("PREVIEW-IROPS-")
    assert plan["analysis_status"] == "PREVIEW_ONLY"
    assert plan["evidence_status"] == "UNVERIFIED_LOCAL_INPUT"
    assert plan["resolved_at"] is None
    assert plan["emergency_lodging_vcc"] is None
    assert plan["lodging_payment_status"] == "NOT_ISSUED"
    assert plan["waiver_status"] == "DRAFT_NOT_SENT"
    compensation = plan["statutory_compensation"]
    assert compensation["amount_eur"] is None
    assert compensation["estimated_amount_eur"] == 600.0
    assert compensation["status"] == "UNVERIFIED_LEGAL_ESTIMATE"
    assert all(option["status"] == "PREVIEW_ONLY" for option in plan["counterfactual_options"])
    assert all(option["provider_connected"] is False for option in plan["counterfactual_options"])
    assert all(option["external_reference"] is None for option in plan["counterfactual_options"])
    assert all(option["effects"] == [] for option in plan["counterfactual_options"])
    assert all("provider confirmation required" in option["action"] for option in plan["counterfactual_options"])
