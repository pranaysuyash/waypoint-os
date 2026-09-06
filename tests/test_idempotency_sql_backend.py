"""
Tests for the durable SQL idempotency backend (PT-08,
Docs/review/SPINE_AUDIT_NEW_FINDINGS_2026-09-02.md).

Coverage honesty:
- Pure parts (no database): row→record mapping, UTC normalization, backend
  selection from ``SPINE_API_IDEMPOTENCY_BACKEND``, key stability, and the
  public-API invariance of ``IdempotencyRegistry``.
- Durable acquire/mark/replay semantics: exercised against an **in-memory
  SQLite (aiosqlite) engine with StaticPool** — the live Postgres test
  database is never written (repo rule: tests must not create rows there).
  SQLite validates the SQLAlchemy control flow (PK-conflict replay, TTL
  reclaim, FAILED retry). The Postgres-specific seam (JSONB column variant
  and true cross-process INSERT races) is covered by the alembic migration
  ``alembic/versions/add_idempotency_keys_table.py`` plus the lazy
  ``create_all`` path, and stays a live-DB integration seam by design.
- Fencing regression: an old owner cannot complete a row after TTL reclaim;
  only the reclaimed owner's token can perform the terminal CAS.
"""

import os
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

os.environ["RUNNING_TESTS"] = "1"

from src.agents.idempotency import (
    IDEMPOTENCY_BACKEND_ENV,
    IdempotencyRegistry,
    IdempotencyStatus,
    SqlIdempotencyBackend,
)


# ---------------------------------------------------------------------------
# Pure parts — no database required
# ---------------------------------------------------------------------------


def test_as_utc_normalizes_naive_and_keeps_aware():
    naive = datetime(2026, 9, 2, 12, 0, 0)
    assert SqlIdempotencyBackend._as_utc(naive).tzinfo == timezone.utc

    aware = datetime(2026, 9, 2, 12, 0, 0, tzinfo=timezone.utc)
    assert SqlIdempotencyBackend._as_utc(aware) is aware


def test_record_from_row_maps_all_fields():
    row = SimpleNamespace(
        status="COMPLETED",
        created_at=datetime(2026, 9, 2, 10, 0, 0, tzinfo=timezone.utc),
        completed_at=datetime(2026, 9, 2, 10, 5, 0, tzinfo=timezone.utc),
        response_payload={"trip_id": "t1"},
        error_message=None,
        ttl_seconds=3600,
    )
    record = SqlIdempotencyBackend._record_from_row(
        key="k1", trip_id="t1", action_name="act", request_hash="h", row=row
    )
    assert record.key == "k1"
    assert record.status is IdempotencyStatus.COMPLETED
    assert record.response_payload == {"trip_id": "t1"}
    assert record.error_message is None
    assert record.ttl_seconds == 3600
    assert record.created_at == row.created_at.timestamp()
    assert record.completed_at == row.completed_at.timestamp()

    row.completed_at = None
    record2 = SqlIdempotencyBackend._record_from_row(
        key="k1", trip_id="t1", action_name="act", request_hash="h", row=row
    )
    assert record2.completed_at is None


def test_generate_key_is_deterministic_and_payload_sensitive():
    a = IdempotencyRegistry.generate_key("t1", "act", {"x": 1})
    b = IdempotencyRegistry.generate_key("t1", "act", {"x": 1})
    c = IdempotencyRegistry.generate_key("t1", "act", {"x": 2})
    d = IdempotencyRegistry.generate_key("t2", "act", {"x": 1})
    assert a == b
    assert a != c
    assert a != d
    assert a.startswith("idem:t1:act:")


@pytest.fixture()
def registry_singleton_guard():
    """Snapshot and restore the process-wide registry singleton around env tests.

    ``spine_api/routers/inbound.py`` resolves its registry at import time; the
    app must keep operating on the instance it captured, so tests put the
    original singleton back instead of leaving a backend resolved from test
    env vars.
    """
    original = IdempotencyRegistry._instance
    yield
    IdempotencyRegistry._instance = original


def _resolve_with(monkeypatch, backend_env, database_url="x"):
    if backend_env is None:
        monkeypatch.delenv(IDEMPOTENCY_BACKEND_ENV, raising=False)
    else:
        monkeypatch.setenv(IDEMPOTENCY_BACKEND_ENV, backend_env)
    if database_url is None:
        monkeypatch.delenv("DATABASE_URL", raising=False)
    else:
        monkeypatch.setenv("DATABASE_URL", database_url)
    # Clear the cached singleton so each resolution actually re-reads the env
    # (get_instance() short-circuits on the previous call's instance).
    IdempotencyRegistry._instance = None
    return IdempotencyRegistry.get_instance()


def test_backend_selection_memory_default(monkeypatch, registry_singleton_guard):
    assert _resolve_with(monkeypatch, None)._backend is None
    assert _resolve_with(monkeypatch, "memory")._backend is None
    assert _resolve_with(monkeypatch, "MEMORY")._backend is None


def test_backend_selection_sql_and_auto(monkeypatch, registry_singleton_guard):
    assert isinstance(_resolve_with(monkeypatch, "sql")._backend, SqlIdempotencyBackend)
    assert isinstance(_resolve_with(monkeypatch, "auto")._backend, SqlIdempotencyBackend)
    # auto without a database falls back to the in-memory backend.
    assert _resolve_with(monkeypatch, "auto", database_url=None)._backend is None


def test_backend_selection_is_cached_singleton(monkeypatch, registry_singleton_guard):
    monkeypatch.setenv(IDEMPOTENCY_BACKEND_ENV, "memory")
    first = IdempotencyRegistry.get_instance()
    second = IdempotencyRegistry.get_instance()
    assert first is second


# ---------------------------------------------------------------------------
# Durable semantics on an isolated in-memory SQLite engine (never live Postgres)
# ---------------------------------------------------------------------------


@pytest.fixture()
def sqlite_sql_backend():
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from sqlalchemy.pool import StaticPool

    engine = create_async_engine(
        "sqlite+aiosqlite://",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
        future=True,
    )
    backend = SqlIdempotencyBackend(
        engine=engine, session_maker=async_sessionmaker(engine, expire_on_commit=False)
    )
    yield backend
    # StaticPool owns one connection; dispose closes it cleanly.
    backend._run(_dispose(engine))


async def _dispose(engine):
    await engine.dispose()


def test_sql_backend_acquire_mark_replay(sqlite_sql_backend):
    backend = sqlite_sql_backend
    key = "idem:t1:act:abc"

    acquired, record = backend.try_acquire(key, trip_id="t1", action_name="act", payload={"x": 1})
    assert acquired is True
    assert record.status is IdempotencyStatus.PENDING

    # Second worker (same table) must see the in-flight reservation.
    acquired2, record2 = backend.try_acquire(key, trip_id="t1", action_name="act", payload={"x": 1})
    assert acquired2 is False
    assert record2.status is IdempotencyStatus.PENDING

    assert backend.mark_completed(
        key,
        {"trip_id": "t1", "replayed": True},
        fencing_token=record.fencing_token,
    ) is True
    acquired3, record3 = backend.try_acquire(key, trip_id="t1", action_name="act", payload={"x": 1})
    assert acquired3 is False
    assert record3.status is IdempotencyStatus.COMPLETED
    assert record3.response_payload == {"trip_id": "t1", "replayed": True}


def test_sql_backend_failed_allows_retry(sqlite_sql_backend):
    backend = sqlite_sql_backend
    key = "idem:t9:act:fail"

    acquired_first, first_record = backend.try_acquire(
        key, trip_id="t9", action_name="act", payload={}
    )
    assert acquired_first is True
    assert first_record is not None
    assert backend.mark_failed(key, "boom", fencing_token=first_record.fencing_token) is True
    acquired, record = backend.try_acquire(key, trip_id="t9", action_name="act", payload={})
    assert acquired is True
    assert record.status is IdempotencyStatus.PENDING


def test_sql_backend_ttl_expiry_reclaims_key(sqlite_sql_backend):
    backend = sqlite_sql_backend
    key = "idem:t-exp:act:ttl"
    assert backend.try_acquire(key, trip_id="t-exp", action_name="act", payload={}, ttl_seconds=3600)[0] is True

    # Age the row past its TTL directly, then reclaim through the public API.
    stale = datetime.now(timezone.utc) - timedelta(seconds=7200)

    async def _age_row():
        from sqlalchemy import update

        from spine_api.models.idempotency import IdempotencyKey

        async with backend._get_session_maker()() as session:
            await session.execute(
                update(IdempotencyKey)
                .where(IdempotencyKey.key == key)
                .values(created_at=stale)
            )
            await session.commit()

    backend._run(_age_row())

    acquired, record = backend.try_acquire(key, trip_id="t-exp", action_name="act", payload={}, ttl_seconds=3600)
    assert acquired is True
    assert record.status is IdempotencyStatus.PENDING


def test_sql_backend_mark_completed_unknown_key_is_noop(sqlite_sql_backend):
    assert sqlite_sql_backend.mark_completed(
        "idem:never:acquired:x", {"ok": True}
    ) is False


def test_sql_backend_stale_owner_cannot_complete_reclaimed_row(sqlite_sql_backend):
    """The old owner and reclaimed owner are both PENDING; status-only guards
    therefore do not fence the stale write. The generation token must."""
    backend = sqlite_sql_backend
    key = "idem:t-fence:act:ttl"

    acquired_old, old_record = backend.try_acquire(
        key, trip_id="t-old", action_name="act", payload={}, ttl_seconds=3600
    )
    assert acquired_old is True
    assert old_record is not None

    stale = datetime.now(timezone.utc) - timedelta(seconds=7200)

    async def _age_row():
        from sqlalchemy import update

        from spine_api.models.idempotency import IdempotencyKey

        async with backend._get_session_maker()() as session:
            await session.execute(
                update(IdempotencyKey)
                .where(IdempotencyKey.key == key)
                .values(created_at=stale)
            )
            await session.commit()

    backend._run(_age_row())

    acquired_new, new_record = backend.try_acquire(
        key, trip_id="t-new", action_name="act", payload={}, ttl_seconds=3600
    )
    assert acquired_new is True
    assert new_record is not None
    assert new_record.fencing_token != old_record.fencing_token

    # The stale owner must not close the reclaimed owner's still-pending row.
    assert backend.mark_completed(
        key, {"owner": "old"}, fencing_token=old_record.fencing_token
    ) is False
    acquired_check, pending = backend.try_acquire(
        key, trip_id="t-new", action_name="act", payload={}, ttl_seconds=3600
    )
    assert acquired_check is False
    assert pending is not None
    assert pending.status is IdempotencyStatus.PENDING
    assert pending.response_payload is None

    assert backend.mark_completed(
        key, {"owner": "new"}, fencing_token=new_record.fencing_token
    ) is True
    _, completed = backend.try_acquire(
        key, trip_id="t-new", action_name="act", payload={}, ttl_seconds=3600
    )
    assert completed is not None
    assert completed.status is IdempotencyStatus.COMPLETED
    assert completed.response_payload == {"owner": "new"}


def test_sql_backend_durable_across_instances(sqlite_sql_backend):
    """A second backend over the same store sees the first one's reservation —
    the property the in-process registry cannot provide across workers."""
    backend_a = sqlite_sql_backend
    key = "idem:t-durable:act:x"
    assert backend_a.try_acquire(key, trip_id="t-durable", action_name="act", payload={})[0] is True

    from sqlalchemy.ext.asyncio import async_sessionmaker

    backend_b = SqlIdempotencyBackend(
        engine=backend_a._engine,
        session_maker=async_sessionmaker(backend_a._engine, expire_on_commit=False),
    )
    acquired, record = backend_b.try_acquire(key, trip_id="t-durable", action_name="act", payload={})
    assert acquired is False
    assert record.status is IdempotencyStatus.PENDING


def test_registry_direct_construction_stays_in_memory():
    """Public-API invariance: constructing IdempotencyRegistry() directly
    (tests, in-process callers) always uses the in-memory backend."""
    registry = IdempotencyRegistry()
    assert registry._backend is None
    key = IdempotencyRegistry.generate_key("t", "act", {"a": 1})
    assert registry.try_acquire(key, trip_id="t", action_name="act", payload={"a": 1})[0] is True
    acquired_first, first_record = registry.try_acquire(
        key, trip_id="t", action_name="act", payload={"a": 1}
    )
    assert acquired_first is False
    assert first_record is not None
    assert registry.mark_completed(
        key, {"done": True}, fencing_token=first_record.fencing_token
    ) is True
    acquired, record = registry.try_acquire(key, trip_id="t", action_name="act", payload={"a": 1})
    assert acquired is False
    assert record.response_payload == {"done": True}
