"""
sse_registry.py — Per-tenant SSE connection registry (FND-0229).

Every SSE fan-out endpoint registers each accepted connection here so a
single tenant (agency) cannot hold unbounded server resources with idle
streams. The registry enforces:

- **Per-agency connection cap** — config-driven via
  ``SPINE_API_SSE_MAX_CONNECTIONS_PER_TENANT`` (explicit integer parsing,
  fail-closed on invalid values, same doctrine as
  ``SPINE_API_LOCKING_BACKEND``), default 50.
- **Oldest-first eviction** — when a new connection would exceed the cap,
  the OLDEST connection for that agency is evicted: its ``closed`` event is
  set with ``evicted=True`` so its generator can emit a retry-hint frame
  (``reconnect: true``) and exit cleanly. No connection is silently
  dropped mid-frame.
- **Explicit eviction on client disconnect** — endpoints call
  ``unregister()`` from their generator ``finally`` (Starlette cancels the
  generator when the client goes away), so slots are freed immediately.

Heartbeat keepalives are the endpoints' responsibility (both SSE surfaces
already emit them per SSE convention); this module only owns capacity.
"""

from __future__ import annotations

import asyncio
import itertools
import logging
import os
import time
from collections import OrderedDict
from typing import Dict, Optional

logger = logging.getLogger("spine_api.core.sse_registry")

DEFAULT_MAX_CONNECTIONS_PER_TENANT = 50


class SSEConfigError(RuntimeError):
    """Raised when SPINE_API_SSE_MAX_CONNECTIONS_PER_TENANT is invalid.

    Unknown/non-integer/zero-or-negative values fail closed (same doctrine
    as SPINE_API_LOCKING_BACKEND): a typoed capacity must never silently
    select unlimited connections.
    """

    def __init__(self, raw_value: str):
        self.raw_value = raw_value
        super().__init__(
            f"SPINE_API_SSE_MAX_CONNECTIONS_PER_TENANT={raw_value!r} is not a "
            "positive integer. Remove the variable to use the default "
            f"({DEFAULT_MAX_CONNECTIONS_PER_TENANT}) or set a positive integer."
        )


def max_connections_per_tenant() -> int:
    """Parse the per-tenant SSE connection cap. Fail-closed on bad values."""
    raw = os.environ.get("SPINE_API_SSE_MAX_CONNECTIONS_PER_TENANT", "").strip()
    if not raw:
        return DEFAULT_MAX_CONNECTIONS_PER_TENANT
    try:
        value = int(raw)
    except ValueError:
        raise SSEConfigError(raw)
    if value < 1:
        raise SSEConfigError(raw)
    return value


class SSEConnection:
    """One live SSE stream registered for an agency."""

    def __init__(self, agency_id: str, conn_id: str, registry: "SSEConnectionRegistry"):
        self.agency_id = agency_id
        self.conn_id = conn_id
        self._registry = registry
        self.connected_at: float = time.monotonic()
        self.closed = asyncio.Event()
        self.evicted = False

    @property
    def should_close(self) -> bool:
        return self.closed.is_set()

    def unregister(self) -> None:
        """Free this slot in its owning registry (idempotent).

        Generators call this from their ``finally`` so the exit path is
        bound to the connection's own registry rather than to whichever
        module-level singleton happens to be imported.
        """
        self._registry.unregister(self)


class SSEConnectionRegistry:
    """Process-local registry enforcing the per-tenant SSE connection cap."""

    def __init__(self, cap: Optional[int] = None):
        self._cap = cap
        self._by_agency: Dict[str, "OrderedDict[str, SSEConnection]"] = {}
        self._ids = itertools.count(1)

    @property
    def cap(self) -> int:
        if self._cap is None:
            self._cap = max_connections_per_tenant()
        return self._cap

    def register(self, agency_id: str) -> SSEConnection:
        """Register a connection, evicting the oldest tenant peer over cap.

        Returns the NEW connection. Evicted peers observe
        ``connection.evicted`` / ``connection.closed`` and must emit a
        retry-hint frame before exiting.
        """
        connections = self._by_agency.setdefault(agency_id, OrderedDict())
        conn = SSEConnection(agency_id, conn_id=f"sse-{next(self._ids)}", registry=self)
        connections[conn.conn_id] = conn

        while len(connections) > self.cap:
            oldest_id, oldest = next(iter(connections.items()))
            # The just-registered connection can never be the eviction
            # candidate while cap >= 1: it is the newest entry.
            del connections[oldest_id]
            oldest.evicted = True
            oldest.closed.set()
            logger.warning(
                "SSE tenant cap (%d) reached for agency %s — evicted oldest "
                "connection %s with retry hint.",
                self.cap,
                agency_id,
                oldest.conn_id,
            )
        return conn

    def unregister(self, conn: SSEConnection) -> None:
        """Remove a connection (idempotent). Called on disconnect/exit."""
        connections = self._by_agency.get(conn.agency_id)
        if connections is None:
            return
        connections.pop(conn.conn_id, None)
        if not connections:
            self._by_agency.pop(conn.agency_id, None)
        conn.closed.set()

    def active_count(self, agency_id: str) -> int:
        return len(self._by_agency.get(agency_id, ()))


# Process-wide registry used by every SSE fan-out endpoint.
SSE_CONNECTION_REGISTRY = SSEConnectionRegistry()
