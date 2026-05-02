"""
spine_api.models.audit — Database-backed audit trail.

Replaces the file-based AuditStore for production-grade traceability.

Schema:
- audit_logs table with agency-scoped, user-attributed, resource-tagged entries
- Indexed on agency_id, user_id, resource_type, created_at for fast filtering
- JSONB `changes` column captures before/after snapshots for state mutations

Design decisions:
- Depends(audit_logger()) dependency for route-level audit injection,
  NOT blanket middleware. Route-opt-in ensures only meaningful mutations
  are logged, avoiding noise from health checks, OPTIONS, etc.
- agency_id and user_id from JWT context (no manual parameter passing)
- `action` uses a controlled vocabulary (see AuditAction enum)
- `changes` uses JSONB for flexible before/after snapshots without schema migration
"""

import uuid
from datetime import datetime, timezone
from enum import StrEnum
from typing import Optional

from sqlalchemy import String, DateTime, Index, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, column_property

from spine_api.core.database import Base, engine as _engine

# Use JSONB on PostgreSQL, JSON on SQLite (for tests)
# SQLAlchemy resolves the type at DDL time based on the dialect.
_DIALECT_NAME = _engine.dialect.name

def _json_type():
    """Return JSONB for PostgreSQL, JSON for everything else."""
    if _DIALECT_NAME == "postgresql":
        from sqlalchemy.dialects.postgresql import JSONB as _JSONB
        return _JSONB
    return JSON


class AuditAction(StrEnum):
    """Controlled vocabulary for audit log actions."""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    PASSWORD_RESET_REQUEST = "password_reset_request"
    PASSWORD_RESET_CONFIRM = "password_reset_confirm"
    RUN_START = "run_start"
    RUN_COMPLETE = "run_complete"
    RUN_FAILED = "run_failed"
    RUN_BLOCKED = "run_blocked"
    OVERRIDE = "override"
    ASSIGN = "assign"
    EXPORT = "export"


class AuditLog(Base):
    """Database-backed audit log entry."""
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_agency_created", "agency_id", "created_at"),
        Index("ix_audit_logs_user_created", "user_id", "created_at"),
        Index("ix_audit_logs_resource", "resource_type", "resource_id"),
        Index("ix_audit_logs_agency_action", "agency_id", "action"),
        {"extend_existing": True},
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    agency_id: Mapped[str] = mapped_column(
        String(36), nullable=False, index=True
    )
    user_id: Mapped[Optional[str]] = mapped_column(
        String(36), nullable=True, index=True
    )
    action: Mapped[str] = mapped_column(
        String(50), nullable=False
    )
    resource_type: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )
    resource_id: Mapped[Optional[str]] = mapped_column(
        String(36), nullable=True
    )
    changes: Mapped[Optional[dict]] = mapped_column(
        _json_type(), nullable=True
    )
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45), nullable=True
    )
    user_agent: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "agency_id": self.agency_id,
            "user_id": self.user_id,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "changes": self.changes,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }