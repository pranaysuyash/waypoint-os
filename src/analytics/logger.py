from datetime import datetime, timedelta, timezone
import hashlib
import logging
import os
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

# Try to import AuditStore - it may not be available in all contexts
AuditStore = None
try:
    from spine_api.persistence import AuditStore
except ModuleNotFoundError:
    # AuditStore is only needed by TripEventLogger, not by TimelineEventMapper
    pass

logger = logging.getLogger(__name__)

def _read_positive_int_env(name: str, default: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        logger.warning("Invalid %s value %r; using default %d", name, os.getenv(name), default)
        return default
    return max(1, value)


_ROUTING_HEALTH_ALERT_DEDUPE_WINDOW_SECONDS = _read_positive_int_env(
    "ROUTING_HEALTH_ALERT_DEDUPE_WINDOW_SECONDS",
    900,
)
_ROUTING_HEALTH_ALERT_DEDUPE_LOOKBACK_LIMIT = _read_positive_int_env(
    "ROUTING_HEALTH_ALERT_DEDUPE_LOOKBACK_LIMIT",
    250,
)
_ROUTING_HEALTH_ALERT_SUSTAINED_WARNING_THRESHOLD = _read_positive_int_env(
    "ROUTING_HEALTH_ALERT_SUSTAINED_WARNING_THRESHOLD",
    3,
)
_ROUTING_HEALTH_ALERT_SUSTAINED_WINDOW_SECONDS = _read_positive_int_env(
    "ROUTING_HEALTH_ALERT_SUSTAINED_WINDOW_SECONDS",
    60 * 60,
)
_ROUTING_HEALTH_ALERT_PAGING_COOLDOWN_SECONDS = _read_positive_int_env(
    "ROUTING_HEALTH_ALERT_PAGING_COOLDOWN_SECONDS",
    60 * 60,
)


# Canonical stage definitions for the audit trail
STAGE_TRANSITIONS = ["INTAKE", "PACKET", "DECISION", "STRATEGY", "OUTPUT", "SAFETY"]

# Normalized status values for timeline presentation
STATUS_MAPPING = {
    "started": "started",
    "in_progress": "in_progress",
    "completed": "completed",
    "approved": "approved",
    "rejected": "rejected",
    "error": "error",
}

# Valid stage names (lowercase for presentation layer)
VALID_STAGES = {"intake", "packet", "decision", "strategy", "safety"}


class TimelineEvent(BaseModel):
    """Presentation-ready timeline event for frontend consumption.
    
    This is the Translation Layer between backend deltas (pre_state/post_state)
    and frontend-ready state.
    
    Maps AuditStore Event -> TimelineEvent for /api/trips/{id}/timeline response.
    """
    trip_id: str
    timestamp: str  # ISO 8601
    stage: str  # "intake", "packet", "decision", "strategy", "safety"
    status: str  # Normalized: "started", "in_progress", "completed", "approved", "rejected", "error"
    state_snapshot: Dict[str, Any]  # Human-readable summary of state at this stage
    decision: Optional[str] = None  # If applicable: "approve", "reject", "ask_followup"
    confidence: Optional[float] = None  # 0-100 confidence score
    reason: Optional[str] = None  # Why this stage/decision happened
    actor: Optional[str] = None  # Who performed this action (user ID or "system"/"owner")
    pre_state: Optional[Dict[str, Any]] = None  # Raw delta (for debugging)
    post_state: Optional[Dict[str, Any]] = None  # Raw delta (for debugging)


class TimelineEventMapper:
    """Maps AuditStore Events to presentation-ready TimelineEvents.
    
    Handles the translation from internal state deltas to human-readable
    timeline format that the frontend can render.
    """
    
    @staticmethod
    def _normalize_status(stage: str, event_details: Dict[str, Any]) -> str:
        """Convert raw event state to normalized status string.
        
        Args:
            stage: The stage this event belongs to
            event_details: Raw details dict from AuditStore event
            
        Returns:
            Normalized status string suitable for timeline display
        """
        # First, check if there's an explicit state field
        event_state = event_details.get("state", "unknown")
        if event_state:
            event_state = event_state.lower()
        else:
            event_state = "unknown"
        
        # Check for decision_type which indicates a decision was made
        decision_type = event_details.get("decision_type")
        if decision_type:
            decision_type = decision_type.lower()
        else:
            decision_type = ""
        
        # Map event state to normalized status
        if decision_type:
            if decision_type in ("approve", "approved"):
                return "approved"
            elif decision_type in ("reject", "rejected"):
                return "rejected"
            elif decision_type in ("ask_followup", "followup"):
                return "in_progress"
        
        # Map general states
        if event_state in ("completed", "done", "success"):
            return "completed"
        elif event_state in ("in_progress", "processing"):
            return "in_progress"
        elif event_state in ("started", "initiated", "beginning"):
            return "started"
        elif event_state in ("failed", "error"):
            return "error"
        elif event_state in ("approved", "accepted"):
            return "approved"
        elif event_state in ("rejected", "denied"):
            return "rejected"
        
        # Default based on stage
        if stage == "intake":
            return "started"
        elif stage == "packet":
            return "in_progress"
        elif stage == "decision":
            return "completed"
        elif stage == "strategy":
            return "completed"
        elif stage == "safety":
            return "completed"
        
        return "in_progress"
    
    @staticmethod
    def _build_state_snapshot(
        stage: str,
        event_details: Dict[str, Any],
        normalized_status: str
    ) -> Dict[str, Any]:
        """Build a human-readable state snapshot from event details.
        
        Args:
            stage: The stage this event belongs to
            event_details: Raw details dict from AuditStore event
            normalized_status: Already-computed normalized status
            
        Returns:
            Dict with human-readable state summary
        """
        snapshot = {
            "stage": stage,
            "status": normalized_status,
        }
        
        # Include description if present
        if "description" in event_details:
            snapshot["description"] = event_details["description"]
        
        # Extract useful info from post_state delta if available
        post_state = event_details.get("post_state")
        if isinstance(post_state, dict):
            # Include relevant fields from post_state
            if "state" in post_state:
                snapshot["previous_state"] = post_state.get("state")
            if "reason" in post_state:
                snapshot["reason"] = post_state.get("reason")
        
        # Include confidence if available
        confidence = event_details.get("confidence")
        if confidence is not None:
            snapshot["confidence"] = confidence
        
        return snapshot
    
    @staticmethod
    def map_event(audit_event: Dict[str, Any]) -> Optional[TimelineEvent]:
        """Transform a single AuditStore event to frontend-ready format.
        
        Args:
            audit_event: Raw event dict from AuditStore
            
        Returns:
            TimelineEvent if valid, None if event cannot be mapped
        """
        details = audit_event.get("details", {})
        
        # Validate required fields
        trip_id = details.get("trip_id")
        stage = details.get("stage", "unknown").lower()
        timestamp = audit_event.get("timestamp", "")
        
        if not trip_id or not timestamp:
            return None
        
        # Normalize status
        normalized_status = TimelineEventMapper._normalize_status(stage, details)
        
        # Build state snapshot
        state_snapshot = TimelineEventMapper._build_state_snapshot(
            stage, details, normalized_status
        )
        
        # Determine decision if present
        decision = None
        decision_type = details.get("decision_type")
        if decision_type:
            decision = decision_type.lower() if isinstance(decision_type, str) else str(decision_type)

        # Extract actor from the event-level user_id field
        actor = audit_event.get("user_id")
        
        # Build the TimelineEvent
        return TimelineEvent(
            trip_id=trip_id,
            timestamp=timestamp,
            stage=stage,
            status=normalized_status,
            state_snapshot=state_snapshot,
            decision=decision,
            confidence=details.get("confidence"),
            reason=details.get("reason"),
            actor=actor,
            pre_state=details.get("pre_state"),
            post_state=details.get("post_state"),
        )
    
    @staticmethod
    def map_events_for_trip(
        audit_events: List[Dict[str, Any]],
        stage_filter: Optional[str] = None
    ) -> List[TimelineEvent]:
        """Transform all events for a trip to frontend-ready format.
        
        Maintains chronological order and filters by stage if specified.
        
        Args:
            audit_events: List of raw event dicts from AuditStore
            stage_filter: Optional stage to filter by (e.g., "decision")
            
        Returns:
            List of TimelineEvent objects in chronological order
        """
        mapped_events: List[TimelineEvent] = []
        
        for audit_event in audit_events:
            mapped = TimelineEventMapper.map_event(audit_event)
            if mapped:
                # Apply stage filter if specified
                if stage_filter and mapped.stage != stage_filter.lower():
                    continue
                mapped_events.append(mapped)
        
        # Events should already be in order from AuditStore,
        # but sort by timestamp to be safe
        mapped_events.sort(key=lambda e: e.timestamp)
        
        return mapped_events


class TripEventLogger:
    """
    Standardized logger for Spine lifecycle events.
    Connects the Spine execution to the AuditStore.
    """
    
    @staticmethod
    def log_stage_transition(
        trip_id: str,
        stage: str,
        actor: str,
        description: str,
        pre_state: Any,
        post_state: Any,
        confidence: float = 1.0,
        state: str | None = None,
        decision_type: str | None = None,
        reason: str | None = None,
    ):
        """Standardized log for stage transitions."""
        # Keep a flat `state` for downstream timeline consumers/tests while
        # preserving richer pre/post snapshots for audit analysis.
        resolved_state = state
        if resolved_state is None and isinstance(post_state, dict):
            candidate = post_state.get("state")
            if isinstance(candidate, str):
                resolved_state = candidate

        details = {
            "trip_id": trip_id,
            "stage": stage,
            "state": resolved_state or "unknown",
            "description": description,
            "confidence": confidence,
            "pre_state": pre_state,
            "post_state": post_state,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        if decision_type is not None:
            details["decision_type"] = decision_type
        if reason is not None:
            details["reason"] = reason

        if AuditStore is None:
            raise RuntimeError("AuditStore not available - cannot log event")
        
        AuditStore.log_event(
            event_type="spine_stage_transition",
            user_id=actor,
            details=details,
        )

    @staticmethod
    def log_anomaly(
        trip_id: str,
        stage: str,
        error_type: str,
        message: str
    ):
        """Standardized log for anomalies/suitability flags."""
        if AuditStore is None:
            raise RuntimeError("AuditStore not available - cannot log event")

        AuditStore.log_event(
            event_type="spine_anomaly",
            user_id="system",
            details={
                "trip_id": trip_id,
                "stage": stage,
                "error_type": error_type,
                "message": message,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

    @staticmethod
    def log_routing_health_alert(
        trip_id: str,
        routing_health: Dict[str, Any],
        authority: Dict[str, Any],
        workflow: str | None = None,
        workflow_unit_id: str | None = None,
        min_occurrences: int | None = None,
        window_minutes: int | None = None,
        metrics_snapshot: Dict[str, Any] | None = None,
    ):
        """Standardized log for routing-health warnings/critical alerts."""
        if AuditStore is None:
            raise RuntimeError("AuditStore not available - cannot log event")

        details = {
            "trip_id": trip_id,
            "status": routing_health.get("status", "unknown"),
            "alert_count": routing_health.get("alert_count", 0),
            "alerts": routing_health.get("alerts", []),
            "checked_at": routing_health.get("checked_at"),
            "workflow": workflow,
            "workflow_unit_id": workflow_unit_id,
            "min_occurrences": min_occurrences,
            "window_minutes": window_minutes,
            "authority": authority,
            "metrics_snapshot": metrics_snapshot,
            "alert_signature": TripEventLogger._build_routing_health_alert_signature(
                trip_id=trip_id,
                routing_health=routing_health,
                authority=authority,
                workflow=workflow,
                workflow_unit_id=workflow_unit_id,
                min_occurrences=min_occurrences,
                window_minutes=window_minutes,
            ),
        }

        if TripEventLogger._is_duplicate_routing_health_alert(
            trip_id=trip_id,
            routing_health=routing_health,
            authority=authority,
            workflow=workflow,
            workflow_unit_id=workflow_unit_id,
            min_occurrences=min_occurrences,
            window_minutes=window_minutes,
        ):
            logger.debug(
                "Skipping duplicate routing health alert for trip=%s status=%s",
                trip_id,
                routing_health.get("status", "unknown"),
            )
            return

        AuditStore.log_event(
            event_type="routing_health_alert",
            user_id="system",
            details=details,
        )

        if str(routing_health.get("status", "")).lower() in {"warning", "critical"}:
            TripEventLogger._log_routing_health_paging_alert(
                trip_id=trip_id,
                routing_health=routing_health,
                authority=authority,
                workflow=workflow,
                workflow_unit_id=workflow_unit_id,
                min_occurrences=min_occurrences,
                window_minutes=window_minutes,
            )

    @staticmethod
    def _log_routing_health_paging_alert(
        trip_id: str,
        routing_health: Dict[str, Any],
        authority: Dict[str, Any],
        workflow: str | None = None,
        workflow_unit_id: str | None = None,
        min_occurrences: int | None = None,
        window_minutes: int | None = None,
    ) -> None:
        """Emit a paging/triage alert when warnings/critical persist.

        The rule is stateful, but bounded:
        - Requires sustained occurrences within the sustained alert window.
        - Only emits when count first reaches threshold.
        - Suppresses re-emission for the same context for cooldown window.
        """
        sustained_count = TripEventLogger._count_recent_routing_health_alerts(
            trip_id=trip_id,
            routing_health=routing_health,
            authority=authority,
            workflow=workflow,
            workflow_unit_id=workflow_unit_id,
            min_occurrences=min_occurrences,
            window_minutes=window_minutes,
        ) + 1

        if sustained_count < _ROUTING_HEALTH_ALERT_SUSTAINED_WARNING_THRESHOLD:
            return

        status = str(routing_health.get("status", "")).lower()

        paging_signature = TripEventLogger._build_routing_health_paging_signature(
            trip_id=trip_id,
            status=status,
            workflow=workflow,
            workflow_unit_id=workflow_unit_id,
            min_occurrences=min_occurrences,
            window_minutes=window_minutes,
            authority=authority,
        )

        if TripEventLogger._is_duplicate_routing_health_paging_alert(
            trip_id=trip_id,
            routing_health=routing_health,
            authority=authority,
            workflow=workflow,
            workflow_unit_id=workflow_unit_id,
            min_occurrences=min_occurrences,
            window_minutes=window_minutes,
            paging_signature=paging_signature,
        ):
            logger.debug(
                "Skipping duplicate sustained routing health page for trip=%s status=%s",
                trip_id,
                status,
            )
            return

        details = {
            "trip_id": trip_id,
            "status": status,
            "occurrence_index": sustained_count,
            "workflow": workflow,
            "workflow_unit_id": workflow_unit_id,
            "window_minutes": window_minutes,
            "min_occurrences": min_occurrences,
            "authority": authority,
            "alert_signature": paging_signature,
            "sustained_window_seconds": _ROUTING_HEALTH_ALERT_SUSTAINED_WINDOW_SECONDS,
            "paging_cooldown_seconds": _ROUTING_HEALTH_ALERT_PAGING_COOLDOWN_SECONDS,
        }

        AuditStore.log_event(
            event_type="routing_health_paging_alert",
            user_id="system",
            details=details,
        )

    @staticmethod
    def _build_routing_health_alert_signature(
        trip_id: str,
        routing_health: Dict[str, Any],
        authority: Dict[str, Any],
        workflow: str | None = None,
        workflow_unit_id: str | None = None,
        min_occurrences: int | None = None,
        window_minutes: int | None = None,
    ) -> str:
        """Compute a stable fingerprint for a routing-health alert payload."""
        workflow_norm = workflow or ""
        workflow_unit_id_norm = workflow_unit_id or ""
        status = str(routing_health.get("status", "unknown")).lower()
        alert_count = int(routing_health.get("alert_count", 0) or 0)
        min_occurrences_norm = int(min_occurrences or 0)
        window_minutes_norm = int(window_minutes or 0)
        authority_source = str((authority or {}).get("source", "") or "")
        authority_blocks_ci = bool((authority or {}).get("blocks_ci", False))

        alerts = routing_health.get("alerts", [])
        compact_alerts = []
        if isinstance(alerts, list):
            for alert in alerts:
                if not isinstance(alert, dict):
                    continue
                compact_alerts.append(
                    (
                        str(alert.get("metric", "")),
                        str(alert.get("severity", "")),
                        _round_float(alert.get("actual_value")),
                        _round_float(alert.get("threshold")),
                    )
                )
        compact_alerts.sort()

        fingerprint_payload = {
            "trip_id": trip_id,
            "status": status,
            "workflow": workflow_norm,
            "workflow_unit_id": workflow_unit_id_norm,
            "min_occurrences": min_occurrences_norm,
            "window_minutes": window_minutes_norm,
            "alert_count": alert_count,
            "authority_source": authority_source,
            "authority_blocks_ci": authority_blocks_ci,
            "alerts": compact_alerts,
        }

        digest = hashlib.sha256(
            repr(fingerprint_payload).encode("utf-8")
        ).hexdigest()
        return digest

    @staticmethod
    def _is_duplicate_routing_health_alert(
        trip_id: str,
        routing_health: Dict[str, Any],
        authority: Dict[str, Any],
        workflow: str | None = None,
        workflow_unit_id: str | None = None,
        min_occurrences: int | None = None,
        window_minutes: int | None = None,
    ) -> bool:
        """True if a materially identical alert was persisted recently."""
        candidate_signature = TripEventLogger._build_routing_health_alert_signature(
            trip_id=trip_id,
            routing_health=routing_health,
            authority=authority,
            workflow=workflow,
            workflow_unit_id=workflow_unit_id,
            min_occurrences=min_occurrences,
            window_minutes=window_minutes,
        )
        now = datetime.now(timezone.utc)
        dedupe_cutoff = now - timedelta(
            seconds=_ROUTING_HEALTH_ALERT_DEDUPE_WINDOW_SECONDS
        )

        try:
            recent_events = AuditStore.get_events(
                limit=_ROUTING_HEALTH_ALERT_DEDUPE_LOOKBACK_LIMIT
            )
        except Exception:
            # Never allow dedupe lookup failures to block signal emission.
            logger.exception(
                "Failed to query recent routing_health_alert events for dedupe trip=%s",
                trip_id,
            )
            return False

        # Iterate newest-first to avoid unnecessary work once we cross the dedupe
        # time window.
        for event in reversed(recent_events):
            if not isinstance(event, dict) or event.get("type") != "routing_health_alert":
                continue

            event_timestamp = _parse_audit_timestamp(event.get("timestamp"))
            if event_timestamp is None:
                # Unknown timestamp -> cannot reason about dedupe safely.
                # Keep going in case newer/older events have valid time.
                continue
            if event_timestamp < dedupe_cutoff:
                break

            details = event.get("details", {})
            if not isinstance(details, dict):
                continue
            existing_signature = TripEventLogger._build_routing_health_alert_signature(
                trip_id=str(details.get("trip_id", "")),
                routing_health={
                    "status": details.get("status", ""),
                    "alert_count": details.get("alert_count", 0),
                    "alerts": details.get("alerts", []),
                },
                authority=details.get("authority", {}) if isinstance(details.get("authority", {}), dict) else {},
                workflow=details.get("workflow"),
                workflow_unit_id=details.get("workflow_unit_id"),
                min_occurrences=details.get("min_occurrences"),
                window_minutes=details.get("window_minutes"),
            )
            if existing_signature == candidate_signature:
                return True

        return False

    @staticmethod
    def _build_routing_health_paging_signature(
        trip_id: str,
        status: str,
        authority: Dict[str, Any],
        workflow: str | None = None,
        workflow_unit_id: str | None = None,
        min_occurrences: int | None = None,
        window_minutes: int | None = None,
    ) -> str:
        """Compute a stable fingerprint for paging/triage alert context."""
        payload = {
            "trip_id": trip_id,
            "status": str(status).lower(),
            "workflow": workflow or "",
            "workflow_unit_id": workflow_unit_id or "",
            "min_occurrences": int(min_occurrences or 0),
            "window_minutes": int(window_minutes or 0),
            "authority_source": str((authority or {}).get("source", "") or ""),
            "authority_blocks_ci": bool((authority or {}).get("blocks_ci", False)),
        }

        return hashlib.sha256(repr(payload).encode("utf-8")).hexdigest()

    @staticmethod
    def _is_duplicate_routing_health_paging_alert(
        trip_id: str,
        routing_health: Dict[str, Any],
        authority: Dict[str, Any],
        workflow: str | None = None,
        workflow_unit_id: str | None = None,
        min_occurrences: int | None = None,
        window_minutes: int | None = None,
        paging_signature: str | None = None,
    ) -> bool:
        """True if an identical paging event was emitted recently."""
        if not paging_signature:
            paging_signature = TripEventLogger._build_routing_health_paging_signature(
                trip_id=trip_id,
                status=str(routing_health.get("status", "")),
                authority=authority,
                workflow=workflow,
                workflow_unit_id=workflow_unit_id,
                min_occurrences=min_occurrences,
                window_minutes=window_minutes,
            )

        cooldown_cutoff = datetime.now(timezone.utc) - timedelta(
            seconds=_ROUTING_HEALTH_ALERT_PAGING_COOLDOWN_SECONDS
        )

        try:
            recent_events = AuditStore.get_events(
                limit=_ROUTING_HEALTH_ALERT_DEDUPE_LOOKBACK_LIMIT
            )
        except Exception:
            logger.exception(
                "Failed to query paging routing health events for trip=%s",
                trip_id,
            )
            return False

        for event in reversed(recent_events):
            if (
                not isinstance(event, dict)
                or event.get("type") != "routing_health_paging_alert"
            ):
                continue

            details = event.get("details", {})
            if not isinstance(details, dict):
                continue

            if details.get("trip_id") != trip_id:
                continue

            event_timestamp = _parse_audit_timestamp(event.get("timestamp"))
            if event_timestamp is None:
                continue

            if event_timestamp < cooldown_cutoff:
                break

            if details.get("alert_signature") == paging_signature:
                return True

        return False

    @staticmethod
    def _count_recent_routing_health_alerts(
        trip_id: str,
        routing_health: Dict[str, Any],
        authority: Dict[str, Any],
        workflow: str | None = None,
        workflow_unit_id: str | None = None,
        min_occurrences: int | None = None,
        window_minutes: int | None = None,
    ) -> int:
        """Count recent routing health alerts matching the same sustained context."""
        status = str(routing_health.get("status", "")).lower()
        if status not in {"warning", "critical"}:
            return 0

        sustained_cutoff = datetime.now(timezone.utc) - timedelta(
            seconds=_ROUTING_HEALTH_ALERT_SUSTAINED_WINDOW_SECONDS
        )

        try:
            recent_events = AuditStore.get_events(
                limit=_ROUTING_HEALTH_ALERT_DEDUPE_LOOKBACK_LIMIT
            )
        except Exception:
            logger.exception(
                "Failed to query sustained routing health signals for trip=%s",
                trip_id,
            )
            return 0

        workflow_norm = workflow or ""
        workflow_unit_id_norm = workflow_unit_id or ""
        window_minutes_norm = int(window_minutes or 0)
        min_occurrences_norm = int(min_occurrences or 0)
        authority_source = str((authority or {}).get("source", "") or "")
        authority_blocks_ci = bool((authority or {}).get("blocks_ci", False))

        count = 0
        for event in reversed(recent_events):
            if not isinstance(event, dict) or event.get("type") != "routing_health_alert":
                continue

            event_timestamp = _parse_audit_timestamp(event.get("timestamp"))
            if event_timestamp is None:
                continue

            if event_timestamp < sustained_cutoff:
                break

            details = event.get("details", {})
            if not isinstance(details, dict):
                continue

            if details.get("trip_id") != trip_id:
                continue

            if str(details.get("status", "")).lower() != status:
                continue

            if (details.get("workflow") or "") != workflow_norm:
                continue

            if (details.get("workflow_unit_id") or "") != workflow_unit_id_norm:
                continue

            if int(details.get("window_minutes") or 0) != window_minutes_norm:
                continue

            if int(details.get("min_occurrences") or 0) != min_occurrences_norm:
                continue

            details_authority = details.get("authority")
            if not isinstance(details_authority, dict):
                continue

            if str(details_authority.get("source", "") or "") != authority_source:
                continue

            if bool(details_authority.get("blocks_ci", False)) != authority_blocks_ci:
                continue

            count += 1

        return count


def _parse_audit_timestamp(timestamp_value: Any) -> Optional[datetime]:
    if not isinstance(timestamp_value, str):
        return None

    value = timestamp_value
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _round_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return round(float(value), 6)
    except (TypeError, ValueError):
        return None
