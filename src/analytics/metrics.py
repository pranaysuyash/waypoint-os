from typing import List, Optional
from datetime import datetime, timezone
import random

from src.analytics.models import (
    InsightsSummary,
    PipelineVelocity,
    StageMetrics,
    TeamMemberMetrics,
    BottleneckAnalysis,
    BottleneckCause,
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

def aggregate_insights(trips: list, days: int = 30) -> InsightsSummary:
    # Just basic counts for now
    total = len(trips)
    # fake conversions for sample size
    converted = sum(1 for t in trips if t.get("analytics", {}).get("quality_score", 0) > 80)
    
    rate = (converted / total * 100) if total > 0 else 0
    margin = sum((t.get("analytics", {}).get("margin_pct", 0) for t in trips))
    
    return InsightsSummary(
        totalInquiries=total,
        convertedToBooked=converted,
        conversionRate=round(rate, 1),
        avgResponseTime=round(random.uniform(2.5, 6.0), 1),  # Simulated for now
        pipelineValue=total * 15000, 
        pipelineVelocity=PipelineVelocity(
            stage1To2=1.2,
            stage2To3=2.4,
            stage3To4=4.1,
            stage4To5=0.5,
            stage5ToBooked=1.1,
            averageTotal=9.3
        )
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
    
    total_trips = len(trips)
    for stage_id, stage_name in stages_config:
        count = stage_counts[stage_id]
        # Only show timing data when there are actual trips; otherwise null/0
        if count > 0 and total_trips > 0:
            avg_time = round(random.uniform(1.0, 15.0), 1)
            exit_rate = round(random.uniform(30.0, 95.0), 1)
            avg_exit = round(random.uniform(2.0, 20.0), 1)
        else:
            avg_time = 0.0
            exit_rate = 0.0
            avg_exit = 0.0
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
        packet = trip.get("extracted") or trip.get("packet") or {}
        feedback = packet.get("feedback") or trip.get("analytics", {}).get("latest_feedback")

        if feedback and isinstance(feedback, dict):
            rating = feedback.get("rating")
            if rating and isinstance(rating, (int, float)):
                agent_data[uid]["ratings"].append(float(rating))

    # Build final metrics objects
    team_metrics = []
    for uid, stats in agent_data.items():
        ratings = stats["ratings"]
        # Use simple mean for CSAT; default to 4.5 if no ratings yet (baseline expectation)
        csat = round(sum(ratings) / len(ratings), 1) if ratings else 4.5
        
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
    return [
        BottleneckAnalysis(
            stageId="decision",
            stageName="Feasibility & Decision",
            avgTimeInStage=24.5,
            isBottleneck=True,
            severity="medium",
            primaryCauses=[
                BottleneckCause(
                    cause="Missing Budget Clarification",
                    percentage=45.0,
                    affectedTrips=12,
                    suggestedAction="Request budget minimums upfront"
                )
            ]
        )
    ]

def compute_revenue_metrics(trips: list, days: int = 30) -> RevenueMetrics:
    """
    Calculate revenue and forecasting metrics from trip data.
    
    Booked Revenue = Σ(budget where status == booked)
    Projected Revenue = Σ(budget * stage_probability)
    Total Pipeline Value = Σ(budget for non-booked active trips)
    Near Close Revenue = Σ(budget for output/safety stages)
    """
    now = datetime.now(timezone.utc)
    
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
        packet = trip.get("extracted", {}) or trip.get("packet", {}) or {}
        budget = packet.get("budget", {}) or {}
        # Some sample data has "value" as a string or nested. Normalise to float.
        raw_val = budget.get("value", 0)
        try:
            val = float(raw_val) if raw_val is not None else 0.0
        except (ValueError, TypeError):
            val = 0.0
            
        status = trip.get("status", "new")
        stage = trip.get("meta", {}).get("stage", "discovery")
        
        if status == "booked":
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
        analytics = trip.get("analytics") or {}
        
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
