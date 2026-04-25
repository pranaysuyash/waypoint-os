"""
FastAPI middleware for Waypoint OS.

Provides:
- AuthMiddleware: Enforces authentication on all routes except public paths.
"""

import logging
from typing import Awaitable, Callable

from fastapi import Request, status
from sqlalchemy import select
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from spine_api.core.database import async_session_maker
from spine_api.core.security import decode_token_safe
from spine_api.models.tenant import User

logger = logging.getLogger("spine_api.middleware")


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware that enforces JWT authentication on protected backend routes.

    Public routes:
    - /health
    - /docs, /openapi.json, /redoc
    - /api/auth/*
    """

    PUBLIC_PATHS: set[str] = {"/health", "/docs", "/openapi.json", "/redoc"}
    PUBLIC_PREFIXES: tuple[str, ...] = ("/api/auth",)

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[JSONResponse]],
    ) -> JSONResponse:
        path = request.url.path

        if path in self.PUBLIC_PATHS or any(
            path.startswith(prefix) for prefix in self.PUBLIC_PREFIXES
        ):
            return await call_next(request)

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

        async with async_session_maker() as db:
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()

            if not user or not user.is_active:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "User not found or inactive"},
                    headers={"WWW-Authenticate": "Bearer"},
                )

            request.state.user = user

        return await call_next(request)
