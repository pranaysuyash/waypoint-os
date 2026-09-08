"""
spine_api/services/advisor_payout_store.py — Durable IC Advisor Payout Ledger (PA-23).

The durable, reconcilable record of advisor payout movements backing
``spine_api.services.commission_reconciliation``. Each payout is one row:
uuid payout id, agency-scoped, amount, optional trip link (for settlement
reconciliation), ``payout_ref`` globally unique (double-recording is
impossible), and an optional ``authority_approval_id`` pointing at the
ratified dual-control approval that authorized an over-cap payout (PA-08).

Backend selection mirrors ``payment_mandate_service``: the default
``memory`` backend is an in-process preview (tests / single-process dev);
``SPINE_API_ADVISOR_PAYOUT_BACKEND=sql`` selects Postgres explicitly, and
production (``ENVIRONMENT=production|prod`` with a ``DATABASE_URL``) selects
SQL automatically. The SQL ledger starts at true zero and is never seeded.
"""

from __future__ import annotations

import os
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

STATUS_RECORDED = "recorded"
STATUS_VOIDED = "voided"


@dataclass(slots=True)
class PayoutRecord:
    payout_id: str
    agency_id: str
    advisor_id: str
    amount_usd: float
    payout_ref: str
    recorded_by: str
    currency: str = "USD"
    trip_id: Optional[str] = None
    status: str = STATUS_RECORDED
    method: str = "DIRECT_DEPOSIT"
    authority_approval_id: Optional[str] = None
    note: Optional[str] = None
    created_at: str = field(default_factory=lambda: _now().isoformat())
    storage_backend: str = field(default="memory")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "payout_id": self.payout_id,
            "agency_id": self.agency_id,
            "advisor_id": self.advisor_id,
            "amount_usd": self.amount_usd,
            "currency": self.currency,
            "trip_id": self.trip_id,
            "status": self.status,
            "payout_ref": self.payout_ref,
            "recorded_by": self.recorded_by,
            "method": self.method,
            "authority_approval_id": self.authority_approval_id,
            "note": self.note,
            "created_at": self.created_at,
            "storage_backend": self.storage_backend,
        }


def _now() -> datetime:
    return datetime.now(timezone.utc)


def backend() -> str:
    """Resolve the payout ledger backend (mirrors payment_mandate_service).

    Precedence: explicit ``SPINE_API_ADVISOR_PAYOUT_BACKEND`` (memory|sql,
    postgres/postgresql aliased to sql) > production default (sql when
    ``DATABASE_URL`` is configured) > memory (tests / local preview).
    """
    raw = (os.environ.get("SPINE_API_ADVISOR_PAYOUT_BACKEND") or "").strip().lower()
    if raw in ("postgres", "postgresql"):
        return "sql"
    if raw in ("memory", "sql"):
        return raw
    environment = os.environ.get("ENVIRONMENT", "development").strip().lower()
    if environment in ("production", "prod") and os.environ.get("DATABASE_URL"):
        return "sql"
    return "memory"


def new_payout_id() -> str:
    """uuid-derived payout id (PA-23: never clock-derived — ids collided)."""
    return f"pay_{uuid.uuid4().hex[:12]}"


class AdvisorPayoutStore:
    """Payout movement ledger. All operations are agency-scoped."""

    _MEMORY_LOCK = threading.Lock()
    _MEMORY_STORE: Dict[str, PayoutRecord] = {}

    # ------------------------------------------------------------------
    # Record / list / void
    # ------------------------------------------------------------------

    @classmethod
    def record_payout(
        cls,
        *,
        agency_id: str,
        advisor_id: str,
        amount_usd: float,
        recorded_by: str,
        currency: str = "USD",
        trip_id: Optional[str] = None,
        method: str = "DIRECT_DEPOSIT",
        authority_approval_id: Optional[str] = None,
        note: Optional[str] = None,
        payout_id: Optional[str] = None,
    ) -> PayoutRecord:
        if not agency_id:
            raise ValueError("agency_id is required for a payout record.")
        if not advisor_id:
            raise ValueError("advisor_id is required for a payout record.")
        amount = round(float(amount_usd), 2)
        if amount <= 0:
            raise ValueError("amount_usd must be positive.")
        if not recorded_by:
            raise ValueError("recorded_by is required for a payout record.")

        record = PayoutRecord(
            payout_id=payout_id or new_payout_id(),
            agency_id=agency_id,
            advisor_id=advisor_id,
            amount_usd=amount,
            currency=(currency or "USD").upper(),
            trip_id=trip_id or None,
            payout_ref=f"PO-{uuid.uuid4().hex[:16].upper()}",
            recorded_by=recorded_by,
            method=(method or "DIRECT_DEPOSIT"),
            authority_approval_id=authority_approval_id or None,
            note=(note or None),
            storage_backend="sql" if backend() == "sql" else "memory",
        )
        if backend() == "sql":
            cls._sql_insert(record)
        else:
            with cls._MEMORY_LOCK:
                cls._MEMORY_STORE[record.payout_id] = record
        return record

    @classmethod
    def list_payouts(
        cls,
        *,
        agency_id: str,
        advisor_id: Optional[str] = None,
        trip_id: Optional[str] = None,
        status: Optional[str] = STATUS_RECORDED,
    ) -> List[Dict[str, Any]]:
        if backend() == "sql":
            rows = cls._sql_list(agency_id, advisor_id, trip_id, status)
            return [cls._sql_row_to_dict(r) for r in rows]
        with cls._MEMORY_LOCK:
            records = [
                r
                for r in cls._MEMORY_STORE.values()
                if r.agency_id == agency_id
                and (advisor_id is None or r.advisor_id == advisor_id)
                and (trip_id is None or r.trip_id == trip_id)
                and (status is None or r.status == status)
            ]
            return [r.to_dict() for r in sorted(records, key=lambda x: x.created_at, reverse=True)]

    @classmethod
    def get_payout(cls, *, agency_id: str, payout_id: str) -> Optional[Dict[str, Any]]:
        if backend() == "sql":
            row = cls._sql_get(agency_id, payout_id)
            return cls._sql_row_to_dict(row) if row else None
        with cls._MEMORY_LOCK:
            record = cls._MEMORY_STORE.get(payout_id)
            if record is None or record.agency_id != agency_id:
                return None
            return record.to_dict()

    @classmethod
    def void_payout(cls, *, agency_id: str, payout_id: str, note: Optional[str] = None) -> bool:
        """CAS void: only a recorded payout can be voided (never re-recorded)."""
        if backend() == "sql":
            return cls._sql_void(agency_id, payout_id, note)
        with cls._MEMORY_LOCK:
            record = cls._MEMORY_STORE.get(payout_id)
            if record is None or record.agency_id != agency_id:
                return False
            if record.status != STATUS_RECORDED:
                return False
            record.status = STATUS_VOIDED
            record.note = (note or record.note)
            return True

    # ------------------------------------------------------------------
    # SQL backend (canonical RLS session + single-statement CAS)
    # ------------------------------------------------------------------

    @staticmethod
    def _run(coro: Any) -> Any:
        from spine_api.persistence import _run_async_blocking

        return _run_async_blocking(coro)

    @classmethod
    def _ensure_table(cls) -> None:
        from sqlalchemy import text

        from spine_api.core.database import Base
        from spine_api.models.advisor_payout import AdvisorPayoutModel

        if getattr(cls, "_ensure_table_done", False):
            return

        # Idempotent tenant RLS posture — matches the alembic revision
        # (pa_wave2_authority_payouts_cost) so lazily-created tables get the
        # same isolation as migration-created ones, in either ordering.
        _RLS_STATEMENTS = (
            text("ALTER TABLE advisor_payouts ENABLE ROW LEVEL SECURITY"),
            text("ALTER TABLE advisor_payouts FORCE ROW LEVEL SECURITY"),
            text(
                """
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_policy
                        WHERE polrelid = 'advisor_payouts'::regclass
                          AND polname = 'waypoint_rls_select'
                    ) THEN
                        CREATE POLICY waypoint_rls_select ON advisor_payouts
                            FOR SELECT USING (
                                agency_id = current_setting('app.current_agency_id', TRUE)
                            );
                    END IF;
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_policy
                        WHERE polrelid = 'advisor_payouts'::regclass
                          AND polname = 'waypoint_rls_all'
                    ) THEN
                        CREATE POLICY waypoint_rls_all ON advisor_payouts
                            USING (agency_id = current_setting('app.current_agency_id', TRUE))
                            WITH CHECK (agency_id = current_setting('app.current_agency_id', TRUE));
                    END IF;
                END $$;
                """
            ),
        )

        async def _create_all() -> None:
            from spine_api.core.database import engine

            async with engine.begin() as conn:
                await conn.run_sync(
                    lambda sync_conn: Base.metadata.create_all(
                        sync_conn, tables=[AdvisorPayoutModel.__table__], checkfirst=True
                    )
                )
                for statement in _RLS_STATEMENTS:
                    await conn.execute(statement)

        cls._run(_create_all())
        cls._ensure_table_done = True

    @staticmethod
    def _rls_session(agency_id: str) -> Any:
        from spine_api.persistence import SQLTripStore

        return SQLTripStore._rls_session_for_agency(agency_id)

    @classmethod
    def _sql_insert(cls, record: PayoutRecord) -> None:
        cls._ensure_table()

        async def _go() -> None:
            from spine_api.models.advisor_payout import AdvisorPayoutModel

            async with cls._rls_session(record.agency_id) as session:
                session.add(
                    AdvisorPayoutModel(
                        payout_id=record.payout_id,
                        agency_id=record.agency_id,
                        advisor_id=record.advisor_id,
                        amount_usd=record.amount_usd,
                        currency=record.currency,
                        trip_id=record.trip_id,
                        status=record.status,
                        payout_ref=record.payout_ref,
                        recorded_by=record.recorded_by,
                        method=record.method,
                        authority_approval_id=record.authority_approval_id,
                        note=record.note,
                        created_at=datetime.fromisoformat(record.created_at),
                    )
                )
                await session.commit()

        cls._run(_go())

    @staticmethod
    def _sql_row_to_dict(row: Any) -> Dict[str, Any]:
        return {
            "payout_id": row.payout_id,
            "agency_id": row.agency_id,
            "advisor_id": row.advisor_id,
            "amount_usd": float(row.amount_usd) if row.amount_usd is not None else 0.0,
            "currency": row.currency,
            "trip_id": row.trip_id,
            "status": row.status,
            "payout_ref": row.payout_ref,
            "recorded_by": row.recorded_by,
            "method": row.method,
            "authority_approval_id": row.authority_approval_id,
            "note": row.note,
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "storage_backend": "sql",
        }

    @classmethod
    def _sql_get(cls, agency_id: str, payout_id: str) -> Any:
        cls._ensure_table()

        async def _go():
            from sqlalchemy import select

            from spine_api.models.advisor_payout import AdvisorPayoutModel

            async with cls._rls_session(agency_id) as session:
                result = await session.execute(
                    select(AdvisorPayoutModel).where(
                        AdvisorPayoutModel.payout_id == payout_id,
                        AdvisorPayoutModel.agency_id == agency_id,
                    )
                )
                return result.scalar_one_or_none()

        return cls._run(_go())

    @classmethod
    def _sql_list(
        cls,
        agency_id: str,
        advisor_id: Optional[str],
        trip_id: Optional[str],
        status: Optional[str],
    ) -> List[Any]:
        cls._ensure_table()

        async def _go():
            from sqlalchemy import select

            from spine_api.models.advisor_payout import AdvisorPayoutModel

            async with cls._rls_session(agency_id) as session:
                stmt = select(AdvisorPayoutModel).where(AdvisorPayoutModel.agency_id == agency_id)
                if advisor_id is not None:
                    stmt = stmt.where(AdvisorPayoutModel.advisor_id == advisor_id)
                if trip_id is not None:
                    stmt = stmt.where(AdvisorPayoutModel.trip_id == trip_id)
                if status is not None:
                    stmt = stmt.where(AdvisorPayoutModel.status == status)
                stmt = stmt.order_by(AdvisorPayoutModel.created_at.desc())
                result = await session.execute(stmt)
                return result.scalars().all()

        return cls._run(_go())

    @classmethod
    def _sql_void(cls, agency_id: str, payout_id: str, note: Optional[str]) -> bool:
        cls._ensure_table()

        async def _go() -> bool:
            from sqlalchemy import update

            from spine_api.models.advisor_payout import AdvisorPayoutModel

            async with cls._rls_session(agency_id) as session:
                result = await session.execute(
                    update(AdvisorPayoutModel)
                    .where(
                        AdvisorPayoutModel.payout_id == payout_id,
                        AdvisorPayoutModel.agency_id == agency_id,
                        AdvisorPayoutModel.status == STATUS_RECORDED,
                    )
                    .values(status=STATUS_VOIDED, note=(note or AdvisorPayoutModel.note))
                )
                changed = bool(result.rowcount)
                await session.commit()
                return changed

        return cls._run(_go())
