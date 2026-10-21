"""src/analytics/trace_reader.py — OpenTelemetry trace-correlation reader and CI event-flow assertion (R-16 / FND-0214).

Reads, structures, and correlates OpenTelemetry spans and pipeline execution events
into causal trees, validating event-flow integrity across stages and agency boundaries.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass(slots=True)
class TraceNode:
    span_id: str
    trace_id: str
    event_type: str
    timestamp: datetime
    parent_span_id: Optional[str] = None
    agency_id: Optional[str] = None
    trip_id: Optional[str] = None
    attributes: Dict[str, Any] = field(default_factory=dict)
    children: List[TraceNode] = field(default_factory=list)


class TraceCorrelationReader:
    """Ingests flat OpenTelemetry span dictionaries and builds correlated causal DAGs."""

    def __init__(self) -> None:
        self.traces: Dict[str, List[TraceNode]] = {}

    def ingest_events(self, events: List[Dict[str, Any]]) -> None:
        """Ingest raw span dictionaries into correlated trace trees."""
        nodes_by_id: Dict[str, TraceNode] = {}
        roots_by_trace: Dict[str, List[TraceNode]] = {}

        # 1. Instantiate nodes
        for ev in events:
            trace_id = ev.get("trace_id") or ev.get("details", {}).get("trace_id", "default_trace")
            span_id = ev.get("span_id") or ev.get("details", {}).get("span_id", f"span_{len(nodes_by_id)}")
            parent_id = ev.get("parent_span_id") or ev.get("details", {}).get("parent_span_id")
            ts_raw = ev.get("timestamp") or ev.get("created_at") or datetime.utcnow().isoformat()
            
            if isinstance(ts_raw, str):
                try:
                    ts = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
                except ValueError:
                    ts = datetime.utcnow()
            else:
                ts = ts_raw

            node = TraceNode(
                span_id=str(span_id),
                trace_id=str(trace_id),
                event_type=ev.get("event_type") or ev.get("name", "unknown_event"),
                timestamp=ts,
                parent_span_id=str(parent_id) if parent_id else None,
                agency_id=ev.get("agency_id") or ev.get("user_id"),
                trip_id=ev.get("trip_id") or ev.get("details", {}).get("trip_id"),
                attributes=ev.get("details", {}),
            )
            nodes_by_id[node.span_id] = node
            roots_by_trace.setdefault(node.trace_id, []).append(node)

        # 2. Wire child-parent links
        for node in nodes_by_id.values():
            if node.parent_span_id and node.parent_span_id in nodes_by_id:
                parent = nodes_by_id[node.parent_span_id]
                parent.children.append(node)
                if node in roots_by_trace[node.trace_id]:
                    roots_by_trace[node.trace_id].remove(node)

        self.traces = roots_by_trace

    def get_trace_roots(self, trace_id: str) -> List[TraceNode]:
        """Return root nodes for a given trace_id."""
        return self.traces.get(trace_id, [])

    def validate_event_flow(self, trace_id: str, required_sequence: Optional[List[str]] = None) -> List[str]:
        """Verify that event flow follows required temporal ordering and causal consistency."""
        errors: List[str] = []
        roots = self.get_trace_roots(trace_id)
        if not roots:
            return [f"Trace '{trace_id}' has no root spans recorded."]

        # Collect all nodes under trace in chronological order
        all_nodes: List[TraceNode] = []

        def _traverse(node: TraceNode) -> None:
            all_nodes.append(node)
            for child in sorted(node.children, key=lambda n: n.timestamp):
                _traverse(child)

        for r in roots:
            _traverse(r)

        all_nodes.sort(key=lambda n: n.timestamp)
        event_types = [n.event_type for n in all_nodes]

        # Verify required sequence progression
        if required_sequence:
            last_idx = -1
            for req in required_sequence:
                try:
                    curr_idx = event_types.index(req, last_idx + 1)
                    last_idx = curr_idx
                except ValueError:
                    errors.append(f"Required event '{req}' was missing or out of sequence in trace '{trace_id}'. Observed: {event_types}")
                    break

        # Verify agency isolation across all spans in the trace
        agencies = {n.agency_id for n in all_nodes if n.agency_id}
        if len(agencies) > 1:
            errors.append(f"Cross-tenant pollution detected in trace '{trace_id}': multiple agencies {agencies}")

        return errors


def assert_trace_event_flow(events: List[Dict[str, Any]], trace_id: str, required_sequence: Optional[List[str]] = None) -> None:
    """CI assertion helper for verifying OpenTelemetry event flows."""
    reader = TraceCorrelationReader()
    reader.ingest_events(events)
    violations = reader.validate_event_flow(trace_id, required_sequence)
    if violations:
        raise AssertionError(f"Trace event flow assertion failed: {'; '.join(violations)}")
