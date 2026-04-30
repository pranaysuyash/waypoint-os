from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from spine_api.contract import IntegrityIssue
from spine_api.persistence import TripStore

from src.services.dashboard_aggregator import DashboardAggregator


class IntegrityService:
    @staticmethod
    def map_orphan_to_issue(
        orphan: Dict[str, Any],
        detected_at: Optional[str] = None,
    ) -> IntegrityIssue:
        entity_id = orphan.get("id", "unknown")
        issue_detected_at = detected_at or datetime.now(timezone.utc).isoformat()

        return IntegrityIssue(
            id=f"integrity_orphaned_record_{entity_id}",
            entity_id=entity_id,
            entity_type="unknown",
            issue_type="orphaned_record",
            severity="medium",
            reason="Record is detached from normal inbox/workspace routing.",
            current_status=orphan.get("status"),
            created_at=orphan.get("created_at"),
            detected_at=issue_detected_at,
            allowed_actions=[],
        )

    @staticmethod
    def list_integrity_issues(agency_id: Optional[str] = None) -> Dict[str, Any]:
        unified_state = DashboardAggregator.get_unified_state(agency_id=agency_id)
        detected_at = (
            unified_state.get("integrity_meta", {}).get("last_sync")
            or datetime.now(timezone.utc).isoformat()
        )
        items = [
            IntegrityService.map_orphan_to_issue(orphan, detected_at=detected_at)
            for orphan in unified_state.get("orphans", [])
        ]

        return {
            "items": items,
            "total": len(items),
        }
