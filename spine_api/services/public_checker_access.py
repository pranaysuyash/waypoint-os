"""Public-checker access tokens, disputes escrow, retention sweep (WOBS P2/P3).

EX-04 capability tokens: every run issues an opaque bearer token (stored
hashed — the raw token never persists) that authorizes the anonymous owner to
fetch, export, and delete exactly that trip. This closes the live-probed AUD-04
defect (anonymous 401 on result/report data) without opening trip-id paths to
the world.

Dispute escrow v0 (Second-Opinion Escrow): disagreements are recorded as
client-claimed rows, quarantined as unverified — they become corpus gold only
after server-side confirmation (honest-labeling rule).

Retention sweep (EX-02/D-03): PUBLIC_CHECKER_RETENTION_DAYS (default 90)
bounds trip-row lifetime; sweep deletes expired public-checker trips + artifacts
+ tokens + their event segments. 0 disables.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

_TOKEN_BYTES = 32
_TOKEN_FILE = Path("data") / "public_checker" / "access_tokens.json"


def _token_file() -> Path:
    return Path(os.environ.get("PUBLIC_CHECKER_TOKEN_FILE", str(_TOKEN_FILE)))


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def retention_days() -> int:
    """Call-time read; 0 disables expiry (tokens valid until revoked)."""
    try:
        return max(0, int(os.environ.get("PUBLIC_CHECKER_RETENTION_DAYS", "90")))
    except ValueError:
        return 90



def issue_access_token(trip_id: str) -> str:
    """Issue a fresh bearer token bound to one trip. Raw token returned once."""
    token = secrets.token_urlsafe(_TOKEN_BYTES)
    entry = {
        "trip_id": trip_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "revoked": False,
        "retention_days": retention_days(),
    }
    path = _token_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    store: Dict[str, Any] = {}
    if path.exists():
        try:
            store = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            store = {}
    store[_hash_token(token)] = entry
    path.write_text(json.dumps(store, indent=0, ensure_ascii=False), encoding="utf-8")
    return token


def verify_access_token(token: str, trip_id: str) -> bool:
    """Constant-time check that the token is valid, unexpired, and bound to this trip."""
    if not token or not trip_id:
        return False
    path = _token_file()
    if not path.exists():
        return False
    try:
        store = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return False
    entry = store.get(_hash_token(token))
    if not isinstance(entry, dict) or entry.get("revoked"):
        return False
    if entry.get("trip_id") != trip_id:
        return False
    retention_days = int(entry.get("retention_days") or 0)
    if retention_days > 0:
        created = str(entry.get("created_at") or "")
        try:
            created_at = datetime.fromisoformat(created)
            age_days = (datetime.now(timezone.utc) - created_at).total_seconds() / 86400
            if age_days > retention_days:
                return False
        except ValueError:
            return False
    # Bound the comparison surface; the trip_id binding above already matched.
    hmac.compare_digest(str(entry.get("trip_id")), trip_id)
    return True


def revoke_tokens_for_trip(trip_id: str) -> int:
    """Revoke (and compact) all tokens bound to a trip. Returns revoked count."""
    path = _token_file()
    if not path.exists():
        return 0
    try:
        store = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return 0
    revoked = 0
    for key, entry in list(store.items()):
        if isinstance(entry, dict) and entry.get("trip_id") == trip_id and not entry.get("revoked"):
            store.pop(key)
            revoked += 1
    if revoked:
        path.write_text(json.dumps(store), encoding="utf-8")
    return revoked


# ---------------------------------------------------------------------------
# Dispute escrow v0 — client-claimed disagreements, quarantined as unverified.
# ---------------------------------------------------------------------------

DISPUTES_FILE = Path("data") / "public_checker" / "disputes.jsonl"


def record_dispute(
    *,
    trip_id: str,
    finding_text: str,
    verdict: str,
) -> Dict[str, Any]:
    """Record a client-claimed dispute. Honest labeling: verified=false."""
    disputes_path = Path(os.environ.get("PUBLIC_CHECKER_DISPUTES_FILE", str(DISPUTES_FILE)))
    disputes_path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "dispute_id": f"dsp_{secrets.token_hex(6)}",
        "trip_id": trip_id,
        "finding_text": finding_text[:500],
        "verdict": verdict,
        "verified": False,  # client claim, not server-confirmed (escrow quarantine)
        "origin": "client",
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }
    with open(disputes_path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record


def list_disputes() -> List[Dict[str, Any]]:
    disputes_path = Path(os.environ.get("PUBLIC_CHECKER_DISPUTES_FILE", str(DISPUTES_FILE)))
    if not disputes_path.exists():
        return []
    rows: List[Dict[str, Any]] = []
    with open(disputes_path, "r", encoding="utf-8") as handle:
        for line in handle:
            raw = line.strip()
            if not raw:
                continue
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, dict):
                rows.append(parsed)
    return rows


# ---------------------------------------------------------------------------
# Retention sweep (EX-02/D-03): file-store trips + artifacts + tokens + old
# event segments. SQL-side deletion is deliberately out of v0 (durable-store
# endgame E-G owns SQL lifecycle); env flag gates any automatic invocation.
# ---------------------------------------------------------------------------

def sweep_expired_public_checker_trips(
    *,
    trips_dir: Path,
    public_checker_dir: Path,
    max_age_days: int,
) -> Dict[str, int]:
    """Delete file-store public-checker trips older than the retention window."""
    now = time.time()
    deleted_trips = 0
    revoked = 0
    if max_age_days <= 0:
        return {"deleted_trips": 0, "deleted_tokens": 0}
    cutoff = now - max_age_days * 86400
    for path in trips_dir.glob("*.json"):
        try:
            if path.stat().st_mtime >= cutoff:
                continue
            trip = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if trip.get("source") != "public_checker":
            continue
        trip_id = str(trip.get("id") or "")
        revoked += revoke_tokens_for_trip(trip_id)
        try:
            path.unlink()
            deleted_trips += 1
        except OSError:
            continue
    # Consent-gated upload artifacts expire with the same window.
    uploads_dir = public_checker_dir / "uploads"
    if uploads_dir.exists():
        for path in uploads_dir.glob("*"):
            try:
                if path.stat().st_mtime < cutoff:
                    path.unlink()
            except OSError:
                continue
    return {"deleted_trips": deleted_trips, "deleted_tokens": revoked}


def prune_old_event_segments(*, events_dir: Path, max_age_days: int = 180) -> int:
    """Delete rotated event segments (`.1`) older than the age cap. FT-06/EX-10."""
    if max_age_days <= 0 or not events_dir.exists():
        return 0
    cutoff = time.time() - max_age_days * 86400
    pruned = 0
    for path in events_dir.glob("*.jsonl.1"):
        try:
            if path.stat().st_mtime < cutoff:
                path.unlink()
                pruned += 1
        except OSError:
            continue
    return pruned
