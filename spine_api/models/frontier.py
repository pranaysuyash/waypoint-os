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
from typing import Optional

from sqlalchemy import String, ForeignKey, DateTime, Float, Integer, JSON, Index, Numeric, Enum
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
    trip_id: Mapped[str] = mapped_column(String(36), nullable=False)  # Link to JSON trip ID for now
    
    task_type: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., 'transfer_verify'
    status: Mapped[str] = mapped_column(
        String(50), default="pending"
    )  # 'pending', 'executing', 'completed', 'failed', 'escalated'
    
    action_payload: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    autonomic_level: Mapped[int] = mapped_column(Integer, default=0)  # 0-4
    
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    agency: Mapped["Agency"] = relationship("Agency")

    __table_args__ = (
        Index("ix_ghost_workflows_agency_id", "agency_id"),
        Index("ix_ghost_workflows_trip_id", "trip_id"),
        Index("ix_ghost_workflows_status", "status"),
    )


class EmotionalStateLog(Base):
    """High-fidelity tracking of traveler sentiment and anxiety monitoring."""
    __tablename__ = "emotional_state_logs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    traveler_id: Mapped[str] = mapped_column(String(36), nullable=False)
    trip_id: Mapped[str] = mapped_column(String(36), nullable=False)
    
    sentiment_score: Mapped[float] = mapped_column(Float, default=0.5)  # 0.0 to 1.0
    anxiety_trigger: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    mitigation_action_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    recovery_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        Index("ix_emotional_state_logs_trip_id", "trip_id"),
        Index("ix_emotional_state_logs_traveler_id", "traveler_id"),
    )


class IntelligencePoolRecord(Base):
    """Anonymized industry-wide risk data for federated intelligence."""
    __tablename__ = "intelligence_pool"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    incident_type: Mapped[str] = mapped_column(String(100), nullable=False)
    anonymized_data: Mapped[dict] = mapped_column(JSON, default=dict)
    
    severity: Mapped[int] = mapped_column(Integer, default=1)  # 1-5
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    
    source_agency_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    verified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        Index("ix_intelligence_pool_incident_type", "incident_type"),
        Index("ix_intelligence_pool_severity", "severity"),
    )


class LegacyAspiration(Base):
    """Decadal travel goal persistence for life-mapping."""
    __tablename__ = "legacy_aspirations"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    traveler_id: Mapped[str] = mapped_column(String(36), nullable=False)
    agency_id: Mapped[str] = mapped_column(
        ForeignKey("agencies.id", ondelete="CASCADE"), nullable=False
    )
    
    goal_title: Mapped[str] = mapped_column(String(255), nullable=False)
    target_year: Mapped[int] = mapped_column(Integer, nullable=False)
    
    fitness_window_age: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    estimated_cost: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    
    status: Mapped[str] = mapped_column(
        String(50), default="aspirational"
    )  # 'aspirational', 'planning', 'executed', 'cancelled'
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    agency: Mapped["Agency"] = relationship("Agency")

    __table_args__ = (
        Index("ix_legacy_aspirations_traveler_id", "traveler_id"),
        Index("ix_legacy_aspirations_agency_id", "agency_id"),
    )
