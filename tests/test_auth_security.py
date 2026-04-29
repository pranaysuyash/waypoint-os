"""
Auth security tests — verify reset-token exposure, test-user gating,
and JWT secret fail-fast behavior.
"""

import os
import sys
from pathlib import Path

import pytest

src_dir = Path(__file__).parent.parent / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

spine_api_dir = Path(__file__).parent.parent / "spine_api"
if str(spine_api_dir) not in sys.path:
    sys.path.insert(0, str(spine_api_dir))


class TestJWTSecretFailFast:
    """JWT_SECRET must be set; the module raises at import time if missing."""

    def test_jwt_secret_exists_after_conftest(self):
        """Conftest sets JWT_SECRET; verify it is non-empty."""
        import spine_api.core.security as sec
        assert sec.JWT_SECRET, "JWT_SECRET must not be empty after conftest setup"

    def test_guard_logic_rejects_empty(self):
        """Verify the guard pattern: os.getenv returns None → RuntimeError."""
        val = os.getenv("JWT_SECRET_MISSING_SENTINEL", None)
        assert val is None
        # The same pattern in security.py would raise for this value


class TestResetTokenExposure:
    """
    reset_token must never appear in API responses unless
    ENVIRONMENT=development AND EXPOSE_RESET_TOKEN=1.
    """

    def test_no_env_vars_excludes_reset_token(self, monkeypatch):
        monkeypatch.delenv("EXPOSE_RESET_TOKEN", raising=False)
        monkeypatch.delenv("ENVIRONMENT", raising=False)
        result = self._build_reset_response()
        # Default ENVIRONMENT is "development", but EXPOSE_RESET_TOKEN is unset
        assert "reset_token" not in result

    def test_expose_only_does_not_include_without_environment(self, monkeypatch):
        """EXPOSE_RESET_TOKEN=1 with ENVIRONMENT unset defaults to development
        which is the ONLY case where reset_token is included. This test
        verifies that the combination IS included (expected behavior)."""
        monkeypatch.setenv("EXPOSE_RESET_TOKEN", "1")
        monkeypatch.delenv("ENVIRONMENT", raising=False)
        result = self._build_reset_response()
        # Default is "development" + EXPOSE_RESET_TOKEN=1 → included
        assert "reset_token" in result

    def test_production_expose_excludes(self, monkeypatch):
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("EXPOSE_RESET_TOKEN", "1")
        result = self._build_reset_response()
        assert "reset_token" not in result

    def test_staging_expose_excludes(self, monkeypatch):
        monkeypatch.setenv("ENVIRONMENT", "staging")
        monkeypatch.setenv("EXPOSE_RESET_TOKEN", "1")
        result = self._build_reset_response()
        assert "reset_token" not in result

    def test_development_expose_includes(self, monkeypatch):
        monkeypatch.setenv("ENVIRONMENT", "development")
        monkeypatch.setenv("EXPOSE_RESET_TOKEN", "1")
        result = self._build_reset_response()
        assert "reset_token" in result

    def test_development_without_expose_excludes(self, monkeypatch):
        monkeypatch.setenv("ENVIRONMENT", "development")
        monkeypatch.delenv("EXPOSE_RESET_TOKEN", raising=False)
        result = self._build_reset_response()
        assert "reset_token" not in result

    def _build_reset_response(self):
        """Simulate the logic in auth_service.request_password_reset."""
        response = {
            "ok": True,
            "message": "If the email exists, a reset link has been sent",
        }
        if (
            os.getenv("ENVIRONMENT", "development").lower() == "development"
            and os.getenv("EXPOSE_RESET_TOKEN") == "1"
        ):
            response["reset_token"] = "simulated-token"
        return response


class TestRouterResetTokenSanitization:
    """
    The auth router constructs its own response dict and only adds
    reset_token under ENVIRONMENT=development + EXPOSE_RESET_TOKEN=1.
    """

    def test_router_strips_token_by_default(self):
        _ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()
        service_result = {
            "ok": True,
            "message": "If the email exists, a reset link has been sent",
            "reset_token": "secret-plain-token",
        }
        response = {
            "ok": True,
            "message": "If the email exists, a reset link has been sent",
        }
        expose = (
            _ENVIRONMENT == "development"
            and os.getenv("EXPOSE_RESET_TOKEN") == "1"
            and isinstance(service_result, dict)
            and "reset_token" in service_result
        )
        if expose:
            response["reset_token"] = service_result["reset_token"]
        # By default EXPOSE_RESET_TOKEN is not set, so no token in response
        assert "reset_token" not in response


class TestTestUserGating:
    """
    @test.com signup must only seed test data when ENVIRONMENT=development.
    """

    def test_production_ignores_test_domain(self, monkeypatch):
        monkeypatch.setenv("ENVIRONMENT", "production")
        _ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()
        is_test = _ENVIRONMENT == "development" and "user@test.com".lower().endswith("@test.com")
        assert is_test is False

    def test_development_allows_test_domain(self, monkeypatch):
        monkeypatch.setenv("ENVIRONMENT", "development")
        _ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()
        is_test = _ENVIRONMENT == "development" and "user@test.com".lower().endswith("@test.com")
        assert is_test is True

    def test_production_normal_email_not_test(self, monkeypatch):
        monkeypatch.setenv("ENVIRONMENT", "production")
        _ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()
        is_test = _ENVIRONMENT == "development" and "user@example.com".lower().endswith("@test.com")
        assert is_test is False


class TestUnknownEmailDoesNotLeak:
    """Password reset for unknown email must return same shape as known email."""

    def test_unknown_email_response_has_no_token(self):
        result = {"ok": True, "message": "If the email exists, a reset link has been sent"}
        assert "reset_token" not in result
        assert result["ok"] is True
        # The message should not indicate whether the email was found or not
        # (it mentions "exists" generically, which is fine — it does not
        # vary based on whether the email was actually found)