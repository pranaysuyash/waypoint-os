"""
Auth router — signup, login, logout, me, refresh endpoints.

Token delivery strategy:
- Access token returned in response body (frontend stores in localStorage)
- Refresh token set as httpOnly cookie for security
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.auth import get_current_user, get_current_membership
from models.tenant import User, Membership
from services.auth_service import signup as signup_service, login as login_service, refresh_access_token

logger = logging.getLogger("spine-api.auth")

router = APIRouter(prefix="/api/auth", tags=["auth"])


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    name: str | None = Field(default=None, max_length=255)
    agency_name: str | None = Field(default=None, max_length=255)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str | None = None


class AuthResponse(BaseModel):
    ok: bool = True
    user: dict
    agency: dict
    membership: dict
    access_token: str


class MeResponse(BaseModel):
    ok: bool = True
    user: dict
    agency: dict
    membership: dict


class RefreshResponse(BaseModel):
    ok: bool = True
    access_token: str


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def post_signup(request: SignupRequest, response: Response, db: AsyncSession = Depends(get_db)):
    try:
        result = await signup_service(
            db=db,
            email=request.email,
            password=request.password,
            name=request.name,
            agency_name=request.agency_name,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    response.set_cookie(
        key="refresh_token",
        value=result["refresh_token"],
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=7 * 24 * 60 * 60,
        path="/api/auth",
    )

    return AuthResponse(
        ok=True,
        user=result["user"],
        agency=result["agency"],
        membership=result["membership"],
        access_token=result["access_token"],
    )


@router.post("/login", response_model=AuthResponse)
async def post_login(request: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)):
    try:
        result = await login_service(db=db, email=request.email, password=request.password)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

    response.set_cookie(
        key="refresh_token",
        value=result["refresh_token"],
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=7 * 24 * 60 * 60,
        path="/api/auth",
    )

    return AuthResponse(
        ok=True,
        user=result["user"],
        agency=result["agency"],
        membership=result["membership"],
        access_token=result["access_token"],
    )


@router.post("/logout")
async def post_logout(response: Response):
    response.delete_cookie(key="refresh_token", path="/api/auth")
    return {"ok": True}


@router.get("/me", response_model=MeResponse)
async def get_me(
    user: User = Depends(get_current_user),
    membership: Membership = Depends(get_current_membership),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select
    from models.tenant import Agency

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
async def post_refresh(request: RefreshRequest, response: Response, db: AsyncSession = Depends(get_db)):
    token = request.refresh_token
    if not token:
        raise HTTPException(status_code=401, detail="No refresh token provided")

    try:
        result = await refresh_access_token(db=db, refresh_token_str=token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

    response.set_cookie(
        key="refresh_token",
        value=result["refresh_token"],
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=7 * 24 * 60 * 60,
        path="/api/auth",
    )

    return RefreshResponse(ok=True, access_token=result["access_token"])
