"""Audit-chain causal linkage (`caused_by`) — EXPLORE #5 / topic 51a gap 2.

The hash chain proves WHAT happened in order. This module adds the WHY: a
lightweight convention where audit events that were *caused by* another
audit event carry that event's id in `details.caused_by`, plus a `why()`
reader that walks the causal ancestry backward.

Design (doctrine: no parallel systems, additive-only):
- NO schema change: `caused_by` rides inside `details`, which the RULE_015
  hash already covers (it is part of the hashed changes JSON) — so the causal
  linkage is itself tamper-evident.
- NO forced adoption: call sites populate it where causality is naturally
  known (disposition transitions caused by a fare-drop signal, reassessments
  caused by a correction, escalations caused by a disruption). Events without
  causality simply omit it.
- The reader (`why`) resolves an event id to its chain record and walks the
  `caused_by` chain, returning the causal path from effect to root cause.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

CAUSED_BY_KEY = "caused_by"


def why(event_id: str, lookup, max_depth: int = 20) -> List[Dict[str, Any]]:
    """Walk the causal ancestry of an audit event, effect → root cause.

    ``lookup`` is a callable(event_id) -> dict|None resolving one audit event
    (injected so the module stays dependency-free; callers pass
    ``_find_event_by_id`` or a test double).

    Returns the causal path INCLUDING the starting event: [effect, cause,
    root_cause, ...]. Cycles and missing ancestors terminate the walk
    defensively (the chain is append-only, but callers are untrusted).
    """
    path: List[Dict[str, Any]] = []
    seen: set[str] = set()
    current: Optional[str] = event_id
    depth = 0
    while current and depth < max_depth and current not in seen:
        seen.add(current)
        event = lookup(current)
        if not event:
            break
        path.append(event)
        details = event.get("details") if isinstance(event.get("details"), dict) else {}
        current = details.get(CAUSED_BY_KEY) or None
        depth += 1
    return path


def find_event_by_id(events: List[Dict[str, Any]], event_id: str) -> Optional[Dict[str, Any]]:
    """Linear lookup over an in-memory event list (merged SQL + file archive)."""
    for event in events:
        if event.get("id") == event_id or event.get("event_id") == event_id:
            return event
    return None
