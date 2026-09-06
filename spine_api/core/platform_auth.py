"""Platform-admin authorization separate from tenant membership roles."""

from __future__ import annotations

from typing import Final

from fastapi import Depends, HTTPException, status

from spine_api.core.auth import get_current_user
from spine_api.models.tenant import User

PLATFORM_ROLES: Final[frozenset[str]] = frozenset(
    {"none", "support", "ops_admin", "super_admin"}
)


def require_platform_role(*allowed_roles: str):
    """Return a dependency requiring an explicit platform role.

    Platform roles are intentionally independent from agency membership roles.
    A tenant ``owner`` or ``admin`` never grants cross-workspace visibility.
    """

    invalid_roles = set(allowed_roles) - PLATFORM_ROLES
    if invalid_roles:
        raise ValueError(f"Unknown platform role(s): {sorted(invalid_roles)}")
    if not allowed_roles:
        raise ValueError("At least one platform role is required")

    async def platform_role_guard(user: User = Depends(get_current_user)) -> User:
        actual_role = str(getattr(user, "platform_role", "none") or "none").lower()
        if actual_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Platform administrator access required",
            )
        return user

    return Depends(platform_role_guard)
