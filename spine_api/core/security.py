"""
Security utilities for Waypoint OS.

Provides:
- Password hashing and verification (bcrypt)
- JWT token creation and validation
"""

import os
import uuid as _uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

import bcrypt
import jwt

from spine_api.core.env import load_project_env

load_project_env()

# JWT configuration
JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET:
    raise RuntimeError(
        "JWT_SECRET is required. Set it in the environment before starting the API."
    )
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 0.25  # 15 minutes, aligned with cookie max_age in auth.py:52
REFRESH_TOKEN_EXPIRE_DAYS = 7


def hash_password(plain_password: str) -> str:
    """Hash a plain text password using bcrypt."""
    password_bytes = plain_password.encode("utf-8")
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain text password against a bcrypt hash."""
    password_bytes = plain_password.encode("utf-8")
    hash_bytes = hashed_password.encode("utf-8")
    return bcrypt.checkpw(password_bytes, hash_bytes)


def create_access_token(
    user_id: str,
    agency_id: str,
    role: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a JWT access token.

    Payload:
        sub: user_id
        agency_id: primary agency id
        role: user's role in the agency
        iat: issued at
        exp: expiration
        type: "access"
    """
    if expires_delta is None:
        expires_delta = timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)

    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "agency_id": agency_id,
        "role": role,
        "iat": now,
        "exp": now + expires_delta,
        "type": "access",
    }

    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token


def create_refresh_token(user_id: str) -> str:
    """Create a JWT refresh token with longer expiry and a unique JTI."""
    now = datetime.now(timezone.utc)
    jti = str(_uuid.uuid4())
    payload = {
        "sub": user_id,
        "jti": jti,
        "iat": now,
        "exp": now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        "type": "refresh",
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """
    Decode and validate a JWT token.
    Raises:
        jwt.ExpiredSignatureError: if token is expired
        jwt.InvalidTokenError: if token is invalid
    """
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])


def decode_token_safe(token: str) -> Optional[dict]:
    """
    Safely decode a JWT token. Returns None on any error.
    Use this when you don't want exceptions (e.g., optional auth).
    """
    try:
        return decode_token(token)
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None

def revoke_refresh_token_jti(jti: str) -> None:
    """Record a revoked refresh token JTI.

    This is a synchronous helper that returns the JTI for the caller
    to persist. The actual DB write happens in the auth router/service
    layer which has access to the async session.
    """
    # No-op placeholder — actual persistence is in auth_service.
    pass


def get_token_jti(token: str) -> Optional[str]:
    """Extract the JTI from a JWT token without validation."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM], options={"verify_exp": False})
        return payload.get("jti")
    except (jwt.InvalidTokenError, Exception):
        return None
