"""
spine_api/models/agent_lease.py — Distributed Agent Lease Model.

Backs DurableAgentLeaseManager when SPINE_API_AGENT_LEASE_BACKEND=sql.
Ensures distributed mutual exclusion across multi-worker and multi-container deployments.
"""

from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import JSON, Boolean, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from spine_api.core.database import Base


class AgentLeaseModel(Base):
    """One row per locked trip lease."""

    __tablename__ = "agent_leases"

    trip_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    holder_id: Mapped[str] = mapped_column(String(255), nullable=False)
    lease_token: Mapped[str] = mapped_column(String(128), nullable=False)
    fencing_token: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    acquired_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    ttl_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    lease_metadata: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"), nullable=True
    )
