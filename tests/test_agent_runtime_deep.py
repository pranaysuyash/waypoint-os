"""
tests/test_agent_runtime_deep.py — Unit tests for PER-0700 deep agentic runtime capabilities.
"""

import asyncio
import pytest

from src.agents.checkpoints import CheckpointStore
from src.agents.idempotency import IdempotencyRegistry, IdempotencyStatus
from src.agents.sandbox import TenantConcurrencyLimiter, ToolSandbox
from src.agents.visualizer import AgentExecutionVisualizer


def test_idempotency_key_lifecycle():
    """Verify idempotency key acquisition, duplicate suppression, and completion caching."""
    registry = IdempotencyRegistry()
    trip_id = "trip_idem_101"
    action = "reserve_hotel_room"
    payload = {"hotel_id": "hot_99", "room_type": "DELUXE", "nights": 3}

    key = registry.generate_key(trip_id, action, payload)

    # 1. Acquire key
    acquired, rec = registry.try_acquire(key, trip_id, action, payload)
    assert acquired is True
    assert rec.status == IdempotencyStatus.PENDING

    # 2. Second concurrent acquire should be rejected (returns pending record)
    acquired_dup, rec_dup = registry.try_acquire(key, trip_id, action, payload)
    assert acquired_dup is False
    assert rec_dup.status == IdempotencyStatus.PENDING

    # 3. Mark completed with response
    response_data = {"booking_reference": "CONF-998877", "amount_charged": 650.0}
    assert registry.mark_completed(
        key, response_data, fencing_token=rec.fencing_token
    ) is True

    # 4. Subsequent acquire returns completed cached result
    acquired_post, rec_post = registry.try_acquire(key, trip_id, action, payload)
    assert acquired_post is False
    assert rec_post.status == IdempotencyStatus.COMPLETED
    assert rec_post.response_payload["booking_reference"] == "CONF-998877"


def test_checkpoint_store_and_resumption():
    """Verify execution state checkpoint persistence and visualizer generation."""
    store = CheckpointStore()
    run_id = "run_chk_001"
    trip_id = "trip_chk_001"

    # Step 1 Checkpoint
    cp1 = store.save_checkpoint(
        run_id=run_id,
        trip_id=trip_id,
        step_index=0,
        step_name="parse_intent",
        completed_steps=["parse_intent"],
        state_payload={"origin": "JFK", "destination": "CDG"},
        tool_outputs={"parser": {"dates": ["2026-09-01", "2026-09-08"]}},
    )
    assert cp1.step_index == 0

    # Step 2 Checkpoint
    cp2 = store.save_checkpoint(
        run_id=run_id,
        trip_id=trip_id,
        step_index=1,
        step_name="search_flights",
        completed_steps=["parse_intent", "search_flights"],
        state_payload={"origin": "JFK", "destination": "CDG", "selected_flight": "AF22"},
        tool_outputs={"flight_search": {"options_found": 5}},
    )
    assert cp2.step_index == 1

    latest = store.get_latest_checkpoint(run_id)
    assert latest.step_index == 1
    assert latest.step_name == "search_flights"
    assert "parse_intent" in latest.completed_steps

    # Generate Mermaid Flow
    all_cps = store.get_all_checkpoints(run_id)
    mermaid_diagram = AgentExecutionVisualizer.generate_mermaid_flow(run_id, all_cps, "COMPLETED")
    assert "flowchart TD" in mermaid_diagram
    assert "Step 0: parse_intent" in mermaid_diagram
    assert "Step 1: search_flights" in mermaid_diagram


@pytest.mark.asyncio
async def test_tool_sandbox_execution_and_timeout():
    """Verify tool sandboxing executes normal tools and enforces strict timeouts."""
    # Fast tool succeeds
    async def fast_tool(x: int, y: int) -> int:
        return x + y

    res_fast = await ToolSandbox.execute_tool("math_tool", fast_tool, 10, 20)
    assert res_fast.success is True
    assert res_fast.output == 30
    assert res_fast.duration_ms > 0

    # Slow tool times out
    async def slow_tool():
        await asyncio.sleep(0.5)
        return "finished"

    res_slow = await ToolSandbox.execute_tool("slow_tool", slow_tool, custom_timeout_seconds=0.1)
    assert res_slow.success is False
    assert "timed out after 0.1s" in res_slow.error_message


def test_tenant_concurrency_limiter():
    """Verify per-agency concurrency throttling."""
    limiter = TenantConcurrencyLimiter(default_max_concurrent=2)
    agency = "agency_throttle_test"

    # Acquire 2 slots (allowed)
    assert limiter.try_acquire_slot(agency) is True
    assert limiter.try_acquire_slot(agency) is True
    assert limiter.get_active_count(agency) == 2

    # 3rd slot should be rejected
    assert limiter.try_acquire_slot(agency) is False

    # Release 1 slot
    limiter.release_slot(agency)
    assert limiter.get_active_count(agency) == 1

    # Now acquisition succeeds
    assert limiter.try_acquire_slot(agency) is True
