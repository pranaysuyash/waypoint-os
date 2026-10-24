from typing import List, Dict, Optional, Literal, Any
from pydantic import BaseModel, Field


class CurrencyTotal(BaseModel):
    currency: str
    amount: float
    amountDecimal: str = Field(default="0", description="Exact recorded decimal sum before display formatting")
    minorUnitDigits: int = 2
    tripCount: int = Field(default=0)


class MonetaryMeasure(BaseModel):
    """Money retains its unit and missing-evidence state; no implicit FX."""

    availability: Literal["available", "partial", "unavailable"] = "unavailable"
    totals: List[CurrencyTotal] = Field(default_factory=list)
    evidenceTripCount: int = 0
    missingAmountTripCount: int = 0
    missingCurrencyTripCount: int = 0
    excludedPreviewTripCount: int = 0
    reason: str = "No evidence recorded."


class CommercialOutcomes(BaseModel):
    budgetPipeline: MonetaryMeasure = Field(default_factory=MonetaryMeasure)
    weightedPipelineBudget: MonetaryMeasure = Field(default_factory=MonetaryMeasure)
    nearCloseBudget: MonetaryMeasure = Field(default_factory=MonetaryMeasure)
    bookedCustomerValue: MonetaryMeasure = Field(default_factory=MonetaryMeasure)
    recordedCustomerCollections: MonetaryMeasure = Field(default_factory=MonetaryMeasure)
    agencyEarnedRevenue: MonetaryMeasure = Field(default_factory=MonetaryMeasure)
    agencyRealizedRevenue: MonetaryMeasure = Field(default_factory=MonetaryMeasure)


class ActivationSummary(BaseModel):
    """Lifetime agency progress derived from persisted work, never link clicks."""

    inquiryCount: int = 0
    needsDetailsCount: int = 0
    readyBriefCount: int = Field(default=0, description="Inquiries with canonical quote-ready evidence or a recorded approved brief")
    reviewedBriefCount: int = 0
    planningStartedCount: int = 0
    firstValueAchieved: bool = False
    nextAction: Literal["add_inquiry", "resolve_details", "review_brief", "continue_work"] = "add_inquiry"
    nextTripId: Optional[str] = None


class MonthlyRevenue(BaseModel):
    month: str
    revenue: Optional[float] = Field(default=None, description="Deprecated single-currency customer booking value; not agency revenue")
    inquiries: int = Field(default=0)
    booked: int = Field(default=0)
    currency: Optional[str] = None
    customerValueByCurrency: List[CurrencyTotal] = Field(default_factory=list)


class RevenueMetrics(BaseModel):
    period: str = Field(default="30d")
    periodStart: Optional[str] = None
    periodEnd: Optional[str] = None
    snapshotBasis: str = "Pipeline budgets and recorded collections are current cumulative snapshots."
    currency: Optional[str] = Field(default=None, description="Unit of legacy scalar fields; null when units differ or evidence is incomplete")
    totalPipelineValue: Optional[float] = Field(default=None, description="Deprecated single-currency pipeline budget, never earned revenue")
    bookedRevenue: Optional[float] = Field(default=None, description="Deprecated alias for receipt-backed customer booking value, never agency revenue")
    projectedRevenue: Optional[float] = Field(default=None, description="Deprecated assumed customer value (booked value plus stage-weighted budgets)")
    nearCloseRevenue: Optional[float] = Field(default=None, description="Deprecated single-currency budget of output/safety pipeline stages")
    avgTripValue: Optional[float] = Field(default=None, description="Deprecated mean budget in one known currency")
    revenueByMonth: List[MonthlyRevenue] = Field(default_factory=list)
    commercial: CommercialOutcomes = Field(default_factory=CommercialOutcomes)



class PipelineVelocity(BaseModel):
    stage1To2: float = Field(default=0.0)
    stage2To3: float = Field(default=0.0)
    stage3To4: float = Field(default=0.0)
    stage4To5: float = Field(default=0.0)
    stage5ToBooked: float = Field(default=0.0)
    averageTotal: float = Field(default=0.0)


class InsightsSummary(BaseModel):
    # FND-0345 / roadmap invariant 3: counts must declare their basis —
    # "paged_total" (canonical no-truncation pager) or "capped_sample" (the
    # count came from a bounded page and is NOT a tenant-wide total).
    count_basis: str = Field(
        default="paged_total",
        description='How the counts were computed: "paged_total" | "capped_sample"',
    )
    totalInquiries: int = Field(default=0)
    convertedToBooked: int = Field(default=0)
    conversionRate: float = Field(default=0.0)
    avgResponseTime: Optional[float] = Field(
        default=None,
        description="Hours from creation to first status transition; None until timing data exists",
    )
    pipelineValue: Optional[float] = Field(default=None, description="Deprecated single-currency current pipeline budget")
    gmv: Optional[float] = Field(
        default=None,
        description="Deprecated single-currency receipt-backed customer booking value; not budget or agency revenue",
    )
    currency: Optional[str] = None
    period: str = "all"
    periodStart: Optional[str] = None
    periodEnd: Optional[str] = None
    activation: ActivationSummary = Field(default_factory=ActivationSummary)
    pipelineVelocity: PipelineVelocity = Field(default_factory=PipelineVelocity)


class StageMetrics(BaseModel):
    stageId: str
    stageName: str
    tripCount: int
    avgTimeInStage: Optional[float] = Field(
        default=None, description="Mean dwell hours from status_history; None without evidence"
    )
    exitRate: Optional[float] = Field(
        default=None, description="Percent of entrants that exited the stage; None without evidence"
    )
    avgTimeToExit: Optional[float] = Field(
        default=None, description="Mean dwell hours among exited trips; None without evidence"
    )


class TeamMemberMetrics(BaseModel):
    userId: str
    name: str
    role: str
    activeTrips: int
    completedTrips: int
    conversionRate: float
    avgResponseTime: Optional[float] = Field(default=None, description="Not yet computed from real data")
    customerSatisfaction: Optional[float] = Field(
        default=None, description="Mean of real feedback ratings; None until ratings exist"
    )
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
