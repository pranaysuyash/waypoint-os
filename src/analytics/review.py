"""
Review state machine for owner approval workflows.

Handles applying review actions to trips and logging audit events.
Follows Hybrid Policy B:
- approve: sets owner_approved=true, requires_review=false
- request_changes: sets revision_needed, requires_review=false, reassigns back to agent
- reject: sets rejected, requires_review=false
- escalate: sets escalated
"""
from datetime import datetime, timezone
from typing import Any, Optional

# Expected in PYTHONPATH: spine-api/
from persistence import TripStore, AuditStore


# Actions accepted from the backend endpoint (post-normalisation)
VALID_ACTIONS = {"approved", "rejected", "escalated", "revision_needed", "recovery", "resolved"}

# Map frontend action names → internal status names
ACTION_MAP = {
    "approve": "approved",
    "reject": "rejected",
    "escalate": "escalated",
    "request_changes": "revision_needed",
    "resolve": "resolved",
}


def process_review_action(
    trip_id: str,
    action: str,
    notes: str,
    user_id: str,
    reassign_to: Optional[str] = None,
    error_category: Optional[str] = None
) -> dict:
    """Apply a review action to a trip and log an audit event.

    Args:
        trip_id: ID of the trip to review.
        action: One of VALID_ACTIONS or a frontend alias (approve / reject / escalate).
        notes: Free-text owner notes.
        user_id: Identity of the reviewer (defaults to "owner").
        reassign_to: Optional user_id to reassign the trip to.

    Returns:
        The updated trip dict as stored on disk.

    Raises:
        KeyError: If the trip_id does not exist in TripStore.
        ValueError: If the action is not recognised.
    """
    normalised = ACTION_MAP.get(action, action)
    if normalised not in VALID_ACTIONS:
        raise ValueError(
            f"Invalid action '{action}'. Valid options: {sorted(VALID_ACTIONS)}"
        )

    trip = TripStore.get_trip(trip_id)
    if trip is None:
        raise KeyError(f"Trip not found: {trip_id}")

    # Capture PRE-STATE for audit deltas
    analytics_pre = trip.get("analytics") or {}
    pre_state = {
        "review_status": analytics_pre.get("review_status", "pending"),
        "requires_review": analytics_pre.get("requires_review", False),
        "assignee": trip.get("assigned_to", "unassigned"),
    }

    # Prepare POST-STATE updates
    analytics = dict(analytics_pre)
    analytics["review_status"] = normalised
    analytics["requires_review"] = False  # Clear from queue for most actions except escalation logic
    
    review_meta = {
        "action": normalised,
        "reviewed_by": user_id,
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
        "notes": notes,
        "owner_approved": normalised == "approved",
        "reassigned_to": reassign_to,
    }
    analytics["review_metadata"] = review_meta

    update_fields: dict[str, Any] = {"analytics": analytics}

    # Policy-specific logic
    if normalised == "approved":
        # Automated state change to 'delivered' upon approval
        update_fields["status"] = "delivered"
        analytics["delivery_status"] = "delivered"
        analytics["proactive_feedback_asked"] = True
        analytics["proactive_feedback_at"] = datetime.now(timezone.utc).isoformat()
        
        # Mocking an automated email/WhatsApp dispatch
        _emit_notification(trip_id, pre_state["assignee"], "DELIVERY_ASK_FEEDBACK", 
                           "Trip approved and delivered. Automated feedback request sent to customer.")

    elif normalised == "revision_needed":
        # Mandatory reassignment: reassign_to if provided, else original assignee (already in pre_state)
        new_assignee = reassign_to or pre_state["assignee"]
        update_fields["assigned_to"] = new_assignee
        _emit_notification(trip_id, new_assignee, "REVISION_NEEDED", notes)

    elif normalised == "rejected":
        # Optional reassignment
        if reassign_to:
            update_fields["assigned_to"] = reassign_to

    elif normalised == "escalated":
        # Keep in review queue but tag as escalated/management
        analytics["requires_review"] = True
        update_fields["assigned_to"] = "management_queue"

    # Capture POST-STATE for audit deltas
    post_state = {
        "review_status": normalised,
        "requires_review": analytics["requires_review"],
        "assignee": update_fields.get("assigned_to", pre_state["assignee"]),
    }

    # Persist
    TripStore.update_trip(trip_id, update_fields)
    
    # Audit log entry with deltas
    AuditStore.log_event(
        "review_action",
        user_id,
        {
            "trip_id": trip_id,
            "action": normalised,
            "notes": notes,
            "error_category": error_category,
            "pre_state": pre_state,
            "post_state": post_state,
            "timestamp": review_meta["reviewed_at"]
        },
    )

    return TripStore.get_trip(trip_id)


def _emit_notification(trip_id: str, recipient: str, type: str, message: str):
    """Emit a notification and log it to the AuditStore for traceability."""
    # In a real system, this would push to a message outbox or trigger a webhook.
    # For now, we ensure it's recorded in the AuditStore so the UI can surface it.
    AuditStore.log_event(
        "notification_emitted",
        "system",
        {
            "trip_id": trip_id,
            "recipient": recipient,
            "notification_type": type,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )
    logger.info(f"Notification emitted: {type} to {recipient} for trip {trip_id}")


def trip_to_review(trip: dict) -> dict:
    """Transform a stored trip dict into a TripReview-shaped dict for the frontend.

    Maps the internal trip/analytics structure to the fields expected by the
    TripReview TypeScript type.
    """
    analytics = trip.get("analytics") or {}
    packet = trip.get("packet") or {}

    budget = packet.get("budget") or {}
    value = budget.get("value", 0)
    currency = budget.get("currency", "INR")

    trip_id = trip.get("trip_id", "")
    review_status = analytics.get("review_status", "pending")
    review_meta = analytics.get("review_metadata") or {}

    # Derive risk flags from analytics data
    risk_flags = []
    if value > 500000:
        risk_flags.append("high_value")
    quality_breakdown = analytics.get("quality_breakdown") or {}
    if quality_breakdown.get("risk", 100) < 50:
        risk_flags.append("complex_itinerary")

    return {
        "id": trip_id,
        "tripId": trip_id,
        "tripReference": f"TRIP-{trip_id[-6:].upper()}" if trip_id else "TRIP-UNKNOWN",
        "destination": packet.get("destination", "Unknown"),
        "tripType": packet.get("trip_type", packet.get("tripType", "leisure")),
        "partySize": packet.get("party_size", packet.get("partySize", 1)),
        "dateWindow": packet.get("date_window", packet.get("dateWindow", "")),
        "value": value,
        "currency": currency,
        "agentId": trip.get("assigned_to", "unassigned"),
        "agentName": trip.get("assigned_to_name", "Unassigned"),
        "submittedAt": trip.get("created_at", datetime.now(timezone.utc).isoformat()),
        "status": review_status,
        "reason": analytics.get("review_reason", "Flagged for review"),
        "agentNotes": packet.get("notes") or None,
        "ownerNotes": review_meta.get("notes") or None,
        "reviewedAt": review_meta.get("reviewed_at") or None,
        "reviewedBy": review_meta.get("reviewed_by") or None,
        "riskFlags": risk_flags,
        # Wave 10: Feedback-Driven Actioning
        "feedbackSeverity": analytics.get("feedback_severity"),
        "followupNeeded": analytics.get("followup_needed", False),
        "recoveryStatus": analytics.get("recovery_status"),
        # Wave 11: SLA Tracking
        "recoveryStartedAt": analytics.get("recovery_started_at"),
        "recoveryDeadline": analytics.get("recovery_deadline"),
        "isEscalated": analytics.get("is_escalated", False),
        "slaStatus": analytics.get("sla_status", "on_track"),
    }


def trigger_feedback_recovery(trip_id: str, reason: str = "Critical Negative Feedback"):
    """
    Automated transition for low-CSAT recovery.
    Assigns back to original agent and moves to 'recovery' status.
    """
    trip = TripStore.get_trip(trip_id)
    if not trip:
        return

    analytics = trip.get("analytics") or {}
    pre_assignee = trip.get("assigned_to", "unassigned")

    # Update analytics and status
    now = datetime.now(timezone.utc)
    analytics["recovery_status"] = "IN_RECOVERY"
    analytics["recovery_started_at"] = now.isoformat()
    analytics["requires_review"] = True  # Surface on owner dashboard
    analytics["review_status"] = "recovery"
    
    # Initialize SLA if missing (should be set by engine, but safety first)
    if not analytics.get("recovery_deadline"):
        from datetime import timedelta
        severity = analytics.get("feedback_severity", "high")
        hours = 2 if severity == "critical" else 6
        analytics["recovery_deadline"] = (now + timedelta(hours=hours)).isoformat()
        analytics["sla_status"] = "on_track"

    update_fields: dict[str, Any] = {
        "status": "recovery",
        "analytics": analytics,
        "assigned_to": pre_assignee  # Confirmed Choice: Re-assign to original agent
    }

    TripStore.update_trip(trip_id, update_fields)

    # Audit log
    AuditStore.log_event(
        "feedback_recovery_triggered",
        "system",
        {
            "trip_id": trip_id,
            "reason": reason,
            "assigned_to": pre_assignee,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )

    # Operator Notification
    _emit_notification(trip_id, pre_assignee, "RECOVERY_ASSIGNED", 
                       f"CRITICAL FEEDBACK RECOVERY: Trip re-opened due to low CSAT. Reason: {reason}")
