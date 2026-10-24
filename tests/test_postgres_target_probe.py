"""The suite availability probe must inspect the configured isolated target."""

from unittest.mock import MagicMock

import pytest

from conftest import _is_postgres_available


@pytest.mark.parametrize(("database_url", "expected_target"), [
    ("postgresql+asyncpg://waypoint@127.0.0.1:55439/isolated", ("127.0.0.1", 55439)),
    ("postgresql://waypoint@db.internal/example", ("db.internal", 5432)),
    ("postgresql+asyncpg://waypoint@[::1]:55439/isolated", ("::1", 55439)),
])
def test_postgres_probe_uses_configured_database_target(monkeypatch, database_url, expected_target):
    monkeypatch.setenv("DATABASE_URL", database_url)
    socket = MagicMock()
    socket.connect_ex.return_value = 0
    monkeypatch.setattr("socket.socket", lambda *_args: socket)
    assert _is_postgres_available() is True
    socket.connect_ex.assert_called_once_with(expected_target)
    socket.close.assert_called_once()


def test_postgres_probe_preserves_unset_url_fallback(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    socket = MagicMock()
    socket.connect_ex.return_value = 0
    monkeypatch.setattr("socket.socket", lambda *_args: socket)
    assert _is_postgres_available() is True
    socket.connect_ex.assert_called_once_with(("localhost", 5432))


def test_postgres_probe_does_not_probe_unrelated_db_on_bad_configuration(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "not a database url")
    socket = MagicMock()
    monkeypatch.setattr("socket.socket", lambda *_args: socket)
    assert _is_postgres_available() is False
    socket.connect_ex.assert_not_called()
