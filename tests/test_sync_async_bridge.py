"""_SyncAsyncBridge starvation-regression tests — FND-0367 (2026-10-24).

Reproduced live during the fare-drop visual pass: the original bridge held a
process-wide lock across ``future.result()`` with no timeout, so one stuck
sync-facade SQL call deadlocked every sync TripStore endpoint in the process
until restart. These tests pin the redesign:

  * no global serialization — concurrent bridge calls proceed independently;
  * every call is bounded — a stuck coroutine raises instead of waiting forever;
  * a stuck call does NOT starve subsequent calls (the core regression);
  * the bridge loop survives stuck calls and stays usable.

Database-free: the coroutines here are pure asyncio, so the bridge semantics
are tested in isolation.
"""

import asyncio
import threading
import time

import pytest

from spine_api.persistence import _SyncAsyncBridge


def test_bridge_returns_values_from_the_background_loop():
    bridge = _SyncAsyncBridge(call_timeout_s=5)
    try:
        async def value():
            await asyncio.sleep(0)
            return 42

        assert bridge.run(value()) == 42
    finally:
        bridge.loop.call_soon_threadsafe(bridge.loop.stop)


def test_stuck_call_times_out_and_later_calls_still_succeed():
    """THE regression: one stuck call must not starve the bridge.

    Old behavior: the stuck call held _run_lock forever; every subsequent
    sync call queued behind it until process restart.
    """
    bridge = _SyncAsyncBridge(call_timeout_s=0.3)
    try:
        async def stuck():
            await asyncio.sleep(30)

        start = time.monotonic()
        with pytest.raises(RuntimeError, match="exceeded 0.3s"):
            bridge.run(stuck())
        elapsed = time.monotonic() - start
        assert elapsed < 5, "the caller must stop waiting at the timeout, not at the coroutine"

        async def healthy():
            await asyncio.sleep(0)
            return "ok"

        # Immediately after the stuck call: the bridge is still usable.
        assert bridge.run(healthy()) == "ok"
        assert bridge.run(healthy()) == "ok"
    finally:
        bridge.loop.call_soon_threadsafe(bridge.loop.stop)


def test_concurrent_calls_are_not_serialized_behind_a_slow_one():
    """No global lock: slow and fast calls interleave; fast ones don't queue."""
    bridge = _SyncAsyncBridge(call_timeout_s=5)
    try:
        async def slow():
            await asyncio.sleep(1.0)
            return "slow"

        async def fast():
            await asyncio.sleep(0)
            return "fast"

        slow_result = {}
        t = threading.Thread(target=lambda: slow_result.update(value=bridge.run(slow())))
        t.start()
        time.sleep(0.05)  # let the slow call start
        start = time.monotonic()
        assert bridge.run(fast()) == "fast"
        fast_elapsed = time.monotonic() - start
        t.join(timeout=5)
        assert slow_result["value"] == "slow"
        assert fast_elapsed < 0.5, "the fast call must not wait behind the slow one"
    finally:
        bridge.loop.call_soon_threadsafe(bridge.loop.stop)


def test_bridge_survives_multiple_stuck_calls():
    bridge = _SyncAsyncBridge(call_timeout_s=0.2)
    try:
        async def stuck():
            await asyncio.sleep(30)

        for _ in range(3):
            with pytest.raises(RuntimeError):
                bridge.run(stuck())

        async def healthy():
            await asyncio.sleep(0)
            return "still-here"

        assert bridge.run(healthy()) == "still-here"
        assert not bridge.loop.is_closed()
    finally:
        bridge.loop.call_soon_threadsafe(bridge.loop.stop)


def test_timeout_default_resolves_from_env(monkeypatch):
    from spine_api import persistence

    monkeypatch.setenv("TRIPSTORE_BRIDGE_TIMEOUT_SECONDS", "7.5")
    bridge = persistence._SyncAsyncBridge()
    try:
        assert bridge.call_timeout_s == 7.5
    finally:
        bridge.loop.call_soon_threadsafe(bridge.loop.stop)

    monkeypatch.setenv("TRIPSTORE_BRIDGE_TIMEOUT_SECONDS", "garbage")
    bridge2 = persistence._SyncAsyncBridge()
    try:
        assert bridge2.call_timeout_s == 30.0  # documented default
    finally:
        bridge2.loop.call_soon_threadsafe(bridge2.loop.stop)


def test_shutdown_bridge_reports_clear_error():
    bridge = _SyncAsyncBridge(call_timeout_s=5)
    bridge.loop.call_soon_threadsafe(bridge.loop.stop)
    bridge._thread.join(timeout=2)
    bridge.loop.close()

    async def any_coro():
        return 1

    # A closed bridge loop fails loudly (RuntimeError), never silently hangs.
    with pytest.raises(RuntimeError, match="loop is closed|shut down"):
        bridge.run(any_coro())
