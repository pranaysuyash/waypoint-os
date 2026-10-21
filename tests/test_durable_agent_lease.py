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


# ---------------------------------------------------------------------------
# FND-0227: pipeline-version fencing
# ---------------------------------------------------------------------------


def test_acquire_stamps_pipeline_version_and_renew_succeeds_when_current(monkeypatch):
    monkeypatch.setenv("SPINE_API_PIPELINE_VERSION", "v7")
    lease = DurableAgentLeaseManager.acquire_lease("TRIP-PV-1", "agent_a", ttl_seconds=30)
    assert lease.metadata["pipeline_version"] == "v7"

    renewed = DurableAgentLeaseManager.renew_lease("TRIP-PV-1", lease.lease_token, ttl_seconds=30)
    assert renewed.metadata["pipeline_version"] == "v7"


def test_renew_refuses_lease_from_older_pipeline_version(monkeypatch):
    from src.orchestration.agent_lease import PipelineVersionMismatchError

    monkeypatch.setenv("SPINE_API_PIPELINE_VERSION", "v1")
    lease = DurableAgentLeaseManager.acquire_lease("TRIP-PV-2", "agent_a", ttl_seconds=300)

    monkeypatch.setenv("SPINE_API_PIPELINE_VERSION", "v2")
    with pytest.raises(PipelineVersionMismatchError, match="v1.*v2"):
        DurableAgentLeaseManager.renew_lease("TRIP-PV-2", lease.lease_token, ttl_seconds=30)


def test_renew_without_version_stamp_stays_backward_compatible(monkeypatch):
    monkeypatch.setenv("SPINE_API_PIPELINE_VERSION", "v9")
    lease = DurableAgentLeaseManager.acquire_lease("TRIP-PV-3", "agent_a", ttl_seconds=300)
    # Pre-stamp leases (deployed before FND-0227) carry no version — must not break.
    lease.metadata.pop("pipeline_version")

    renewed = DurableAgentLeaseManager.renew_lease("TRIP-PV-3", lease.lease_token, ttl_seconds=30)
    assert renewed.metadata.get("pipeline_version") is None


def test_explicit_caller_pipeline_version_is_preserved(monkeypatch):
    monkeypatch.setenv("SPINE_API_PIPELINE_VERSION", "v3")
    lease = DurableAgentLeaseManager.acquire_lease(
        "TRIP-PV-4", "agent_a", ttl_seconds=300, metadata={"pipeline_version": "legacy"}
    )
    assert lease.metadata["pipeline_version"] == "legacy"


# ---------------------------------------------------------------------------
# FND-0160: terminal lease retention
# ---------------------------------------------------------------------------


def test_prune_removes_only_old_terminal_leases():
    from src.orchestration.agent_lease import MemoryAgentLeaseBackend

    backend = MemoryAgentLeaseBackend()
    old = backend.acquire_lease("TRIP-PRUNE-OLD", "agent_a", ttl_seconds=10)
    fresh = backend.acquire_lease("TRIP-PRUNE-FRESH", "agent_b", ttl_seconds=10)
    backend.acquire_lease("TRIP-PRUNE-ACTIVE", "agent_c", ttl_seconds=3000)

    backend.release_lease("TRIP-PRUNE-OLD", old.lease_token)
    backend.release_lease("TRIP-PRUNE-FRESH", fresh.lease_token)
    # Artificially age the OLD terminal lease past any retention window.
    old.expires_at = datetime.now(timezone.utc) - timedelta(days=365)

    pruned = backend.prune_terminal_leases(older_than_days=30)
    assert pruned == 1
    assert backend.get_lease("TRIP-PRUNE-OLD") is None
    assert backend.get_lease("TRIP-PRUNE-FRESH") is not None
    assert backend.get_lease("TRIP-PRUNE-ACTIVE").is_active is True


def test_prune_rejects_invalid_retention_config(monkeypatch):
    from src.orchestration.agent_lease import MemoryAgentLeaseBackend

    monkeypatch.setenv("SPINE_API_LEASE_TERMINAL_RETENTION_DAYS", "banana")
    with pytest.raises(ValueError, match="non-negative integer"):
        MemoryAgentLeaseBackend().prune_terminal_leases()
