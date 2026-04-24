"""
FastAPI middleware for Waypoint OS.

Provides:
- AuthMiddleware: Enforces authentication on all routes except public paths.
"""

import logging
from typing import Awaitable, Callable

from fastapi import Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from core.database import async_session_maker
from core.security import decode_token_safe
from models.tenant import User

logger = logging.getLogger("spine-api.middleware")


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware that enforces JWT authentication on all routes.

    Public routes (no auth required):
    - /health
    - /docs, /openapi.json, /redoc
    - /api/auth/*  (login, signup, refresh, etc.)
    """

    PUBLIC_PATHS: set[str] = {"/health", "/docs", "/openapi.json", "/redoc"}
    PUBLIC_PREFIXES: tuple[str, ...] = ("/api/auth",)

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[JSONResponse]]
    ) -> JSONResponse:
        path = request.url.path

        # Allow public routes
        if path in self.PUBLIC_PATHS or any(
            path.startswith(prefix) for prefix in self.PUBLIC_PREFIXES
        ):
            return await call_next(request)

        # Extract token from Authorization header or cookie
        token: str | None = None
        auth_header = request.headers.get("authorization", "")
        if auth_header.lower().startswith("bearer "):
            token = auth_header[7:]
        else:
            token = request.cookies.get("access_token")

        if not token:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Not authenticated"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Validate token
        payload = decode_token_safe(token)
        if not payload:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid or expired token"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        user_id = payload.get("sub")
        if not user_id:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid token payload"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Validate user exists and is active
        async with async_session_maker() as db:
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()

            if not user or not user.is_active:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "User not found or inactive"},
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # Attach user to request state for downstream handlers
            request.state.user = user

        return await call_next(request)
