"""
spine_api.services.recovery_store — Durable Recoveries Ledger (T10, phase 1).

Tracking-only record of entitlements owed to travelers or the agency, with
their lifecycle through settlement. The platform NEVER moves money — this is
the permanent boundary (``test_no_payment_code_paths``); the ledger records
states and amounts with honesty bases.

Dual backend mirroring ``advisor_payout_store``:
- ``sql`` when DATABASE_URL is configured (RLS-enabled idempotently, mirroring
  the payout table's posture);
- ``memory`` for tests / local preview.

Lifecycle (one-directional CAS):
    detected → filed → accepted → paid | credited
                     ↘ rejected → filed (appeal)   | withdrawn (any state)
"""

from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from spine_api.models.recovery import (
    AMOUNT_BASES,
    RECOVERY_STATUSES,
    RECOVERY_TERMINAL_STATUSES,
    SOURCE_TYPES,
    RecoveryModel,
)
# Boundary note: disruption claims (EU261/UK261/DOT) are NOT recorded here —
# their lifecycle is the purpose-built ``claim_disposition`` machine on the
# passenger-rights router (shipped 2026-09-30). This ledger covers every
# OTHER entitlement class; a cross-source rollup bridge is future work.

_TRANSITIONS: Dict[str, set] = {
    "detected": {"filed", "withdrawn"},
    "filed": {"accepted", "rejected", "withdrawn"},
    "rejected": {"filed", "withdrawn"},  # appeal re-files
    "accepted": {"paid", "credited", "withdrawn"},
    "paid": set(),
    "credited": set(),
    "withdrawn": set(),
}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def new_recovery_id() -> str:
    import uuid

    return f"rec_{uuid.uuid4().hex[:12]}"


class RecoveryStore:
    """Recoveries ledger. All operations are agency-scoped."""

    _MEMORY_LOCK = threading.Lock()
    _MEMORY_STORE: Dict[str, Dict[str, Any]] = {}

    # ------------------------------------------------------------------
    # Backend resolution (mirrors advisor_payout_store)
    # ------------------------------------------------------------------

    @staticmethod
    def backend() -> str:
        raw = (os.environ.get("SPINE_API_RECOVERY_BACKEND") or "").strip().lower()
        if raw in ("postgres", "postgresql"):
            return "sql"
        if raw in ("memory", "sql"):
            return raw
        environment = os.environ.get("ENVIRONMENT", "development").strip().lower()
        if environment in ("production", "prod") and os.environ.get("DATABASE_URL"):
            return "sql"
        return "memory"

    @staticmethod
    def _run(coro: Any) -> Any:
        from spine_api.persistence import _run_async_blocking

        return _run_async_blocking(coro)

    @staticmethod
    def _rls_session(agency_id: str) -> Any:
        from spine_api.persistence import SQLTripStore

        return SQLTripStore._rls_session_for_agency(agency_id)

    @classmethod
    def _ensure_table(cls) -> None:
        from sqlalchemy import text

        from spine_api.core.database import Base

        if getattr(cls, "_ensure_table_done", False):
            return

        _RLS_STATEMENTS = (
            text("ALTER TABLE recoveries ENABLE ROW LEVEL SECURITY"),
            text("ALTER TABLE recoveries FORCE ROW LEVEL SECURITY"),
            text(
                """
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_policy
                        WHERE polrelid = 'recoveries'::regclass
                          AND polname = 'waypoint_rls_select'
                    ) THEN
                        CREATE POLICY waypoint_rls_select ON recoveries
                            FOR SELECT USING (
                                agency_id = current_setting('app.current_agency_id', TRUE)
                            );
                    END IF;
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_policy
                        WHERE polrelid = 'recoveries'::regclass
                          AND polname = 'waypoint_rls_all'
                    ) THEN
                        CREATE POLICY waypoint_rls_all ON recoveries
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
                        sync_conn, tables=[RecoveryModel.__table__], checkfirst=True
                    )
                )
                for statement in _RLS_STATEMENTS:
                    await conn.execute(statement)

        cls._run(_create_all())
        cls._ensure_table_done = True

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    @staticmethod
    def _validate(
        *,
        agency_id: str,
        source_type: str,
        status: str,
        amount: Optional[float],
        amount_basis: Optional[str],
    ) -> None:
        if not agency_id:
            raise ValueError("agency_id is required for a recovery record.")
        if source_type not in SOURCE_TYPES:
            raise ValueError(f"Invalid source_type: {source_type}. Valid: {sorted(SOURCE_TYPES)}")
        if status not in RECOVERY_STATUSES:
            raise ValueError(f"Invalid status: {status}. Valid: {sorted(RECOVERY_STATUSES)}")
        if amount is not None:
            if amount <= 0:
                raise ValueError("amount, when present, must be positive.")
            if not amount_basis:
                raise ValueError("amount_basis is required when amount is present.")
            if amount_basis not in AMOUNT_BASES:
                raise ValueError(f"Invalid amount_basis: {amount_basis}. Valid: {sorted(AMOUNT_BASES)}")
        if amount is None and amount_basis:
            raise ValueError("amount_basis without an amount is meaningless — omit it.")

    # ------------------------------------------------------------------
    # Create / read / transition
    # ------------------------------------------------------------------

    @classmethod
    def create_recovery(
        cls,
        *,
        agency_id: str,
        source_type: str,
        created_by: str,
        trip_id: Optional[str] = None,
        traveler_ref: Optional[str] = None,
        counterparty: Optional[str] = None,
        amount: Optional[float] = None,
        currency: str = "USD",
        amount_basis: Optional[str] = None,
        status: str = "detected",
        details: Optional[Dict[str, Any]] = None,
        deadline_at: Optional[str] = None,
    ) -> Dict[str, Any]:
        cls._validate(
            agency_id=agency_id,
            source_type=source_type,
            status=status,
            amount=amount,
            amount_basis=amount_basis,
        )
        record: Dict[str, Any] = {
            "recovery_id": new_recovery_id(),
            "agency_id": agency_id,
            "trip_id": trip_id or None,
            "traveler_ref": (traveler_ref or "").strip()[:255] or None,
            "source_type": source_type,
            "counterparty": (counterparty or "").strip()[:255] or None,
            "amount": round(float(amount), 2) if amount is not None else None,
            "currency": (currency or "USD").upper(),
            "amount_basis": amount_basis,
            "status": status,
            "details": details or None,
            "deadline_at": deadline_at,
            "created_by": created_by,
            "created_at": _now().isoformat(),
            "updated_at": _now().isoformat(),
            "storage_backend": cls.backend(),
        }
        if cls.backend() == "sql":
            cls._sql_insert(record)
        else:
            with cls._MEMORY_LOCK:
                cls._MEMORY_STORE[record["recovery_id"]] = record
        return record

    @classmethod
    def list_recoveries(
        cls,
        *,
        agency_id: str,
        trip_id: Optional[str] = None,
        status: Optional[str] = None,
        source_type: Optional[str] = None,
        limit: int = 200,
    ) -> List[Dict[str, Any]]:
        if cls.backend() == "sql":
            cls._ensure_table()
            rows = cls._run(cls._sql_list(agency_id, trip_id, status, source_type, limit))
            return [cls._sql_row_to_dict(r) for r in rows]
        with cls._MEMORY_LOCK:
            records = [
                r
                for r in cls._MEMORY_STORE.values()
                if r["agency_id"] == agency_id
                and (trip_id is None or r["trip_id"] == trip_id)
                and (status is None or r["status"] == status)
                and (source_type is None or r["source_type"] == source_type)
            ]
            return sorted(records, key=lambda r: r["created_at"], reverse=True)[: max(1, limit)]

    @classmethod
    def get_recovery(cls, *, agency_id: str, recovery_id: str) -> Optional[Dict[str, Any]]:
        if cls.backend() == "sql":
            row = cls._run(cls._sql_get(agency_id, recovery_id))
            return cls._sql_row_to_dict(row) if row else None
        with cls._MEMORY_LOCK:
            record = cls._MEMORY_STORE.get(recovery_id)
            if record is None or record["agency_id"] != agency_id:
                return None
            return dict(record)

    @classmethod
    def transition_recovery(
        cls,
        *,
        agency_id: str,
        recovery_id: str,
        to_status: str,
        actor: str,
        amount: Optional[float] = None,
        amount_basis: Optional[str] = None,
        note: Optional[str] = None,
    ) -> Dict[str, Any]:
        """CAS lifecycle transition. Rejected→filed re-files (appeal). Amount
        may be set/updated at accepted/paid/credited (e.g. confirmed amount
        replacing the statutory model)."""
        if to_status not in RECOVERY_STATUSES:
            raise ValueError(f"Invalid status: {to_status}. Valid: {sorted(RECOVERY_STATUSES)}")
        if amount is not None or amount_basis is not None:
            cls._validate(
                agency_id=agency_id,
                source_type="manual",  # source-type-agnostic validation
                status="detected",
                amount=amount,
                amount_basis=amount_basis,
            )

        current: Optional[Dict[str, Any]] = None
        if cls.backend() == "sql":
            row = cls._run(cls._sql_get(agency_id, recovery_id))
            current = cls._sql_row_to_dict(row) if row else None
        else:
            with cls._MEMORY_LOCK:
                record = cls._MEMORY_STORE.get(recovery_id)
                if record is not None and record["agency_id"] == agency_id:
                    current = dict(record)
        if current is None:
            raise LookupError(f"Recovery not found: {recovery_id}")

        from_status = current["status"]
        if to_status not in _TRANSITIONS.get(from_status, set()):
            raise ValueError(
                f"Invalid transition {from_status} → {to_status}. Allowed: {sorted(_TRANSITIONS.get(from_status, set()))}"
            )

        if cls.backend() == "sql":
            cls._run(cls._sql_transition(agency_id, recovery_id, from_status, to_status, amount, amount_basis, actor, note))
        else:
            with cls._MEMORY_LOCK:
                record = cls._MEMORY_STORE[recovery_id]
                record["status"] = to_status
                record["updated_at"] = _now().isoformat()
                if amount is not None:
                    record["amount"] = round(float(amount), 2)
                if amount_basis is not None:
                    record["amount_basis"] = amount_basis
                if note:
                    record["details"] = {**(record.get("details") or {}), "last_transition_note": note[:2000]}
        updated = cls.get_recovery(agency_id=agency_id, recovery_id=recovery_id)
        return updated  # type: ignore[return-value]

    @classmethod
    def open_exists(cls, *, agency_id: str, trip_id: str, source_type: str) -> bool:
        """True when a non-terminal recovery already exists for this trip and
        source — the idempotency guard producers use to avoid duplicates."""
        for r in cls.list_recoveries(agency_id=agency_id, trip_id=trip_id, source_type=source_type):
            if r["status"] not in RECOVERY_TERMINAL_STATUSES:
                return True
        return False

    # ------------------------------------------------------------------
    # SQL backend
    # ------------------------------------------------------------------

    @classmethod
    def _sql_insert(cls, record: Dict[str, Any]) -> None:
        cls._ensure_table()

        async def _go() -> None:
            async with cls._rls_session(record["agency_id"]) as session:
                session.add(
                    RecoveryModel(
                        recovery_id=record["recovery_id"],
                        agency_id=record["agency_id"],
                        trip_id=record["trip_id"],
                        traveler_ref=record["traveler_ref"],
                        source_type=record["source_type"],
                        counterparty=record["counterparty"],
                        amount=record["amount"],
                        currency=record["currency"],
                        amount_basis=record["amount_basis"],
                        status=record["status"],
                        details=json.dumps(record["details"], ensure_ascii=False) if record.get("details") else None,
                        deadline_at=datetime.fromisoformat(record["deadline_at"]) if record.get("deadline_at") else None,
                        created_by=record["created_by"],
                        created_at=datetime.fromisoformat(record["created_at"]),
                        updated_at=datetime.fromisoformat(record["updated_at"]),
                    )
                )
                await session.commit()

        cls._run(_go())

    @staticmethod
    def _sql_row_to_dict(row: Any) -> Dict[str, Any]:
        return {
            "recovery_id": row.recovery_id,
            "agency_id": row.agency_id,
            "trip_id": row.trip_id,
            "traveler_ref": row.traveler_ref,
            "source_type": row.source_type,
            "counterparty": row.counterparty,
            "amount": float(row.amount) if row.amount is not None else None,
            "currency": row.currency,
            "amount_basis": row.amount_basis,
            "status": row.status,
            "details": json.loads(row.details) if isinstance(row.details, str) else row.details,
            "deadline_at": row.deadline_at.isoformat() if row.deadline_at else None,
            "created_by": row.created_by,
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "updated_at": row.updated_at.isoformat() if row.updated_at else None,
            "storage_backend": "sql",
        }

    @classmethod
    async def _sql_list(cls, agency_id: str, trip_id: Optional[str], status: Optional[str], source_type: Optional[str], limit: int):
        from sqlalchemy import select

        async with cls._rls_session(agency_id) as session:
            stmt = select(RecoveryModel).where(RecoveryModel.agency_id == agency_id)
            if trip_id:
                stmt = stmt.where(RecoveryModel.trip_id == trip_id)
            if status:
                stmt = stmt.where(RecoveryModel.status == status)
            if source_type:
                stmt = stmt.where(RecoveryModel.source_type == source_type)
            stmt = stmt.order_by(RecoveryModel.created_at.desc()).limit(max(1, limit))
            result = await session.execute(stmt)
            return result.scalars().all()

    @classmethod
    async def _sql_get(cls, agency_id: str, recovery_id: str):
        cls._ensure_table()
        from sqlalchemy import select

        async with cls._rls_session(agency_id) as session:
            result = await session.execute(
                select(RecoveryModel).where(
                    RecoveryModel.recovery_id == recovery_id,
                    RecoveryModel.agency_id == agency_id,
                )
            )
            return result.scalar_one_or_none()

    @classmethod
    async def _sql_transition(
        cls,
        agency_id: str,
        recovery_id: str,
        from_status: str,
        to_status: str,
        amount: Optional[float],
        amount_basis: Optional[str],
        actor: str,
        note: Optional[str],
    ) -> None:
        from sqlalchemy import select

        async with cls._rls_session(agency_id) as session:
            result = await session.execute(
                select(RecoveryModel).where(
                    RecoveryModel.recovery_id == recovery_id,
                    RecoveryModel.agency_id == agency_id,
                )
            )
            row = result.scalar_one_or_none()
            if row is None or row.status != from_status:
                raise LookupError(f"Recovery {recovery_id} no longer in state {from_status} (CAS guard)")
            row.status = to_status
            if amount is not None:
                row.amount = round(float(amount), 2)
            if amount_basis is not None:
                row.amount_basis = amount_basis
            if note:
                details = json.loads(row.details) if isinstance(row.details, str) else (row.details or {})
                details["last_transition_note"] = note[:2000]
                row.details = json.dumps(details, ensure_ascii=False)
            row.updated_at = _now()
            await session.commit()
