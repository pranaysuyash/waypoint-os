"""
Agent Runtime & Resilience Engine Tests (PER-0700, PER-0924).
"""

from datetime import datetime, timedelta, timezone
from src.agents.runtime import (
    ExecutionLease,
    ExecutionCheckpoint,
    CheckpointStore,
    ZombieLeaseSweeper,
    DeadLetterQueue,
)


def test_lease_heartbeat_and_expiry():
    t0 = datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc)
    lease = ExecutionLease(
        lease_id="LEASE-001",
        work_item_id="WORK-001",
        owner_worker_id="WORKER-A",
        acquired_at=t0,
        lease_expires_at=t0 + timedelta(seconds=60),
        last_heartbeat_at=t0,
        ttl_seconds=60,
    )

    assert lease.is_expired(t0 + timedelta(seconds=30)) is False
    assert lease.is_expired(t0 + timedelta(seconds=70)) is True

    # Test heartbeat extension
    lease.heartbeat(extend_seconds=120, now=t0 + timedelta(seconds=10))
    assert lease.lease_expires_at > t0 + timedelta(seconds=60)


def test_zombie_lease_sweeper():
    t0 = datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc)
    leases = {
        "WORK-ACTIVE": ExecutionLease("L1", "WORK-ACTIVE", "W1", t0, t0 + timedelta(seconds=60), t0, 60),
        "WORK-ZOMBIE": ExecutionLease("L2", "WORK-ZOMBIE", "W2", t0, t0 + timedelta(seconds=10), t0, 10),
    }

    now = t0 + timedelta(seconds=30)
    reclaimed = ZombieLeaseSweeper.sweep(leases, now=now)
    assert "WORK-ZOMBIE" in reclaimed
    assert "WORK-ACTIVE" not in reclaimed


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
