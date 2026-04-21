# Dashboard Governance Wiring Implementation Plan
**Date**: 2026-04-20
**Scope**: Wire live telemetry metrics and analytics to owner dashboard surfaces, replacing mocks with real data sources and implementing margin/quality calculations.
**Companion docs**: `COVERAGE_MATRIX_2026-04-15.md` (Agency Owner P1 priority), `DATA_ARCHITECTURE.md`

---

## 1. Current State Assessment

### What's Working (Mock Data)
- `/owner/insights` page renders with `MOCK_INSIGHTS_SUMMARY`
- `/owner/reviews` page renders with `MOCK_REVIEWS`
- Basic API endpoints exist: `/api/stats`, `/api/trips`, `/api/pipeline`
- Governance hooks (`useGovernance.ts`) are implemented but bypassed
- Visual components (`RevenueChart`, `PipelineFunnel`, `TeamPerformanceChart`) exist

### What's Missing (Live Data)
- No backend analytics calculation endpoints
- No margin calculation logic
- No quote-quality scoring system
- No real-time pipeline metrics aggregation
- No team performance analytics
- No bottleneck detection algorithms

### Data Sources Available
- Trip data via `/api/trips` (currently mock)
- Pipeline stages via `/api/pipeline` (currently mock)
- Basic stats via `/api/stats` (currently mock)
- Spine API results (packet, decision, strategy, bundles)

---

## 2. Implementation Waves

### Wave 1: Backend Analytics Foundation
**Effort**: Medium (3-4 days)
**Impact**: High — establishes data pipeline foundation

#### 1a. Analytics Calculation Engine
**Files to create/modify**:
- `src/analytics/calculations.py` — Core analytics functions
- `src/analytics/models.py` — Analytics data models
- `spine-api/server.py` — Add `/analytics/*` endpoints

**Implementation**:
```python
# src/analytics/calculations.py
def calculate_conversion_metrics(trips: List[Trip]) -> ConversionMetrics:
    """Calculate conversion rates by stage and overall."""
    pass

def calculate_pipeline_velocity(trips: List[Trip]) -> PipelineVelocity:
    """Calculate average time between stages."""
    pass

def calculate_margin_metrics(trips: List[Trip]) -> MarginMetrics:
    """Calculate margin percentages and totals."""
    pass
```

**API Endpoints to Add**:
- `GET /api/analytics/insights?timeRange=30d` — Main insights summary
- `GET /api/analytics/pipeline-metrics` — Stage-by-stage metrics
- `GET /api/analytics/team-performance` — Agent performance data
- `GET /api/analytics/bottlenecks` — Bottleneck analysis

#### 1b. Margin Calculation Logic
**Business Logic**:
- Base margin: 15-25% depending on trip complexity
- Premium services: +5-10% margin
- Volume discounts: -2-5% margin
- Risk adjustments: ±2-5% based on destination/complexity

**Implementation**:
```python
def calculate_trip_margin(trip: Trip, strategy: StrategyOutput) -> MarginBreakdown:
    """Calculate margin for a single trip."""
    base_margin = 0.20  # 20%
    # Adjust based on complexity, destination risk, etc.
    return MarginBreakdown(...)
```

#### 1c. Quality Scoring System
**Scoring Dimensions**:
- Completeness: All required fields populated
- Feasibility: Budget/dates realistic
- Risk: Visa/health/safety concerns addressed
- Profitability: Margin meets agency targets

**Implementation**:
```python
def calculate_quote_quality_score(trip: Trip, decision: DecisionOutput) -> QualityScore:
    """Score quote quality 0-100."""
    completeness = calculate_completeness_score(trip)
    feasibility = calculate_feasibility_score(trip, decision)
    risk = calculate_risk_score(trip, decision)
    profitability = calculate_profitability_score(trip)

    return QualityScore(
        overall=weighted_average([completeness, feasibility, risk, profitability]),
        breakdown={...}
    )
```

### Wave 2: Frontend Data Wiring
**Effort**: Low (2-3 days)
**Impact**: High — connects UI to live data

#### 2a. Wire Governance Hooks
**Files to modify**:
- `frontend/src/hooks/useGovernance.ts` — Remove mock bypasses
- `frontend/src/lib/governance-api.ts` — Update API calls

**Changes**:
```typescript
// Before (bypassed)
export function useInsightsSummary(timeRange: TimeRange = '30d') {
  // Return mock data
  return { data: MOCK_INSIGHTS_SUMMARY, ... };
}

// After (live data)
export function useInsightsSummary(timeRange: TimeRange = '30d') {
  return useQuery({
    queryKey: ['insights', timeRange],
    queryFn: () => governanceApi.getInsightsSummary(timeRange),
  });
}
```

#### 2b. Update Owner Insights Page
**Files to modify**:
- `frontend/src/app/owner/insights/page.tsx` — Remove MOCK_ constants

**Changes**:
- Replace `MOCK_INSIGHTS_SUMMARY` with `useInsightsSummary()` hook
- Replace `MOCK_PIPELINE_METRICS` with `usePipelineMetrics()` hook
- Replace `MOCK_TEAM_METRICS` with `useTeamMetrics()` hook

#### 2c. Update Owner Reviews Page
**Files to modify**:
- `frontend/src/app/owner/reviews/page.tsx` — Remove mock data

**Changes**:
- Replace `MOCK_REVIEWS` with `useReviews()` hook
- Add real filtering and pagination

### Wave 3: Enhanced Analytics Features
**Effort**: Medium (3-4 days)
**Impact**: Medium — adds advanced insights

#### 3a. Bottleneck Detection
**Algorithm**:
- Identify stages with longest average time
- Flag trips stuck >2x average time
- Calculate stage exit rates

**Implementation**:
```python
def detect_bottlenecks(trips: List[Trip]) -> List[Bottleneck]:
    """Find workflow bottlenecks."""
    stage_times = calculate_stage_durations(trips)
    avg_times = {stage: mean(times) for stage, times in stage_times.items()}

    bottlenecks = []
    for stage, avg_time in avg_times.items():
        stuck_trips = [t for t in trips if get_time_in_stage(t, stage) > 2 * avg_time]
        if stuck_trips:
            bottlenecks.append(Bottleneck(stage=stage, stuck_count=len(stuck_trips)))

    return bottlenecks
```

#### 3b. Team Performance Analytics
**Metrics**:
- Conversion rate by agent
- Average response time
- Customer satisfaction scores
- Workload distribution

**Implementation**:
```python
def calculate_team_performance(trips: List[Trip], agents: List[Agent]) -> List[TeamMetrics]:
    """Calculate per-agent performance metrics."""
    return [
        TeamMetrics(
            agent_id=agent.id,
            conversion_rate=calculate_agent_conversion_rate(agent, trips),
            avg_response_time=calculate_agent_response_time(agent, trips),
            workload_score=calculate_workload_score(agent, trips),
        )
        for agent in agents
    ]
```

#### 3c. Revenue Analytics
**Charts to implement**:
- Monthly revenue trends
- Revenue by destination/type
- Margin analysis over time
- Revenue forecasting

**Implementation**:
- Extend `RevenueChart` component with real data
- Add revenue breakdown by category
- Implement forecasting algorithms

### Wave 4: Owner Review Workflows
**Effort**: Low-Medium (2-3 days)
**Impact**: High — enables owner oversight

#### 4a. Review Threshold System
**Logic**:
- High-value trips (>₹5L) require owner review
- Complex itineraries (multi-city, groups >6)
- High-risk destinations
- Margin outliers (<10% or >35%)

**Implementation**:
```python
def should_require_owner_review(trip: Trip, strategy: StrategyOutput) -> bool:
    """Determine if trip needs owner review."""
    if trip.value > 500000:  # ₹5L
        return True
    if len(trip.destinations) > 2:  # Multi-city
        return True
    # ... other criteria
    return False
```

#### 4b. Review Action Interface
**Features**:
- Approve/reject quotes
- Add owner notes
- Override pricing
- Escalate to senior management

**Implementation**:
- Extend review modal with action buttons
- Add owner annotation system
- Implement approval workflow

#### 4c. Review Analytics
**Metrics**:
- Review approval rates
- Average review time
- Common rejection reasons
- Review backlog trends

---

## 3. Testing Strategy

### Unit Tests
- Analytics calculation functions
- Margin algorithms
- Quality scoring logic
- API endpoint contracts

### Integration Tests
- End-to-end analytics pipeline
- Frontend hook integration
- Real-time data updates

### Acceptance Tests
- Owner can view live metrics
- Margin calculations are accurate
- Review workflows function correctly
- Performance meets SLA (<2s load times)

---

## 4. Rollout Plan

### Phase 1: Backend Only (Internal)
- Implement analytics engine
- Add API endpoints
- Test calculations with mock data
- **Duration**: 1 week

### Phase 2: Frontend Wiring
- Wire hooks to live APIs
- Remove mock data
- Test UI integration
- **Duration**: 3-4 days

### Phase 3: Enhanced Features
- Add bottleneck detection
- Implement team analytics
- Add review workflows
- **Duration**: 1 week

### Phase 4: Production Validation
- Load testing with real data
- Performance optimization
- User acceptance testing
- **Duration**: 3-4 days

---

## 5. Success Metrics

### Quantitative
- **Data Freshness**: <5 min latency for insights
- **Query Performance**: <2s for all analytics queries
- **Accuracy**: >95% match between calculated and expected metrics
- **Coverage**: >80% of trips have complete analytics data

### Qualitative
- **Owner Satisfaction**: Owners can answer key business questions
- **Actionability**: Insights lead to concrete business decisions
- **Reliability**: No data gaps or calculation errors in production
- **Performance**: Dashboard loads instantly

---

## 6. Risk Mitigation

### Technical Risks
- **Data Volume**: Implement pagination and caching for large datasets
- **Calculation Complexity**: Pre-compute expensive metrics during trip processing
- **API Performance**: Add database indexes and query optimization

### Business Risks
- **Data Accuracy**: Implement validation and reconciliation checks
- **Privacy Compliance**: Ensure no PII leakage in analytics
- **Cost Impact**: Monitor API usage and optimize expensive operations

### Operational Risks
- **Downtime**: Implement graceful degradation with cached data
- **Data Loss**: Add backup and recovery procedures
- **Support Load**: Create self-service troubleshooting guides

---

## 7. Dependencies & Prerequisites

### Required Before Starting
- ✅ Trip data persistence (Wave 1-5 complete)
- ✅ Spine API results storage
- ✅ Basic frontend routing (Wave 3-5 complete)
- ✅ Governance hook structure exists

### Parallel Work
- Database schema for analytics storage
- Caching layer for performance
- Monitoring and alerting setup

---

## 8. Next Steps

1. **Immediate**: Create `src/analytics/` module structure
2. **Week 1**: Implement core calculation functions
3. **Week 2**: Add API endpoints and wire frontend
4. **Week 3**: Enhanced features and testing
5. **Week 4**: Production deployment and monitoring

**Ready to proceed with Wave 1 implementation?**</content>
<parameter name="filePath">/Users/pranay/Projects/travel_agency_agent/Docs/DASHBOARD_GOVERNANCE_WIRING_PLAN_2026-04-20.md