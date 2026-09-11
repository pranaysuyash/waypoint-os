"""
security.privacy_guard — PII guardrails for untrusted / plaintext stores.

Purpose:
Block real user PII from being stored in plaintext JSON when the persistence
layer cannot be trusted to protect it.

Layer 1 (always active): Regex-based heuristics for emails, India phone numbers,
Aadhaar-pattern numbers, medical keywords, and freeform field detection.

Layer 2 (optional, enabled by default): SpaCy NER for PERSON entities. Detects
names like "Priya Sharma" in freeform text that regex cannot catch. Requires
`spacy` + `en_core_web_sm` (via `bash scripts/setup_nlp_models.sh`). This layer
is a best-effort enhancement and FAILS OPEN: if the model is unavailable the
guard degrades to Layer 1 only and never raises. It is never the boundary
control — see the mode matrix below.

Mode matrix (see check_trip_data for the authoritative behaviour):
  dogfood (default):
    - Plaintext JSON store, no encryption/RLS. FAIL-CLOSED: real-user PII is
      blocked; known fixtures and synthetic data are allowed.
    - Layer 2 (SpaCy) runs and contributes to the block decision.
  beta / production:
    - The guard is NOT the production encryption boundary; PostgreSQL + RLS is.
    - If the active store is the PLAINTEXT FILE STORE (TRIPSTORE_BACKEND in
      {file, json}), the boundary is absent, so the guard FAILS CLOSED and
      blocks real-user PII exactly as in dogfood.
    - If the store is SQL/Postgres (TRIPSTORE_BACKEND in {sql, postgres,
      postgresql}), the guard FAILS OPEN but runs a non-blocking Layer 1 audit
      scan and logs findings. It does not block (avoids false-positive outages);
      encryption/RLS is the real control.

Environment variables:
  DATA_PRIVACY_MODE — dogfood | beta | production (default: dogfood)
  TRIPSTORE_BACKEND — sql | postgres | postgresql (safe) | file | json (plaintext)
  NLP_PII_GUARD_ENABLED — 1|true|yes or 0|false|no (default: 1)
    Set to 0 to disable SpaCy NLP layer (e.g. in unit tests without the model)
"""

import logging
import os
import re
from typing import Any, Dict, Optional, Set

log = logging.getLogger(__name__)

# =============================================================================
# Configuration
# =============================================================================

def _data_privacy_mode() -> str:
    return os.getenv("DATA_PRIVACY_MODE", "dogfood").lower().strip()

# Known fixture IDs from data/fixtures/raw_fixtures.py
# These are auto-populated at module load from fixture files
KNOWN_FIXTURE_IDS: Set[str] = set()


def _load_fixture_ids() -> None:
    """Autodetect fixture IDs from the fixture data module."""
    try:
        from data.fixtures.raw_fixtures import RAW_FIXTURES

        KNOWN_FIXTURE_IDS.update(RAW_FIXTURES.keys())
    except ImportError:
        # Fallback: try scanning the raw_fixtures.py for fixture_id keys
        try:
            import ast
            import pathlib

            fixture_path = pathlib.Path(__file__).parent.parent / "data" / "fixtures" / "raw_fixtures.py"
            if fixture_path.exists():
                source = fixture_path.read_text()
                tree = ast.parse(source)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Call) and getattr(node.func, "attr", None) == "get":
                        if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant):
                            fixture_id = node.args[1].value
                            if isinstance(fixture_id, str):
                                KNOWN_FIXTURE_IDS.add(fixture_id)
        except (SyntaxError, ValueError, OSError, AttributeError):
            pass


_load_fixture_ids()

# Also common synthetic fixture prefixes/patterns
_SYNTHETIC_PATTERNS = {
    "fixture_id",
    "test",
    "seed",
    "demo",
    "sample",
    "synthetic",
}

# =============================================================================
# High-risk PII patterns (simple, high-signal heuristics)
# =============================================================================

_EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
_PHONE_PATTERN = re.compile(
    r"(\+91[-\s]?)?((\d{5}[-\s]?\d{5})|(\d{10})|(\d{3}[-\s]?\d{3}[-\s]?\d{4}))"
)
_GENERATED_ID_PATTERN = re.compile(
    r"^(?:draft|trip|pkt|run|ref|pkt_[a-z0-9]+|draft_[a-z0-9]+|trip_[a-z0-9]+|run_[a-z0-9]+)$",
    re.IGNORECASE,
)
_MEDICAL_KEYWORDS = re.compile(
    r"\b(diabetic|diabetes|wheelchair|mobility|medical|health|allerg|disabil|chronic|insulin|epilepsy|asthma|heart|bp|blood pressure|pregnant|pregnancy)\b",
    re.IGNORECASE,
)

# Fields that if present indicate real freeform user input.
# NOTE: only checked at the top level or within raw_input/extracted/extracted facts.
# Deeply nested fields (e.g. analytics.review_metadata.notes) are ignored.
_FREEFORM_FIELD_NAMES = {
    "raw_note",
    "freeform_text",
    "content",
    "note",
    "notes",
    "text",
    "user_note",
    "traveler_note",
    "comment",
    "description",
    "feedback",
    "additional_info",
    "special_requests",
    "medical_notes",
    "dietary_restrictions",
    "agent_notes",
    "agentNotes",
    "owner_note",
    # FND-0267: customer-supplied attachment filenames are user-controlled
    # free text (e.g. "john_doe_+919876543210_quote.png" on the TS-03 inbound
    # manifest) and must be scanned like any other freeform field.
    "filename",
}


class PrivacyGuardError(Exception):
    """Raised when dogfood mode blocks persistence of real-user PII."""

    pass


# =============================================================================
# Helper: deep string extraction
# =============================================================================

def _extract_strings(value: Any, max_depth: int = 5) -> list:
    """Recursively extract all string values from a nested dict/list."""
    if max_depth <= 0:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        result = []
        for k, v in value.items():
            if isinstance(v, str):
                result.append(v)
            elif isinstance(v, (dict, list)):
                result.extend(_extract_strings(v, max_depth - 1))
        return result
    if isinstance(value, list):
        result = []
        for item in value:
            result.extend(_extract_strings(item, max_depth - 1))
        return result
    return []


def _extract_field_names(value: Any, prefix: str = "", max_depth: int = 5) -> Set[str]:
    """Recursively extract all field names from nested dicts up to max_depth."""
    if max_depth <= 0:
        return set()
    result = set()
    if isinstance(value, dict):
        for k, v in value.items():
            full = f"{prefix}.{k}" if prefix else k
            result.add(full)
            result.update(_extract_field_names(v, full, max_depth - 1))
    elif isinstance(value, list):
        for item in value:
            result.update(_extract_field_names(item, prefix, max_depth - 1))
    return result


# =============================================================================
# Check: is this data from a known fixture?
# =============================================================================

def _is_known_fixture(trip_data: Dict[str, Any]) -> bool:
    """Check if trip data is from a known synthetic fixture."""
    raw_input = trip_data.get("raw_input") or {}
    fixture_id = raw_input.get("fixture_id")
    if fixture_id:
        if fixture_id in KNOWN_FIXTURE_IDS:
            return True
        # Also allow known synthetic prefixes
        if any(fixture_id.startswith(p) or p in fixture_id.lower() for p in _SYNTHETIC_PATTERNS):
            return True

    # Check if source field indicates fixture
    source = trip_data.get("source", "")
    if any(p in source.lower() for p in _SYNTHETIC_PATTERNS):
        return True

    # Check if the raw_input contains a fixture_id key (even if value is None)
    if isinstance(raw_input, dict) and "fixture_id" in raw_input:
        return True

    return False


# =============================================================================
# Check: high-signal PII heuristics
# =============================================================================

def _has_email(data: Dict[str, Any]) -> Optional[str]:
    """Return offending string if an email is found, else None."""
    for s in _extract_strings(data):
        if _EMAIL_PATTERN.search(s):
            return s[:200]
    return None


def _has_phone(data: Dict[str, Any]) -> Optional[str]:
    """Return offending string if a phone-like number is found, else None."""
    for s in _extract_strings(data):
        cleaned = s.strip()
        if _GENERATED_ID_PATTERN.match(cleaned):
            continue
        if _PHONE_PATTERN.search(s):
            s_clean = re.sub(r"[^\d\+]", "", s)
            if len(s_clean) >= 10:
                return s[:200]
    return None


def _has_medical_indicator(data: Dict[str, Any]) -> Optional[str]:
    """Return field name if a medical/health keyword is found, else None."""
    all_text = " ".join(_extract_strings(data))
    match = _MEDICAL_KEYWORDS.search(all_text)
    if match:
        return match.group(0)
    return None


def _has_freeform_user_input(data: Dict[str, Any]) -> Optional[str]:
    """
    Check for freeform user input fields that are populated.
    Only checks top-level and raw_input/extracted (first 2 levels), ignoring deeply nested fields
    like analytics.review_metadata.notes.
    Returns field path if found, else None.
    """
    # Only check up to 2 levels deep (top level + one sub-level)
    max_depth = 2
    field_names = _extract_field_names(data, max_depth=max_depth)

    for name in field_names:
        base = name.split(".")[-1]
        if base not in _FREEFORM_FIELD_NAMES:
            continue
        value = _get_nested_value(data, name)
        if _is_populated_freeform(value):
            return name
    return None


def _is_populated_freeform(value: Any) -> bool:
    """Return True if value contains populated freeform text."""
    if isinstance(value, str) and len(value.strip()) > 10:
        return True
    if isinstance(value, dict):
        for sub_v in value.values():
            if isinstance(sub_v, str) and len(sub_v.strip()) > 10:
                return True
    if isinstance(value, list):
        for item in value:
            if isinstance(item, str) and len(item.strip()) > 10:
                return True
    return False


def _get_nested_value(data: Dict[str, Any], path: str) -> Any:
    """Get value from nested dict by dot-notation path."""
    parts = path.split(".")
    for part in parts:
        if isinstance(data, dict) and part in data:
            data = data[part]
        else:
            return None
    return data


def _scan_layer1(trip_data: Dict[str, Any]) -> Optional[str]:
    """
    Layer 1 (always-active regex heuristics). Returns a human-readable reason
    string if the data looks like real-user PII, else None.

    No model dependency — safe to run on any write path, including the
    non-blocking production audit scan. Checks:
      1. Email/phone in raw user-input fields (raw_input, raw_note) — even for
         known fixtures, because a fixture's raw input may carry real contacts.
      2. Known fixtures bypass the remaining checks (synthetic scenario data).
      3. Full scan for email, phone, freeform user input, and medical/mobility
         indicators.
    """
    # Always check raw user-input fields for email/phone — even for known fixtures.
    raw_input_scope: Dict[str, Any] = {}
    for field in ("raw_input", "raw_note"):
        if field in trip_data:
            raw_input_scope[field] = trip_data[field]

    if raw_input_scope:
        email_str = _has_email(raw_input_scope)
        if email_str:
            return f"Detected email address: '{email_str[:50]}...'"
        phone_str = _has_phone(raw_input_scope)
        if phone_str:
            return f"Detected phone number: '{phone_str[:50]}...'"

    # Known fixtures are allowed to contain freeform text and medical content
    # (synthetic/scenario data) in structured output fields.
    if _is_known_fixture(trip_data):
        return None

    # Full scan for non-fixture trips.
    email_str = _has_email(trip_data)
    if email_str:
        return f"Detected email address: '{email_str[:50]}...'"

    phone_str = _has_phone(trip_data)
    if phone_str:
        return f"Detected phone number: '{phone_str[:50]}...'"

    # Check for freeform user input
    freeform = _has_freeform_user_input(trip_data)
    if freeform:
        return f"Detected freeform user input in field: '{freeform}'"

    # Check for medical/health indicators (high-signal for sensitive PII)
    medical = _has_medical_indicator(trip_data)
    if medical:
        return f"Detected health/mobility indicator: '{medical}'"

    return None


def _is_likely_real_user_data(data: Dict[str, Any]) -> Optional[str]:
    """
    Return a human-readable reason string if data appears to be real user PII.
    Return None if clean (or if from a known fixture without PII in raw input).

    Combines Layer 1 (regex, always active) with Layer 2 (SpaCy NER for PERSON,
    fail-open). Layer 2 only runs when NLP_PII_GUARD_ENABLED and the model is
    available; if it is not, the function degrades to Layer 1 and never raises.
    """
    reason = _scan_layer1(data)
    if reason:
        return reason

    # Layer 1 has already checked raw fixture input for email and phone. Once
    # those boundary checks pass, synthetic fixtures remain exempt from the
    # freeform and NLP heuristics just as they were before the layer split.
    if _is_known_fixture(data):
        return None

    # Layer 2: SpaCy NLP NER scan on freeform field values only.
    # Detects PERSON entities that regex cannot catch (e.g. "My name is Priya Sharma").
    # Runs only when spacy + en_core_web_sm are installed; fails-open otherwise.
    # NLP_PII_GUARD_ENABLED=0 disables this layer (e.g. in unit tests).
    if _is_nlp_guard_enabled():
        freeform_texts: list[str] = []
        for field_name in _FREEFORM_FIELD_NAMES:
            val = data.get(field_name)
            if isinstance(val, str) and len(val.strip()) > 5:
                freeform_texts.append(val)
            # Also check raw_input sub-fields
            raw = data.get("raw_input", {})
            if isinstance(raw, dict):
                sub = raw.get(field_name)
                if isinstance(sub, str) and len(sub.strip()) > 5:
                    freeform_texts.append(sub)

        for text in freeform_texts:
            persons = _nlp_scan_for_person_entities(text)
            if persons:
                names = ", ".join(f"'{p}'" for p in persons[:3])
                return (
                    f"NLP Layer 2: Detected PERSON entity in freeform field "
                    f"(names: {names}). Review before storing."
                )

    return None


# =============================================================================
# LAYER 2: SpaCy NLP NER Guard (optional, fail-open)
# =============================================================================
# Loaded lazily on first scan call. If spacy or en_core_web_sm are not
# installed, falls back to regex-only (Layer 1) with a single WARNING log.
# This means the guard is always available even in development setups that
# have not run scripts/setup_nlp_models.sh.
#
# Controlled by: NLP_PII_GUARD_ENABLED env var (default: enabled)
# Set NLP_PII_GUARD_ENABLED=0 to disable in unit tests or CI without the model.

_nlp_model = None  # Lazy-loaded on first use
_nlp_load_attempted = False  # Prevent repeated import failures


def _is_nlp_guard_enabled() -> bool:
    """Check if SpaCy NLP guard is enabled via environment variable."""
    val = os.environ.get("NLP_PII_GUARD_ENABLED", "1").strip().lower()
    return val not in ("0", "false", "no", "off")


def _get_nlp_model():
    """
    Lazy-load SpaCy en_core_web_sm. Returns model or None on failure.

    Thread-safe in CPython (GIL protects module-level assignment).
    Only attempts load once per process — failure is cached to avoid
    repeated import overhead on every request.

    FAILS OPEN: Layer 2 is a best-effort enhancement, not the boundary control.
    If spacy or en_core_web_sm are unavailable the function returns None and the
    guard degrades to Layer 1. It never raises — raising here would crash
    legitimate writes on boxes without the optional model installed, and the
    previous production fail-closed branch was unreachable dead code that only
    created a false sense of protection (see R-15).
    """
    global _nlp_model, _nlp_load_attempted
    if _nlp_load_attempted:
        return _nlp_model
    _nlp_load_attempted = True

    if not _is_nlp_guard_enabled():
        return None

    try:
        import spacy  # noqa: PLC0415
        _nlp_model = spacy.load("en_core_web_sm")
        log.info("privacy_guard: SpaCy NLP Layer 2 loaded (en_core_web_sm)")
    except ImportError:
        log.warning(
            "privacy_guard: spacy not installed — NLP Layer 2 disabled (fail-open). "
            "Run: bash scripts/setup_nlp_models.sh to enable PERSON NER."
        )
    except OSError:
        log.warning(
            "privacy_guard: en_core_web_sm model not found — NLP Layer 2 disabled "
            "(fail-open). Run: python -m spacy download en_core_web_sm"
        )
    return _nlp_model


def _nlp_scan_for_person_entities(text: str) -> list[str]:
    """
    Use SpaCy NER to extract PERSON entity mentions from freeform text.

    Returns a list of found person name strings (empty if none or NLP unavailable).

    Why PERSON only: ORG and GPE (location) entities are expected in travel text
    and would create noise. PERSON is the highest-signal PII risk in traveler
    inquiry context — names embedded in WhatsApp messages like "My name is Priya
    Sharma" are exactly what regex patterns miss.
    """
    nlp = _get_nlp_model()
    if nlp is None:
        return []

    try:
        doc = nlp(text[:2000])  # Cap at 2000 chars to bound latency
        return [ent.text for ent in doc.ents if ent.label_ == "PERSON"]
    except Exception as exc:  # noqa: BLE001
        log.warning("privacy_guard: SpaCy scan error — %s", exc)
        return []




def is_dogfood_mode() -> bool:
    return _data_privacy_mode() == "dogfood"


def is_beta_mode() -> bool:
    return _data_privacy_mode() == "beta"


def is_production_mode() -> bool:
    return _data_privacy_mode() == "production"


def get_privacy_mode() -> str:
    return _data_privacy_mode()


# Backends that represent the plaintext file store. Mirrors the unsafe branch of
# TripStore._backend() (must stay in sync). Safe backends are {sql, postgres,
# postgresql}; see the mode matrix in the module docstring.
_PLAINTEXT_BACKENDS = {"file", "json"}


def _uses_plaintext_store() -> bool:
    """True when TripStore persists to the plaintext file store.

    Only explicit plaintext backends (file/json) count. An unset backend is left
    to TripStore._backend()'s own environment enforcement (it fails closed in
    production/staging), so we do not block legitimate dev/test runs that leave
    it unset. See R-15.
    """
    raw = os.getenv("TRIPSTORE_BACKEND", "").strip().lower()
    return raw in _PLAINTEXT_BACKENDS


def _block_message(reason: str) -> str:
    return (
        f"Real user trip data cannot be persisted in plaintext in this mode. "
        f"Detected: {reason}. "
        f"Enable encryption/migration (TRIPSTORE_BACKEND=sql|postgres and "
        f"ENCRYPTION_KEY) before storing real user data."
    )



def _emit_audit_event(event_type: str, details: Dict[str, Any]) -> None:
    """Best-effort emission into the AuditStore hash chain (R-15 2.5).

    Lazy import: spine_api.persistence imports this module, so a module-level
    import would be circular. Audit failures are logged and swallowed — the
    guard observes the write path and must never become the outage.
    """
    try:
        from spine_api.persistence import AuditStore

        AuditStore.log_event(event_type, "system", dict(details))
    except Exception as exc:  # noqa: BLE001
        log.warning("privacy_guard: audit event %s could not be written — %s", event_type, exc)


def check_trip_data(trip_data: Dict[str, Any]) -> None:
    """Check trip data before persistence.

    Mode matrix (R-15):
      - dogfood:           FAIL-CLOSED. Block real-user PII in the plaintext store.
      - beta / production:
          * If the store is the PLAINTEXT FILE STORE, the encryption/RLS boundary
            is absent → FAIL-CLOSED (block), matching dogfood.
          * If the store is SQL/Postgres, the guard is NOT the boundary. It FAILS
            OPEN but runs a non-blocking Layer 1 audit scan and logs findings. It
            never blocks (avoids false-positive outages); encryption/RLS is the
            real control.

    Raises:
        PrivacyGuardError: when it fails closed and real-user PII is detected.
    """
    if is_dogfood_mode():
        reason = _is_likely_real_user_data(trip_data)
        if reason:
            raise PrivacyGuardError(_block_message(reason))
        return

    # beta / production.
    if _data_privacy_mode() == "production" and _uses_plaintext_store():
        # Misconfiguration: we claim to be safe but the store is plaintext. Real
        # PII would land in plaintext JSON — exactly what this guard exists to
        # prevent — so fail closed.
        reason = _is_likely_real_user_data(trip_data)
        if reason:
            log.error(
                "privacy_guard: DATA_PRIVACY_MODE=production but TRIPSTORE_BACKEND "
                "is a plaintext file store. Refusing to persist real-user PII "
                "(fail-closed)."
            )
            _emit_audit_event(
                "privacy_guard_blocked",
                {"mode": "production", "store": "plaintext", "findings": reason, "blocked": True},
            )
            raise PrivacyGuardError(_block_message(reason))
        return

    # Intended safe configuration (prod + SQL/Postgres, or beta): observable,
    # non-blocking audit. Layer 1 only (no model) to keep the write path fast
    # and deterministic; Layer 2 NER is dogfood-only where blocking matters.
    reason = _scan_layer1(trip_data)
    if reason:
        log.warning(
            "privacy_guard: AUDIT — real-PII-shaped data persisted in %s mode "
            "(not blocked; encryption/RLS is the boundary): %s",
            _data_privacy_mode(), reason,
        )
        # R-15 2.5: the fail-open admission must be observable in the audit
        # chain, not only in process logs — this is the guard admitting
        # PII-shaped data past the non-blocking layer.
        _emit_audit_event(
            "privacy_guard_admitted_pii_shape",
            {"mode": _data_privacy_mode(), "findings": reason, "blocked": False},
        )


def sanitize_input(text: str) -> str:
    """Scrub email addresses and phone numbers from raw text input."""
    if not text:
        return text
    # Mask emails
    scrubbed = re.sub(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "[REDACTED_EMAIL]", text)
    # Mask phone numbers
    scrubbed = re.sub(r"\+?\d{1,4}[-.\s]?\(?\d{1,3}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}", "[REDACTED_PHONE]", scrubbed)
    return scrubbed
