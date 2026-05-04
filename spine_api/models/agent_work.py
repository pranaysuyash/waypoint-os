"""Durable product-agent work lease records."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from spine_api.core.database import Base


class AgentWorkLease(Base):
    """One durable lease/idempotency row per agent work idempotency key."""

    __tablename__ = "agent_work_leases"
    __table_args__ = (
        Index("ix_agent_work_leases_agent_name", "agent_name"),
        Index("ix_agent_work_leases_trip_id", "trip_id"),
        Index("ix_agent_work_leases_status", "status"),
        Index("ix_agent_work_leases_leased_until", "leased_until"),
    )

    idempotency_key: Mapped[str] = mapped_column(String(500), primary_key=True)
    agent_name: Mapped[str] = mapped_column(String(120), nullable=False)
    trip_id: Mapped[str] = mapped_column(String(255), nullable=False)
    action: Mapped[str] = mapped_column(String(120), nullable=False)
    owner: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False)
    attempts: Mapped[int] = mapped_column(default=0, nullable=False)
    leased_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_reason: Mapped[str] = mapped_column(Text, default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
