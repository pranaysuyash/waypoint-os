"""
Journey Dependency Graph (JDG) API Router.

Provides endpoints for building journey DAGs, evaluating IROPS delay ripple cascades,
calculating co-terminal transfer cushions, and topological sorting.

PA-01 (2026-09-06): the previous handler synthesized a canonical "confirmed"
itinerary (PNR772 / Amadeus NDC / Blacklane / Belmond) whenever no stored
journey-graph nodes existed, and the public route served any trip id
unauthenticated. Both behaviors are removed:

- No fabrication. If no stored journey-graph nodes exist for a trip, the API
  abstains: the tenant route returns 404
  (``{"detail": "no journey graph available for this trip"}``), and the public
  traveler-companion route returns the softer contract documented on
  ``get_public_journey_graph`` below. Reality tier is ``"unavailable"`` in the
  abstention envelope — the system never invents bookings it does not have.
- The public route is capability-gated: it requires a valid signed proposal
  share token (?token=...) that encodes exactly the requested trip_id, using
  the canonical verifier in ``spine_api.routers.public_proposals``.
- Scoped-lookup failures (DB/infrastructure errors) surface as 503 instead of
  being swallowed into fake data; only a genuinely missing trip (or a trip
  outside the caller's agency) maps to 404.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from spine_api.core.auth import get_current_agency_id

from src.schemas.journey_graph import (
    JourneyDependencyGraph,
    JourneyNode,
    NodeType,
    DependencyRelation,
    CO_TERMINAL_TRANSFER_MINUTES,
)

router = APIRouter(prefix="/api/v1/journey-graph", tags=["journey-graph"])

_NO_GRAPH_DETAIL = "no journey graph available for this trip"


class NodeInput(BaseModel):
    node_id: str
    node_type: str = "FLIGHT"
    title: str
    start_time: str
    end_time: str
    location: str
    provider: str = ""
    min_connection_minutes: int = 60


class EdgeInput(BaseModel):
    from_node_id: str
    to_node_id: str
    relation: str = "REQUIRES_ARRIVAL_BEFORE"
    min_connection_minutes: int = 60


class EvaluateDisruptionRequest(BaseModel):
    trip_id: str
    nodes: List[NodeInput] = []
    edges: List[EdgeInput] = []
    delayed_node_id: str
    delay_minutes: int = 45
    is_cancellation: bool = False


@router.post("/evaluate")
def evaluate_journey_disruption(
    payload: EvaluateDisruptionRequest,
    agency_id: str = Depends(get_current_agency_id),
) -> Dict[str, Any]:
    """Evaluate disruption on the stored journey graph, or on caller-supplied nodes.

    AT-19: client-posted DAGs are labeled deterministic_preview. An empty node
    list loads the persisted trip graph; missing storage abstains instead of
    returning ``status: success`` for an invented itinerary.
    """
    from spine_api.core.reality_tier import RealityTier, TierMetadata
    from spine_api.persistence import TripStore

    graph = JourneyDependencyGraph(trip_id=payload.trip_id)
    used_stored = False

    if payload.nodes:
        pass
    else:
        stored = TripStore.get_trip_for_agency(payload.trip_id, agency_id) or {}
        stored_nodes = stored.get("journey_graph_nodes") or []
        stored_edges = stored.get("journey_graph_edges") or []
        if stored_nodes:
            graph = JourneyDependencyGraph.from_stored(
                payload.trip_id, stored_nodes, stored_edges
            )
            used_stored = True
        else:
            return {
                "status": "abstain",
                "trip_id": payload.trip_id,
                "reality_tier": "unavailable",
                "provider_connected": False,
                "reason": "no stored journey graph and no nodes supplied",
                "metadata": TierMetadata.for_response(
                    RealityTier.DETERMINISTIC_PREVIEW,
                    "journey_graph_evaluate",
                    data_sufficient=False,
                    computation_method="abstain: no itinerary DAG to evaluate",
                    missing_for_upgrade=["persisted journey_graph_nodes on the trip"],
                ),
            }

    for n in payload.nodes:
        try:
            nt = NodeType(n.node_type)
        except ValueError:
            nt = NodeType.FLIGHT

        node = JourneyNode(
            node_id=n.node_id,
            node_type=nt,
            title=n.title,
            start_time=datetime.fromisoformat(n.start_time.replace("Z", "+00:00")),
            end_time=datetime.fromisoformat(n.end_time.replace("Z", "+00:00")),
            location=n.location,
            provider=n.provider,
        )
        graph.add_node(node)

    for e in payload.edges:
        try:
            rel = DependencyRelation(e.relation)
        except ValueError:
            rel = DependencyRelation.REQUIRES_ARRIVAL_BEFORE

        graph.add_edge(
            from_node_id=e.from_node_id,
            to_node_id=e.to_node_id,
            relation=rel,
            min_connection_minutes=e.min_connection_minutes,
        )

    try:
        report = graph.evaluate_disruption(
            delayed_node_id=payload.delayed_node_id,
            delay_minutes=payload.delay_minutes,
            is_cancellation=payload.is_cancellation,
        )
        return {
            "status": "success",
            "trip_id": payload.trip_id,
            "report": report.to_dict(),
            "topological_order": [n.node_id for n in graph.topological_sort()],
            "reality_tier": RealityTier.DETERMINISTIC_PREVIEW.value,
            "provider_connected": False,
            "used_stored_graph": used_stored,
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/co-terminal-buffers")
def get_co_terminal_transfer_buffers() -> Dict[str, Any]:
    """Returns standard inter-airport transfer minimum connecting times."""
    formatted = [
        {"airports": f"{k[0]} ↔ {k[1]}", "min_transfer_minutes": v}
        for k, v in CO_TERMINAL_TRANSFER_MINUTES.items()
    ]
    return {
        "status": "success",
        "buffers": formatted,
    }


def _load_scoped_trip_record(trip_id: str, agency_id: str) -> Optional[dict]:
    """Load the agency-scoped trip record.

    Returns the record dict, or None when the trip does not exist OR does not
    belong to the agency (identical 404 semantics, never revealing which).
    Infrastructure failures raise — callers map them to 503.
    """
    from spine_api import persistence

    trip_record = persistence.TripStore.get_trip_for_agency(trip_id, agency_id)
    return trip_record


def _stored_graph_payload(trip_record: dict, trip_id: str) -> Dict[str, Any]:
    """Build the response from stored trip data ONLY. No synthesis."""
    from spine_api.core.reality_tier import RealityTier

    destination = (
        trip_record.get("destination")
        or (trip_record.get("packet") or {}).get("destination")
    )
    booking_confirmation = trip_record.get("booking_confirmation")
    raw_nodes = trip_record.get("journey_graph_nodes")
    raw_edges = trip_record.get("journey_graph_edges")

    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []
    if raw_nodes and isinstance(raw_nodes, list):
        nodes = [dict(n) for n in raw_nodes if isinstance(n, dict)]
    if raw_edges and isinstance(raw_edges, list):
        edges = [dict(e) for e in raw_edges if isinstance(e, dict)]

    if not nodes:
        # PA-01: abstain instead of synthesizing a confirmed itinerary.
        raise _NoStoredGraph()

    # Part-J #4 companion backstop: a top-level provider attestation derived
    # FAIL-CLOSED — live only when the confirmation explicitly says
    # provider_connected is True AND no node contradicts it. Legacy blobs
    # without the field attest False rather than letting clients fail open.
    confirmation_attests_live = isinstance(booking_confirmation, dict) and (
        booking_confirmation.get("provider_connected") is True
    )
    node_contradicts = any(
        isinstance(n, dict)
        and isinstance(n.get("metadata"), dict)
        and n["metadata"].get("provider_connected") is False
        for n in nodes
    )
    provider_connected = confirmation_attests_live and not node_contradicts

    # TS-08: trip-level component-state verdict (PENDING_BOOKING / BOOKED /
    # BOOKING_EXCEPTION / None), derived from stored nodes only — abstains
    # when the trip declares no non-void nodes.
    from src.schemas.journey_graph import JourneyDependencyGraph

    graph = JourneyDependencyGraph.from_stored(trip_id, nodes=nodes, edges=edges)
    commitment_verdict = graph.aggregate_commitment()

    return {
        "status": "success",
        "trip_id": trip_id,
        "destination": destination,
        "provider_connected": provider_connected,
        "commitment_verdict": commitment_verdict,
        "reality_tier": (
            booking_confirmation.get("reality_tier")
            if isinstance(booking_confirmation, dict) and booking_confirmation.get("reality_tier")
            else RealityTier.DETERMINISTIC_PREVIEW.value
        ),
        "booking_confirmation": booking_confirmation,
        "nodes": nodes,
        "edges": edges,
    }


class _NoStoredGraph(Exception):
    """Raised when the trip exists but has no stored journey-graph nodes."""


@router.get("/{trip_id}")
def get_journey_graph(
    trip_id: str,
    agency_id: str = Depends(get_current_agency_id),
) -> Dict[str, Any]:
    """Retrieve the stored Journey Dependency Graph for a trip.

    Tenant-scoped (register F-30 defect class): agency is sourced from the
    authenticated membership, and the lookup uses the agency-scoped accessor —
    the previous raw unscoped fetch was cross-tenant readable and tripped the
    unscoped-access CI gate.

    PA-01 honesty contract:
    - Trip missing or owned by another agency -> 404 (existence not revealed).
    - Trip exists but has no stored journey-graph nodes -> 404 with
      ``{"detail": "no journey graph available for this trip"}``. This route
      NEVER synthesizes placeholder providers/confirmations.
    - Scoped-lookup infrastructure failure -> 503 (previously swallowed into
      fabricated data by a bare ``except Exception``).
    """
    try:
        trip_record = _load_scoped_trip_record(trip_id, agency_id)
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="journey graph lookup temporarily unavailable",
        ) from exc

    if not trip_record:
        raise HTTPException(status_code=404, detail="Trip not found")

    try:
        return _stored_graph_payload(trip_record, trip_id)
    except _NoStoredGraph:
        raise HTTPException(status_code=404, detail=_NO_GRAPH_DETAIL)


public_router = APIRouter(prefix="/api/public/journey-graph", tags=["public-journey-graph"])


@public_router.get("/{trip_id}")
def get_public_journey_graph(trip_id: str, token: str = "") -> Dict[str, Any]:
    """Traveler companion endpoint for viewing a CONFIRMED, stored itinerary DAG.

    Contract (PA-01, chosen option documented here):
    - Missing or invalid share token, or a token that encodes a different
      trip_id -> 404 with a generic detail. Existence of any trip is never
      revealed to unauthenticated callers.
    - Valid token but no stored journey graph for the trip -> HTTP 200 with the
      soft abstention envelope ``{"ok": true, "exists": false,
      "reality_tier": "unavailable"}``. The softer (non-404) shape was chosen
      for the traveler companion so the UI can render a neutral
      "itinerary not yet available" state without error handling for the
      authenticated-truth case; ``exists`` is authoritative.
    - Valid token with a stored graph -> the stored graph only.
    """
    from spine_api.routers.public_proposals import (
        verify_proposal_token,
        _decode_agency_field,
    )

    is_valid, _reason, token_trip_id = verify_proposal_token(token)
    if not is_valid or token_trip_id != trip_id:
        # Do not reveal whether the trip exists.
        raise HTTPException(status_code=404, detail="Not Found")

    # The trip read must be agency-scoped (RLS-safe even outside an
    # authenticated request). The token format v2 embeds the issuing agency;
    # the canonical verifier above already validated the signature, TTL,
    # revocation, and the canonical encoding of that agency field, so decoding
    # it here reuses the verified value instead of forking the verifier.
    #
    # Legacy demo allowlist tokens (no agency field) decode to a value that
    # matches no agency, so the scoped lookup fails closed to 404 — demo
    # fixtures are not journey-graph capabilities.
    try:
        _body = token[len("prop_") :]
        _head = _body.rsplit("_", 2)[0]  # strip exp_ts and signature fields
        _, _, agency_field = _head.rpartition("_")
        token_agency_id = _decode_agency_field(agency_field)
    except (ValueError, UnicodeDecodeError):
        raise HTTPException(status_code=404, detail="Not Found")

    try:
        from spine_api import persistence

        trip_record = persistence.TripStore.get_trip_for_agency(trip_id, token_agency_id)
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="journey graph lookup temporarily unavailable",
        ) from exc

    if not trip_record:
        raise HTTPException(status_code=404, detail="Not Found")

    try:
        return _stored_graph_payload(trip_record, trip_id)
    except _NoStoredGraph:
        return {
            "ok": True,
            "exists": False,
            "reality_tier": "unavailable",
            "trip_id": trip_id,
        }
