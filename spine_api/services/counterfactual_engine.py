"""
spine_api.services.counterfactual_engine — Counterfactual What-If itinerary branching sandbox.

Allows advisors to fork canonical itineraries into alternative scenarios (e.g. swap Rome for Florence,
upgrade all hotels to 5-star, add a 2-day Amalfi extension) and computes side-by-side logistics & pricing diffs.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(slots=True)
class ItineraryDiff:
    price_delta_usd: float
    duration_delta_days: int
    hotels_changed_count: int
    activities_added: List[str] = field(default_factory=list)
    activities_removed: List[str] = field(default_factory=list)
    pacing_impact_summary: str = ""


@dataclass(slots=True)
class ItineraryBranch:
    branch_id: str
    parent_trip_id: str
    branch_name: str
    hypothesis_notes: str
    manifest_data: Dict[str, Any]
    diff_from_parent: Optional[ItineraryDiff] = None
    status: str = "draft"  # "draft" | "promoted_to_canonical" | "discarded"


def create_counterfactual_branch(
    parent_trip_id: str,
    branch_name: str,
    hypothesis_notes: str,
    base_manifest: Dict[str, Any],
) -> ItineraryBranch:
    """Create an isolated, fork of a canonical itinerary for what-if experimentation."""
    branch_id = f"fork_{parent_trip_id}_{abs(hash(branch_name)) % 10000}"
    forked_data = copy.deepcopy(base_manifest)
    return ItineraryBranch(
        branch_id=branch_id,
        parent_trip_id=parent_trip_id,
        branch_name=branch_name,
        hypothesis_notes=hypothesis_notes,
        manifest_data=forked_data,
        diff_from_parent=None,
        status="draft",
    )


def compute_branch_diff(
    canonical_manifest: Dict[str, Any],
    forked_manifest: Dict[str, Any],
) -> ItineraryDiff:
    """Compute mathematical and logistic delta between canonical trip and forked branch."""
    can_price = float(canonical_manifest.get("total_price_usd", 0.0))
    fork_price = float(forked_manifest.get("total_price_usd", 0.0))
    price_delta = round(fork_price - can_price, 2)

    can_days = int(canonical_manifest.get("duration_days", 0))
    fork_days = int(forked_manifest.get("duration_days", 0))
    days_delta = fork_days - can_days

    can_activities = set(canonical_manifest.get("activity_titles", []))
    fork_activities = set(forked_manifest.get("activity_titles", []))

    added = sorted(list(fork_activities - can_activities))
    removed = sorted(list(can_activities - fork_activities))

    pacing = (
        f"Price delta: {('+' if price_delta >= 0 else '')}${price_delta:,.2f}; "
        f"Duration delta: {('+' if days_delta >= 0 else '')}{days_delta} days; "
        f"{len(added)} activity(ies) added, {len(removed)} removed."
    )

    return ItineraryDiff(
        price_delta_usd=price_delta,
        duration_delta_days=days_delta,
        hotels_changed_count=1 if canonical_manifest.get("hotel_name") != forked_manifest.get("hotel_name") else 0,
        activities_added=added,
        activities_removed=removed,
        pacing_impact_summary=pacing,
    )
