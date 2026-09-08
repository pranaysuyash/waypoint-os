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
