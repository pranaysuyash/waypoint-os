"""
Core tenant data models for Waypoint OS.

Entities:
- Agency: A travel agency tenant
- User: A human user of the system
- Membership: Junction linking users to agencies with a role
- WorkspaceCode: Invitation code for agents to join an agency
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy import String, ForeignKey, DateTime, Boolean, Integer, Text, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from spine_api.core.database import Base


class Agency(Base):
    """A travel agency tenant."""
    __tablename__ = "agencies"
    __table_args__ = {"extend_existing": True}
    
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    logo_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    plan: Mapped[str] = mapped_column(String(50), default="free")
    is_test: Mapped[bool] = mapped_column(Boolean, default=False)  # Flag for test agencies
    settings: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    memberships: Mapped[List["Membership"]] = relationship(
        "Membership", back_populates="agency", cascade="all, delete-orphan"
    )
    workspace_codes: Mapped[List["WorkspaceCode"]] = relationship(
        "WorkspaceCode", back_populates="agency", cascade="all, delete-orphan"
    )


class User(Base):
    """A human user of the system. Users can belong to multiple agencies."""
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    memberships: Mapped[List["Membership"]] = relationship(
        "Membership", back_populates="user", cascade="all, delete-orphan"
    )


class Membership(Base):
    """Junction table linking users to agencies with a role and operational config."""
    __tablename__ = "memberships"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    agency_id: Mapped[str] = mapped_column(
        ForeignKey("agencies.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    capacity: Mapped[int] = mapped_column(Integer, default=5)
    specializations: Mapped[Optional[dict]] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(
        String(50), default="active"
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    user: Mapped["User"] = relationship("User", back_populates="memberships")
    agency: Mapped["Agency"] = relationship("Agency", back_populates="memberships")

    __table_args__ = (
        Index("ix_memberships_agency_id", "agency_id"),
        Index("ix_memberships_user_id", "user_id"),
        Index("ix_memberships_user_agency", "user_id", "agency_id", unique=True),
    )


class WorkspaceCode(Base):
    """Invitation code for agents to join an agency workspace."""
    __tablename__ = "workspace_codes"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    agency_id: Mapped[str] = mapped_column(
        ForeignKey("agencies.id", ondelete="CASCADE"), nullable=False
    )
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    code_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # "internal" | "external"
    status: Mapped[str] = mapped_column(
        String(50), default="generated"
    )  # "generated" | "shared" | "active" | "inactive"
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    used_by: Mapped[Optional[str]] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    agency: Mapped["Agency"] = relationship("Agency", back_populates="workspace_codes")

    __table_args__ = (
        Index("ix_workspace_codes_agency_id", "agency_id"),
        Index("ix_workspace_codes_code", "code"),
    )


class PasswordResetToken(Base):
    """Password reset tokens — short-lived, single-use tokens sent via email."""
    __tablename__ = "password_reset_tokens"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False)  # SHA-256 hex of token
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    user: Mapped["User"] = relationship("User")

    __table_args__ = (
        Index("ix_password_reset_tokens_user_id", "user_id"),
        Index("ix_password_reset_tokens_expires_at", "expires_at"),
    )
