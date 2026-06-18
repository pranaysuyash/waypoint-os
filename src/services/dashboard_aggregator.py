import json
import time
import threading
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import logging
from datetime import datetime, timezone, timedelta

from spine_api.persistence import AuditStore, TripStore

logger = logging.getLogger(__name__)

VALID_STAGES = ["new", "assigned", "in_progress", "completed", "cancelled", "incomplete"]

SLA_THRESHOLDS = {
    "new": timedelta(hours=4),
    "assigned": timedelta(hours=24),
}


def _resolve_sla_thresholds(agency_id: Optional[str] = None) -> Dict[str, timedelta]:
    """Resolve SLA thresholds from SupportSettings, falling back to defaults.

    The dashboard aggregator reads the agency's configured SLA targets so that
    operator-configured response times are enforced at runtime instead of using
    hardcoded values.
    """
    defaults = dict(SLA_THRESHOLDS)
    if agency_id is None:
        return defaults
    try:
        from src.intake.config.agency_settings import AgencySettingsStore
        settings = AgencySettingsStore.load(agency_id)
        support = getattr(settings, "support", None)
        if support is None:
            return defaults
        # Map SupportSettings SLA hours → dashboard thresholds
        default_h = getattr(support, "default_response_sla_hours", 24)
        urgent_h = getattr(support, "urgent_response_sla_hours", 4)
        # 'new' trips use urgent SLA (first response), 'assigned' use default
        defaults["new"] = timedelta(hours=max(1, urgent_h))
        defaults["assigned"] = timedelta(hours=max(1, default_h))
    except Exception:
        logger.debug("Failed to load SupportSettings for SLA thresholds, using defaults")
    return defaults

# ---------------------------------------------------------------------------
# Simple in-memory TTL cache for unified-state and dashboard-stats.
# Keyed by agency_id (None = global). Avoids redundant DB round-trips on
# every page navigation — staleTime on the frontend is already 30s.
# ---------------------------------------------------------------------------
_CACHE_TTL_SECONDS = 30
_cache_lock = threading.Lock()
_unified_state_cache: Dict[Optional[str], Tuple[float, Dict]] = {}
_dashboard_stats_cache: Dict[Optional[str], Tuple[float, Dict]] = {}


def clear_dashboard_cache() -> None:
    """Evict all cached dashboard results. Use in tests or after bulk mutations."""
    with _cache_lock:
        _unified_state_cache.clear()
        _dashboard_stats_cache.clear()


class DashboardAggregator:
    """
    Canonical SSOT for dashboard metrics.
    Aggregates data from TripStore and returns a unified state.
    ALL business logic lives here. The frontend is a pure projection layer.
    """

    @staticmethod
    def get_unified_state(agency_id: str = None) -> Dict[str, Any]:
        # --- TTL cache check ---
        with _cache_lock:
            cached = _unified_state_cache.get(agency_id)
            if cached is not None:
                cached_at, cached_value = cached
                if time.monotonic() - cached_at < _CACHE_TTL_SECONDS:
                    return cached_value

        t0 = time.perf_counter()

        # Use list_trip_summaries: avoids fetching heavy JSONB blobs (itinerary,
        # notes, messages) — we only need status, id, created_at for this aggregation.
        all_trips = TripStore.list_trip_summaries(limit=10000, agency_id=agency_id)
        t1 = time.perf_counter()
        logger.warning(
            "[perf] unified-state list_trip_summaries agency=%s trips=%d elapsed=%.3fs",
            agency_id, len(all_trips), t1 - t0
        )

        trips = [t for t in all_trips if t.get("id")]
        canonical_total = len(trips)
        stages = {stage: 0 for stage in VALID_STAGES}
        sla_breached = 0
        orphans = []

        # Resolve SLA thresholds from SupportSettings (falls back to defaults)
        sla_thresholds = _resolve_sla_thresholds(agency_id)

        now = datetime.now(timezone.utc)

        # Pipeline stage breakdown — aggregate by trip stage (meta.stage or status)
        pipeline_stages: Dict[str, int] = {}
        pending_review_count = 0

        # Per-status review counts (all trips that have interacted with the review system)
        review_counts: Dict[str, int] = {
            "pending": 0,
            "approved": 0,
            "rejected": 0,
            "escalated": 0,
            "revision_needed": 0,
        }
        total_pending_review_value = 0

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

            # Pipeline stage breakdown (meta.stage or status fallback)
            stage = trip.get("stage") or trip.get("meta", {}).get("stage") or status or "unknown"
            pipeline_stages[stage] = pipeline_stages.get(stage, 0) + 1

            # Review counts — compute from analytics.review_status and requires_review
            analytics = trip.get("analytics")
            if isinstance(analytics, dict):
                if analytics.get("requires_review") is True:
                    pending_review_count += 1
                    # Sum value of pending reviews for the summary card
                    packet = trip.get("packet") or {}
                    budget = packet.get("budget") or {}
                    total_pending_review_value += budget.get("value", 0)

                review_status = analytics.get("review_status")
                if review_status in review_counts:
                    review_counts[review_status] += 1

            created_at_str = trip.get("created_at")
            if created_at_str:
                try:
                    if isinstance(created_at_str, datetime):
                        created_at = created_at_str
                        if created_at.tzinfo is None:
                            created_at = created_at.replace(tzinfo=timezone.utc)
                    else:
                        if created_at_str.endswith('Z'):
                            created_at_str = created_at_str.replace('Z', '+00:00')
                        created_at = datetime.fromisoformat(created_at_str)
                        if created_at.tzinfo is None:
                            created_at = created_at.replace(tzinfo=timezone.utc)

                    age = now - created_at

                    if status == "new" and age > sla_thresholds["new"]:
                        sla_breached += 1
                    elif status == "assigned" and age > sla_thresholds["assigned"]:
                        sla_breached += 1
                except (ValueError, TypeError):
                    pass

        sum_stages = sum(stages.values())

        if sum_stages + len(orphans) != canonical_total:
            logger.error(f"Critical Integrity Failure: total={canonical_total}, stages={sum_stages}, orphans={len(orphans)}")

        t2 = time.perf_counter()
        systemic_errors = DashboardAggregator._get_top_errors(AuditStore)
        t3 = time.perf_counter()
        logger.warning(
            "[perf] unified-state _get_top_errors elapsed=%.3fs | total=%.3fs",
            t3 - t2, t3 - t0
        )

        # Derive dashboard counts from trip statuses
        workspace_trip_count = stages.get("assigned", 0) + stages.get("in_progress", 0)
        inbox_lead_count = stages.get("new", 0)

        result = {
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
            "systemic_errors": systemic_errors,
            "workspace_trip_count": workspace_trip_count,
            "inbox_lead_count": inbox_lead_count,
            "pending_review_count": pending_review_count,
            "review_counts": review_counts,
            "total_pending_review_value": total_pending_review_value,
            "pipeline_stages": pipeline_stages,
        }

        # Store in cache
        with _cache_lock:
            _unified_state_cache[agency_id] = (time.monotonic(), result)

        return result

    @staticmethod
    def get_dashboard_stats(agency_id: str = None) -> Dict[str, Any]:
        """
        Compute dashboard stat cards scoped by agency.
        """
        # --- TTL cache check ---
        with _cache_lock:
            cached = _dashboard_stats_cache.get(agency_id)
            if cached is not None:
                cached_at, cached_value = cached
                if time.monotonic() - cached_at < _CACHE_TTL_SECONDS:
                    return cached_value

        t0 = time.perf_counter()
        all_trips = TripStore.list_trip_summaries(limit=10000, agency_id=agency_id)
        t1 = time.perf_counter()
        logger.warning(
            "[perf] dashboard-stats list_trip_summaries agency=%s trips=%d elapsed=%.3fs",
            agency_id, len(all_trips), t1 - t0
        )
        trips = [t for t in all_trips if t.get("id")]

        now = datetime.now(timezone.utc)

        # Resolve SLA thresholds from SupportSettings (once, before the loop)
        sla_t = _resolve_sla_thresholds(agency_id)
        new_limit_h = sla_t["new"].total_seconds() / 3600
        assigned_limit_h = sla_t["assigned"].total_seconds() / 3600

        completed = 0
        ready_to_book = 0
        needs_attention = 0

        for trip in trips:
            status = trip.get("status", "")
            # stage is a top-level field in SQL-backed summaries; fall back to
            # meta.stage for any legacy file-store trips that still nest it.
            stage = trip.get("stage") or trip.get("meta", {}).get("stage", "")
            analytics = trip.get("analytics") or {}
            quality_score = analytics.get("quality_score", 100)

            if status == "completed":
                completed += 1

            if stage in ("strategy", "output"):
                ready_to_book += 1

            created_at_raw = trip.get("created_at")
            if created_at_raw:
                try:
                    if isinstance(created_at_raw, datetime):
                        created_at = created_at_raw
                        if created_at.tzinfo is None:
                            created_at = created_at.replace(tzinfo=timezone.utc)
                    else:
                        created_at_str = created_at_raw
                        if created_at_str.endswith('Z'):
                            created_at_str = created_at_str.replace('Z', '+00:00')
                        created_at = datetime.fromisoformat(created_at_str)
                        if created_at.tzinfo is None:
                            created_at = created_at.replace(tzinfo=timezone.utc)

                    age_hours = (now - created_at).total_seconds() / 3600

                    if status == "new" and age_hours > new_limit_h * 0.75:
                        needs_attention += 1
                    elif status == "assigned" and age_hours > assigned_limit_h * 0.75:
                        needs_attention += 1
                    elif quality_score < 50:
                        needs_attention += 1
                except (ValueError, TypeError):
                    pass

        pending_review = len(trips) - completed

        result = {
            "active": completed,
            "pending_review": max(0, pending_review),
            "ready_to_book": ready_to_book,
            "needs_attention": min(needs_attention, max(0, pending_review)),
        }

        with _cache_lock:
            _dashboard_stats_cache[agency_id] = (time.monotonic(), result)

        return result

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
        decision = trip.get("decision") or {}
        analytics = trip.get("analytics") or {}

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
