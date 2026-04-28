"""
Membership service — team member management backed by the Membership + User models.

Replaces TeamStore (file-based JSON) as the source of truth for team members.
Every team member is a real User with a Membership in an agency.

Operations are async and agency-scoped.
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from spine_api.core.security import hash_password
from spine_api.models.tenant import User, Membership

logger = logging.getLogger("spine_api.membership_service")


def _member_to_dict(m: Membership, user: User) -> dict:
    """Serialize a Membership + User pair to the response shape."""
    return {
        "id": m.id,
        "user_id": user.id,
        "email": user.email,
        "name": user.name or user.email.split("@")[0],
        "role": m.role,
        "capacity": m.capacity,
        "status": m.status,
        "specializations": m.specializations or [],
        "created_at": m.created_at.isoformat(),
        "updated_at": m.updated_at.isoformat() if m.updated_at else None,
    }


async def invite_member(
    db: AsyncSession,
    agency_id: str,
    email: str,
    name: str,
    role: str,
    capacity: int = 5,
    specializations: Optional[List[str]] = None,
    invited_by: Optional[str] = None,
) -> dict:
    """
    Add a team member to an agency.

    If the email already belongs to a User, creates a Membership for them.
    Otherwise creates a new User (with a placeholder password) + Membership.

    Returns the serialized member dict.
    """
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            email=email,
            password_hash=hash_password("PLACEHOLDER_" + email),
            name=name,
        )
        db.add(user)
        await db.flush()

    existing = await db.execute(
        select(Membership).where(
            Membership.user_id == user.id,
            Membership.agency_id == agency_id,
        )
    )
    if existing.scalar_one_or_none():
        raise ValueError(f"User {email} is already a member of this agency")

    member = Membership(
        user_id=user.id,
        agency_id=agency_id,
        role=role,
        capacity=capacity,
        specializations=specializations or [],
        status="active",
        is_primary=False,
    )
    db.add(member)
    await db.commit()
    await db.refresh(member)

    logger.info("Member invited: user=%s agency=%s role=%s", user.id, agency_id, role)

    return _member_to_dict(member, user)


async def list_members(
    db: AsyncSession,
    agency_id: str,
    active_only: bool = False,
) -> List[dict]:
    """List all members of an agency, optionally filtered to active only."""
    query = (
        select(Membership, User)
        .join(User, Membership.user_id == User.id)
        .where(Membership.agency_id == agency_id)
    )

    if active_only:
        query = query.where(Membership.status == "active")

    query = query.order_by(Membership.created_at)

    result = await db.execute(query)
    rows = result.all()

    return [_member_to_dict(m, u) for m, u in rows]


async def get_member(
    db: AsyncSession,
    membership_id: str,
) -> Optional[dict]:
    """Get a single member by membership ID."""
    result = await db.execute(
        select(Membership, User)
        .join(User, Membership.user_id == User.id)
        .where(Membership.id == membership_id)
    )
    row = result.one_or_none()
    if not row:
        return None
    m, u = row
    return _member_to_dict(m, u)


async def update_member(
    db: AsyncSession,
    membership_id: str,
    agency_id: str,
    updates: dict,
) -> Optional[dict]:
    """Update membership fields (role, capacity, specializations)."""
    result = await db.execute(
        select(Membership).where(
            Membership.id == membership_id,
            Membership.agency_id == agency_id,
        )
    )
    membership_row = result.scalar_one_or_none()
    if not membership_row:
        return None

    allowed_fields = {"role", "capacity", "specializations"}
    for key, value in updates.items():
        if key in allowed_fields:
            setattr(membership_row, key, value)

    membership_row.updated_at = datetime.now(timezone.utc)
    await db.commit()

    user_result = await db.execute(select(User).where(User.id == membership_row.user_id))
    user = user_result.scalar_one()

    logger.info("Member updated: membership=%s", membership_id)
    return _member_to_dict(membership_row, user)


async def deactivate_member(
    db: AsyncSession,
    membership_id: str,
    agency_id: str,
) -> bool:
    """Set a member's status to inactive."""
    result = await db.execute(
        select(Membership).where(
            Membership.id == membership_id,
            Membership.agency_id == agency_id,
        )
    )
    membership_row = result.scalar_one_or_none()
    if not membership_row:
        return False

    membership_row.status = "inactive"
    membership_row.updated_at = datetime.now(timezone.utc)
    await db.commit()

    logger.info("Member deactivated: membership=%s", membership_id)
    return True
