"""
Trip data models for Waypoint OS.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import String, ForeignKey, DateTime, JSON, Index, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from spine_api.core.database import Base


class Trip(Base):
    """A trip object representing the canonical state of a travel request."""
    __tablename__ = "trips"
    
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    run_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    agency_id: Mapped[str] = mapped_column(
        ForeignKey("agencies.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    
    source: Mapped[str] = mapped_column(String(100), default="unknown")
    status: Mapped[str] = mapped_column(String(50), default="new")
    stage: Mapped[str] = mapped_column(String(50), default="discovery", nullable=False)
    
    # Intake fields
    follow_up_due_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    party_composition: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    pace_preference: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    date_year_confidence: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    lead_source: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    activity_provenance: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    trip_priorities: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    date_flexibility: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Spine output fields
    extracted: Mapped[dict] = mapped_column(JSON, default=dict)
    validation: Mapped[dict] = mapped_column(JSON, default=dict)
    decision: Mapped[dict] = mapped_column(JSON, default=dict)
    strategy: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    traveler_bundle: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    internal_bundle: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    safety: Mapped[dict] = mapped_column(JSON, default=dict)
    frontier_result: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    fees: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Metadata
    raw_input: Mapped[dict] = mapped_column(JSON, default=dict)
    analytics: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc)
    )

    agency: Mapped["Agency"] = relationship("Agency")
    user: Mapped["User"] = relationship("User")

    __table_args__ = (
        Index("ix_trips_agency_id", "agency_id"),
        Index("ix_trips_status", "status"),
        Index("ix_trips_created_at", "created_at"),
    )
