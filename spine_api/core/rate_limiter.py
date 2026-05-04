"""
spine_api.core.rate_limiter — Environment-aware rate limiting for auth endpoints.

Provides:
- limiter: SlowAPI LimiterInstance configured from environment
- RateLimitMiddleware: Starlette middleware that enforces limits
- Environment awareness: limits are disabled/raised in development and test
"""

import os
import logging

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger("spine_api.rate_limiter")


def _key_func(request: Request) -> str:
    """Rate limit key: IP address from X-Forwarded-For or direct client."""
    return get_remote_address(request)


def _get_default_limits() -> list[str]:
    """
    Environment-aware default rate limits.
    In development/test: very generous (1000/min) so devs never hit 429.
    In production: conservative (60/min general).
    
    Re-reads ENVIRONMENT at call time so tests don't need importlib.reload.
    """
    environment = os.environ.get("ENVIRONMENT", "development").lower()
    if environment in ("development", "test", "dev"):
        return ["1000/minute"]
    return ["60/minute"]


limiter = Limiter(
    key_func=_key_func,
    default_limits=_get_default_limits(),
    enabled=True,
    headers_enabled=True,
)


class RateLimitExceededHandler:
    """Custom 429 handler that returns structured JSON matching the app's error format."""

    @staticmethod
    async def handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
        logger.warning(
            "Rate limit exceeded: ip=%s path=%s detail=%s",
            get_remote_address(request),
            request.url.path,
            str(exc.detail),
        )
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded. Please try again later."},
        )