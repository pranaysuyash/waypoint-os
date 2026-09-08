"""
spine_api/models/payment_mandate.py — Payment Authorization Mandate Model (F-04).

Backs the durable mandate ledger (``spine_api.services.payment_mandate_service``)
that records consent artifacts for money movement: split deposits, installment
plans, final balance collection, and supplier incidental holds.

Tenant-owned table (agency_id) — RLS-enabled with select/all policies in
``alembic/versions/add_payment_mandates_table.py``, consistent with
``trip_routing_states`` and the rest of the tenant fleet. A mandate row is the
audit-proof answer to "who consented to this money moving, for how much, and
is that consent still in force?" — Fulfillment consults it before executing
(payment movement without a consent artifact is the F-04 defect class).
"""

from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from spine_api.core.database import Base


class PaymentMandateModel(Base):
    """One row per payment authorization mandate."""

    __tablename__ = "payment_mandates"

    mandate_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    agency_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    trip_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    customer_id: Mapped[str] = mapped_column(String(255), nullable=False)
    customer_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    customer_email: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    max_authorized_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="USD")
    purpose: Mapped[str] = mapped_column(String(40), nullable=False)
    consent_text_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    consent_artifact_ref: Mapped[str] = mapped_column(String(255), nullable=False)
    client_ip_address: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    signed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE")
    consumed_amount_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    revocation_reason: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    mandate_metadata: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB(), nullable=True)
