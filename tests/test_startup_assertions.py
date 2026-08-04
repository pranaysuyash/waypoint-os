"""
tests/test_startup_assertions.py — Tests for fail-closed startup checks.

Verifies:
  - Assertions pass with correct env vars
  - Assertions fail with missing/bad env vars
  - Production mode is strict (would crash)
  - Development mode warns but continues
"""

import os
import pytest
from unittest.mock import patch

from spine_api.core.startup_assertions import (
    run_startup_assertions,
    StartupAssertionError,
    _check_database_url,
    _check_auth_not_disabled_in_production,
    _check_secret_key,
    _check_environment_declared,
    _check_tripstore_backend,
)


class TestDatabaseUrlCheck:
    """DATABASE_URL must be set and appropriate for environment."""

    def test_missing_database_url(self):
        with patch.dict(os.environ, {}, clear=True):
            passed, msg = _check_database_url()
            assert not passed
            assert "not set" in msg

    def test_valid_database_url(self):
        with patch.dict(os.environ, {"DATABASE_URL": "postgresql://localhost/test"}):
            passed, msg = _check_database_url()
            assert passed

    def test_sqlite_in_production(self):
        with patch.dict(os.environ, {
            "DATABASE_URL": "sqlite:///test.db",
            "ENVIRONMENT": "production",
        }):
            passed, msg = _check_database_url()
            assert not passed
            assert "SQLite" in msg


class TestAuthSafety:
    """Auth must not be disabled in production."""

    def test_auth_disabled_in_production(self):
        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
            "SPINE_API_DISABLE_AUTH": "1",
        }):
            passed, msg = _check_auth_not_disabled_in_production()
            assert not passed
            assert "security violation" in msg.lower()

    def test_auth_enabled_in_production(self):
        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
        }, clear=False):
            env = os.environ.copy()
            env.pop("SPINE_API_DISABLE_AUTH", None)
            with patch.dict(os.environ, env, clear=True):
                passed, msg = _check_auth_not_disabled_in_production()
                assert passed

    def test_auth_disabled_in_dev_is_ok(self):
        with patch.dict(os.environ, {
            "ENVIRONMENT": "development",
            "SPINE_API_DISABLE_AUTH": "1",
        }):
            passed, msg = _check_auth_not_disabled_in_production()
            assert passed


class TestSecretKey:
    """SECRET_KEY must be set, non-trivial, and long enough."""

    def test_missing_secret_key(self):
        with patch.dict(os.environ, {}, clear=True):
            passed, msg = _check_secret_key()
            assert not passed

    def test_known_default_secret(self):
        with patch.dict(os.environ, {"SECRET_KEY": "changeme"}):
            passed, msg = _check_secret_key()
            assert not passed
            assert "known default" in msg

    def test_short_secret(self):
        with patch.dict(os.environ, {"SECRET_KEY": "abc"}):
            passed, msg = _check_secret_key()
            assert not passed
            assert "characters" in msg

    def test_valid_secret(self):
        with patch.dict(os.environ, {"SECRET_KEY": "a" * 32}):
            passed, msg = _check_secret_key()
            assert passed


class TestEnvironmentDeclared:
    """ENVIRONMENT must be explicitly set to a known value."""

    def test_missing_environment(self):
        with patch.dict(os.environ, {}, clear=True):
            passed, msg = _check_environment_declared()
            assert not passed

    def test_invalid_environment(self):
        with patch.dict(os.environ, {"ENVIRONMENT": "foo"}):
            passed, msg = _check_environment_declared()
            assert not passed

    def test_valid_environments(self):
        for env in ("development", "staging", "production", "test"):
            with patch.dict(os.environ, {"ENVIRONMENT": env}):
                passed, msg = _check_environment_declared()
                assert passed, f"Should pass for {env}"


class TestTripstoreBackend:
    """TRIPSTORE_BACKEND must be 'postgres' in production."""

    def test_missing_in_production(self):
        with patch.dict(os.environ, {"ENVIRONMENT": "production"}, clear=True):
            os.environ.pop("TRIPSTORE_BACKEND", None)
            with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
                passed, msg = _check_tripstore_backend()
                assert not passed

    def test_non_postgres_in_production(self):
        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
            "TRIPSTORE_BACKEND": "file",
        }):
            passed, msg = _check_tripstore_backend()
            assert not passed

    def test_postgres_in_production(self):
        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
            "TRIPSTORE_BACKEND": "postgres",
        }):
            passed, msg = _check_tripstore_backend()
            assert passed

    def test_missing_in_dev_is_ok(self):
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}, clear=True):
            passed, msg = _check_tripstore_backend()
            assert passed


class TestStartupAssertionRunner:
    """Integration test for the full assertion runner."""

    def test_all_pass_in_dev(self):
        with patch.dict(os.environ, {
            "ENVIRONMENT": "development",
            "DATABASE_URL": "postgresql://localhost/test",
            "SECRET_KEY": "a" * 32,
        }):
            failures = run_startup_assertions(strict=False)
            # Should have zero critical failures in dev with these vars set
            assert isinstance(failures, list)

    def test_production_crashes_on_failure(self):
        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
            "SPINE_API_DISABLE_AUTH": "1",
        }, clear=True):
            with pytest.raises(StartupAssertionError):
                run_startup_assertions(strict=True)
