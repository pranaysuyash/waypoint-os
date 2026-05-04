"""
Routing state model for trip assignment.

TripRoutingState tracks who owns a trip at any point in time and the
history of handoffs. One row per trip; updated in place as the state
machine transitions. handoff_history is an append-only JSON log.

State machine:
  unassigned
    → assigned        (assign / claim)
    → escalated       (escalate from assigned)
    → reassigned      (reassign from any non-unassigned state; resets to assigned with new owner)
    → returned        (reviewer sends back for changes; back to assigned)

The "returned" state uses assigned as the operational state — the reviewer
note is stored in the most recent handoff_history entry. This keeps the
primary UI simple: unassigned or assigned are the two main operator views.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import String, ForeignKey, DateTime, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column

from spine_api.core.database import Base


# Valid status values — used by the service layer for validation.
ROUTING_STATUSES = frozenset({
    "unassigned",
    "assigned",
    "escalated",
    "reassigned",
    "returned",
})


class TripRoutingState(Base):
    """Operational routing state for a trip."""

    __tablename__ = "trip_routing_states"
    __table_args__ = (
        Index("ix_routing_trip_id", "trip_id"),
        Index("ix_routing_agency_id", "agency_id"),
        Index("ix_routing_assignee", "primary_assignee_id"),
        Index("ix_routing_status", "status"),
        {"extend_existing": True},
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    trip_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    agency_id: Mapped[str] = mapped_column(
        ForeignKey("agencies.id"), nullable=False
    )

    primary_assignee_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    reviewer_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    escalation_owner_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )

    status: Mapped[str] = mapped_column(String(50), default="unassigned", nullable=False)

    assigned_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    escalated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Append-only log: [{"action", "from_user_id", "to_user_id", "by_user_id", "reason", "at"}]
    handoff_history: Mapped[list] = mapped_column(JSON, default=list, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
