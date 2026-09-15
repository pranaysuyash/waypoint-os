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


# ---------------------------------------------------------------------------
# FND-0225: backend selection is pinned by config, never by accident, and a
# configured-but-unavailable backend REFUSES the critical section (fail
# closed) instead of silently downgrading to process-local locks.
# ---------------------------------------------------------------------------

from spine_api.core.locking import (  # noqa: E402 — grouped with FND-0225 tests
    LockingBackendMisconfiguredError,
    LockingBackendUnavailableError,
    configured_locking_backend,
)
from spine_api.core.startup_assertions import (  # noqa: E402
    StartupAssertionError,
    _check_locking_backend,
)


class _FakeBind:
    def __init__(self, dialect_name: str):
        self.dialect = type("Dialect", (), {"name": dialect_name})()


class _FakeSession:
    def __init__(self, dialect_name: str):
        self.bind = _FakeBind(dialect_name)


def test_unknown_backend_value_fails_closed(monkeypatch):
    monkeypatch.setenv("SPINE_API_LOCKING_BACKEND", "sqll")  # typo
    with pytest.raises(LockingBackendMisconfiguredError):
        configured_locking_backend()


def test_backend_aliases_canonicalize(monkeypatch):
    for raw, expected in (
        ("sql", "postgres"),
        ("postgres", "postgres"),
        ("POSTGRESQL", "postgres"),
        ("memory", "memory"),
        ("", "auto"),
        ("auto", "auto"),
    ):
        monkeypatch.setenv("SPINE_API_LOCKING_BACKEND", raw)
        assert configured_locking_backend() == expected


def test_sql_pinned_backend_refuses_when_no_session(monkeypatch):
    monkeypatch.setenv("SPINE_API_LOCKING_BACKEND", "sql")

    async def _scenario():
        async with trip_advisory_lock(None, "trip_fnd0225_a"):
            pass  # pragma: no cover — must never enter the section

    with pytest.raises(LockingBackendUnavailableError):
        asyncio.run(_scenario())


def test_sql_pinned_backend_refuses_non_postgres_dialect(monkeypatch):
    monkeypatch.setenv("SPINE_API_LOCKING_BACKEND", "sql")
    db = _FakeSession("sqlite")

    async def _scenario():
        async with trip_advisory_lock(db, "trip_fnd0225_b"):
            pass  # pragma: no cover

    with pytest.raises(LockingBackendUnavailableError):
        asyncio.run(_scenario())


@pytest.mark.asyncio
async def test_memory_pin_preserves_mutual_exclusion(monkeypatch):
    monkeypatch.setenv("SPINE_API_LOCKING_BACKEND", "memory")
    order = []

    async def task(task_id: int):
        async with trip_advisory_lock(None, "trip_fnd0225_mem"):
            order.append(f"{task_id}_start")
            await asyncio.sleep(0.01)
            order.append(f"{task_id}_end")

    await asyncio.gather(task(1), task(2))
    assert order == ["1_start", "1_end", "2_start", "2_end"]


def test_auto_refuses_non_postgres_session_in_production(monkeypatch):
    monkeypatch.setenv("SPINE_API_LOCKING_BACKEND", "auto")
    monkeypatch.setenv("ENVIRONMENT", "production")
    db = _FakeSession("sqlite")

    async def _scenario():
        async with trip_advisory_lock(db, "trip_fnd0225_prod"):
            pass  # pragma: no cover

    with pytest.raises(LockingBackendUnavailableError):
        asyncio.run(_scenario())


@pytest.mark.asyncio
async def test_auto_allows_memory_fallback_in_development(monkeypatch):
    monkeypatch.setenv("SPINE_API_LOCKING_BACKEND", "auto")
    monkeypatch.setenv("ENVIRONMENT", "development")
    async with trip_advisory_lock(None, "trip_fnd0225_dev"):
        pass  # entered and exited cleanly


def test_startup_assertion_requires_pinned_backend_in_production(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.delenv("SPINE_API_LOCKING_BACKEND", raising=False)
    passed, message = _check_locking_backend()
    assert not passed

    monkeypatch.setenv("SPINE_API_LOCKING_BACKEND", "memory")
    passed, message = _check_locking_backend()
    assert not passed

    monkeypatch.setenv("SPINE_API_LOCKING_BACKEND", "postgres")
    passed, message = _check_locking_backend()
    assert passed


def test_startup_assertion_rejects_unknown_value_everywhere(monkeypatch):
    for env in ("development", "production"):
        monkeypatch.setenv("ENVIRONMENT", env)
        monkeypatch.setenv("SPINE_API_LOCKING_BACKEND", "nope")
        passed, message = _check_locking_backend()
        assert not passed
        assert "not recognized" in message


def test_startup_assertion_memory_ok_in_development(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("SPINE_API_LOCKING_BACKEND", "memory")
    passed, message = _check_locking_backend()
    assert passed


def test_startup_assertion_registered_in_boot_checks():
    from spine_api.core.startup_assertions import _ASSERTIONS

    assert any(name == "LOCKING_BACKEND" for name, _ in _ASSERTIONS)


def test_strict_boot_refuses_unpinned_locking_in_production(monkeypatch):
    from spine_api.core.startup_assertions import run_startup_assertions

    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.delenv("SPINE_API_LOCKING_BACKEND", raising=False)
    # Only the locking assertion is expected to fail here; patch the other
    # assertion inputs so a failure is attributable to LOCKING_BACKEND.
    monkeypatch.setenv("TRIPSTORE_BACKEND", "sql")
    monkeypatch.setenv("SPINE_API_IDEMPOTENCY_BACKEND", "sql")
    try:
        run_startup_assertions(strict=True)
    except StartupAssertionError as exc:
        assert "LOCKING_BACKEND" in str(exc)
    else:
        pytest.fail("expected StartupAssertionError for unpinned locking backend")
