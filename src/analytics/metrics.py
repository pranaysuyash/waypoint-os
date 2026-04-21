from typing import List, Optional
from datetime import datetime, timezone
import random

from src.analytics.models import (
    InsightsSummary,
    PipelineVelocity,
    PipelineStage,  # Will fake this for logic output
    StageMetrics,
    TeamMemberMetrics,
    BottleneckAnalysis,
    BottleneckCause
)

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
