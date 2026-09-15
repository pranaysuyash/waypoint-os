"""memory.slot_candidates — the sole sanctioned read seam into memory.

ADR-008 item 4 (owner-ratified with amendments, blueprint Addendum 9):
implements the E-D slot spec's ``memory_slot_candidates`` contract. The
E-D invariant is binding: **memory may rank questions, never select
inventory** — candidates may promote an already-known unknown higher in
the ask order (with a rationale tag), never answer an unknown, never
suppress one, and never touch pricing/inventory/selection.

Suitability scoring is an explicit E-D NON-SLOT (§4): memory must never
reach suitability/inventory selection at all. Enforcement is the
import-containment test in tests/test_memory_slot_wiring.py plus the
trust/boundary guarantees below — cross-trip preferences can only reach
another trip through THIS seam, promotion-only, trust-weighted, and
shadow-gated.

Shadow-first doctrine: callers gate on MEMORY_SLOT_READ_MODE —
  "shadow" (default) → the candidate order is computed and audited, but
                        the caller must not apply it;
  "active"           → promotion-only reordering is applied.

Freshness horizon: an expired fact is DROPPED here (per E-D §2 corollary 2),
not merely down-weighted — stale facts must not be able to promote.

Trust weighting (FND-0230): influence is proportional to trust. Every
candidate records its source_type, coarse trust_class, and trust_weight;
the influence score is the retrieval blend scaled by the trust weight, so
a low-trust memory can never outrank an explicit traveler statement at
equal similarity/recency. Rationale tags carry the trust class so every
memory-derived influence is visible in the decision rationale (E-D §2
corollary 3).

Cross-trip isolation: trip-scoped facts (episodic trip events tied to a
specific trip) promote only that same trip's unknowns — a memory from
trip A never steers trip B. Entity-scoped facts (traveler profile
preferences, supplier outcomes) are global by design and remain eligible.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from src.memory.models import (
    SOURCE_CONFIDENCE_WEIGHTS,
    SOURCE_TRUST_CLASS,
    SourceTrustClass,
    TRUST_CLASS_WEIGHTS,
)

logger = logging.getLogger("spine_api.memory.slot_candidates")

# Per-fact-type freshness horizons (days). Expired → dropped, not
# down-weighted (E-D §2 corollary 2).
_FRESHNESS_HORIZON_DAYS: Dict[str, int] = {
    "preference": 365,
    "constraint": 180,
    "fact": 90,
    "default": 90,
}

_READ_MODE_ENV = "MEMORY_SLOT_READ_MODE"

# Real-store categories that map onto E-D fact types for the freshness
# horizon. BaseMemoryItem has no ``metadata`` dict, so the horizon is
# derived from the memory category (falling back to the duck-typed
# metadata fact_type used by test fakes).
_CATEGORY_FACT_TYPE: Dict[str, str] = {
    "seating_preference": "preference",
    "traveler_preference": "preference",
    "agency_preference": "preference",
    "general_affinity": "preference",
    "dietary_safety": "constraint",
    "credentials_loyalty": "constraint",
    "supplier_outcome": "fact",
    "trip_event": "fact",
    "agency_policy": "fact",
    "procedural_rule": "fact",
}

# Trip-scoped fact classes: these describe ONE trip, not the traveler.
# They may only promote unknowns for their own trip.
_TRIP_SCOPED_CATEGORIES = {"trip_event"}


def read_mode() -> str:
    """Current read mode: "shadow" (default) or "active"."""
    return os.environ.get(_READ_MODE_ENV, "shadow").strip().lower()


def _item_attr(item: Any, *names: str, default: Any = None) -> Any:
    """Read the first existing attribute — supports both the real
    BaseMemoryItem shape and duck-typed test fakes."""
    for name in names:
        value = getattr(item, name, None)
        if value is not None:
            return value
    return default


def _fact_type(item: Any) -> str:
    meta = getattr(item, "metadata", None) or {}
    if meta.get("fact_type") or meta.get("type"):
        return str(meta.get("fact_type", meta.get("type")))
    category = str(getattr(item, "category", "") or "").lower()
    return _CATEGORY_FACT_TYPE.get(category, "default")


def _item_trip_id(item: Any) -> Optional[str]:
    """The trip a memory was recorded for, if it is trip-scoped."""
    payload = getattr(item, "payload", None)
    if isinstance(payload, dict) and payload.get("trip_id"):
        return str(payload["trip_id"])
    trip_attr = getattr(item, "trip_id", None)
    if trip_attr:
        return str(trip_attr)
    provenance = getattr(item, "provenance", None)
    ref = getattr(provenance, "source_ref_id", None) if provenance is not None else None
    # supplier_/cust_ entity-scoped namespaces are not trip refs; a bare
    # trip id ref means the fact was recorded against that trip.
    if ref and not str(ref).startswith(("supplier::", "cust_")):
        return str(ref)
    return None


def _is_cross_trip(item: Any, trip_id: str) -> bool:
    """True when a trip-scoped fact belongs to a DIFFERENT trip (or when
    the requesting trip is unknown — such a fact cannot be proven topical
    to the current ask, so it is excluded conservatively)."""
    category = str(getattr(item, "category", "") or "").lower()
    if category not in _TRIP_SCOPED_CATEGORIES:
        return False
    item_trip = _item_trip_id(item)
    if trip_id:
        return item_trip is not None and item_trip != trip_id
    return True


def _is_expired(item: Any, now: datetime) -> bool:
    horizon_days = _FRESHNESS_HORIZON_DAYS.get(_fact_type(item), 90)
    created = getattr(item, "created_at", None)
    if created is None:
        return False  # cannot date the fact → keep, retriever score governs
    if isinstance(created, str):
        try:
            created = datetime.fromisoformat(created.replace("Z", "+00:00"))
        except ValueError:
            return False
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    age_days = (now - created).total_seconds() / 86400.0
    return age_days > horizon_days


def _source_type_of(item: Any):
    """The item's MemorySourceType (None when absent/duck-typed fake)."""
    provenance = getattr(item, "provenance", None)
    source_type = getattr(provenance, "source_type", None)
    try:
        from src.memory.models import MemorySourceType

        if isinstance(source_type, MemorySourceType):
            return source_type
    except Exception:  # pragma: no cover - models always importable here
        pass
    return None


def _trust_of(item: Any) -> Tuple[str, float]:
    """(source_type_value, trust_weight) for a memory item.

    Trust is dual-sourced: the source hierarchy weight (per-source-type)
    and the coarse trust-class weight (explicit_user > derived >
    agent_inferred > system_default). The binding constraint is the
    class weight — a derived/agent_inferred memory can never carry
    explicit-user authority into the ask order.
    """
    source_type = _source_type_of(item)
    if source_type is None:
        return "unknown", TRUST_CLASS_WEIGHTS[SourceTrustClass.SYSTEM_DEFAULT]
    trust_class = SOURCE_TRUST_CLASS[source_type]
    weight = min(
        TRUST_CLASS_WEIGHTS[trust_class],
        SOURCE_CONFIDENCE_WEIGHTS[source_type],
    )
    return source_type.value, weight


def memory_slot_candidates(
    store: Any,
    agency_id: str,
    trip_id: str,
    unknowns: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Compute memory-backed promotion candidates for the unknown ask.

    Returns {"candidates": [{field_name, memory_excerpt, rationale,
    score, source_type, trust_class, trust_weight, blend_score}],
    "shadow": bool}. Contract:
      - promotion-only: field_name MUST already exist in `unknowns`;
      - expired/stale facts are dropped, never down-weighted;
      - trip-scoped facts from another trip never promote (cross-trip
        isolation; unknown current trip → trip-scoped facts excluded);
      - influence is trust-weighted (FND-0230);
      - tombstoned/superseded items are filtered upstream by the store.
    """
    mode = read_mode()
    now = datetime.now(timezone.utc)
    unknown_names = {u.get("field_name") for u in unknowns if isinstance(u, dict)}

    candidates: List[Dict[str, Any]] = []
    try:
        results = store.query_memories(
            agency_id=agency_id,
            query=" ".join(sorted(n for n in unknown_names if n)),
            top_k=10,
        )
    except Exception:
        logger.warning("slot candidate query failed; returning none", exc_info=True)
        return {"candidates": [], "shadow": mode != "active"}

    for item, score in results:
        if _is_expired(item, now):
            continue
        if _is_cross_trip(item, trip_id):
            logger.debug(
                "slot candidate dropped: cross-trip fact %s",
                _item_attr(item, "memory_id", "id", default="anon"),
            )
            continue
        excerpt = str(_item_attr(item, "summary", "content", default=""))[:120]
        fact_type = _fact_type(item)
        source_type, trust_weight = _trust_of(item)
        trust_class = _trust_class_label(item)
        # Influence proportional to trust (FND-0230): the retrieval blend
        # already carries provenance confidence; the trust-class weight
        # bounds the TOTAL influence so a low-trust memory cannot outrank
        # an explicit traveler statement at equal similarity/recency.
        blend_score = float(score)
        influence = round(blend_score * trust_weight, 4)
        matched = sorted(n for n in unknown_names if _topical(n, excerpt))
        for field_name in matched:
            candidates.append({
                "field_name": field_name,
                "memory_excerpt": excerpt,
                "rationale": (
                    f"memory:{fact_type}:{source_type}:"
                    f"{_item_attr(item, 'memory_id', 'id', default='anon')}"
                ),
                "score": influence,
                "blend_score": round(blend_score, 4),
                "source_type": source_type,
                "trust_class": trust_class,
                "trust_weight": trust_weight,
            })

    candidates.sort(key=lambda c: -c["score"])
    return {"candidates": candidates, "shadow": mode != "active"}


def _trust_class_label(item: Any) -> str:
    """Coarse trust class label for audit/rationale surfaces."""
    source_type = _source_type_of(item)
    if source_type is not None:
        return SOURCE_TRUST_CLASS[source_type].value
    return SourceTrustClass.SYSTEM_DEFAULT.value


def _topical(field_name: str, excerpt: str) -> bool:
    """Loose topicality: an unknown may be promoted only if the memory
    excerpt plausibly speaks to it. Conservative token overlap — never
    invents an answer, only ranks an existing unknown."""
    tokens = {t for t in field_name.lower().split("_") if len(t) > 3}
    if not tokens:
        return False
    excerpt_lower = excerpt.lower()
    return any(token in excerpt_lower for token in tokens)


def apply_shadow(
    unknowns: List[Dict[str, Any]],
    candidates: List[Dict[str, Any]],
    *,
    agency_id: str,
    trip_id: str,
) -> List[Dict[str, Any]]:
    """Emit the audit record for a shadow evaluation. In shadow mode the
    RETURNED order is unchanged (promotion-only influence requires mode
    "active"); the audit event records what WOULD have moved so the
    promotion-value metric can be measured."""
    if candidates:
        logger.info(
            "memory_slot_promotion agency=%s trip=%s shadow=%s promoted=%s",
            agency_id, trip_id, read_mode() != "active",
            [
                (c["field_name"], c["rationale"], c.get("trust_class"))
                for c in candidates[:5]
            ],
        )
    return unknowns


def apply_active(
    unknowns: List[Dict[str, Any]],
    candidates: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """ACTIVE mode: promotion-only reorder of unknowns by trust-weighted
    candidate score. Never adds, answers, or removes an unknown."""
    if not candidates:
        return unknowns
    score_by_name = {c["field_name"]: c["score"] for c in candidates}
    ordered = sorted(
        enumerate(unknowns),
        key=lambda pair: -score_by_name.get(
            pair[1].get("field_name") if isinstance(pair[1], dict) else None, 0.0
        ),
    )
    return [u for _, u in ordered]
