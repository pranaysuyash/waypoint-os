"""
spine_api/services/payment_mandate_service.py — Durable Payment Mandate Ledger (F-04).

Records the consent artifacts that authorize money movement (split deposits,
installments, final balance, supplier incidental holds) and enforces their
authorization bounds at execution time. This is the ledger F-04 asks for: the
audit-proof answer to "who consented to this money moving, for how much, and
is that consent still in force?".

Design constraints carried from the findings family:

- F-04: no movement may claim a consent artifact that does not exist —
  registration REQUIRES a ``consent_artifact_ref`` (the durable acceptance
  token / audit event that carries the full consent text). Raw consent text
  is never stored here; only its SHA-256 digest.
- F-01/PA-06 class: consumption uses a single-statement compare-and-set
  (``consumed + amount <= max``, status guards) — never a blind
  read-modify-write. A mandate that cannot cover the charge is refused, never
  partially applied.
- Tenancy: every operation is agency-scoped; the SQL backend runs inside the
  canonical RLS session helper so rows are filtered exactly like trips.
- Honest provenance: responses declare ``storage_backend``. The default
  ``memory`` backend is an in-process preview (single-worker, not durable),
  the same posture the idempotency registry had before PT-08; SQL is selected
  via ``SPINE_API_PAYMENT_MANDATE_BACKEND=sql``.
"""

from __future__ import annotations

import hashlib
import os
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

VALID_PURPOSES = (
    "INITIAL_DEPOSIT",
    "SPLIT_INSTALLMENT",
    "FINAL_BALANCE",
    "SUPPLIER_INCIDENTAL_HOLD",
)


@dataclass(slots=True)
class MandateRecord:
    mandate_id: str
    agency_id: str
    trip_id: str
    customer_id: str
    max_authorized_cents: int
    currency: str
    purpose: str
    consent_text_sha256: str
    consent_artifact_ref: str
    signed_at: str
    expires_at: str
    status: str = "ACTIVE"
    consumed_amount_cents: int = 0
    customer_name: str = ""
    customer_email: str = ""
    client_ip_address: str = ""
    revocation_reason: Optional[str] = None
    storage_backend: str = field(default="memory")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mandate_id": self.mandate_id,
            "agency_id": self.agency_id,
            "trip_id": self.trip_id,
            "customer_id": self.customer_id,
            "customer_name": self.customer_name,
            "customer_email": self.customer_email,
            "max_authorized_cents": self.max_authorized_cents,
            "currency": self.currency,
            "purpose": self.purpose,
            "consent_text_sha256": self.consent_text_sha256,
            "consent_artifact_ref": self.consent_artifact_ref,
            "client_ip_address": self.client_ip_address,
            "signed_at": self.signed_at,
            "expires_at": self.expires_at,
            "status": self.status,
            "consumed_amount_cents": self.consumed_amount_cents,
            "revocation_reason": self.revocation_reason,
            "storage_backend": self.storage_backend,
        }


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _backend() -> str:
    raw = (os.environ.get("SPINE_API_PAYMENT_MANDATE_BACKEND") or "memory").strip().lower()
    if raw in ("postgres", "postgresql"):
        return "sql"
    return raw if raw in ("memory", "sql") else "memory"


def _digest(consent_text: str) -> str:
    return hashlib.sha256(consent_text.encode("utf-8")).hexdigest()


class PaymentMandateLedger:
    """Consent-artifact ledger for money movement. All ops agency-scoped."""

    _MEMORY_LOCK = threading.Lock()
    _MEMORY_STORE: Dict[str, MandateRecord] = {}

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    @classmethod
    def register_mandate(
        cls,
        *,
        agency_id: str,
        trip_id: str,
        customer_id: str,
        max_authorized_cents: int,
        purpose: str,
        consent_text: str,
        consent_artifact_ref: str,
        currency: str = "USD",
        customer_name: str = "",
        customer_email: str = "",
        client_ip_address: str = "",
        validity_days: int = 60,
    ) -> MandateRecord:
        """Record a payment mandate. ``consent_artifact_ref`` is REQUIRED and
        must point at the durable consent artifact (e-sign acceptance token /
        audit event id) — a mandate without one is the decorative ledger the
        findings family forbids."""
        if not agency_id:
            raise ValueError("agency_id is required for a payment mandate.")
        if not trip_id:
            raise ValueError("trip_id is required for a payment mandate.")
        if purpose not in VALID_PURPOSES:
            raise ValueError(f"purpose must be one of {VALID_PURPOSES}; got {purpose!r}")
        if max_authorized_cents <= 0:
            raise ValueError("max_authorized_cents must be positive.")
        if not consent_text:
            raise ValueError("consent_text is required (only its digest is stored).")
        if not consent_artifact_ref:
            raise ValueError(
                "consent_artifact_ref is required: a mandate must reference the "
                "durable consent artifact (acceptance token / audit event) that "
                "carries the traveler's authorization."
            )

        backend = _backend()
        record = MandateRecord(
            mandate_id=f"MAN-{uuid.uuid4().hex[:10].upper()}",
            agency_id=agency_id,
            trip_id=trip_id,
            customer_id=customer_id,
            max_authorized_cents=int(max_authorized_cents),
            currency=(currency or "USD").upper(),
            purpose=purpose,
            consent_text_sha256=_digest(consent_text),
            consent_artifact_ref=consent_artifact_ref,
            signed_at=_now().isoformat(),
            expires_at=(_now() + timedelta(days=max(1, validity_days))).isoformat(),
            customer_name=customer_name,
            customer_email=customer_email,
            client_ip_address=client_ip_address,
            storage_backend="sql" if backend == "sql" else "memory",
        )
        if backend == "sql":
            cls._sql_insert(record)
        else:
            with cls._MEMORY_LOCK:
                cls._MEMORY_STORE[record.mandate_id] = record
        return record

    # ------------------------------------------------------------------
    # Execution-time authorization (the seam fulfillment calls)
    # ------------------------------------------------------------------

    @classmethod
    def authorize_charge(
        cls,
        *,
        agency_id: str,
        mandate_id: str,
        amount_cents: int,
    ) -> Dict[str, Any]:
        """CAS-authorize ``amount_cents`` against an ACTIVE, unexpired mandate.

        Refuses (authorized=False) when the mandate is missing, revoked,
        expired, or has insufficient remaining authorization — never partially
        consumes. Returns the updated snapshot on success.
        """
        if amount_cents <= 0:
            return {"authorized": False, "reason": "amount_cents must be positive."}
        if _backend() == "sql":
            return cls._sql_authorize(agency_id, mandate_id, int(amount_cents))
        return cls._memory_authorize(agency_id, mandate_id, int(amount_cents))

    @classmethod
    def resolve_for_trip(cls, *, agency_id: str, trip_id: str) -> Optional[MandateRecord]:
        """Newest ACTIVE, unexpired mandate for a trip, if any."""
        candidates = [
            m
            for m in cls.list_mandates(agency_id=agency_id, trip_id=trip_id)
            if m["status"] == "ACTIVE"
        ]
        if not candidates:
            return None
        for m in sorted(candidates, key=lambda r: r["signed_at"], reverse=True):
            try:
                if datetime.fromisoformat(m["expires_at"]) > _now():
                    return MandateRecord(**m)
            except (TypeError, ValueError):
                continue
        return None

    # ------------------------------------------------------------------
    # Lifecycle reads / revocation
    # ------------------------------------------------------------------

    @classmethod
    def get_mandate(cls, *, agency_id: str, mandate_id: str) -> Optional[Dict[str, Any]]:
        if _backend() == "sql":
            row = cls._sql_get(agency_id, mandate_id)
            return cls._sql_row_to_dict(row) if row else None
        with cls._MEMORY_LOCK:
            record = cls._MEMORY_STORE.get(mandate_id)
            if record is None or record.agency_id != agency_id:
                return None
            cls._expire_if_due(record)
            return record.to_dict()

    @classmethod
    def list_mandates(
        cls,
        *,
        agency_id: str,
        trip_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        if _backend() == "sql":
            rows = cls._sql_list(agency_id, trip_id, status)
            return [cls._sql_row_to_dict(r) for r in rows]
        with cls._MEMORY_LOCK:
            records = [
                r
                for r in cls._MEMORY_STORE.values()
                if r.agency_id == agency_id
                and (trip_id is None or r.trip_id == trip_id)
                and (status is None or r.status == status)
            ]
            for r in records:
                cls._expire_if_due(r)
            return [r.to_dict() for r in records]

    @classmethod
    def revoke_mandate(cls, *, agency_id: str, mandate_id: str, reason: str) -> bool:
        """CAS revocation: only an ACTIVE mandate can be revoked."""
        if _backend() == "sql":
            return cls._sql_revoke(agency_id, mandate_id, reason)
        with cls._MEMORY_LOCK:
            record = cls._MEMORY_STORE.get(mandate_id)
            if record is None or record.agency_id != agency_id:
                return False
            if record.status != "ACTIVE":
                return False
            record.status = "REVOKED"
            record.revocation_reason = reason[:500] if reason else reason
            return True

    # ------------------------------------------------------------------
    # Memory backend
    # ------------------------------------------------------------------

    @classmethod
    def _expire_if_due(cls, record: MandateRecord) -> None:
        try:
            if record.status == "ACTIVE" and datetime.fromisoformat(record.expires_at) <= _now():
                record.status = "EXPIRED"
        except (TypeError, ValueError):
            pass

    @classmethod
    def _memory_authorize(cls, agency_id: str, mandate_id: str, amount_cents: int) -> Dict[str, Any]:
        with cls._MEMORY_LOCK:
            record = cls._MEMORY_STORE.get(mandate_id)
            if record is None or record.agency_id != agency_id:
                return {"authorized": False, "reason": "Mandate not found in ledger."}
            cls._expire_if_due(record)
            if record.status != "ACTIVE":
                return {"authorized": False, "reason": f"Mandate is in {record.status} status."}
            remaining = record.max_authorized_cents - record.consumed_amount_cents
            if amount_cents > remaining:
                return {
                    "authorized": False,
                    "reason": (
                        f"Charge of {amount_cents} cents exceeds remaining mandate "
                        f"authorization of {remaining} cents."
                    ),
                }
            record.consumed_amount_cents += amount_cents
            if record.consumed_amount_cents >= record.max_authorized_cents:
                record.status = "CONSUMED"
            return {
                "authorized": True,
                "mandate_id": record.mandate_id,
                "charged_cents": amount_cents,
                "remaining_authorized_cents": record.max_authorized_cents
                - record.consumed_amount_cents,
                "consent_text_sha256": record.consent_text_sha256,
                "status": record.status,
                "storage_backend": record.storage_backend,
            }

    # ------------------------------------------------------------------
    # SQL backend (canonical RLS session + single-statement CAS)
    # ------------------------------------------------------------------

    @staticmethod
    def _run(coro: Any) -> Any:
        from spine_api.persistence import _run_async_blocking

        return _run_async_blocking(coro)

    @classmethod
    def _ensure_table(cls) -> None:
        from spine_api.core.database import Base
        from spine_api.models.payment_mandate import PaymentMandateModel

        if getattr(cls, "_ensure_table_done", False):
            return

        async def _create_all() -> None:
            from spine_api.core.database import engine

            async with engine.begin() as conn:
                await conn.run_sync(
                    lambda sync_conn: Base.metadata.create_all(
                        sync_conn, tables=[PaymentMandateModel.__table__], checkfirst=True
                    )
                )

        cls._run(_create_all())
        cls._ensure_table_done = True

    @staticmethod
    def _rls_session(agency_id: str) -> Any:
        from spine_api.persistence import SQLTripStore

        return SQLTripStore._rls_session_for_agency(agency_id)

    @classmethod
    def _sql_insert(cls, record: MandateRecord) -> None:
        cls._ensure_table()

        async def _go() -> None:
            from spine_api.models.payment_mandate import PaymentMandateModel

            async with cls._rls_session(record.agency_id) as session:
                session.add(
                    PaymentMandateModel(
                        mandate_id=record.mandate_id,
                        agency_id=record.agency_id,
                        trip_id=record.trip_id,
                        customer_id=record.customer_id,
                        customer_name=record.customer_name,
                        customer_email=record.customer_email,
                        max_authorized_cents=record.max_authorized_cents,
                        currency=record.currency,
                        purpose=record.purpose,
                        consent_text_sha256=record.consent_text_sha256,
                        consent_artifact_ref=record.consent_artifact_ref,
                        client_ip_address=record.client_ip_address,
                        signed_at=datetime.fromisoformat(record.signed_at),
                        expires_at=datetime.fromisoformat(record.expires_at),
                        status=record.status,
                        consumed_amount_cents=record.consumed_amount_cents,
                    )
                )
                await session.commit()

        cls._run(_go())

    @staticmethod
    def _sql_row_to_dict(row: Any) -> Dict[str, Any]:
        return {
            "mandate_id": row.mandate_id,
            "agency_id": row.agency_id,
            "trip_id": row.trip_id,
            "customer_id": row.customer_id,
            "customer_name": row.customer_name or "",
            "customer_email": row.customer_email or "",
            "max_authorized_cents": row.max_authorized_cents,
            "currency": row.currency,
            "purpose": row.purpose,
            "consent_text_sha256": row.consent_text_sha256,
            "consent_artifact_ref": row.consent_artifact_ref,
            "client_ip_address": row.client_ip_address or "",
            "signed_at": row.signed_at.isoformat() if row.signed_at else None,
            "expires_at": row.expires_at.isoformat() if row.expires_at else None,
            "status": row.status,
            "consumed_amount_cents": row.consumed_amount_cents,
            "revocation_reason": row.revocation_reason,
            "storage_backend": "sql",
        }

    @classmethod
    def _sql_get(cls, agency_id: str, mandate_id: str) -> Any:
        cls._ensure_table()

        async def _go():
            from sqlalchemy import select

            from spine_api.models.payment_mandate import PaymentMandateModel

            async with cls._rls_session(agency_id) as session:
                result = await session.execute(
                    select(PaymentMandateModel).where(
                        PaymentMandateModel.mandate_id == mandate_id,
                        PaymentMandateModel.agency_id == agency_id,
                    )
                )
                return result.scalar_one_or_none()

        return cls._run(_go())

    @classmethod
    def _sql_list(
        cls,
        agency_id: str,
        trip_id: Optional[str],
        status: Optional[str],
    ) -> List[Any]:
        cls._ensure_table()

        async def _go():
            from sqlalchemy import select

            from spine_api.models.payment_mandate import PaymentMandateModel

            async with cls._rls_session(agency_id) as session:
                stmt = select(PaymentMandateModel).where(
                    PaymentMandateModel.agency_id == agency_id
                )
                if trip_id is not None:
                    stmt = stmt.where(PaymentMandateModel.trip_id == trip_id)
                if status is not None:
                    stmt = stmt.where(PaymentMandateModel.status == status)
                stmt = stmt.order_by(PaymentMandateModel.signed_at.desc())
                result = await session.execute(stmt)
                return result.scalars().all()

        return cls._run(_go())

    @classmethod
    def _sql_revoke(cls, agency_id: str, mandate_id: str, reason: str) -> bool:
        cls._ensure_table()

        async def _go() -> bool:
            from sqlalchemy import update

            from spine_api.models.payment_mandate import PaymentMandateModel

            # The RLS helper executes set_config(..., transaction_local=true) on
            # an autobegun transaction — all work here joins that ONE
            # transaction and commits explicitly (no nested session.begin()).
            async with cls._rls_session(agency_id) as session:
                result = await session.execute(
                    update(PaymentMandateModel)
                    .where(
                        PaymentMandateModel.mandate_id == mandate_id,
                        PaymentMandateModel.agency_id == agency_id,
                        PaymentMandateModel.status == "ACTIVE",
                    )
                    .values(status="REVOKED", revocation_reason=(reason or "")[:500])
                )
                changed = bool(result.rowcount)
                await session.commit()
                return changed

        return cls._run(_go())

    @classmethod
    def _sql_authorize(cls, agency_id: str, mandate_id: str, amount_cents: int) -> Dict[str, Any]:
        cls._ensure_table()

        async def _go() -> Dict[str, Any]:
            from sqlalchemy import case, select, update

            from spine_api.models.payment_mandate import PaymentMandateModel

            # Single-transaction pattern (see _sql_revoke): the CAS consume,
            # the refusal-reason read-back, and the commit all share the
            # transaction that carries the RLS context.
            async with cls._rls_session(agency_id) as session:
                result = await session.execute(
                    update(PaymentMandateModel)
                    .where(
                        PaymentMandateModel.mandate_id == mandate_id,
                        PaymentMandateModel.agency_id == agency_id,
                        PaymentMandateModel.status == "ACTIVE",
                        PaymentMandateModel.expires_at > _now(),
                        PaymentMandateModel.consumed_amount_cents + amount_cents
                        <= PaymentMandateModel.max_authorized_cents,
                    )
                    .values(
                        consumed_amount_cents=PaymentMandateModel.consumed_amount_cents
                        + amount_cents,
                        status=case(
                            (
                                PaymentMandateModel.consumed_amount_cents + amount_cents
                                >= PaymentMandateModel.max_authorized_cents,
                                "CONSUMED",
                            ),
                            else_=PaymentMandateModel.status,
                        ),
                    )
                    .returning(
                        PaymentMandateModel.mandate_id,
                        PaymentMandateModel.status,
                        PaymentMandateModel.max_authorized_cents,
                        PaymentMandateModel.consumed_amount_cents,
                        PaymentMandateModel.consent_text_sha256,
                    )
                )
                row = result.first()
                if row is None:
                    # Refusal reason: read current state in the SAME transaction
                    # (after commit the RLS context would be gone).
                    current = await session.execute(
                        select(PaymentMandateModel).where(
                            PaymentMandateModel.mandate_id == mandate_id,
                            PaymentMandateModel.agency_id == agency_id,
                        )
                    )
                    existing = current.scalar_one_or_none()
                    await session.commit()  # nothing mutated; closes the tx cleanly
                    if existing is None:
                        return {"authorized": False, "reason": "Mandate not found in ledger."}
                    if existing.status != "ACTIVE":
                        return {
                            "authorized": False,
                            "reason": f"Mandate is in {existing.status} status.",
                        }
                    if existing.expires_at and existing.expires_at <= _now():
                        return {"authorized": False, "reason": "Payment mandate has expired."}
                    remaining = existing.max_authorized_cents - existing.consumed_amount_cents
                    return {
                        "authorized": False,
                        "reason": (
                            f"Charge of {amount_cents} cents exceeds remaining mandate "
                            f"authorization of {remaining} cents."
                        ),
                    }
                await session.commit()
                remaining = row.max_authorized_cents - row.consumed_amount_cents
                return {
                    "authorized": True,
                    "mandate_id": row.mandate_id,
                    "charged_cents": amount_cents,
                    "remaining_authorized_cents": remaining,
                    "consent_text_sha256": row.consent_text_sha256,
                    "status": row.status,
                    "storage_backend": "sql",
                }

        return cls._run(_go())

