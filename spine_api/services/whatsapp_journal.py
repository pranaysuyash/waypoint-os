"""Single-host journal for Meta inbox messages, ownership and dispatch attempts."""

from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from time import time
from uuid import uuid4

from spine_api.services.message_store import messages_dir
from src.security.encryption import blind_index, decrypt_strict, encrypt, key_fingerprint

SERVICE_WINDOW_SECONDS = 24 * 60 * 60
ATTEMPT_REVIEW_SECONDS = 120
DELIVERY_ORDER = {"sent": 1, "failed": 2, "delivered": 3, "read": 4}

SCHEMA = """
CREATE TABLE IF NOT EXISTS whatsapp_conversations (
    id TEXT PRIMARY KEY, agency_id TEXT NOT NULL, inbox_id TEXT NOT NULL,
    traveler TEXT NOT NULL, traveler_key TEXT NOT NULL, staff_id TEXT, ownership_updated_at INTEGER,
    ownership_revision INTEGER NOT NULL DEFAULT 0,
    UNIQUE (agency_id, inbox_id, traveler_key)
);
CREATE TABLE IF NOT EXISTS whatsapp_journal_key (id INTEGER PRIMARY KEY CHECK (id=1), fingerprint TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS whatsapp_events (
    id TEXT PRIMARY KEY, agency_id TEXT NOT NULL, inbox_id TEXT NOT NULL,
    conversation_id TEXT NOT NULL REFERENCES whatsapp_conversations(id),
    provider_id TEXT NOT NULL, body TEXT NOT NULL, occurred_at INTEGER,
    received_at INTEGER NOT NULL, display_phone TEXT NOT NULL, mime TEXT, filename TEXT,
    processing_state TEXT NOT NULL, trip_id TEXT,
    UNIQUE (agency_id, inbox_id, provider_id)
);
CREATE TABLE IF NOT EXISTS whatsapp_replies (
    id TEXT PRIMARY KEY, conversation_id TEXT NOT NULL REFERENCES whatsapp_conversations(id),
    inbound_id TEXT REFERENCES whatsapp_events(id), staff_request_id TEXT,
    body TEXT NOT NULL, state TEXT NOT NULL, created_at INTEGER NOT NULL,
    started_at INTEGER, actor_id TEXT, provider_id TEXT, delivery_status TEXT,
    delivery_detail TEXT, dispatch_detail TEXT,
    UNIQUE (inbound_id), UNIQUE (conversation_id, staff_request_id)
);
CREATE INDEX IF NOT EXISTS whatsapp_events_conversation ON whatsapp_events(conversation_id, received_at);
CREATE INDEX IF NOT EXISTS whatsapp_replies_conversation ON whatsapp_replies(conversation_id, created_at);
CREATE INDEX IF NOT EXISTS whatsapp_replies_provider ON whatsapp_replies(provider_id);
"""


class JournalConflict(Exception):
    """An operator action cannot be applied to the current conversation state."""


def _connect(*, create: bool = True):
    path = messages_dir() / "whatsapp.sqlite3"
    if not create and not path.is_file():
        return None
    if create:
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError:
            pass
        else:
            os.close(fd)
    conn = sqlite3.connect(path, timeout=10)
    try:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        if create:
            conn.executescript(SCHEMA)
            conn.execute("INSERT OR IGNORE INTO whatsapp_journal_key VALUES (1, ?)", (key_fingerprint(),))
            conn.commit()
        fingerprint = conn.execute("SELECT fingerprint FROM whatsapp_journal_key WHERE id=1").fetchone()
        if not fingerprint or fingerprint[0] != key_fingerprint():
            raise RuntimeError("WhatsApp journal requires its original Waypoint encryption key")
        return conn
    except Exception:
        conn.close()
        raise


@contextmanager
def _transaction():
    conn = _connect()
    try:
        conn.execute("BEGIN IMMEDIATE")
        yield conn
        conn.commit()
    finally:
        conn.close()


def bound_inbox(agency_id: str) -> str | None:
    if os.getenv("WAYPOINT_WHATSAPP_MANAGED_ENABLED") != "1":
        return None
    inbox = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "").strip()
    agency = os.getenv("MESSAGING_WEBHOOK_AGENCY_ID", "").strip()
    required = ("ENCRYPTION_KEY", "WHATSAPP_APP_SECRET", "WHATSAPP_VERIFY_TOKEN")
    configured = all(os.getenv(name, "").strip() for name in required)
    return inbox if configured and inbox.isascii() and inbox.isdecimal() and agency and agency == agency_id else None


def claim_event(agency_id: str, inbox_id: str, event: dict) -> dict | None:
    now = int(time())
    traveler_key = blind_index(f"whatsapp-traveler:{agency_id}:{inbox_id}", event["traveler"])
    with _transaction() as conn:
        if conn.execute(
            "SELECT 1 FROM whatsapp_events WHERE agency_id=? AND inbox_id=? AND provider_id=?",
            (agency_id, inbox_id, event["provider_id"]),
        ).fetchone():
            return None
        conn.execute(
            "INSERT INTO whatsapp_conversations (id, agency_id, inbox_id, traveler, traveler_key) VALUES (?, ?, ?, ?, ?) "
            "ON CONFLICT (agency_id, inbox_id, traveler_key) DO NOTHING",
            (f"wa_{uuid4().hex}", agency_id, inbox_id, encrypt(event["traveler"]), traveler_key),
        )
        conversation = conn.execute(
            "SELECT id, agency_id, staff_id, ownership_revision FROM whatsapp_conversations "
            "WHERE agency_id=? AND inbox_id=? AND traveler_key=?",
            (agency_id, inbox_id, traveler_key),
        ).fetchone()
        process = not conn.execute(
            "SELECT 1 FROM whatsapp_events WHERE conversation_id=? AND processing_state='processing' LIMIT 1",
            (conversation["id"],),
        ).fetchone()
        event_id = f"msg_{uuid4().hex}"
        conn.execute(
            """INSERT INTO whatsapp_events (id, agency_id, inbox_id, conversation_id, provider_id,
                body, occurred_at, received_at, display_phone, mime, filename, processing_state)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (event_id, agency_id, inbox_id, conversation["id"], event["provider_id"],
             encrypt(event["body"]), event["occurred_at"], now, encrypt(event["display_phone"]),
             event["mime"], encrypt(event["filename"]),
             "processing" if process else "review_required"),
        )
        return {**dict(conversation), "event_id": event_id, "process": process}


def finish_event(claim: dict, *, trip_id: str | None, draft: str | None, review: bool = False):
    with _transaction() as conn:
        owner = conn.execute(
            "SELECT staff_id, ownership_revision FROM whatsapp_conversations WHERE id=?", (claim["id"],)
        ).fetchone()
        # A takeover and release during extraction still invalidate the old draft.
        suppressed = owner["staff_id"] is not None or owner["ownership_revision"] != claim["ownership_revision"]
        conn.execute(
            "UPDATE whatsapp_events SET trip_id=?, processing_state=? WHERE id=?",
            (trip_id, "review_required" if review else "processed", claim["event_id"]),
        )
        if draft and not review:
            conn.execute(
                "INSERT INTO whatsapp_replies (id, conversation_id, inbound_id, body, state, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (f"msg_{uuid4().hex}", claim["id"], claim["event_id"], encrypt(draft),
                 "SUPPRESSED" if suppressed else "QUEUED", int(time())),
            )


def _conversation(conn, agency_id: str, conversation_id: str):
    conversation = conn.execute(
        "SELECT * FROM whatsapp_conversations WHERE agency_id=? AND id=?", (agency_id, conversation_id)
    ).fetchone()
    if conversation is None:
        raise LookupError(conversation_id)
    return conversation


def _visible_state(row: dict) -> dict:
    if row.get("state") == "SENDING" and time() - row["started_at"] >= ATTEMPT_REVIEW_SECONDS:
        row["state"] = "DELIVERY_UNKNOWN"
    if row.get("processing_state") == "processing" and time() - row["received_at"] >= ATTEMPT_REVIEW_SECONDS:
        row["processing_state"] = "review_required"
    if "body" in row:
        row["body"] = decrypt_strict(row["body"])
    return row


def conversation_view(agency_id: str, conversation_id: str) -> dict:
    conn = _connect(create=False)
    if conn is None:
        raise LookupError(conversation_id)
    try:
        conversation = dict(_conversation(conn, agency_id, conversation_id))
        conversation.pop("traveler_key")
        conversation["traveler"] = decrypt_strict(conversation["traveler"])
        replies = conn.execute(
            "SELECT * FROM whatsapp_replies WHERE conversation_id=? ORDER BY created_at DESC, rowid DESC LIMIT 100",
            (conversation_id,),
        ).fetchall()
        return {**conversation, "replies": [_visible_state(dict(row)) for row in replies]}
    finally:
        conn.close()


def set_ownership(agency_id: str, conversation_id: str, actor_id: str, *, takeover: bool) -> dict:
    with _transaction() as conn:
        _conversation(conn, agency_id, conversation_id)
        conn.execute(
            "UPDATE whatsapp_conversations SET staff_id=?, "
            "ownership_updated_at=?, ownership_revision=ownership_revision+1 WHERE id=?",
            (actor_id if takeover else None, int(time()), conversation_id),
        )
        if takeover:
            conn.execute(
                "UPDATE whatsapp_replies SET state='SUPPRESSED' WHERE conversation_id=? AND state='QUEUED' "
                "AND inbound_id IS NOT NULL",
                (conversation_id,),
            )
    return conversation_view(agency_id, conversation_id)


def prepare_dispatch(
    agency_id: str, conversation_id: str, actor_id: str, *, reply_id: str | None = None,
    staff_request_id: str | None = None, body: str | None = None,
) -> tuple[dict, bool]:
    """Serialize provider attempt authorization with takeover, then release the database lock."""
    with _transaction() as conn:
        conversation = _conversation(conn, agency_id, conversation_id)
        if staff_request_id is not None:
            if conversation["staff_id"] != actor_id:
                raise JournalConflict("Take over the conversation before sending a staff reply")
            conn.execute(
                "INSERT INTO whatsapp_replies (id, conversation_id, staff_request_id, body, state, created_at) "
                "VALUES (?, ?, ?, ?, 'QUEUED', ?) ON CONFLICT (conversation_id, staff_request_id) DO NOTHING",
                (f"msg_{uuid4().hex}", conversation_id, staff_request_id, encrypt(body), int(time())),
            )
            reply = conn.execute(
                "SELECT * FROM whatsapp_replies WHERE conversation_id=? AND staff_request_id=?",
                (conversation_id, staff_request_id),
            ).fetchone()
            if decrypt_strict(reply["body"]) != body or (reply["actor_id"] and reply["actor_id"] != actor_id):
                raise JournalConflict("Reply request ID has already been used")
        else:
            reply = conn.execute(
                "SELECT * FROM whatsapp_replies WHERE id=? AND conversation_id=? AND inbound_id IS NOT NULL",
                (reply_id, conversation_id),
            ).fetchone()
        if reply is None:
            raise LookupError(reply_id)
        result = _visible_state(dict(reply))
        result.update(inbox_id=conversation["inbox_id"], traveler=decrypt_strict(conversation["traveler"]))
        if reply["state"] != "QUEUED":
            return result, False
        if reply["inbound_id"] and conversation["staff_id"]:
            conn.execute("UPDATE whatsapp_replies SET state='SUPPRESSED' WHERE id=?", (reply["id"],))
            return {**result, "state": "SUPPRESSED"}, False
        last_inbound = conn.execute(
            "SELECT MAX(occurred_at) AS latest FROM whatsapp_events WHERE conversation_id=?", (conversation_id,)
        ).fetchone()["latest"]
        now = int(time())
        if last_inbound is None or not 0 <= now - last_inbound < SERVICE_WINDOW_SECONDS:
            raise JournalConflict("Free-form reply requires a verified inbound message in the last 24 hours")
        if bound_inbox(agency_id) != conversation["inbox_id"]:
            raise JournalConflict("The original WhatsApp inbox is not configured for this agency")
        conn.execute(
            "UPDATE whatsapp_replies SET state='SENDING', started_at=?, actor_id=? WHERE id=?",
            (now, actor_id, reply["id"]),
        )
        return {**result, "state": "SENDING", "started_at": now, "actor_id": actor_id}, True


def finish_dispatch(reply_id: str, result: dict) -> dict:
    with _transaction() as conn:
        conn.execute(
            "UPDATE whatsapp_replies SET state=?, provider_id=?, dispatch_detail=? WHERE id=? AND state='SENDING'",
            (result["dispatch_status"], result.get("provider_message_id"), result["detail"], reply_id),
        )
        return _visible_state(dict(conn.execute("SELECT * FROM whatsapp_replies WHERE id=?", (reply_id,)).fetchone()))


def apply_status(agency_id: str, inbox_id: str, status: dict) -> bool:
    delivery = status["status"].lower()
    if delivery not in DELIVERY_ORDER:
        return False
    with _transaction() as conn:
        reply = conn.execute(
            """SELECT r.* FROM whatsapp_replies r JOIN whatsapp_conversations c ON c.id=r.conversation_id
            WHERE c.agency_id=? AND c.inbox_id=? AND r.started_at IS NOT NULL
            AND (r.provider_id=? OR (r.id=? AND r.provider_id IS NULL AND r.state IN ('SENDING','DELIVERY_UNKNOWN')))""",
            (agency_id, inbox_id, status["provider_message_id"], status.get("callback_id")),
        ).fetchone()
        if reply is None:
            return False
        if DELIVERY_ORDER[delivery] > DELIVERY_ORDER.get(reply["delivery_status"], 0):
            conn.execute(
                "UPDATE whatsapp_replies SET provider_id=?, state='SENT', delivery_status=?, delivery_detail=? WHERE id=?",
                (status["provider_message_id"], delivery, status.get("error"), reply["id"]),
            )
        return True


def agency_messages(agency_id: str, trip_id: str | None, limit: int) -> list[dict]:
    """Project Meta inbox and reply rows through the existing message feed."""
    conn = _connect(create=False)
    if conn is None:
        return []
    try:
        return _agency_messages(conn, agency_id, trip_id, limit)
    finally:
        conn.close()


def _agency_messages(conn, agency_id: str, trip_id: str | None, limit: int) -> list[dict]:
    events = conn.execute(
        """SELECT e.*, c.traveler, c.staff_id FROM whatsapp_events e
        JOIN whatsapp_conversations c ON c.id=e.conversation_id
        WHERE e.agency_id=? AND (? IS NULL OR e.trip_id=?) ORDER BY e.received_at DESC, e.rowid DESC LIMIT ?""",
        (agency_id, trip_id, trip_id, limit),
    ).fetchall()
    replies = conn.execute(
        """SELECT r.*, c.traveler, c.staff_id, e.provider_id AS reply_to, e.display_phone, e.trip_id
        FROM whatsapp_replies r JOIN whatsapp_conversations c ON c.id=r.conversation_id
        LEFT JOIN whatsapp_events e ON e.id=COALESCE(r.inbound_id, (
            SELECT id FROM whatsapp_events WHERE conversation_id=c.id ORDER BY received_at DESC, rowid DESC LIMIT 1
        )) WHERE c.agency_id=? AND (? IS NULL OR e.trip_id=?) ORDER BY r.created_at DESC, r.rowid DESC LIMIT ?""",
        (agency_id, trip_id, trip_id, limit),
    ).fetchall()
    messages = []
    for raw in [*events, *replies]:
        row = _visible_state(dict(raw))
        inbound = "processing_state" in row
        traveler = decrypt_strict(row["traveler"])
        display_phone = decrypt_strict(row["display_phone"])
        messages.append({
            "message_id": row["id"], "agency_id": agency_id, "channel": "whatsapp",
            "direction": "inbound" if inbound else "outbound", "body": row["body"],
            "from_party": traveler if inbound else display_phone,
            "to_party": display_phone if inbound else traveler,
            "trip_id": row["trip_id"], "provider_message_id": row["provider_id"],
            "reply_to_provider_message_id": row.get("reply_to"), "mime": row.get("mime"),
            "filename": decrypt_strict(row.get("filename")), "conversation_id": row["conversation_id"],
            "conversation_owner": "staff" if row["staff_id"] else "assistant",
            "processing_state": row.get("processing_state"), "dispatch_status": row.get("state"),
            "delivery_status": row.get("delivery_status"), "delivery_detail": row.get("delivery_detail"),
            "received_at": datetime.fromtimestamp(row.get("received_at", row.get("created_at")), timezone.utc).isoformat(),
        })
    return messages
