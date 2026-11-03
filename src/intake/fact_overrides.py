"""Canonical field replacement semantics shared by intake correction writers.

Message extraction accumulates evidence. An explicit correction replaces a
field and invalidates values derived from its previous value. No request may
promote itself to an internal authoritative SourceEnvelope by using these keys
inside structured_json; the executor constructs that envelope from stored trip
state after tenant authorization.

Authority-ranked writes (inv-2 fact-store tranche, 2026-11-03): every slot
write declares its ``authority_level`` and the write is rejected — returned as
a conflict, value preserved — when the stored slot carries strictly higher
authority. A traveler's explicit answer can never regress an operator's
manual correction; a derived value can never clobber a stated fact. Equal
authority = last writer wins within the same actor class.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Optional, Tuple

from src.intake.packet_models import AuthorityLevel


FACT_ALIASES = {
    "origin": "origin_city",
    "destination": "destination_candidates",
    "destinations": "destination_candidates",
    "party": "party_size",
    "travelers": "party_size",
    "traveler_count": "party_size",
    "budget": "budget_raw_text",
    "total_budget": "budget_raw_text",
    "budget_range": "budget_raw_text",
    "dates": "date_window",
    "dateWindow": "date_window",
    "tripPurpose": "trip_purpose",
    "tripPriorities": "trip_priorities",
    "dateFlexibility": "date_flexibility",
}

TRIP_FIELD_FACTS = {
    "origin": "origin_city", "destination": "destination_candidates",
    "budget": "budget_raw_text", "party": "party_size",
    "dateWindow": "date_window", "date_window": "date_window",
    "tripPurpose": "trip_purpose", "trip_purpose": "trip_purpose",
    "tripPriorities": "trip_priorities", "trip_priorities": "trip_priorities",
    "dateFlexibility": "date_flexibility", "date_flexibility": "date_flexibility",
    "party_composition": "party_composition", "pace_preference": "pace_preference",
    "date_year_confidence": "date_year_confidence", "lead_source": "lead_source",
    "activity_provenance": "activity_provenance", "follow_up_due_date": "follow_up_due_date",
}

FACT_DEPENDENTS = {
    "budget_raw_text": ("budget", "budget_min", "budget_max", "budget_currency", "budget_scope", "budget_flexibility"),
    "date_window": ("date_start", "date_end", "date_confidence", "date_year_confidence"),
    "party_size": ("party_composition", "child_ages"),
    "destination_candidates": ("destination_status", "destination_country", "resolved_destination"),
}

AUTHORITATIVE_FACT_SNAPSHOT = "authoritative_fact_snapshot"
CORRECTION_MODES = frozenset({"manual_entry", "traveler_ask_link", "adopted_from_memory"})

_MODE_CHANNEL = {
    "traveler_ask_link": "ask_link",
    "manual_entry": "operator_edit",
    "adopted_from_memory": "memory",
}


def canonical_fact_name(field_name: str) -> str:
    return FACT_ALIASES.get(field_name, field_name)


def slot_authority_rank(slot: Any) -> int:
    """Rank of a stored slot's authority; unknown/missing → weakest (7)."""
    if not isinstance(slot, dict):
        return AuthorityLevel.rank("unknown")
    return AuthorityLevel.rank(str(slot.get("authority_level") or "unknown"))


def explicit_fact_override(
    field_name: str,
    value: Any,
    *,
    source_ref: str,
    mode: str = "manual_entry",
    updated_at: str | None = None,
    previous: dict[str, Any] | None = None,
    authority_level: str = AuthorityLevel.EXPLICIT_USER,
) -> dict[str, Any]:
    """Represent a correction or intentional clear without losing provenance."""
    if mode not in CORRECTION_MODES:
        raise ValueError(
            f"Unknown correction mode '{mode}'; expected one of {sorted(CORRECTION_MODES)}"
        )
    if authority_level not in AuthorityLevel.FACT_LEVELS:
        raise ValueError(
            f"Slot writes require a fact authority level, got '{authority_level}' "
            f"(expected one of {sorted(AuthorityLevel.FACT_LEVELS)})"
        )
    if isinstance(value, str):
        value = value.strip() or None
    if field_name == "party_size" and isinstance(value, str) and value.isdigit():
        value = int(value)
    if field_name == "destination_candidates" and isinstance(value, str):
        value = [value]
    previous = previous if isinstance(previous, dict) else {}
    return {
        "value": deepcopy(value),
        "confidence": 1.0,
        "authority_level": authority_level,
        "epistemic_status": "UNKNOWN" if value is None else "FACT",
        "extraction_mode": mode,
        "evidence_refs": [{
            "envelope_id": source_ref,
            "evidence_type": "manual_entry",
            "excerpt": str(value)[:200] if value is not None else f"Explicitly cleared {field_name}",
            "ref_id": source_ref,
            "confidence": 1.0,
            "metadata": {
                "channel": _MODE_CHANNEL[mode],
                "source_field": field_name,
                "previous_value": deepcopy(previous.get("value")),
                "previous_evidence_refs": deepcopy(previous.get("evidence_refs") or []),
            },
        }],
        "derived_from": [],
        "updated_at": updated_at or datetime.now(timezone.utc).isoformat(),
        "notes": previous.get("notes"),
        "supersedes": previous.get("extraction_mode"),
    }


def try_record_fact_override(
    facts: dict[str, Any], field_name: str, value: Any,
    *, previous: dict[str, Any] | None = None,
    authority_level: str = AuthorityLevel.EXPLICIT_USER,
    **provenance: Any,
) -> Tuple[Optional[dict[str, Any]], Optional[str]]:
    """Authority-guarded canonical slot writer.

    Applies the write (root slot + dependent invalidation) only when the
    stored slot's authority is weaker than or equal to the incoming write.
    Returns ``(slot, None)`` on success or ``(None, conflict_reason)`` when
    the stored slot carries strictly higher authority — the requested value
    is preserved in the conflict reason, never lost silently.
    """
    canonical = canonical_fact_name(field_name)
    existing = facts.get(canonical)
    if not isinstance(previous, dict):
        previous = None
    incoming_rank = AuthorityLevel.rank(authority_level)
    existing_rank = slot_authority_rank(existing if previous is None else previous)
    if incoming_rank > existing_rank:
        kept_value = existing.get("value") if isinstance(existing, dict) else None
        return None, (
            f"'{canonical}' is held by higher authority "
            f"(existing={existing.get('authority_level') if isinstance(existing, dict) else 'unknown'}, "
            f"incoming={authority_level}); kept value preserved: {kept_value!r}"
        )
    slot = explicit_fact_override(
        canonical, value,
        previous=previous or existing,
        authority_level=authority_level,
        **provenance,
    )
    facts[canonical] = slot
    for dependent in FACT_DEPENDENTS.get(canonical, ()):
        invalidated = explicit_fact_override(
            dependent, None, previous=facts.get(dependent),
            authority_level=authority_level,
            **provenance,
        )
        invalidated["extraction_mode"] = "invalidated_by_override"
        invalidated["derived_from"] = [canonical]
        facts[dependent] = invalidated
    return slot, None


def record_fact_override(
    facts: dict[str, Any], field_name: str, value: Any,
    *, previous: dict[str, Any] | None = None,
    authority_level: str = AuthorityLevel.EXPLICIT_USER,
    **provenance: Any,
) -> dict[str, Any]:
    """Guarded canonical write that raises on an authority conflict.

    Writers that expect conflicts to be possible (traveler ask answers over
    operator-corrected slots) should call :func:`try_record_fact_override`
    and report the rejection honestly instead.
    """
    slot, conflict = try_record_fact_override(
        facts, field_name, value,
        previous=previous, authority_level=authority_level, **provenance,
    )
    if conflict:
        raise ValueError(conflict)
    return slot  # type: ignore[return-value]  # conflict is None here
