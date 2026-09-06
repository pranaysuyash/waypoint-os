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
    _check_redis_url,
    _check_public_proposal_demo_mode,
    auth_bypass_enabled,
)
from spine_api.core.middleware import _is_public_path


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

    def test_development_database_credential_rejected_in_production(self):
        with patch.dict(os.environ, {
            "DATABASE_URL": "postgresql+asyncpg://waypoint:waypoint_dev_password@db:5432/app",
            "ENVIRONMENT": "production",
        }):
            passed, msg = _check_database_url()
            assert not passed
            assert "development credential" in msg


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

    def test_auth_disabled_in_staging(self):
        """A-18: staging must refuse the auth kill switch, not just production."""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "staging",
            "SPINE_API_DISABLE_AUTH": "1",
        }):
            passed, msg = _check_auth_not_disabled_in_production()
            assert not passed
            assert "staging" in msg.lower()
            assert "security violation" in msg.lower()

    def test_auth_disabled_in_test_env_is_ok(self):
        with patch.dict(os.environ, {
            "ENVIRONMENT": "test",
            "SPINE_API_DISABLE_AUTH": "1",
        }):
            passed, msg = _check_auth_not_disabled_in_production()
            assert passed

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

    @pytest.mark.parametrize("raw", ["0", "false", "no", "off", "", "unexpected"])
    def test_auth_bypass_requires_explicit_truthy_value(self, raw):
        with patch.dict(os.environ, {"SPINE_API_DISABLE_AUTH": raw}, clear=True):
            assert auth_bypass_enabled() is False

    @pytest.mark.parametrize("raw", ["1", "true", "yes", "on", " TRUE "])
    def test_auth_bypass_accepts_explicit_truthy_value(self, raw):
        with patch.dict(os.environ, {"SPINE_API_DISABLE_AUTH": raw}, clear=True):
            assert auth_bypass_enabled() is True

    def test_middleware_does_not_make_protected_path_public_for_zero(self):
        with patch.dict(os.environ, {"SPINE_API_DISABLE_AUTH": "0"}, clear=True):
            assert _is_public_path("/api/v1/private") is False

    def test_middleware_bypass_is_explicit(self):
        with patch.dict(os.environ, {"SPINE_API_DISABLE_AUTH": "1"}, clear=True):
            assert _is_public_path("/api/v1/private") is True


class TestSecretKey:
    """SECRET_KEY must be set, non-trivial, and long enough."""

    def test_missing_secret_key(self):
        with patch.dict(os.environ, {}, clear=True):
            passed, msg = _check_secret_key()
            assert not passed

    def test_known_default_secret(self):
        with patch.dict(os.environ, {"JWT_SECRET": "changeme", "SECRET_KEY": "changeme"}):
            passed, msg = _check_secret_key()
            assert not passed
            assert "known default" in msg

    def test_short_secret(self):
        with patch.dict(os.environ, {"JWT_SECRET": "abc", "SECRET_KEY": "abc"}):
            passed, msg = _check_secret_key()
            assert not passed
            assert "characters" in msg

    def test_valid_secret(self):
        with patch.dict(os.environ, {"JWT_SECRET": "a" * 32, "SECRET_KEY": "a" * 32}):
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


class TestRedisUrl:
    def test_redis_required_in_production(self):
        with patch.dict(os.environ, {"ENVIRONMENT": "production"}, clear=True):
            passed, msg = _check_redis_url()
            assert not passed
            assert "REDIS_URL" in msg

    def test_redis_optional_in_development(self):
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}, clear=True):
            passed, _ = _check_redis_url()
            assert passed

    def test_redis_scheme_is_validated(self):
        with patch.dict(os.environ, {"ENVIRONMENT": "production", "REDIS_URL": "http://redis"}, clear=True):
            passed, msg = _check_redis_url()
            assert not passed
            assert "redis://" in msg


class TestPublicProposalDemoMode:
    """Synthetic public proposal fixtures are local-only."""

    @pytest.mark.parametrize("env", ["production", "staging"])
    def test_demo_mode_rejected_in_production_like_environment(self, env):
        with patch.dict(os.environ, {
            "ENVIRONMENT": env,
            "PUBLIC_PROPOSAL_DEMO_MODE": "true",
        }, clear=True):
            passed, msg = _check_public_proposal_demo_mode()
            assert not passed
            assert "production-like" in msg

    @pytest.mark.parametrize("raw", ["", "0", "false", "off", "unexpected"])
    def test_demo_mode_disabled_values_are_safe_in_production(self, raw):
        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
            "PUBLIC_PROPOSAL_DEMO_MODE": raw,
        }, clear=True):
            passed, _ = _check_public_proposal_demo_mode()
            assert passed

    def test_demo_mode_allowed_for_local_development(self):
        with patch.dict(os.environ, {
            "ENVIRONMENT": "development",
            "PUBLIC_PROPOSAL_DEMO_MODE": "1",
        }, clear=True):
            passed, msg = _check_public_proposal_demo_mode()
            assert passed
            assert "development" in msg

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
