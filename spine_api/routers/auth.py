"""
Auth router — signup, login, logout, me, refresh, password reset endpoints.

Token delivery strategy (Cookie-Only Transport):
- Access token: httpOnly cookie, path="/", SameSite=Lax, 15-minute TTL
- Refresh token: httpOnly cookie, path="/api/auth", SameSite=Lax, 7-day TTL

No tokens are returned in the JSON response body.
This eliminates XSS-based token theft vectors and enables
the Next.js middleware to authenticate page-route requests
without client-side JavaScript.

Rate limits (environment-aware, slowapi):
- POST /signup: 5/min per IP
- POST /login: 10/min per IP
- POST /refresh: 30/min per IP
- POST /request-password-reset: 3/min per IP
- POST /confirm-password-reset: 5/min per IP
Global default: 60/min (prod) / 1000/min (dev/test)
"""

import logging

import os

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession

from spine_api.core.database import get_db
from spine_api.core.auth import get_current_user, get_current_membership
from spine_api.core.rate_limiter import limiter
from spine_api.core.audit import audit_logger, AuditContext, AuditAction
from spine_api.models.tenant import User, Membership, PasswordResetToken
from spine_api.services.auth_service import (
    signup as signup_service,
    login as login_service,
    refresh_access_token,
    request_password_reset,
    confirm_password_reset,
    validate_workspace_code,
    join_with_code,
)

logger = logging.getLogger("spine_api.auth")

# ---------------------------------------------------------------------------
# Call-time env helpers — read at function time, not import time —
# so tests can change ENVIRONMENT without importlib.reload().
# ---------------------------------------------------------------------------

def _is_cookie_secure() -> bool:
    return os.environ.get("ENVIRONMENT", "development").lower() == "production"


# Access token: short-lived, sent on every request
_ACCESS_TTL_SECONDS = 15 * 60  # 15 minutes

# Refresh token: long-lived, only sent to /api/auth/*
_REFRESH_TTL_SECONDS = 7 * 24 * 60 * 60  # 7 days

router = APIRouter(prefix="/api/auth", tags=["auth"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    """Set both access_token and refresh_token as httpOnly cookies."""
    is_secure = _is_cookie_secure()
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=is_secure,
        samesite="lax",
        max_age=_ACCESS_TTL_SECONDS,
        path="/",
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=is_secure,
        samesite="lax",
        max_age=_REFRESH_TTL_SECONDS,
        path="/api/auth",
    )


def _clear_auth_cookies(response: Response) -> None:
    """Delete both auth cookies."""
    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="refresh_token", path="/api/auth")


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    name: str | None = Field(default=None, max_length=255)
    agency_name: str | None = Field(default=None, max_length=255)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    ok: bool = True
    user: dict
    agency: dict
    membership: dict


class MeResponse(BaseModel):
    ok: bool = True
    user: dict
    agency: dict
    membership: dict


class RefreshResponse(BaseModel):
    ok: bool = True


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)


class JoinRequest(BaseModel):
    workspace_code: str = Field(min_length=1, max_length=64)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    name: str | None = Field(default=None, max_length=255)


# ---------------------------------------------------------------------------
# Auth endpoints
# ---------------------------------------------------------------------------

@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def post_signup(
    request: Request,
    response: Response,
    signup_req: SignupRequest,
    audit: AuditContext = Depends(audit_logger()),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new user, agency, and membership.
    Sets httpOnly cookies for auth.

    Test users: Email ending with '@test.com' will get mock data seeded,
    but only in development. In production, @test.com signups are treated
    as normal accounts with no test data.
    """
    is_dev = os.environ.get("ENVIRONMENT", "development").lower() == "development"
    is_test = (
        is_dev
        and signup_req.email.lower().endswith("@test.com")
    )

    try:
        result = await signup_service(
            db=db,
            email=signup_req.email,
            password=signup_req.password,
            name=signup_req.name,
            agency_name=signup_req.agency_name,
            is_test=is_test,
        )
    except ValueError as e:
        await audit.log(AuditAction.LOGIN_FAILED, resource_type="user", changes={"email": signup_req.email, "reason": str(e)})
        raise HTTPException(status_code=400, detail=str(e))

    _set_auth_cookies(response, result["access_token"], result["refresh_token"])

    await audit.log(
        AuditAction.CREATE,
        resource_type="user",
        resource_id=result["user"]["id"],
        changes={"email": signup_req.email, "agency": result["agency"]["name"]},
    )

    return AuthResponse(
        ok=True,
        user=result["user"],
        agency=result["agency"],
        membership=result["membership"],
    )


@router.post("/login", response_model=AuthResponse)
@limiter.limit("10/minute")
async def post_login(
    request: Request,
    response: Response,
    login_req: LoginRequest,
    audit: AuditContext = Depends(audit_logger()),
    db: AsyncSession = Depends(get_db),
):
    try:
        result = await login_service(db=db, email=login_req.email, password=login_req.password)
    except ValueError as e:
        await audit.log(AuditAction.LOGIN_FAILED, resource_type="user", changes={"email": login_req.email, "reason": str(e)})
        raise HTTPException(status_code=401, detail=str(e))

    _set_auth_cookies(response, result["access_token"], result["refresh_token"])

    await audit.log(AuditAction.LOGIN, resource_type="user", resource_id=result["user"]["id"])

    return AuthResponse(
        ok=True,
        user=result["user"],
        agency=result["agency"],
        membership=result["membership"],
    )


@router.post("/logout")
async def post_logout(
    response: Response,
    membership: Membership = Depends(get_current_membership),
    audit: AuditContext = Depends(audit_logger()),
):
    _clear_auth_cookies(response)
    await audit.log(AuditAction.LOGOUT, resource_type="session")
    return {"ok": True}


@router.get("/me", response_model=MeResponse)
async def get_me(
    user: User = Depends(get_current_user),
    membership: Membership = Depends(get_current_membership),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select
    from spine_api.models.tenant import Agency

    result = await db.execute(select(Agency).where(Agency.id == membership.agency_id))
    agency = result.scalar_one_or_none()

    if not agency:
        raise HTTPException(status_code=404, detail="Agency not found")

    return MeResponse(
        ok=True,
        user={
            "id": user.id,
            "email": user.email,
            "name": user.name,
        },
        agency={
            "id": agency.id,
            "name": agency.name,
            "slug": agency.slug,
            "logo_url": agency.logo_url,
        },
        membership={
            "role": membership.role,
            "is_primary": membership.is_primary,
        },
    )


@router.post("/refresh", response_model=RefreshResponse)
@limiter.limit("30/minute")
async def post_refresh(request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    """
    Refresh the access token using the refresh_token cookie.

    The refresh_token is read from the cookie jar (httpOnly, path=/api/auth).
    Clients do NOT need to send it in the request body — the browser
    automatically includes it because the path matches.
    """
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(status_code=401, detail="No refresh token provided")

    try:
        result = await refresh_access_token(db=db, refresh_token_str=token)
    except ValueError as e:
        # If refresh fails, clear all cookies to force re-login
        _clear_auth_cookies(response)
        raise HTTPException(status_code=401, detail=str(e))

    _set_auth_cookies(response, result["access_token"], result["refresh_token"])

    return RefreshResponse(ok=True)


# ---------------------------------------------------------------------------
# PASSWORD RESET
# ---------------------------------------------------------------------------

@router.post("/request-password-reset")
@limiter.limit("3/minute")
async def post_request_password_reset(
    request: Request,
    reset_req: PasswordResetRequest,
    audit: AuditContext = Depends(audit_logger()),
    db: AsyncSession = Depends(get_db),
):
    result = await request_password_reset(db=db, email=reset_req.email)
    await audit.log(
        AuditAction.PASSWORD_RESET_REQUEST,
        resource_type="user",
        changes={"email": reset_req.email},
    )
    response = {
        "ok": True,
        "message": "If the email exists, a reset link has been sent",
    }
    if (
        os.environ.get("ENVIRONMENT", "development").lower() == "development"
        and os.environ.get("EXPOSE_RESET_TOKEN") == "1"
        and isinstance(result, dict)
        and "reset_token" in result
    ):
        response["reset_token"] = result["reset_token"]
    return response


@router.post("/confirm-password-reset")
@limiter.limit("5/minute")
async def post_confirm_password_reset(
    request: Request,
    confirm_req: PasswordResetConfirm,
    audit: AuditContext = Depends(audit_logger()),
    db: AsyncSession = Depends(get_db),
):
    try:
        result = await confirm_password_reset(
            db=db, token=confirm_req.token, new_password=confirm_req.new_password
        )
        await audit.log(
            AuditAction.PASSWORD_RESET_CONFIRM,
            resource_type="user",
            changes={"success": True},
        )
        return result
    except ValueError as e:
        await audit.log(
            AuditAction.PASSWORD_RESET_CONFIRM,
            resource_type="user",
            changes={"success": False, "reason": str(e)},
        )
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------------------------
# Workspace code — validate and join
# ---------------------------------------------------------------------------

@router.get("/validate-code/{code}")
async def get_validate_code(
    code: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Validate a workspace invitation code without requiring authentication.

    Used by the /join/[code] page to display the agency name before the user
    commits to signing up. Returns 404 for any invalid/expired/revoked code
    to avoid leaking information about code existence.

    This endpoint is intentionally unauthenticated — it is listed under /api/auth/
    which is a PUBLIC_PREFIX in the auth middleware, so no JWT is required.
    """
    try:
        result = await validate_workspace_code(db=db, code=code)
        return result
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation code not found")


@router.post("/join", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def post_join(
    request: Request,
    response: Response,
    join_req: JoinRequest,
    audit: AuditContext = Depends(audit_logger()),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new user account and join an existing agency via a workspace invitation code.

    This is the agent onboarding path — distinct from /signup which creates a new agency.
    On success, sets the same httpOnly auth cookies as /signup and /login.

    Codes are multi-use (reusable invitation links). The owner revokes a code to prevent
    further joins. Role defaults to junior_agent regardless of code_type; the owner
    promotes agents to senior_agent after onboarding review.
    """
    try:
        result = await join_with_code(
            db=db,
            code=join_req.workspace_code,
            email=join_req.email,
            password=join_req.password,
            name=join_req.name,
        )
    except ValueError as e:
        await audit.log(
            AuditAction.LOGIN_FAILED,
            resource_type="user",
            changes={"email": join_req.email, "reason": str(e)},
        )
        # Use 400 for email-taken / validation errors; 404 for bad code
        code_str = str(e)
        status_code = (
            status.HTTP_404_NOT_FOUND
            if "invitation code" in code_str
            else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(status_code=status_code, detail=code_str)

    _set_auth_cookies(response, result["access_token"], result["refresh_token"])

    await audit.log(
        AuditAction.CREATE,
        resource_type="user",
        resource_id=result["user"]["id"],
        changes={
            "email": join_req.email,
            "agency": result["agency"]["name"],
            "role": result["membership"]["role"],
            "via": "workspace_code",
        },
    )

    return AuthResponse(
        ok=True,
        user=result["user"],
        agency=result["agency"],
        membership=result["membership"],
    )