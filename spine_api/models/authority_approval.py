"""
spine_api/models/authority_approval.py — Dual-Control Authority Approval Model (PA-08).

Backs the durable dual-control approval ledger
(``spine_api.services.authority_approval_service``): the ratified, persisted
answer to "two distinct owner/admin humans approved exactly this action on
exactly this subject, for exactly this amount". Execution paths (fulfillment,
advisor payouts) consult it when the governance registry's per-agent budget
cap would otherwise deny the action — the ratified approval IS the authority.

Tenant-owned table (agency_id) — RLS-enabled with select/all policies in
``alembic/versions/pa_wave2_authority_payouts_cost.py``, consistent with
``payment_mandates`` and the rest of the tenant fleet. Status lifecycle:
``pending_second`` → ``approved`` | ``denied``; transitions are guarded by
compare-and-set so two concurrent approvers can never both be recorded as the
"second" approver.
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from spine_api.core.database import Base


class AuthorityApprovalModel(Base):
    """One row per dual-control authority approval request."""

    __tablename__ = "authority_approvals"

    approval_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    agency_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(120), nullable=False)
    subject_type: Mapped[str] = mapped_column(String(40), nullable=False)
    subject_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    amount_usd: Mapped[Optional[float]] = mapped_column(Numeric(14, 2), nullable=True)
    requested_by: Mapped[str] = mapped_column(String(255), nullable=False)
    # pending_second | approved | denied
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending_second")
    first_approver_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    first_approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    second_approver_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    second_approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    reason: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    denial_reason: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
