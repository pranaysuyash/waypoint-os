"""Canonical field replacement semantics shared by intake correction writers.

Message extraction accumulates evidence. An explicit correction replaces a
field and invalidates values derived from its previous value. No request may
promote itself to an internal authoritative SourceEnvelope by using these keys
inside structured_json; the executor constructs that envelope from stored trip
state after tenant authorization.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any


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
CORRECTION_MODES = frozenset({"manual_entry", "traveler_ask_link"})


def canonical_fact_name(field_name: str) -> str:
    return FACT_ALIASES.get(field_name, field_name)


def explicit_fact_override(
    field_name: str,
    value: Any,
    *,
    source_ref: str,
    mode: str = "manual_entry",
    updated_at: str | None = None,
    previous: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Represent a correction or intentional clear without losing provenance."""
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
        "authority_level": "explicit_user",
        "epistemic_status": "UNKNOWN" if value is None else "FACT",
        "extraction_mode": mode,
        "evidence_refs": [{
            "envelope_id": source_ref,
            "evidence_type": "manual_entry",
            "excerpt": str(value)[:200] if value is not None else f"Explicitly cleared {field_name}",
            "ref_id": source_ref,
            "confidence": 1.0,
            "metadata": {
                "channel": "ask_link" if mode == "traveler_ask_link" else "operator_edit",
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


def record_fact_override(
    facts: dict[str, Any], field_name: str, value: Any,
    *, previous: dict[str, Any] | None = None, **provenance: Any,
) -> dict[str, Any]:
    """Write one root correction and invalidate stale dependent projections."""
    canonical = canonical_fact_name(field_name)
    slot = explicit_fact_override(canonical, value, previous=previous or facts.get(canonical), **provenance)
    facts[canonical] = slot
    for dependent in FACT_DEPENDENTS.get(canonical, ()):
        invalidated = explicit_fact_override(
            dependent, None, previous=facts.get(dependent), **provenance
        )
        invalidated["extraction_mode"] = "invalidated_by_override"
        invalidated["derived_from"] = [canonical]
        facts[dependent] = invalidated
    return slot
