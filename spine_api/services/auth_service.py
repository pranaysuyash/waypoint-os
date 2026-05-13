"""
Auth service — business logic for signup, login, logout, token refresh.

Handles:
- User creation with bcrypt password hashing
- Workspace code validation and agent join flow (join_with_code, validate_workspace_code)
- Agency + Membership bootstrap on signup
- JWT access + refresh token generation
- httpOnly cookie management for token delivery
"""

import hashlib
import logging
import os
import secrets
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from spine_api.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from spine_api.models.tenant import Agency, User, Membership, WorkspaceCode, PasswordResetToken
from spine_api.core.rls import apply_rls

logger = logging.getLogger("spine_api.auth_service")


async def _ensure_user_membership(db: AsyncSession, user: User) -> Membership:
    """
    Ensure the user has at least one agency membership.
    If the user is an orphan (no memberships), create a default agency and
    an owner membership on the fly so the user can log in.

    Idempotent: if memberships already exist, returns the primary one.
    """
    # Try primary first
    result = await db.execute(
        select(Membership)
        .where(Membership.user_id == user.id)
        .where(Membership.is_primary == True)
    )
    membership = result.scalar_one_or_none()
    if membership:
        return membership

    # Fallback to any membership
    result = await db.execute(
        select(Membership).where(Membership.user_id == user.id)
    )
    membership = result.scalar_one_or_none()
    if membership:
        return membership

    # Orphan user: create default agency + owner membership
    agency_name = f"{user.name or user.email}'s Agency"
    slug_base = agency_name.lower().replace("'s agency", "").replace(" ", "-")
    slug = f"{slug_base[:40]}-{secrets.token_hex(4)}"

    # Ensure slug uniqueness
    slug_result = await db.execute(select(Agency).where(Agency.slug == slug))
    if slug_result.scalar_one_or_none():
        slug = f"{slug_base[:40]}-{secrets.token_hex(6)}"

    agency = Agency(
        name=agency_name,
        slug=slug,
        email=user.email,
    )
    db.add(agency)
    await db.flush()  # get agency.id

    # Apply RLS so the membership insert passes tenant policy
    await apply_rls(db, agency.id)

    membership = Membership(
        user_id=user.id,
        agency_id=agency.id,
        role="owner",
        is_primary=True,
        status="active",
    )
    db.add(membership)
    await db.flush()

    logger.info(
        "Runtime backfill: created agency=%s + membership for orphan user=%s",
        agency.id, user.id,
    )
    return membership


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
    is_test: bool = False,
) -> dict:
    """
    Create a new user, agency, membership, and workspace code.
    
    Args:
        db: Database session
        email: User email
        password: User password (min 8 chars)
        name: Optional user display name
        agency_name: Optional agency name (defaults to email domain)
        is_test: If True, marks the agency as a test agency
        
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
        is_test=is_test,  # Mark as test agency if applicable
    )
    db.add(agency)
    await db.flush()

    # Apply RLS context so the membership insert passes tenant policy
    await apply_rls(db, agency.id)

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

    # NOTE: db.refresh() omitted here because RLS resets after commit.
    # The in-memory membership already has all fields we need (user_id,
    # agency_id, role, is_primary).  Downstream code (access-token creation)
    # uses only those fields, so refresh is unnecessary and would fail under
    # FORCE RLS when the new transaction lacks app.current_agency_id.

    access_token = create_access_token(
        user_id=user.id,
        agency_id=agency.id,
        role=membership.role,
    )
    refresh_token = create_refresh_token(user_id=user.id)
    
    logger.info("Signup complete: user=%s agency=%s is_test=%s", user.id, agency.id, is_test)
    
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
            "is_test": agency.is_test,
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

    membership = await _ensure_user_membership(db, user)

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

    membership = await _ensure_user_membership(db, user)
    await db.commit()

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


async def request_password_reset(db: AsyncSession, email: str) -> dict:
    """
    Generate a password reset token.

    The plain token is only returned in local development when both
    ENVIRONMENT=development and EXPOSE_RESET_TOKEN=1 are set.
    Otherwise the response is generic and does not reveal whether
    the email exists.

    Tokens are stored as SHA-256 hashes; the plain token is never
    persisted.

    Returns:
        dict with ok=True and a generic message. reset_token is
        included only in development when explicitly enabled.
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

    response = {
        "ok": True,
        "message": "If the email exists, a reset link has been sent",
    }

    if os.getenv("ENVIRONMENT", "development").lower() == "development" and os.getenv("EXPOSE_RESET_TOKEN") == "1":
        response["reset_token"] = plain_token

    return response


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


async def validate_workspace_code(
    db: AsyncSession,
    code: str,
) -> dict:
    """
    Validate a workspace invitation code without requiring authentication.

    Used by the /join/[code] page to show the agency name before signup.

    Returns:
        dict with valid, agency_name, agency_id, code_type — or raises ValueError.

    Design note: We return a consistent 404-style ValueError for any invalid code
    (not found, revoked, used) to avoid leaking whether a given code format exists.
    """
    result = await db.execute(
        select(WorkspaceCode)
        .where(WorkspaceCode.code == code)
        .where(WorkspaceCode.status == "active")
    )
    workspace_code = result.scalar_one_or_none()

    if not workspace_code:
        raise ValueError("Invalid or expired invitation code")

    agency_result = await db.execute(
        select(Agency).where(Agency.id == workspace_code.agency_id)
    )
    agency = agency_result.scalar_one_or_none()

    if not agency:
        raise ValueError("Invalid or expired invitation code")

    return {
        "valid": True,
        "agency_name": agency.name,
        "agency_id": agency.id,
        "code_type": workspace_code.code_type,
    }


# Role assigned to agents joining via invitation code.
# Owners/Admins can promote to SeniorAgent after onboarding review.
_CODE_TYPE_ROLE: dict[str, str] = {
    "internal": "junior_agent",
    "external": "junior_agent",
}


async def join_with_code(
    db: AsyncSession,
    code: str,
    email: str,
    password: str,
    name: Optional[str] = None,
) -> dict:
    """
    Create a new user and join an existing agency via a workspace invitation code.

    This is the agent onboarding path. Unlike signup(), it does NOT create a new agency.
    The invitation code determines which agency the new user joins and at which role.

    Codes are multi-use (reusable invitation links). They are not consumed on join;
    the owner must explicitly revoke a code to stop further joins. This matches the
    roadmap's "regeneratable" code model where old codes are invalidated by generating new ones.

    Role assignment:
        - Both internal and external codes start the joining agent at junior_agent.
        - Owners and Admins can promote via the team management panel.

    Returns:
        Same shape as signup() — user, agency, membership, access_token, refresh_token.

    Raises:
        ValueError: if email taken, password too short, or code invalid.
    """
    # 1. Validate code (same logic as validate_workspace_code to stay consistent)
    code_result = await db.execute(
        select(WorkspaceCode)
        .where(WorkspaceCode.code == code)
        .where(WorkspaceCode.status == "active")
    )
    workspace_code = code_result.scalar_one_or_none()

    if not workspace_code:
        raise ValueError("Invalid or expired invitation code")

    agency_result = await db.execute(
        select(Agency).where(Agency.id == workspace_code.agency_id)
    )
    agency = agency_result.scalar_one_or_none()

    if not agency:
        raise ValueError("Invalid or expired invitation code")

    # 2. Guard against duplicate email
    user_result = await db.execute(select(User).where(User.email == email))
    if user_result.scalar_one_or_none():
        raise ValueError("Email already registered")

    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters")

    # 3. Create user and membership
    user = User(
        email=email,
        password_hash=hash_password(password),
        name=name or email.split("@")[0],
    )
    db.add(user)
    await db.flush()  # get user.id before membership

    role = _CODE_TYPE_ROLE.get(workspace_code.code_type, "junior_agent")

    # Set RLS context before inserting into memberships (FORCE RLS protected)
    await apply_rls(db, agency.id)

    membership = Membership(
        user_id=user.id,
        agency_id=agency.id,
        role=role,
        is_primary=True,
    )
    db.add(membership)
    await db.commit()

    # NOTE: db.refresh() omitted after commit because RLS resets. The in-memory
    # user and membership objects already contain all fields needed downstream.

    access_token = create_access_token(
        user_id=user.id,
        agency_id=agency.id,
        role=role,
    )
    refresh_token = create_refresh_token(user_id=user.id)

    logger.info(
        "Agent joined via code: user=%s agency=%s role=%s code_type=%s",
        user.id, agency.id, role, workspace_code.code_type,
    )

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
