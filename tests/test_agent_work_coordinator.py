"""Direct tests for SQLWorkCoordinator — the durable SQL-backed work lease coordinator.

These tests require a running PostgreSQL instance (TRIPSTORE_BACKEND=sql).
They use the shared test DB via db_session and are skipped when Postgres
is unavailable.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import text

from src.agents.runtime import RetryPolicy, WorkItem, WorkStatus


pytestmark = pytest.mark.require_postgres


@pytest.fixture(autouse=True)
async def _ensure_schema(db_session):
    """Ensure the agent_work_leases table exists via the coordinator.

    Runs once before each test in this file. Idempotent.
    """
    from spine_api.services.agent_work_coordinator import SQLWorkCoordinator

    coordinator = SQLWorkCoordinator()
    coordinator.ensure_schema()
    # Clear any stale data from prior tests
    await db_session.execute(text("DELETE FROM agent_work_leases"))
    await db_session.commit()


def _make_item(
    trip_id: str = "trip_001",
    action: str = "test_action",
    agent_name: str = "test_agent",
    suffix: str = "",
) -> WorkItem:
    return WorkItem(
        agent_name=agent_name,
        trip_id=trip_id,
        action=action,
        idempotency_key=f"{agent_name}:{trip_id}:{action}{suffix}",
        payload={"origin": "test"},
    )


_default_retry = RetryPolicy(max_attempts=3, backoff_seconds=(0, 1, 5))


class TestSQLWorkCoordinatorEnsureSchema:
    """Schema creation and idempotency."""

    def test_ensure_schema_creates_table(self, db_session):
        from spine_api.services.agent_work_coordinator import SQLWorkCoordinator

        coordinator = SQLWorkCoordinator(lease_seconds=60)
        coordinator.ensure_schema()

        result = db_session.execute(
            text(
                "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
                "WHERE table_name = 'agent_work_leases')"
            )
        )
        assert result.scalar() is True

    def test_ensure_schema_is_idempotent(self, db_session):
        from spine_api.services.agent_work_coordinator import SQLWorkCoordinator

        coordinator = SQLWorkCoordinator(lease_seconds=60)
        coordinator.ensure_schema()
        coordinator.ensure_schema()
        coordinator.ensure_schema()

        result = db_session.execute(
            text("SELECT COUNT(*) FROM agent_work_leases")
        )
        assert result.scalar() == 0


class TestSQLWorkCoordinatorAcquire:
    """Work lease acquisition."""

    def test_acquire_fresh_work_succeeds(self, db_session):
        from spine_api.services.agent_work_coordinator import SQLWorkCoordinator

        coordinator = SQLWorkCoordinator(lease_seconds=60)
        item = _make_item(suffix="_fresh")
        acquired, reason, attempt = coordinator.acquire(item, "owner_a", _default_retry)

        assert acquired is True
        assert reason == "acquired"
        assert attempt == 1

    def test_acquired_work_is_visible_in_db(self, db_session):
        from spine_api.services.agent_work_coordinator import SQLWorkCoordinator

        coordinator = SQLWorkCoordinator(lease_seconds=60)
        item = _make_item(trip_id="trip_visible", suffix="_dbcheck")
        coordinator.acquire(item, "owner_a", _default_retry)

        row = db_session.execute(
            text(
                "SELECT idempotency_key, status, owner, attempts "
                "FROM agent_work_leases WHERE idempotency_key = :key"
            ),
            {"key": item.idempotency_key},
        ).mappings().first()

        assert row is not None
        assert row["status"] == "running"
        assert row["owner"] == "owner_a"
        assert row["attempts"] == 1

    def test_completed_work_is_idempotent(self, db_session):
        from spine_api.services.agent_work_coordinator import SQLWorkCoordinator

        coordinator = SQLWorkCoordinator(lease_seconds=60)
        item = _make_item(suffix="_idempotent_complete")
        coordinator.acquire(item, "owner_a", _default_retry)
        coordinator.complete(item, "done")

        acquired, reason, attempt = coordinator.acquire(item, "owner_b", _default_retry)

        assert acquired is False
        assert reason == "idempotent_reentry_completed"
        assert attempt == 0

    def test_poisoned_work_is_fail_closed(self, db_session):
        from spine_api.services.agent_work_coordinator import SQLWorkCoordinator

        coordinator = SQLWorkCoordinator(lease_seconds=60)
        item = _make_item(suffix="_poisoned")
        coordinator.acquire(item, "owner_a", _default_retry)
        coordinator.fail(item, WorkStatus.POISONED, "terminal_error")

        acquired, reason, attempt = coordinator.acquire(item, "owner_b", _default_retry)

        assert acquired is False
        assert reason == "poisoned_fail_closed"
        assert attempt == 0

    def test_active_lease_blocks_other_owners(self, db_session):
        from spine_api.services.agent_work_coordinator import SQLWorkCoordinator

        coordinator = SQLWorkCoordinator(lease_seconds=600)
        item = _make_item(suffix="_active_block")
        coordinator.acquire(item, "owner_a", _default_retry)

        acquired, reason, attempt = coordinator.acquire(item, "owner_b", _default_retry)

        assert acquired is False
        assert reason.startswith("owned_by:")
        assert "owner_a" in reason

    def test_expired_lease_can_be_reacquired(self, db_session):
        from spine_api.services.agent_work_coordinator import SQLWorkCoordinator

        coordinator = SQLWorkCoordinator(lease_seconds=0)
        item = _make_item(suffix="_expired_reacquire")
        coordinator.acquire(item, "owner_a", _default_retry)

        acquired, reason, attempt = coordinator.acquire(item, "owner_b", _default_retry)

        assert acquired is True
        assert reason == "acquired"
        assert attempt == 2

    def test_retry_exhaustion_poisons_work(self, db_session):
        from spine_api.services.agent_work_coordinator import SQLWorkCoordinator

        coordinator = SQLWorkCoordinator(lease_seconds=0)
        item = _make_item(suffix="_exhaustion")
        tight_retry = RetryPolicy(max_attempts=2, backoff_seconds=(0, 0))

        first, _, _ = coordinator.acquire(item, "owner_a", tight_retry)
        assert first is True

        second, reason, attempt = coordinator.acquire(item, "owner_a", tight_retry)
        assert second is True
        assert attempt == 2

        third, reason, attempt = coordinator.acquire(item, "owner_a", tight_retry)

        assert third is False
        assert reason == "retry_policy_exhausted"
        assert attempt == 2

        row = db_session.execute(
            text(
                "SELECT status FROM agent_work_leases "
                "WHERE idempotency_key = :key"
            ),
            {"key": item.idempotency_key},
        ).mappings().first()

        assert row is not None
        assert row["status"] == "poisoned"

    def test_retry_gets_correct_attempt_count(self, db_session):
        from spine_api.services.agent_work_coordinator import SQLWorkCoordinator

        coordinator = SQLWorkCoordinator(lease_seconds=0)
        item = _make_item(suffix="_retry_count")

        _, _, a1 = coordinator.acquire(item, "owner_a", _default_retry)
        assert a1 == 1

        _, _, a2 = coordinator.acquire(item, "owner_a", _default_retry)
        assert a2 == 2

        _, _, a3 = coordinator.acquire(item, "owner_a", _default_retry)
        assert a3 == 3


class TestSQLWorkCoordinatorComplete:
    """Terminal completion."""

    def test_complete_sets_completed_status(self, db_session):
        from spine_api.services.agent_work_coordinator import SQLWorkCoordinator

        coordinator = SQLWorkCoordinator(lease_seconds=60)
        item = _make_item(suffix="_complete_status")
        coordinator.acquire(item, "owner_a", _default_retry)
        coordinator.complete(item, "all_good")

        row = db_session.execute(
            text(
                "SELECT status, last_reason FROM agent_work_leases "
                "WHERE idempotency_key = :key"
            ),
            {"key": item.idempotency_key},
        ).mappings().first()

        assert row is not None
        assert row["status"] == "completed"
        assert row["last_reason"] == "all_good"

    def test_completed_work_is_not_reacquired(self, db_session):
        from spine_api.services.agent_work_coordinator import SQLWorkCoordinator

        coordinator = SQLWorkCoordinator(lease_seconds=60)
        item = _make_item(suffix="_complete_block")
        coordinator.acquire(item, "owner_a", _default_retry)
        coordinator.complete(item, "done")

        acquired, reason, _ = coordinator.acquire(item, "owner_b", _default_retry)
        assert acquired is False
        assert reason == "idempotent_reentry_completed"

    def test_complete_after_expired_lease_still_works(self, db_session):
        from spine_api.services.agent_work_coordinator import SQLWorkCoordinator

        coordinator = SQLWorkCoordinator(lease_seconds=0)
        item = _make_item(suffix="_complete_after_expiry")
        coordinator.acquire(item, "owner_a", _default_retry)
        coordinator.complete(item, "done_after_expired")

        row = db_session.execute(
            text(
                "SELECT status FROM agent_work_leases "
                "WHERE idempotency_key = :key"
            ),
            {"key": item.idempotency_key},
        ).mappings().first()
        assert row["status"] == "completed"


class TestSQLWorkCoordinatorFail:
    """Terminal failure and poisoning."""

    def test_fail_poisoned_sets_poisoned_status(self, db_session):
        from spine_api.services.agent_work_coordinator import SQLWorkCoordinator

        coordinator = SQLWorkCoordinator(lease_seconds=60)
        item = _make_item(suffix="_fail_poisoned")
        coordinator.acquire(item, "owner_a", _default_retry)
        coordinator.fail(item, WorkStatus.POISONED, "irrecoverable")

        row = db_session.execute(
            text(
                "SELECT status, last_reason FROM agent_work_leases "
                "WHERE idempotency_key = :key"
            ),
            {"key": item.idempotency_key},
        ).mappings().first()

        assert row is not None
        assert row["status"] == "poisoned"
        assert row["last_reason"] == "irrecoverable"

    def test_fail_retry_pending_sets_retry_pending_status(self, db_session):
        from spine_api.services.agent_work_coordinator import SQLWorkCoordinator

        coordinator = SQLWorkCoordinator(lease_seconds=60)
        item = _make_item(suffix="_fail_retry")
        coordinator.acquire(item, "owner_a", _default_retry)
        coordinator.fail(item, WorkStatus.RETRY_PENDING, "transient_error")

        row = db_session.execute(
            text(
                "SELECT status FROM agent_work_leases "
                "WHERE idempotency_key = :key"
            ),
            {"key": item.idempotency_key},
        ).mappings().first()

        assert row["status"] == "retry_pending"

    def test_fail_escalated_sets_escalated_status(self, db_session):
        from spine_api.services.agent_work_coordinator import SQLWorkCoordinator

        coordinator = SQLWorkCoordinator(lease_seconds=60)
        item = _make_item(suffix="_fail_escalated")
        coordinator.acquire(item, "owner_a", _default_retry)
        coordinator.fail(item, WorkStatus.ESCALATED, "needs_human_review")

        row = db_session.execute(
            text(
                "SELECT status FROM agent_work_leases "
                "WHERE idempotency_key = :key"
            ),
            {"key": item.idempotency_key},
        ).mappings().first()

        assert row["status"] == "escalated"


class TestSQLWorkCoordinatorSnapshot:
    """Snapshot reporting."""

    def test_snapshot_backend_is_sql(self, db_session):
        from spine_api.services.agent_work_coordinator import SQLWorkCoordinator

        coordinator = SQLWorkCoordinator(lease_seconds=60)
        snap = coordinator.snapshot()

        assert snap["backend"] == "sql"

    def test_snapshot_counts_are_accurate(self, db_session):
        from spine_api.services.agent_work_coordinator import SQLWorkCoordinator

        coordinator = SQLWorkCoordinator(lease_seconds=60)
        item_a = _make_item(trip_id="snap_a", action="a", suffix="_snap1")
        item_b = _make_item(trip_id="snap_b", action="b", suffix="_snap2")
        item_c = _make_item(trip_id="snap_c", action="c", suffix="_snap3")

        coordinator.acquire(item_a, "owner_a", _default_retry)
        coordinator.complete(item_a, "done")
        coordinator.acquire(item_b, "owner_a", _default_retry)
        coordinator.fail(item_b, WorkStatus.POISONED, "bad")
        coordinator.acquire(item_c, "owner_a", _default_retry)

        snap = coordinator.snapshot()

        assert snap["backend"] == "sql"
        assert snap["completed"] >= 1
        assert snap["poisoned"] >= 1

        for key_prefix in ("snap_a", "snap_b", "snap_c"):
            matching = [
                k for k in snap["leases"]
                if k.endswith(f":{key_prefix}")
            ]

    def test_snapshot_includes_lease_details(self, db_session):
        from spine_api.services.agent_work_coordinator import SQLWorkCoordinator

        coordinator = SQLWorkCoordinator(lease_seconds=60)
        item = _make_item(suffix="_snap_detail")
        coordinator.acquire(item, "owner_x", _default_retry)

        snap = coordinator.snapshot()
        lease = snap["leases"].get(item.idempotency_key)

        assert lease is not None
        assert lease["owner"] == "owner_x"
        assert lease["status"] == "running"
        assert lease["attempts"] == 1
