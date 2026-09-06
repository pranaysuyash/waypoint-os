"""
Journey Dependency Graph (JDG) API Router.

Provides endpoints for building journey DAGs, evaluating IROPS delay ripple cascades,
calculating co-terminal transfer cushions, and topological sorting.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.schemas.journey_graph import (
    JourneyDependencyGraph,
    JourneyNode,
    NodeType,
    DependencyRelation,
    CO_TERMINAL_TRANSFER_MINUTES,
)

router = APIRouter(prefix="/api/v1/journey-graph", tags=["journey-graph"])


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
    trip_id: str = "TRIP-001"
    nodes: List[NodeInput]
    edges: List[EdgeInput]
    delayed_node_id: str
    delay_minutes: int = 45
    is_cancellation: bool = False


@router.post("/evaluate")
def evaluate_journey_disruption(payload: EvaluateDisruptionRequest) -> Dict[str, Any]:
    """Builds the journey DAG and evaluates disruption propagation."""
    graph = JourneyDependencyGraph(trip_id=payload.trip_id)

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
