import json
from pathlib import Path
from typing import Dict, List, Any
import logging
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)

VALID_STAGES = ["new", "assigned", "in_progress", "completed", "cancelled"]

SLA_THRESHOLDS = {
    "new": timedelta(hours=4),
    "assigned": timedelta(hours=24),
}


class DashboardAggregator:
    """
    Canonical SSOT for dashboard metrics.
    Aggregates data from TripStore and returns a unified state.
    ALL business logic lives here. The frontend is a pure projection layer.
    """

    @staticmethod
    def get_unified_state() -> Dict[str, Any]:
        try:
            from spine_api.persistence import TripStore, AuditStore
        except ImportError:
            import sys
            import os
            sys.path.append(os.path.join(os.getcwd(), "spine-api"))
            import persistence
            TripStore = persistence.TripStore
            AuditStore = persistence.AuditStore

        all_trips = TripStore.list_trips(limit=10000)
        trips = [t for t in all_trips if t.get("id")]
        canonical_total = len(trips)
        stages = {stage: 0 for stage in VALID_STAGES}
        sla_breached = 0
        orphans = []

        now = datetime.now(timezone.utc)

        for trip in trips:
            status = trip.get("status")
            trip_id = trip.get("id", "missing_id")

            if status in VALID_STAGES:
                stages[status] += 1
            else:
                orphans.append({
                    "id": trip_id,
                    "status": status,
                    "created_at": trip.get("created_at")
                })

            created_at_str = trip.get("created_at")
            if created_at_str:
                try:
                    if created_at_str.endswith('Z'):
                        created_at_str = created_at_str.replace('Z', '+00:00')
                    created_at = datetime.fromisoformat(created_at_str)

                    if created_at.tzinfo is None:
                        created_at = created_at.replace(tzinfo=timezone.utc)

                    age = now - created_at

                    if status == "new" and age > SLA_THRESHOLDS["new"]:
                        sla_breached += 1
                    elif status == "assigned" and age > SLA_THRESHOLDS["assigned"]:
                        sla_breached += 1
                except (ValueError, TypeError):
                    pass

        sum_stages = sum(stages.values())

        if sum_stages + len(orphans) != canonical_total:
            logger.error(f"Critical Integrity Failure: total={canonical_total}, stages={sum_stages}, orphans={len(orphans)}")

        return {
            "canonical_total": canonical_total,
            "stages": stages,
            "sla_breached": sla_breached,
            "orphans": orphans,
            "integrity_meta": {
                "sum_stages": sum_stages,
                "orphan_count": len(orphans),
                "consistent": (sum_stages + len(orphans) == canonical_total),
                "last_sync": now.isoformat()
            },
            "systemic_errors": DashboardAggregator._get_top_errors(AuditStore)
        }

    @staticmethod
    def get_dashboard_stats() -> Dict[str, Any]:
        """
        Compute dashboard stat cards. This replaces all frontend Math/filter logic.

        active: completed trips (booked/delivered)
        pending_review: trips not yet completed
        ready_to_book: trips in strategy/output stages (weighted)
        needs_attention: trips with SLA risk or low-quality signals
        """
        try:
            from spine_api.persistence import TripStore
        except ImportError:
            import sys
            import os
            sys.path.append(os.path.join(os.getcwd(), "spine-api"))
            import persistence
            TripStore = persistence.TripStore

        all_trips = TripStore.list_trips(limit=10000)
        trips = [t for t in all_trips if t.get("id")]

        now = datetime.now(timezone.utc)

        completed = 0
        ready_to_book = 0
        needs_attention = 0

        for trip in trips:
            status = trip.get("status", "")
            meta = trip.get("meta", {})
            stage = meta.get("stage", "")
            analytics = trip.get("analytics", {})
            quality_score = analytics.get("quality_score", 100)

            if status == "completed":
                completed += 1

            if stage in ("strategy", "output"):
                ready_to_book += 1

            created_at_str = trip.get("created_at")
            if created_at_str:
                try:
                    if created_at_str.endswith('Z'):
                        created_at_str = created_at_str.replace('Z', '+00:00')
                    created_at = datetime.fromisoformat(created_at_str)
                    if created_at.tzinfo is None:
                        created_at = created_at.replace(tzinfo=timezone.utc)

                    age_hours = (now - created_at).total_seconds() / 3600

                    if status == "new" and age_hours > 3:
                        needs_attention += 1
                    elif status == "assigned" and age_hours > 18:
                        needs_attention += 1
                    elif quality_score < 50:
                        needs_attention += 1
                except (ValueError, TypeError):
                    pass

        pending_review = len(trips) - completed

        return {
            "active": completed,
            "pending_review": max(0, pending_review),
            "ready_to_book": ready_to_book,
            "needs_attention": min(needs_attention, max(0, pending_review)),
        }

    @staticmethod
    def get_trip_sla_status(trip: Dict[str, Any]) -> str:
        """
        Compute SLA status for a single trip.

        Returns: "on_track" | "at_risk" | "breached"

        Rules:
          - new: breach at 4h, at_risk at 3h
          - assigned: breach at 24h, at_risk at 18h
          - in_progress: breach at 72h, at_risk at 60h
          - completed/cancelled: always "on_track"
        """
        status = trip.get("status", "")
        if status in ("completed", "cancelled"):
            return "on_track"

        thresholds = {
            "new": (3.0, 4.0),
            "assigned": (18.0, 24.0),
            "in_progress": (60.0, 72.0),
        }

        limit = thresholds.get(status)
        if not limit:
            return "on_track"

        at_risk_h, breach_h = limit
        created_at_str = trip.get("created_at")
        if not created_at_str:
            return "on_track"

        try:
            if created_at_str.endswith('Z'):
                created_at_str = created_at_str.replace('Z', '+00:00')
            created_at = datetime.fromisoformat(created_at_str)
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)

            age_hours = (datetime.now(timezone.utc) - created_at).total_seconds() / 3600

            if age_hours > breach_h:
                return "breached"
            elif age_hours > at_risk_h:
                return "at_risk"
            return "on_track"
        except (ValueError, TypeError):
            return "on_track"

    @staticmethod
    def get_suitability_signals(trip: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract suitability risk signals from a trip for frontend rendering.
        All severity classification happens here — frontend just displays.
        """
        signals = []
        decision = trip.get("decision", {})
        analytics = trip.get("analytics", {})

        flags = decision.get("suitability_flags", [])
        for flag in flags:
            severity = flag.get("severity", "low")
            signals.append({
                "trip_id": trip.get("id", ""),
                "flag_type": flag.get("flag", flag.get("flag_type", "unknown")),
                "severity": severity,
                "reason": flag.get("reason", ""),
                "confidence": min(100, max(0, float(flag.get("confidence", 0)))),
            })

        margin = analytics.get("margin_pct", 100)
        if margin < 10:
            signals.append({
                "trip_id": trip.get("id", ""),
                "flag_type": "low_margin",
                "severity": "high",
                "reason": f"Margin at {margin}% (below 10% threshold)",
                "confidence": 95.0,
            })

        quality = analytics.get("quality_score", 100)
        if quality < 50:
            signals.append({
                "trip_id": trip.get("id", ""),
                "flag_type": "low_quality",
                "severity": "warning",
                "reason": f"Quality score {quality} (below 50 threshold)",
                "confidence": 90.0,
            })

        return signals

    @staticmethod
    def _get_top_errors(AuditStore, limit: int = 5) -> List[Dict]:
        try:
            events = AuditStore.get_events(limit=500)
            error_counts = {}

            for event in events:
                if event.get("type") == "review_action_applied":
                    category = event.get("details", {}).get("error_category")
                    if category:
                        error_counts[category] = error_counts.get(category, 0) + 1

            sorted_errors = sorted(
                [{"category": k, "count": v} for k, v in error_counts.items()],
                key=lambda x: x["count"],
                reverse=True
            )
            return sorted_errors[:limit]
        except Exception as e:
            logger.error(f"Failed to aggregate systemic errors: {e}")
            return []
