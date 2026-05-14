"""
FastAPI middleware for Waypoint OS.

Provides:
- AuthMiddleware: Enforces authentication on all routes except public paths.
  Uses a pure-ASGI approach to avoid BaseHTTPMiddleware body-consumption issues.
- RequestBodySizeMiddleware: Enforces maximum request body size at the ASGI
  level by counting received bytes before they reach the application.
"""

import logging
import os
from typing import Awaitable, Callable

from fastapi import HTTPException, Request, status
from sqlalchemy import select
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from spine_api.core.database import async_session_maker
from spine_api.core.security import decode_token_safe
from spine_api.models.tenant import User

logger = logging.getLogger("spine_api.middleware")

PUBLIC_PATHS: set[str] = {"/health", "/docs", "/openapi.json", "/redoc"}
PUBLIC_PREFIXES: tuple[str, ...] = ("/api/auth", "/api/public/", "/api/public-checker")


def _is_public_path(path: str) -> bool:
    return path in PUBLIC_PATHS or any(
        path.startswith(prefix) for prefix in PUBLIC_PREFIXES
    )


class AuthMiddleware:
    """
    Pure-ASGI middleware that enforces JWT authentication on protected routes.

    Public routes:
    - /health
    - /docs, /openapi.json, /redoc
    - /api/auth/*
    - /api/public/*
    - /api/public-checker/*
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")

        if _is_public_path(path):
            await self.app(scope, receive, send)
            return

        # Build a FastAPI Request from the ASGI scope to access headers/cookies.
        # We intercept before the app runs so we don't consume the body.
        request = Request(scope, receive)

        token: str | None = None
        auth_header = request.headers.get("authorization", "")
        if auth_header.lower().startswith("bearer "):
            token = auth_header[7:]
        else:
            token = request.cookies.get("access_token")

        if not token:
            response = JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Not authenticated"},
                headers={"WWW-Authenticate": "Bearer"},
            )
            await response(scope, receive, send)
            return

        payload = decode_token_safe(token)
        if not payload:
            response = JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid or expired token"},
                headers={"WWW-Authenticate": "Bearer"},
            )
            await response(scope, receive, send)
            return

        user_id = payload.get("sub")
        if not user_id:
            response = JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid token payload"},
                headers={"WWW-Authenticate": "Bearer"},
            )
            await response(scope, receive, send)
            return

        async with async_session_maker() as db:
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()

            if not user or not user.is_active:
                response = JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "User not found or inactive"},
                    headers={"WWW-Authenticate": "Bearer"},
                )
                await response(scope, receive, send)
                return

            # Inject user into request state before passing to the app
            scope["state"] = dict(scope.get("state", {}))
            scope["state"]["user"] = user

        await self.app(scope, receive, send)


PUBLIC_CHECKER_MAX_BYTES = int(os.environ.get("PUBLIC_CHECKER_MAX_CONTENT_LENGTH", str(256 * 1024)))


class RequestBodySizeMiddleware:
    """
    ASGI middleware that enforces a maximum request body size.

    Counts bytes as they arrive via receive(), rejecting oversized bodies
    before the application can parse them. This is more robust than checking
    Content-Length alone (which can be omitted, duplicated, or spoofed).

    Public checker paths get a tighter limit; all other paths use a larger limit.
    Both limits are enforced at the ASGI level, before the application sees the body.
    The public checker limit matches PUBLIC_CHECKER_MAX_CONTENT_LENGTH (256 KB by default)
    used by the /api/public-checker/run endpoint.
    """

    _PUBLIC_CHECKER_PREFIX = "/api/public-checker"
    _DEFAULT_MAX_BYTES = 5 * 1024 * 1024  # 5 MB

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        max_bytes = (
            PUBLIC_CHECKER_MAX_BYTES
            if path.startswith(self._PUBLIC_CHECKER_PREFIX)
            else self._DEFAULT_MAX_BYTES
        )

        bytes_read = 0

        async def sized_receive() -> Message:
            nonlocal bytes_read
            message = await receive()
            if message["type"] == "http.request":
                chunk = message.get("body", b"")
                bytes_read += len(chunk)
                if bytes_read > max_bytes:
                    raise HTTPException(
                        status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                        detail="Request body too large",
                    )
            return message

        try:
            await self.app(scope, sized_receive, send)
        except HTTPException as exc:
            response = JSONResponse(
                status_code=exc.status_code,
                content={"detail": exc.detail},
            )
            await response(scope, receive, send)
