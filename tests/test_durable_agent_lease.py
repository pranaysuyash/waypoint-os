"""Tests for Durable Agent Lease and Distributed Fencing Token State Machine."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

import pytest
from src.orchestration.agent_lease import DurableAgentLeaseManager


def setup_function():
    DurableAgentLeaseManager.clear()


def test_acquire_lease_monotonic_fencing():
    lease1 = DurableAgentLeaseManager.acquire_lease("TRIP-001", "agent_marcus", ttl_seconds=10)
    assert lease1.holder_id == "agent_marcus"
    assert lease1.fencing_token == 1
    assert lease1.is_active is True

    # Validate fencing token
    assert DurableAgentLeaseManager.verify_fencing_token("TRIP-001", 1) is True
    assert DurableAgentLeaseManager.verify_fencing_token("TRIP-001", 0) is False


def test_concurrent_lease_contention_rejected():
    DurableAgentLeaseManager.acquire_lease("TRIP-002", "agent_elena", ttl_seconds=60)

    # Second worker should be rejected while unexpired
    with pytest.raises(ValueError, match="is currently locked by 'agent_elena'"):
        DurableAgentLeaseManager.acquire_lease("TRIP-002", "agent_sam", ttl_seconds=30)


def test_lease_renewal_and_voluntary_release():
    lease = DurableAgentLeaseManager.acquire_lease("TRIP-003", "agent_devlin", ttl_seconds=10)
    token = lease.lease_token

    renewed = DurableAgentLeaseManager.renew_lease("TRIP-003", token, ttl_seconds=20)
    assert renewed.ttl_seconds == 20

    released = DurableAgentLeaseManager.release_lease("TRIP-003", token)
    assert released is True

    # After release, another agent can acquire and receives incremented fencing token
    lease2 = DurableAgentLeaseManager.acquire_lease("TRIP-003", "agent_klaus", ttl_seconds=15)
    assert lease2.holder_id == "agent_klaus"
    assert lease2.fencing_token == 2
    # Old fencing token is now stale
    assert DurableAgentLeaseManager.verify_fencing_token("TRIP-003", 1) is False
    assert DurableAgentLeaseManager.verify_fencing_token("TRIP-003", 2) is True


def test_expired_lease_cannot_be_renewed_or_released_and_next_acquire_fences_it():
    lease = DurableAgentLeaseManager.acquire_lease("TRIP-004", "agent_devlin", ttl_seconds=10)
    lease.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)

    with pytest.raises(ValueError, match="has expired and cannot be renewed"):
        DurableAgentLeaseManager.renew_lease("TRIP-004", lease.lease_token, ttl_seconds=20)

    assert DurableAgentLeaseManager.get_lease("TRIP-004").is_active is False
    assert DurableAgentLeaseManager.release_lease("TRIP-004", lease.lease_token) is False

    replacement = DurableAgentLeaseManager.acquire_lease("TRIP-004", "agent_klaus", ttl_seconds=10)
    assert replacement.fencing_token == lease.fencing_token + 1
    assert DurableAgentLeaseManager.verify_fencing_token("TRIP-004", lease.fencing_token) is False
    assert DurableAgentLeaseManager.verify_fencing_token("TRIP-004", replacement.fencing_token) is True


def test_released_lease_cannot_be_renewed():
    lease = DurableAgentLeaseManager.acquire_lease("TRIP-005", "agent_elena", ttl_seconds=10)
    assert DurableAgentLeaseManager.release_lease("TRIP-005", lease.lease_token) is True

    with pytest.raises(ValueError, match="No active lease found"):
        DurableAgentLeaseManager.renew_lease("TRIP-005", lease.lease_token, ttl_seconds=20)
    assert DurableAgentLeaseManager.verify_fencing_token("TRIP-005", lease.fencing_token) is False


def test_sweep_stale_leases_is_idempotent_and_blocks_resurrection():
    lease = DurableAgentLeaseManager.acquire_lease("TRIP-006", "agent_sam", ttl_seconds=10)
    lease.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)

    assert DurableAgentLeaseManager.sweep_stale_leases() == 1
    assert DurableAgentLeaseManager.sweep_stale_leases() == 0
    assert DurableAgentLeaseManager.verify_fencing_token("TRIP-006", lease.fencing_token) is False
    with pytest.raises(ValueError, match="No active lease found"):
        DurableAgentLeaseManager.renew_lease("TRIP-006", lease.lease_token)


def test_concurrent_acquisition_has_one_winner_and_one_fence_generation():
    def acquire(holder_number: int):
        try:
            return DurableAgentLeaseManager.acquire_lease(
                "TRIP-007", f"agent-{holder_number}", ttl_seconds=30
            )
        except ValueError:
            return None

    with ThreadPoolExecutor(max_workers=8) as pool:
        leases = list(pool.map(acquire, range(8)))

    winners = [lease for lease in leases if lease is not None]
    assert len(winners) == 1
    assert winners[0].fencing_token == 1
    assert DurableAgentLeaseManager.verify_fencing_token("TRIP-007", 1) is True
