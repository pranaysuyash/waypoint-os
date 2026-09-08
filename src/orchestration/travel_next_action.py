"""Canonical travel next-best-action projection (E-NBA / AT-07).

Commercial CRM actions (`SEND_FOLLOWUP`, …) stay on `commercial_next_action`.
Travel actions are priority-merged so a weather tick cannot erase disruption.
"""

from __future__ import annotations

from typing import Any, Dict, Mapping, Optional

# Higher wins. CRM tokens sit at the bottom so they never beat a travel action.
ACTION_PRIORITY: Dict[str, int] = {
    "human_safety_review": 100,
    "review_flight_disruption": 90,
    "human_booking_review": 80,
    "collect_booking_details": 80,
    "verify_documents": 70,
    "revalidate_quote_before_payment": 60,
    "revise_proposal_before_review": 50,
    "operator_review_proposal": 50,
    "operator_review_proposal_risks": 50,
    "human_feasibility_review": 40,
    "review_weather_pivots": 40,
    "refresh_destination_intelligence": 40,
    "human_review": 85,
    "collect_missing_facts": 55,
    "continue_proposal": 45,
    "monitor_flights": 20,
    "monitor_weather": 20,
    "monitor_safety_alerts": 20,
    "monitor_pnr": 20,
    "monitor_suppliers": 20,
    "review_pnr_mismatch": 80,
    "review_canonical_travel_objects": 40,
    "review_supplier_risk": 40,
    "SEND_FOLLOWUP": 10,
    "SEND_TARGETED_FOLLOWUP": 10,
    "MOVE_TO_NURTURE": 10,
    "CLOSE_LOST": 10,
    "REQUEST_TOKEN": 10,
    "REQUEST_TOKEN_OR_PLANNING_FEE": 10,
    "SET_BOUNDARY": 10,
    "SET_REVISION_BOUNDARY": 10,
    "REACTIVATE_REPEAT": 10,
    "CHURN_RECOVERY_REACHOUT": 10,
    "PERSONALIZED_REACTIVATION": 10,
    "NONE": 0,
}

_DEFAULT_PRIORITY = 15


def priority_for(action: Optional[str]) -> int:
    if not action:
        return 0
    return ACTION_PRIORITY.get(str(action), _DEFAULT_PRIORITY)


def travel_action_from_decision_state(decision_state: str) -> str:
    """Intake-time travel action — not CRM ghost-risk."""
    if decision_state == "ASK_FOLLOWUP":
        return "collect_missing_facts"
    if decision_state == "STOP_NEEDS_REVIEW":
        return "human_review"
    if decision_state in {
        "PROCEED_INTERNAL_DRAFT",
        "PROCEED_TRAVELER_SAFE",
        "BRANCH_OPTIONS",
    }:
        return "continue_proposal"
    return "review_decision"


def _as_trip_dict(trip: Any) -> Dict[str, Any]:
    if trip is None:
        return {}
    if isinstance(trip, Mapping):
        return dict(trip)
    getter = getattr(trip, "get", None)
    if callable(getter):
        try:
            return dict(trip)
        except Exception:
            return {}
    return {}


def _load_current_trip(trip_repo: Any, trip_id: str) -> Dict[str, Any]:
    getter = getattr(trip_repo, "get_trip", None)
    if callable(getter):
        try:
            loaded = getter(trip_id)
            return _as_trip_dict(loaded)
        except Exception:
            pass
    list_active = getattr(trip_repo, "list_active", None)
    if not callable(list_active):
        return {}
    try:
        for trip in list_active() or []:
            ident = ""
            if isinstance(trip, Mapping):
                ident = str(trip.get("id") or trip.get("trip_id") or "")
            else:
                ident = str(getattr(trip, "id", "") or "")
            if ident == trip_id:
                return _as_trip_dict(trip)
    except Exception:
        return {}
    return {}


def merge_next_action_updates(
    trip_repo: Any,
    trip_id: str,
    updates: Dict[str, Any],
) -> Dict[str, Any]:
    """Keep the highest-priority travel action on the trip.

    Agent snapshots may still carry their own ``operator_next_action``.
    The trip-level field becomes an alias of the winning travel action.
    """
    proposed = updates.get("operator_next_action")
    if not proposed:
        return updates

    current = _load_current_trip(trip_repo, trip_id)
    current_action = current.get("travel_next_action") or current.get("operator_next_action")
    try:
        current_priority = int(current.get("travel_next_action_priority") or 0)
    except (TypeError, ValueError):
        current_priority = 0
    if current_priority <= 0:
        current_priority = priority_for(current_action if isinstance(current_action, str) else None)

    proposed_priority = priority_for(str(proposed))
    merged = dict(updates)
    merged["last_agent_proposal"] = str(proposed)
    if updates.get("last_agent_action"):
        merged["last_agent_proposal_source"] = updates.get("last_agent_action")

    if proposed_priority >= current_priority or not current_action:
        merged["travel_next_action"] = str(proposed)
        merged["travel_next_action_priority"] = proposed_priority
        if updates.get("last_agent_action"):
            merged["travel_next_action_source"] = updates.get("last_agent_action")
        merged["operator_next_action"] = str(proposed)
    else:
        merged.pop("operator_next_action", None)
    return merged


class NextActionAwareTripRepo:
    """TripRepository proxy that enforces travel-NBA priority on writes."""

    def __init__(self, inner: Any):
        self._inner = inner

    def list_active(self) -> list[Any]:
        return self._inner.list_active()

    def get_trip(self, trip_id: str) -> Optional[dict[str, Any]]:
        getter = getattr(self._inner, "get_trip", None)
        if callable(getter):
            return getter(trip_id)
        loaded = _load_current_trip(self._inner, trip_id)
        return loaded or None

    def update_trip(self, trip_id: str, updates: dict[str, Any]) -> Optional[dict[str, Any]]:
        patched = updates
        if isinstance(updates, dict) and updates.get("operator_next_action"):
            patched = merge_next_action_updates(self._inner, trip_id, updates)

        cas = getattr(self._inner, "update_trip_if_version", None)
        advances_priority = isinstance(patched, dict) and "travel_next_action" in patched
        if not callable(cas) or not advances_priority:
            return self._inner.update_trip(trip_id, patched)

        # Part-H P1 (2026-09-07): optimistic compare-and-set with verify-and-
        # heal. The plain read→merge→write sequence let a stale lower-priority
        # write land after ours and erase the winning action (e.g. a weather
        # tick clobbering review_flight_disruption). Each attempt writes
        # against the version just read; afterwards the stored action is
        # re-checked and a loss is re-applied against the fresh state.
        # Residual window: a clobber landing AFTER the final verification is
        # healed by the next writer's loop — full closure requires a
        # store-level priority merge (E-G durable-store endgame).
        intended_action = str(patched.get("travel_next_action") or "")
        intended_priority = int(patched.get("travel_next_action_priority") or 0)
        for _ in range(3):
            current = self._inner.get_trip(trip_id) or {}
            expected_version = current.get("updated_at")
            result = cas(trip_id, patched, expected_version)
            if result is None:
                # Version moved under us: re-merge against the latest state
                # and try again.
                patched = merge_next_action_updates(self._inner, trip_id, updates)
                if "travel_next_action" not in patched:
                    return self._inner.update_trip(trip_id, patched)
                continue

            stored = self._inner.get_trip(trip_id) or {}
            stored_action = stored.get("travel_next_action")
            stored_priority = int(stored.get("travel_next_action_priority") or 0)
            if stored_action == intended_action and stored_priority >= intended_priority:
                return result

            # A concurrent writer landed after ours. Re-merge against the
            # fresh state: if our action still wins, re-apply it; otherwise
            # the higher-priority action holds and we stand down.
            patched = merge_next_action_updates(self._inner, trip_id, updates)
            if "travel_next_action" not in patched:
                return self._inner.update_trip(trip_id, patched)
            intended_action = str(patched.get("travel_next_action") or "")
            intended_priority = int(patched.get("travel_next_action_priority") or 0)

        # Part-J #6: fail CLOSED. Persistent CAS contention must not degrade
        # into a plain stale write that can clobber a newer action — strip the
        # action fields and commit only the contention-safe metadata.
        safe_updates = {
            key: value
            for key, value in patched.items()
            if key
            not in ("travel_next_action", "travel_next_action_priority", "operator_next_action")
        }
        if safe_updates:
            return self._inner.update_trip(trip_id, safe_updates)
        return self._inner.get_trip(trip_id)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)
