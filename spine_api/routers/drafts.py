"""
Draft router.

Owns the draft lifecycle API: create, list, read, update, discard/restore,
audit-event lookup, run lookup, and promotion. Extracted from
``spine_api.server`` without changing paths or response shapes.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from spine_api.core.auth import get_current_agency, get_current_user
from spine_api.draft_store import DraftStore
from spine_api.models.tenant import Agency, User
from spine_api.run_ledger import RunLedger

try:
    from spine_api import persistence
except (ImportError, ValueError):
    import persistence

AuditStore = persistence.AuditStore

router = APIRouter()


class CreateDraftRequest(BaseModel):
    name: Optional[str] = None
    customer_message: Optional[str] = None
    agent_notes: Optional[str] = None
    stage: str = "discovery"
    operating_mode: str = "normal_intake"
    scenario_id: Optional[str] = None
    strict_leakage: bool = False


class UpdateDraftRequest(BaseModel):
    name: Optional[str] = None
    customer_message: Optional[str] = None
    agent_notes: Optional[str] = None
    structured_json: Optional[dict] = None
    itinerary_text: Optional[str] = None
    stage: Optional[str] = None
    operating_mode: Optional[str] = None
    scenario_id: Optional[str] = None
    strict_leakage: Optional[bool] = None
    expected_version: Optional[int] = None
    is_auto_save: bool = False


class PromoteDraftRequest(BaseModel):
    trip_id: str


def _generate_draft_name(customer_message: Optional[str], agent_notes: Optional[str]) -> str:
    """Auto-generate draft name from first line of content."""
    content = (customer_message or "").strip() or (agent_notes or "").strip()
    if content:
        first_line = content.split("\n")[0].strip()
        if len(first_line) > 60:
            first_line = first_line[:57] + "..."
        return first_line or f"Draft — {datetime.now(timezone.utc).strftime('%b %d, %H:%M')}"
    return f"Draft — {datetime.now(timezone.utc).strftime('%b %d, %H:%M')}"


@router.post("/api/drafts")
def create_draft(
    request: CreateDraftRequest,
    agency: Agency = Depends(get_current_agency),
    user: User = Depends(get_current_user),
):
    """Create a new draft. Auto-generates name if not provided."""
    name = request.name or _generate_draft_name(request.customer_message, request.agent_notes)
    draft = DraftStore.create(
        agency_id=agency.id,
        created_by=user.id,
        name=name,
        customer_message=request.customer_message,
        agent_notes=request.agent_notes,
        stage=request.stage,
        operating_mode=request.operating_mode,
        scenario_id=request.scenario_id,
        strict_leakage=request.strict_leakage,
    )
    AuditStore.log_event("draft_created", user.id, {
        "draft_id": draft.id,
        "agency_id": agency.id,
        "name": draft.name,
    })
    return {
        "draft_id": draft.id,
        "name": draft.name,
        "status": draft.status,
        "created_at": draft.created_at,
    }


@router.get("/api/drafts")
def list_drafts(
    status: Optional[str] = None,
    limit: int = 100,
    agency: Agency = Depends(get_current_agency),
    user: User = Depends(get_current_user),
):
    """List drafts for the current agency, optionally filtered by status."""
    drafts = DraftStore.list_by_agency(agency.id, status=status, limit=limit)
    return {
        "items": [
            {
                "draft_id": d.id,
                "name": d.name,
                "status": d.status,
                "stage": d.stage,
                "operating_mode": d.operating_mode,
                "last_run_state": d.last_run_state,
                "promoted_trip_id": d.promoted_trip_id,
                "created_at": d.created_at,
                "updated_at": d.updated_at,
                "created_by": d.created_by,
            }
            for d in drafts
        ],
        "total": len(drafts),
    }


@router.get("/api/drafts/{draft_id}")
def get_draft(
    draft_id: str,
    agency: Agency = Depends(get_current_agency),
):
    """Get a single draft by ID."""
    draft = DraftStore.get(draft_id)
    if not draft or draft.agency_id != agency.id:
        raise HTTPException(status_code=404, detail="Draft not found")
    return draft.model_dump()


@router.put("/api/drafts/{draft_id}")
def update_draft(
    draft_id: str,
    request: UpdateDraftRequest,
    agency: Agency = Depends(get_current_agency),
    user: User = Depends(get_current_user),
):
    """Full update of a draft. Requires version match for optimistic concurrency."""
    draft = DraftStore.get(draft_id)
    if not draft or draft.agency_id != agency.id:
        raise HTTPException(status_code=404, detail="Draft not found")

    if draft.status in ("promoted", "merged", "discarded"):
        raise HTTPException(status_code=409, detail=f"Cannot update draft in status: {draft.status}")

    updates = request.model_dump(exclude_none=True)
    is_auto_save = updates.pop("is_auto_save", False)
    expected_version = updates.pop("expected_version", None)

    try:
        updated = DraftStore.patch(draft_id, updates, expected_version=expected_version)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))

    if updated:
        AuditStore.log_event(
            "draft_autosaved" if is_auto_save else "draft_saved",
            user.id,
            {"draft_id": draft_id, "fields_changed": list(updates.keys()), "auto_save": is_auto_save},
        )
    return updated.model_dump() if updated else None


@router.patch("/api/drafts/{draft_id}")
def patch_draft(
    draft_id: str,
    request: UpdateDraftRequest,
    agency: Agency = Depends(get_current_agency),
    user: User = Depends(get_current_user),
):
    """Partial update of a draft. Same as PUT but semantic PATCH."""
    return update_draft(draft_id, request, agency, user)


@router.delete("/api/drafts/{draft_id}")
def discard_draft(
    draft_id: str,
    agency: Agency = Depends(get_current_agency),
    user: User = Depends(get_current_user),
):
    """Soft-delete a draft."""
    draft = DraftStore.get(draft_id)
    if not draft or draft.agency_id != agency.id:
        raise HTTPException(status_code=404, detail="Draft not found")

    discarded = DraftStore.discard(draft_id, user.id)
    if discarded:
        AuditStore.log_event("draft_discarded", user.id, {"draft_id": draft_id})
    return {"ok": True, "draft_id": draft_id, "status": "discarded"}


@router.post("/api/drafts/{draft_id}/restore")
def restore_draft(
    draft_id: str,
    agency: Agency = Depends(get_current_agency),
    user: User = Depends(get_current_user),
):
    """Restore a discarded draft."""
    draft = DraftStore.get(draft_id)
    if not draft or draft.agency_id != agency.id:
        raise HTTPException(status_code=404, detail="Draft not found")

    restored = DraftStore.restore(draft_id)
    if restored:
        AuditStore.log_event("draft_restored", user.id, {"draft_id": draft_id})
    return {"ok": True, "draft_id": draft_id, "status": restored.status if restored else "unknown"}


@router.get("/api/drafts/{draft_id}/events")
def get_draft_events(
    draft_id: str,
    limit: int = 100,
    agency: Agency = Depends(get_current_agency),
):
    """Get audit events for a draft."""
    draft = DraftStore.get(draft_id)
    if not draft or draft.agency_id != agency.id:
        raise HTTPException(status_code=404, detail="Draft not found")

    all_events = AuditStore.get_events(limit=limit * 2)
    draft_events = [
        e for e in all_events
        if e.get("details", {}).get("draft_id") == draft_id
    ]
    return {"draft_id": draft_id, "events": draft_events[-limit:], "total": len(draft_events)}


@router.get("/api/drafts/{draft_id}/runs")
def get_draft_runs(
    draft_id: str,
    agency: Agency = Depends(get_current_agency),
):
    """Get runs linked to this draft via run_snapshots."""
    draft = DraftStore.get(draft_id)
    if not draft or draft.agency_id != agency.id:
        raise HTTPException(status_code=404, detail="Draft not found")

    runs = []
    for snapshot in (draft.run_snapshots or []):
        run_id = snapshot.get("run_id")
        if not run_id:
            continue
        meta = RunLedger.get_meta(run_id)
        if meta and meta.get("agency_id") == agency.id:
            runs.append(meta)

    return {"draft_id": draft_id, "runs": runs, "total": len(runs)}


@router.post("/api/drafts/{draft_id}/promote")
def promote_draft(
    draft_id: str,
    request: PromoteDraftRequest,
    agency: Agency = Depends(get_current_agency),
    user: User = Depends(get_current_user),
):
    """Promote a draft to a trip. Marks draft as promoted and read-only."""
    trip_id = request.trip_id
    draft = DraftStore.get(draft_id)
    if not draft or draft.agency_id != agency.id:
        raise HTTPException(status_code=404, detail="Draft not found")

    if draft.status == "promoted":
        raise HTTPException(status_code=409, detail="Draft already promoted")

    promoted = DraftStore.promote(draft_id, trip_id)
    if promoted:
        AuditStore.log_event("draft_promoted", user.id, {
            "draft_id": draft_id,
            "trip_id": trip_id,
        })
    return {"ok": True, "draft_id": draft_id, "trip_id": trip_id, "status": "promoted"}
