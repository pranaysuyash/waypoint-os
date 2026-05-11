import pytest

import server


class _ScalarResult:
    def __init__(self, value):
        self._value = value

    def scalar(self):
        return self._value


class _FakeConn:
    def __init__(self, table_exists: bool, agency_exists: bool):
        self.table_exists = table_exists
        self.agency_exists = agency_exists
        self.calls = []

    async def execute(self, statement, params=None):
        sql = str(statement)
        self.calls.append((sql, params))
        if "set_config(" in sql:
            return _ScalarResult(True)
        if "information_schema.tables" in sql:
            return _ScalarResult(self.table_exists)
        if "FROM agencies WHERE id" in sql:
            return _ScalarResult(self.agency_exists)
        raise AssertionError(f"Unexpected SQL in test fake: {sql}")


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


@pytest.mark.asyncio
async def test_validate_public_checker_agency_configuration_passes_when_agency_exists(monkeypatch):
    monkeypatch.setenv("TRIPSTORE_BACKEND", "sql")
    monkeypatch.setenv("PUBLIC_CHECKER_AGENCY_ID", "agency-123")

    fake_conn = _FakeConn(table_exists=True, agency_exists=True)
    monkeypatch.setattr(server, "engine", _FakeEngine(fake_conn))

    await server._validate_public_checker_agency_configuration()

    assert any("information_schema.tables" in sql for sql, _ in fake_conn.calls)
    assert any(
        "set_config(" in sql
        and (params or {}).get("lock_timeout") == "5s"
        and (params or {}).get("statement_timeout") == "20s"
        for sql, params in fake_conn.calls
    )
    assert any((params or {}).get("agency_id") == "agency-123" for _, params in fake_conn.calls)


@pytest.mark.asyncio
async def test_validate_public_checker_agency_configuration_raises_when_agency_missing(monkeypatch):
    monkeypatch.setenv("TRIPSTORE_BACKEND", "sql")
    monkeypatch.setenv("PUBLIC_CHECKER_AGENCY_ID", "missing-agency")

    fake_conn = _FakeConn(table_exists=True, agency_exists=False)
    monkeypatch.setattr(server, "engine", _FakeEngine(fake_conn))

    with pytest.raises(RuntimeError, match="Public checker agency invariant failed"):
        await server._validate_public_checker_agency_configuration()


@pytest.mark.asyncio
async def test_validate_public_checker_agency_configuration_skips_when_not_sql(monkeypatch):
    monkeypatch.setenv("TRIPSTORE_BACKEND", "file")
    monkeypatch.setenv("PUBLIC_CHECKER_AGENCY_ID", "anything")

    class _BombEngine:
        def begin(self):
            raise AssertionError("engine.begin() should not be called when backend is file")

    monkeypatch.setattr(server, "engine", _BombEngine())

    await server._validate_public_checker_agency_configuration()


def test_get_public_checker_agency_id_uses_default_and_strips(monkeypatch):
    monkeypatch.delenv("PUBLIC_CHECKER_AGENCY_ID", raising=False)
    assert server._get_public_checker_agency_id() == "d1e3b2b6-5509-4c27-b123-4b1e02b0bf5b"

    monkeypatch.setenv("PUBLIC_CHECKER_AGENCY_ID", "  custom-agency  ")
    assert server._get_public_checker_agency_id() == "custom-agency"
