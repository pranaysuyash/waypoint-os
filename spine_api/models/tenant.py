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
    agency_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("agencies.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    trip_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("trips.id", ondelete="CASCADE"),
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


# ---------------------------------------------------------------------------
# Booking task constants
# ---------------------------------------------------------------------------

TASK_STATUSES = (
    "not_started", "blocked", "ready", "in_progress",
    "waiting_on_customer", "completed", "cancelled",
)

TASK_TYPES = (
    "verify_traveler_details", "verify_passport", "verify_visa", "verify_insurance",
    "confirm_flights", "confirm_hotels", "collect_payment_proof",
    "send_final_confirmation", "custom",
)

TASK_SOURCES = (
    "system_suggested", "agent_created", "readiness_generated",
    "document_generated", "extraction_generated",
)

TASK_PRIORITIES = ("low", "medium", "high", "critical")

BLOCKER_CODES = (
    "missing_booking_data", "missing_document", "missing_extraction",
    "extraction_not_reviewed", "document_not_accepted",
    "missing_passport_field", "missing_visa_field", "missing_insurance_field",
    "manual_block",
)

VALID_TRANSITIONS: dict[str, set[str]] = {
    "not_started": {"ready", "blocked", "cancelled"},
    "blocked": {"ready", "cancelled"},
    "ready": {"in_progress", "blocked", "cancelled"},
    "in_progress": {"completed", "waiting_on_customer", "cancelled"},
    "waiting_on_customer": {"in_progress", "cancelled"},
    "completed": set(),
    "cancelled": set(),
}

TASK_TITLE_TEMPLATES: dict[str, str] = {
    "verify_traveler_details": "Verify traveler details for Traveler {ordinal}",
    "verify_passport": "Verify passport for Traveler {ordinal}",
    "verify_visa": "Verify visa for Traveler {ordinal}",
    "verify_insurance": "Verify insurance for Traveler {ordinal}",
    "confirm_flights": "Confirm flights",
    "confirm_hotels": "Confirm hotels",
    "collect_payment_proof": "Collect payment proof",
    "send_final_confirmation": "Send final confirmation",
}


class BookingTask(Base):
    """A booking execution task for a trip."""
    __tablename__ = "booking_tasks"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    trip_id: Mapped[str] = mapped_column(String(36), nullable=False)
    agency_id: Mapped[str] = mapped_column(
        ForeignKey("agencies.id", ondelete="CASCADE"), nullable=False
    )

    task_type: Mapped[str] = mapped_column(String(40), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="not_started")
    priority: Mapped[str] = mapped_column(String(20), nullable=False, server_default="medium")

    owner_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    due_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    blocker_code: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    blocker_refs: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    source: Mapped[str] = mapped_column(String(30), nullable=False, server_default="agent_created")
    generation_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    created_by: Mapped[str] = mapped_column(String(36), nullable=False)
    completed_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index("ix_bt_trip_id", "trip_id"),
        Index("ix_bt_agency_id", "agency_id"),
        Index("ix_bt_status", "status"),
        Index("ix_bt_task_type", "task_type"),
        Index("ix_bt_trip_status", "trip_id", "status"),
        Index("ix_bt_generation_hash", "generation_hash"),
    )


# ---------------------------------------------------------------------------
# Confirmation constants
# ---------------------------------------------------------------------------

CONFIRMATION_TYPES = ("flight", "hotel", "insurance", "payment", "other")

CONFIRMATION_STATUSES = ("draft", "recorded", "verified", "voided")

CONFIRMATION_VALID_TRANSITIONS: dict[str, set[str]] = {
    "draft": {"recorded", "voided"},
    "recorded": {"verified", "voided"},
    "verified": {"voided"},
    "voided": set(),
}

NOTES_MAX_LENGTH = 2000

ALLOWED_EVIDENCE_REF_TYPES = frozenset({
    "booking_document", "document_extraction", "extraction_attempt", "booking_task",
})

# ---------------------------------------------------------------------------
# Execution event constants
# ---------------------------------------------------------------------------

EVENT_CATEGORIES = ("task", "confirmation", "document", "extraction")

TASK_EVENT_TYPES = (
    "task_created", "task_blocked", "task_ready", "task_started",
    "task_waiting", "task_completed", "task_cancelled",
)

CONFIRMATION_EVENT_TYPES = (
    "confirmation_created", "confirmation_updated", "confirmation_recorded",
    "confirmation_verified", "confirmation_voided",
)

DOCUMENT_EVENT_TYPES = (
    "document_uploaded",
    "document_accepted",
    "document_rejected",
    "document_deleted",
)

EXTRACTION_EVENT_TYPES = (
    "extraction_run_started",
    "extraction_run_completed",
    "extraction_run_failed",
    "extraction_applied",
    "extraction_rejected",
    "extraction_attempt_completed",
    "extraction_attempt_failed",
)

ALLOWED_SUBJECT_TYPES = (
    "booking_task",
    "booking_confirmation",
    "booking_document",
    "document_extraction",
    "document_extraction_attempt",
)

ALLOWED_ACTOR_TYPES = ("agent", "system")

ALLOWED_EVENT_SOURCES = (
    "agent_action",
    "system_generation",
    "reconciliation",
    "customer_submission",
)

ALLOWED_EVENT_METADATA_KEYS = frozenset({
    # Phase 5B
    "task_type", "confirmation_type", "document_type",
    "provider", "model", "blocker_code", "evidence_ref_count",
    # Phase 5C — document metadata
    "size_bytes", "mime_type", "uploaded_by_type", "scan_status",
    "review_notes_present", "storage_delete_status",
    # Phase 5C — extraction metadata
    "run_count", "attempt_count", "page_count",
    "overall_confidence", "field_count",
    "latency_ms", "cost_estimate_usd",
    "error_code",
    # Phase 5C — attempt metadata
    "run_number", "attempt_number", "fallback_rank",
    "fields_applied_count", "allow_overwrite",
})

FORBIDDEN_METADATA_PATTERNS = frozenset({
    "supplier_name", "confirmation_number", "notes", "traveler_name",
    "dob", "passport_number", "filename", "filename_hash", "sha256",
    "storage_key", "signed_url",
    "extracted_fields", "blocker_refs", "error_summary",
    "confidence_scores", "raw_error",
})


class BookingConfirmation(Base):
    """Durable booking confirmation record with encrypted private fields."""
    __tablename__ = "booking_confirmations"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    agency_id: Mapped[str] = mapped_column(
        ForeignKey("agencies.id", ondelete="CASCADE"), nullable=False
    )
    trip_id: Mapped[str] = mapped_column(String(36), nullable=False)
    task_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("booking_tasks.id", ondelete="SET NULL"), nullable=True
    )

    confirmation_type: Mapped[str] = mapped_column(String(20), nullable=False)
    confirmation_status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="draft"
    )

    # Encrypted private fields
    supplier_name_encrypted: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    confirmation_number_encrypted: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    notes_encrypted: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    external_ref_encrypted: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Queryable indicators (no decryption needed for list views)
    has_supplier: Mapped[bool] = mapped_column(Boolean, default=False)
    has_confirmation_number: Mapped[bool] = mapped_column(Boolean, default=False)
    notes_present: Mapped[bool] = mapped_column(Boolean, default=False)
    external_ref_present: Mapped[bool] = mapped_column(Boolean, default=False)

    # Typed evidence refs
    evidence_refs: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Lifecycle actors
    recorded_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    recorded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    verified_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    voided_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    voided_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    created_by: Mapped[str] = mapped_column(String(36), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index("ix_bc_trip_id", "trip_id"),
        Index("ix_bc_agency_id", "agency_id"),
        Index("ix_bc_task_id", "task_id"),
        Index("ix_bc_status", "confirmation_status"),
        Index("ix_bc_type", "confirmation_type"),
        Index("ix_bc_trip_status", "trip_id", "confirmation_status"),
    )


class ExecutionEvent(Base):
    """Durable execution event ledger — source of truth for timeline."""
    __tablename__ = "execution_events"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    agency_id: Mapped[str] = mapped_column(
        ForeignKey("agencies.id", ondelete="CASCADE"), nullable=False
    )
    trip_id: Mapped[str] = mapped_column(String(36), nullable=False)

    subject_type: Mapped[str] = mapped_column(String(30), nullable=False)
    subject_id: Mapped[str] = mapped_column(String(36), nullable=False)

    event_type: Mapped[str] = mapped_column(String(40), nullable=False)
    event_category: Mapped[str] = mapped_column(String(20), nullable=False)

    status_from: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    status_to: Mapped[str] = mapped_column(String(20), nullable=False)

    actor_type: Mapped[str] = mapped_column(String(20), nullable=False, server_default="system")
    actor_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)

    source: Mapped[str] = mapped_column(String(30), nullable=False, server_default="agent_action")

    event_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index("ix_ee_trip_id", "trip_id"),
        Index("ix_ee_agency_id", "agency_id"),
        Index("ix_ee_subject", "subject_type", "subject_id"),
        Index("ix_ee_category", "event_category"),
        Index("ix_ee_trip_created", "trip_id", "created_at"),
    )
