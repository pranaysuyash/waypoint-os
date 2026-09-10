"""
src/memory/feedback_bridge.py — Feedback-to-Memory Event-Class Bridge (E-10).

Translates post-trip feedback events into durable memory writes under the
event-class rules from Docs/exploration/E10_SURVEY_MEMORY_FEEDBACK_LOOP_2026-09-02.md:

- Traveler free text → explicit correction: TRAVELER_DIRECT, 365d half-life,
  written to the traveler's customer-memory entity (cust_ convention).
- Supplier ratings → supplier outcomes: supplier-scoped entity namespace
  (`supplier::{name}`), aggregate across trips, 365d half-life.
- NPS (agency-level) → deliberately NOT a memory write: it feeds scorecard
  aggregation only. NPS measures the agency, not a durable preference.
- Empty text / zero ratings → never-write class: the bridge skips rather
  than persisting noise.

Every write goes through MemoryStore.ingest_memory so the eligibility gate,
sanitizer, provenance, and supersession apply — the bridge never writes
around the store.

Trust note (F-13): these writes are durable-store records. They do NOT
influence suitability scoring until retrieval is trust-weighted at the two
F-13 slot points (retriever.py blend + legacy hydrate path).
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from src.memory.models import MemorySourceType
from src.memory.store import MemoryStore

logger = logging.getLogger("src.memory.feedback_bridge")

TRAVELER_ENTITY_PREFIX = "cust_"
SUPPLIER_ENTITY_PREFIX = "supplier::"

# Half-life (days) per event class — outcome/correction class sits between
# SEMANTIC's 730d (durable preferences) and the 90d implicit-signal horizon.
OUTCOME_HALF_LIFE_DAYS = 365.0
CORRECTION_HALF_LIFE_DAYS = 365.0


@dataclass
class FeedbackMemoryWriteResult:
    persisted: List[Dict[str, Any]] = field(default_factory=list)
    skipped: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def wrote_anything(self) -> bool:
        return bool(self.persisted)


def traveler_entity_for(contact_email: Optional[str], contact_phone: Optional[str], trip_id: str) -> str:
    """Derive the customer entity id using the cust_ convention from
    customer_memory.py (normalized email → phone → name)."""
    if contact_email:
        return f"{TRAVELER_ENTITY_PREFIX}{contact_email.strip().lower()}"
    if contact_phone:
        digits = re.sub(r"[^0-9]", "", contact_phone)
        if digits:
            return f"{TRAVELER_ENTITY_PREFIX}{digits}"
    return f"{TRAVELER_ENTITY_PREFIX}trip_{trip_id}"


def bridge_feedback_response_to_memory(
    store: MemoryStore,
    agency_id: str,
    trip_id: str,
    response: Dict[str, Any],
    actor_id: Optional[str] = None,
) -> FeedbackMemoryWriteResult:
    """Translate a stored post-trip feedback response into durable memory
    writes under the event-class rules.

    `response` is the validated feedback response payload:
      {free_text?, nps_score?, supplier_ratings?: [{supplier_name, category?, score}]}
    """
    result = FeedbackMemoryWriteResult()
    if not isinstance(response, dict):
        return result

    traveler_entity = traveler_entity_for(
        response.get("respondent_email"),
        response.get("respondent_phone"),
        trip_id,
    )

    free_text = str(response.get("free_text") or "").strip()
    if free_text:
        item, status = store.ingest_memory(
            agency_id=agency_id,
            entity_id=traveler_entity,
            raw_text=f"Post-trip feedback correction: {free_text}",
            source_type=MemorySourceType.TRAVELER_DIRECT,
            payload={"trip_id": trip_id, "free_text": free_text, "event_class": "traveler_correction"},
            source_ref_id=trip_id,
            actor_id=actor_id,
            category_hint="preference",
            explicit_confidence=0.8,
            half_life_days=CORRECTION_HALF_LIFE_DAYS,
        )
        if item is not None:
            result.persisted.append(
                {"event_class": "traveler_correction", "entity_id": traveler_entity, "memory_id": item.memory_id}
            )
        else:
            result.skipped.append({"event_class": "traveler_correction", "reason": status})

    for rating in response.get("supplier_ratings") or []:
        supplier_name = str((rating or {}).get("supplier_name") or "").strip()
        score = (rating or {}).get("score")
        if not supplier_name or score is None:
            result.skipped.append({"event_class": "supplier_outcome", "reason": "missing supplier_name or score"})
            continue
        supplier_entity = f"{SUPPLIER_ENTITY_PREFIX}{supplier_name.strip().lower()}"
        item, status = store.ingest_memory(
            agency_id=agency_id,
            entity_id=supplier_entity,
            raw_text=(
                f"Post-trip outcome: {supplier_name} rated {score}/5 "
                f"(trip {trip_id}, category {(rating or {}).get('category') or 'general'})."
            ),
            source_type=MemorySourceType.TRAVELER_DIRECT,
            payload={
                "trip_id": trip_id,
                "supplier_name": supplier_name,
                "score": score,
                "event_class": "supplier_outcome",
            },
            source_ref_id=trip_id,
            actor_id=actor_id,
            category_hint="supplier_outcome",
            explicit_confidence=0.75,
            half_life_days=OUTCOME_HALF_LIFE_DAYS,
        )
        if item is not None:
            result.persisted.append(
                {"event_class": "supplier_outcome", "entity_id": supplier_entity, "memory_id": item.memory_id}
            )
        else:
            result.skipped.append({"event_class": "supplier_outcome", "reason": status})

    if not result.persisted and not result.skipped:
        result.skipped.append({"event_class": "none", "reason": "empty feedback response"})

    logger.info(
        "Feedback bridge trip=%s: %d persisted, %d skipped",
        trip_id,
        len(result.persisted),
        len(result.skipped),
    )
    return result
