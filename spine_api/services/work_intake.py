"""
spine_api.services.work_intake — the single work-intake classification choke point.

Implements recommendation A1/A2 of the Incoming Work Classification Map
(Docs/architecture/INCOMING_WORK_CLASSIFICATION_MAP_2026-10-24.md §5): every
door that accepts external work classifies ONE WorkItem on the shared axes
(origin, intent, authority, urgency, entity binding, money boundary, PII
class) instead of each door inventing its own intake semantics.

Design contract:
- **Derived metadata only.** Raw traveler text, contact strings, and names are
  NEVER persisted. Contact reduces to a salted-free SHA-256 ``identity_key``
  scoped to the agency (C3); payload summary carries counts/flags only.
- **Classification is cheap and synchronous** (regex heuristics + one bounded
  memory read). Doors call it best-effort: a classification failure must never
  fail the door itself.
- **Recording is append-only JSONL** per agency (``data/work_items/{agency}.jsonl``,
  overridable via ``WAYPOINT_WORK_ITEMS_DIR``), mirroring the message-store
  durability pattern (spine_api/services/message_store.py).
- **Returning-guest recognition (C2 / roadmap U13)** is a classification
  annotation read from the durable memory store via the SAME entity-id
  convention as the remember/hydrate paths (``cust_<email|digits>``). It is
  display/queue metadata ONLY — per the ratified ADR-008 §7 row 4 / E-D §3
  slot 2 contract, memory facts are never written into the trip packet, never
  satisfy a gate, and the deeper authority-ranked slot injection remains
  roadmap Phase-2 (Invariant 2) work with its own gate.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

logger = logging.getLogger("spine_api.work_intake")

_WRITE_LOCK = threading.Lock()

# Origin classes (map §1): demand / supply / operator / system / world.
WORK_ORIGINS = ("demand", "supply", "operator", "system", "world")
# Intent types (map §1).
WORK_INTENTS = (
    "new_demand",
    "answer",
    "decision",
    "info",
    "exception",
    "query",
    "meta",
)
# Door-level default authority (A2): who the payload's assertions speak for.
WORK_AUTHORITIES = ("explicit_user", "operator", "profile", "system")
URGENCY_CLASSES = ("high", "normal", "low")

# door -> (origin, default intent, default authority). Reserved doors
# (whatsapp_channel, vendor_quote_inbox, disruption_feed) are registered so
# future doors declare their class at the seam instead of inventing one.
DOOR_CONTRACTS: Dict[str, Dict[str, str]] = {
    "run": {"origin": "demand", "intent": "new_demand", "authority": "operator"},
    "inbound_parse": {"origin": "demand", "intent": "new_demand", "authority": "explicit_user"},
    "channel_webhook": {"origin": "demand", "intent": "info", "authority": "explicit_user"},
    "ask_answers": {"origin": "demand", "intent": "answer", "authority": "explicit_user"},
    "collection_submit": {"origin": "demand", "intent": "info", "authority": "explicit_user"},
    "public_checker": {"origin": "demand", "intent": "new_demand", "authority": "explicit_user"},
    "proposal_acceptance": {"origin": "demand", "intent": "decision", "authority": "explicit_user"},
    "group_share": {"origin": "demand", "intent": "decision", "authority": "explicit_user"},
    "operator_action": {"origin": "operator", "intent": "meta", "authority": "operator"},
    "knowledge_admin": {"origin": "operator", "intent": "meta", "authority": "operator"},
    "triage_preview": {"origin": "demand", "intent": "info", "authority": "explicit_user"},
    # Reserved seams — no live door wires these yet (map §5 B1/B2/B3).
    "whatsapp_channel": {"origin": "demand", "intent": "new_demand", "authority": "explicit_user"},
    "vendor_quote_inbox": {"origin": "supply", "intent": "info", "authority": "explicit_user"},
    "disruption_feed": {"origin": "world", "intent": "exception", "authority": "system"},
}

DUPLICATE_WINDOW_HOURS = 24

_URGENT_RE = re.compile(
    r"\b(urgent|urgently|asap|emergency|tonight|today|tomorrow|right now|last[- ]minute|within \d+ (?:hours|days|hrs))\b",
    re.IGNORECASE,
)
_LOW_URGENCY_RE = re.compile(
    r"\b(just (?:browsing|exploring|looking)|no rush|sometime|not sure (?:when|if)|flexible|no plans yet)\b",
    re.IGNORECASE,
)
_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_PHONE_RE = re.compile(r"\+?\d[\d\s\-()]{6,}\d")


# ---------------------------------------------------------------------------
# Identity + heuristics
# ---------------------------------------------------------------------------

def normalize_contact(contact: str) -> Optional[str]:
    """Normalize a free-form contact to its stable comparison form.

    Email -> lowercased; otherwise digits-only phone (>=7 digits). This is the
    same normalization shape the inbound lead resolver uses
    (spine_api/routers/inbound.py::_resolve_existing_lead).
    """
    contact = (contact or "").strip()
    if not contact:
        return None
    if "@" in contact:
        email = _EMAIL_RE.search(contact)
        return (email.group(0) if email else contact.split()[0]).lower()
    digits = "".join(ch for ch in contact if ch.isdigit())
    return digits if len(digits) >= 7 else None


def identity_key(agency_id: str, contact: Optional[str]) -> Optional[str]:
    """Agency-scoped hash of a normalized contact (C3). One-way by design."""
    normalized = normalize_contact(contact or "")
    if not normalized:
        return None
    return hashlib.sha256(f"{agency_id}|{normalized}".encode("utf-8")).hexdigest()


def urgency_from_text(text: Optional[str]) -> str:
    """Cheap, deterministic urgency heuristic over the inbound words."""
    if not text:
        return "normal"
    if _URGENT_RE.search(text):
        return "high"
    if _LOW_URGENCY_RE.search(text):
        return "low"
    return "normal"


def harvest_contact(text: Optional[str]) -> Optional[str]:
    """Pull the first email or phone out of free text (for /run-style doors
    where contact is not a structured field)."""
    if not text:
        return None
    email = _EMAIL_RE.search(text)
    if email:
        return email.group(0).lower()
    phone = _PHONE_RE.search(text)
    if phone:
        digits = "".join(ch for ch in phone.group(0) if ch.isdigit())
        if len(digits) >= 7:
            return digits
    return None


def text_contains_pii(text: Optional[str]) -> bool:
    if not text:
        return False
    return bool(_EMAIL_RE.search(text) or _PHONE_RE.search(text))


# ---------------------------------------------------------------------------
# Returning-guest recognition (C2 — display-only annotation)
# ---------------------------------------------------------------------------

def _memory_facts_for_contact(agency_id: str, contact: Optional[str]) -> Dict[str, Any]:
    """Read on-file memory facts for the contact's canonical entity id.

    Uses the exact ``cust_`` convention the remember/hydrate paths write under
    (src/memory/feedback_bridge.py::traveler_entity_for), so recognition
    matches what was remembered. Never raises; classification is best-effort.
    """
    out: Dict[str, Any] = {"returning_customer": False, "memory_entity_id": None, "memory_fact_count": 0}
    normalized = normalize_contact(contact or "")
    if not normalized:
        return out
    try:
        from src.memory.feedback_bridge import traveler_entity_for
        from src.memory.slot_candidates import memory_on_file_facts
        from src.memory.store import get_memory_store

        email = normalized if "@" in normalized else None
        phone = None if email else normalized
        entity_id = traveler_entity_for(email, phone, "")
        facts = memory_on_file_facts(get_memory_store(), agency_id, entity_id)
        out["returning_customer"] = bool(facts)
        out["memory_entity_id"] = entity_id if facts else None
        out["memory_fact_count"] = len(facts)
    except Exception as exc:  # memory read is an annotation, never a blocker
        logger.debug("returning-guest lookup skipped: %s", exc)
    return out


# ---------------------------------------------------------------------------
# Store
# ---------------------------------------------------------------------------

def work_items_dir() -> Path:
    override = os.getenv("WAYPOINT_WORK_ITEMS_DIR", "").strip()
    base = Path(override) if override else Path("data/work_items")
    base.mkdir(parents=True, exist_ok=True)
    return base


def _agency_path(agency_id: str) -> Path:
    safe = "".join(ch for ch in agency_id if ch.isalnum() or ch in "-_") or "unknown"
    return work_items_dir() / f"{safe}.jsonl"


def _read_all(agency_id: str) -> List[Dict[str, Any]]:
    path = _agency_path(agency_id)
    if not path.exists():
        return []
    items: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                items.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return items


def _append(agency_id: str, item: Dict[str, Any]) -> None:
    path = _agency_path(agency_id)
    with _WRITE_LOCK:
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(item, ensure_ascii=False) + "\n")


def _find_recent_duplicate(items: List[Dict[str, Any]], item: Dict[str, Any]) -> Optional[str]:
    """C3: same traveler identity + same new-demand intent inside the window."""
    key = item.get("identity_key")
    if not key or item.get("intent") != "new_demand":
        return None
    now = datetime.now(timezone.utc)
    window = timedelta(hours=DUPLICATE_WINDOW_HOURS)
    for other in items:
        if other.get("identity_key") != key or other.get("item_id") == item.get("item_id"):
            continue
        if other.get("intent") != "new_demand":
            continue
        try:
            other_at = datetime.fromisoformat(str(other.get("received_at")))
        except (TypeError, ValueError):
            continue
        if other_at.tzinfo is None:
            other_at = other_at.replace(tzinfo=timezone.utc)
        if abs(now - other_at) <= window:
            return str(other.get("item_id"))
    return None


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------

def classify(
    door: str,
    *,
    agency_id: str,
    text: Optional[str] = None,
    contact: Optional[str] = None,
    channel: Optional[str] = None,
    trip_id: Optional[str] = None,
    run_id: Optional[str] = None,
    draft_id: Optional[str] = None,
    actor: Optional[str] = None,
    intent_override: Optional[str] = None,
    urgency_override: Optional[str] = None,
    money_touch: bool = False,
) -> Dict[str, Any]:
    """Pure classification (no persistence). Doors and preview surfaces
    (message triage) share this so preview and record can never diverge."""
    contract = DOOR_CONTRACTS.get(door)
    if contract is None:
        raise ValueError(f"Unknown work-intake door: {door!r} (register it in DOOR_CONTRACTS first)")
    intent = intent_override if intent_override in WORK_INTENTS else contract["intent"]
    urgency = urgency_override if urgency_override in URGENCY_CLASSES else urgency_from_text(text)
    resolved_contact = contact or harvest_contact(text)
    memory = _memory_facts_for_contact(agency_id, resolved_contact)
    return {
        "door": door,
        "origin": contract["origin"],
        "intent": intent,
        "authority": contract["authority"],
        "urgency": urgency,
        "channel": channel,
        "trip_id": trip_id,
        "run_id": run_id,
        "draft_id": draft_id,
        "actor": actor,
        "identity_key": identity_key(agency_id, resolved_contact),
        "identity_known": bool(normalize_contact(resolved_contact or "")),
        "returning_customer": memory["returning_customer"],
        "memory_entity_id": memory["memory_entity_id"],
        "memory_fact_count": memory["memory_fact_count"],
        "money_touch": bool(money_touch),
        "pii_present": text_contains_pii(text),
        "payload_summary": {"text_chars": len(text or "")},
    }


def classify_and_record(
    door: str,
    *,
    agency_id: str,
    text: Optional[str] = None,
    contact: Optional[str] = None,
    channel: Optional[str] = None,
    trip_id: Optional[str] = None,
    run_id: Optional[str] = None,
    draft_id: Optional[str] = None,
    actor: Optional[str] = None,
    intent_override: Optional[str] = None,
    urgency_override: Optional[str] = None,
    money_touch: bool = False,
) -> Dict[str, Any]:
    """Classify + persist one WorkItem. Best-effort by contract: doors wrap
    this in their own try/except so classification can never fail a door."""
    item = classify(
        door,
        agency_id=agency_id,
        text=text,
        contact=contact,
        channel=channel,
        trip_id=trip_id,
        run_id=run_id,
        draft_id=draft_id,
        actor=actor,
        intent_override=intent_override,
        urgency_override=urgency_override,
        money_touch=money_touch,
    )
    item["item_id"] = f"wi_{uuid4().hex[:12]}"
    item["received_at"] = datetime.now(timezone.utc).isoformat()
    try:
        item["duplicate_of"] = _find_recent_duplicate(_read_all(agency_id), item)
    except Exception as exc:
        logger.debug("duplicate scan skipped: %s", exc)
        item["duplicate_of"] = None
    _append(agency_id, item)
    return item


def record_outcome(agency_id: str, item_id: str, **fields: Any) -> None:
    """Attach derived outcome metadata (e.g. resolved trip_id) to a recorded
    item. Append-only store: outcomes land on a copy and the store rewrites
    that one line (bounded, lock-guarded)."""
    path = _agency_path(agency_id)
    if not path.exists():
        return
    with _WRITE_LOCK:
        lines: List[str] = []
        with path.open("r", encoding="utf-8") as fh:
            for line in fh:
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    rec = json.loads(stripped)
                except json.JSONDecodeError:
                    lines.append(stripped)
                    continue
                if rec.get("item_id") == item_id:
                    rec.update({k: v for k, v in fields.items() if v is not None})
                lines.append(json.dumps(rec, ensure_ascii=False))
        with path.open("w", encoding="utf-8") as fh:
            for line in lines:
                fh.write(line + "\n")


def duplicate_risk(agency_id: str, contact: Optional[str], *, intent: str = "new_demand") -> bool:
    """Public preview seam (E2): would this contact + intent duplicate a
    recently recorded item? Read-only; used by triage without persisting."""
    key = identity_key(agency_id, contact)
    if not key:
        return False
    try:
        probe = {"identity_key": key, "intent": intent, "item_id": None}
        return _find_recent_duplicate(_read_all(agency_id), probe) is not None
    except Exception:
        return False


_URGENCY_RANK = {"high": 0, "normal": 1, "low": 2}


def ranked_queue(agency_id: str, *, limit: int = 50) -> Dict[str, Any]:
    """C1: the operator work queue — urgency first, returning guests next,
    then recency. Plus honest counts per class."""
    items = _read_all(agency_id)
    items.sort(
        key=lambda r: (
            _URGENCY_RANK.get(r.get("urgency"), 1),
            0 if r.get("returning_customer") else 1,
            -(datetime.fromisoformat(r["received_at"]).timestamp() if r.get("received_at") else 0),
        )
    )
    counts: Dict[str, Dict[str, int]] = {
        "by_origin": {o: 0 for o in WORK_ORIGINS},
        "by_intent": {i: 0 for i in WORK_INTENTS},
        "by_urgency": {u: 0 for u in URGENCY_CLASSES},
    }
    for r in items:
        if r.get("origin") in counts["by_origin"]:
            counts["by_origin"][r["origin"]] += 1
        if r.get("intent") in counts["by_intent"]:
            counts["by_intent"][r["intent"]] += 1
        if r.get("urgency") in counts["by_urgency"]:
            counts["by_urgency"][r["urgency"]] += 1
    duplicates = sum(1 for r in items if r.get("duplicate_of"))
    returning = sum(1 for r in items if r.get("returning_customer"))
    return {
        "items": items[: max(1, limit)],
        "total": len(items),
        "duplicates_flagged": duplicates,
        "returning_customers": returning,
        "counts": counts,
        "count_basis": "work_item_log_total",
    }
