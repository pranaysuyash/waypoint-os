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

from sqlalchemy import String, ForeignKey, DateTime, Boolean, Integer, Float, Text, JSON, Index
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
    is_test: Mapped[bool] = mapped_column(Boolean, default=False)
    jurisdiction: Mapped[str] = mapped_column(
        String(10), default="other"
    )
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


class BookingCollectionToken(Base):
    """Time-limited, single-use tokens for customer booking-data collection."""
    __tablename__ = "booking_collection_tokens"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    trip_id: Mapped[str] = mapped_column(
        ForeignKey("trips.id", ondelete="CASCADE"), nullable=False
    )
    agency_id: Mapped[str] = mapped_column(
        ForeignKey("agencies.id", ondelete="CASCADE"), nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active")
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[str] = mapped_column(String(36), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    trip: Mapped["Trip"] = relationship("Trip")
    agency: Mapped["Agency"] = relationship("Agency")

    __table_args__ = (
        Index("ix_bct_token_hash", "token_hash"),
        Index("ix_bct_trip_id", "trip_id"),
    )


class BookingDocument(Base):
    """Uploaded travel documents — passports, visas, tickets, insurance, etc.

    Documents are binary evidence awaiting agent review. They are NOT trusted
    execution data and do not affect booking_ready. Access only through
    dedicated endpoints — never inlined into trip hydration.
    """
    __tablename__ = "booking_documents"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    trip_id: Mapped[str] = mapped_column(
        ForeignKey("trips.id", ondelete="CASCADE"), nullable=False
    )
    agency_id: Mapped[str] = mapped_column(
        ForeignKey("agencies.id", ondelete="CASCADE"), nullable=False
    )
    traveler_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    uploaded_by_type: Mapped[str] = mapped_column(String(20), nullable=False)  # agent | customer
    uploaded_by_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    collection_token_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("booking_collection_tokens.id", ondelete="SET NULL"), nullable=True
    )
    # No original_filename stored — hash + extension only.
    filename_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    filename_ext: Mapped[str] = mapped_column(String(10), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    document_type: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(20), server_default="pending_review")
    scan_status: Mapped[str] = mapped_column(String(20), server_default="skipped")
    review_notes_present: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewed_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    storage_delete_status: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    trip: Mapped["Trip"] = relationship("Trip")
    agency: Mapped["Agency"] = relationship("Agency")
    collection_token: Mapped[Optional["BookingCollectionToken"]] = relationship("BookingCollectionToken")

    __table_args__ = (
        Index("ix_bd_trip_id", "trip_id"),
        Index("ix_bd_agency_id", "agency_id"),
        Index("ix_bd_status", "status"),
    )


class DocumentExtraction(Base):
    __tablename__ = "document_extractions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id: Mapped[str] = mapped_column(
        ForeignKey("booking_documents.id", ondelete="CASCADE"),
        unique=True, nullable=False,
    )
    trip_id: Mapped[str] = mapped_column(ForeignKey("trips.id", ondelete="CASCADE"), nullable=False)
    agency_id: Mapped[str] = mapped_column(ForeignKey("agencies.id", ondelete="CASCADE"), nullable=False)

    # Encrypted blob — Fernet-encrypted JSON of extracted PII fields
    # Shape: {"full_name": "...", "passport_number": "...", ...}
    extracted_fields_encrypted: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Plaintext indicators for queryability — no PII values
    fields_present: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    field_count: Mapped[int] = mapped_column(Integer, default=0)

    # Confidence scores — numbers only, no PII
    confidence_scores: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    overall_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Status: pending_review → applied / rejected / failed (terminal)
    status: Mapped[str] = mapped_column(String(20), server_default="pending_review")
    extracted_by: Mapped[str] = mapped_column(String(20), server_default="noop_extractor")

    # Provider metadata (Phase 4D)
    provider_name: Mapped[str] = mapped_column(String(30), server_default="noop_extractor")
    model_name: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    prompt_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    completion_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    total_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    cost_estimate_usd: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    error_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    error_summary: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    confidence_method: Mapped[str] = mapped_column(String(30), server_default="model")

    # Review metadata
    reviewed_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    document: Mapped["BookingDocument"] = relationship("BookingDocument")
    trip: Mapped["Trip"] = relationship("Trip")
    agency: Mapped["Agency"] = relationship("Agency")

    __table_args__ = (
        Index("ix_de_document_id", "document_id", unique=True),
        Index("ix_de_trip_id", "trip_id"),
        Index("ix_de_status", "status"),
        Index("ix_de_current_attempt_id", "current_attempt_id"),
    )

    # Phase 4E: attempt tracking columns
    current_attempt_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    run_count: Mapped[int] = mapped_column(Integer, default=0)
    page_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)


class DocumentExtractionAttempt(Base):
    """One attempt row per provider call. Preserves full fallback history."""
    __tablename__ = "document_extraction_attempts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    extraction_id: Mapped[str] = mapped_column(
        ForeignKey("document_extractions.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    run_number: Mapped[int] = mapped_column(Integer, nullable=False)
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    fallback_rank: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Provider details for this specific call
    provider_name: Mapped[str] = mapped_column(String(30), nullable=False)
    model_name: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Timing and usage
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    prompt_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    completion_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    total_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    cost_estimate_usd: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Result
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # "success" or "failed"
    error_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    error_summary: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # Encrypted fields — NULL for failed attempts, populated only for success
    extracted_fields_encrypted: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    fields_present: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    field_count: Mapped[int] = mapped_column(Integer, default=0)
    confidence_scores: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    overall_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    confidence_method: Mapped[str] = mapped_column(String(30), server_default="model")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
    )
