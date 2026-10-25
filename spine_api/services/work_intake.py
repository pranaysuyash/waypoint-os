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
# (whatsapp_channel, vendor_quote_inbox) are registered so future doors
# declare their class at the seam instead of inventing one. disruption_feed
# is wired by the in-tree IROPS watch loop (deterministic-preview signal);
# the live flight-status upgrade rides the same door unchanged.
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
    # Reserved seams — no live door wires these yet (map §5 B1/B2).
    "whatsapp_channel": {"origin": "demand", "intent": "new_demand", "authority": "explicit_user"},
    "vendor_quote_inbox": {"origin": "supply", "intent": "info", "authority": "explicit_user"},
    # Wired by the IROPS watch loop (map §13): world-side disruption →
    # operator obligation to review the auto-healing plan.
    "disruption_feed": {"origin": "world", "intent": "exception", "authority": "system"},
    # W4 system-generated operator work (map §5 E3).
    "ghost_concierge": {"origin": "system", "intent": "exception", "authority": "system"},
    "requeue_poison": {"origin": "system", "intent": "exception", "authority": "system"},
    # Third tranche (map §11): traveler words arriving via non-canonical doors.
    "social_inbound": {"origin": "demand", "intent": "new_demand", "authority": "explicit_user"},
    "checker_route_request": {"origin": "demand", "intent": "new_demand", "authority": "explicit_user"},
    "multimodal": {"origin": "demand", "intent": "info", "authority": "explicit_user"},
    # W4 writers (map §11): recovery-agent escalation → agency queue.
    "recovery_escalation": {"origin": "system", "intent": "exception", "authority": "system"},
    # W4 writers (map §13): supervisor terminal poison + stale-run sweep.
    "supervisor_escalation": {"origin": "system", "intent": "exception", "authority": "system"},
    "stale_run_timeout": {"origin": "system", "intent": "exception", "authority": "system"},
}

# ---------------------------------------------------------------------------
# Operator display vocabulary (2026-10-25 supersession of map §12.1's raw
# "origin · intent · authority" subtitle): the classification axes are machine
# vocabulary for routing and gating; the queue is a read-model projection, so
# the human sentence is COMPOSED AT READ TIME (work_intake.display_for) —
# never stored on the append-only log. Read-time composition means label
# evolution never rewrites history, pre-lifecycle rows are retroactively
# labeled, and the FE can never drift from the door semantics because the
# backend is the only composer. Exhaustiveness is enforced by test
# (test_door_display_covers_every_door): a new door cannot ship jargon.
# ---------------------------------------------------------------------------

# Human headline per door. "{channel}" is substituted with the channel's
# display name (CHANNEL_DISPLAY) when the item carries one; doors whose
# headline does not reference {channel} keep the channel in the meta line.
DOOR_DISPLAY: Dict[str, str] = {
    "run": "Run request submitted",
    "inbound_parse": "New trip request",
    "channel_webhook": "{channel} message received",
    "ask_answers": "Traveler answered pending questions",
    "collection_submit": "Traveler submitted details",
    "public_checker": "Public checker request routed in",
    "proposal_acceptance": "Proposal decision received",
    "group_share": "Group share received",
    "operator_action": "Operator updated a trip",
    "knowledge_admin": "Knowledge base updated",
    "triage_preview": "Message triaged for review",
    # Reserved seams (map §5 B1/B2).
    "whatsapp_channel": "{channel} message received",
    "vendor_quote_inbox": "Vendor quote received",
    # World/system doors (map §11/§13).
    "disruption_feed": "Disruption detected on a live trip",
    "ghost_concierge": "Silent traveler detected — draft awaiting review",
    "requeue_poison": "Poisoned job quarantined",
    "social_inbound": "{channel} message received",
    "checker_route_request": "Public checker lead routed in",
    "multimodal": "Attachment received",
    "recovery_escalation": "Recovery agent escalated a disruption",
    "supervisor_escalation": "Supervisor escalation recorded",
    "stale_run_timeout": "Run timed out",
}

CHANNEL_DISPLAY: Dict[str, str] = {
    "whatsapp": "WhatsApp",
    "email": "Email",
    "sms": "SMS",
    "web": "Web",
    "phone": "Phone",
    "voice": "Voice",
    "instagram": "Instagram",
    "facebook": "Facebook",
    "telegram": "Telegram",
    "booking_collection": "Collection form",
    "public_checker": "Public checker",
    "proposal_link": "Proposal link",
    "group_pay": "Group payment",
}

# System/synthetic actor slugs → operator-facing labels. User-UUID actors are
# resolved to display names by the router (batched query); anything not here
# and not a UUID (e.g. an operator email) passes through as-is.
ACTOR_DISPLAY: Dict[str, str] = {
    "irops_watch": "the disruption watch",
    "run_ledger_sweep": "the run watchdog",
    "agent_requeue_jobs": "the requeue worker",
    "ghost_concierge": "the concierge monitor",
    "public_checker": "the public checker",
    "system": "the system",
    "traveler_collection_link": "the collection form",
    "traveler_proposal_link": "the proposal link",
    "public_asks": "the public ask form",
}

_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


def _display_channel(channel: Optional[str]) -> str:
    """Human channel name; unknown channels degrade to title-case, never None.

    Unknown channel slugs are identifiers ("pigeon_post") — underscores are
    jargon in operator prose (map §15 display contract), so degrade to spaces
    before title-casing, same rule as unknown door names in display_for.
    """
    if not channel:
        return "Message"
    raw = str(channel).strip()
    return CHANNEL_DISPLAY.get(raw.lower(), raw.replace("_", " ").title())


def display_for(
    item: Dict[str, Any],
    *,
    trip_label: Optional[str] = None,
    actor_label: Optional[str] = None,
) -> Dict[str, Any]:
    """Compose the operator-facing projection of one classified WorkItem.

    Pure and read-time (never persisted): ``headline`` is the row title an
    operator can act on; ``meta`` is the human context line (channel when the
    headline did not already carry it, the bound entity label, the actor).
    Raw classification axes (origin/intent/authority, raw ids) stay on the
    entry for tooling/tooltips — they are debug vocabulary, not display copy.
    ``actor_label`` carries the user-display-name resolution done by the
    router (batched per request); ``ACTOR_DISPLAY`` covers system/synthetic
    actors here. Unknown doors degrade to a title-cased door name rather than
    raising, so display can never fail a queue read.
    """
    door = str(item.get("door") or "")
    template = DOOR_DISPLAY.get(door)
    channel_name = _display_channel(item.get("channel"))
    if template is None:
        headline = door.replace("_", " ").strip().title() or "Work item"
        headline_carried_channel = False
    elif item.get("channel"):
        headline_carried_channel = "{channel}" in template
        headline = template.replace("{channel}", channel_name)
    else:
        # Channel-less degradation: "{channel} message received" composes to
        # "Message received" (never "Message message received"); any other
        # {channel} template degrades to a grammatical "Inbound …" form.
        headline_carried_channel = True
        headline = template.replace("{channel} message", "Message").replace(
            "{channel}", "Inbound"
        )
    meta: List[str] = []
    if item.get("channel") and not headline_carried_channel:
        meta.append(channel_name)
    if trip_label:
        meta.append(f"Trip — {trip_label}")
    elif item.get("trip_id"):
        # Entity binding exists but the trip did not resolve: keep the raw id
        # on the entry (tooltip/tooling) but do not put an opaque id in prose.
        pass
    actor = item.get("actor")
    if actor:
        # Actor display: the router resolves user-UUID actors to names
        # (actor_label); system/synthetic actors fall to ACTOR_DISPLAY here.
        # Raw ids never reach prose — an unresolved actor drops the "by" line
        # entirely (the id stays on the entry for tooltips/tooling).
        if actor_label:
            meta.append(f"by {actor_label}")
        else:
            human_actor = ACTOR_DISPLAY.get(str(actor))
            if human_actor:
                meta.append(f"by {human_actor}")
            elif not _UUID_RE.match(str(actor)):
                meta.append(f"by {actor}")
    return {"headline": headline, "meta": meta}


# The requeue queue is deliberately agency-less (agent_requeue_jobs.py::
# list_poisoned: "a tenant-facing route must not be inferred until an
# ownership contract exists"). Poison work items record under this scope —
# observable in the store, but NOT on the tenant queue endpoint; a platform-
# scope reader can expose them once that ownership contract exists.
SYSTEM_WORK_SCOPE = "__system__"

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


# ---------------------------------------------------------------------------
# Outcome-state lifecycle (map §14): open → claimed → resolved/dismissed.
# Event-sourced — lifecycle transitions append as their own records to the
# same agency log (record_type="lifecycle_event") and state is DERIVED at
# read time. The log stays append-only; the event trail IS the audit trail.
# ---------------------------------------------------------------------------

WORK_ITEM_STATES = ("open", "claimed", "resolved", "dismissed")
LIFECYCLE_ACTIONS = ("claim", "unclaim", "dismiss", "resolve")

_ACTION_TARGET_STATE = {
    "claim": "claimed",
    "unclaim": "open",
    "dismiss": "dismissed",
    "resolve": "resolved",
}
# (current_state, action) pairs the machine accepts. resolved/dismissed are
# terminal — done work never re-enters the queue through the same item.
_VALID_TRANSITIONS = {
    ("open", "claim"),
    ("claimed", "unclaim"),
    ("open", "dismiss"),
    ("claimed", "dismiss"),
    ("open", "resolve"),
    ("claimed", "resolve"),
}


def _derive_lifecycle(items: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Fold lifecycle events (in append order) into per-item state. Records
    without record_type are items (backward compat with pre-lifecycle logs)."""
    states: Dict[str, Dict[str, Any]] = {}
    for rec in items:
        if rec.get("record_type") == "lifecycle_event":
            target = str(rec.get("target_item_id") or "")
            if not target:
                continue
            state = states.setdefault(
                target,
                {"state": "open", "claimed_by": None, "claimed_at": None, "actions": 0},
            )
            action = str(rec.get("action") or "")
            if (state["state"], action) not in _VALID_TRANSITIONS:
                continue  # stale/duplicated event; state machine ignores it
            state["state"] = _ACTION_TARGET_STATE[action]
            state["actions"] += 1
            if action == "claim":
                state["claimed_by"] = rec.get("actor")
                state["claimed_at"] = rec.get("at")
            elif action == "unclaim":
                state["claimed_by"] = None
                state["claimed_at"] = None
    return states


def record_lifecycle(
    agency_id: str,
    item_id: str,
    action: str,
    *,
    actor: Optional[str] = None,
    note: Optional[str] = None,
) -> Dict[str, Any]:
    """Apply one lifecycle transition to a recorded item. Raises KeyError if
    the item does not exist in this agency's log and ValueError if the
    transition is invalid for the item's current state. Returns the derived
    post-transition state."""
    if action not in LIFECYCLE_ACTIONS:
        raise ValueError(f"Unknown lifecycle action: {action!r}")
    items = _read_all(agency_id)
    exists = any(
        r.get("item_id") == item_id and r.get("record_type", "item") == "item" for r in items
    )
    if not exists:
        raise KeyError(f"Work item not found: {item_id!r}")

    states = _derive_lifecycle(items)
    current = states.get(item_id, {"state": "open", "claimed_by": None})
    if (current["state"], action) not in _VALID_TRANSITIONS:
        raise ValueError(
            f"Invalid transition: item {item_id!r} is {current['state']!r}; "
            f"action {action!r} is not allowed from that state"
        )

    event = {
        "record_type": "lifecycle_event",
        "target_item_id": item_id,
        "action": action,
        "actor": actor,
        "note": (note or None)[:200] if note else None,
        "at": datetime.now(timezone.utc).isoformat(),
    }
    _append(agency_id, event)
    new_state = _ACTION_TARGET_STATE[action]
    return {
        "item_id": item_id,
        "previous_state": current["state"],
        "state": new_state,
        "claimed_by": (actor if new_state == "claimed" else None),
        "at": event["at"],
    }


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


def ranked_queue(agency_id: str, *, limit: int = 50, include_done: bool = False) -> Dict[str, Any]:
    """C1: the operator work queue — urgency first, returning guests next,
    then recency. Lifecycle-aware: resolved/dismissed items leave the ranked
    list; open + claimed stay (claimed carries its badge). Class counts
    describe ACTIONABLE work; ``total`` and ``counts.by_state`` stay honest
    log totals over everything ever recorded.

    ``include_done=True`` is the history reader (map §14.4): resolved/dismissed
    items appear AFTER the actionable list (same sort within each group), so
    the top of the queue is always actionable even in history mode."""
    records = _read_all(agency_id)
    states = _derive_lifecycle(records)
    items = [r for r in records if r.get("record_type", "item") == "item"]
    annotated = []
    for r in items:
        rec = dict(r)
        state = states.get(rec["item_id"], {"state": "open", "claimed_by": None})
        rec["state"] = state["state"]
        rec["claimed_by"] = state["claimed_by"]
        annotated.append(rec)

    def _rank(r: Dict[str, Any]) -> tuple:
        return (
            _URGENCY_RANK.get(r.get("urgency"), 1),
            0 if r.get("returning_customer") else 1,
            -(datetime.fromisoformat(r["received_at"]).timestamp() if r.get("received_at") else 0),
        )

    actionable = [r for r in annotated if r["state"] in ("open", "claimed")]
    actionable.sort(key=_rank)

    # Run collapse (map §15.3): identical work on the SAME bound entity is one
    # operator obligation, not N rows. Collapse only entity-bound OPEN items
    # sharing (door, trip_id, channel, urgency) — the binding is what proves
    # identity; unbound or claimed items never collapse. The representative
    # (newest) carries group_count; collapsed members stay in every count
    # (counts remain actionable-work totals; count_basis stays the log).
    collapsed: Dict[str, Dict[str, Any]] = {}
    visible_actionable: List[Dict[str, Any]] = []
    for r in actionable:
        if r["state"] == "open" and r.get("trip_id"):
            key = f"{r.get('door')}|{r.get('trip_id')}|{r.get('channel') or ''}|{r.get('urgency')}"
            if key in collapsed:
                collapsed[key]["group_count"] += 1
                continue
            rep = dict(r)
            rep["group_count"] = 1
            collapsed[key] = rep
            visible_actionable.append(rep)
        else:
            visible_actionable.append(dict(r))

    visible = visible_actionable
    if include_done:
        done = [r for r in annotated if r["state"] in ("resolved", "dismissed")]
        done.sort(key=_rank)
        visible = visible_actionable + [dict(r) for r in done]
    counts: Dict[str, Dict[str, int]] = {
        "by_origin": {o: 0 for o in WORK_ORIGINS},
        "by_intent": {i: 0 for i in WORK_INTENTS},
        "by_urgency": {u: 0 for u in URGENCY_CLASSES},
        "by_state": {s: 0 for s in WORK_ITEM_STATES},
    }
    for r in actionable:
        if r.get("origin") in counts["by_origin"]:
            counts["by_origin"][r["origin"]] += 1
        if r.get("intent") in counts["by_intent"]:
            counts["by_intent"][r["intent"]] += 1
        if r.get("urgency") in counts["by_urgency"]:
            counts["by_urgency"][r["urgency"]] += 1
    for r in annotated:
        counts["by_state"][r["state"]] += 1
    duplicates = sum(1 for r in actionable if r.get("duplicate_of"))
    returning = sum(1 for r in actionable if r.get("returning_customer"))
    return {
        "items": visible[: max(1, limit)],
        "total": len(annotated),
        "actionable": len(actionable),
        "duplicates_flagged": duplicates,
        "returning_customers": returning,
        "counts": counts,
        "count_basis": "work_item_log_total",
    }
