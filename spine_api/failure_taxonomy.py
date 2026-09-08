"""
failure_taxonomy.py — PA-07 failure classification for Waypoint OS spine runs.

Historically the run ledger recorded only ``error_type`` (raw
``type(e).__name__``) and recovery requeued every stuck run through the same
2x-requeue ladder regardless of cause. That is class-blind: re-running a run
that failed because persisted state diverged cannot fix it, and re-running a
policy block is never safe.

This module defines a closed set of failure classes and a best-effort
``classify_failure(exc, stage)`` mapper so the ledger meta carries a stable
``failure_class`` alongside the raw exception type, and the recovery agent can
branch on cause:

    tool / model / environment → transient: requeue is meaningful (max 2)
    state / verification / authority → re-running cannot fix divergence:
        straight to human escalation
    policy_block → never requeue

Classification is best-effort by design: it never raises, and unknown
exceptions land in ``unclassified`` (existing ladders still apply there). The
raw ``error_type`` remains authoritative evidence in ledger meta.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional


class FailureClass(str, Enum):
    """Closed taxonomy of run failure causes (PA-07)."""

    MODEL = "model"                    # LLM / provider-model errors
    TOOL = "tool"                      # HTTP / provider / network tool errors
    ENVIRONMENT = "environment"        # timeouts and infra environment faults
    STATE = "state"                    # persistence / TripStore / DB divergence
    VERIFICATION = "verification"      # assertion / verification-style errors
    AUTHORITY = "authority"            # authorization / permission failures
    POLICY_BLOCK = "policy_block"      # strict leakage / validation policy
    UNCLASSIFIED = "unclassified"      # anything not yet mapped


# Classes where re-running the pipeline is a meaningful repair strategy.
REQUEUEABLE_CLASSES = frozenset(
    {
        FailureClass.TOOL.value,
        FailureClass.MODEL.value,
        FailureClass.ENVIRONMENT.value,
    }
)

# Classes where re-running cannot fix the cause — escalate to a human.
ESCALATE_ONLY_CLASSES = frozenset(
    {
        FailureClass.STATE.value,
        FailureClass.VERIFICATION.value,
        FailureClass.AUTHORITY.value,
    }
)

# Classes that must never be requeued under any circumstances.
NEVER_REQUEUE_CLASSES = frozenset({FailureClass.POLICY_BLOCK.value})


def _type_chain_names(exc: BaseException) -> list[str]:
    """Return class names (plus module-qualified) for the exception chain."""
    names: list[str] = []
    current: Optional[BaseException] = exc
    seen = 0
    while current is not None and seen < 8:  # bounded chain walk
        cls = type(current)
        names.append(cls.__name__)
        names.append(f"{cls.__module__}.{cls.__name__}")
        current = current.__cause__ or current.__context__
        seen += 1
    return names


def _message(exc: BaseException) -> str:
    try:
        return f"{type(exc).__name__}: {exc}"
    except Exception:  # pragma: no cover — defensive, classification never raises
        return type(exc).__name__


def _matches_any(names: list[str], *needles: str) -> bool:
    lowered_names = [n.lower() for n in names]
    return any(needle in name for name in lowered_names for needle in needles)


_TIMEOUT_MARKERS = ("timeout", "timed out", "deadline exceeded")
_STATE_MARKERS = (
    "tripstore",
    "persistence",
    "database",
    "ledger entry",
    "sqlalchemy",
    "asyncpg",
    "psycopg",
    "sqlite",
    "deadlock",
    "connection refused",
    "no ledger",
)
_MODEL_MARKERS = ("llm", "model", "genai", "gemini", "provider", "completion")
_TOOL_MARKERS = (
    "http",
    "request",
    "connection",
    "network",
    "socket",
    "api",
    "curl",
    "urllib",
)
_AUTHORITY_MARKERS = ("permission", "forbidden", "unauthorized", "not allowed", "access denied")

# Module-qualified prefixes that identify specific third-party error families.
_DB_NAME_NEEDLES = (
    "sqlite3.",
    "asyncpg.",
    "sqlalchemy.",
    "psycopg",
    "pyodbc.",
)
_HTTP_NAME_NEEDLES = (
    "requests.",
    "httpx.",
    "urllib.error",
    "aiohttp.",
    "socket.",
)
_LLM_NAME_NEEDLES = (
    "google.genai",
    "google.api_core",
    "openai.",
    "anthropic.",
)


def classify_failure(exc: Optional[BaseException], stage: Optional[str] = None) -> str:
    """Best-effort map an exception (optionally with its stage) to a class.

    Order matters — most specific first:
      1. strict leakage / validation policy violations → policy_block
      2. assertion / verification errors → verification
      3. timeouts → environment
      4. LLM / provider-model errors → model
      5. persistence / database errors → state
      6. authorization errors → authority
      7. HTTP / network tool errors → tool
      8. anything else → unclassified

    Never raises; returns FailureClass values as plain strings so ledger meta
    stays JSON-serializable without enum plumbing.
    """
    if exc is None:
        return FailureClass.UNCLASSIFIED.value

    try:
        names = _type_chain_names(exc)
        message = _message(exc).lower()

        # 1. Policy blocks: strict leakage and validation gate violations.
        # StrictLeakageViolation is unambiguously a policy surface by name.
        if isinstance(exc, AssertionError) and "leakage" in message:
            return FailureClass.POLICY_BLOCK.value
        if _matches_any(names, "leakage"):
            return FailureClass.POLICY_BLOCK.value
        if _matches_any(names, "validationerror", "schemaerror"):
            # pydantic ValidationError etc. — confirm via message to avoid
            # over-matching unrelated classes merely named like this.
            if "leak" in message or "validation" in message or "invalid" in message:
                return FailureClass.POLICY_BLOCK.value

        # 2. Assertion / verification failures.
        if isinstance(exc, AssertionError) or _matches_any(names, "verificationerror", "assertionerror"):
            return FailureClass.VERIFICATION.value

        # 3. Timeouts are environment faults (the sweep uses the same class).
        if isinstance(exc, TimeoutError) or any(marker in message for marker in _TIMEOUT_MARKERS):
            return FailureClass.ENVIRONMENT.value

        # 4. LLM / provider-model errors (before generic tool match: LLM
        # clients raise HTTP-flavored errors too).
        if _matches_any(names, *_LLM_NAME_NEEDLES) or (
            _matches_any(names, *_MODEL_MARKERS) and _matches_any(names, "error", "exception", "failure")
        ):
            return FailureClass.MODEL.value

        # 5. Persistence / state divergence.
        if _matches_any(names, *_DB_NAME_NEEDLES) or _matches_any(
            names, "databaseerror", "storageerror", "persistenceerror", "guardstorageerror"
        ):
            return FailureClass.STATE.value
        if any(marker in message for marker in _STATE_MARKERS):
            return FailureClass.STATE.value

        # 6. Authority.
        if any(marker in message for marker in _AUTHORITY_MARKERS) or _matches_any(
            names, "permissionerror"
        ):
            return FailureClass.AUTHORITY.value

        # 7. HTTP / network tool errors.
        if _matches_any(names, *_HTTP_NAME_NEEDLES) or isinstance(exc, ConnectionError):
            return FailureClass.TOOL.value
        if any(marker in message for marker in _TOOL_MARKERS):
            return FailureClass.TOOL.value

        return FailureClass.UNCLASSIFIED.value
    except Exception:  # pragma: no cover — classification must never break a run
        return FailureClass.UNCLASSIFIED.value


def recovery_action_for(failure_class: Optional[str]) -> str:
    """Map a persisted failure_class to the recovery action class (PA-07).

    Returns one of:
      "requeue"  — transient cause; existing max-2 requeue ladder applies
      "escalate" — re-running cannot fix it (state/verification/authority)
      "never_requeue" — policy block; escalate, never requeue
      "default"  — unknown/unclassified; keep the existing ladder
    """
    if failure_class in NEVER_REQUEUE_CLASSES:
        return "never_requeue"
    if failure_class in ESCALATE_ONLY_CLASSES:
        return "escalate"
    if failure_class in REQUEUEABLE_CLASSES:
        return "requeue"
    return "default"


def describe(failure_class: Optional[str]) -> dict[str, Any]:
    """Human-readable descriptor for operator surfaces (additive helper)."""
    descriptions = {
        FailureClass.MODEL.value: "LLM/provider-model error",
        FailureClass.TOOL.value: "external tool/network error",
        FailureClass.ENVIRONMENT.value: "environment/timeout fault",
        FailureClass.STATE.value: "persisted-state divergence",
        FailureClass.VERIFICATION.value: "verification/assertion failure",
        FailureClass.AUTHORITY.value: "authorization failure",
        FailureClass.POLICY_BLOCK.value: "policy block (strict leakage/validation)",
        FailureClass.UNCLASSIFIED.value: "unclassified",
    }
    return {
        "failure_class": failure_class or FailureClass.UNCLASSIFIED.value,
        "description": descriptions.get(
            failure_class or FailureClass.UNCLASSIFIED.value, "unclassified"
        ),
    }
