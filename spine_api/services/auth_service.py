"""
Auth service — business logic for signup, login, logout, token refresh.

Handles:
- User creation with bcrypt password hashing
- Agency + Membership bootstrap on signup
- JWT access + refresh token generation
- httpOnly cookie management for token delivery
"""

import logging
import secrets
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from models.tenant import Agency, User, Membership, WorkspaceCode

logger = logging.getLogger("spine_api.auth_service")


def _slug_from_name(name: str) -> str:
    slug = name.lower().strip()
    slug = slug.replace(" ", "-")
    keep = set("abcdefghijklmnopqrstuvwxyz0123456789-")
    slug = "".join(c for c in slug if c in keep)
    slug = "-".join(part for part in slug.split("-") if part)
    return slug[:60] or "agency"


def _agency_name_from_email(email: str) -> str:
    domain = email.split("@")[1] if "@" in email else "agency"
    name = domain.split(".")[0]
    return name.title()


async def signup(
    db: AsyncSession,
    email: str,
    password: str,
    name: Optional[str] = None,
    agency_name: Optional[str] = None,
) -> dict:
    """
    Create a new user, agency, membership, and workspace code.

    Returns:
        dict with user, agency, membership, tokens
    """
    result = await db.execute(select(User).where(User.email == email))
    if result.scalar_one_or_none():
        raise ValueError("Email already registered")

    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters")

    user = User(
        email=email,
        password_hash=hash_password(password),
        name=name or email.split("@")[0],
    )
    db.add(user)

    resolved_agency_name = agency_name or _agency_name_from_email(email)
    slug = _slug_from_name(resolved_agency_name)

    slug_result = await db.execute(select(Agency).where(Agency.slug == slug))
    if slug_result.scalar_one_or_none():
        slug = f"{slug}-{secrets.token_hex(3)}"

    agency = Agency(
        name=resolved_agency_name,
        slug=slug,
        email=email,
    )
    db.add(agency)
    await db.flush()

    membership = Membership(
        user_id=user.id,
        agency_id=agency.id,
        role="owner",
        is_primary=True,
    )
    db.add(membership)

    code = WorkspaceCode(
        agency_id=agency.id,
        code=f"WP-{secrets.token_urlsafe(8)}",
        code_type="internal",
        status="active",
        created_by=user.id,
    )
    db.add(code)
    await db.commit()
    await db.refresh(user)
    await db.refresh(agency)
    await db.refresh(membership)

    access_token = create_access_token(
        user_id=user.id,
        agency_id=agency.id,
        role=membership.role,
    )
    refresh_token = create_refresh_token(user_id=user.id)

    logger.info("Signup complete: user=%s agency=%s", user.id, agency.id)

    return {
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
        },
        "agency": {
            "id": agency.id,
            "name": agency.name,
            "slug": agency.slug,
            "logo_url": agency.logo_url,
        },
        "membership": {
            "role": membership.role,
            "is_primary": membership.is_primary,
        },
        "access_token": access_token,
        "refresh_token": refresh_token,
    }


async def login(
    db: AsyncSession,
    email: str,
    password: str,
) -> dict:
    """
    Authenticate a user by email + password.

    Returns:
        dict with user, agency, membership, tokens
    """
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(password, user.password_hash):
        raise ValueError("Invalid email or password")

    if not user.is_active:
        raise ValueError("Account is deactivated")

    result = await db.execute(
        select(Membership)
        .where(Membership.user_id == user.id)
        .where(Membership.is_primary == True)
    )
    membership = result.scalar_one_or_none()

    if not membership:
        result = await db.execute(
            select(Membership).where(Membership.user_id == user.id)
        )
        membership = result.scalar_one_or_none()

    if not membership:
        raise ValueError("User has no agency membership")

    result = await db.execute(select(Agency).where(Agency.id == membership.agency_id))
    agency = result.scalar_one_or_none()

    if not agency:
        raise ValueError("Agency not found")

    user.last_login_at = datetime.now(timezone.utc)
    await db.commit()

    access_token = create_access_token(
        user_id=user.id,
        agency_id=agency.id,
        role=membership.role,
    )
    refresh_token = create_refresh_token(user_id=user.id)

    logger.info("Login: user=%s agency=%s", user.id, agency.id)

    return {
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
        },
        "agency": {
            "id": agency.id,
            "name": agency.name,
            "slug": agency.slug,
            "logo_url": agency.logo_url,
        },
        "membership": {
            "role": membership.role,
            "is_primary": membership.is_primary,
        },
        "access_token": access_token,
        "refresh_token": refresh_token,
    }


async def refresh_access_token(
    db: AsyncSession,
    refresh_token_str: str,
) -> dict:
    """
    Exchange a valid refresh token for new access + refresh tokens.
    """
    try:
        payload = decode_token(refresh_token_str)
    except Exception:
        raise ValueError("Invalid refresh token")

    if payload.get("type") != "refresh":
        raise ValueError("Not a refresh token")

    user_id = payload.get("sub")
    if not user_id:
        raise ValueError("Invalid token payload")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise ValueError("User not found or inactive")

    result = await db.execute(
        select(Membership)
        .where(Membership.user_id == user.id)
        .where(Membership.is_primary == True)
    )
    membership = result.scalar_one_or_none()

    if not membership:
        raise ValueError("No active membership")

    new_access = create_access_token(
        user_id=user.id,
        agency_id=membership.agency_id,
        role=membership.role,
    )
    new_refresh = create_refresh_token(user_id=user.id)

    return {
        "access_token": new_access,
        "refresh_token": new_refresh,
    }


# ============================================================================
# PASSWORD RESET
# ============================================================================

import hashlib


async def request_password_reset(db: AsyncSession, email: str) -> dict:
    """
    Generate a password reset token and return it.
    In production, this would send an email with the reset link.
    For now, returns the plain token so the frontend can simulate the reset flow.

    Returns:
        dict with reset_token (to be sent via email in production)
    """
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        # Don't reveal that the email doesn't exist (security best practice)
        return {"ok": True, "message": "If the email exists, a reset link has been sent"}

    # Invalidate old tokens for this user
    await db.execute(
        PasswordResetToken.__table__.delete().where(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used_at.is_(None),
        )
    )

    # Generate a secure token
    import secrets
    plain_token = secrets.token_urlsafe(32)

    # Hash token for storage (we never store the plain token)
    token_hash = hashlib.sha256(plain_token.encode()).hexdigest()

    reset_token = PasswordResetToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    db.add(reset_token)
    await db.commit()

    logger.info("Password reset requested: user=%s", user.id)

    # In production: send email with /reset-password?token=plain_token
    # For now, return the token so the frontend can use it
    return {
        "ok": True,
        "message": "If the email exists, a reset link has been sent",
        "reset_token": plain_token,  # Remove in production (use email instead)
    }


async def confirm_password_reset(db: AsyncSession, token: str, new_password: str) -> dict:
    """
    Validate a password reset token and set a new password.

    Returns:
        dict with ok=True on success

    Raises:
        ValueError: if token is invalid or expired
    """
    if len(new_password) < 8:
        raise ValueError("Password must be at least 8 characters")

    token_hash = hashlib.sha256(token.encode()).hexdigest()

    result = await db.execute(
        select(PasswordResetToken)
        .where(PasswordResetToken.token_hash == token_hash)
        .where(PasswordResetToken.used_at.is_(None))
    )
    reset_record = result.scalar_one_or_none()

    if not reset_record:
        raise ValueError("Invalid or expired reset token")

    if reset_record.expires_at < datetime.now(timezone.utc):
        raise ValueError("Reset token has expired")

    # Update password
    result = await db.execute(select(User).where(User.id == reset_record.user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise ValueError("User not found")

    user.password_hash = hash_password(new_password)
    reset_record.used_at = datetime.now(timezone.utc)

    await db.commit()

    logger.info("Password reset completed: user=%s", user.id)

    return {"ok": True, "message": "Password has been reset successfully"}
