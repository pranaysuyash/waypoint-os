"""Focused readiness contract tests (deployment envelope, not liveness)."""

from __future__ import annotations

import pytest

from spine_api.routers import health


class _Result:
    def __init__(self, values):
        self.values = values if isinstance(values, list) else [values]

    def scalar(self):
        return self.values[0] if self.values else None

    def scalars(self):
        return self

    def all(self):
        return self.values


class _Connection:
    def __init__(self, *, migration_version="head", migration_versions=None, fail=False):
        self.migration_versions = (
            migration_versions
            if migration_versions is not None
            else ([] if migration_version is None else [migration_version])
        )
        self.fail = fail

    async def execute(self, statement):
        if self.fail:
            raise RuntimeError("database unavailable")
        if "version_num" in str(statement):
            return _Result(self.migration_versions)
        return _Result(1)


class _ConnectionContext:
    def __init__(self, connection):
        self.connection = connection

    async def __aenter__(self):
        return self.connection

    async def __aexit__(self, *_args):
        return False


class _Engine:
    def __init__(self, connection):
        self.connection = connection

    def connect(self):
        return _ConnectionContext(self.connection)


@pytest.fixture(autouse=True)
def _test_migration_head(monkeypatch):
    monkeypatch.setattr(health, "_expected_migration_heads", lambda: ("head",))


@pytest.mark.asyncio
async def test_ready_requires_database_migration_and_reports_dev_redis(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.delenv("REDIS_URL", raising=False)
    monkeypatch.setattr(health, "engine", _Engine(_Connection()))

    response = type("Response", (), {"status_code": 200})()
    payload = await health.ready(response)

    assert payload["status"] == "ready"
    assert response.status_code == 200
    assert payload["checks"] == {
        "database": "ok",
        "migrations": "ok",
        "redis": "not_configured",
    }


@pytest.mark.asyncio
async def test_ready_is_unready_when_migrations_missing(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.delenv("REDIS_URL", raising=False)
    monkeypatch.setattr(health, "engine", _Engine(_Connection(migration_version=None)))

    response = type("Response", (), {"status_code": 200})()
    payload = await health.ready(response)

    assert payload["status"] == "unready"
    assert response.status_code == 503
    assert payload["checks"]["migrations"] == "failed"


@pytest.mark.asyncio
async def test_ready_is_unready_when_production_redis_is_missing(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.delenv("REDIS_URL", raising=False)
    monkeypatch.setattr(health, "engine", _Engine(_Connection()))

    response = type("Response", (), {"status_code": 200})()
    payload = await health.ready(response)

    assert payload["status"] == "unready"
    assert response.status_code == 503
    assert payload["checks"]["redis"] == "not_configured"


@pytest.mark.asyncio
async def test_ready_is_unready_when_configured_redis_is_down(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("REDIS_URL", "redis://127.0.0.1:1/0")
    monkeypatch.setattr(health, "engine", _Engine(_Connection()))

    response = type("Response", (), {"status_code": 200})()
    payload = await health.ready(response)

    assert payload["status"] == "unready"
    assert response.status_code == 503
    assert payload["checks"]["redis"] == "failed"


@pytest.mark.asyncio
async def test_ready_does_not_leak_database_exception(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.delenv("REDIS_URL", raising=False)
    monkeypatch.setattr(health, "engine", _Engine(_Connection(fail=True)))

    response = type("Response", (), {"status_code": 200})()
    payload = await health.ready(response)

    assert payload["status"] == "unready"
    assert "database unavailable" not in str(payload)
    assert payload["checks"]["database"] == "failed"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "connection, expected_status",
    [
        (_Connection(migration_version="stale"), "unready"),
        (_Connection(migration_versions=[]), "unready"),
        (_Connection(migration_versions=["head", "other"]), "unready"),
    ],
)
async def test_ready_requires_exactly_one_current_migration_head(
    monkeypatch, connection, expected_status
):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.delenv("REDIS_URL", raising=False)
    monkeypatch.setattr(health, "engine", _Engine(connection))

    response = type("Response", (), {"status_code": 200})()
    payload = await health.ready(response)

    assert payload["status"] == expected_status
    assert response.status_code == 503
    assert payload["checks"]["migrations"] == "failed"


@pytest.mark.asyncio
async def test_ready_fails_closed_when_migration_graph_cannot_resolve(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.delenv("REDIS_URL", raising=False)
    monkeypatch.setattr(health, "_expected_migration_heads", lambda: (_ for _ in ()).throw(RuntimeError("bad graph")))
    monkeypatch.setattr(health, "engine", _Engine(_Connection()))

    response = type("Response", (), {"status_code": 200})()
    payload = await health.ready(response)

    assert payload["status"] == "unready"
    assert response.status_code == 503
    assert payload["checks"]["migrations"] == "failed"
    assert "bad graph" not in str(payload)
