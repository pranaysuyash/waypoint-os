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

FND-0221 extension (2026-09-14, additive — no schema ALTER, no parallel
ledger): the mandate gained the payer-authorization shape —

- ``payer_ref`` / ``granted_by`` / ``granted_at``: the authenticated principal
  who granted the mandate (JWT-bound at the granting router), matching the
  ADR-008 money-principal binding posture.
- ``scope``: deposit | balance | fee | payout. Legacy purpose-only mandates
  keep working via the purpose→scope map (INITIAL_DEPOSIT/SPLIT_INSTALLMENT →
  deposit, FINAL_BALANCE → balance, SUPPLIER_INCIDENTAL_HOLD → fee); a
  payout-scope mandate can never satisfy a traveler deposit movement and
  vice versa.
- ``idempotency_key``: grant idempotency — re-granting with the same key
  returns the SAME mandate (no duplicate consent rows).
- movement idempotency: ``authorize_charge(movement_idempotency_key=...)``
  executes a money movement once — a replay with the same key returns the
  stored outcome without consuming headroom again (no double movement).
- ``revoked_at`` / ``revoked_by`` recorded on CAS revocation.

New fields persist in the existing ``payment_mandates.mandate_metadata``
JSONB column (namespaced under ``fnd0221``; movement outcomes under
``movements``) — the additive-only path that requires no ALTER of the
existing table (repo constraint: create-only migrations).
"""

from __future__ import annotations

import hashlib
import os
import threading
import uuid
from dataclasses import dataclass, field, fields as dataclass_fields
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

VALID_PURPOSES = (
    "INITIAL_DEPOSIT",
    "SPLIT_INSTALLMENT",
    "FINAL_BALANCE",
    "SUPPLIER_INCIDENTAL_HOLD",
)

# FND-0221 canonical movement scopes. Every money movement must chain to a
# mandate whose scope covers it.
VALID_SCOPES = ("deposit", "balance", "fee", "payout")

# Legacy purpose-only mandates resolve to a scope through this map so the
# scope check composes with pre-FND-0221 rows without any data migration.
_PURPOSE_TO_SCOPE = {
    "INITIAL_DEPOSIT": "deposit",
    "SPLIT_INSTALLMENT": "deposit",
    "FINAL_BALANCE": "balance",
    "SUPPLIER_INCIDENTAL_HOLD": "fee",
}

# Normalized lifecycle triad (FND-0221): granted | revoked | expired.
_STATE_MAP = {
    "ACTIVE": "granted",
    "CONSUMED": "granted",
    "REVOKED": "revoked",
    "EXPIRED": "expired",
}


def resolved_scope(record: Any) -> str:
    """Scope a mandate (record or dict) covers, deriving from purpose for
    legacy rows. Empty string = unknown (never matches a required scope)."""
    if isinstance(record, dict):
        scope = record.get("scope") or ""
        purpose = record.get("purpose") or ""
    else:
        scope = record.scope or ""
        purpose = record.purpose or ""
    return scope or _PURPOSE_TO_SCOPE.get(purpose, "")


def mandate_state(status: str) -> str:
    """Normalize the stored status into the FND-0221 lifecycle triad."""
    return _STATE_MAP.get((status or "").upper(), (status or "").lower())


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
    # FND-0221 payer-authorization shape. All persisted via mandate_metadata.
    scope: str = ""
    payer_ref: str = ""
    granted_by: str = ""
    revoked_at: Optional[str] = None
    revoked_by: str = ""
    idempotency_key: Optional[str] = None
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
            # FND-0221 aliases/shapes: granted_at == signed_at, evidence_ref ==
            # consent_artifact_ref (the proposal id / approval event showing
            # what the payer agreed to), mandate_state = lifecycle triad.
            "granted_at": self.signed_at,
            "evidence_ref": self.consent_artifact_ref,
            "mandate_state": mandate_state(self.status),
            "scope": resolved_scope(self),
            "payer_ref": self.payer_ref,
            "granted_by": self.granted_by or self.payer_ref,
            "revoked_at": self.revoked_at,
            "revoked_by": self.revoked_by,
            "idempotency_key": self.idempotency_key,
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
    # FND-0221 movement idempotency: (agency_id, movement_key) -> first
    # execution outcome. A replay with the same key returns this snapshot
    # instead of consuming headroom a second time.
    _MOVEMENT_OUTCOMES: Dict[Tuple[str, str], Dict[str, Any]] = {}

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
        scope: str = "",
        payer_ref: str = "",
        granted_by: str = "",
        idempotency_key: Optional[str] = None,
        evidence_ref: str = "",
    ) -> MandateRecord:
        """Record a payment mandate. ``consent_artifact_ref`` is REQUIRED and
        must point at the durable consent artifact (e-sign acceptance token /
        audit event id) — a mandate without one is the decorative ledger the
        findings family forbids. ``evidence_ref`` is an accepted alias for the
        same artifact (FND-0221 naming).

        FND-0221: ``scope`` is one of deposit | balance | fee | payout
        (default derived from ``purpose``); ``payer_ref`` is the authenticated
        principal who granted the mandate; ``idempotency_key`` makes granting
        idempotent — the same key returns the SAME mandate, never a duplicate.
        """
        if not agency_id:
            raise ValueError("agency_id is required for a payment mandate.")
        if not trip_id:
            raise ValueError("trip_id is required for a payment mandate.")
        if scope and scope not in VALID_SCOPES:
            raise ValueError(f"scope must be one of {VALID_SCOPES}; got {scope!r}")
        if purpose not in VALID_PURPOSES:
            if scope in VALID_SCOPES and not purpose:
                # FND-0221: scope-driven mandates (e.g. payout) are purpose-free —
                # the customer-payment purpose vocabulary does not apply.
                purpose = ""
            else:
                raise ValueError(f"purpose must be one of {VALID_PURPOSES}; got {purpose!r}")
        if max_authorized_cents <= 0:
            raise ValueError("max_authorized_cents must be positive.")
        if not consent_text:
            raise ValueError("consent_text is required (only its digest is stored).")
        consent_artifact_ref = consent_artifact_ref or evidence_ref
        if not consent_artifact_ref:
            raise ValueError(
                "consent_artifact_ref is required: a mandate must reference the "
                "durable consent artifact (acceptance token / audit event) that "
                "carries the traveler's authorization."
            )

        # Grant idempotency: same agency + idempotency_key → the SAME mandate
        # is returned (same outcome), never a duplicate consent row.
        if idempotency_key:
            existing = cls.find_by_idempotency_key(
                agency_id=agency_id, idempotency_key=idempotency_key
            )
            if existing is not None:
                return existing

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
            scope=scope or _PURPOSE_TO_SCOPE.get(purpose, ""),
            payer_ref=payer_ref,
            granted_by=granted_by or payer_ref,
            idempotency_key=idempotency_key,
            storage_backend="sql" if backend == "sql" else "memory",
        )
        if backend == "sql":
            cls._sql_insert(record)
        else:
            with cls._MEMORY_LOCK:
                cls._MEMORY_STORE[record.mandate_id] = record
        return record

    @classmethod
    def find_by_idempotency_key(
        cls, *, agency_id: str, idempotency_key: str
    ) -> Optional[MandateRecord]:
        """The mandate previously granted under this idempotency key, if any."""
        if not idempotency_key:
            return None
        if _backend() == "sql":
            row = cls._sql_find_by_idempotency_key(agency_id, idempotency_key)
            return cls._row_to_record(row) if row is not None else None
        with cls._MEMORY_LOCK:
            for record in cls._MEMORY_STORE.values():
                if record.agency_id == agency_id and record.idempotency_key == idempotency_key:
                    return record
        return None

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
        scope: Optional[str] = None,
        movement_idempotency_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """CAS-authorize ``amount_cents`` against an ACTIVE, unexpired mandate.

        Refuses (authorized=False) when the mandate is missing, revoked,
        expired, out of scope, or has insufficient remaining authorization —
        never partially consumes. Returns the updated snapshot on success.

        FND-0221: ``scope`` (when given) must match the mandate's resolved
        scope — a payout mandate never covers a traveler deposit and vice
        versa. ``movement_idempotency_key`` makes the MOVEMENT idempotent:
        the first execution consumes and stores the outcome; a replay with
        the same key returns the stored outcome (``replayed: True``) without
        consuming again — same key, same outcome, no double movement.
        """
        if amount_cents <= 0:
            return {"authorized": False, "reason": "amount_cents must be positive."}

        # Movement replay fast path: the stored first-execution outcome IS the
        # outcome of the replay (no re-consumption).
        if movement_idempotency_key:
            stored = cls._stored_movement_outcome(agency_id, movement_idempotency_key)
            if stored is not None:
                return {**stored, "replayed": True}

        if _backend() == "sql":
            return cls._sql_authorize(
                agency_id, mandate_id, int(amount_cents), scope, movement_idempotency_key
            )
        return cls._memory_authorize(
            agency_id, mandate_id, int(amount_cents), scope, movement_idempotency_key
        )

    @classmethod
    def resolve_for_trip(
        cls,
        *,
        agency_id: str,
        trip_id: str,
        allowed_scopes: Optional[Tuple[str, ...]] = None,
    ) -> Optional[MandateRecord]:
        """Newest ACTIVE, unexpired mandate for a trip, if any.

        FND-0221: ``allowed_scopes`` restricts which mandate scopes may cover
        the caller's movement class (e.g. fulfillment deposits accept
        deposit/balance/fee but never payout).
        """
        candidates = [
            m
            for m in cls.list_mandates(agency_id=agency_id, trip_id=trip_id)
            if m["status"] == "ACTIVE"
        ]
        if allowed_scopes is not None:
            candidates = [m for m in candidates if resolved_scope(m) in allowed_scopes]
        if not candidates:
            return None
        for m in sorted(candidates, key=lambda r: r["signed_at"], reverse=True):
            try:
                if datetime.fromisoformat(m["expires_at"]) > _now():
                    return cls._dict_to_record(m)
            except (TypeError, ValueError):
                continue
        return None

    @classmethod
    def _stored_movement_outcome(
        cls, agency_id: str, movement_key: str
    ) -> Optional[Dict[str, Any]]:
        """First-execution outcome previously recorded for this movement key
        (memory backend). The SQL backend checks movements on the mandate row
        inside ``_sql_authorize`` where the mandate id is in scope."""
        if _backend() == "sql":
            return None
        with cls._MEMORY_LOCK:
            return cls._MOVEMENT_OUTCOMES.get((agency_id, movement_key))

    @staticmethod
    def _record_fields() -> Tuple[str, ...]:
        return tuple(f.name for f in dataclass_fields(MandateRecord))

    @classmethod
    def _dict_to_record(cls, m: Dict[str, Any]) -> MandateRecord:
        """Build a MandateRecord from a to_dict() payload, dropping derived
        keys (granted_at/evidence_ref/mandate_state) that are not fields."""
        names = cls._record_fields()
        return MandateRecord(**{k: v for k, v in m.items() if k in names})

    @classmethod
    def _row_to_record(cls, row: Any) -> Optional[MandateRecord]:
        if row is None:
            return None
        return cls._dict_to_record(cls._sql_row_to_dict(row))

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
    def revoke_mandate(
        cls,
        *,
        agency_id: str,
        mandate_id: str,
        reason: str,
        revoked_by: str = "",
    ) -> bool:
        """CAS revocation: only an ACTIVE mandate can be revoked. FND-0221:
        records ``revoked_at`` and ``revoked_by`` with the revocation."""
        if _backend() == "sql":
            return cls._sql_revoke(agency_id, mandate_id, reason, revoked_by)
        with cls._MEMORY_LOCK:
            record = cls._MEMORY_STORE.get(mandate_id)
            if record is None or record.agency_id != agency_id:
                return False
            if record.status != "ACTIVE":
                return False
            record.status = "REVOKED"
            record.revocation_reason = reason[:500] if reason else reason
            record.revoked_at = _now().isoformat()
            record.revoked_by = revoked_by
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
    def _memory_authorize(
        cls,
        agency_id: str,
        mandate_id: str,
        amount_cents: int,
        scope: Optional[str] = None,
        movement_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        with cls._MEMORY_LOCK:
            record = cls._MEMORY_STORE.get(mandate_id)
            if record is None or record.agency_id != agency_id:
                return {"authorized": False, "reason": "Mandate not found in ledger."}
            cls._expire_if_due(record)
            if record.status != "ACTIVE":
                return {"authorized": False, "reason": f"Mandate is in {record.status} status."}
            if scope is not None:
                mandate_scope = resolved_scope(record)
                if mandate_scope != scope:
                    return {
                        "authorized": False,
                        "reason": (
                            f"Mandate scope '{mandate_scope or 'unknown'}' does not "
                            f"cover the requested movement scope '{scope}'."
                        ),
                        "mandate_id": record.mandate_id,
                        "mandate_scope": mandate_scope,
                        "requested_scope": scope,
                    }
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
            outcome = {
                "authorized": True,
                "mandate_id": record.mandate_id,
                "charged_cents": amount_cents,
                "remaining_authorized_cents": record.max_authorized_cents
                - record.consumed_amount_cents,
                "consent_text_sha256": record.consent_text_sha256,
                "status": record.status,
                "storage_backend": record.storage_backend,
            }
            if movement_key:
                outcome["movement_idempotency_key"] = movement_key
                cls._MOVEMENT_OUTCOMES[(agency_id, movement_key)] = dict(outcome)
            return outcome

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
    def _extension_metadata(cls, record: MandateRecord) -> Dict[str, Any]:
        """FND-0221 fields persisted in the existing ``mandate_metadata``
        JSONB column — additive-only (no ALTER of the existing table)."""
        return {
            "fnd0221": {
                "scope": record.scope or "",
                "payer_ref": record.payer_ref or "",
                "granted_by": record.granted_by or "",
                "idempotency_key": record.idempotency_key,
                "revoked_at": record.revoked_at,
                "revoked_by": record.revoked_by or "",
            }
        }

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
                        mandate_metadata=cls._extension_metadata(record),
                    )
                )
                await session.commit()

        cls._run(_go())

    @staticmethod
    def _sql_row_to_dict(row: Any) -> Dict[str, Any]:
        meta = getattr(row, "mandate_metadata", None) or {}
        ext = meta.get("fnd0221") if isinstance(meta, dict) else None
        ext = ext if isinstance(ext, dict) else {}
        signed_at = row.signed_at.isoformat() if row.signed_at else None
        d = {
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
            "signed_at": signed_at,
            "expires_at": row.expires_at.isoformat() if row.expires_at else None,
            "status": row.status,
            "consumed_amount_cents": row.consumed_amount_cents,
            "revocation_reason": row.revocation_reason,
            # FND-0221 fields merged back from mandate_metadata.
            "scope": ext.get("scope", ""),
            "payer_ref": ext.get("payer_ref", ""),
            "granted_by": ext.get("granted_by", ""),
            "revoked_at": ext.get("revoked_at"),
            "revoked_by": ext.get("revoked_by", ""),
            "idempotency_key": ext.get("idempotency_key"),
            # Derived aliases (same semantics as the memory backend to_dict).
            "granted_at": signed_at,
            "evidence_ref": row.consent_artifact_ref,
            "storage_backend": "sql",
        }
        d["mandate_state"] = mandate_state(d["status"])
        return d

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
    def _sql_find_by_idempotency_key(cls, agency_id: str, idempotency_key: str) -> Any:
        cls._ensure_table()

        async def _go():
            from sqlalchemy import select

            from spine_api.models.payment_mandate import PaymentMandateModel

            async with cls._rls_session(agency_id) as session:
                stmt = select(PaymentMandateModel).where(
                    PaymentMandateModel.agency_id == agency_id,
                    PaymentMandateModel.mandate_metadata["fnd0221"]["idempotency_key"]
                    .astext
                    == idempotency_key,
                )
                result = await session.execute(stmt)
                return result.scalar_one_or_none()

        return cls._run(_go())

    @classmethod
    def _sql_revoke(
        cls, agency_id: str, mandate_id: str, reason: str, revoked_by: str = ""
    ) -> bool:
        cls._ensure_table()

        async def _go() -> bool:
            from sqlalchemy import func, update

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
                    .values(
                        status="REVOKED",
                        revocation_reason=(reason or "")[:500],
                        mandate_metadata=func.jsonb_set(
                            func.coalesce(PaymentMandateModel.mandate_metadata, "{}"),
                            ["{fnd0221}"],
                            func.jsonb_build_object(
                                "revoked_at", _now().isoformat(),
                                "revoked_by", revoked_by or "",
                            ).op("||")(
                                func.coalesce(
                                    PaymentMandateModel.mandate_metadata["fnd0221"], "{}"
                                )
                            ),
                        ),
                    )
                )
                changed = bool(result.rowcount)
                await session.commit()
                return changed

        return cls._run(_go())

    @classmethod
    def _sql_authorize(
        cls,
        agency_id: str,
        mandate_id: str,
        amount_cents: int,
        scope: Optional[str] = None,
        movement_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        cls._ensure_table()

        async def _go() -> Dict[str, Any]:
            from sqlalchemy import case, func, select, update

            from spine_api.models.payment_mandate import PaymentMandateModel

            # Single-transaction pattern (see _sql_revoke): the pre-checks,
            # the CAS consume, and the commit all share the transaction that
            # carries the RLS context. Scope is immutable per row, so the
            # pre-CAS scope check is race-free; the CAS still guards
            # concurrent over-consumption.
            async with cls._rls_session(agency_id) as session:
                current = await session.execute(
                    select(PaymentMandateModel).where(
                        PaymentMandateModel.mandate_id == mandate_id,
                        PaymentMandateModel.agency_id == agency_id,
                    )
                )
                existing = current.scalar_one_or_none()
                if existing is None:
                    await session.commit()
                    return {"authorized": False, "reason": "Mandate not found in ledger."}

                # FND-0221 movement replay: same movement key → stored outcome,
                # no second consumption.
                if movement_key:
                    movements = (existing.mandate_metadata or {}).get("movements") or {}
                    if isinstance(movements, dict) and movement_key in movements:
                        await session.commit()
                        return {
                            **movements[movement_key],
                            "replayed": True,
                        }

                if existing.status != "ACTIVE":
                    await session.commit()
                    return {
                        "authorized": False,
                        "reason": f"Mandate is in {existing.status} status.",
                    }
                if existing.expires_at and existing.expires_at <= _now():
                    await session.commit()
                    return {"authorized": False, "reason": "Payment mandate has expired."}
                mandate_scope = resolved_scope(cls._sql_row_to_dict(existing))
                if scope is not None and mandate_scope != scope:
                    await session.commit()
                    return {
                        "authorized": False,
                        "reason": (
                            f"Mandate scope '{mandate_scope or 'unknown'}' does not "
                            f"cover the requested movement scope '{scope}'."
                        ),
                        "mandate_id": existing.mandate_id,
                        "mandate_scope": mandate_scope,
                        "requested_scope": scope,
                    }
                remaining = existing.max_authorized_cents - existing.consumed_amount_cents
                if amount_cents > remaining:
                    await session.commit()
                    return {
                        "authorized": False,
                        "reason": (
                            f"Charge of {amount_cents} cents exceeds remaining mandate "
                            f"authorization of {remaining} cents."
                        ),
                    }

                outcome: Dict[str, Any] = {
                    "authorized": True,
                    "mandate_id": mandate_id,
                    "charged_cents": amount_cents,
                    "remaining_authorized_cents": remaining - amount_cents,
                    "consent_text_sha256": existing.consent_text_sha256,
                    "status": "CONSUMED"
                    if existing.consumed_amount_cents + amount_cents
                    >= existing.max_authorized_cents
                    else existing.status,
                    "storage_backend": "sql",
                }
                if movement_key:
                    outcome["movement_idempotency_key"] = movement_key

                values: Dict[str, Any] = {
                    "consumed_amount_cents": PaymentMandateModel.consumed_amount_cents
                    + amount_cents,
                    "status": case(
                        (
                            PaymentMandateModel.consumed_amount_cents + amount_cents
                            >= PaymentMandateModel.max_authorized_cents,
                            "CONSUMED",
                        ),
                        else_=PaymentMandateModel.status,
                    ),
                }
                if movement_key:
                    values["mandate_metadata"] = func.jsonb_set(
                        func.coalesce(PaymentMandateModel.mandate_metadata, "{}"),
                        ["{movements}"],
                        func.coalesce(
                            PaymentMandateModel.mandate_metadata["movements"], "{}"
                        ).op("||")(
                            func.jsonb_build_object(movement_key, outcome)
                        ),
                    )

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
                    .values(**values)
                )
                if result.rowcount == 0:
                    # Lost a concurrent race (e.g. cap exhausted between the
                    # pre-check and the CAS) — re-read for the honest refusal.
                    recheck = await session.execute(
                        select(PaymentMandateModel).where(
                            PaymentMandateModel.mandate_id == mandate_id,
                            PaymentMandateModel.agency_id == agency_id,
                        )
                    )
                    latest = recheck.scalar_one_or_none()
                    await session.commit()
                    if latest is None:
                        return {"authorized": False, "reason": "Mandate not found in ledger."}
                    left = latest.max_authorized_cents - latest.consumed_amount_cents
                    return {
                        "authorized": False,
                        "reason": (
                            f"Charge of {amount_cents} cents exceeds remaining mandate "
                            f"authorization of {left} cents."
                        ),
                    }
                await session.commit()
                return outcome

        return cls._run(_go())
