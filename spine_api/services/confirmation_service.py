"""Confirmation service: CRUD, encryption, state machine, event emission.

Privacy tiers:
- list_confirmations → summary only (no decrypted fields)
- get_confirmation → detail (decrypts for authenticated agent)
- Timeline events contain zero private data.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from spine_api.models.tenant import (
    BookingConfirmation,
    BookingTask,
    CONFIRMATION_TYPES,
    CONFIRMATION_VALID_TRANSITIONS,
    ALLOWED_EVIDENCE_REF_TYPES,
    NOTES_MAX_LENGTH,
)
from spine_api.services.private_fields import encrypt_field, decrypt_field
from spine_api.services import execution_event_service

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class ConfirmationSummary:
    id: str
    trip_id: str
    task_id: Optional[str]
    confirmation_type: str
    confirmation_status: str
    has_supplier: bool
    has_confirmation_number: bool
    external_ref_present: bool
    notes_present: bool
    evidence_ref_count: int
    recorded_at: Optional[datetime]
    verified_at: Optional[datetime]
    voided_at: Optional[datetime]
    created_by: str
    created_at: datetime


@dataclass
class ConfirmationDetail:
    id: str
    trip_id: str
    task_id: Optional[str]
    confirmation_type: str
    confirmation_status: str
    has_supplier: bool
    has_confirmation_number: bool
    external_ref_present: bool
    notes_present: bool
    evidence_refs: Optional[list[dict]]
    evidence_ref_count: int
    supplier_name: Optional[str]
    confirmation_number: Optional[str]
    notes: Optional[str]
    external_ref: Optional[str]
    recorded_by: Optional[str]
    recorded_at: Optional[datetime]
    verified_by: Optional[str]
    verified_at: Optional[datetime]
    voided_by: Optional[str]
    voided_at: Optional[datetime]
    created_by: str
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# F-31 / FND-0118 typed attach failures
# ---------------------------------------------------------------------------

class ConfirmationAttachConflict(ValueError):
    """A deliberate, non-double-attaching rejection of an insurance attach.

    Raised when an active (non-void) insurance confirmation already occupies
    the trip slot (explicit immutable-create contract from the F-31 design:
    after A is replaced/voided, replaying A must not resurrect A, and a second
    active policy must be rejected rather than silently attached), or when the
    same confirmation key is currently in flight / unresolved.
    """

    def __init__(
        self,
        message: str,
        *,
        existing_confirmation_id: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.existing_confirmation_id = existing_confirmation_id


class ConfirmationAttachUnavailable(ValueError):
    """The durable confirmation store rejected the write; no evidence was recorded.

    Adapters must fail closed on this: no successful response without durable
    required evidence (F-31 design, attachment verification item 3).
    """


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

def _validate_evidence_refs(refs: Optional[list[dict]]) -> None:
    if not refs:
        return
    for ref in refs:
        if not isinstance(ref, dict):
            raise ValueError(f"Evidence ref must be a dict, got {type(ref)}")
        ref_type = ref.get("type")
        ref_id = ref.get("id")
        if not ref_type or not ref_id:
            raise ValueError("Evidence ref must have 'type' and 'id'")
        if ref_type not in ALLOWED_EVIDENCE_REF_TYPES:
            raise ValueError(f"Invalid evidence ref type: {ref_type}")


async def _validate_ownership(
    db: AsyncSession,
    trip_id: str,
    agency_id: str,
    task_id: Optional[str] = None,
    evidence_refs: Optional[list[dict]] = None,
) -> None:
    """Validate that task_id and evidence refs belong to the same trip/agency."""
    if task_id:
        result = await db.execute(
            select(BookingTask).where(BookingTask.id == task_id)
        )
        task = result.scalar_one_or_none()
        if not task:
            raise ValueError(f"Task {task_id} not found")
        if task.trip_id != trip_id or task.agency_id != agency_id:
            raise ValueError("Task does not belong to this trip/agency")

    if evidence_refs:
        for ref in evidence_refs:
            ref_type = ref.get("type")
            ref_id = ref.get("id")
            if ref_type == "booking_task":
                result = await db.execute(
                    select(BookingTask).where(BookingTask.id == ref_id)
                )
                task = result.scalar_one_or_none()
                if task and (task.trip_id != trip_id or task.agency_id != agency_id):
                    raise ValueError(
                        f"Evidence ref {ref_type}:{ref_id} does not belong to this trip/agency"
                    )


# ---------------------------------------------------------------------------
# Summary/detail helpers
# ---------------------------------------------------------------------------

def _to_summary(c: BookingConfirmation) -> ConfirmationSummary:
    refs = c.evidence_refs or []
    return ConfirmationSummary(
        id=c.id,
        trip_id=c.trip_id,
        task_id=c.task_id,
        confirmation_type=c.confirmation_type,
        confirmation_status=c.confirmation_status,
        has_supplier=c.has_supplier,
        has_confirmation_number=c.has_confirmation_number,
        external_ref_present=c.external_ref_present,
        notes_present=c.notes_present,
        evidence_ref_count=len(refs),
        recorded_at=c.recorded_at,
        verified_at=c.verified_at,
        voided_at=c.voided_at,
        created_by=c.created_by,
        created_at=c.created_at,
    )


def _to_detail(c: BookingConfirmation) -> ConfirmationDetail:
    refs = c.evidence_refs or []
    return ConfirmationDetail(
        id=c.id,
        trip_id=c.trip_id,
        task_id=c.task_id,
        confirmation_type=c.confirmation_type,
        confirmation_status=c.confirmation_status,
        has_supplier=c.has_supplier,
        has_confirmation_number=c.has_confirmation_number,
        external_ref_present=c.external_ref_present,
        notes_present=c.notes_present,
        evidence_refs=refs,
        evidence_ref_count=len(refs),
        supplier_name=decrypt_field(c.supplier_name_encrypted),
        confirmation_number=decrypt_field(c.confirmation_number_encrypted),
        notes=decrypt_field(c.notes_encrypted),
        external_ref=decrypt_field(c.external_ref_encrypted),
        recorded_by=c.recorded_by,
        recorded_at=c.recorded_at,
        verified_by=c.verified_by,
        verified_at=c.verified_at,
        voided_by=c.voided_by,
        voided_at=c.voided_at,
        created_by=c.created_by,
        created_at=c.created_at,
        updated_at=c.updated_at,
    )


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------

async def list_confirmations(
    db: AsyncSession,
    trip_id: str,
    agency_id: str,
) -> list[ConfirmationSummary]:
    """List confirmations — summary only, no decrypted fields."""
    result = await db.execute(
        select(BookingConfirmation).where(
            BookingConfirmation.trip_id == trip_id,
            BookingConfirmation.agency_id == agency_id,
        ).order_by(BookingConfirmation.created_at)
    )
    rows = list(result.scalars().all())
    return [_to_summary(c) for c in rows]


async def get_confirmation(
    db: AsyncSession,
    confirmation_id: str,
    agency_id: str,
) -> ConfirmationDetail:
    """Get confirmation detail — decrypts private fields."""
    result = await db.execute(
        select(BookingConfirmation).where(
            BookingConfirmation.id == confirmation_id,
            BookingConfirmation.agency_id == agency_id,
        )
    )
    c = result.scalar_one_or_none()
    if not c:
        raise ValueError("Confirmation not found")
    return _to_detail(c)


async def create_confirmation_in_transaction(
    db: AsyncSession,
    *,
    trip_id: str,
    agency_id: str,
    created_by: str,
    data: dict,
) -> BookingConfirmation:
    """Transactional internal: validate, build and stage a confirmation row and
    emit its required creation event — WITHOUT committing.

    F-31 (FND-0118): the canonical service internals participate in one
    caller-owned transaction so evidence and the required execution event can
    be committed coherently (or rolled back together, leaving no partial
    state). The commit-owning public callers (:func:`create_confirmation`)
    remain the stable API.
    """
    c_type = data.get("confirmation_type", "")
    if c_type not in CONFIRMATION_TYPES:
        raise ValueError(f"Invalid confirmation_type: {c_type}")

    task_id = data.get("task_id")
    evidence_refs = data.get("evidence_refs")

    # Validate evidence refs schema
    _validate_evidence_refs(evidence_refs)

    # Validate ownership of task_id and evidence refs
    await _validate_ownership(db, trip_id, agency_id, task_id, evidence_refs)

    # Validate notes length
    notes = data.get("notes")
    if notes and len(notes) > NOTES_MAX_LENGTH:
        raise ValueError(f"Notes exceed max length of {NOTES_MAX_LENGTH}")

    supplier_name = data.get("supplier_name")
    confirmation_number = data.get("confirmation_number")
    external_ref = data.get("external_ref")

    c = BookingConfirmation(
        agency_id=agency_id,
        trip_id=trip_id,
        task_id=task_id,
        confirmation_type=c_type,
        confirmation_status="draft",
        supplier_name_encrypted=encrypt_field(supplier_name),
        confirmation_number_encrypted=encrypt_field(confirmation_number),
        notes_encrypted=encrypt_field(notes),
        external_ref_encrypted=encrypt_field(external_ref),
        has_supplier=bool(supplier_name and supplier_name.strip()),
        has_confirmation_number=bool(confirmation_number and confirmation_number.strip()),
        notes_present=bool(notes and notes.strip()),
        external_ref_present=bool(external_ref and external_ref.strip()),
        evidence_refs=evidence_refs,
        created_by=created_by,
    )
    db.add(c)
    # Flush (not commit): the PK must exist inside the caller's transaction so
    # the required event can reference it, while a later failure still rolls
    # the whole unit back atomically.
    await db.flush()

    # Emit required creation event inside the same caller-owned transaction.
    await execution_event_service.emit_event(
        db,
        agency_id=agency_id,
        trip_id=trip_id,
        subject_type="booking_confirmation",
        subject_id=c.id,
        event_type="confirmation_created",
        event_category="confirmation",
        status_from=None,
        status_to="draft",
        actor_type="agent",
        actor_id=created_by,
        source="agent_action",
        event_metadata={"confirmation_type": c_type},
    )
    return c


async def create_confirmation(
    db: AsyncSession,
    *,
    trip_id: str,
    agency_id: str,
    created_by: str,
    data: dict,
) -> ConfirmationDetail:
    """Create a new confirmation with encrypted private fields.

    F-31 (FND-0118) deliberate migration: the historical split-commit sequence
    (row commit, then event emission, then a second commit) is replaced by one
    atomic commit of the row and its required creation event, via
    :func:`create_confirmation_in_transaction`. The public contract is
    unchanged.
    """
    c = await create_confirmation_in_transaction(
        db,
        trip_id=trip_id,
        agency_id=agency_id,
        created_by=created_by,
        data=data,
    )
    await db.commit()
    await db.refresh(c)
    return _to_detail(c)


async def update_confirmation(
    db: AsyncSession,
    *,
    confirmation_id: str,
    agency_id: str,
    data: dict,
    updated_by: str,
) -> ConfirmationDetail:
    """Update a confirmation. Only draft and recorded are editable."""
    result = await db.execute(
        select(BookingConfirmation).where(
            BookingConfirmation.id == confirmation_id,
            BookingConfirmation.agency_id == agency_id,
        )
    )
    c = result.scalar_one_or_none()
    if not c:
        raise ValueError("Confirmation not found")

    if c.confirmation_status in ("verified", "voided"):
        raise ValueError(f"Cannot edit {c.confirmation_status} confirmation")

    old_status = c.confirmation_status

    # Validate notes length if provided
    notes = data.get("notes")
    if notes is not None and len(notes) > NOTES_MAX_LENGTH:
        raise ValueError(f"Notes exceed max length of {NOTES_MAX_LENGTH}")

    # Validate evidence refs if provided
    evidence_refs = data.get("evidence_refs")
    if evidence_refs is not None:
        _validate_evidence_refs(evidence_refs)
        await _validate_ownership(db, c.trip_id, agency_id, c.task_id, evidence_refs)

    # Update fields
    if "supplier_name" in data:
        val = data["supplier_name"]
        c.supplier_name_encrypted = encrypt_field(val)
        c.has_supplier = bool(val and val.strip())

    if "confirmation_number" in data:
        val = data["confirmation_number"]
        c.confirmation_number_encrypted = encrypt_field(val)
        c.has_confirmation_number = bool(val and val.strip())

    if "notes" in data:
        val = data["notes"]
        c.notes_encrypted = encrypt_field(val)
        c.notes_present = bool(val and val.strip())

    if "external_ref" in data:
        val = data["external_ref"]
        c.external_ref_encrypted = encrypt_field(val)
        c.external_ref_present = bool(val and val.strip())

    if "evidence_refs" in data:
        c.evidence_refs = evidence_refs

    if "task_id" in data:
        task_id = data["task_id"]
        await _validate_ownership(db, c.trip_id, agency_id, task_id)
        c.task_id = task_id

    if "confirmation_type" in data:
        c_type = data["confirmation_type"]
        if c_type not in CONFIRMATION_TYPES:
            raise ValueError(f"Invalid confirmation_type: {c_type}")
        c.confirmation_type = c_type

    await db.commit()
    await db.refresh(c)

    # Emit update event if recorded (draft edits are silent)
    if old_status == "recorded":
        await execution_event_service.emit_event(
            db,
            agency_id=agency_id,
            trip_id=c.trip_id,
            subject_type="booking_confirmation",
            subject_id=c.id,
            event_type="confirmation_updated",
            event_category="confirmation",
            status_from=old_status,
            status_to="recorded",
            actor_type="agent",
            actor_id=updated_by,
            source="agent_action",
            event_metadata={"confirmation_type": c.confirmation_type},
        )
        await db.commit()

    return _to_detail(c)


# ---------------------------------------------------------------------------
# State machine transitions
# ---------------------------------------------------------------------------

async def record_confirmation_in_transaction(
    db: AsyncSession,
    confirmation: BookingConfirmation,
    *,
    recorded_by: str,
) -> BookingConfirmation:
    """Transactional internal: draft → recorded without committing.

    State-machine validation and the required event happen inside the
    caller-owned transaction (F-31 / FND-0118 migration).
    """
    old_status = confirmation.confirmation_status
    allowed = CONFIRMATION_VALID_TRANSITIONS.get(old_status, set())
    if "recorded" not in allowed:
        raise ValueError(f"Cannot record from {old_status}")

    confirmation.confirmation_status = "recorded"
    confirmation.recorded_by = recorded_by
    confirmation.recorded_at = datetime.now(timezone.utc)

    await execution_event_service.emit_event(
        db,
        agency_id=confirmation.agency_id,
        trip_id=confirmation.trip_id,
        subject_type="booking_confirmation",
        subject_id=confirmation.id,
        event_type="confirmation_recorded",
        event_category="confirmation",
        status_from=old_status,
        status_to="recorded",
        actor_type="agent",
        actor_id=recorded_by,
        source="agent_action",
        event_metadata={"confirmation_type": confirmation.confirmation_type},
    )
    return confirmation


async def record_confirmation(
    db: AsyncSession,
    *,
    confirmation_id: str,
    agency_id: str,
    recorded_by: str,
) -> ConfirmationSummary:
    """draft → recorded."""
    result = await db.execute(
        select(BookingConfirmation).where(
            BookingConfirmation.id == confirmation_id,
            BookingConfirmation.agency_id == agency_id,
        )
    )
    c = result.scalar_one_or_none()
    if not c:
        raise ValueError("Confirmation not found")

    await record_confirmation_in_transaction(db, c, recorded_by=recorded_by)
    await db.commit()
    await db.refresh(c)

    return _to_summary(c)


async def try_record_fulfillment_confirmation(
    *,
    agency_id: str,
    trip_id: str,
    created_by: str,
    pnr_locator: str,
    e_ticket_number: str,
    vcc_card_id: str,
    total_usd: float,
    reality_tier: str,
    provider_connected: bool,
) -> Dict[str, Any]:
    """AT-04: durably record a fulfillment as a ``BookingConfirmation`` row
    (draft → recorded) so the SQL confirmation machine — not the trip JSON
    blob — is the durable truth the void/verify paths operate on.

    Honest degradation (Part-H, 2026-09-07): without a configured database
    session maker, or on any write failure, this returns
    ``{"recorded": False, "reason": …}`` instead of raising into the booking
    path or pretending the row exists. The caller surfaces that outcome on
    the fulfillment result and audit record.
    """
    try:
        from spine_api.core.rls import rls_session
    except Exception as exc:  # pragma: no cover - depends on deploy env
        return {"recorded": False, "reason": f"no_database_session_maker: {exc}"}

    notes = (
        f"reality_tier={reality_tier}; provider_connected={provider_connected}; "
        f"vcc_card_id={vcc_card_id}; total_usd={total_usd}; "
        "recorded by booking fulfillment engine (AT-04)"
    )
    try:
        # rls_session was already probe-imported above; reuse that binding.

        # Part-L A3 (2026-09-08): fulfillment runs OUTSIDE request context
        # (background/engine path), so the bare session maker has no RLS
        # agency set and booking_confirmations INSERTs fail row-level
        # security. The canonical rls_session binds the agency explicitly —
        # same isolation, background-safe.
        async with rls_session(agency_id) as db:
            # FND-0174: convergent replay repair. If a flight confirmation
            # row for this trip already exists (e.g. the blob-side
            # ``sql_confirmation`` marker was lost in the same crash that
            # lost the first record attempt, or a repair runs twice), re-link
            # the EXISTING durable row instead of colliding with
            # ``uq_bc_trip_type_active`` — repair must converge on the
            # durable truth, never double-record it.
            existing = (
                await db.execute(
                    select(BookingConfirmation).where(
                        BookingConfirmation.agency_id == agency_id,
                        BookingConfirmation.trip_id == trip_id,
                        BookingConfirmation.confirmation_type == "flight",
                        BookingConfirmation.confirmation_status != "voided",
                    )
                )
            ).scalars().first()
            if existing is not None:
                return {
                    "recorded": True,
                    "confirmation_id": existing.id,
                    "status": existing.confirmation_status,
                    "relinked": True,
                }
            detail = await create_confirmation(
                db,
                trip_id=trip_id,
                agency_id=agency_id,
                created_by=created_by,
                data={
                    "confirmation_type": "flight",
                    "supplier_name": "Amadeus NDC (simulated sandbox)",
                    "confirmation_number": pnr_locator,
                    "external_ref": e_ticket_number,
                    "notes": notes,
                },
            )
            summary = await record_confirmation(
                db,
                confirmation_id=detail.id,
                agency_id=agency_id,
                recorded_by=created_by,
            )
            return {
                "recorded": True,
                "confirmation_id": detail.id,
                "status": summary.confirmation_status,
            }
    except Exception as exc:
        return {"recorded": False, "reason": f"{type(exc).__name__}: {exc}"}


# ---------------------------------------------------------------------------
# F-31 / FND-0118: canonical insurance evidence attachment
# ---------------------------------------------------------------------------

INSURANCE_ATTACH_ACTION = "insurance_policy_attach"


def _insurance_attach_idempotency_payload(
    *,
    agency_id: str,
    insurance_provider: str,
    policy_number: str,
    selected_plan_id: str,
    premium_paid_usd: float,
) -> dict:
    """Canonical attach payload: agency is part of the key so identical trip
    ids from different tenants can never collide on one replay receipt."""
    return {
        "agency_id": agency_id,
        "insurance_provider": insurance_provider,
        "policy_number": policy_number,
        "selected_plan_id": selected_plan_id,
        "premium_paid_usd": premium_paid_usd,
    }


async def _find_active_insurance_confirmation(db: AsyncSession, agency_id: str, trip_id: str):
    result = await db.execute(
        select(BookingConfirmation).where(
            BookingConfirmation.agency_id == agency_id,
            BookingConfirmation.trip_id == trip_id,
            BookingConfirmation.confirmation_type == "insurance",
            BookingConfirmation.confirmation_status != "voided",
        )
    )
    return result.scalars().first()


async def attach_insurance_confirmation(
    *,
    agency_id: str,
    trip_id: str,
    actor_id: str,
    insurance_provider: str,
    policy_number: str,
    selected_plan_id: str,
    premium_paid_usd: float,
    provider_source: str = "agent_recorded",
    reality_tier: str = "deterministic_preview",
) -> Dict[str, Any]:
    """Durably record operator-asserted insurance evidence as the canonical
    ``insurance`` ``BookingConfirmation`` row (F-31 design,
    ``Docs/research/INSURANCE_TIMING_AND_ELIGIBILITY_CONTRACT_2026-09-05.md``).

    Contract implemented here:

    - **Canonical record, not a second policy store.** The insurer, policy
      number, plan reference and provenance markers are encrypted private
      fields on the existing row type; adapters may keep a legacy trip-blob
      projection but this row is the authority.
    - **Atomic save.** The evidence row and its required creation/recording
      execution events commit in ONE caller-owned transaction via
      :func:`create_confirmation_in_transaction` /
      :func:`record_confirmation_in_transaction`. Any failure rolls back to no
      partial state.
    - **Replay idempotency.** A deterministic key (agency + trip + payload)
      through the canonical :class:`IdempotencyRegistry` returns the recorded
      outcome without a second attach. The durable backstop is the
      ``uq_bc_trip_type_active`` immutable-create contract: while an active
      insurance confirmation exists, a different payload raises
      :class:`ConfirmationAttachConflict` (carrying the existing confirmation
      id) instead of double-attaching, and replaying a voided/replaced record
      never resurrects it.
    - **Actor semantics.** ``actor_id`` MUST be the authenticated principal;
      the agency stays a separate tenant dimension (row column + key payload),
      never the audit actor.
    - **Money is evidence only.** ``premium_paid_usd`` is recorded as
      operator-asserted evidence; no charge is initiated and no payment
      authorization is evaluated here — that remains the payment-mandate
      seam's responsibility (compose, do not bypass).

    Returns a JSON-serializable outcome dict with ``replayed`` marking whether
    an existing recorded outcome was returned instead of a new attach.
    """
    from sqlalchemy.exc import IntegrityError

    from src.agents.idempotency import IdempotencyRegistry, IdempotencyStatus

    payload = _insurance_attach_idempotency_payload(
        agency_id=agency_id,
        insurance_provider=insurance_provider,
        policy_number=policy_number,
        selected_plan_id=selected_plan_id,
        premium_paid_usd=premium_paid_usd,
    )
    key = IdempotencyRegistry.generate_key(trip_id, INSURANCE_ATTACH_ACTION, payload)
    registry = IdempotencyRegistry.get_instance()
    acquired, record = registry.try_acquire(key, trip_id, INSURANCE_ATTACH_ACTION, payload)
    if not acquired:
        if (
            record is not None
            and record.status is IdempotencyStatus.COMPLETED
            and record.response_payload
        ):
            # Same confirmation key → same outcome, no double-attach.
            return {**record.response_payload, "replayed": True}
        # PENDING = a concurrent attach is in flight; UNKNOWN = the previous
        # outcome is unresolved and must be verified, never silently retried
        # (TS-08 semantics). Neither may be re-executed here.
        raise ConfirmationAttachConflict(
            "Insurance attach for this confirmation key is "
            f"{record.status.value if record else 'UNKNOWN'}; resolve or retry after it settles"
        )
    fencing_token = record.fencing_token if record is not None else None

    try:
        from spine_api.core.rls import rls_session

        async with rls_session(agency_id) as db:
            existing = await _find_active_insurance_confirmation(db, agency_id, trip_id)
            if existing is not None:
                raise ConfirmationAttachConflict(
                    "An active insurance confirmation already exists for this trip",
                    existing_confirmation_id=existing.id,
                )

            # Encrypted private evidence; provenance markers travel in the
            # encrypted notes so no general log can reconstruct them.
            notes = (
                f"provider_source={provider_source}; premium_paid_usd={premium_paid_usd}; "
                f"reality_tier={reality_tier}; carrier_confirmed=false; "
                f"plan={selected_plan_id}; recorded via insurance attach-policy "
                "evidence migration (F-31/FND-0118)"
            )
            c = await create_confirmation_in_transaction(
                db,
                trip_id=trip_id,
                agency_id=agency_id,
                created_by=actor_id,
                data={
                    "confirmation_type": "insurance",
                    "supplier_name": insurance_provider,
                    "confirmation_number": policy_number,
                    "external_ref": selected_plan_id,
                    "notes": notes,
                },
            )
            await record_confirmation_in_transaction(db, c, recorded_by=actor_id)
            await db.commit()
            await db.refresh(c)
    except ConfirmationAttachConflict:
        registry.mark_failed(
            key,
            "active insurance confirmation exists or attach in flight",
            fencing_token=fencing_token,
        )
        raise
    except IntegrityError as exc:
        # Concurrent attach raced past the precheck: the durable partial
        # unique index uq_bc_trip_type_active decided the winner. Surface the
        # winning confirmation id instead of double-attaching.
        registry.mark_failed(
            key, f"{type(exc).__name__}: {exc}", fencing_token=fencing_token
        )
        existing_id = None
        try:
            from spine_api.core.rls import rls_session as _rls_session

            async with _rls_session(agency_id) as db:
                winner = await _find_active_insurance_confirmation(db, agency_id, trip_id)
                existing_id = winner.id if winner is not None else None
        except Exception:  # pragma: no cover - diagnostic only
            pass
        raise ConfirmationAttachConflict(
            "Concurrent insurance attach detected; one active confirmation exists",
            existing_confirmation_id=existing_id,
        ) from exc
    except Exception as exc:
        registry.mark_failed(key, f"{type(exc).__name__}: {exc}", fencing_token=fencing_token)
        raise ConfirmationAttachUnavailable(
            f"Insurance evidence could not be durably recorded: {type(exc).__name__}: {exc}"
        ) from exc

    outcome = {
        "replayed": False,
        "confirmation_id": c.id,
        "confirmation_status": c.confirmation_status,
        "recorded_at": c.recorded_at.isoformat() if c.recorded_at else None,
    }
    # Best-effort fence: losing the race here does not change the durable
    # outcome; a reclaiming caller would only re-run the (idempotent) precheck.
    registry.mark_completed(key, outcome, fencing_token=fencing_token)
    return outcome


async def verify_confirmation_in_transaction(
    db: AsyncSession,
    confirmation: BookingConfirmation,
    *,
    verified_by: str,
) -> BookingConfirmation:
    """Transactional internal: recorded → verified without committing.

    State-machine validation and the required event happen inside the
    caller-owned transaction (F-31 / FND-0118 migration parity): the row and
    its required execution event commit atomically — a failure anywhere
    leaves no durable status without its event, and no event without its
    status.
    """
    old_status = confirmation.confirmation_status
    allowed = CONFIRMATION_VALID_TRANSITIONS.get(old_status, set())
    if "verified" not in allowed:
        raise ValueError(f"Cannot verify from {old_status}")

    confirmation.confirmation_status = "verified"
    confirmation.verified_by = verified_by
    confirmation.verified_at = datetime.now(timezone.utc)

    await execution_event_service.emit_event(
        db,
        agency_id=confirmation.agency_id,
        trip_id=confirmation.trip_id,
        subject_type="booking_confirmation",
        subject_id=confirmation.id,
        event_type="confirmation_verified",
        event_category="confirmation",
        status_from=old_status,
        status_to="verified",
        actor_type="agent",
        actor_id=verified_by,
        source="agent_action",
        event_metadata={"confirmation_type": confirmation.confirmation_type},
    )
    return confirmation


async def verify_confirmation(
    db: AsyncSession,
    *,
    confirmation_id: str,
    agency_id: str,
    verified_by: str,
) -> ConfirmationSummary:
    """recorded → verified."""
    result = await db.execute(
        select(BookingConfirmation).where(
            BookingConfirmation.id == confirmation_id,
            BookingConfirmation.agency_id == agency_id,
        )
    )
    c = result.scalar_one_or_none()
    if not c:
        raise ValueError("Confirmation not found")

    await verify_confirmation_in_transaction(db, c, verified_by=verified_by)
    await db.commit()
    await db.refresh(c)

    return _to_summary(c)


async def void_confirmation_in_transaction(
    db: AsyncSession,
    confirmation: BookingConfirmation,
    *,
    voided_by: str,
) -> BookingConfirmation:
    """Transactional internal: any non-voided → voided without committing.

    State-machine validation and the required event happen inside the
    caller-owned transaction (F-31 / FND-0118 migration parity).
    """
    old_status = confirmation.confirmation_status
    allowed = CONFIRMATION_VALID_TRANSITIONS.get(old_status, set())
    if "voided" not in allowed:
        raise ValueError(f"Cannot void from {old_status}")

    confirmation.confirmation_status = "voided"
    confirmation.voided_by = voided_by
    confirmation.voided_at = datetime.now(timezone.utc)

    await execution_event_service.emit_event(
        db,
        agency_id=confirmation.agency_id,
        trip_id=confirmation.trip_id,
        subject_type="booking_confirmation",
        subject_id=confirmation.id,
        event_type="confirmation_voided",
        event_category="confirmation",
        status_from=old_status,
        status_to="voided",
        actor_type="agent",
        actor_id=voided_by,
        source="agent_action",
        event_metadata={"confirmation_type": confirmation.confirmation_type},
    )
    return confirmation


async def void_confirmation(
    db: AsyncSession,
    *,
    confirmation_id: str,
    agency_id: str,
    voided_by: str,
) -> ConfirmationSummary:
    """any non-voided → voided."""
    result = await db.execute(
        select(BookingConfirmation).where(
            BookingConfirmation.id == confirmation_id,
            BookingConfirmation.agency_id == agency_id,
        )
    )
    c = result.scalar_one_or_none()
    if not c:
        raise ValueError("Confirmation not found")

    await void_confirmation_in_transaction(db, c, voided_by=voided_by)
    await db.commit()
    await db.refresh(c)

    return _to_summary(c)
