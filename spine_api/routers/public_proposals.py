"""
spine_api.routers.public_proposals — Public client-facing proposal co-creation endpoints.

Allows travelers to:
- View interactive proposals via secure public tokens (/p/{token})
- Select options (room upgrades, excursions, transfer options) with real-time recalculation
- Accept and e-sign proposals with audit logging

Capability credential lifecycle (FND-0219): a public proposal token is a
capability URL — a real credential. Issuance, TTL, and revocation are durable
in the SQL-backed ``ProposalTokenStore``
(spine_api/services/proposal_token_store.py, table ``proposal_access_tokens``,
alembic ``add_proposal_access_tokens``), which stores only SHA-256 token
hashes plus a short lookup prefix — never raw token material. The in-process
``_PROPOSAL_VIEW_CACHE`` below is a strictly bounded, expiring projection
cache only: it NEVER participates in authorization (every request verifies
the credential first).

Token wire formats:
- ``propv3_<urlsafe>`` (current): opaque 256-bit material via
  ``secrets.token_urlsafe(32)``; all binding (agency/trip/proposal/TTL/
  consent) lives in the durable row.
- ``prop_{trip}_{agency}_{exp}_{hmac}`` (legacy v2, still verified): signed
  and TTL'd inline; revocation via the file-backed store below.
- Pre-hardening 16-hex tokens: fail closed (only the explicit demo
  allowlist resolves, and only when PUBLIC_PROPOSAL_DEMO_MODE=1). No silent
  upgrade — honest errors.

Revocation durability boundary (PT-05 / N-07): v2 revocations are durable on
ONE host — a JSON file behind an OS lock (hash-keyed since FND-0219: the file
no longer stores raw token material), reloaded before every verification.
v3 revocations are durable in SQL (multi-replica safe). Multi-replica
deployments should issue v3 credentials; see .env.example.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import math
import os
import threading
import time
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional

try:
    import fcntl
except ImportError:  # pragma: no cover - Windows has no fcntl; DB is required there.
    fcntl = None

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

try:
    from spine_api import persistence
except (ImportError, ValueError):
    import persistence

try:
    from spine_api.services.proposal_token_store import (
        V3_TOKEN_PREFIX,
        ProposalTokenStore,
        TokenStatus,
        hash_token,
        new_token_material,
    )
except (ImportError, ValueError):
    from services.proposal_token_store import (
        V3_TOKEN_PREFIX,
        ProposalTokenStore,
        TokenStatus,
        hash_token,
        new_token_material,
    )

try:
    from spine_api.core.env import load_project_env
except (ImportError, ValueError):
    from core.env import load_project_env

AuditStore = persistence.AuditStore
TripStore = persistence.TripStore

logger = logging.getLogger("spine_api.public_proposals")
router = APIRouter(prefix="/api/public/proposals", tags=["public-proposals"])


class ProposalOption(BaseModel):
    id: str
    category: str  # "accommodation" | "transport" | "activity" | "insurance"
    name: str
    description: str
    price_delta_usd: float = 0.0
    selected: bool = False
    is_default: bool = False


class ProposalDay(BaseModel):
    day_number: int
    title: str
    location: str
    description: str
    highlights: List[str] = Field(default_factory=list)
    options: List[ProposalOption] = Field(default_factory=list)


class PublicProposalView(BaseModel):
    token: str
    trip_id: str
    title: str
    destination: str
    duration_days: int
    traveler_name: str
    base_price_usd: float
    selected_total_price_usd: float
    currency: str = "USD"
    status: str = "open"  # "open" | "accepted" | "expired"
    accepted_at: Optional[str] = None
    accepted_by: Optional[str] = None
    days: List[ProposalDay] = Field(default_factory=list)
    available_options: List[ProposalOption] = Field(default_factory=list)
    # Part-H P1 (2026-09-07): travelers must be able to tell a persisted,
    # observed quote from the explicitly gated demo fixture. The frontend
    # badges ``demo``; "persisted_observed" marks real agency data.
    reality_tier: Optional[str] = None


class UpdateOptionsRequest(BaseModel):
    selected_option_ids: List[str]


class AcceptProposalRequest(BaseModel):
    signer_name: str
    signer_email: str
    selected_option_ids: List[str] = Field(default_factory=list)
    e_signature_consent: bool


class _ProposalViewCache:
    """Bounded, expiring in-process cache of projected ``PublicProposalView``s.

    FND-0219: replaces the former unbounded ``_PROPOSAL_REGISTRY`` dict. Two
    hard bounds and one scoping rule:

    - Size: at most ``max_entries`` rows (oldest evicted first; default 4096).
    - Time: every row expires after ``ttl_seconds`` (default 3600) — the view
      is always re-derivable from the durable trip store / durable token row,
      so a short TTL only trades a rebuild for staleness.
    - Scope: this cache is a projection cache ONLY. It is never consulted for
      authorization — every request verifies the credential (signature /
      store row TTL / revocation) before a cached view may be returned, and
      ``revoke_proposal_token`` evicts the entry so a revoked credential's
      view cannot linger.
    """

    __slots__ = ("_entries", "_lock", "_max_entries", "_ttl_seconds")

    def __init__(self, max_entries: int = 4096, ttl_seconds: int = 3600) -> None:
        self._max_entries = max_entries
        self._ttl_seconds = ttl_seconds
        self._entries: "Dict[str, tuple[PublicProposalView, float]]" = {}
        self._lock = threading.Lock()

    def _purge_expired_locked(self, now: float) -> None:
        expired = [key for key, (_view, expires) in self._entries.items() if expires <= now]
        for key in expired:
            del self._entries[key]

    def set(self, token: str, view: PublicProposalView) -> None:
        now = time.monotonic()
        with self._lock:
            self._purge_expired_locked(now)
            if token not in self._entries and len(self._entries) >= self._max_entries:
                # FIFO eviction: dict preserves insertion order, so the first
                # key is the oldest. Recaching a token refreshes its position.
                oldest = next(iter(self._entries))
                del self._entries[oldest]
            self._entries[token] = (view, now + self._ttl_seconds)

    def get(self, token: str) -> Optional[PublicProposalView]:
        now = time.monotonic()
        with self._lock:
            entry = self._entries.get(token)
            if entry is None:
                return None
            view, expires = entry
            if expires <= now:
                del self._entries[token]
                return None
            return view

    def contains(self, token: str) -> bool:
        return self.get(token) is not None

    def pop(self, token: str) -> None:
        with self._lock:
            self._entries.pop(token, None)

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()


# Bounded projection cache (FND-0219). Authorization never consults this.
_PROPOSAL_VIEW_CACHE = _ProposalViewCache()


# ---------------------------------------------------------------------------
# PT-01 (S-01): signing key is required — no committed fallback.
# Mirrors spine_api/core/database.py (A-18): a hardcoded default would let
# anyone forge capability tokens for any trip id on any deployment that
# forgot to set the env var. Fail loudly at import instead.
# ---------------------------------------------------------------------------
load_project_env()


def _require_signing_key() -> str:
    value = (os.getenv("PROPOSAL_SIGNING_KEY") or "").strip()
    known_defaults = {
        "waypoint_secret_proposal_key_2026",
        "change-me-to-a-random-secret",
        "secret",
        "changeme",
        "password",
        "default",
        "test",
        "dev",
    }
    if not value:
        raise RuntimeError(
            "PROPOSAL_SIGNING_KEY is not set. Proposal capability tokens are "
            "signed with this secret, so shipping a default would let anyone "
            "forge tokens for arbitrary trips. Provide it via the environment "
            "or .env (see .env.example). Local test runs: "
            "scripts/run_backend_tests.sh sets a dev-only value for you."
        )
    if value.lower() in known_defaults or len(value) < 32:
        raise RuntimeError(
            "PROPOSAL_SIGNING_KEY is too weak or is a known placeholder. "
            "Use a randomly generated secret of at least 32 characters."
        )
    return value


_SECRET_KEY = _require_signing_key()

# ---------------------------------------------------------------------------
# PT-02 (S-02): the old "len(token) >= 16 → legacy_ok" heuristic accepted any
# attacker-supplied junk string and resolved it to the demo proposal. The only
# legacy tokens that must keep working are the exact demo strings below, so
# they are allowlisted explicitly (each entry names why it exists).
# ---------------------------------------------------------------------------
_DEMO_TOKEN_ALLOWLIST = frozenset(
    {
        # Seeded demo proposal used by the public proposal page and
        # tests/test_public_proposals.py::test_get_public_proposal_by_token.
        "prop_demo_italy_123",
        # Option-recalculation demo (tests/test_public_proposals.py::test_calculate_proposal_options).
        "prop_calc_test_456",
        # E-sign acceptance demo (tests/test_public_proposals.py::test_accept_proposal_success_and_validation).
        "prop_accept_test_789",
    }
)
_DEMO_LEGACY_TRIP_ID = "trip_legacy"

# ---------------------------------------------------------------------------
# PT-05 (S-11a): durable revocation store.
# Revocation is a trust control, so it must survive restarts. The registry
# above is in-memory only, so revocations are persisted to a JSON file the
# same way FileTripStore persists trips (data/ directory, atomic replace).
#
# Durability boundary (honest): single-host durability. Restart-safe and
# worker-safe on one machine; multi-replica deployments must point
# PROPOSAL_REVOCATIONS_PATH at a shared volume (or promote revocations to
# PostgreSQL alongside the SQL trip store). The registry row status set in
# revoke_proposal_token is process-local sugar only — verification trusts the
# file-backed store, which is reloaded from disk.
# ---------------------------------------------------------------------------
_REVOCATIONS_PATH = Path(
    os.environ.get(
        "PROPOSAL_REVOCATIONS_PATH",
        # Repo-root data/ (same convention as the FileTripStore's data/ dir) so
        # ops can find revocations next to the other durable stores — NOT
        # inside the package tree (review finding, 2026-09-02).
        str(Path(__file__).resolve().parents[2] / "data" / "proposals" / "revoked_tokens.json"),
    )
)
# token_hash (SHA-256 hex) -> ISO-8601 revocation timestamp (dict, not set, so
# the file is self-describing and audit-friendly). FND-0219: keys are HASHES —
# the file never stores raw capability material. Legacy files that keyed by
# raw token are normalized on load (re-keyed by hashing) so prior revocations
# keep working without any silent re-issue.
_REVOKED_TOKENS: Dict[str, str] = {}
_revocations_lock = threading.Lock()


def _normalize_revocation_key(key: str) -> str:
    """Return the hash key for a stored revocation entry.

    Entries written since FND-0219 are already 64-hex SHA-256 digests; legacy
    raw-token keys are hashed on load (one-way — the raw value is dropped,
    never persisted again).
    """
    if len(key) == 64 and all(char in "0123456789abcdef" for char in key):
        return key
    return hash_token(key)[0]


def _load_revocations() -> bool:
    # A replace() writer never leaves a partially written JSON file, so reads
    # do not need to hold the writer lock. Reloading on every verification is
    # intentional: another worker may have revoked this token since import.
    try:
        if not _REVOCATIONS_PATH.exists():
            return True
    except OSError as exc:
        logger.error("Failed to inspect proposal revocations at %s: %s", _REVOCATIONS_PATH, exc)
        return False
    try:
        raw = json.loads(_REVOCATIONS_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        logger.error("Failed to load proposal revocations from %s: %s", _REVOCATIONS_PATH, exc)
        return False
    if not isinstance(raw, dict):
        logger.error("Proposal revocation store %s is not a JSON object", _REVOCATIONS_PATH)
        return False
    with _revocations_lock:
        _REVOKED_TOKENS.update(
            {_normalize_revocation_key(str(k)): str(v) for k, v in raw.items()}
        )
    return True


@contextmanager
def _revocation_file_lock():
    """Serialize revocation read/merge/write across local worker processes.

    The file remains a deliberately bounded single-host backend. Deployments
    with multiple replicas must provide a shared volume with locking semantics
    or use the planned PostgreSQL revocation table instead.
    """
    lock_path = _REVOCATIONS_PATH.with_name(_REVOCATIONS_PATH.name + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+", encoding="utf-8") as lock_file:
        if fcntl is not None:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            if fcntl is not None:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def _persist_revocations_locked() -> bool:
    """Atomically persist revocations. Caller must hold ``_revocations_lock``.

    The latest on-disk map is merged while holding an OS lock before replacing
    the file. This avoids lost updates when two local workers revoke different
    tokens concurrently.
    """
    try:
        with _revocation_file_lock():
            persisted: Dict[str, str] = {}
            if _REVOCATIONS_PATH.exists():
                try:
                    raw = json.loads(_REVOCATIONS_PATH.read_text(encoding="utf-8"))
                except (OSError, ValueError) as exc:
                    logger.error("Failed to merge proposal revocations from %s: %s", _REVOCATIONS_PATH, exc)
                    return False
                if not isinstance(raw, dict):
                    logger.error("Proposal revocation store %s is not a JSON object", _REVOCATIONS_PATH)
                    return False
                # Normalize (hash) any legacy raw-token keys during merge so
                # raw credential material leaves the durable file at the next
                # write; revocation timestamps are preserved.
                persisted = {
                    _normalize_revocation_key(str(k)): str(v) for k, v in raw.items()
                }
            persisted.update(_REVOKED_TOKENS)
            tmp_path = _REVOCATIONS_PATH.with_name(
                f"{_REVOCATIONS_PATH.name}.{os.getpid()}.tmp"
            )
            tmp_path.write_text(json.dumps(persisted, indent=2, sort_keys=True), encoding="utf-8")
            os.replace(tmp_path, _REVOCATIONS_PATH)
            _REVOKED_TOKENS.update(persisted)
            return True
    except OSError as exc:
        # Keep the in-memory revocation effective, but report that durable
        # confirmation failed so callers can retry or fail closed.
        logger.error("Failed to persist proposal revocations to %s: %s", _REVOCATIONS_PATH, exc)
        return False


_load_revocations()

# ---------------------------------------------------------------------------
# PT-03/PT-04 (S-03): token format v2 embeds the issuing agency.
#   prop_{trip_id}_{agency_field}_{exp_ts}_{sig}
# agency_field carries the agency_id (UUID or slug) escaped by
# _encode_agency_field below so the '_' field delimiter stays unambiguous even
# after HTTP percent-decoding. The HMAC payload is rebuilt from the token's own
# agency field, so verification never guesses the issuing agency (the old
# hardcoded ["system", "default", ...] fallback list — which embedded the
# shared test-agency UUID — is gone).
# ---------------------------------------------------------------------------
_TOKEN_PREFIX = "prop_"

# agency_field codec: escaping charset. Anything outside [A-Za-z0-9-] is
# escaped; '~' itself is escaped as '~~' to keep the codec injective.
_AGENCY_FIELD_SAFE = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-"
)


def _encode_agency_field(agency_id: str) -> str:
    """Encode an agency id into a delimiter-safe, percent-decode-stable token
    field.

    Output alphabet is [A-Za-z0-9~-]: it contains no '_' (the token's field
    delimiter, so the trip_id/agency_id boundary stays unambiguous) and no '%'
    (the percent-decoding trigger, so HTTP intermediaries that normalize
    percent-escapes in path segments cannot alter the value). 'urllib.parse.
    quote(safe='')' was tried first but is NOT decode-stable: its always-safe
    set leaves '_' raw, and substituting '%5F' gets decoded back to '_' by
    conformant path decoding (RFC 3986 unreserved characters), which corrupts
    the field boundary in transit.
    """
    out: List[str] = []
    for byte in agency_id.encode("utf-8"):
        char = chr(byte)
        if char in _AGENCY_FIELD_SAFE:
            out.append(char)
        elif char == "~":
            out.append("~~")
        else:
            out.append(f"~{byte:02X}")
    return "".join(out)


def _decode_agency_field(field: str) -> str:
    """Exact inverse of _encode_agency_field."""
    out = bytearray()
    i = 0
    length = len(field)
    while i < length:
        char = field[i]
        if char != "~":
            out.append(ord(char))
            i += 1
            continue
        if i + 1 < length and field[i + 1] == "~":
            out.append(0x7E)
            i += 2
        elif i + 2 < length:
            out.append(int(field[i + 1 : i + 3], 16))
            i += 3
        else:
            raise ValueError("Truncated agency field escape")
    return out.decode("utf-8")


def generate_signed_proposal_token(
    trip_id: str,
    agency_id: str = "system",
    ttl_hours: int = 168,  # 7 days default TTL
) -> str:
    """Generate a tamper-evident, cryptographically signed capability token with TTL."""
    if not trip_id or not isinstance(trip_id, str):
        raise ValueError("trip_id must be a non-empty string")
    if not agency_id or not isinstance(agency_id, str):
        raise ValueError("agency_id must be a non-empty string")
    exp_ts = int((datetime.now(timezone.utc) + timedelta(hours=ttl_hours)).timestamp())
    agency_field = _encode_agency_field(agency_id)
    # The HMAC payload carries the RAW agency id; the token carries the encoded
    # form. _decode_agency_field(_encode_agency_field(a)) == a, and the encoded
    # form is unchanged by HTTP percent-decoding, so verification is canonical
    # over both direct and wire-transit paths.
    payload = f"{trip_id}:{agency_id}:{exp_ts}"
    # PT-06 (S-11b): full SHA-256 hex digest (256-bit) — the previous
    # hexdigest()[:16] truncation gave only 64 bits of signature.
    signature = hmac.new(_SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f"prop_{trip_id}_{agency_field}_{exp_ts}_{signature}"


def _store() -> ProposalTokenStore:
    return ProposalTokenStore.get_instance()


def issue_proposal_capability(
    trip_id: str,
    agency_id: str,
    consented_by: str,
    purpose: str = "proposal_share",
    proposal_id: Optional[str] = None,
    ttl_hours: Optional[int] = None,
) -> tuple[str, "object"]:
    """Issue a durable v3 capability credential and record its consent artifact.

    FND-0219 issuance path: mints opaque ``secrets.token_urlsafe(32)`` material
    (256-bit, URL-safe, nothing about the trip leaked in the URL), then records
    the durable row — sha256 hash + lookup prefix (never raw material),
    agency/trip/proposal binding, TTL, and the consent artifact naming the
    authenticated principal who authorized external sharing.

    Must only be called from agency-authenticated contexts. Replay is
    idempotent per credential: re-registering identical material returns the
    stored row unchanged (no TTL or consent refresh).
    """
    if not trip_id or not isinstance(trip_id, str):
        raise ValueError("trip_id must be a non-empty string")
    if not agency_id or not isinstance(agency_id, str):
        raise ValueError("agency_id must be a non-empty string")
    if not consented_by or not isinstance(consented_by, str):
        raise ValueError(
            "consented_by is required: external sharing must be attributable "
            "to the authenticated principal who authorized it"
        )
    token = new_token_material()
    _created, record = _store().issue(
        token=token,
        format_version="v3",
        agency_id=agency_id,
        trip_id=trip_id,
        proposal_id=proposal_id,
        ttl_hours=ttl_hours,
        consented_by=consented_by,
        purpose=purpose,
    )
    return token, record


def verify_proposal_token(token: str) -> tuple[bool, str, Optional[str]]:
    """
    Verify capability token (v3 store-backed or legacy v2 signed), TTL, and
    revocation status.
    Returns: (is_valid, reason, trip_id)
    """
    # Revocations may be written by another worker after this process starts.
    # Refresh before consulting the cache so restart/worker durability is also
    # a live authorization property, not just a file-on-disk claim.
    if not _load_revocations():
        return False, "Proposal revocation store is unavailable", None

    # FND-0219: the file store is hash-keyed — compare against the hash of the
    # presented token, never against the raw value.
    token_hash, _prefix = hash_token(token)
    if token_hash in _REVOKED_TOKENS:
        return False, "Token has been revoked by travel advisor", None

    # --- v3 opaque credential: the durable store row is authoritative -------
    if token.startswith(V3_TOKEN_PREFIX):
        try:
            credential_status, record = _store().verify(token)
        except Exception as exc:  # store outage must fail closed, not open
            logger.error("Proposal token store unavailable during verification: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Proposal verification temporarily unavailable",
            ) from exc
        if credential_status == TokenStatus.VALID and record is not None:
            # Resource binding comes from the durable row — a credential only
            # ever resolves to the trip it was issued for.
            return True, "valid", record.trip_id
        # FND-0219, no-oracle rule: expired, revoked, and unknown credentials
        # are indistinguishable on the public surface (same reason string, so
        # the HTTP layer emits the same 410 + detail for every failure).
        # Operators read the truth from the store row / logs, never from the
        # traveler response.
        return False, "Proposal link is no longer available", None

    if token in _DEMO_TOKEN_ALLOWLIST:
        return True, "legacy_ok", _DEMO_LEGACY_TRIP_ID

    if not token.startswith(_TOKEN_PREFIX):
        return False, "Malformed proposal token", None

    body = token[len(_TOKEN_PREFIX):]
    parts = body.rsplit("_", 2)
    if len(parts) != 3:
        return False, "Malformed proposal token", None

    head, _, agency_field = parts[0].rpartition("_")
    if not head:
        return False, "Malformed proposal token", None
    trip_id = head
    exp_ts_str, signature = parts[1], parts[2]

    try:
        exp_ts = int(exp_ts_str)
    except ValueError:
        return False, "Malformed proposal token", None

    # Verify signature against the token's own agency field (no guess-loop):
    # recover the raw agency id by inverting generation's escaping, then
    # rebuild the exact payload that was signed.
    try:
        agency_id = _decode_agency_field(agency_field)
    except (ValueError, UnicodeDecodeError):
        return False, "Malformed proposal token", None
    # Enforce one canonical wire representation. Without this check, an
    # attacker could submit an alternate raw representation (for example a
    # slash or percent escape) that verifies the same HMAC but is not the
    # representation emitted by the issuer and may be interpreted differently
    # by routers/proxies.
    if not agency_id or _encode_agency_field(agency_id) != agency_field:
        return False, "Malformed proposal token", None
    payload = f"{trip_id}:{agency_id}:{exp_ts}"
    expected_sig = hmac.new(_SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()
    if len(signature) != len(expected_sig) or not hmac.compare_digest(signature, expected_sig):
        return False, "Invalid cryptographic token signature", None

    # Verify TTL
    now_ts = int(datetime.now(timezone.utc).timestamp())
    if now_ts >= exp_ts:
        return False, "Proposal capability token has expired (TTL elapsed)", None

    return True, "valid", trip_id



def revoke_proposal_token(token: str) -> bool:
    """Explicitly revoke a proposal capability token (durable across restarts).

    FND-0219: the durable trust control for v3 credentials is the SQL token
    store (hash-keyed, multi-replica safe); the file-backed store is retained
    for legacy v2 credentials (also hash-keyed now). The projection-cache
    entry is evicted so no stale view can outlive the revocation.
    """
    revoked_at = datetime.now(timezone.utc)
    persisted_file = False
    try:
        store_revoked = _store().revoke(token)
    except Exception as exc:
        logger.error("Failed to revoke proposal token in durable store: %s", exc)
        store_revoked = False
    with _revocations_lock:
        _REVOKED_TOKENS[hash_token(token)[0]] = revoked_at.isoformat()
        persisted_file = _persist_revocations_locked()
    _PROPOSAL_VIEW_CACHE.pop(token)
    return persisted_file or store_revoked


def generate_proposal_token(trip_id: str, agency_id: str = "system") -> str:
    """Generate a cryptographically signed capability token with TTL (F-02)."""
    return generate_signed_proposal_token(trip_id, agency_id)


def _build_demo_proposal(token: str, trip_id: str) -> PublicProposalView:
    """Build the legacy rich fixture only for an explicitly gated demo.

    This data is intentionally not a fallback for signed production tokens.
    A valid capability token still has to resolve to a persisted, agency-bound
    proposal resource in the normal path below.
    """
    base_options = [
        ProposalOption(
            id="opt_hotel_upgrade",
            category="accommodation",
            name="Upgrade to 5-Star Grand Luxury Suite",
            description="Private balcony overlooking the grand canal with daily champagne breakfast.",
            price_delta_usd=450.0,
            selected=False,
            is_default=False,
        ),
        ProposalOption(
            id="opt_private_transfer",
            category="transport",
            name="Private Chauffeur Airport & Rail Transfers",
            description="Dedicated Mercedes-Benz S-Class transfer with meet-and-greet.",
            price_delta_usd=180.0,
            selected=True,
            is_default=True,
        ),
        ProposalOption(
            id="opt_wine_tour",
            category="activity",
            name="Exclusive Sommelier Vineyard Masterclass",
            description="Private tasting tour through historic family estates with lunch.",
            price_delta_usd=220.0,
            selected=False,
            is_default=False,
        ),
    ]

    proposal = PublicProposalView(
        token=token,
        trip_id=trip_id or "trip_2333bff6434d",
        title="Bespoke Italian Grand Tour: Rome, Florence & Amalfi Coast",
        destination="Italy (Rome, Florence, Amalfi Coast)",
        duration_days=8,
        traveler_name="Priya & Rajesh Sharma",
        base_price_usd=4850.0,
        selected_total_price_usd=5030.0,
        currency="USD",
        status="open",
        days=[
            ProposalDay(
                day_number=1,
                title="Arrival in the Eternal City & Sunset Welcome",
                location="Rome, Italy",
                description="Private VIP arrival transfer to Hotel de Russie. Evening aperitivo in Piazza del Popolo.",
                highlights=["VIP Airport Meet & Greet", "Colosseum at Twilight View", "Private Welcome Dinner"],
                options=[],
            ),
            ProposalDay(
                day_number=2,
                title="Vatican Secret Archives & Renaissance Masterpieces",
                location="Rome & Vatican City",
                description="Early morning access before public opening hours with a private art historian guide.",
                highlights=["Sistine Chapel Private Access", "St. Peter's Basilica", "Historic Trastevere Walk"],
                options=[],
            ),
            ProposalDay(
                day_number=3,
                title="High-Speed Rail to Florence & Tuscan Hillside",
                location="Florence, Italy",
                description="First-class Frecciarossa express to Florence. Check-in at Four Seasons Hotel Firenze.",
                highlights=["Frecciarossa Executive Class", "Uffizi Gallery Fast-Track", "Duomo Panoramic Rooftop"],
                options=[base_options[0]],
            ),
        ],
        available_options=base_options,
        reality_tier="demo",
    )
    _PROPOSAL_VIEW_CACHE.set(token, proposal)
    return proposal


def _demo_mode_enabled() -> bool:
    """Return whether the explicitly opt-in legacy demo seam is enabled."""
    return os.getenv("PUBLIC_PROPOSAL_DEMO_MODE", "").strip().lower() in {
        "1",
        "true",
        "yes",
    }


def _verified_agency_id(token: str) -> Optional[str]:
    """Recover the canonical agency claim after token verification.

    ``verify_proposal_token`` deliberately keeps its historical three-value
    return contract. This helper performs only the already-verified structural
    decode needed to bind that claim to the persisted trip resource.
    """
    if token in _DEMO_TOKEN_ALLOWLIST or not token.startswith(_TOKEN_PREFIX):
        return None
    parts = token[len(_TOKEN_PREFIX) :].rsplit("_", 2)
    if len(parts) != 3:
        return None
    head = parts[0]
    _trip_id, separator, agency_field = head.rpartition("_")
    if not separator:
        return None
    try:
        agency_id = _decode_agency_field(agency_field)
    except (ValueError, UnicodeDecodeError):
        return None
    if not agency_id or _encode_agency_field(agency_id) != agency_field:
        return None
    return agency_id


def _verified_agency_for_token(token: str) -> Optional[str]:
    """Issuing agency for a VERIFIED token, across wire formats (FND-0219).

    v3 credentials carry no inline agency: the durable row is the binding.
    Legacy v2 tokens decode their signed agency field. Callers must only use
    this after ``verify_proposal_token`` accepted the token.
    """
    if token.startswith(V3_TOKEN_PREFIX):
        try:
            credential_status, record = _store().verify(token)
        except Exception as exc:
            logger.error("Proposal token store unavailable during agency lookup: %s", exc)
            return None
        if credential_status == TokenStatus.VALID and record is not None:
            return record.agency_id
        return None
    return _verified_agency_id(token)


def _as_finite_price(value: object) -> Optional[float]:
    """Convert an observed proposal price without inventing a value."""
    if isinstance(value, bool) or value is None:
        return None
    try:
        price = float(value)
    except (TypeError, ValueError):
        return None
    return price if math.isfinite(price) and price >= 0 else None


def _duration_from_packet(packet: dict) -> Optional[int]:
    """Derive duration from persisted dates; return ``None`` when absent."""
    start_raw = packet.get("start_date")
    end_raw = packet.get("end_date")
    if not start_raw or not end_raw:
        return None
    try:
        start = datetime.fromisoformat(str(start_raw).replace("Z", "+00:00"))
        end = datetime.fromisoformat(str(end_raw).replace("Z", "+00:00"))
    except ValueError:
        return None
    duration = (end.date() - start.date()).days
    return duration if duration > 0 else None


def _build_persisted_proposal(token: str, trip_id: str, agency_id: str) -> PublicProposalView:
    """Project only persisted, traveler-safe proposal facts.

    Missing proposal content is a non-ready resource, not permission to fill
    the response with a generic Italy itinerary or prices. Returning ``None``
    would conflate a missing record with a malformed projection, so this
    helper raises a uniform not-found response at the public boundary.
    """
    trip = TripStore.get_trip_for_agency(trip_id, agency_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Proposal resource not found or link expired")

    safe_trip = TripStore.get_trip_for_public_access(trip_id)
    if not safe_trip:
        raise HTTPException(status_code=404, detail="Proposal resource not found or link expired")

    packet = safe_trip.get("packet") or {}
    strategy = safe_trip.get("strategy") or {}
    recommendation = strategy.get("recommended_option") or {}
    destination = packet.get("destination") or safe_trip.get("destination")
    title = recommendation.get("name")
    base_price = _as_finite_price(recommendation.get("cost"))
    duration_days = _duration_from_packet(packet)

    # A public proposal must have enough observed data to be meaningful. Do
    # not turn absent dates, title, or price into plausible-looking fixtures.
    if not destination or not title or base_price is None or duration_days is None:
        raise HTTPException(status_code=404, detail="Proposal resource not found or link expired")

    currency = recommendation.get("currency") or "USD"
    if not isinstance(currency, str) or not currency.strip():
        currency = "USD"

    return PublicProposalView(
        token=token,
        trip_id=trip_id,
        title=str(title),
        destination=str(destination),
        duration_days=duration_days,
        # The safe projection intentionally does not expose traveler PII. A
        # neutral label is truthful and avoids claiming an unobserved name.
        traveler_name="Traveler",
        base_price_usd=base_price,
        selected_total_price_usd=base_price,
        currency=currency,
        status="accepted" if trip.get("proposal_accepted_at") else "open",
        accepted_at=trip.get("proposal_accepted_at"),
        accepted_by=None,
        days=[],
        available_options=[],
        reality_tier="persisted_observed",
    )


def _get_or_create_proposal(token: str) -> PublicProposalView:
    is_valid, reason, trip_id = verify_proposal_token(token)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED if "signature" in reason.lower() or "malformed" in reason.lower() else status.HTTP_410_GONE,
            detail=f"Proposal access denied: {reason}",
        )

    # The exact allowlisted fixtures remain available only to local/demo
    # callers that explicitly opt in. Production never receives fabricated
    # proposal content merely because a token string is recognized.
    if token in _DEMO_TOKEN_ALLOWLIST:
        if not _demo_mode_enabled():
            raise HTTPException(status_code=404, detail="Proposal resource not found or link expired")
        cached_demo = _PROPOSAL_VIEW_CACHE.get(token)
        if cached_demo is not None:
            return cached_demo
        return _build_demo_proposal(token, trip_id or _DEMO_LEGACY_TRIP_ID)

    # Projection cache only — the credential was verified above, so a cached
    # view may be served; TTL/revocation is re-enforced on every request.
    cached = _PROPOSAL_VIEW_CACHE.get(token)
    if cached is not None:
        return cached

    agency_id = _verified_agency_for_token(token)
    if not agency_id or not trip_id:
        raise HTTPException(status_code=401, detail="Proposal access denied: malformed proposal token")
    proposal = _build_persisted_proposal(token, trip_id, agency_id)
    _PROPOSAL_VIEW_CACHE.set(token, proposal)
    return proposal



@router.get("/{token}", response_model=PublicProposalView)
def get_public_proposal(token: str) -> PublicProposalView:
    """Retrieve public interactive proposal details by token."""
    return _get_or_create_proposal(token)


@router.post("/{token}/calculate", response_model=PublicProposalView)
def calculate_proposal_options(token: str, req: UpdateOptionsRequest) -> PublicProposalView:
    """Recalculate proposal total based on selected option IDs."""
    proposal = _get_or_create_proposal(token)
    selected_set = set(req.selected_option_ids)

    updated_options = []
    options_total = 0.0
    for opt in proposal.available_options:
        is_selected = opt.id in selected_set
        updated_options.append(
            ProposalOption(
                id=opt.id,
                category=opt.category,
                name=opt.name,
                description=opt.description,
                price_delta_usd=opt.price_delta_usd,
                selected=is_selected,
                is_default=opt.is_default,
            )
        )
        if is_selected:
            options_total += opt.price_delta_usd

    proposal.available_options = updated_options
    proposal.selected_total_price_usd = round(proposal.base_price_usd + options_total, 2)
    _PROPOSAL_VIEW_CACHE.set(token, proposal)
    return proposal


@router.post("/{token}/accept", response_model=PublicProposalView)
def accept_proposal(token: str, req: AcceptProposalRequest) -> PublicProposalView:
    """E-sign and accept proposal.

    PA-02: acceptance is the authorization artifact for the whole money path,
    so besides the process-local registry cache it is persisted DURABLY on the
    trip record (``proposal_accepted_at`` / ``proposal_accepted_by`` /
    ``proposal_acceptance_token`` / ``proposal_esign_consent``). Fulfillment
    verifies against that durable field. If the trip record cannot be updated,
    acceptance fails loudly instead of silently staying non-durable.
    """
    if not req.e_signature_consent:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Electronic signature consent is required to accept this proposal.",
        )

    proposal = _get_or_create_proposal(token)
    now_iso = datetime.now(timezone.utc).isoformat()

    # PA-02: durable persistence on the trip record FIRST — the registry row
    # must never advertise an acceptance the durable store does not have (a
    # failed persistence must not leave a process-local "accepted" row). The
    # exact allowlisted demo fixtures are explicitly process-local test/demo
    # seams (see _build_demo_proposal) with no durable trip behind them, so
    # the registry remains their only store; real signed tokens MUST persist
    # durably.
    signer_label = f"{req.signer_name} <{req.signer_email}>"
    if token not in _DEMO_TOKEN_ALLOWLIST:
        acceptance_updates = {
            "proposal_accepted_at": now_iso,
            "proposal_accepted_by": signer_label,
            "proposal_acceptance_token": token,
            "proposal_esign_consent": True,
            # FND-0174: explicit honest markers. The acceptance is
            # consequential state (it authorizes the money path), so it may
            # never look like a silently blob-only record: the durable
            # storage authority is the trip record itself (TripStore), the
            # evidence is a real asserted e-sign consent (not a preview, not
            # a carrier-verified artifact). Deliberately NOT migrated into
            # the BookingConfirmation state machine: that table models
            # supplier commitments (supplier/confirmation-number fields,
            # shared active-slot uniqueness), while this is client
            # authorization evidence — a different evidence family with its
            # own authority, now labeled as such.
            "proposal_acceptance_reality_tier": "real",
            "proposal_acceptance_storage": "trip_record_durable",
        }
        persisted_trip = TripStore.update_trip(proposal.trip_id, acceptance_updates)
        if not persisted_trip:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Proposal acceptance could not be persisted: trip "
                    f"'{proposal.trip_id}' has no durable record. Acceptance is "
                    "refused rather than kept process-local (PA-02)."
                ),
            )

    proposal.status = "accepted"
    proposal.accepted_at = now_iso
    proposal.accepted_by = signer_label

    # Audit the acceptance — emitted from the durable-persistence path, before
    # and independent of the registry cache write below.
    AuditStore.log_event(
        "proposal_accepted",
        "public_client",
        {
            "proposal_token": token,
            "trip_id": proposal.trip_id,
            "signer_name": req.signer_name,
            "signer_email": req.signer_email,
            "total_price_usd": proposal.selected_total_price_usd,
            "accepted_at": now_iso,
            "persisted_on_trip": token not in _DEMO_TOKEN_ALLOWLIST,
            # FND-0174: mirror the acceptance markers so the audit trail
            # carries the same honest provenance the trip record does.
            "reality_tier": "real",
            "storage": "trip_record_durable",
        },
    )
    _PROPOSAL_VIEW_CACHE.set(token, proposal)
    return proposal
