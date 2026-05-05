"""
tests/test_rate_limiter — Behavioral tests for rate limiting on auth endpoints.

Strategy:
- Test slowapi limiter's internal registry to verify rate limits are REGISTERED
  (not function attributes — slowapi uses __marked_for_limiting / _route_limits)
- Test the 429 handler via synchronous Starlette TestClient (no pytest-asyncio needed)
- Test Pydantic models still validate (router preserves FastAPI body validation)
- Test environment-aware defaults
- Test middleware registration on the app

This tests BEHAVIOR, not implementation internals that slowapi doesn't expose.
"""

import os
import importlib

import pytest
from fastapi.testclient import TestClient
from slowapi.errors import RateLimitExceeded
from limits import parse as parse_limit
from slowapi.wrappers import Limit

from spine_api.core.rate_limiter import RateLimitExceededHandler


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_limiter():
    from spine_api.core.rate_limiter import limiter
    return limiter


def _get_app():
    from spine_api.server import app
    return app


# ---------------------------------------------------------------------------
# Rate limiter configuration
# ---------------------------------------------------------------------------

class TestRateLimiterConfiguration:
    def test_dev_mode_has_generous_default_limits(self):
        import spine_api.core.rate_limiter as mod
        limits = mod._get_default_limits()
        assert limits == ["1000/minute"]

    def test_prod_mode_has_conservative_default_limits(self):
        import spine_api.core.rate_limiter as mod
        # _get_default_limits checks os.environ at call time
        original = os.environ.get("ENVIRONMENT")
        os.environ["ENVIRONMENT"] = "production"
        try:
            limits = mod._get_default_limits()
            assert limits == ["60/minute"]
        finally:
            if original is None:
                os.environ.pop("ENVIRONMENT", None)
            else:
                os.environ["ENVIRONMENT"] = original

    def test_test_mode_has_generous_default_limits(self):
        import spine_api.core.rate_limiter as mod
        original = os.environ.get("ENVIRONMENT")
        os.environ["ENVIRONMENT"] = "test"
        try:
            limits = mod._get_default_limits()
            assert limits == ["1000/minute"]
        finally:
            if original is None:
                os.environ.pop("ENVIRONMENT", None)
            else:
                os.environ["ENVIRONMENT"] = original

    def test_limiter_is_enabled(self):
        limiter = _get_limiter()
        assert limiter.enabled is True

    def test_limiter_has_headers_enabled(self):
        limiter = _get_limiter()
        assert limiter._headers_enabled is True

    def test_key_func_uses_remote_address(self):
        from starlette.requests import Request
        from spine_api.core.rate_limiter import _key_func
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/health",
            "headers": [],
            "query_string": b"",
            "server": ("testclient", 80),
            "client": ("192.168.1.100", 54321),
        }
        request = Request(scope)
        key = _key_func(request)
        assert key == "192.168.1.100"


# ---------------------------------------------------------------------------
# 429 handler — tested synchronously via Starlette TestClient
# ---------------------------------------------------------------------------

class TestRateLimitExceededHandler:
    def test_handler_returns_429_json(self):
        """
        Test the 429 handler by constructing a real RateLimitExceeded,
        calling the handler synchronously via Starlette's TestClient,
        and verifying the structured JSON response.
        """
        limit_item = parse_limit("5/minute")
        limit = Limit(
            limit=limit_item,
            key_func=lambda: "test",
            scope="test",
            per_method=False,
            methods=None,
            error_message=None,
            exempt_when=None,
            cost=1,
            override_defaults=True,
        )
        exc = RateLimitExceeded(limit=limit)

        from fastapi import FastAPI
        from starlette.requests import Request
        from starlette.responses import Response
        from starlette.testclient import TestClient as StarletteTestClient

        test_app = FastAPI()

        @test_app.exception_handler(RateLimitExceeded)
        async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
            return await RateLimitExceededHandler.handler(request, exc)

        @test_app.get("/test-rate-limit")
        async def trigger_rate_limit():
            raise exc

        client = StarletteTestClient(test_app, raise_server_exceptions=False)
        response = client.get("/test-rate-limit")
        assert response.status_code == 429
        body = response.json()
        assert "detail" in body
        assert body["detail"] == "Rate limit exceeded. Please try again later."

    def test_handler_response_is_json_content_type(self):
        """Verify the 429 response uses application/json content type."""
        limit_item = parse_limit("10/minute")
        limit = Limit(
            limit=limit_item,
            key_func=lambda: "test",
            scope="test",
            per_method=False,
            methods=None,
            error_message=None,
            exempt_when=None,
            cost=1,
            override_defaults=True,
        )
        exc = RateLimitExceeded(limit=limit)

        from fastapi import FastAPI
        from starlette.testclient import TestClient as StarletteTestClient

        test_app = FastAPI()

        @test_app.exception_handler(RateLimitExceeded)
        async def rate_limit_handler(request, exc):
            return await RateLimitExceededHandler.handler(request, exc)

        @test_app.get("/test-content-type")
        async def trigger_rate_limit():
            raise RateLimitExceeded(limit=limit)

        client = StarletteTestClient(test_app, raise_server_exceptions=False)
        response = client.get("/test-content-type")
        assert response.status_code == 429
        assert "application/json" in response.headers.get("content-type", "")


# ---------------------------------------------------------------------------
# Slowapi route registry — verify limits are REGISTERED (not function attrs)
# ---------------------------------------------------------------------------

class TestRateLimitRegistry:
    """
    slowapi stores rate limits in an internal registry (limiter._route_limits).

    The registry key format uses the full module dotted path.
    When the router lives at spine_api/routers/auth.py, keys look like:
        spine_api.routers.auth.post_signup
    """

    @pytest.fixture(autouse=True)
    def _ensure_app_imported(self):
        """Import the full app to trigger decorator registration."""
        import spine_api.routers.auth  # noqa: F401

    def _limiter(self):
        """Get the limiter AFTER the router module has been imported."""
        from spine_api.core.rate_limiter import limiter
        return limiter

    _KEY = "spine_api.routers.auth"

    def test_signup_registered_with_rate_limit(self):
        limiter = self._limiter()
        key = f"{self._KEY}.post_signup"
        assert key in limiter._Limiter__marked_for_limiting, (
            f"post_signup not in slowapi registry. "
            f"Available: {list(limiter._Limiter__marked_for_limiting.keys())}"
        )
        assert key in limiter._route_limits, f"No static limits for {key}"
        limits = limiter._route_limits[key]
        assert any("5" in str(l.limit) for l in limits), (
            f"Expected 5/minute limit for signup, got: {[str(l.limit) for l in limits]}"
        )

    def test_login_registered_with_rate_limit(self):
        key = f"{self._KEY}.post_login"
        assert key in self._limiter()._Limiter__marked_for_limiting

    def test_refresh_registered_with_rate_limit(self):
        key = f"{self._KEY}.post_refresh"
        assert key in self._limiter()._Limiter__marked_for_limiting

    def test_request_password_reset_registered_with_rate_limit(self):
        key = f"{self._KEY}.post_request_password_reset"
        assert key in self._limiter()._Limiter__marked_for_limiting

    def test_confirm_password_reset_registered_with_rate_limit(self):
        key = f"{self._KEY}.post_confirm_password_reset"
        assert key in self._limiter()._Limiter__marked_for_limiting

    def test_logout_not_rate_limited(self):
        limiter = self._limiter()
        key = f"{self._KEY}.post_logout"
        assert key not in limiter._Limiter__marked_for_limiting, (
            f"post_logout should NOT have a rate limit, but found in registry"
        )

    def test_me_not_rate_limited(self):
        limiter = self._limiter()
        key = f"{self._KEY}.get_me"
        assert key not in limiter._Limiter__marked_for_limiting, (
            f"get_me should NOT have a rate limit, but found in registry"
        )


# ---------------------------------------------------------------------------
# Middleware registration on the app
# ---------------------------------------------------------------------------

class TestRateLimitMiddlewareRegistration:
    def test_slowapi_middleware_registered_on_app(self):
        app = _get_app()
        middleware_classes = [
            m.cls.__name__ if hasattr(m, "cls") else type(m).__name__
            for m in app.user_middleware
        ]
        assert "SlowAPIMiddleware" in middleware_classes, (
            f"SlowAPIMiddleware not found in middleware: {middleware_classes}"
        )

    def test_rate_limit_exception_handler_registered(self):
        app = _get_app()
        assert RateLimitExceeded in app.exception_handlers, (
            f"RateLimitExceeded not in exception handlers. "
            f"Handlers: {list(app.exception_handlers.keys())}"
        )

    def test_auth_router_has_9_routes(self):
        from spine_api.routers.auth import router
        assert len(router.routes) == 9, (
            f"Expected 9 auth routes, got {len(router.routes)}: "
            f"{[r.path for r in router.routes]}"
        )


# ---------------------------------------------------------------------------
# Pydantic validation preserved (router uses typed body params, not request.json())
# ---------------------------------------------------------------------------

class TestAuthRouterPreservesPydanticValidation:
    """Verify that adding request: Request for slowapi did NOT break Pydantic models."""

    def test_signup_uses_pydantic_body(self):
        from spine_api.routers.auth import SignupRequest
        with pytest.raises(Exception):
            SignupRequest(email="not-an-email", password="short")

    def test_signup_accepts_valid_body(self):
        from spine_api.routers.auth import SignupRequest
        req = SignupRequest(email="user@example.com", password="longenoughpwd")
        assert req.email == "user@example.com"
        assert req.password == "longenoughpwd"

    def test_login_uses_pydantic_body(self):
        from spine_api.routers.auth import LoginRequest
        req = LoginRequest(email="user@example.com", password="anypassword")
        assert req.email == "user@example.com"

    def test_password_reset_request_rejects_invalid_email(self):
        from spine_api.routers.auth import PasswordResetRequest
        with pytest.raises(Exception):
            PasswordResetRequest(email="not-an-email")

    def test_password_reset_confirm_rejects_short_password(self):
        from spine_api.routers.auth import PasswordResetConfirm
        with pytest.raises(Exception):
            PasswordResetConfirm(token="", new_password="short")

    def test_signup_endpoint_has_both_request_and_body_params(self):
        """FastAPI allows both Request (for slowapi) and Pydantic body params."""
        from spine_api.routers.auth import post_signup
        import inspect
        params = list(inspect.signature(post_signup).parameters.keys())
        assert "request" in params, f"request not in params: {params}"
        assert "signup_req" in params, f"signup_req not in params: {params}"

    def test_login_endpoint_has_both_request_and_body_params(self):
        from spine_api.routers.auth import post_login
        import inspect
        params = list(inspect.signature(post_login).parameters.keys())
        assert "request" in params, f"request not in params: {params}"
        assert "login_req" in params, f"login_req not in params: {params}"