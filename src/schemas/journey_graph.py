"""
src/schemas/journey_graph.py — Journey Dependency Graph (JDG) for IROPS Disruption Propagation.

Models the physical, temporal, and spatial dependencies across all legs and
bookings in an itinerary (PER-0700, PER-0442 / Travel Operating Systems Architect).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import StrEnum
from typing import Any, Dict, List, Literal, Optional


class NodeType(StrEnum):
    FLIGHT = "FLIGHT"
    RAIL = "RAIL"
    RAIL_HIGH_SPEED = "RAIL_HIGH_SPEED"
    FERRY = "FERRY"
    CRUISE = "CRUISE"
    TRANSFER = "TRANSFER"
    HOTEL_CHECKIN = "HOTEL_CHECKIN"
    HOTEL_STAY = "HOTEL_STAY"
    ACTIVITY = "ACTIVITY"
    RESTAURANT = "RESTAURANT"


CO_TERMINAL_TRANSFER_MINUTES: Dict[tuple[str, str], int] = {
    ("LHR", "LGW"): 180,
    ("LGW", "LHR"): 180,
    ("JFK", "EWR"): 150,
    ("EWR", "JFK"): 150,
    ("JFK", "LGA"): 90,
    ("LGA", "JFK"): 90,
    ("NRT", "HND"): 120,
    ("HND", "NRT"): 120,
    ("CDG", "ORY"): 120,
    ("ORY", "CDG"): 120,
    ("TXL", "BER"): 60,
}


class DependencyRelation(StrEnum):
    REQUIRES_ARRIVAL_BEFORE = "REQUIRES_ARRIVAL_BEFORE"
    TRANSFER_CONNECTS = "TRANSFER_CONNECTS"
    SAME_DAY_ACTIVITY = "SAME_DAY_ACTIVITY"
    HOTEL_NIGHT_FOR = "HOTEL_NIGHT_FOR"
    RETURN_LEG_OF = "RETURN_LEG_OF"


# Progressive-commitment states on a journey node (AT-02 / PER-0443).
# A rung is real only if a later writer honors these; ticketed nodes must not
# be silently overwritten by a second fulfill.
CommitmentStatus = Literal["quoted", "held", "booked", "ticketed", "void"]


def _parse_dt(value: Any) -> Optional[datetime]:
    """Tolerant timestamp parse.

    Stored journey nodes may legitimately lack schedule times (identity,
    provider, and confirmation fields only). Raising on absence made every
    such record fail hydration even though the router can serve it raw —
    the parser now abstains (``None``) instead of fabricating a datetime or
    crashing (codex Part-H P2, 2026-09-07).

    Naive timestamps are normalized to UTC (storage canonical is UTC; legacy
    naive values are presumed UTC) so mixed-provenance nodes never crash
    datetime comparisons in topological_sort (Part-J #7).
    """
    if isinstance(value, datetime):
        parsed = value
    else:
        text = str(value or "").replace("Z", "+00:00")
        if not text:
            return None
        try:
            parsed = datetime.fromisoformat(text)
        except ValueError:
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _node_type_value(node_type: Any) -> Any:
    """Serialize a node type that may be a NodeType or a preserved raw string."""
    return getattr(node_type, "value", node_type)


@dataclass(slots=True)
class JourneyNode:
    """An atomic node in a journey DAG (a flight, hotel, transfer, or activity)."""
    node_id: str
    node_type: NodeType
    title: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    location: str = ""
    provider: str = ""
    confirmation_code: Optional[str] = None
    buffer_minutes_before: int = 30
    is_cancellable: bool = True
    cancellation_deadline: Optional[datetime] = None
    commitment_status: CommitmentStatus = "quoted"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "node_type": _node_type_value(self.node_type),
            "title": self.title,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "location": self.location,
            "provider": self.provider,
            "confirmation_code": self.confirmation_code,
            "buffer_minutes_before": self.buffer_minutes_before,
            "is_cancellable": self.is_cancellable,
            "cancellation_deadline": self.cancellation_deadline.isoformat() if self.cancellation_deadline else None,
            "commitment_status": self.commitment_status,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, raw: Dict[str, Any]) -> "JourneyNode":
        raw_type = str(raw.get("node_type") or "FLIGHT")
        try:
            node_type: Any = NodeType(raw_type)
        except ValueError:
            # Preserve the operational meaning of unknown/future node types
            # instead of silently re-labeling them FLIGHT (Part-H P2).
            node_type = raw_type
        status_raw = str(raw.get("commitment_status") or "quoted")
        commitment: CommitmentStatus
        if status_raw in ("quoted", "held", "booked", "ticketed", "void"):
            commitment = status_raw  # type: ignore[assignment]
        else:
            commitment = "quoted"
        deadline = raw.get("cancellation_deadline")
        return cls(
            node_id=str(raw.get("node_id") or ""),
            node_type=node_type,
            title=str(raw.get("title") or ""),
            start_time=_parse_dt(raw.get("start_time")),
            end_time=_parse_dt(raw.get("end_time")),
            location=str(raw.get("location") or ""),
            provider=str(raw.get("provider") or ""),
            confirmation_code=raw.get("confirmation_code"),
            buffer_minutes_before=int(raw.get("buffer_minutes_before") or 30),
            is_cancellable=bool(raw.get("is_cancellable", True)),
            cancellation_deadline=_parse_dt(deadline) if deadline else None,
            commitment_status=commitment,
            metadata=dict(raw.get("metadata") or {}),
        )


@dataclass(slots=True)
class DependencyEdge:
    """A directional dependency edge linking two journey nodes."""
    from_node_id: str
    to_node_id: str
    relation: DependencyRelation
    min_connection_minutes: int = 60
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "from_node_id": self.from_node_id,
            "to_node_id": self.to_node_id,
            "relation": self.relation.value,
            "min_connection_minutes": self.min_connection_minutes,
            "notes": self.notes,
        }


@dataclass(slots=True)
class DisruptionImpact:
    """Evaluated impact on a specific downstream node."""
    impacted_node_id: str
    impacted_node_title: str
    impact_severity: Literal["critical", "high", "medium", "low"]
    reason: str
    scheduled_start: datetime
    feasible_start: datetime
    time_deficit_minutes: int
    recommended_action: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "impacted_node_id": self.impacted_node_id,
            "impacted_node_title": self.impacted_node_title,
            "impact_severity": self.impact_severity,
            "reason": self.reason,
            "scheduled_start": self.scheduled_start.isoformat(),
            "feasible_start": self.feasible_start.isoformat(),
            "time_deficit_minutes": self.time_deficit_minutes,
            "recommended_action": self.recommended_action,
        }


@dataclass(slots=True)
class DisruptionRippleReport:
    """Full cascade report generated when a node experiences a delay or cancellation."""
    root_disrupted_node_id: str
    delay_minutes: int
    is_cancellation: bool
    evaluated_at: datetime
    impacted_nodes: List[DisruptionImpact] = field(default_factory=list)
    unaffected_nodes_count: int = 0
    operator_summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "root_disrupted_node_id": self.root_disrupted_node_id,
            "delay_minutes": self.delay_minutes,
            "is_cancellation": self.is_cancellation,
            "evaluated_at": self.evaluated_at.isoformat(),
            "impacted_nodes": [i.to_dict() for i in self.impacted_nodes],
            "unaffected_nodes_count": self.unaffected_nodes_count,
            "operator_summary": self.operator_summary,
        }


class JourneyDependencyGraph:
    """DAG representing the temporal-spatial topology of a complete trip."""

    def __init__(self, trip_id: str):
        self.trip_id = trip_id
        self.nodes: Dict[str, JourneyNode] = {}
        self.edges: List[DependencyEdge] = []

    def add_node(self, node: JourneyNode) -> None:
        self.nodes[node.node_id] = node

    def get_node(self, node_id: str) -> Optional[JourneyNode]:
        return self.nodes.get(node_id)

    def to_stored_payload(self) -> Dict[str, Any]:
        """Trip-record fields the journey-graph GET already reads (AT-01)."""
        return {
            "journey_graph_nodes": [n.to_dict() for n in self.nodes.values()],
            "journey_graph_edges": [e.to_dict() for e in self.edges],
        }

    @classmethod
    def from_stored(
        cls,
        trip_id: str,
        nodes: Optional[List[Dict[str, Any]]] = None,
        edges: Optional[List[Dict[str, Any]]] = None,
    ) -> "JourneyDependencyGraph":
        graph = cls(trip_id=trip_id)
        for raw in nodes or []:
            if not isinstance(raw, dict) or not raw.get("node_id"):
                continue
            graph.add_node(JourneyNode.from_dict(raw))
        for raw in edges or []:
            if not isinstance(raw, dict):
                continue
            from_id = str(raw.get("from_node_id") or "")
            to_id = str(raw.get("to_node_id") or "")
            if from_id not in graph.nodes or to_id not in graph.nodes:
                continue
            try:
                relation = DependencyRelation(str(raw.get("relation") or "REQUIRES_ARRIVAL_BEFORE"))
            except ValueError:
                relation = DependencyRelation.REQUIRES_ARRIVAL_BEFORE
            graph.add_edge(
                from_id,
                to_id,
                relation=relation,
                min_connection_minutes=int(raw.get("min_connection_minutes") or 60),
                notes=raw.get("notes"),
            )
        return graph

    def add_edge(
        self,
        from_node_id: str,
        to_node_id: str,
        relation: DependencyRelation = DependencyRelation.REQUIRES_ARRIVAL_BEFORE,
        min_connection_minutes: int = 60,
        notes: Optional[str] = None,
    ) -> None:
        if from_node_id not in self.nodes:
            raise ValueError(f"Source node {from_node_id} does not exist in graph")
        if to_node_id not in self.nodes:
            raise ValueError(f"Target node {to_node_id} does not exist in graph")
        self.edges.append(
            DependencyEdge(
                from_node_id=from_node_id,
                to_node_id=to_node_id,
                relation=relation,
                min_connection_minutes=min_connection_minutes,
                notes=notes,
            )
        )

    def evaluate_disruption(
        self,
        delayed_node_id: str,
        delay_minutes: int,
        is_cancellation: bool = False,
    ) -> DisruptionRippleReport:
        """Evaluate downstream ripple effects of a delay or cancellation."""
        if delayed_node_id not in self.nodes:
            raise ValueError(f"Node {delayed_node_id} not found in JourneyDependencyGraph")

        root = self.nodes[delayed_node_id]
        if root.end_time is None:
            raise ValueError(
                f"Node {delayed_node_id} has no scheduled end time; disruption "
                "ripple evaluation abstains instead of guessing a schedule."
            )
        impacts: List[DisruptionImpact] = []
        visited = set()

        # Queue of (current_node_id, cumulative_delayed_end_time)
        new_end_time = root.end_time + timedelta(minutes=delay_minutes)
        queue = [(delayed_node_id, new_end_time)]

        while queue:
            curr_id, curr_end = queue.pop(0)
            if curr_id in visited and curr_id != delayed_node_id:
                continue
            visited.add(curr_id)

            # Find all downstream outgoing edges
            out_edges = [e for e in self.edges if e.from_node_id == curr_id]
            for edge in out_edges:
                target = self.nodes[edge.to_node_id]
                if target.start_time is None or target.end_time is None:
                    # Undated nodes have no schedule to violate; they cannot
                    # participate in a temporal ripple evaluation.
                    continue
                min_allowed_start = curr_end + timedelta(minutes=edge.min_connection_minutes)

                if is_cancellation:
                    impacts.append(
                        DisruptionImpact(
                            impacted_node_id=target.node_id,
                            impacted_node_title=target.title,
                            impact_severity="critical",
                            reason=f"Upstream leg '{self.nodes[curr_id].title}' was cancelled.",
                            scheduled_start=target.start_time,
                            feasible_start=min_allowed_start,
                            time_deficit_minutes=9999,
                            recommended_action="Cancel or rebook connecting leg immediately.",
                        )
                    )
                    queue.append((target.node_id, target.end_time + timedelta(days=1)))
                elif min_allowed_start > target.start_time:
                    deficit = int((min_allowed_start - target.start_time).total_seconds() / 60)
                    severity: Literal["critical", "high", "medium", "low"] = (
                        "critical" if deficit > 60 or target.node_type == NodeType.FLIGHT
                        else "high" if deficit > 15
                        else "medium"
                    )
                    impacts.append(
                        DisruptionImpact(
                            impacted_node_id=target.node_id,
                            impacted_node_title=target.title,
                            impact_severity=severity,
                            reason=(
                                f"Connection window violated: requires arrival by {target.start_time.strftime('%H:%M')} "
                                f"with {edge.min_connection_minutes}m buffer, but upstream arrival will be {curr_end.strftime('%H:%M')}."
                            ),
                            scheduled_start=target.start_time,
                            feasible_start=min_allowed_start,
                            time_deficit_minutes=deficit,
                            recommended_action=(
                                f"Rebook {target.title} to departure after {min_allowed_start.strftime('%H:%M')} "
                                f"or request airport fast-track transfer."
                            ),
                        )
                    )
                    # Propagate delay to target's end time
                    propagated_end = target.end_time + timedelta(minutes=deficit)
                    queue.append((target.node_id, propagated_end))

        unaffected = len(self.nodes) - len(impacts) - 1
        summary = (
            f"Disruption on '{root.title}' (+{delay_minutes}m) caused {len(impacts)} downstream ripple impact(s)."
            if impacts
            else f"Disruption on '{root.title}' (+{delay_minutes}m) is absorbed within existing buffer windows."
        )

        return DisruptionRippleReport(
            root_disrupted_node_id=delayed_node_id,
            delay_minutes=delay_minutes,
            is_cancellation=is_cancellation,
            evaluated_at=datetime.now(),
            impacted_nodes=impacts,
            unaffected_nodes_count=max(0, unaffected),
            operator_summary=summary,
        )

    def topological_sort(self) -> List[JourneyNode]:
        """
        Return nodes sorted in topological chronological order using Kahn's algorithm.
        Raises ValueError if a cycle is detected.
        """
        in_degree = {nid: 0 for nid in self.nodes}
        adj: Dict[str, List[str]] = {nid: [] for nid in self.nodes}

        for edge in self.edges:
            adj[edge.from_node_id].append(edge.to_node_id)
            in_degree[edge.to_node_id] += 1

        queue = [nid for nid, deg in in_degree.items() if deg == 0]
        # Sort initial queue by start_time; undated nodes sort last so they
        # never crash the ordering against scheduled nodes.
        _undated = datetime.max.replace(tzinfo=timezone.utc)
        queue.sort(key=lambda nid: (self.nodes[nid].start_time is None, self.nodes[nid].start_time or _undated))

        sorted_nodes: List[JourneyNode] = []

        while queue:
            curr_id = queue.pop(0)
            sorted_nodes.append(self.nodes[curr_id])

            for neighbor in adj[curr_id]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
            queue.sort(key=lambda nid: (self.nodes[nid].start_time is None, self.nodes[nid].start_time or _undated))

        if len(sorted_nodes) != len(self.nodes):
            raise ValueError("Cycle detected in JourneyDependencyGraph")

        return sorted_nodes

    def compute_cushion_variance(self, from_node_id: str, to_node_id: str) -> float:
        """
        Calculate the connection cushion variance in minutes between two linked nodes.
        Positive = surplus buffer; Negative = connection deficit.
        """
        from_node = self.get_node(from_node_id)
        to_node = self.get_node(to_node_id)
        if not from_node or not to_node:
            raise ValueError("Both nodes must exist in graph")
        if from_node.end_time is None or to_node.start_time is None:
            raise ValueError(
                "Connection cushion requires scheduled times on both nodes; "
                "abstaining instead of computing against an unknown schedule."
            )

        edge = next((e for e in self.edges if e.from_node_id == from_node_id and e.to_node_id == to_node_id), None)
        min_mct = edge.min_connection_minutes if edge else 60

        available_minutes = (to_node.start_time - from_node.end_time).total_seconds() / 60.0
        return available_minutes - min_mct

    def to_geojson(self) -> Dict[str, Any]:
        """Serialize journey nodes and dependency edges into standard GeoJSON FeatureCollection."""
        features = []
        for node in self.nodes.values():
            features.append({
                "type": "Feature",
                "id": node.node_id,
                "geometry": None,  # Can be populated with coordinates if available
                "properties": {
                    "node_id": node.node_id,
                    "node_type": _node_type_value(node.node_type),
                    "title": node.title,
                    "location": node.location,
                    "start_time": node.start_time.isoformat() if node.start_time else None,
                    "end_time": node.end_time.isoformat() if node.end_time else None,
                    "provider": node.provider,
                }
            })
        return {
            "type": "FeatureCollection",
            "trip_id": self.trip_id,
            "features": features,
        }

    def diff(self, other: JourneyDependencyGraph) -> Dict[str, Any]:
        """Compute structural delta between this journey graph and another version."""
        this_nodes = set(self.nodes.keys())
        other_nodes = set(other.nodes.keys())

        added = [other.nodes[nid].to_dict() for nid in (other_nodes - this_nodes)]
        removed = [self.nodes[nid].to_dict() for nid in (this_nodes - other_nodes)]
        modified = []

        for common_id in (this_nodes & other_nodes):
            n1 = self.nodes[common_id]
            n2 = other.nodes[common_id]
            if n1.start_time != n2.start_time or n1.end_time != n2.end_time or n1.location != n2.location:
                modified.append({
                    "node_id": common_id,
                    "before": n1.to_dict(),
                    "after": n2.to_dict(),
                })

        return {
            "added_nodes_count": len(added),
            "removed_nodes_count": len(removed),
            "modified_nodes_count": len(modified),
            "added": added,
            "removed": removed,
            "modified": modified,
        }
