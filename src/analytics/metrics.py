from typing import Any, List, Optional
from datetime import datetime, timezone

from src.analytics.models import (
    InsightsSummary,
    PipelineVelocity,
    StageMetrics,
    TeamMemberMetrics,
    BottleneckAnalysis,
    RevenueMetrics,
    MonthlyRevenue,
    OperationalAlert
)

STAGE_CONVERSION_PROBABILITIES = {
    "discovery": 0.10,
    "packet": 0.25,
    "decision": 0.50,
    "strategy": 0.75,
    "output": 0.90,
    "safety": 0.95,
}

# Non-terminal statuses that can act as pipeline stages (a trip can dwell in
# them and later leave). Terminal statuses never "exit", so they are excluded
# from bottleneck/timing analysis.
_NON_TERMINAL_STAGES = ("new", "assigned", "in_progress")

# Booked-equivalent statuses for revenue metrics (FND-0122). Anchored on the
# canonical 12-state machine (spine_api/core/trip_lifecycle.py): revenue counts
# only states at or after the booking commitment — "booked" (commitment),
# "change_requested" (booked change loop), "in_trip" (post-commitment travel),
# "returned" (dormant post-trip COMPLETED split), "completed" (terminal), and
# "delivered" (review-approval terminal writer, src/analytics/review.py:101).
# Deliberately excluded: "active" (audit-gated alias of in_trip; semantics
# pending the persisted-distribution audit — counting it would book revenue on
# possibly-pre-routing leads) and "archived" (its only current writer archives
# inbox leads, spine_api/routers/inbox.py — not booked-trip evidence), and
# "cancelled" (refund path). No writer emits canonical "booked" yet — the
# booking rail is the remaining producer gap.
BOOKED_REVENUE_STATUSES = frozenset({
    "booked", "change_requested", "in_trip", "returned", "completed", "delivered",
})


def _dict_payload(value: Any) -> dict:
    """Return dict-shaped JSON payloads; treat null/malformed payloads as absent evidence."""
    return value if isinstance(value, dict) else {}


def _trip_analytics(trip: dict) -> dict:
    return _dict_payload(trip.get("analytics"))


def _trip_packet(trip: dict) -> dict:
    extracted = _dict_payload(trip.get("extracted"))
    return extracted or _dict_payload(trip.get("packet"))


def _parse_ts(value: Any) -> Optional[datetime]:
    """Parse an ISO-8601 timestamp; None for absent/malformed values."""
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed
    except ValueError:
        return None


def _trip_budget_value(trip: dict) -> float:
    """Normalized budget value from the trip packet; 0.0 when absent/unparseable."""
    budget = _dict_payload(_trip_packet(trip).get("budget"))
    raw_val = budget.get("value", 0)
    try:
        return float(raw_val) if raw_val is not None else 0.0
    except (ValueError, TypeError):
        return 0.0


def _stage_dwell_samples(trips: list) -> dict:
    """Dwell-time evidence per status, from durable status_history.

    Returns ``{status: {"exited": [hours...], "current": [hours...],
    "entered": int, "exited_count": int}}``. ``exited`` holds completed dwells
    (the trip later transitioned out); ``current`` holds censored dwells (the
    trip is still in the status, measured to its last update). Entries without
    parseable timestamps are skipped, never guessed.
    """
    dwell: dict = {}
    for trip in trips:
        history = trip.get("status_history") or []
        if not isinstance(history, list):
            continue
        events = []
        for entry in history:
            if not isinstance(entry, dict):
                continue
            at = _parse_ts(entry.get("at"))
            if at is None:
                continue
            events.append((at, str(entry.get("from") or ""), str(entry.get("to") or "")))
        if not events:
            continue
        events.sort(key=lambda e: e[0])

        created = _parse_ts(trip.get("created_at"))
        updated = _parse_ts(trip.get("updated_at"))

        def _record(status: str, hours: float, *, exited: bool) -> None:
            if not status or hours < 0:
                return
            slot = dwell.setdefault(status, {"exited": [], "current": [], "entered": 0, "exited_count": 0})
            if exited:
                slot["exited"].append(hours)
                slot["exited_count"] += 1
            else:
                slot["current"].append(hours)

        # Dwell in the pre-history status (from creation to first transition).
        first_at, _, first_to = events[0]
        if created is not None and first_at > created:
            _record(events[0][1], (first_at - created).total_seconds() / 3600, exited=True)

        # Dwell between consecutive transitions.
        for (_at, _from, _to), (next_at, _, _) in zip(events, events[1:]):
            if next_at > _at:
                _record(_to, (next_at - _at).total_seconds() / 3600, exited=True)

        # Censored dwell in the current status (to last update).
        last_at, _, last_to = events[-1]
        censor = updated or datetime.now(timezone.utc)
        if censor > last_at:
            _record(last_to, (censor - last_at).total_seconds() / 3600, exited=False)

    for slot in dwell.values():
        slot["entered"] = slot["exited_count"] + len(slot["current"])
    return dwell


def _mean(values: list) -> Optional[float]:
    return round(sum(values) / len(values), 1) if values else None


def aggregate_insights(trips: list, days: int = 30) -> InsightsSummary:
    """Compute actual pipeline metrics from trip data.

    Uses trip status, timestamps, and stage transitions to calculate
    real velocity metrics. Every unavailable metric is None/0 — never a
    fabricated placeholder.
    """
    total = len(trips)
    # Terminal/revenue statuses writers actually emit (F-35): no writer ever
    # sets "booked"; "delivered" (review approval, review.py:101) and
    # "completed" are the real terminal vocabulary. "booked" kept for the
    # future booking-rail writer.
    _TERMINAL_STATUSES = ("booked", "delivered", "completed")
    converted = sum(
        1
        for t in trips
        if t.get("status") in _TERMINAL_STATUSES or _trip_analytics(t).get("quality_score", 0) > 80
    )

    rate = (converted / total * 100) if total > 0 else 0

    # Response time = hours from trip creation to the first recorded status
    # transition (the first human/system action on the inquiry). None when no
    # trip has both timestamps — never a random placeholder.
    response_times: list = []
    for trip in trips:
        created = _parse_ts(trip.get("created_at"))
        history = trip.get("status_history") or []
        first_at = None
        if isinstance(history, list):
            for entry in history:
                if isinstance(entry, dict):
                    first_at = _parse_ts(entry.get("at"))
                    if first_at is not None:
                        break
        if created is not None and first_at is not None and first_at > created:
            response_times.append((first_at - created).total_seconds() / 3600)
    avg_response_time = _mean(response_times)

    # Pipeline value = sum of real trip budgets for non-terminal trips.
    pipeline_value = sum(
        _trip_budget_value(t) for t in trips if t.get("status") not in _TERMINAL_STATUSES
    )

    # GMV (FND-0269): sum of real recorded trip budgets for terminal-status
    # trips — the commercial value actually delivered, not a projection.
    gmv = sum(_trip_budget_value(t) for t in trips if t.get("status") in _TERMINAL_STATUSES)

    # Velocity from real status dwell times (days). Stage boundaries beyond
    # the status vocabulary (strategy→output, output→booked) have no writer
    # yet and stay 0.0 — honest absence, not fabricated spread.
    dwell = _stage_dwell_samples(trips)

    def _dwell_days(status: str) -> float:
        samples = dwell.get(status, {}).get("exited", []) + dwell.get(status, {}).get("current", [])
        mean_hours = _mean(samples)
        return round(mean_hours / 24.0, 2) if mean_hours is not None else 0.0

    velocity_values = {
        "stage1To2": _dwell_days("new"),
        "stage2To3": _dwell_days("assigned"),
        "stage3To4": _dwell_days("in_progress"),
        "stage4To5": 0.0,
        "stage5ToBooked": 0.0,
    }
    pipeline_velocity = PipelineVelocity(
        **velocity_values,
        averageTotal=round(sum(velocity_values.values()), 2),
    )

    return InsightsSummary(
        totalInquiries=total,
        convertedToBooked=converted,
        conversionRate=round(rate, 1) if total > 0 else 0.0,
        avgResponseTime=avg_response_time,
        pipelineValue=round(pipeline_value, 2),
        gmv=round(gmv, 2),
        pipelineVelocity=pipeline_velocity,
    )


def compute_pipeline_metrics(trips: list, days: int = 30) -> List[StageMetrics]:
    metrics = []
    # Map internal stages to display names
    stages_config = [
        ("new", "Discovery & Intake"),
        ("assigned", "Signal Extraction"),
        ("in_progress", "Feasibility & Decision"),
        ("completed", "Deliverables"),
        ("cancelled", "Safety & Compliance")
    ]

    # Count actual occurrences in canonical trips
    stage_counts = {s[0]: 0 for s in stages_config}
    for t in trips:
        stage = t.get("status", "new")
        if stage in stage_counts:
            stage_counts[stage] += 1

    # Real dwell/exit evidence from durable status_history. None when a
    # stage has no evidence — the UI renders an explicit "no data" state.
    dwell = _stage_dwell_samples(trips)
    for stage_id, stage_name in stages_config:
        count = stage_counts[stage_id]
        slot = dwell.get(stage_id, {})
        exited = slot.get("exited", [])
        current = slot.get("current", [])
        entered = slot.get("entered", 0)
        exited_count = slot.get("exited_count", 0)

        avg_time = _mean(exited + current) if (exited or current) else None
        exit_rate = round(exited_count / entered * 100, 1) if entered > 0 else None
        avg_exit = _mean(exited) if exited else None

        metrics.append(StageMetrics(
            stageId=str(stage_id),
            stageName=stage_name,
            tripCount=count,
            avgTimeInStage=avg_time,
            exitRate=exit_rate,
            avgTimeToExit=avg_exit
        ))
    return metrics


def compute_team_metrics(trips: list, members: list, days: int = 30) -> List[TeamMemberMetrics]:
    """
    Calculate performance metrics for each team member.

    Builds from the actual team roster (not assignment records), then joins trip data
    by assigned_to to count active/completed trips. CSAT is derived from extracted
    feedback ratings (1-5) when available.

    Args:
        trips: canonical trip records from TripStore
        members: team member roster from TeamStore
        days: analysis window (unused until we have date-based filtering on trips)

    Returns:
        One TeamMemberMetrics per team member; members with no assignments show 0s.
    """
    # Build agent slot map from the canonical roster
    agent_data = {}
    for member in members:
        uid = member.get("id")
        if not uid:
            continue
        agent_data[uid] = {
            "name": member.get("name", "Unknown"),
            "role": member.get("role", "junior_agent"),
            "ratings": [],
            "active": 0,
            "completed": 0,
        }

    # Aggregate trip counts and ratings by assignee
    for trip in trips:
        uid = trip.get("assigned_to")
        if not uid or uid not in agent_data:
            continue

        status = trip.get("status", "new")
        if status in ("booked", "delivered", "completed"):
            agent_data[uid]["completed"] += 1
        else:
            agent_data[uid]["active"] += 1

        # Extract quality signal: Feedback Rating
        # Try both packet/feedback (Wave 9) and analytics/latest_feedback
        packet = _trip_packet(trip)
        feedback = packet.get("feedback") or _trip_analytics(trip).get("latest_feedback")

        if feedback and isinstance(feedback, dict):
            rating = feedback.get("rating")
            if rating and isinstance(rating, (int, float)):
                agent_data[uid]["ratings"].append(float(rating))

    # Build final metrics objects
    team_metrics = []
    for uid, stats in agent_data.items():
        ratings = stats["ratings"]
        # CSAT is the mean of real feedback ratings; None when no ratings
        # exist — never a fabricated baseline.
        csat = round(sum(ratings) / len(ratings), 1) if ratings else None

        active = stats["active"]
        completed = stats["completed"]
        total = active + completed

        # Real conversion rate from persisted evidence (completed / total * 100)
        conversion_rate = round((completed / total * 100), 1) if total > 0 else 0.0

        # Workload score maps active count to a 0-100 percentage band
        workload_score = min(100.0, active * 6.0)

        team_metrics.append(TeamMemberMetrics(
            userId=uid,
            name=stats["name"],
            role=stats["role"],
            activeTrips=active,
            completedTrips=completed,
            conversionRate=conversion_rate,
            avgResponseTime=None,  # Explicitly unavailable: no real response-time data yet
            customerSatisfaction=csat,
            currentWorkload="optimal" if active < 15 else "over",
            workloadScore=workload_score
        ))

    return team_metrics


def compute_bottlenecks(trips: list, days: int = 30) -> List[BottleneckAnalysis]:
    """Identify the slowest non-terminal stage from real dwell evidence.

    No dwell evidence → empty list (the UI shows its no-data state).
    Causes are NOT fabricated: until per-delay cause data exists, the
    bottleneck carries its real measured dwell time only.
    """
    dwell = _stage_dwell_samples(trips)
    best: Optional[tuple] = None  # (avg_hours, stage_id, stage_name)
    stage_names = {
        "new": "Discovery & Intake",
        "assigned": "Signal Extraction",
        "in_progress": "Feasibility & Decision",
    }
    for stage_id in _NON_TERMINAL_STAGES:
        slot = dwell.get(stage_id, {})
        samples = slot.get("exited", []) + slot.get("current", [])
        if not samples:
            continue
        avg_hours = _mean(samples)
        if avg_hours is None:
            continue
        if best is None or avg_hours > best[0]:
            best = (avg_hours, stage_id, stage_names[stage_id])

    if best is None:
        return []

    avg_hours, stage_id, stage_name = best
    if avg_hours > 72:
        severity = "high"
    elif avg_hours > 24:
        severity = "medium"
    else:
        severity = "low"

    return [
        BottleneckAnalysis(
            stageId=stage_id,
            stageName=stage_name,
            avgTimeInStage=avg_hours,
            isBottleneck=True,
            severity=severity,
            primaryCauses=[],
        )
    ]

def compute_revenue_metrics(trips: list, days: int = 30) -> RevenueMetrics:
    """
    Calculate revenue and forecasting metrics from trip data.

    Booked Revenue = Σ(budget where status in BOOKED_REVENUE_STATUSES — the
    canonical booked-equivalent states, FND-0122)
    Projected Revenue = Σ(budget * stage_probability)
    Total Pipeline Value = Σ(budget for non-booked active trips)
    Near Close Revenue = Σ(budget for output/safety stages)
    """
    datetime.now(timezone.utc)

    booked_revenue = 0.0
    projected_revenue = 0.0
    pipeline_value = 0.0
    near_close_revenue = 0.0
    total_value = 0.0
    trip_count = 0

    # Monthly aggregation
    monthly_data = {} # "YYYY-MM" -> {"revenue": 0.0, "inquiries": 0, "booked": 0}

    # Sort trips by date for stable grouping
    sorted_trips = sorted(
        trips,
        key=lambda t: t.get("created_at", ""),
        reverse=False
    )

    for trip in sorted_trips:
        created_at_str = trip.get("created_at")
        if not created_at_str:
            continue

        try:
            created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
        except ValueError:
            continue

        month_key = created_at.strftime("%Y-%m")
        if month_key not in monthly_data:
            monthly_data[month_key] = {"revenue": 0.0, "inquiries": 0, "booked": 0}

        monthly_data[month_key]["inquiries"] += 1

        # Determine value
        packet = _trip_packet(trip)
        budget = _dict_payload(packet.get("budget"))
        # Some sample data has "value" as a string or nested. Normalise to float.
        raw_val = budget.get("value", 0)
        try:
            val = float(raw_val) if raw_val is not None else 0.0
        except (ValueError, TypeError):
            val = 0.0

        status = trip.get("status", "new")
        stage = _dict_payload(trip.get("meta")).get("stage", "discovery")

        if status in BOOKED_REVENUE_STATUSES:
            booked_revenue += val
            monthly_data[month_key]["revenue"] += val
            monthly_data[month_key]["booked"] += 1
            projected_revenue += val # 100% probability
        else:
            # Active pipeline
            total_value += val
            trip_count += 1
            pipeline_value += val

            # Weighted projection
            prob = STAGE_CONVERSION_PROBABILITIES.get(stage, 0.0)
            projected_revenue += val * prob

            # Near close revenue (output or safety)
            if stage in ("output", "safety"):
                near_close_revenue += val

    # Format monthly results
    revenue_by_month = [
        MonthlyRevenue(
            month=m,
            revenue=data["revenue"],
            inquiries=data["inquiries"],
            booked=data["booked"]
        ) for m, data in sorted(monthly_data.items())
    ]

    avg_val = (total_value / trip_count) if trip_count > 0 else 0.0

    return RevenueMetrics(
        period=f"{days}d",
        totalPipelineValue=round(pipeline_value, 2),
        bookedRevenue=round(booked_revenue, 2),
        projectedRevenue=round(projected_revenue, 2),
        nearCloseRevenue=round(near_close_revenue, 2),
        avgTripValue=round(avg_val, 2),
        revenueByMonth=revenue_by_month
    )


def compute_alerts(trips: list) -> List[OperationalAlert]:
    """
    Identify trips requiring manual recovery/intervention.
    Currently focuses on Wave 10: Feedback-Driven Actioning.
    """
    alerts = []

    for trip in trips:
        analytics = _trip_analytics(trip)

        # Check for feedback re-open condition
        if analytics.get("feedback_reopen") and not analytics.get("feedback_dismissed"):
            trip_id = trip.get("id") or trip.get("trip_id")
            severity = analytics.get("feedback_severity", "high")

            # Wave 11: SLA Tracking & Escalation Logic
            deadline_str = analytics.get("recovery_deadline")
            sla_status = analytics.get("sla_status", "on_track")
            is_escalated = analytics.get("is_escalated", False)

            if deadline_str:
                try:
                    deadline = datetime.fromisoformat(deadline_str.replace("Z", "+00:00"))
                    now = datetime.now(timezone.utc)
                    diff = (deadline - now).total_seconds() / 60.0 # minutes

                    if diff <= 0:
                        sla_status = "breached"
                        is_escalated = True
                        # Persist the escalation back to the trip if not already set
                        if not analytics.get("is_escalated") or analytics.get("sla_status") != "breached":
                            from spine_api.persistence import TripStore
                            analytics["is_escalated"] = True
                            analytics["sla_status"] = "breached"
                            TripStore.update_trip(trip_id, {"analytics": analytics})
                    elif diff <= 30:
                        sla_status = "at_risk"
                        if analytics.get("sla_status") != "at_risk":
                            from spine_api.persistence import TripStore
                            analytics["sla_status"] = "at_risk"
                            TripStore.update_trip(trip_id, {"analytics": analytics})
                    else:
                        sla_status = "on_track"
                except Exception:
                    pass

            alert_type = "sla_breach" if sla_status == "breached" else "critical_feedback"
            alert_severity = "critical" if severity == "critical" or sla_status == "breached" else "high"

            message = analytics.get("review_reason", "Critical Feedback Recovery Required")
            if sla_status == "breached":
                message = f"SLA BREACHED: {message}"
            elif sla_status == "at_risk":
                message = f"AT RISK (30m): {message}"

            alerts.append(OperationalAlert(
                id=f"alert_{trip_id}",
                tripId=trip_id,
                type=alert_type,
                severity=alert_severity,
                message=message,
                timestamp=trip.get("updated_at") or trip.get("saved_at") or analytics.get("proactive_feedback_at") or datetime.now(timezone.utc).isoformat(),
                isDismissed=False,
                metadata={
                    "rating": analytics.get("feedback", {}).get("rating"),
                    "agent_id": trip.get("assigned_to"),
                    "sla_status": sla_status,
                    "is_escalated": is_escalated,
                    "deadline": deadline_str
                }
            ))

    # Sort by timestamp descending
    return sorted(alerts, key=lambda a: a.timestamp, reverse=True)
