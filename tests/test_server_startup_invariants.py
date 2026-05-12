from __future__ import annotations

import pytest

from spine_api.core.rls import RlsRuntimePosture, RlsTablePosture

import server


class _ScalarResult:
    def __init__(self, value):
        self._value = value

    def scalar(self):
        return self._value


class _FakeConn:
    def __init__(self, *, table_exists: bool = True, agency_exists: bool = True):
        self.table_exists = table_exists
        self.agency_exists = agency_exists
        self.calls = []

    async def execute(self, statement, params=None):
        sql = str(statement)
        self.calls.append((sql, params))
        if "set_config('lock_timeout'" in sql:
            return _ScalarResult(True)
        if "information_schema.tables" in sql:
            return _ScalarResult(self.table_exists)
        if "FROM agencies WHERE id" in sql:
            return _ScalarResult(self.agency_exists)
        if "ALTER TABLE agencies" in sql:
            return _ScalarResult(True)
        raise AssertionError(f"Unexpected SQL in fake: {sql}")


class _FakeBegin:
    def __init__(self, conn):
        self.conn = conn

    async def __aenter__(self):
        return self.conn

    async def __aexit__(self, exc_type, exc, tb):
        return False


class _FakeEngine:
    def __init__(self, conn):
        self.conn = conn

    def begin(self):
        return _FakeBegin(self.conn)


def _rls_posture_with_owner_bypass() -> RlsRuntimePosture:
    return RlsRuntimePosture(
        current_user="waypoint",
        is_superuser=False,
        bypasses_rls=False,
        tables=(
            RlsTablePosture(
                table_name="trips",
                owner="waypoint",
                rls_enabled=True,
                force_rls=False,
            ),
        ),
        expected_tables=("trips",),
    )


def _rls_posture_enforced() -> RlsRuntimePosture:
    return RlsRuntimePosture(
        current_user="waypoint_app",
        is_superuser=False,
        bypasses_rls=False,
        tables=(
            RlsTablePosture(
                table_name="trips",
                owner="waypoint_owner",
                rls_enabled=True,
                force_rls=False,
            ),
        ),
        expected_tables=("trips",),
    )


def test_startup_invariant_tripstore_rejects_unknown_backend(monkeypatch):
    monkeypatch.setenv("TRIPSTORE_BACKEND", "redis")
    monkeypatch.setenv("ENVIRONMENT", "development")

    with pytest.raises(RuntimeError, match="Unknown TRIPSTORE_BACKEND"):
        server._get_tripstore_backend()


def test_startup_invariant_tripstore_requires_sql_in_production(monkeypatch):
    monkeypatch.delenv("TRIPSTORE_BACKEND", raising=False)
    monkeypatch.setenv("ENVIRONMENT", "production")

    with pytest.raises(RuntimeError, match="TRIPSTORE_BACKEND must be set explicitly in production/staging"):
        server._get_tripstore_backend()


@pytest.mark.asyncio
async def test_startup_db_timeouts_are_transaction_local_and_env_configurable(monkeypatch):
    monkeypatch.setenv("SPINE_API_STARTUP_LOCK_TIMEOUT", "2s")
    monkeypatch.setenv("SPINE_API_STARTUP_STATEMENT_TIMEOUT", "9s")

    fake_conn = _FakeConn()

    await server._apply_startup_db_timeouts(fake_conn)

    timeout_call = fake_conn.calls[0]
    assert "set_config('lock_timeout'" in timeout_call[0]
    assert "set_config('statement_timeout'" in timeout_call[0]
    assert timeout_call[1] == {
        "lock_timeout": "2s",
        "statement_timeout": "9s",
    }


@pytest.mark.asyncio
async def test_agencies_schema_compatibility_applies_timeouts_before_schema_queries(monkeypatch):
    fake_conn = _FakeConn(table_exists=True)
    monkeypatch.setattr(server, "engine", _FakeEngine(fake_conn))

    await server._ensure_agencies_schema_compatibility()

    assert "set_config('lock_timeout'" in fake_conn.calls[0][0]
    assert any("ALTER TABLE agencies" in sql for sql, _ in fake_conn.calls)


@pytest.mark.asyncio
async def test_startup_invariant_file_backend_skips_sql_check(monkeypatch):
    monkeypatch.setenv("TRIPSTORE_BACKEND", "file")
    monkeypatch.setenv("PUBLIC_CHECKER_AGENCY_ID", "anything")

    class _BombEngine:
        def begin(self):
            raise AssertionError("engine.begin() should not run in file mode")

    monkeypatch.setattr(server, "engine", _BombEngine())

    await server._validate_public_checker_agency_configuration()


@pytest.mark.asyncio
async def test_startup_invariant_sql_fails_when_agencies_table_missing(monkeypatch):
    monkeypatch.setenv("TRIPSTORE_BACKEND", "sql")
    monkeypatch.setenv("PUBLIC_CHECKER_AGENCY_ID", "agency-123")

    fake_conn = _FakeConn(table_exists=False)
    monkeypatch.setattr(server, "engine", _FakeEngine(fake_conn))

    with pytest.raises(RuntimeError, match="agencies table"):
        await server._validate_public_checker_agency_configuration()


@pytest.mark.asyncio
async def test_startup_invariant_sql_fails_when_agency_missing(monkeypatch):
    monkeypatch.setenv("TRIPSTORE_BACKEND", "sql")
    monkeypatch.setenv("PUBLIC_CHECKER_AGENCY_ID", "missing-agency")

    fake_conn = _FakeConn(table_exists=True, agency_exists=False)
    monkeypatch.setattr(server, "engine", _FakeEngine(fake_conn))

    with pytest.raises(RuntimeError, match="Public checker agency invariant failed"):
        await server._validate_public_checker_agency_configuration()


@pytest.mark.asyncio
async def test_startup_invariant_sql_passes_when_agency_exists(monkeypatch):
    monkeypatch.setenv("TRIPSTORE_BACKEND", "sql")
    monkeypatch.setenv("PUBLIC_CHECKER_AGENCY_ID", "agency-123")

    fake_conn = _FakeConn(table_exists=True, agency_exists=True)
    monkeypatch.setattr(server, "engine", _FakeEngine(fake_conn))

    await server._validate_public_checker_agency_configuration()

    assert any((params or {}).get("agency_id") == "agency-123" for _, params in fake_conn.calls)


@pytest.mark.asyncio
async def test_startup_invariant_sql_wraps_unexpected_exception(monkeypatch):
    monkeypatch.setenv("TRIPSTORE_BACKEND", "sql")
    monkeypatch.setenv("PUBLIC_CHECKER_AGENCY_ID", "agency-123")

    class _ErrConn:
        async def execute(self, statement, params=None):
            raise Exception("db offline")

    monkeypatch.setattr(server, "engine", _FakeEngine(_ErrConn()))

    with pytest.raises(RuntimeError, match="Failed public checker agency validation"):
        await server._validate_public_checker_agency_configuration()


@pytest.mark.asyncio
async def test_rls_posture_invariant_file_backend_skips_sql_check(monkeypatch):
    monkeypatch.setenv("TRIPSTORE_BACKEND", "file")

    class _BombEngine:
        def begin(self):
            raise AssertionError("engine.begin() should not run in file mode")

    monkeypatch.setattr(server, "engine", _BombEngine())

    await server._validate_rls_runtime_posture_configuration()


@pytest.mark.asyncio
async def test_rls_posture_invariant_warns_in_development(monkeypatch, caplog):
    monkeypatch.setenv("TRIPSTORE_BACKEND", "sql")
    monkeypatch.setenv("ENVIRONMENT", "development")

    async def _fake_inspect(_conn):
        return _rls_posture_with_owner_bypass()

    monkeypatch.setattr(server, "engine", _FakeEngine(_FakeConn()))
    monkeypatch.setattr(server, "inspect_rls_runtime_posture", _fake_inspect)

    with caplog.at_level("WARNING"):
        await server._validate_rls_runtime_posture_configuration()

    assert "RLS runtime posture invariant failed" in caplog.text
    assert "Local/development startup will continue" in caplog.text


@pytest.mark.asyncio
async def test_rls_posture_invariant_fails_in_production(monkeypatch):
    monkeypatch.setenv("TRIPSTORE_BACKEND", "sql")
    monkeypatch.setenv("ENVIRONMENT", "production")

    async def _fake_inspect(_conn):
        return _rls_posture_with_owner_bypass()

    monkeypatch.setattr(server, "engine", _FakeEngine(_FakeConn()))
    monkeypatch.setattr(server, "inspect_rls_runtime_posture", _fake_inspect)

    with pytest.raises(RuntimeError, match="RLS runtime posture invariant failed"):
        await server._validate_rls_runtime_posture_configuration()


@pytest.mark.asyncio
async def test_rls_posture_invariant_passes_when_runtime_role_is_enforced(monkeypatch):
    monkeypatch.setenv("TRIPSTORE_BACKEND", "sql")
    monkeypatch.setenv("ENVIRONMENT", "production")

    async def _fake_inspect(_conn):
        return _rls_posture_enforced()

    monkeypatch.setattr(server, "engine", _FakeEngine(_FakeConn()))
    monkeypatch.setattr(server, "inspect_rls_runtime_posture", _fake_inspect)

    await server._validate_rls_runtime_posture_configuration()
