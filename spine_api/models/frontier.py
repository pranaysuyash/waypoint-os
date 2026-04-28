"""
Frontier Features Models for Waypoint OS.

This module contains SQLAlchemy models for advanced agentic features:
- GhostWorkflow: Autonomic task execution tracking
- EmotionalStateLog: Traveler sentiment and anxiety monitoring
- IntelligencePoolRecord: Federated industry risk data
- LegacyAspiration: Long-term travel goal persistence (Life-mapping)
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    String, ForeignKey, DateTime, Float, Integer, JSON, Index,
    Numeric, CheckConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from spine_api.core.database import Base


class GhostWorkflow(Base):
    """Tracks silent, automated tasks performed by the Ghost Concierge."""
    __tablename__ = "ghost_workflows"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    agency_id: Mapped[str] = mapped_column(
        ForeignKey("agencies.id", ondelete="CASCADE"), nullable=False
    )
    # TODO(frontier): replace loose trip_id with ForeignKey once trips are normalized into SQL.
    trip_id: Mapped[str] = mapped_column(String(36), nullable=False)

    task_type: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)

    action_payload: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    autonomic_level: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
        onupdate=lambda: datetime.now(timezone.utc),
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    agency: Mapped["Agency"] = relationship("Agency")

    __table_args__ = (
        Index("ix_ghost_workflows_agency_id", "agency_id"),
        Index("ix_ghost_workflows_trip_id", "trip_id"),
        Index("ix_ghost_workflows_status", "status"),
        CheckConstraint(
            "status IN ('pending', 'executing', 'completed', 'failed', 'escalated')",
            name="ck_ghost_workflows_status",
        ),
        CheckConstraint(
            "autonomic_level BETWEEN 0 AND 4",
            name="ck_ghost_workflows_autonomic_level",
        ),
    )


class EmotionalStateLog(Base):
    """High-fidelity tracking of traveler sentiment and anxiety monitoring."""
    __tablename__ = "emotional_state_logs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    agency_id: Mapped[str] = mapped_column(
        ForeignKey("agencies.id", ondelete="CASCADE"), nullable=False
    )
    # TODO(frontier): replace loose traveler_id with ForeignKey once travelers are normalized into SQL.
    traveler_id: Mapped[str] = mapped_column(String(36), nullable=False)
    # TODO(frontier): replace loose trip_id with ForeignKey once trips are normalized into SQL.
    trip_id: Mapped[str] = mapped_column(String(36), nullable=False)

    sentiment_score: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    # Privacy note: anxiety_trigger may contain sensitive traveler data. Ensure
    # access controls and retention policies are in place before production use.
    anxiety_trigger: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    mitigation_action_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    recovery_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    agency: Mapped["Agency"] = relationship("Agency")

    __table_args__ = (
        Index("ix_emotional_state_logs_agency_id", "agency_id"),
        Index("ix_emotional_state_logs_trip_id", "trip_id"),
        Index("ix_emotional_state_logs_traveler_id", "traveler_id"),
        CheckConstraint(
            "sentiment_score >= 0 AND sentiment_score <= 1",
            name="ck_emotional_state_logs_sentiment_score",
        ),
    )


class IntelligencePoolRecord(Base):
    """Anonymized industry-wide risk data for federated intelligence."""
    __tablename__ = "intelligence_pool"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    incident_type: Mapped[str] = mapped_column(String(100), nullable=False)
    # anonymized_data must be sanitized before persistence. Do not store raw traveler,
    # agency, booking, email, phone, or location-identifying data here.
    anonymized_data: Mapped[dict] = mapped_column(JSON, default=dict)

    severity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)

    # Privacy note: source_agency_hash is a stable pseudonymous identifier.
    # Ensure it cannot be reverse-mapped to a specific agency.
    source_agency_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    verified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    __table_args__ = (
        Index("ix_intelligence_pool_incident_type", "incident_type"),
        Index("ix_intelligence_pool_severity", "severity"),
        CheckConstraint(
            "severity BETWEEN 1 AND 5",
            name="ck_intelligence_pool_severity",
        ),
        CheckConstraint(
            "confidence >= 0 AND confidence <= 1",
            name="ck_intelligence_pool_confidence",
        ),
    )


class LegacyAspiration(Base):
    """Decadal travel goal persistence for life-mapping."""
    __tablename__ = "legacy_aspirations"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    # TODO(frontier): replace loose traveler_id with ForeignKey once travelers are normalized into SQL.
    traveler_id: Mapped[str] = mapped_column(String(36), nullable=False)
    agency_id: Mapped[str] = mapped_column(
        ForeignKey("agencies.id", ondelete="CASCADE"), nullable=False
    )

    goal_title: Mapped[str] = mapped_column(String(255), nullable=False)
    target_year: Mapped[int] = mapped_column(Integer, nullable=False)

    fitness_window_age: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    estimated_cost: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)

    status: Mapped[str] = mapped_column(String(50), default="aspirational", nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
        onupdate=lambda: datetime.now(timezone.utc),
    )

    agency: Mapped["Agency"] = relationship("Agency")

    __table_args__ = (
        Index("ix_legacy_aspirations_traveler_id", "traveler_id"),
        Index("ix_legacy_aspirations_agency_id", "agency_id"),
        CheckConstraint(
            "status IN ('aspirational', 'planning', 'executed', 'cancelled')",
            name="ck_legacy_aspirations_status",
        ),
    )
