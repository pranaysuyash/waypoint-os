"""
spine_api/draft_store.py — Draft persistence layer for Waypoint OS.

Provides:
- Draft model (Pydantic, schema-ready for future SQL migration)
- FileDraftStore: file-based JSON backend for Phase 0
- DraftStore: stable facade (allows future SQL backend swap)

Architecture:
    Draft = operational entity with lifecycle, ownership, and audit trail.
    FileDraftStore persists as JSON files for Phase 0 debuggability.
    The abstraction (DraftStore) keeps callers agnostic to backend.

Directory layout:
    data/drafts/
        draft_<id>.json     — draft document
        index.json          — rebuildable agency/user/status index

File writes are atomic (temp file + rename) with file_lock() concurrency.
"""

from __future__ import annotations

import json
import os
import threading
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

from spine_api.persistence import file_lock

logger = __import__("logging").getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DRAFTS_DIR = DATA_DIR / "drafts"
INDEX_FILE = DRAFTS_DIR / "index.json"
MAX_EVENTS_PER_DRAFT = 1000  # Cap audit event history per draft

# Ensure directory exists
DRAFTS_DIR.mkdir(parents=True, exist_ok=True)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------

class Draft(BaseModel):
    # === Identity (SQL metadata) ===
    id: str
    agency_id: str
    created_by: str
    assigned_to: Optional[str] = None

    # === Metadata (SQL metadata) ===
    name: str
    name_source: str = "auto"
    status: str = "open"  # open | processing | blocked | failed | promoted | merged | discarded
    stage: str = "discovery"
    operating_mode: str = "normal_intake"
    scenario_id: Optional[str] = None
    strict_leakage: bool = False
    source_channel: Optional[str] = None

    # === Customer identity (future duplicate detection) ===
    customer_id: Optional[str] = None
    customer_name_snapshot: Optional[str] = None
    customer_phone_hash: Optional[str] = None
    customer_email_hash: Optional[str] = None

    # === Run tracking (SQL metadata) ===
    last_run_id: Optional[str] = None
    last_run_state: Optional[str] = None
    last_run_completed_at: Optional[str] = None

    # === Promotion (SQL metadata) ===
    promoted_trip_id: Optional[str] = None
    promoted_at: Optional[str] = None
    merged_into_draft_id: Optional[str] = None

    # === Lifecycle (SQL metadata) ===
    discarded_at: Optional[str] = None
    discarded_by: Optional[str] = None
    version: int = 1
    created_at: str
    updated_at: str

    # === Payload (JSONB in full app) ===
    customer_message: Optional[str] = None
    agent_notes: Optional[str] = None
    structured_json: Optional[dict] = None
    itinerary_text: Optional[str] = None
    last_validation: Optional[dict] = None
    last_packet: Optional[dict] = None
    run_snapshots: list[dict] = Field(default_factory=list)
    merge_history: list[dict] = Field(default_factory=list)

    # === Linking cache (denormalized from draft_links table in full app) ===
    linked_draft_ids: list[str] = Field(default_factory=list)
    linked_trip_ids: list[str] = Field(default_factory=list)

    class Config:
        extra = "allow"  # Forward-compatible with future fields


def _draft_path(draft_id: str) -> Path:
    return DRAFTS_DIR / f"{draft_id}.json"


# ---------------------------------------------------------------------------
# FileDraftStore
# ---------------------------------------------------------------------------

class FileDraftStore:
    """
    File-based draft storage using JSON.

    All writes are atomic (temp file + rename) and use file_lock()
    for cross-process safety.

    Index is rebuildable by scanning data/drafts/*.json.
    """

    _lock = threading.Lock()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _load_json(path: Path) -> Optional[dict]:
        if not path.exists():
            return None
        try:
            with open(path, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except json.JSONDecodeError:
            logger.error("Corrupt draft file: %s", path)
            return None

    @staticmethod
    def _save_json(path: Path, data: dict) -> None:
        """Atomic write: write to temp file, then rename."""
        temp_path = path.with_suffix(path.suffix + ".tmp")
        with open(temp_path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, default=str)
        os.replace(temp_path, path)

    @staticmethod
    def _load_index() -> dict:
        if not INDEX_FILE.exists():
            return {"version": 1, "by_agency": {}, "by_user": {}, "by_status": {}}
        data = FileDraftStore._load_json(INDEX_FILE)
        if data is None:
            return {"version": 1, "by_agency": {}, "by_user": {}, "by_status": {}}
        return data

    @staticmethod
    def _save_index(index: dict) -> None:
        with FileDraftStore._lock:
            with file_lock(INDEX_FILE, timeout_seconds=10.0):
                FileDraftStore._save_json(INDEX_FILE, index)

    @staticmethod
    def _rebuild_index() -> dict:
        """Rebuild index from all draft files. Used as recovery fallback."""
        index: dict[str, Any] = {
            "version": 1,
            "by_agency": {},
            "by_user": {},
            "by_status": {},
        }
        for path in DRAFTS_DIR.glob("draft_*.json"):
            data = FileDraftStore._load_json(path)
            if not data:
                continue
            draft_id = data.get("id")
            if not draft_id:
                continue
            agency_id = data.get("agency_id")
            created_by = data.get("created_by")
            status = data.get("status")
            if agency_id:
                index["by_agency"].setdefault(agency_id, []).append(draft_id)
            if created_by:
                index["by_user"].setdefault(created_by, []).append(draft_id)
            if status:
                index["by_status"].setdefault(status, []).append(draft_id)
        return index

    @staticmethod
    def _update_index_for(draft_id: str, old_status: Optional[str], new_status: str, agency_id: str, user_id: str) -> None:
        """Efficiently update index when a single draft changes."""
        with FileDraftStore._lock:
            with file_lock(INDEX_FILE, timeout_seconds=10.0):
                index = FileDraftStore._load_index()
                # Remove from old status bucket
                if old_status and old_status in index.get("by_status", {}):
                    index["by_status"][old_status] = [
                        d for d in index["by_status"][old_status] if d != draft_id
                    ]
                # Add to new status bucket
                index.setdefault("by_status", {}).setdefault(new_status, [])
                if draft_id not in index["by_status"][new_status]:
                    index["by_status"][new_status].append(draft_id)
                # Ensure agency listing
                index.setdefault("by_agency", {}).setdefault(agency_id, [])
                if draft_id not in index["by_agency"][agency_id]:
                    index["by_agency"][agency_id].append(draft_id)
                # Ensure user listing
                index.setdefault("by_user", {}).setdefault(user_id, [])
                if draft_id not in index["by_user"][user_id]:
                    index["by_user"][user_id].append(draft_id)
                FileDraftStore._save_json(INDEX_FILE, index)

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    @staticmethod
    def create(
        agency_id: str,
        created_by: str,
        name: str,
        customer_message: Optional[str] = None,
        agent_notes: Optional[str] = None,
        stage: str = "discovery",
        operating_mode: str = "normal_intake",
        scenario_id: Optional[str] = None,
        strict_leakage: bool = False,
        source_channel: Optional[str] = None,
    ) -> Draft:
        draft_id = f"draft_{uuid4().hex[:12]}"
        now = _now_iso()
        draft = Draft(
            id=draft_id,
            agency_id=agency_id,
            created_by=created_by,
            assigned_to=created_by,
            name=name,
            name_source="auto" if name.startswith("Draft —") else "user",
            status="open",
            stage=stage,
            operating_mode=operating_mode,
            scenario_id=scenario_id,
            strict_leakage=strict_leakage,
            source_channel=source_channel,
            customer_message=customer_message,
            agent_notes=agent_notes,
            created_at=now,
            updated_at=now,
        )
        path = _draft_path(draft_id)
        with FileDraftStore._lock:
            with file_lock(path, timeout_seconds=10.0):
                FileDraftStore._save_json(path, draft.model_dump())
        FileDraftStore._update_index_for(draft_id, None, "open", agency_id, created_by)
        return draft

    @staticmethod
    def get(draft_id: str) -> Optional[Draft]:
        path = _draft_path(draft_id)
        data = FileDraftStore._load_json(path)
        if not data:
            return None
        try:
            return Draft.model_validate(data)
        except Exception as exc:
            logger.error("Invalid draft data for %s: %s", draft_id, exc)
            return None

    @staticmethod
    def save(draft: Draft, auto_save: bool = False) -> Draft:
        """Full save. Increments version. Returns updated draft."""
        path = _draft_path(draft.id)
        existing = FileDraftStore.get(draft.id)
        old_status = existing.status if existing else None
        now = _now_iso()
        draft.updated_at = now
        draft.version += 1
        with FileDraftStore._lock:
            with file_lock(path, timeout_seconds=10.0):
                FileDraftStore._save_json(path, draft.model_dump())
        if old_status != draft.status:
            FileDraftStore._update_index_for(draft.id, old_status, draft.status, draft.agency_id, draft.created_by)
        return draft

    @staticmethod
    def patch(draft_id: str, updates: dict, expected_version: Optional[int] = None) -> Optional[Draft]:
        """
        Partial update with optimistic concurrency.

        If expected_version is provided and does not match current version,
        raises ValueError (409 conflict).
        """
        path = _draft_path(draft_id)
        with FileDraftStore._lock:
            with file_lock(path, timeout_seconds=10.0):
                data = FileDraftStore._load_json(path)
                if not data:
                    return None
                if expected_version is not None and data.get("version") != expected_version:
                    raise ValueError(
                        f"Draft {draft_id} version conflict: expected {expected_version}, got {data.get('version')}"
                    )
                old_status = data.get("status")
                data.update(updates)
                data["updated_at"] = _now_iso()
                data["version"] = data.get("version", 0) + 1
                FileDraftStore._save_json(path, data)
        # Update index if status changed
        if updates.get("status") and updates["status"] != old_status:
            draft = Draft.model_validate(data)
            FileDraftStore._update_index_for(draft_id, old_status, draft.status, draft.agency_id, draft.created_by)
        return Draft.model_validate(data)

    @staticmethod
    def discard(draft_id: str, discarded_by: str) -> Optional[Draft]:
        """Soft delete: set status to discarded."""
        return FileDraftStore.patch(
            draft_id,
            {"status": "discarded", "discarded_at": _now_iso(), "discarded_by": discarded_by},
        )

    @staticmethod
    def restore(draft_id: str) -> Optional[Draft]:
        """Restore a discarded draft to open."""
        return FileDraftStore.patch(
            draft_id,
            {"status": "open", "discarded_at": None, "discarded_by": None},
        )

    @staticmethod
    def list_by_agency(agency_id: str, status: Optional[str] = None, limit: int = 100) -> list[Draft]:
        """List drafts for an agency, optionally filtered by status."""
        index = FileDraftStore._load_index()
        ids = index.get("by_agency", {}).get(agency_id, [])
        drafts: list[Draft] = []
        for draft_id in ids:
            draft = FileDraftStore.get(draft_id)
            if draft and draft.status != "discarded":
                if status is None or draft.status == status:
                    drafts.append(draft)
            if len(drafts) >= limit:
                break
        return drafts

    @staticmethod
    def list_by_user(user_id: str, status: Optional[str] = None, limit: int = 100) -> list[Draft]:
        """List drafts created by a user."""
        index = FileDraftStore._load_index()
        ids = index.get("by_user", {}).get(user_id, [])
        drafts: list[Draft] = []
        for draft_id in ids:
            draft = FileDraftStore.get(draft_id)
            if draft and draft.status != "discarded":
                if status is None or draft.status == status:
                    drafts.append(draft)
            if len(drafts) >= limit:
                break
        return drafts

    @staticmethod
    def promote(draft_id: str, trip_id: str) -> Optional[Draft]:
        """
        Promote a draft to a trip.
        Sets status to promoted, stores promoted_trip_id.
        Returns updated draft.
        """
        return FileDraftStore.patch(
            draft_id,
            {
                "status": "promoted",
                "promoted_trip_id": trip_id,
                "promoted_at": _now_iso(),
            },
        )

    @staticmethod
    def update_run_state(
        draft_id: str,
        run_id: str,
        run_state: str,
        run_snapshot: Optional[dict] = None,
    ) -> Optional[Draft]:
        """
        Update draft with latest run state.
        Also appends run snapshot to run_snapshots array (capped).
        """
        draft = FileDraftStore.get(draft_id)
        if not draft:
            return None
        updates: dict[str, Any] = {
            "last_run_id": run_id,
            "last_run_state": run_state,
        }
        if run_state in ("completed", "failed", "blocked"):
            updates["last_run_completed_at"] = _now_iso()
        # Update status based on run state
        if run_state == "completed":
            updates["status"] = "open"  # stays open until explicitly promoted
        elif run_state == "blocked":
            updates["status"] = "blocked"
        elif run_state == "failed":
            updates["status"] = "failed"
        elif run_state == "running":
            updates["status"] = "processing"
        # Append run snapshot (cap at MAX_EVENTS_PER_DRAFT)
        snapshots = draft.run_snapshots or []
        if run_snapshot:
            snapshots.append({
                "run_id": run_id,
                "state": run_state,
                "snapshot": run_snapshot,
                "timestamp": _now_iso(),
            })
            if len(snapshots) > MAX_EVENTS_PER_DRAFT:
                snapshots = snapshots[-MAX_EVENTS_PER_DRAFT:]
            updates["run_snapshots"] = snapshots
        return FileDraftStore.patch(draft_id, updates)

    @staticmethod
    def rebuild_index() -> dict:
        """Rebuild index from all draft files. Returns new index."""
        index = FileDraftStore._rebuild_index()
        FileDraftStore._save_index(index)
        return index


# ---------------------------------------------------------------------------
# DraftStore facade
# ---------------------------------------------------------------------------

class DraftStore:
    """
    Stable facade over draft persistence.

    Phase 0: delegates to FileDraftStore.
    Future: can be swapped to SQLDraftStore without changing callers.
    """

    _backend = FileDraftStore

    @staticmethod
    def create(*args: Any, **kwargs: Any) -> Draft:
        return DraftStore._backend.create(*args, **kwargs)

    @staticmethod
    def get(draft_id: str) -> Optional[Draft]:
        return DraftStore._backend.get(draft_id)

    @staticmethod
    def save(draft: Draft, auto_save: bool = False) -> Draft:
        return DraftStore._backend.save(draft, auto_save=auto_save)

    @staticmethod
    def patch(draft_id: str, updates: dict, expected_version: Optional[int] = None) -> Optional[Draft]:
        return DraftStore._backend.patch(draft_id, updates, expected_version=expected_version)

    @staticmethod
    def discard(draft_id: str, discarded_by: str) -> Optional[Draft]:
        return DraftStore._backend.discard(draft_id, discarded_by)

    @staticmethod
    def restore(draft_id: str) -> Optional[Draft]:
        return DraftStore._backend.restore(draft_id)

    @staticmethod
    def list_by_agency(agency_id: str, status: Optional[str] = None, limit: int = 100) -> list[Draft]:
        return DraftStore._backend.list_by_agency(agency_id, status=status, limit=limit)

    @staticmethod
    def list_by_user(user_id: str, status: Optional[str] = None, limit: int = 100) -> list[Draft]:
        return DraftStore._backend.list_by_user(user_id, status=status, limit=limit)

    @staticmethod
    def promote(draft_id: str, trip_id: str) -> Optional[Draft]:
        return DraftStore._backend.promote(draft_id, trip_id)

    @staticmethod
    def update_run_state(
        draft_id: str,
        run_id: str,
        run_state: str,
        run_snapshot: Optional[dict] = None,
    ) -> Optional[Draft]:
        return DraftStore._backend.update_run_state(draft_id, run_id, run_state, run_snapshot=run_snapshot)

    @staticmethod
    def rebuild_index() -> dict:
        return DraftStore._backend.rebuild_index()
