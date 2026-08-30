import asyncio
import pytest
from spine_api.core.locking import (
    TripConcurrencyConflictError,
    _trip_id_to_bigint,
    trip_advisory_lock,
)


def test_trip_id_to_bigint_deterministic():
    trip_id = "trip_2333bff6434d"
    val1 = _trip_id_to_bigint(trip_id)
    val2 = _trip_id_to_bigint(trip_id)
    assert val1 == val2
    assert isinstance(val1, int)
    # Must fit within signed 64-bit integer
    assert -(2**63) <= val1 < 2**63


@pytest.mark.asyncio
async def test_in_memory_lock_mutual_exclusion():
    trip_id = "trip_test_concurrency_1"
    order = []

    async def task(task_id: int, delay: float):
        async with trip_advisory_lock(None, trip_id, timeout_seconds=2.0):
            order.append(f"{task_id}_start")
            await asyncio.sleep(delay)
            order.append(f"{task_id}_end")

    await asyncio.gather(
        task(1, 0.05),
        task(2, 0.01),
    )

    # Task 1 must finish completely before Task 2 starts
    assert order == ["1_start", "1_end", "2_start", "2_end"]


@pytest.mark.asyncio
async def test_in_memory_lock_timeout_raises_conflict():
    trip_id = "trip_test_timeout_1"

    async def holding_task():
        async with trip_advisory_lock(None, trip_id, timeout_seconds=1.0):
            await asyncio.sleep(0.5)

    async def waiting_task():
        await asyncio.sleep(0.05)
        # Timeout quickly while holding_task is still running
        with pytest.raises(TripConcurrencyConflictError):
            async with trip_advisory_lock(None, trip_id, timeout_seconds=0.1):
                pass

    await asyncio.gather(holding_task(), waiting_task())
