"""
tests/test_inbound_sse_bounds.py — PA-14 S2 evidence (2026-09-06).

FAILED BEFORE: the inbound SSE generator ran ``while True`` with client
disconnect as the only exit, and its finally-cleanup removed the queue but
left an empty list in ``_TRIP_EVENT_LISTENERS[trip_id]`` forever — the dict
grew without bound, one entry per trip ever streamed.

PASSES AFTER:
- bounded lifetime via a wait-cycle budget (the ``max_iterations`` pattern
  from routers/trip_observability.py): on exhaustion the stream emits a final
  ``STREAM_LIMIT_REACHED`` event with ``reconnect: true`` and closes;
- the finally-cleanup prunes the dict entry once NO listeners remain, while
  concurrent listeners for the same trip keep working.
"""

from __future__ import annotations

import asyncio

import pytest

import spine_api.routers.inbound as inbound


@pytest.fixture(autouse=True)
def _clean_listeners():
    inbound._TRIP_EVENT_LISTENERS.clear()
    yield
    inbound._TRIP_EVENT_LISTENERS.clear()


@pytest.fixture()
def fast_budget(monkeypatch):
    """Shrink the budget so exhaustion is testable in milliseconds."""
    monkeypatch.setattr(inbound, "SSE_MAX_WAIT_CYCLES", 3)
    monkeypatch.setattr(inbound, "SSE_WAIT_TIMEOUT_SECONDS", 0.001)


def test_prune_keeps_concurrent_listeners():
    q1, q2 = asyncio.Queue(), asyncio.Queue()
    inbound._TRIP_EVENT_LISTENERS["trip_sse_a"] = [q1, q2]

    inbound._prune_trip_listener("trip_sse_a", q1)
    assert inbound._TRIP_EVENT_LISTENERS["trip_sse_a"] == [q2]

    inbound._prune_trip_listener("trip_sse_a", q2)
    assert "trip_sse_a" not in inbound._TRIP_EVENT_LISTENERS  # entry dropped


def test_prune_ignores_unknown_trip_and_stranger_queue():
    # Must not raise when the trip entry was already removed.
    inbound._prune_trip_listener("trip_sse_missing", asyncio.Queue())
    # A queue that never registered must not disturb existing listeners.
    inbound._TRIP_EVENT_LISTENERS["trip_sse_b"] = [asyncio.Queue()]
    inbound._prune_trip_listener("trip_sse_b", asyncio.Queue())
    assert len(inbound._TRIP_EVENT_LISTENERS["trip_sse_b"]) == 1


def test_stream_exhausts_budget_emits_reconnect_and_prunes(fast_budget):
    async def _scenario():
        queue: asyncio.Queue = asyncio.Queue()
        inbound._TRIP_EVENT_LISTENERS["trip_sse_c"] = [queue]

        chunks = []
        async for chunk in inbound._trip_event_stream("trip_sse_c", queue):
            chunks.append(chunk)

        return chunks

    chunks = asyncio.run(asyncio.wait_for(_scenario(), timeout=10.0))

    # First event: CONNECTED heartbeat.
    assert '"event": "CONNECTED"' in chunks[0]
    # Heartbeats for each silent wait cycle, then the final reconnect event.
    heartbeat_count = sum(1 for c in chunks if '"event": "HEARTBEAT"' in c)
    assert heartbeat_count == 3  # budget of SSE_MAX_WAIT_CYCLES exhausted
    final = chunks[-1]
    assert '"event": "STREAM_LIMIT_REACHED"' in final
    assert '"reconnect": true' in final
    # Cleanup pruned the emptied listener entry (the leak fix).
    assert "trip_sse_c" not in inbound._TRIP_EVENT_LISTENERS


def test_stream_event_delivery_resets_nothing_but_stays_bounded(fast_budget):
    """Delivered events consume budget too; stream always terminates."""
    async def _scenario():
        queue: asyncio.Queue = asyncio.Queue()
        inbound._TRIP_EVENT_LISTENERS["trip_sse_d"] = [queue]
        for i in range(2):
            await queue.put({"event": "STATE_SYNC", "seq": i})

        chunks = []
        async for chunk in inbound._trip_event_stream("trip_sse_d", queue):
            chunks.append(chunk)
        return chunks

    chunks = asyncio.run(asyncio.wait_for(_scenario(), timeout=10.0))
    assert any('"event": "STATE_SYNC"' in c for c in chunks)
    assert chunks[-1].startswith("data: ") and "STREAM_LIMIT_REACHED" in chunks[-1]
    assert "trip_sse_d" not in inbound._TRIP_EVENT_LISTENERS


def test_stream_endpoint_rejects_unknown_trip(session_client):
    """The live endpoint's ownership check still fires before streaming."""
    resp = session_client.get("/api/v1/inbound/stream-events/trip_sse_missing")
    assert resp.status_code in (404, 401, 403)


# ---------------------------------------------------------------------------
# FND-0229: per-tenant SSE connection cap, oldest-first eviction with a
# retry hint, and explicit slot eviction on disconnect.
# ---------------------------------------------------------------------------

from types import SimpleNamespace  # noqa: E402

from spine_api.core import sse_registry  # noqa: E402
from spine_api.core.sse_registry import (  # noqa: E402
    SSE_CONNECTION_REGISTRY,
    SSEConfigError,
    SSEConnectionRegistry,
)


@pytest.fixture(autouse=True)
def _reset_sse_registry(monkeypatch):
    """Isolate the process-wide registry + cap for every test in this file."""
    monkeypatch.delenv("SPINE_API_SSE_MAX_CONNECTIONS_PER_TENANT", raising=False)
    SSE_CONNECTION_REGISTRY._by_agency.clear()
    SSE_CONNECTION_REGISTRY._cap = None
    yield
    SSE_CONNECTION_REGISTRY._by_agency.clear()
    SSE_CONNECTION_REGISTRY._cap = None


class TestSSEConfig:
    def test_default_cap(self, monkeypatch):
        monkeypatch.delenv("SPINE_API_SSE_MAX_CONNECTIONS_PER_TENANT", raising=False)
        assert sse_registry.max_connections_per_tenant() == 50

    def test_env_override(self, monkeypatch):
        monkeypatch.setenv("SPINE_API_SSE_MAX_CONNECTIONS_PER_TENANT", "7")
        assert sse_registry.max_connections_per_tenant() == 7

    @pytest.mark.parametrize("raw", ["abc", "0", "-3", "1.5"])
    def test_invalid_values_fail_closed(self, monkeypatch, raw):
        monkeypatch.setenv("SPINE_API_SSE_MAX_CONNECTIONS_PER_TENANT", raw)
        with pytest.raises(SSEConfigError):
            sse_registry.max_connections_per_tenant()


class TestRegistryCapAndEviction:
    def test_register_under_cap_no_eviction(self):
        registry = SSEConnectionRegistry(cap=3)
        conns = [registry.register("ag-1") for _ in range(3)]
        assert all(not c.evicted for c in conns)
        assert registry.active_count("ag-1") == 3

    def test_cap_evicts_oldest_first_with_retry_hint(self):
        registry = SSEConnectionRegistry(cap=2)
        first = registry.register("ag-1")
        second = registry.register("ag-1")

        third = registry.register("ag-1")

        assert first.evicted and first.closed.is_set()
        assert not second.evicted and not second.closed.is_set()
        assert not third.evicted
        assert registry.active_count("ag-1") == 2

        fourth = registry.register("ag-1")
        assert second.evicted and second.closed.is_set()
        assert not fourth.evicted

    def test_caps_are_per_tenant(self):
        registry = SSEConnectionRegistry(cap=1)
        a = registry.register("ag-a")
        b = registry.register("ag-b")
        assert not a.evicted and not b.evicted
        assert registry.active_count("ag-a") == 1
        assert registry.active_count("ag-b") == 1

    def test_unregister_frees_slots_and_is_idempotent(self):
        registry = SSEConnectionRegistry(cap=1)
        first = registry.register("ag-1")
        registry.unregister(first)
        registry.unregister(first)  # idempotent
        assert registry.active_count("ag-1") == 0

        # Slot freed: next register does not evict anything.
        replacement = registry.register("ag-1")
        assert not replacement.evicted


def test_stream_emits_tenant_cap_eviction_and_frees_slot(monkeypatch):
    """Eviction mid-stream: the older generator exits with a retry hint.

    Uses a REAL (slow) wait timeout so the stream is still alive when the
    eviction fires — fast_budget would exhaust it first.
    """
    monkeypatch.setattr(inbound, "SSE_WAIT_TIMEOUT_SECONDS", 1.0)
    registry = SSEConnectionRegistry(cap=1)

    async def _scenario():
        queue_a: asyncio.Queue = asyncio.Queue()
        conn_a = registry.register("ag-sse")
        inbound._TRIP_EVENT_LISTENERS["trip_sse_evict"] = [queue_a]

        async def _consume():
            chunks = []
            async for chunk in inbound._trip_event_stream(
                "trip_sse_evict", queue_a, conn_a
            ):
                chunks.append(chunk)
            return chunks

        consume_task = asyncio.ensure_future(_consume())
        # Let the stream start (CONNECTED + first wait cycle), then saturate
        # the tenant: the new registration must evict conn_a mid-stream.
        await asyncio.sleep(0.05)
        evictor = registry.register("ag-sse")
        chunks = await asyncio.wait_for(consume_task, timeout=10.0)
        # The evictor's own slot is test scaffolding, not the stream under test.
        evictor.unregister()
        return chunks

    chunks = asyncio.run(asyncio.wait_for(_scenario(), timeout=10.0))

    assert any('"event": "CONNECTED"' in c for c in chunks)
    final = chunks[-1]
    assert "TENANT_CAP_EVICTION" in final
    assert '"reconnect": true' in final
    assert '"reason": "tenant_connection_cap"' in final
    # The evicted slot was explicitly unregistered on exit.
    assert registry.active_count("ag-sse") == 0
    assert "trip_sse_evict" not in inbound._TRIP_EVENT_LISTENERS


def test_stream_unregisters_on_normal_exhaustion(fast_budget):
    """Disconnect/budget exhaustion path frees the registry slot too."""
    registry = SSEConnectionRegistry(cap=5)

    async def _scenario():
        queue: asyncio.Queue = asyncio.Queue()
        conn = registry.register("ag-sse-2")
        inbound._TRIP_EVENT_LISTENERS["trip_sse_norm"] = [queue]

        chunks = []
        async for chunk in inbound._trip_event_stream(
            "trip_sse_norm", queue, conn
        ):
            chunks.append(chunk)
        return chunks

    chunks = asyncio.run(asyncio.wait_for(_scenario(), timeout=10.0))
    assert chunks[-1].startswith("data: ") and "STREAM_LIMIT_REACHED" in chunks[-1]
    assert registry.active_count("ag-sse-2") == 0


def test_observability_stream_emits_eviction_and_frees_slot(monkeypatch):
    """The trip_observability SSE surface honors the same tenant cap.

    The endpoint registers on the process-wide singleton, so the test drives
    that singleton (the autouse fixture isolates it) and evicts the
    endpoint's own connection mid-stream with a third registration.
    """
    import spine_api.routers.trip_observability as trip_observability

    SSE_CONNECTION_REGISTRY._cap = 1
    first = SSE_CONNECTION_REGISTRY.register("ag-obs")

    # Keep the poll loop hermetic and cheap.
    monkeypatch.setattr(
        trip_observability.AuditStore,
        "get_events_for_trip",
        staticmethod(lambda trip_id: []),
    )
    monkeypatch.setattr(
        trip_observability.TripStore,
        "get_trip_for_agency",
        staticmethod(lambda trip_id, agency_id: {"trip_id": trip_id}),
    )

    async def _scenario():
        async def _consume():
            response = await trip_observability.stream_trip_events(
                "trip-obs", SimpleNamespace(id="ag-obs")
            )
            chunks = []
            async for chunk in response.body_iterator:
                chunks.append(chunk if isinstance(chunk, str) else chunk.decode())
            return chunks

        consume_task = asyncio.ensure_future(_consume())
        # t≈0.05s: the endpoint registered its own connection (evicting
        # `first`) and is inside its first 1s poll cycle.
        await asyncio.sleep(0.05)
        assert first.evicted and first.closed.is_set()
        # Now evict the endpoint's own connection — its loop must observe
        # the closed event and exit with the retry hint.
        evictor = SSE_CONNECTION_REGISTRY.register("ag-obs")
        chunks = await asyncio.wait_for(consume_task, timeout=15.0)
        # The evictor's own slot is test scaffolding, not the endpoint's.
        evictor.unregister()
        return chunks

    chunks = asyncio.run(asyncio.wait_for(_scenario(), timeout=15.0))
    assert any("tenant_cap_eviction" in c for c in chunks)
    assert any('"reconnect": true' in c for c in chunks)
    # The endpoint's own slot is freed by the generator's finally.
    assert SSE_CONNECTION_REGISTRY.active_count("ag-obs") == 0
