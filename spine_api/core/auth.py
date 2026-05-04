"""
FastAPI auth dependencies for Waypoint OS.

Provides:
- get_current_user: Extract and validate JWT from Authorization header or cookie
- require_auth: Dependency that ensures user is authenticated
- require_permission: Dependency factory that checks role-based permissions
- get_current_agency_id: Extract primary agency_id from authenticated user
"""

import os
from typing import Optional

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from spine_api.core.database import get_db
from spine_api.core.security import decode_token_safe
from spine_api.models.tenant import User, Membership
from spine_api.core.rls import set_rls_agency

# Security scheme for Swagger docs
security_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Extract and validate JWT from Authorization header or cookie,
    then load the user from the database.
    """
    token = None

    # Try Authorization header first
    if credentials:
        token = credentials.credentials
    else:
        # Fallback to cookie
        token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token_safe(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def _auth_or_skip(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """Authenticate unless SPINE_API_DISABLE_AUTH is set (dev/test only).

    Reads the env var at call time — not at import time — so tests can
    toggle auth behavior without importlib.reload().
    """
    if os.environ.get("SPINE_API_DISABLE_AUTH"):
        return None
    return await get_current_user(request, credentials, db)


async def get_current_membership(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Membership:
    """
    Get the user's primary membership (the agency they're currently operating in).
    If user has multiple memberships, returns the one marked is_primary=True.
    """
    result = await db.execute(
        select(Membership)
        .where(Membership.user_id == user.id)
        .where(Membership.is_primary == True)
    )
    membership = result.scalar_one_or_none()

    if not membership:
        # Fallback: return first membership
        result = await db.execute(
            select(Membership).where(Membership.user_id == user.id)
        )
        membership = result.scalar_one_or_none()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not a member of any agency",
        )

    # Populate the RLS ContextVar so get_rls_db() can enforce tenant isolation.
    set_rls_agency(membership.agency_id)

    return membership


async def get_current_agency_id(
    membership: Membership = Depends(get_current_membership),
) -> str:
    """Return the current agency_id for tenant scoping."""
    return membership.agency_id


async def get_current_agency(
    agency_id: str = Depends(get_current_agency_id),
    db: AsyncSession = Depends(get_db),
) -> "Agency":
    """Return the current agency object for the authenticated user."""
    from spine_api.models.tenant import Agency
    
    result = await db.execute(select(Agency).where(Agency.id == agency_id))
    agency = result.scalar_one_or_none()
    
    if not agency:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agency not found",
        )
    
    return agency


# Permission matrix
ROLE_PERMISSIONS = {
    "owner": ["*"],
    "admin": [
        "team:manage", "trips:read", "trips:write", "trips:assign",
        "trips:reassign", "trips:escalate", "settings:read", "settings:write",
        "customers:read", "customers:write", "ai_workforce:manage",
        "reports:read", "audit:read",
    ],
    "senior_agent": [
        "trips:read", "trips:write", "trips:claim", "trips:request_handoff",
        "customers:read", "customers:write", "reports:read:own",
    ],
    "junior_agent": [
        "trips:read:assigned", "trips:write:assigned", "trips:request_review",
        "customers:read:assigned",
    ],
    "viewer": [
        "trips:read", "customers:read", "reports:read",
    ],
}


def require_permission(permission: str):
    """
    Dependency factory that checks if the current user has a specific permission.

    Usage:
        @app.post("/api/team/invite")
        async def invite_member(
            current_user: User = Depends(require_permission("team:manage"))
        ):
            ...
    """
    async def permission_checker(
        membership: Membership = Depends(get_current_membership),
    ) -> Membership:
        role = membership.role.lower()
        permissions = ROLE_PERMISSIONS.get(role, [])

        if "*" in permissions or permission in permissions:
            return membership

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission denied: {permission}",
        )

    return Depends(permission_checker)


# Convenience dependency that just requires any valid auth
require_auth = Depends(get_current_user)
