"""
Agent Runtime & Resilience Engine Tests (PER-0700, PER-0924).

Lease-resilience coverage moved to the durable lease (FND-0213 superseded the
in-process ``ExecutionLease``/``ZombieLeaseSweeper``, which had zero callers
outside their own tests): expiry/heartbeat semantics live in
``tests/test_durable_agent_lease.py`` and stale-sweep in the SQL/memory
backend sweeps exercised there. This file keeps runtime-local resilience
surfaces (checkpoints, DLQ) and a behavioral echo of the lease semantics
against the durable backend.
"""

from datetime import datetime, timedelta, timezone

from src.agents.runtime import (
    ExecutionCheckpoint,
    CheckpointStore,
    DeadLetterQueue,
)
from src.orchestration.agent_lease import MemoryAgentLeaseBackend


def test_lease_heartbeat_and_expiry():
    """Durable-lease echo of the retired ExecutionLease semantics (FND-0213)."""
    backend = MemoryAgentLeaseBackend()
    lease = backend.acquire_lease("trip-resilience-1", "WORKER-A", ttl_seconds=60)

    assert lease.is_expired() is False
    renewed = backend.renew_lease("trip-resilience-1", lease.lease_token, ttl_seconds=120)
    assert renewed.expires_at > lease.acquired_at + timedelta(seconds=60)

    # A stale holder (old fencing token) is rejected after re-acquisition.
    backend.release_lease("trip-resilience-1", renewed.lease_token)
    second = backend.acquire_lease("trip-resilience-1", "WORKER-B", ttl_seconds=60)
    assert second.fencing_token > renewed.fencing_token
    assert backend.verify_fencing_token("trip-resilience-1", renewed.fencing_token) is False
    assert backend.verify_fencing_token("trip-resilience-1", second.fencing_token) is True


def test_stale_lease_sweeper():
    """Durable-lease echo of the retired ZombieLeaseSweeper semantics (FND-0213)."""
    backend = MemoryAgentLeaseBackend()
    backend.acquire_lease("trip-active", "W1", ttl_seconds=60)
    backend.acquire_lease("trip-zombie", "W2", ttl_seconds=1)

    backend._leases["trip-zombie"].expires_at = (
        datetime.now(timezone.utc) - timedelta(seconds=10)
    )
    swept = backend.sweep_stale_leases()
    assert swept == 1
    assert backend._leases["trip-zombie"].is_active is False
    assert backend._leases["trip-active"].is_active is True


def test_execution_checkpoint_save_and_resume():
    cp = ExecutionCheckpoint(
        checkpoint_id="CP-001",
        trip_id="TRIP-990",
        run_id="RUN-881",
        step_name="pricing_scan",
        completed_steps=["intake_parse", "inventory_search"],
        state_snapshot={"flight_id": "FL-BA112", "price_usd": 1200.0},
    )

    CheckpointStore.save(cp)
    retrieved = CheckpointStore.get_latest("TRIP-990", "RUN-881")
    assert retrieved is not None
    assert retrieved.step_name == "pricing_scan"
    assert "intake_parse" in retrieved.completed_steps
    assert retrieved.state_snapshot["price_usd"] == 1200.0


def test_dead_letter_queue_quarantine():
    record = DeadLetterQueue.quarantine(
        trip_id="TRIP-POISON",
        run_id="RUN-FAIL",
        error="Malformed supplier XML response with recursive entity bomb",
        retry_count=3,
    )
    assert record["status"] == "QUARANTINED"
    assert DeadLetterQueue.get("TRIP-POISON", "RUN-FAIL") is not None
