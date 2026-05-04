import logging
import sys
from datetime import datetime, timezone
from typing import Any, List, Optional, Dict
from pydantic import BaseModel

# Try to import AuditStore - it may not be available in all contexts
AuditStore = None
try:
    from spine_api.persistence import AuditStore
except ModuleNotFoundError:
    # AuditStore is only needed by TripEventLogger, not by TimelineEventMapper
    pass

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
