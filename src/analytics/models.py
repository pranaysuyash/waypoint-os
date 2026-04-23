from typing import List, Dict, Optional, Literal, Any
from pydantic import BaseModel, Field


class MonthlyRevenue(BaseModel):
    month: str
    revenue: float = Field(default=0.0)
    inquiries: int = Field(default=0)
    booked: int = Field(default=0)


class RevenueMetrics(BaseModel):
    period: str = Field(default="30d")
    totalPipelineValue: float = Field(default=0.0)
    bookedRevenue: float = Field(default=0.0)
    projectedRevenue: float = Field(default=0.0)
    nearCloseRevenue: float = Field(default=0.0)
    avgTripValue: float = Field(default=0.0)
    revenueByMonth: List[MonthlyRevenue] = Field(default_factory=list)



class PipelineVelocity(BaseModel):
    stage1To2: float = Field(default=0.0)
    stage2To3: float = Field(default=0.0)
    stage3To4: float = Field(default=0.0)
    stage4To5: float = Field(default=0.0)
    stage5ToBooked: float = Field(default=0.0)
    averageTotal: float = Field(default=0.0)


class InsightsSummary(BaseModel):
    totalInquiries: int = Field(default=0)
    convertedToBooked: int = Field(default=0)
    conversionRate: float = Field(default=0.0)
    avgResponseTime: float = Field(default=0.0)
    pipelineValue: float = Field(default=0.0)
    pipelineVelocity: PipelineVelocity = Field(default_factory=PipelineVelocity)


class StageMetrics(BaseModel):
    stageId: str
    stageName: str
    tripCount: int
    avgTimeInStage: float
    exitRate: float
    avgTimeToExit: float


class TeamMemberMetrics(BaseModel):
    userId: str
    name: str
    role: str
    activeTrips: int
    completedTrips: int
    conversionRate: float
    avgResponseTime: float
    customerSatisfaction: float
    currentWorkload: Literal["under", "optimal", "over", "critical"]
    workloadScore: float


class BottleneckCause(BaseModel):
    cause: str
    percentage: float
    affectedTrips: int
    suggestedAction: str


class BottleneckAnalysis(BaseModel):
    stageId: str
    stageName: str
    avgTimeInStage: float
    isBottleneck: bool
    severity: Literal["low", "medium", "high", "critical"]
    primaryCauses: List[BottleneckCause]


class QualityScore(BaseModel):
    overall: float
    breakdown: Dict[str, float]


class AnalyticsPayload(BaseModel):
    """
    Stored inside each trip_id.json natively under `"analytics"` 
    """
    margin_pct: float
    quality_score: float
    quality_breakdown: Dict[str, float]
    requires_review: bool
    review_reason: Optional[str] = None
    
    # Wave 10: Feedback-Driven Actioning
    feedback_reopen: bool = Field(default=False)
    feedback_severity: Optional[Literal["low", "medium", "high", "critical"]] = None
    followup_needed: bool = Field(default=False)
    recovery_status: Optional[str] = None # e.g. "PENDING_NOTIFY", "IN_RECOVERY"

    # Wave 11: Real-time SLA Tracking
    recovery_started_at: Optional[str] = None
    recovery_deadline: Optional[str] = None
    is_escalated: bool = Field(default=False)
    sla_status: Optional[Literal["on_track", "at_risk", "breached"]] = None
    owner_review_deadline: Optional[str] = None
    escalation_severity: Optional[Literal["high", "critical"]] = None
    approval_required_for_send: bool = Field(default=False)
    send_policy_reason: Optional[str] = None
    revision_count: int = Field(default=0)


class OperationalAlert(BaseModel):
    """
    High-priority incident alert for the owner dashboard.
    """
    id: str
    tripId: str
    type: Literal["critical_feedback", "trend_decline", "sla_breach"]
    severity: Literal["high", "critical"]
    message: str
    timestamp: str
    isDismissed: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)
