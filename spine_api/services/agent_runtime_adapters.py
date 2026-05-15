"""
Thin adapters bridging agent runtime to TripStore and AuditStore.

Extracted from spine_api/server.py so the runtime factory (and tests) can
import adapters without pulling in server-side dependencies.
"""

from __future__ import annotations

import asyncio
from typing import Any, Optional


class TripStoreAdapter:
    """Thin adapter so backend agents can query TripStore through a stable boundary."""

    def __init__(self, trip_store: Any = None):
        self._trip_store = trip_store

    def list_active(self) -> list:
        """Return trips that are in processing stages (not closed/cancelled)."""
        from spine_api.persistence import TripStore
        store = self._trip_store or TripStore
        trips_raw = self._resolve_sync(store.list_trips(limit=500))
        terminal = {"closed", "cancelled", "completed", "archived"}
        return [t for t in trips_raw if (t.get("stage") or t.get("state") or t.get("status")) not in terminal]

    def set_review_status(self, trip_id: str, status: str) -> None:
        from spine_api.persistence import TripStore
        store = self._trip_store or TripStore
        self._resolve_sync(store.update_trip(trip_id, {"review_status": status}))

    def update_trip(self, trip_id: str, updates: dict) -> Optional[dict]:
        from spine_api.persistence import TripStore
        store = self._trip_store or TripStore
        return self._resolve_sync(store.update_trip(trip_id, updates))

    def _resolve_sync(self, value):
        if asyncio.iscoroutine(value):
            from spine_api.persistence import _run_async_blocking
            return _run_async_blocking(value)
        return value


class AuditStoreAdapter:
    """Thin adapter mapping product-agent audit events to AuditStore.log_event()."""

    def __init__(self, audit_store: Any = None):
        self._audit_store = audit_store

    def log(self, event_type: str, trip_id: str, payload: dict, user_id: Optional[str] = None) -> None:
        from spine_api.persistence import AuditStore
        store = self._audit_store or AuditStore
        store.log_event(
            event_type=event_type,
            user_id=user_id or payload.get("agent_name") or "agent_runtime",
            details={"trip_id": trip_id, **payload},
        )
