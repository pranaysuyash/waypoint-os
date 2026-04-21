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
    MonthlyRevenue
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
    stages = [
        ("discovery", "Discovery & Intake"),
        ("packet", "Signal Extraction"),
        ("decision", "Feasibility & Decision"),
        ("strategy", "Strategy & Budget"),
        ("output", "Deliverables"),
        ("safety", "Safety & Compliance")
    ]
    
    total = len(trips)
    dist = []
    
    # Simple mocked simulation to give nice presentation from trips length
    for stage_id, stage_name in stages:
        stage_cnt = max(1, int(total * random.uniform(0.1, 0.4)))
        metrics.append(StageMetrics(
            stageId=stage_id,
            stageName=stage_name,
            tripCount=stage_cnt,
            avgTimeInStage=round(random.uniform(1.0, 15.0), 1),
            exitRate=round(random.uniform(30.0, 95.0), 1),
            avgTimeToExit=round(random.uniform(2.0, 20.0), 1)
        ))
    return metrics


def compute_team_metrics(trips: list, assignments: list, days: int = 30) -> List[TeamMemberMetrics]:
    # Hardcoded team for Wave 1
    return [
        TeamMemberMetrics(
            userId="usr_123",
            name="Alice Agent",
            role="agent",
            activeTrips=12,
            completedTrips=45,
            conversionRate=68.5,
            avgResponseTime=2.4,
            customerSatisfaction=4.8,
            currentWorkload="optimal",
            workloadScore=75.0
        ),
        TeamMemberMetrics(
            userId="usr_456",
            name="Bob Broker",
            role="agent",
            activeTrips=28,
            completedTrips=31,
            conversionRate=42.1,
            avgResponseTime=8.5,
            customerSatisfaction=4.1,
            currentWorkload="over",
            workloadScore=92.0
        )
    ]


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
