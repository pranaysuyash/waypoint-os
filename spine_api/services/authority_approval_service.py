"""
spine_api/services/authority_approval_service.py — Durable Dual-Control Approval Ledger (PA-08).

Records and ratifies dual-control authority approvals: when a governance
registry cap denies an execution path (``AuthorityApprovalRequired``), a
human operator requests an approval for the exact (agency, action, subject,
amount) and TWO DISTINCT owner/admin users must approve it before the path
may proceed. The ratified record is the audit-proof answer to "which two
humans authorized this over-cap action, and when?".

Design constraints carried from the findings family:

- Dual control is real: the same user can never be both approvers (CAS-guarded,
  409-class conflict), and only owner/admin roles may approve (403-class).
- Tenancy: every operation is agency-scoped; the SQL backend runs inside the
  canonical RLS session helper so rows are filtered exactly like trips.
- Honest provenance: responses declare ``storage_backend``. The default
  ``memory`` backend is an in-process preview (single-worker, not durable),
  mirroring ``payment_mandate_service``; SQL is selected via
  ``SPINE_API_AUTHORITY_APPROVAL_BACKEND=sql`` (or automatically in
  production when a ``DATABASE_URL`` is configured).
- CAS transitions: first/second approval and denial are single-statement
  compare-and-set updates (``WHERE status='pending_second'`` and the
  approver-slot guards) — two racing writers can never both become the
  "second" approver.
"""

from __future__ import annotations

import os
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

STATUS_PENDING_SECOND = "pending_second"
STATUS_APPROVED = "approved"
STATUS_DENIED = "denied"

APPROVER_ROLES = frozenset({"owner", "admin"})


class ApprovalNotAuthorized(ValueError):
    """403-class: the caller's role may not approve/deny this request."""


class ApprovalConflict(ValueError):
    """409-class: same-person double approval or a non-pending record."""


@dataclass(slots=True)
class ApprovalRecord:
    approval_id: str
    agency_id: str
    action: str
    subject_type: str
    subject_id: str
    requested_by: str
    status: str = STATUS_PENDING_SECOND
    amount_usd: Optional[float] = None
    reason: Optional[str] = None
    first_approver_id: Optional[str] = None
    first_approved_at: Optional[str] = None
    second_approver_id: Optional[str] = None
    second_approved_at: Optional[str] = None
    denial_reason: Optional[str] = None
    created_at: str = field(default_factory=lambda: _now().isoformat())
    updated_at: str = field(default_factory=lambda: _now().isoformat())
    storage_backend: str = field(default="memory")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "approval_id": self.approval_id,
            "agency_id": self.agency_id,
            "action": self.action,
            "subject_type": self.subject_type,
            "subject_id": self.subject_id,
            "amount_usd": self.amount_usd,
            "requested_by": self.requested_by,
            "status": self.status,
            "reason": self.reason,
            "first_approver_id": self.first_approver_id,
            "first_approved_at": self.first_approved_at,
            "second_approver_id": self.second_approver_id,
            "second_approved_at": self.second_approved_at,
            "denial_reason": self.denial_reason,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "storage_backend": self.storage_backend,
        }


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _backend() -> str:
    raw = (os.environ.get("SPINE_API_AUTHORITY_APPROVAL_BACKEND") or "").strip().lower()
    if raw in ("postgres", "postgresql"):
        return "sql"
    if raw in ("memory", "sql"):
        return raw
    # Production default: durable SQL when a database is configured. Tests
    # and local preview stay on memory (mirror payment_mandate_service).
    environment = os.environ.get("ENVIRONMENT", "development").strip().lower()
    if environment in ("production", "prod") and os.environ.get("DATABASE_URL"):
        return "sql"
    return "memory"


def _require_approver_role(approver_role: Optional[str]) -> None:
    role = (approver_role or "").strip().lower()
    if role not in APPROVER_ROLES:
        raise ApprovalNotAuthorized(
            f"Role {approver_role!r} may not ratify authority approvals; "
            f"one of {sorted(APPROVER_ROLES)} is required."
        )


class AuthorityApprovalLedger:
    """Dual-control approval ledger. All operations are agency-scoped."""

    _MEMORY_LOCK = threading.Lock()
    _MEMORY_STORE: Dict[str, ApprovalRecord] = {}

    # ------------------------------------------------------------------
    # Request
    # ------------------------------------------------------------------

    @classmethod
    def request_approval(
        cls,
        *,
        agency_id: str,
        action: str,
        subject_type: str,
        subject_id: str,
        requested_by: str,
        amount_usd: Optional[float] = None,
        reason: Optional[str] = None,
    ) -> ApprovalRecord:
        if not agency_id:
            raise ValueError("agency_id is required for an authority approval.")
        if not action:
            raise ValueError("action is required for an authority approval.")
        if not subject_type:
            raise ValueError("subject_type is required for an authority approval.")
        if not subject_id:
            raise ValueError("subject_id is required for an authority approval.")
        if not requested_by:
            raise ValueError("requested_by is required for an authority approval.")
        if amount_usd is not None and float(amount_usd) < 0:
            raise ValueError("amount_usd must be non-negative when provided.")

        backend = _backend()
        record = ApprovalRecord(
            approval_id=f"APR-{uuid.uuid4().hex[:12].upper()}",
            agency_id=agency_id,
            action=action,
            subject_type=subject_type,
            subject_id=subject_id,
            requested_by=requested_by,
            amount_usd=float(amount_usd) if amount_usd is not None else None,
            reason=(reason or None),
            storage_backend="sql" if backend == "sql" else "memory",
        )
        if backend == "sql":
            cls._sql_insert(record)
        else:
            with cls._MEMORY_LOCK:
                cls._MEMORY_STORE[record.approval_id] = record
        return record

    # ------------------------------------------------------------------
    # Ratification (CAS approve / deny)
    # ------------------------------------------------------------------

    @classmethod
    def approve(
        cls,
        *,
        agency_id: str,
        approval_id: str,
        approver_user_id: str,
        approver_role: str,
    ) -> ApprovalRecord:
        """Record one approval leg. First distinct approval fills the first
        slot; a second DISTINCT owner/admin approval ratifies the record."""
        _require_approver_role(approver_role)
        if not approver_user_id:
            raise ValueError("approver_user_id is required.")
        if _backend() == "sql":
            return cls._sql_approve(agency_id, approval_id, approver_user_id)
        return cls._memory_approve(agency_id, approval_id, approver_user_id)

    @classmethod
    def deny(
        cls,
        *,
        agency_id: str,
        approval_id: str,
        approver_user_id: str,
        approver_role: str,
        reason: Optional[str] = None,
    ) -> ApprovalRecord:
        """CAS-deny a pending request (only a pending record can be denied)."""
        _require_approver_role(approver_role)
        if _backend() == "sql":
            return cls._sql_deny(agency_id, approval_id, approver_user_id, reason)
        with cls._MEMORY_LOCK:
            record = cls._MEMORY_STORE.get(approval_id)
            if record is None or record.agency_id != agency_id:
                raise ValueError(f"Approval '{approval_id}' not found.")
            if record.status != STATUS_PENDING_SECOND:
                raise ApprovalConflict(
                    f"Approval '{approval_id}' is in '{record.status}' status and can no longer be denied."
                )
            record.status = STATUS_DENIED
            record.denial_reason = (reason or "")[:500] or None
            record.updated_at = _now().isoformat()
            return record

    # ------------------------------------------------------------------
    # Reads / execution-time lookup (the seam fulfillment + payouts call)
    # ------------------------------------------------------------------

    @classmethod
    def get_approved(cls, *, agency_id: str, action: str, subject_id: str) -> Optional[Dict[str, Any]]:
        """Newest APPROVED record for (agency, action, subject), or None."""
        approvals = cls.list_approvals(agency_id=agency_id, action=action, subject_id=subject_id)
        for row in approvals:
            if row["status"] == STATUS_APPROVED:
                return row
        return None

    @classmethod
    def get_approval(cls, *, agency_id: str, approval_id: str) -> Optional[Dict[str, Any]]:
        if _backend() == "sql":
            row = cls._sql_get(agency_id, approval_id)
            return cls._sql_row_to_dict(row) if row else None
        with cls._MEMORY_LOCK:
            record = cls._MEMORY_STORE.get(approval_id)
            if record is None or record.agency_id != agency_id:
                return None
            return record.to_dict()

    @staticmethod
    def subject_agency_id(subject_type: str, subject_id: str) -> Optional[str]:
        """Resolve the owning agency of an approval subject (tenancy anchor).

        Approvals are agency-scoped, but the requesting execution path may only
        know the subject id (e.g. a fulfillment router that holds a trip id).
        This resolves the subject's owning agency so the ratified-approval
        lookup stays tenant-correct. Service-layer resolution mirrors how the
        orchestration layer derives ``agency_scope`` from the trip record;
        routers must not perform unscoped trip reads (CI gate
        ``check_unscoped_trip_access.sh``).
        """
        if subject_type == "trip":
            from spine_api.persistence import TripStore

            trip = TripStore.get_trip(subject_id)
            if not trip:
                return None
            return str(trip.get("agency_id") or "system")
        return None

    @classmethod
    def list_approvals(
        cls,
        *,
        agency_id: str,
        action: Optional[str] = None,
        subject_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        if _backend() == "sql":
            rows = cls._sql_list(agency_id, action, subject_id, status)
            return [cls._sql_row_to_dict(r) for r in rows]
        with cls._MEMORY_LOCK:
            records = [
                r
                for r in cls._MEMORY_STORE.values()
                if r.agency_id == agency_id
                and (action is None or r.action == action)
                and (subject_id is None or r.subject_id == subject_id)
                and (status is None or r.status == status)
            ]
            return [r.to_dict() for r in sorted(records, key=lambda x: x.created_at, reverse=True)]

    # ------------------------------------------------------------------
    # Memory backend (CAS under lock)
    # ------------------------------------------------------------------

    @classmethod
    def _memory_approve(cls, agency_id: str, approval_id: str, approver_user_id: str) -> ApprovalRecord:
        with cls._MEMORY_LOCK:
            record = cls._MEMORY_STORE.get(approval_id)
            if record is None or record.agency_id != agency_id:
                raise ValueError(f"Approval '{approval_id}' not found.")
            if record.status != STATUS_PENDING_SECOND:
                raise ApprovalConflict(
                    f"Approval '{approval_id}' is in '{record.status}' status and can no longer be approved."
                )
            if record.first_approver_id is not None and record.first_approver_id == approver_user_id:
                raise ApprovalConflict(
                    "Dual control violation: the same user cannot provide both approvals."
                )
            now_iso = _now().isoformat()
            if record.first_approver_id is None:
                record.first_approver_id = approver_user_id
                record.first_approved_at = now_iso
            elif record.first_approver_id != approver_user_id:
                record.second_approver_id = approver_user_id
                record.second_approved_at = now_iso
                record.status = STATUS_APPROVED
            record.updated_at = now_iso
            return record

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
        from spine_api.models.authority_approval import AuthorityApprovalModel

        if getattr(cls, "_ensure_table_done", False):
            return

        # Idempotent tenant RLS posture — matches the alembic revision
        # (pa_wave2_authority_payouts_cost) so lazily-created tables get the
        # same isolation as migration-created ones, in either ordering.
        _RLS_STATEMENTS = (
            text("ALTER TABLE authority_approvals ENABLE ROW LEVEL SECURITY"),
            text("ALTER TABLE authority_approvals FORCE ROW LEVEL SECURITY"),
            text(
                """
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_policy
                        WHERE polrelid = 'authority_approvals'::regclass
                          AND polname = 'waypoint_rls_select'
                    ) THEN
                        CREATE POLICY waypoint_rls_select ON authority_approvals
                            FOR SELECT USING (
                                agency_id = current_setting('app.current_agency_id', TRUE)
                            );
                    END IF;
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_policy
                        WHERE polrelid = 'authority_approvals'::regclass
                          AND polname = 'waypoint_rls_all'
                    ) THEN
                        CREATE POLICY waypoint_rls_all ON authority_approvals
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
                        sync_conn, tables=[AuthorityApprovalModel.__table__], checkfirst=True
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
    def _sql_insert(cls, record: ApprovalRecord) -> None:
        cls._ensure_table()

        async def _go() -> None:
            from spine_api.models.authority_approval import AuthorityApprovalModel

            async with cls._rls_session(record.agency_id) as session:
                session.add(
                    AuthorityApprovalModel(
                        approval_id=record.approval_id,
                        agency_id=record.agency_id,
                        action=record.action,
                        subject_type=record.subject_type,
                        subject_id=record.subject_id,
                        amount_usd=record.amount_usd,
                        requested_by=record.requested_by,
                        status=record.status,
                        reason=record.reason,
                        created_at=datetime.fromisoformat(record.created_at),
                        updated_at=datetime.fromisoformat(record.updated_at),
                    )
                )
                await session.commit()

        cls._run(_go())

    @staticmethod
    def _sql_row_to_dict(row: Any) -> Dict[str, Any]:
        return {
            "approval_id": row.approval_id,
            "agency_id": row.agency_id,
            "action": row.action,
            "subject_type": row.subject_type,
            "subject_id": row.subject_id,
            "amount_usd": float(row.amount_usd) if row.amount_usd is not None else None,
            "requested_by": row.requested_by,
            "status": row.status,
            "reason": row.reason,
            "first_approver_id": row.first_approver_id,
            "first_approved_at": row.first_approved_at.isoformat() if row.first_approved_at else None,
            "second_approver_id": row.second_approver_id,
            "second_approved_at": row.second_approved_at.isoformat() if row.second_approved_at else None,
            "denial_reason": row.denial_reason,
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "updated_at": row.updated_at.isoformat() if row.updated_at else None,
            "storage_backend": "sql",
        }

    @classmethod
    def _sql_get(cls, agency_id: str, approval_id: str) -> Any:
        cls._ensure_table()

        async def _go():
            from sqlalchemy import select

            from spine_api.models.authority_approval import AuthorityApprovalModel

            async with cls._rls_session(agency_id) as session:
                result = await session.execute(
                    select(AuthorityApprovalModel).where(
                        AuthorityApprovalModel.approval_id == approval_id,
                        AuthorityApprovalModel.agency_id == agency_id,
                    )
                )
                return result.scalar_one_or_none()

        return cls._run(_go())

    @classmethod
    def _sql_list(
        cls,
        agency_id: str,
        action: Optional[str],
        subject_id: Optional[str],
        status: Optional[str],
    ) -> List[Any]:
        cls._ensure_table()

        async def _go():
            from sqlalchemy import select

            from spine_api.models.authority_approval import AuthorityApprovalModel

            async with cls._rls_session(agency_id) as session:
                stmt = select(AuthorityApprovalModel).where(
                    AuthorityApprovalModel.agency_id == agency_id
                )
                if action is not None:
                    stmt = stmt.where(AuthorityApprovalModel.action == action)
                if subject_id is not None:
                    stmt = stmt.where(AuthorityApprovalModel.subject_id == subject_id)
                if status is not None:
                    stmt = stmt.where(AuthorityApprovalModel.status == status)
                stmt = stmt.order_by(AuthorityApprovalModel.created_at.desc())
                result = await session.execute(stmt)
                return result.scalars().all()

        return cls._run(_go())

    @classmethod
    def _sql_approve(cls, agency_id: str, approval_id: str, approver_user_id: str) -> ApprovalRecord:
        cls._ensure_table()

        async def _go() -> ApprovalRecord:
            from sqlalchemy import select, update

            from spine_api.models.authority_approval import AuthorityApprovalModel

            async with cls._rls_session(agency_id) as session:
                # Attempt 1 — CAS the FIRST approver slot on a fresh record.
                first = await session.execute(
                    update(AuthorityApprovalModel)
                    .where(
                        AuthorityApprovalModel.approval_id == approval_id,
                        AuthorityApprovalModel.agency_id == agency_id,
                        AuthorityApprovalModel.status == STATUS_PENDING_SECOND,
                        AuthorityApprovalModel.first_approver_id.is_(None),
                    )
                    .values(
                        first_approver_id=approver_user_id,
                        first_approved_at=_now(),
                        updated_at=_now(),
                    )
                )
                if not first.rowcount:
                    # Attempt 2 — CAS the SECOND (distinct) approver slot.
                    second = await session.execute(
                        update(AuthorityApprovalModel)
                        .where(
                            AuthorityApprovalModel.approval_id == approval_id,
                            AuthorityApprovalModel.agency_id == agency_id,
                            AuthorityApprovalModel.status == STATUS_PENDING_SECOND,
                            AuthorityApprovalModel.first_approver_id.is_not(None),
                            AuthorityApprovalModel.first_approver_id != approver_user_id,
                            AuthorityApprovalModel.second_approver_id.is_(None),
                        )
                        .values(
                            status=STATUS_APPROVED,
                            second_approver_id=approver_user_id,
                            second_approved_at=_now(),
                            updated_at=_now(),
                        )
                    )
                    if not second.rowcount:
                        # Refusal reason: read current state in the SAME
                        # transaction (the RLS context dies with it).
                        current = await session.execute(
                            select(AuthorityApprovalModel).where(
                                AuthorityApprovalModel.approval_id == approval_id,
                                AuthorityApprovalModel.agency_id == agency_id,
                            )
                        )
                        existing = current.scalar_one_or_none()
                        await session.commit()  # nothing mutated; close the tx cleanly
                        if existing is None:
                            raise ValueError(f"Approval '{approval_id}' not found.")
                        if existing.status != STATUS_PENDING_SECOND:
                            raise ApprovalConflict(
                                f"Approval '{approval_id}' is in '{existing.status}' status "
                                "and can no longer be approved."
                            )
                        raise ApprovalConflict(
                            "Dual control violation: the same user cannot provide both approvals."
                        )
                result = await session.execute(
                    select(AuthorityApprovalModel).where(
                        AuthorityApprovalModel.approval_id == approval_id,
                        AuthorityApprovalModel.agency_id == agency_id,
                    )
                )
                row = result.scalar_one_or_none()
                await session.commit()
                return cls._record_from_row(row)

        return cls._run(_go())

    @classmethod
    def _sql_deny(
        cls,
        agency_id: str,
        approval_id: str,
        approver_user_id: str,
        reason: Optional[str],
    ) -> ApprovalRecord:
        cls._ensure_table()

        async def _go() -> ApprovalRecord:
            from sqlalchemy import select, update

            from spine_api.models.authority_approval import AuthorityApprovalModel

            async with cls._rls_session(agency_id) as session:
                result = await session.execute(
                    update(AuthorityApprovalModel)
                    .where(
                        AuthorityApprovalModel.approval_id == approval_id,
                        AuthorityApprovalModel.agency_id == agency_id,
                        AuthorityApprovalModel.status == STATUS_PENDING_SECOND,
                    )
                    .values(
                        status=STATUS_DENIED,
                        denial_reason=((reason or "")[:500] or None),
                        updated_at=_now(),
                    )
                )
                if not result.rowcount:
                    current = await session.execute(
                        select(AuthorityApprovalModel).where(
                            AuthorityApprovalModel.approval_id == approval_id,
                            AuthorityApprovalModel.agency_id == agency_id,
                        )
                    )
                    existing = current.scalar_one_or_none()
                    await session.commit()
                    if existing is None:
                        raise ValueError(f"Approval '{approval_id}' not found.")
                    raise ApprovalConflict(
                        f"Approval '{approval_id}' is in '{existing.status}' status "
                        "and can no longer be denied."
                    )
                readback = await session.execute(
                    select(AuthorityApprovalModel).where(
                        AuthorityApprovalModel.approval_id == approval_id,
                        AuthorityApprovalModel.agency_id == agency_id,
                    )
                )
                row = readback.scalar_one_or_none()
                await session.commit()
                return cls._record_from_row(row)

        return cls._run(_go())

    @staticmethod
    def _record_from_row(row: Any) -> ApprovalRecord:
        return ApprovalRecord(
            approval_id=row.approval_id,
            agency_id=row.agency_id,
            action=row.action,
            subject_type=row.subject_type,
            subject_id=row.subject_id,
            requested_by=row.requested_by,
            status=row.status,
            amount_usd=float(row.amount_usd) if row.amount_usd is not None else None,
            reason=row.reason,
            first_approver_id=row.first_approver_id,
            first_approved_at=row.first_approved_at.isoformat() if row.first_approved_at else None,
            second_approver_id=row.second_approver_id,
            second_approved_at=row.second_approved_at.isoformat() if row.second_approved_at else None,
            denial_reason=row.denial_reason,
            created_at=row.created_at.isoformat() if row.created_at else "",
            updated_at=row.updated_at.isoformat() if row.updated_at else "",
            storage_backend="sql",
        )
