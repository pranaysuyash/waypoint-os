import json
from pathlib import Path
from typing import Dict, List, Any
import logging
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)

class DashboardAggregator:
    """
    Canonical SSOT for dashboard metrics.
    Aggregates data from TripStore and returns a unified state.
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
        
        # Define valid stages/statuses for the pipeline
        VALID_STAGES = ["new", "assigned", "in_progress", "completed", "cancelled"]
        
        # Load all trips from storage
        all_trips = TripStore.list_trips(limit=10000)
        
        # Canonical total: Count all valid trips (those with IDs)
        trips = [t for t in all_trips if t.get("id")]
        canonical_total = len(trips)
        stages = {stage: 0 for stage in VALID_STAGES}
        sla_breached = 0
        orphans = []
        
        now = datetime.now(timezone.utc)
        
        # 2. Aggregate metrics
        for trip in trips:
            status = trip.get("status")
            trip_id = trip.get("id", "missing_id")
            
            if status in VALID_STAGES:
                stages[status] += 1
            else:
                # Trip has no valid stage - it's an orphan
                orphans.append({
                    "id": trip_id,
                    "status": status,
                    "created_at": trip.get("created_at")
                })
            
            # SLA Breach Check
            # Breach = 'new' > 4h OR 'assigned' > 24h
            created_at_str = trip.get("created_at")
            if created_at_str:
                try:
                    # Handle potential Z or +00:00 suffixes
                    if created_at_str.endswith('Z'):
                        created_at_str = created_at_str.replace('Z', '+00:00')
                    created_at = datetime.fromisoformat(created_at_str)
                    
                    # Ensure timezone awareness
                    if created_at.tzinfo is None:
                        created_at = created_at.replace(tzinfo=timezone.utc)
                    
                    age = now - created_at
                    
                    if status == "new" and age > timedelta(hours=4):
                        sla_breached += 1
                    elif status == "assigned" and age > timedelta(hours=24):
                        sla_breached += 1
                except (ValueError, TypeError):
                    pass # Skip malformed dates
        
        # 3. Final validation
        sum_stages = sum(stages.values())
        
        # The sum of trips in stages + orphans must equal canonical_total
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
    def _get_top_errors(AuditStore, limit: int = 5) -> List[Dict]:
        """Aggregate top error categories from the AuditStore."""
        try:
            events = AuditStore.get_events(limit=500)
            error_counts = {}
            
            for event in events:
                if event.get("type") == "review_action_applied":
                    category = event.get("details", {}).get("error_category")
                    if category:
                        error_counts[category] = error_counts.get(category, 0) + 1
            
            # Sort and return
            sorted_errors = sorted(
                [{"category": k, "count": v} for k, v in error_counts.items()],
                key=lambda x: x["count"],
                reverse=True
            )
            return sorted_errors[:limit]
        except Exception as e:
            logger.error(f"Failed to aggregate systemic errors: {e}")
            return []
