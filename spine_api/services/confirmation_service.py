"""Confirmation service: CRUD, encryption, state machine, event emission.

Privacy tiers:
- list_confirmations → summary only (no decrypted fields)
- get_confirmation → detail (decrypts for authenticated agent)
- Timeline events contain zero private data.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from spine_api.models.tenant import (
    BookingConfirmation,
    BookingTask,
    CONFIRMATION_TYPES,
    CONFIRMATION_STATUSES,
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


async def create_confirmation(
    db: AsyncSession,
    *,
    trip_id: str,
    agency_id: str,
    created_by: str,
    data: dict,
) -> ConfirmationDetail:
    """Create a new confirmation with encrypted private fields."""
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
    await db.commit()
    await db.refresh(c)

    # Emit event
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
    await db.commit()

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
            metadata={"confirmation_type": c.confirmation_type},
        )
        await db.commit()

    return _to_detail(c)


# ---------------------------------------------------------------------------
# State machine transitions
# ---------------------------------------------------------------------------

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

    old_status = c.confirmation_status
    allowed = CONFIRMATION_VALID_TRANSITIONS.get(old_status, set())
    if "recorded" not in allowed:
        raise ValueError(f"Cannot record from {old_status}")

    c.confirmation_status = "recorded"
    c.recorded_by = recorded_by
    c.recorded_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(c)

    await execution_event_service.emit_event(
        db,
        agency_id=agency_id,
        trip_id=c.trip_id,
        subject_type="booking_confirmation",
        subject_id=c.id,
        event_type="confirmation_recorded",
        event_category="confirmation",
        status_from=old_status,
        status_to="recorded",
        actor_type="agent",
        actor_id=recorded_by,
        source="agent_action",
        metadata={"confirmation_type": c.confirmation_type},
    )
    await db.commit()

    return _to_summary(c)


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

    old_status = c.confirmation_status
    allowed = CONFIRMATION_VALID_TRANSITIONS.get(old_status, set())
    if "verified" not in allowed:
        raise ValueError(f"Cannot verify from {old_status}")

    c.confirmation_status = "verified"
    c.verified_by = verified_by
    c.verified_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(c)

    await execution_event_service.emit_event(
        db,
        agency_id=agency_id,
        trip_id=c.trip_id,
        subject_type="booking_confirmation",
        subject_id=c.id,
        event_type="confirmation_verified",
        event_category="confirmation",
        status_from=old_status,
        status_to="verified",
        actor_type="agent",
        actor_id=verified_by,
        source="agent_action",
        metadata={"confirmation_type": c.confirmation_type},
    )
    await db.commit()

    return _to_summary(c)


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

    old_status = c.confirmation_status
    allowed = CONFIRMATION_VALID_TRANSITIONS.get(old_status, set())
    if "voided" not in allowed:
        raise ValueError(f"Cannot void from {old_status}")

    c.confirmation_status = "voided"
    c.voided_by = voided_by
    c.voided_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(c)

    await execution_event_service.emit_event(
        db,
        agency_id=agency_id,
        trip_id=c.trip_id,
        subject_type="booking_confirmation",
        subject_id=c.id,
        event_type="confirmation_voided",
        event_category="confirmation",
        status_from=old_status,
        status_to="voided",
        actor_type="agent",
        actor_id=voided_by,
        source="agent_action",
        metadata={"confirmation_type": c.confirmation_type},
    )
    await db.commit()

    return _to_summary(c)
