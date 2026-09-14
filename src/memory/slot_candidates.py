"""memory.slot_candidates — the sole sanctioned read seam into memory.

ADR-008 item 4 (owner-ratified with amendments, blueprint Addendum 9):
implements the E-D slot spec's ``memory_slot_candidates`` contract. The
E-D invariant is binding: **memory may rank questions, never select
inventory** — candidates may promote an already-known unknown higher in
the ask order (with a rationale tag), never answer an unknown, never
suppress one, and never touch pricing/inventory/selection.

Shadow-first doctrine: callers gate on MEMORY_SLOT_READ_MODE —
  "shadow" (default) → the candidate order is computed and audited, but
                        the caller must not apply it;
  "active"           → promotion-only reordering is applied.

Freshness horizon: an expired fact is DROPPED here (per E-D §2 corollary 2),
not merely down-weighted — stale facts must not be able to promote.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List

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


def read_mode() -> str:
    """Current read mode: "shadow" (default) or "active"."""
    return os.environ.get(_READ_MODE_ENV, "shadow").strip().lower()


def _fact_type(item: Any) -> str:
    meta = getattr(item, "metadata", None) or {}
    return str(meta.get("fact_type", meta.get("type", "default")))


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


def memory_slot_candidates(
    store: Any,
    agency_id: str,
    trip_id: str,
    unknowns: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Compute memory-backed promotion candidates for the unknown ask.

    Returns {"candidates": [{field_name, memory_excerpt, rationale,
    score}], "shadow": bool}. Contract:
      - promotion-only: field_name MUST already exist in `unknowns`;
      - expired/stale facts are dropped, never down-weighted;
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
        excerpt = str(getattr(item, "content", ""))[:120]
        fact_type = _fact_type(item)
        matched = sorted(n for n in unknown_names if _topical(n, excerpt))
        for field_name in matched:
            candidates.append({
                "field_name": field_name,
                "memory_excerpt": excerpt,
                "rationale": f"memory:{fact_type}:{getattr(item, 'id', 'anon')}",
                "score": round(float(score), 4),
            })

    candidates.sort(key=lambda c: -c["score"])
    return {"candidates": candidates, "shadow": mode != "active"}


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
            [(c["field_name"], c["rationale"]) for c in candidates[:5]],
        )
    return unknowns


def apply_active(
    unknowns: List[Dict[str, Any]],
    candidates: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """ACTIVE mode: promotion-only reorder of unknowns by candidate score.
    Never adds, answers, or removes an unknown."""
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
