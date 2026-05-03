"""
spine_api.core.audit — Dependency-based audit logging for FastAPI routes.

Architecture:
- `Depends(audit_logger())` injects an AuditContext into route handlers
- NOT blanket middleware — only routes that opt in get audit logging
- Agency ID and user ID come from JWT auth context, no manual passing
- AuditContext.log() async method writes to the database via SQLAlchemy

Usage in routes:
    @router.post("/trips")
    async def create_trip(
        audit: AuditContext = Depends(audit_logger()),
        user: User = Depends(get_current_user),
        ...
    ):
        result = ...
        await audit.log(AuditAction.CREATE, resource_type="trip", resource_id=trip_id, changes={...})
        return result

The audit_logger() dependency:
1. Resolves user_id and agency_id from JWT auth context
2. Extracts IP address and User-Agent from the Request
3. Returns an AuditContext that can be used to log events within the route

If auth is disabled (SPINE_API_DISABLE_AUTH), audit_logger() returns a
context with agency_id="system" and user_id=None — the route still needs
to provide action and resource info.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from spine_api.core.database import get_db
from spine_api.core.security import decode_token_safe
from spine_api.models.audit import AuditAction, AuditLog
from spine_api.models.tenant import Membership, User

logger = logging.getLogger("spine_api.audit")


class AuditContext:
    """Context object injected into route handlers for audit logging."""

    def __init__(
        self,
        db: AsyncSession,
        agency_id: str,
        user_id: Optional[str],
        ip_address: Optional[str],
        user_agent: Optional[str],
    ):
        self._db = db
        self._agency_id = agency_id
        self._user_id = user_id
        self._ip_address = ip_address
        self._user_agent = user_agent

    async def log(
        self,
        action: AuditAction | str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        changes: Optional[dict] = None,
    ) -> AuditLog:
        """Write an audit log entry to the database.

        Args:
            action: What happened (use AuditAction enum or plain string)
            resource_type: Type of resource (e.g. "trip", "user", "agency")
            resource_id: ID of the affected resource
            changes: Optional before/after dict for state mutations

        Returns:
            The persisted AuditLog entry
        """
        action_str = action.value if isinstance(action, AuditAction) else str(action)

        entry = AuditLog(
            agency_id=self._agency_id,
            user_id=self._user_id,
            action=action_str,
            resource_type=resource_type,
            resource_id=resource_id,
            changes=changes,
            ip_address=self._ip_address,
            user_agent=self._user_agent,
            created_at=datetime.now(timezone.utc),
        )
        self._db.add(entry)
        try:
            await self._db.flush()
            logger.debug(
                "Audit: agency=%s user=%s action=%s resource=%s/%s",
                self._agency_id, self._user_id, action_str,
                resource_type, resource_id,
            )
        except Exception as exc:
            logger.warning("Audit log flush failed (non-fatal): %s", exc)
        return entry

    @property
    def agency_id(self) -> str:
        return self._agency_id

    @property
    def user_id(self) -> Optional[str]:
        return self._user_id


def audit_logger():
    """FastAPI dependency that provides an AuditContext for route handlers.

    Resolves auth context from JWT token if present. Falls back to system-level
    context for unauthenticated requests (public routes like signup/login).
    """
    async def _get_audit_context(
        request: Request,
        db: AsyncSession = Depends(get_db),
    ) -> AuditContext:
        agency_id = "system"
        user_id = None
        # Try to extract user from token, but don't fail if unauthenticated
        token: str | None = None
        auth_header = request.headers.get("authorization", "")
        if auth_header.lower().startswith("bearer "):
            token = auth_header[7:]
        else:
            token = request.cookies.get("access_token")
        if token:
            payload = decode_token_safe(token)
            if payload and payload.get("sub"):
                result = await db.execute(select(User).where(User.id == payload["sub"]))
                user_obj = result.scalar_one_or_none()
                if user_obj and user_obj.is_active:
                    user_id = user_obj.id
                    m_result = await db.execute(
                        select(Membership)
                        .where(Membership.user_id == user_id)
                        .where(Membership.is_primary == True)
                    )
                    membership_obj = m_result.scalar_one_or_none()
                    if not membership_obj:
                        m_result = await db.execute(
                            select(Membership).where(Membership.user_id == user_id)
                        )
                        membership_obj = m_result.scalar_one_or_none()
                    if membership_obj:
                        agency_id = membership_obj.agency_id

        ip_address = _extract_client_ip(request)
        user_agent = request.headers.get("user-agent")

        return AuditContext(
            db=db,
            agency_id=agency_id,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    return _get_audit_context


def _extract_client_ip(request: Request) -> Optional[str]:
    """Extract client IP from X-Forwarded-For header or direct client."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None