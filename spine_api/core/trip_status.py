"""
spine_api.core.trip_status — Canonical trip-status vocabulary, transition invariant, and history.

Why this exists (register N-2 / F-29 class): trip `status` is currently a freeform
string written by several independent paths (inbound router, pipeline execution,
agent runtime, generic update endpoints). The ESCALATE lead-persistence ADR had to
patch its semantics by hand (never-overwrite, dead-ID guard). This module makes the
load-bearing invariant *structural* instead of per-ADR:

    A trip whose intake is blocked (incomplete / needs_followup /
    needs_clarification / awaiting_customer_details / escalated) can never
    become quote-capable (ready_to_quote / ready_to_book) in one hop.

Quote generation is gated by NB01 at the packet level (src/intake/gates.py);
this guard is the status-level counterpart, enforced inside TripStore.save_trip
so that *every* writer — router, pipeline, agent, generic update — inherits it.

Scope discipline (deliberate, additive-first): the full typed enum + Literal
enforcement of every status value is a later slice gated on the derived
read-model (Docs/TPM_TRAINING_BLUEPRINT_PRODUCT_MAPPING_2026-09-01.md §5 N-4)
validating the real status distribution. Today: invariant + audit history +
alias normalization. Unknown status strings pass through with a warning —
this module never bricks a writer on an unfamiliar value it cannot classify.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger("spine_api.core.trip_status")

# Statuses that mean "quote generation may proceed downstream".
QUOTE_CAPABLE_STATUSES = frozenset({"ready_to_quote", "quote_ready", "ready_to_book"})

# Statuses that mean "intake is blocked; the packet is not trustworthy enough
# to quote". Matching the observed backend vocabulary (runtime.py:647, ESCALATE ADR).
INTAKE_BLOCKED_STATUSES = frozenset(
    {"incomplete", "needs_followup", "needs_clarification", "awaiting_customer_details", "escalated"}
)

STATUS_HISTORY_CAP = 50

# Statuses optimistic-sync may promote to active: its own intake vocabulary
# (moved here from the inbound router, register I-8, so it lives beside the
# invariant it operates on). ESCALATED is deliberately excluded even though
# it is intake-blocked: escalation is operator-owned — only a human
# resolve/reassign may clear it, never a field sync.
SYNC_PROMOTABLE_FROM_STATUSES = (INTAKE_BLOCKED_STATUSES - {"escalated"}) | {"new"}

# Legacy / case variants observed in code and persisted data → canonical token.
_STATUS_ALIASES = {
    "": "new",
    "in_progress": "in_progress",
    "inprogress": "in_progress",
    "new": "new",
    "active": "active",
}


class IllegalTripStatusTransition(ValueError):
    """Raised when a status write would violate the intake-blocked → quote-capable invariant."""

    def __init__(self, old_status: str, new_status: str, message: Optional[str] = None):
        self.old_status = old_status
        self.new_status = new_status
        super().__init__(
            message
            or (
                f"Illegal trip status transition {old_status!r} → {new_status!r}: "
                f"intake-blocked trips must pass through an active state before becoming "
                f"quote-capable (NB01 gating counterpart, register N-2)"
            )
        )


def normalize_trip_status(value: Any) -> str:
    """Map legacy/case variants onto the canonical vocabulary; unknowns pass
    through with a warning (additive-first: never brick a writer on an
    unfamiliar value — but the gap is logged so the vocabulary can be closed)."""
    if value is None:
        return "new"
    text = str(value).strip()
    canonical = _STATUS_ALIASES.get(text.lower())
    if canonical is None:
        logger.warning("Unclassified trip status %r passed through unnormalized", value)
        return text
    return canonical


def is_quote_capable(status: Optional[str]) -> bool:
    return (status or "").strip().lower() in QUOTE_CAPABLE_STATUSES


def is_intake_blocked(status: Optional[str]) -> bool:
    return (status or "").strip().lower() in INTAKE_BLOCKED_STATUSES


def enforce_status_transition(old_status: Optional[str], new_status: Optional[str]) -> None:
    """Raise IllegalTripStatusTransition if old → new violates the intake-blocked invariant.

    Same-status writes and all transitions not covered by the invariant are legal.
    """
    if old_status is None or new_status is None:
        return
    old_norm = str(old_status).strip().lower()
    new_norm = str(new_status).strip().lower()
    if old_norm == new_norm:
        return
    if is_intake_blocked(old_norm) and is_quote_capable(new_norm):
        raise IllegalTripStatusTransition(old_norm, new_norm)


def record_status_transition(
    trip_data: Dict[str, Any],
    old_status: Optional[str],
    new_status: Optional[str],
) -> None:
    """Append a {from,to,at} entry to trip_data['status_history'] (capped, durable).

    Works for both store backends: FileTripStore persists the key as-is;
    SQLTripStore folds unmapped keys into analytics._extra.
    """
    if old_status is None or new_status is None or str(old_status) == str(new_status):
        return
    history: List[Dict[str, Any]] = list(trip_data.get("status_history") or [])
    history.append(
        {
            "from": str(old_status),
            "to": str(new_status),
            "at": datetime.now(timezone.utc).isoformat(),
        }
    )
    trip_data["status_history"] = history[-STATUS_HISTORY_CAP:]
