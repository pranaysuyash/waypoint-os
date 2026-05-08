"""Booking task service: generation, reconciliation, CRUD."""

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from spine_api.models.tenant import (
    BookingTask,
    TASK_STATUSES,
    TASK_TYPES,
    TASK_SOURCES,
    TASK_PRIORITIES,
    BLOCKER_CODES,
    VALID_TRANSITIONS,
    TASK_TITLE_TEMPLATES,
)

logger = logging.getLogger(__name__)

TERMINAL_STATUSES = frozenset({"completed", "cancelled"})
SYSTEM_SOURCES = frozenset({"system_suggested", "readiness_generated", "document_generated", "extraction_generated"})


# ---------------------------------------------------------------------------
# Data classes for results
# ---------------------------------------------------------------------------

@dataclass
class ReconciliationResult:
    task_id: str
    old_status: str
    new_status: str


@dataclass
class GenerateResult:
    created: list[BookingTask]
    skipped: list[str]
    reconciled: list[ReconciliationResult]


@dataclass
class TaskListResult:
    trip_id: str
    tasks: list[BookingTask]
    summary: dict[str, int]


# ---------------------------------------------------------------------------
# Generation hash
# ---------------------------------------------------------------------------

def _generation_hash(
    agency_id: str,
    trip_id: str,
    task_type: str,
    source: str,
    traveler_id: Optional[str],
    blocker_refs: Optional[dict],
) -> str:
    parts = [agency_id, trip_id, task_type, source]
    if traveler_id:
        parts.append(f"tv:{traveler_id}")
    if blocker_refs:
        for k in sorted(blocker_refs.keys()):
            parts.append(f"{k}:{blocker_refs[k]}")
    return hashlib.sha256(":".join(parts).encode()).hexdigest()[:32]


# ---------------------------------------------------------------------------
# Title generation (template-only, no PII)
# ---------------------------------------------------------------------------

def _make_title(task_type: str, traveler_ordinal: Optional[int] = None) -> str:
    template = TASK_TITLE_TEMPLATES.get(task_type)
    if template and traveler_ordinal is not None:
        return template.format(ordinal=traveler_ordinal)
    if template:
        return template
    return task_type.replace("_", " ").title()


# ---------------------------------------------------------------------------
# Transition validation
# ---------------------------------------------------------------------------

def _validate_transition(current: str, target: str) -> None:
    if current == target:
        return
    allowed = VALID_TRANSITIONS.get(current, set())
    if target not in allowed:
        raise ValueError(f"Invalid transition: {current} -> {target}")


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------

async def list_tasks(db: AsyncSession, trip_id: str, agency_id: str) -> TaskListResult:
    result = await db.execute(
        select(BookingTask)
        .where(BookingTask.trip_id == trip_id, BookingTask.agency_id == agency_id)
        .order_by(BookingTask.created_at)
    )
    tasks = list(result.scalars().all())
    summary = {s: 0 for s in TASK_STATUSES}
    summary["total"] = len(tasks)
    for t in tasks:
        summary[t.status] = summary.get(t.status, 0) + 1
    return TaskListResult(trip_id=trip_id, tasks=tasks, summary=summary)


async def create_task(
    db: AsyncSession,
    trip_id: str,
    agency_id: str,
    created_by: str,
    data: dict,
) -> BookingTask:
    task_type = data.get("task_type", "custom")
    if task_type not in TASK_TYPES:
        raise ValueError(f"Invalid task_type: {task_type}")
    title = data.get("title", "").strip()
    if not title:
        raise ValueError("title is required")
    priority = data.get("priority", "medium")
    if priority not in TASK_PRIORITIES:
        raise ValueError(f"Invalid priority: {priority}")

    task = BookingTask(
        trip_id=trip_id,
        agency_id=agency_id,
        task_type=task_type,
        title=title,
        description=data.get("description"),
        status="not_started",
        priority=priority,
        owner_id=data.get("owner_id"),
        due_at=data.get("due_at"),
        source="agent_created",
        created_by=created_by,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


async def update_task(
    db: AsyncSession,
    task_id: str,
    agency_id: str,
    data: dict,
) -> BookingTask:
    result = await db.execute(
        select(BookingTask).where(
            BookingTask.id == task_id, BookingTask.agency_id == agency_id
        )
    )
    task = result.scalar_one_or_none()
    if task is None:
        raise ValueError("Task not found")

    if "status" in data:
        new_status = data["status"]
        if new_status not in TASK_STATUSES:
            raise ValueError(f"Invalid status: {new_status}")
        _validate_transition(task.status, new_status)
        task.status = new_status

    if "priority" in data:
        if data["priority"] not in TASK_PRIORITIES:
            raise ValueError(f"Invalid priority: {data['priority']}")
        task.priority = data["priority"]

    if "owner_id" in data:
        task.owner_id = data["owner_id"]

    if "due_at" in data:
        task.due_at = data["due_at"]

    if "title" in data:
        task.title = data["title"]

    await db.commit()
    await db.refresh(task)
    return task


async def complete_task(
    db: AsyncSession,
    task_id: str,
    agency_id: str,
    completed_by: str,
) -> BookingTask:
    result = await db.execute(
        select(BookingTask).where(
            BookingTask.id == task_id, BookingTask.agency_id == agency_id
        )
    )
    task = result.scalar_one_or_none()
    if task is None:
        raise ValueError("Task not found")

    if task.status == "blocked":
        raise ValueError("Cannot complete a blocked task. Reconcile or unblock first.")

    _validate_transition(task.status, "completed")
    task.status = "completed"
    task.completed_by = completed_by
    task.completed_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(task)
    return task


async def cancel_task(
    db: AsyncSession,
    task_id: str,
    agency_id: str,
) -> BookingTask:
    result = await db.execute(
        select(BookingTask).where(
            BookingTask.id == task_id, BookingTask.agency_id == agency_id
        )
    )
    task = result.scalar_one_or_none()
    if task is None:
        raise ValueError("Task not found")

    _validate_transition(task.status, "cancelled")
    task.status = "cancelled"
    task.cancelled_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(task)
    return task


# ---------------------------------------------------------------------------
# Generation + Reconciliation
# ---------------------------------------------------------------------------

async def generate_tasks(
    db: AsyncSession,
    trip_id: str,
    agency_id: str,
    generated_by: str,
    force: bool = False,
) -> GenerateResult:
    """Two-phase: create missing tasks + reconcile active system tasks."""
    trip_state = await _fetch_trip_state(db, trip_id, agency_id)
    candidates = _compute_task_candidates(trip_id, agency_id, trip_state)
    created, skipped = await _create_missing_tasks(db, candidates, force)
    reconciled = await _reconcile_active_tasks(db, trip_id, agency_id, trip_state)
    return GenerateResult(created=created, skipped=skipped, reconciled=reconciled)


async def _fetch_trip_state(db: AsyncSession, trip_id: str, agency_id: str) -> dict:
    """Fetch booking_data, documents, extractions for task generation."""
    from spine_api.persistence import TripStore
    import asyncio

    trip = await asyncio.to_thread(TripStore.get_trip, trip_id)
    if not trip:
        return {}

    booking_data = trip.get("booking_data") or {}
    validation = trip.get("validation") or {}
    readiness = validation.get("readiness") or {}

    # Fetch documents
    from spine_api.models.tenant import BookingDocument, DocumentExtraction
    docs_result = await db.execute(
        select(BookingDocument).where(BookingDocument.trip_id == trip_id)
    )
    documents = list(docs_result.scalars().all())

    # Fetch extractions
    doc_ids = [d.id for d in documents]
    extractions = []
    if doc_ids:
        ext_result = await db.execute(
            select(DocumentExtraction).where(
                DocumentExtraction.document_id.in_(doc_ids),
                DocumentExtraction.agency_id == agency_id,
            )
        )
        extractions = list(ext_result.scalars().all())

    return {
        "booking_data": booking_data,
        "readiness": readiness,
        "documents": documents,
        "extractions": extractions,
    }


def _compute_task_candidates(trip_id: str, agency_id: str, state: dict) -> list[dict]:
    """Compute candidate tasks from current trip state."""
    candidates = []
    booking_data = state.get("booking_data") or {}
    travelers = booking_data.get("travelers", [])
    documents = state.get("documents") or []
    extractions = state.get("extractions") or []
    base = {"trip_id": trip_id, "agency_id": agency_id}

    # Index documents by type + status
    accepted_docs = {}
    for d in documents:
        if d.status == "accepted":
            accepted_docs.setdefault(d.document_type, []).append(d)

    # Index extractions by document_id
    ext_by_doc = {}
    for e in extractions:
        ext_by_doc[e.document_id] = e

    for i, traveler in enumerate(travelers):
        ordinal = i + 1
        tid = traveler.get("traveler_id", f"tv-{ordinal}")

        # verify_traveler_details
        missing_fields = []
        if not str(traveler.get("full_name", "")).strip():
            missing_fields.append("full_name")
        if not str(traveler.get("date_of_birth", "")).strip():
            missing_fields.append("date_of_birth")
        if missing_fields:
            candidates.append({**base,
                "task_type": "verify_traveler_details",
                "traveler_id": tid,
                "traveler_ordinal": ordinal,
                "blocker_code": "missing_booking_data",
                "blocker_refs": {"traveler_id": tid, "fields": ",".join(sorted(missing_fields))},
            })
        else:
            candidates.append({**base,
                "task_type": "verify_traveler_details",
                "traveler_id": tid,
                "traveler_ordinal": ordinal,
                "blocker_code": None,
                "blocker_refs": None,
            })

        # verify_passport
        passport_missing = not str(traveler.get("passport_number", "")).strip() or \
                          not str(traveler.get("passport_expiry", "")).strip()
        passport_docs = accepted_docs.get("passport", [])
        passport_accepted = any(
            d.traveler_id == tid or d.traveler_id is None
            for d in passport_docs
        )
        passport_ext_reviewed = False
        for d in passport_docs:
            if d.traveler_id == tid or d.traveler_id is None:
                ext = ext_by_doc.get(d.id)
                if ext and ext.status in ("applied", "pending_review"):
                    passport_ext_reviewed = True

        if passport_missing:
            bc = "missing_passport_field"
        elif not passport_accepted:
            bc = "missing_document"
        elif not passport_ext_reviewed:
            bc = "extraction_not_reviewed"
        else:
            bc = None

        br = None
        if bc:
            br = {"traveler_id": tid, "document_type": "passport"}

        candidates.append({**base,
            "task_type": "verify_passport",
            "traveler_id": tid,
            "traveler_ordinal": ordinal,
            "blocker_code": bc,
            "blocker_refs": br,
        })

        # verify_insurance
        insurance_docs = accepted_docs.get("insurance", [])
        insurance_accepted = any(
            d.traveler_id == tid or d.traveler_id is None
            for d in insurance_docs
        )
        if not insurance_accepted:
            candidates.append({**base,
                "task_type": "verify_insurance",
                "traveler_id": tid,
                "traveler_ordinal": ordinal,
                "blocker_code": "missing_document",
                "blocker_refs": {"traveler_id": tid, "document_type": "insurance"},
            })
        else:
            candidates.append({**base,
                "task_type": "verify_insurance",
                "traveler_id": tid,
                "traveler_ordinal": ordinal,
                "blocker_code": None,
                "blocker_refs": None,
            })

    # Booking-level tasks (only if there is booking_data)
    if travelers:
        candidates.append({**base,
            "task_type": "confirm_flights",
            "traveler_id": None,
            "traveler_ordinal": None,
            "blocker_code": None,
            "blocker_refs": None,
        })
        candidates.append({**base,
            "task_type": "confirm_hotels",
            "traveler_id": None,
            "traveler_ordinal": None,
            "blocker_code": None,
            "blocker_refs": None,
        })
        candidates.append({**base,
            "task_type": "collect_payment_proof",
            "traveler_id": None,
            "traveler_ordinal": None,
            "blocker_code": None,
            "blocker_refs": None,
        })
        candidates.append({**base,
            "task_type": "send_final_confirmation",
            "traveler_id": None,
            "traveler_ordinal": None,
            "blocker_code": None,
            "blocker_refs": None,
        })

    return candidates


async def _create_missing_tasks(
    db: AsyncSession,
    candidates: list[dict],
    force: bool,
) -> tuple[list[BookingTask], list[str]]:
    """Create tasks that don't already exist (idempotent)."""
    created = []
    skipped = []

    for c in candidates:
        ghash = _generation_hash(
            c.get("agency_id", ""),
            c.get("trip_id", ""),
            c["task_type"],
            "readiness_generated",
            c.get("traveler_id"),
            c.get("blocker_refs"),
        )

        # Check for existing active task with same hash
        existing = await db.execute(
            select(BookingTask).where(BookingTask.generation_hash == ghash)
        )
        existing_task = existing.scalar_one_or_none()

        if existing_task:
            if existing_task.status not in TERMINAL_STATUSES:
                skipped.append(existing_task.id)
                continue
            elif existing_task.status == "completed":
                # Never reopen completed tasks
                skipped.append(existing_task.id)
                continue
            elif existing_task.status == "cancelled" and not force:
                skipped.append(existing_task.id)
                continue

        blocker_code = c.get("blocker_code")
        status = "blocked" if blocker_code else "not_started"

        task = BookingTask(
            trip_id=c.get("trip_id", ""),
            agency_id=c.get("agency_id", ""),
            task_type=c["task_type"],
            title=_make_title(c["task_type"], c.get("traveler_ordinal")),
            description=None,
            status=status,
            priority="high" if blocker_code else "medium",
            blocker_code=blocker_code,
            blocker_refs=c.get("blocker_refs"),
            source="readiness_generated",
            generation_hash=ghash,
            created_by="system",
        )
        db.add(task)
        created.append(task)

    if created:
        await db.commit()
        for t in created:
            await db.refresh(t)

    return created, skipped


async def _reconcile_active_tasks(
    db: AsyncSession,
    trip_id: str,
    agency_id: str,
    trip_state: dict,
) -> list[ReconciliationResult]:
    """Recompute blocker state for active system-generated tasks."""
    result = await db.execute(
        select(BookingTask).where(
            BookingTask.trip_id == trip_id,
            BookingTask.agency_id == agency_id,
            BookingTask.source.in_(SYSTEM_SOURCES),
            ~BookingTask.status.in_(TERMINAL_STATUSES),
        )
    )
    active_tasks = list(result.scalars().all())

    # Rebuild candidates map: task_type + traveler_id -> candidate
    candidates = _compute_task_candidates(trip_id, agency_id, trip_state)
    candidate_map = {}
    for c in candidates:
        key = (c["task_type"], c.get("traveler_id"))
        candidate_map[key] = c

    reconciled = []
    for task in active_tasks:
        # Only reconcile blocked/ready/not_started
        if task.status not in ("blocked", "ready", "not_started"):
            continue

        key = (task.task_type, task.blocker_refs.get("traveler_id") if task.blocker_refs else None)
        candidate = candidate_map.get(key)

        if candidate is None:
            # Task type no longer in candidates (e.g. no travelers anymore)
            continue

        new_blocker = candidate.get("blocker_code")
        current_blocked = task.status == "blocked"
        should_be_blocked = new_blocker is not None

        if current_blocked and not should_be_blocked:
            task.status = "ready"
            task.blocker_code = None
            task.blocker_refs = None
            reconciled.append(ReconciliationResult(
                task_id=task.id, old_status="blocked", new_status="ready"
            ))
        elif not current_blocked and should_be_blocked:
            task.status = "blocked"
            task.blocker_code = new_blocker
            task.blocker_refs = candidate.get("blocker_refs")
            reconciled.append(ReconciliationResult(
                task_id=task.id, old_status=task.status, new_status="blocked"
            ))

    if reconciled:
        await db.commit()

    return reconciled
