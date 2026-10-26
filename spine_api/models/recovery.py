"""
spine_api/models/recovery.py — Recoveries Ledger model (T10, phase 1).

Backs the durable recoveries ledger (``spine_api.services.recovery_store``):
the persisted record of every entitlement the platform has detected or an
operator has recorded — money or credit owed to the traveler or agency by a
counterparty (airline, supplier, insurer) — with its lifecycle through to
settlement.

Design (first principles):
- **General primitive**: one ledger for every entitlement class — price-drop
  re-locks, supplier-fault compensation, insurance payouts, manual entries.
  Disruption claims are NOT recorded here: their lifecycle is owned by the
  purpose-built ``claim_disposition`` machine (8 legal states, overdue
  nudge, airline→traveler outcome recording — shipped 2026-09-30, FND-0233).
  The two layers are complementary; a rollup bridge is future work.
- **Tracking-only**: the ledger NEVER moves money (permanent boundary,
  ``test_no_payment_code_paths``). It records what is owed, from whom, and
  the operator-recorded lifecycle state.
- **Honesty basis on every amount**: modeled estimates are labeled
  ``modeled``; only counterparty-confirmed amounts may be labeled
  ``confirmed``.

Tenant-owned table (agency_id) — RLS-enabled idempotently at store
initialization, mirroring ``advisor_payouts`` (select/all policies keyed on
``app.current_agency_id``). Lifecycle is one-directional CAS:
``detected → filed → {accepted | rejected} → {paid | credited}``, plus
``withdrawn`` terminal from any non-terminal state.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from spine_api.core.database import Base

RECOVERY_STATUSES = (
    "detected",   # entitlement identified (e.g. statutory evaluation ran)
    "filed",      # claim submitted to the counterparty
    "accepted",   # counterparty acknowledged the entitlement
    "rejected",   # counterparty refused (appeal may restart at filed)
    "paid",       # money received (recorded, not moved, by the platform)
    "credited",   # credit/rebooking value received
    "withdrawn",  # operator or traveler abandoned the claim
)

RECOVERY_TERMINAL_STATUSES = ("paid", "credited", "withdrawn")

AMOUNT_BASES = ("modeled", "confirmed")

SOURCE_TYPES = (
    "price_drop",         # re-lock at lower rate
    "supplier_fault",     # supplier compensation / penalty recovery
    "insurance_payout",   # insurance entitlement
    "manual",             # operator-recorded, no system producer yet
    # NOTE: disruption claims are deliberately absent — their lifecycle lives
    # in claim_disposition (8 legal states, overdue nudge). Recording them
    # here too would double-track one entitlement.
)


class RecoveryModel(Base):
    """One row per recovery (entitlement lifecycle record)."""

    __tablename__ = "recoveries"

    recovery_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    agency_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    trip_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    traveler_ref: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # What kind of entitlement and against whom.
    source_type: Mapped[str] = mapped_column(String(40), nullable=False)
    counterparty: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Amounts carry their honesty basis: modeled (statutory estimate) vs
    # confirmed (counterparty-acknowledged).
    amount: Mapped[Optional[float]] = mapped_column(Numeric(14, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="USD")
    amount_basis: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # detected → filed → accepted/rejected → paid/credited; withdrawn terminal.
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="detected", index=True)

    # Free-form structured context from the producing event (flight details,
    # disruption parameters, evidence refs). Never credentials.
    details: Mapped[Optional[dict]] = mapped_column(Text, nullable=True)

    # Filing/settlement deadline (perishable entitlements must have an owner —
    # the dated-perishables finding gets its concrete consumer here).
    deadline_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    created_by: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
