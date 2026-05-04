"""
InboxProjectionService — canonical read-model projection for the Inbox.

The Inbox is a specialized view over trips. This service owns the computation
of derived fields (priority, SLA status, flags, customer name) and provides
server-side filter/sort/search/paginate over the projected dataset.

Principles:
- Single source of truth for Inbox logic — not in the frontend, not in the BFF.
- O(n) per-agency projection where n = inbox size (bounded, typically <10k).
- All filter/sort/search operate on the projected set, then paginate.
- "filterCounts" are computed from the FULL projected set, not the paginated page.

Author: Agent
Date: 2026-05-04
"""

import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

# ──────────────────────────────────────────────────────────────────────────────
# Type aliases for clarity
# ──────────────────────────────────────────────────────────────────────────────

InboxTripView = Dict[str, Any]
FilterKey = str  # 'all' | 'at_risk' | 'incomplete' | 'unassigned'
SortKey = str    # 'priority' | 'destination' | 'value' | 'party' | 'dates' | 'sla'
SortDir = str    # 'asc' | 'desc'


# ──────────────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────────────

_STATUS_TO_INBOX_STAGE: Dict[str, str] = {
    "new": "intake",
    "assigned": "options",
    "in_progress": "details",
    "completed": "booking",
    "cancelled": "completed",
    "incomplete": "intake",
    "needs_followup": "options",
    "awaiting_customer_details": "details",
    "snoozed": "completed",
}

_STAGE_NUMBERS: Dict[str, int] = {
    "intake": 1,
    "options": 2,
    "details": 3,
    "review": 4,
    "booking": 5,
    "completed": 6,
}

_SLA_DAYS_ON_TRACK = 4
_SLA_DAYS_AT_RISK = 4
_SLA_DAYS_BREACHED = 7

_DEFAULT_PRIORITY_SCORE = {
    "low": 25,
    "medium": 50,
    "high": 75,
    "critical": 90,
}

_INBOX_TAB_FILTERS = {"all", "at_risk", "incomplete", "unassigned"}


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _as_string(value: Any, fallback: str = "") -> str:
    if isinstance(value, str) and value:
        return value
    if isinstance(value, (int, float, bool)):
        return str(value)
    return fallback


def _as_int(value: Any, fallback: int = 0) -> int:
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if isinstance(value, str):
        cleaned = value.replace("$", "").replace(",", "").replace("k", "000")
        try:
            return int(float(cleaned))
        except (ValueError, TypeError):
            pass
    if isinstance(value, float):
        return int(value)
    return fallback


def _as_record(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {}


def _get_nested(data: Any, path: str, default: Any = None) -> Any:
    """Safe deep property access: obj['a']['b'][0]."""
    if not isinstance(data, dict):
        return default
    parts = path.split(".")
    current: Any = data
    for part in parts:
        if isinstance(current, dict):
            current = current.get(part, default)
            if current is None:
                return default
        else:
            return default
    return current if current is not None else default


def _first_present(*values: Any) -> Any:
    for value in values:
        if value is not None and value != "":
            return value
    return None


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _compute_days_in_current_stage(source: Dict[str, Any], now: Optional[datetime] = None) -> int:
    """How many days since creation or most recent event."""
    if now is None:
        now = _now()
    timestamps: List[str] = []
    created_at = source.get("created_at")
    if isinstance(created_at, str):
        timestamps.append(created_at)

    events = _get_nested(source, "extracted.events", [])
    if isinstance(events, list):
        for event in events:
            ts = _get_nested(event, "timestamp", None)
            if isinstance(ts, str):
                timestamps.append(ts)

    valid = []
    for ts in timestamps:
        try:
            parsed = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            valid.append(parsed.timestamp())
        except (ValueError, TypeError):
            continue

    if not valid:
        return 0

    most_recent = max(valid)
    return max(0, int((now.timestamp() - most_recent) // 86400))


def _compute_sla_status(days: int) -> str:
    if days > _SLA_DAYS_BREACHED:
        return "breached"
    if days > _SLA_DAYS_AT_RISK:
        return "at_risk"
    return "on_track"


def _destination_value(source: Dict[str, Any]) -> str:
    candidates = [
        _get_nested(source, "extracted.facts.destination_candidates.value.0", None),
        _get_nested(source, "extracted.facts.destination_candidates", None),
        _get_nested(source, "extracted.trip_metadata.destination.value.0", None),
        _get_nested(source, "extracted.trip_metadata.destination.value", None),
        _get_nested(source, "extracted.destination.value.0", None),
        _get_nested(source, "extracted.destination.value", None),
        _get_nested(source, "extracted.destination", None),
        source.get("destination"),
    ]
    for cand in candidates:
        if isinstance(cand, str) and cand.strip():
            return cand.strip()
        if isinstance(cand, list) and cand and isinstance(cand[0], str):
            return cand[0].strip()
    return "Unknown"


def _trip_type_value(source: Dict[str, Any]) -> str:
    candidates = [
        _get_nested(source, "extracted.facts.primary_intent.value.0", None),
        _get_nested(source, "extracted.facts.trip_purpose.value.0", None),
        _get_nested(source, "extracted.primary_intent.value.0", None),
        _get_nested(source, "extracted.trip_purpose.value.0", None),
        source.get("trip_type"),
        source.get("tripType"),
    ]
    for cand in candidates:
        if isinstance(cand, str) and cand.strip():
            return cand.strip().lower()
    return "leisure"


def _party_size_value(source: Dict[str, Any]) -> int:
    candidates = [
        _get_nested(source, "extracted.facts.party_profile.value", None),
        _get_nested(source, "extracted.facts.party_size.value", None),
        _get_nested(source, "extracted.trip_metadata.party_profile.size", None),
        _get_nested(source, "extracted.party_size.value", None),
        _get_nested(source, "extracted.party_profile.size", None),
        source.get("party_size"),
        source.get("partySize"),
    ]
    for cand in candidates:
        val = _as_int(cand, 0)
        if val > 0:
            return val
    return 1


def _budget_value(source: Dict[str, Any]) -> int:
    candidates = [
        _get_nested(source, "extracted.facts.budget.value", None),
        _get_nested(source, "extracted.trip_metadata.budget.value", None),
        _get_nested(source, "extracted.budget.value", None),
        _get_nested(source, "extracted.budget", None),
        source.get("budget"),
        source.get("value"),
    ]
    for cand in candidates:
        val = _as_int(cand, 0)
        if val > 0:
            return val
    return 0


def _date_window_value(source: Dict[str, Any]) -> str:
    candidates = [
        _get_nested(source, "extracted.facts.date_window.value", None),
        _get_nested(source, "extracted.trip_metadata.date_window.value", None),
        _get_nested(source, "extracted.date_window.value", None),
        source.get("date_window"),
        source.get("dateWindow"),
    ]
    for cand in candidates:
        if isinstance(cand, str) and cand.strip():
            return cand.strip()
    return "TBD"


def _derive_customer_name(source: Dict[str, Any], trip_id: str) -> str:
    """Best-effort customer name from nested blobs."""
    candidates = [
        _get_nested(source, "raw_input.fixture_id", None),
        _get_nested(source, "raw_input.customer_name", None),
        _get_nested(source, "extracted.facts.customer_name.value.0", None),
        _get_nested(source, "extracted.customer_name.value.0", None),
        _get_nested(source, "extracted.customer_name", None),
        source.get("customer_name"),
        source.get("customerName"),
        source.get("contact_name"),
        source.get("contactName"),
    ]
    for cand in candidates:
        if isinstance(cand, str) and cand.strip():
            return cand.strip()
    return f"Client {trip_id[-6:].upper()}"


def _derive_reference(source: Dict[str, Any], trip_id: str) -> str:
    explicit = _first_present(source.get("reference"), source.get("trip_reference"), source.get("tripReference"))
    if explicit and _as_string(explicit) != trip_id:
        return _as_string(explicit)
    raw = re.sub(r"^trip[-_]", "", trip_id, flags=re.IGNORECASE)
    normalized = re.sub(r"[^a-zA-Z0-9]", "", raw).upper()
    return normalized[:4] or trip_id[-4:].upper()


def _extract_flags(source: Dict[str, Any]) -> List[str]:
    """Derive inbox flags from raw trip structure."""
    flags = set()
    validation = _as_record(source.get("validation"))
    analytics = _as_record(source.get("analytics"))
    decision = _as_record(source.get("decision"))

    # Incomplete flag: validation failed
    is_valid = _first_present(validation.get("isValid"), validation.get("is_valid"), True)
    if is_valid is False:
        flags.add("incomplete")

    # Details unclear: low confidence
    confidence = _as_int(_first_present(decision.get("confidenceScore"), decision.get("confidence_score"), 0), 0) / 100
    if confidence < 0.5:
        flags.add("details_unclear")

    # Needs clarification: decision state asks for followup
    decision_state = _first_present(decision.get("decisionState"), decision.get("decision_state"), "")
    if decision_state == "ASK_FOLLOWUP":
        flags.add("needs_clarification")

    # Hard blockers
    hard_blockers = _first_present(decision.get("hardBlockers"), decision.get("hard_blockers"), [])
    if isinstance(hard_blockers, list) and len(hard_blockers) > 0:
        flags.add("incomplete")

    # Unassigned
    assigned_to = _as_string(_first_present(source.get("assignedTo"), source.get("assigned_to"), source.get("user_id"), ""), "")
    if not assigned_to:
        flags.add("unassigned")

    # High value
    budget = _budget_value(source)
    if budget >= 10000:
        flags.add("high_value")

    return list(flags)


# ──────────────────────────────────────────────────────────────────────────────
# InboxProjectionService
# ──────────────────────────────────────────────────────────────────────────────

class InboxProjectionService:
    """
    Reads raw trip dicts from persistence and projects them into the Inbox view model.

    This separates "what a trip looks like in the Inbox" (a presentation concern)
    from "how a trip is stored in the DB" (a persistence concern).

    Call pattern for the /inbox endpoint:
        1. Fetch ALL inbox trips via TripStore.list_trips(status=INBOX_STATUSES, limit=N)
        2. project_all(trips) -> List[InboxTripView]
        3. apply_filter(..., filter_key) if active 
        4. apply_search(..., query) if q param
        5. apply_sort(..., sort_key, direction)
        6. paginate(...) -> page items + counts
        7. filter_counts(full_projection) -> FilterCounts
    """

    def __init__(self, now: Optional[datetime] = None) -> None:
        self._now = now or _now()

    # -----------------------------------------------------------------------
    # 1. Projection
    # -----------------------------------------------------------------------
    def project_all(self, raw_trips: List[Dict[str, Any]]) -> List[InboxTripView]:
        """Return every trip projected into the InboxTrip view."""
        return [self._project_one(t) for t in raw_trips if isinstance(t, dict)]

    def _project_one(self, source: Dict[str, Any]) -> InboxTripView:
        status = _as_string(source.get("status"), "new")
        stage = _STATUS_TO_INBOX_STAGE.get(status, status) or "options"
        days_in_stage = _compute_days_in_current_stage(source, self._now)
        sla_status = _compute_sla_status(days_in_stage)
        analytics = _as_record(source.get("analytics"))
        validation = _as_record(source.get("validation"))
        decision = _as_record(source.get("decision"))

        # Priority derivation (same rules as bff-trip-adapters)
        priority = "medium"
        priority_score = _DEFAULT_PRIORITY_SCORE[priority]
        if (
            sla_status == "at_risk"
            or analytics.get("requires_review") is True
            or validation.get("is_valid") is False
            or (_as_int(decision.get("confidence_score"), 0) < 50)
        ):
            priority = "high"
            priority_score = _DEFAULT_PRIORITY_SCORE[priority]
        if sla_status == "breached" or analytics.get("escalation_severity") == "critical":
            priority = "critical"
            priority_score = _DEFAULT_PRIORITY_SCORE[priority]

        assigned_to = _as_string(
            _first_present(source.get("assignedTo"), source.get("assigned_to"), source.get("user_id"), ""),
            ""
        ) or None

        assigned_to_name = _as_string(
            _first_present(source.get("assignedToName"), source.get("assigned_to_name")), ""
        ) or None

        trip_id = _as_string(source.get("id"), "")

        return {
            "id": trip_id,
            "reference": _derive_reference(source, trip_id),
            "destination": _destination_value(source),
            "tripType": _trip_type_value(source),
            "partySize": _party_size_value(source),
            "dateWindow": _date_window_value(source),
            "value": _budget_value(source),
            "priority": priority,
            "priorityScore": priority_score,
            "stage": stage,
            "stageNumber": _STAGE_NUMBERS.get(stage, 0),
            "assignedTo": assigned_to,
            "assignedToName": assigned_to_name,
            "submittedAt": _as_string(
                _first_present(source.get("createdAt"), source.get("created_at")), self._now.isoformat()
            ),
            "lastUpdated": _as_string(
                _first_present(source.get("updated_at"), source.get("updatedAt"), source.get("createdAt"), source.get("created_at")),
                self._now.isoformat(),
            ),
            "daysInCurrentStage": days_in_stage,
            "slaStatus": sla_status,
            "customerName": _derive_customer_name(source, trip_id),
            "flags": _extract_flags(source),
        }

    # -----------------------------------------------------------------------
    # 2. Filter
    # -----------------------------------------------------------------------
    def apply_filter(self, trips: List[InboxTripView], filter_key: Optional[str]) -> List[InboxTripView]:
        if not filter_key or filter_key == "all":
            return trips
        if filter_key == "at_risk":
            return [t for t in trips if t.get("slaStatus") == "at_risk"]
        if filter_key == "incomplete":
            return [t for t in trips if "incomplete" in t.get("flags", [])]
        if filter_key == "unassigned":
            return [t for t in trips if not t.get("assignedTo")]
        return trips

    # -----------------------------------------------------------------------
    # 3. Search
    # -----------------------------------------------------------------------
    def apply_search(self, trips: List[InboxTripView], query: Optional[str]) -> List[InboxTripView]:
        if not query or not (q := query.strip().lower()):
            return trips
        return [
            t for t in trips
            if q in t.get("customerName", "").lower()
            or q in t.get("destination", "").lower()
            or q in t.get("reference", "").lower()
            or q in t.get("id", "").lower()
        ]

    # -----------------------------------------------------------------------
    # 4. Sort
    # -----------------------------------------------------------------------
    def apply_sort(self, trips: List[InboxTripView], sort_key: Optional[str], direction: str = "desc") -> List[InboxTripView]:
        sort_fn = {
            "priority": lambda t: (_DEFAULT_PRIORITY_SCORE.get(t.get("priority", "medium"), 50), t.get("priorityScore", 0)),
            "destination": lambda t: t.get("destination", "").lower(),
            "value": lambda t: t.get("value", 0),
            "party": lambda t: t.get("partySize", 0),
            "dates": lambda t: t.get("submittedAt", ""),
            "sla": lambda t: (
                {"breached": 3, "at_risk": 2, "on_track": 1}.get(t.get("slaStatus", ""), 0),
                t.get("daysInCurrentStage", 0),
            ),
        }.get(sort_key, lambda t: (_DEFAULT_PRIORITY_SCORE.get(t.get("priority", "medium"), 50), t.get("priorityScore", 0)))

        reverse = direction.lower() != "asc"
        return sorted(trips, key=sort_fn, reverse=reverse)

    # -----------------------------------------------------------------------
    # 4b. Multi-select filters (composable filter panel)
    # -----------------------------------------------------------------------
    def apply_multi_filters(
        self,
        trips: List[InboxTripView],
        *,
        priorities: Optional[List[str]] = None,
        sla_statuses: Optional[List[str]] = None,
        stages: Optional[List[str]] = None,
        assigned_to: Optional[List[str]] = None,
        min_value: Optional[int] = None,
        max_value: Optional[int] = None,
    ) -> List[InboxTripView]:
        """
        Apply composable multi-select filters to a projected dataset.

        Each filter field is OR within its values (user wants High OR Critical).
        Across fields it is AND (user wants High/Critical AND At Risk/Breached).
        """
        result = trips

        if priorities:
            allowed = {p.lower() for p in priorities}
            result = [t for t in result if t.get("priority", "").lower() in allowed]

        if sla_statuses:
            allowed = {s.lower() for s in sla_statuses}
            result = [t for t in result if t.get("slaStatus", "").lower() in allowed]

        if stages:
            allowed = {s.lower() for s in stages}
            result = [t for t in result if t.get("stage", "").lower() in allowed]

        if assigned_to is not None:
            has_unassigned = "unassigned" in assigned_to
            agent_ids = [a for a in assigned_to if a.lower() != "unassigned"]
            if has_unassigned and agent_ids:
                result = [
                    t for t in result
                    if not t.get("assignedTo") or t.get("assignedTo") in agent_ids
                ]
            elif has_unassigned:
                result = [t for t in result if not t.get("assignedTo")]
            elif agent_ids:
                result = [t for t in result if t.get("assignedTo") in agent_ids]

        if min_value is not None:
            result = [t for t in result if (t.get("value") or 0) >= min_value]
        if max_value is not None:
            result = [t for t in result if (t.get("value") or 0) <= max_value]

        return result

    # -----------------------------------------------------------------------
    # 5. Paginate
    # -----------------------------------------------------------------------
    def paginate(
        self,
        trips: List[InboxTripView],
        page: int = 1,
        limit: int = 20,
    ) -> Tuple[List[InboxTripView], int, int, bool]:
        total = len(trips)
        # Clamp page
        total_pages = max(1, (total + limit - 1) // limit) if total > 0 else 1
        page = max(1, min(page, total_pages)) if total > 0 else 1
        offset = (page - 1) * limit
        items = trips[offset:offset + limit]
        has_more = offset + len(items) < total
        return items, total, offset, has_more

    # -----------------------------------------------------------------------
    # 6. Filter counts (over full dataset)
    # -----------------------------------------------------------------------
    def filter_counts(self, trips: List[InboxTripView]) -> Dict[str, int]:
        all_count = len(trips)
        at_risk = sum(1 for t in trips if t.get("slaStatus") == "at_risk")
        incomplete = sum(1 for t in trips if "incomplete" in t.get("flags", []))
        unassigned = sum(1 for t in trips if not t.get("assignedTo"))
        return {
            "all": all_count,
            "at_risk": at_risk,
            "incomplete": incomplete,
            "unassigned": unassigned,
        }


# ──────────────────────────────────────────────────────────────────────────────
# Convenience builder for the /inbox endpoint
# ──────────────────────────────────────────────────────────────────────────────

def build_inbox_response(
    raw_trips: List[Dict[str, Any]],
    page: int = 1,
    limit: int = 20,
    filter_key: Optional[str] = None,
    sort_key: Optional[str] = None,
    sort_dir: Optional[str] = None,
    search_query: Optional[str] = None,
    *,
    priorities: Optional[List[str]] = None,
    sla_statuses: Optional[List[str]] = None,
    stages: Optional[List[str]] = None,
    assigned_to: Optional[List[str]] = None,
    min_value: Optional[int] = None,
    max_value: Optional[int] = None,
) -> Dict[str, Any]:
    """
    End-to-end projection & pagination for the /inbox endpoint.

    Use when TripStore.list_trips has returned raw dicts but we need
    filterCounts, sorting, and filtering by computed fields.
    """
    svc = InboxProjectionService()
    full_projection = svc.project_all(raw_trips)
    filtered = svc.apply_filter(full_projection, filter_key)
    searched = svc.apply_search(filtered, search_query)
    multi_filtered = svc.apply_multi_filters(
        searched,
        priorities=priorities,
        sla_statuses=sla_statuses,
        stages=stages,
        assigned_to=assigned_to,
        min_value=min_value,
        max_value=max_value,
    )
    sorted_trips = svc.apply_sort(multi_filtered, sort_key, sort_dir or "desc")
    items, total, _, has_more = svc.paginate(sorted_trips, page, limit)
    counts = svc.filter_counts(full_projection)

    return {
        "items": items,
        "total": total,
        "hasMore": has_more,
        "filterCounts": counts,
    }
