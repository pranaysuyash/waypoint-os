"""
spine_api/models/advisor_payout.py — IC Advisor Payout Ledger Model (PA-23).

Backs the durable advisor payout ledger
(``spine_api.services.advisor_payout_store``): the persisted, reconcilable
record of every advisor payout movement. ``reconcile_trip_commission``
(commission_reconciliation) compares the booking confirmation total for a
trip against the payout rows linked to that trip — the ledger is the
settlement source of truth, honestly labeled (``storage_backend="sql"``).

Tenant-owned table (agency_id) — RLS-enabled with select/all policies in
``alembic/versions/pa_wave2_authority_payouts_cost.py``, consistent with
``payment_mandates``. ``payout_ref`` is globally unique so a payout movement
can never be double-recorded. Lifecycle: ``recorded`` → ``voided`` (CAS —
only a recorded payout can be voided).
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from spine_api.core.database import Base


class AdvisorPayoutModel(Base):
    """One row per recorded advisor payout movement."""

    __tablename__ = "advisor_payouts"

    payout_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    agency_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    advisor_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    amount_usd: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="USD")
    trip_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    # recorded | voided
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="recorded")
    payout_ref: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    recorded_by: Mapped[str] = mapped_column(String(255), nullable=False)
    method: Mapped[str] = mapped_column(String(40), nullable=False, default="DIRECT_DEPOSIT")
    authority_approval_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    note: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
