# Tracking Plan Audit & Analysis

> Based on **analytics-tracking** skill (`~/.hermes/skills/agents/analytics-tracking/SKILL.md`)

## 1. Current State: Event Inventory

### 1.1 System-Generated Events (Pipeline State)

These fire automatically as trips move through the spine pipeline:

| Event | Source | Properties | Trigger |
|-------|--------|------------|---------|
| `stage_transition` | `TripEventLogger.log_stage_transition()` | trip_id, stage, actor, description, pre_state, post_state, state, decision_type, reason | Spine pipeline phase completion |
| `packet.extracted` | `orchestration.py` | packet_id, envelope_count | Extraction pipeline completes |
| `packet.failed` | `orchestration.py` | error | Extraction exception |
| `validation.completed` | `orchestration.py` | status, gate, reasons | NB01 gate evaluation |
| `decision.completed` | `orchestration.py` | decision_state, decision_type | Decision engine runs |
| `strategy.built` | `orchestration.py` | session_goal | Strategy construction |
| `safety.validated` | `orchestration.py` | is_safe, leak_count | Leakage check completes |

**Canonical stage names:** INTAKE, PACKET, DECISION, STRATEGY, OUTPUT, SAFETY

### 1.2 Computed Metrics (Aggregated)

| Metric | Model | Source | Values |
|--------|-------|--------|--------|
| Pipeline velocity | `PipelineVelocity` | `metrics.py` | stage1To2, stage2To3, stage3To4, stage4To5, stage5ToBooked, averageTotal (days) |
| Revenue | `RevenueMetrics` | `metrics.py` | bookedRevenue, projectedRevenue, pipelineValue, nearCloseRevenue, avgTripValue |
| Quality | `AnalyticsPayload` | `engine.py` | completeness, feasibility, risk, profitability, overall quality_score |
| Stage metrics | `StageMetrics` | `metrics.py` | tripCount, avgTimeInStage, exitRate, avgTimeToExit |
| Team metrics | `TeamMemberMetrics` | `metrics.py` | activeTrips, completedTrips, conversionRate, customerSatisfaction, workloadScore |
| Bottlenecks | `BottleneckAnalysis` | `metrics.py` | stageId, avgTimeInStage, isBottleneck, severity, primaryCauses |

### 1.3 Telemetry Events (Diagnostic)

| Event | Source | Properties |
|-------|--------|------------|
| `spine_telemetry.*` (daily JSONL) | `intake.telemetry.emit_telemetry()` | event_type, data, timestamp |
| Decision metrics | `decision.telemetry.DecisionMetrics` | decision_type, source, latency_ms, cache_hit, llm_used, cost_inr |

### 1.4 Alerts (Operational)

| Alert Type | Trigger | Severity |
|------------|---------|----------|
| `critical_feedback` | Trip feedback rating <= 2 | critical / high |
| `sla_breach` | Recovery deadline passed | critical |
| `at_risk` | Recovery deadline within 30 min | high |

---

## 2. Audit Against analytics-tracking Skill Framework

### 2.1 Naming Convention

| Criteria | Status | Finding |
|----------|--------|---------|
| Object-Action format | 🟡 Partial | Stage transitions use `stage_transition` (good), but internal events use dotted form (`packet.extracted`, `decision.completed`) while stage enums use UPPER_SNAKE (`INTAKE`, `PACKET`) — inconsistent |
| Lowercase with underscores | 🟡 Partial | Mix of `snake_case` and `dotted.case` across event types |
| Specific vs generic | ✅ Good | Events carry context in properties, not in names |
| Documented decisions | ❌ Missing | No tracking plan document exists |

### 2.2 Event Types Coverage

| Type | Status | What's tracked |
|------|--------|----------------|
| Pageviews | ❌ N/A | This is an API backend, not a web app |
| User Actions | ❌ Missing | No operator action events (override, reassign, skip, dismiss) |
| System Events | ✅ Covered | All pipeline stage transitions, quality assessments, decision outcomes |
| Custom Conversions | 🟡 Partial | Pipeline funnel stages exist (discovery→packet→decision→strategy→output→booked) but no explicit conversion event |

### 2.3 Event Properties

| Category | Status | Finding |
|----------|--------|---------|
| Standard properties | 🟡 Partial | Events carry trip_id, stage, actor — but no consistent user context (user_id, role, agency) on every event |
| Contextual properties | ✅ Good | Decision events carry decision_state, hard_blockers; safety events carry is_safe, leak_count |
| No PII | ✅ Good | No PII detected in event payloads |

### 2.4 Funnel Completeness

| Funnel Step | Tracked? | Notes |
|-------------|----------|-------|
| Inquiry received | ✅ | Trip created in store |
| Extraction complete | ✅ | Packet state logged |
| Validation passed | ✅ | NB01 gate verdict |
| Decision made | ✅ | Decision state recorded |
| Suitability screened | ✅ | Flag count tracked |
| Strategy built | ✅ | Session strategy created |
| Output delivered | 🟡 | Bundle creation tracked but no "sent_to_traveler" event |
| Booked | 🟡 | Status tracked in TripStore but no explicit booking completion event |

### 2.5 Tool Integration

| Tool | Status | Note |
|------|--------|------|
| GA4 | ❌ Not integrated | All analytics in-app only |
| Mixpanel | ❌ Not integrated | No external analytics platform |
| PostHog | ❌ Not integrated | No external analytics platform |
| Segment | ❌ Not integrated | No external analytics platform |

All analytics live inside the application database. There is no pipeline to external analytics tools for marketing, funnel analysis, or user behavior tracking.

---

## 3. Identified Gaps

### Gap 1: Missing Operator Action Events (Critical)

The biggest gap. The system knows when pipeline stages complete but has zero visibility into:

- Operator overrides of system decisions
- Manual trip reassignments
- Consultation requests between operators
- Quick replies, dismissals, approvals
- Time spent by operators reviewing a trip before taking action
- Which operators are fastest/slowest per stage

**Evidence:** `compute_team_metrics()` explicitly sets `avgResponseTime=None` with comment "Explicitly unavailable: no real response-time data yet" (line 211, metrics.py).

### Gap 2: No External Analytics Pipeline

All data stays in the app database. No events are sent to:
- GA4 / PostHog / Mixpanel for product analytics
- Segment for downstream routing
- Any marketing or attribution tool

**Impact:** Cannot measure operator adoption, feature usage, or create funnel visualizations outside the app.

### Gap 3: Hardcoded / Placeholder Metrics

| Location | Value | Issue |
|----------|-------|-------|
| `metrics.py:88` | `random.uniform(2.5, 6.0)` | avgResponseTime is random |
| `metrics.py:117` | `random.uniform(1.0, 15.0)` | avgTimeInStage is random |
| `metrics.py:118` | `random.uniform(30.0, 95.0)` | exitRate is random |
| `metrics.py:220-236` | All hardcoded | bottleneck analysis is static |
| `metrics.py:148` | Comment notes | days parameter unused, no date-based filtering on trips |

### Gap 4: Inconsistent Event Naming

- Pipeline events: `packet.extracted`, `decision.completed` (dotted)
- Stage constants: `INTAKE`, `PACKET` (UPPER_SNAKE)
- Computed fields: `stage1To2`, `stage2To3` (camelCase)
- Models: `avgTimeInStage`, `exitRate` (camelCase vs snake_case)

The skill recommends **Object-Action** with lowercase underscores (`stage_transition`, `pipeline_extracted`) consistently.

### Gap 5: No Property Taxonomy Document

No single source of truth that defines:
- What each event means
- What properties it carries
- What triggers it
- Who owns it

### Gap 6: No Conversion Events

The funnel analysis (STAGE_CONVERSION_PROBABILITIES in metrics.py) uses fixed probabilities by stage name rather than actual conversion events. There is no `trip_converted_to_booked` event that captures the moment of conversion with deal value, operator, and time.

---

## 4. Recommended Tracking Plan

### 4.1 Standardized Event Taxonomy

Adopt the **Object-Action** convention from the analytics-tracking skill consistently:

```markdown
# Standardized Event Names

## Pipeline Events
pipeline_extracted       # Raw data → CanonicalPacket
pipeline_validated       # Packet validation complete
pipeline_gate_evaluated  # NB01 or NB02 gate ran (property: gate_name)
pipeline_decision_made   # Decision engine output (property: decision_state)
pipeline_suitability_scored  # Activity suitability check
pipeline_strategy_built  # Session strategy constructed
pipeline_output_created  # Internal + traveler bundles ready
pipeline_safety_checked  # Sanitization + leakage check
pipeline_fees_calculated # Trip fee computation

## Operator Action Events (New — Critical Gap)
operator_trip_assigned   # Trip assigned to an operator
operator_trip_reviewed   # Operator opened a trip for review
operator_override_made   # Operator overrode a system decision
operator_approval_given  # Operator approved a traveler message send
operator_trip_reassigned # Trip moved to another operator
operator_note_added      # Internal note added to a trip

## Conversion Events (New)
trip_booked              # Trip converted to booked (property: deal_value)
trip_closed              # Trip closed without booking (property: reason)
trip_inquiry_converted   # Inquiry → active pipeline (property: source)
```

**Standard properties on every event:**

| Property | Type | Source |
|----------|------|--------|
| trip_id | string | Always available |
| timestamp | ISO-8601 | Auto |
| actor_id | string | Current user |
| actor_role | string | junior_agent / senior_agent / admin |
| agency_id | string | Tenant context |
| source | string | system / operator / automation |

### 4.2 Recommended Tool Integration

| Tool | Purpose | Effort |
|------|---------|--------|
| **PostHog** | Self-hosted or cloud. Product analytics, funnel visualization, session replays. Best fit for B2B SaaS. | Low — single SDK, can self-host |
| **Segment** | CDP — route events to multiple destinations. Overkill unless multi-tool is needed. | Medium |
| **Custom analytics dashboard** | Already exists via your `src/analytics/` stack. Keep as primary. | Done |

**Recommendation:** PostHog for funnel + user behavior analytics alongside your existing in-app analytics.

### 4.3 Funnel Definition

```markdown
# Conversion Funnel

1. Inquiry Received          → event: trip_created
2. Extraction Complete       → event: pipeline_extracted
3. Validation Passed         → event: pipeline_gate_evaluated (gate_name: NB01, verdict: PASS)
4. Decision Made             → event: pipeline_decision_made (decision_state: PROCEED)
5. Suitability Screened      → event: pipeline_suitability_scored (critical_flags: 0)
6. Strategy Built            → event: pipeline_strategy_built
7. Output Created            → event: pipeline_output_created
8. Sent to Traveler          → event: pipeline_output_sent (add this — currently missing)
9. Booked                    → event: trip_booked

Dropoff analysis: Track which step has the highest exit rate.
Bottleneck analysis: Track avg time between steps (already partially computed as pipeline velocity).
```

### 4.4 Metrics That Need Fixing

| Current | Fix | Priority |
|---------|-----|----------|
| `random.uniform()` for avgResponseTime | Add real operator response-time tracking via `operator_trip_assigned` → first `operator_trip_reviewed` delta | P0 |
| `random.uniform()` for stage timing | Use actual stage transition timestamps (already partially computed in pipeline_velocity) | P1 |
| Hardcoded bottleneck analysis | Generate from real stage duration data | P1 |
| Unused `days` parameter | Implement date-based trip filtering | P2 |

---

## 5. Implementation Recommendations

### Phase 1: Operator Action Events (P0)

Add events for the most common operator actions:

```python
# src/analytics/logger.py — add operator action telemetry
@staticmethod
def log_operator_action(
    trip_id: str,
    action: str,
    actor_id: str,
    actor_role: str,
    properties: Dict[str, Any] = None,
):
    """Log an operator action to the audit trail + external analytics."""
    event = AnalyticsEvent(
        event=f"operator_{action}",
        properties={
            "trip_id": trip_id,
            "actor_id": actor_id,
            "actor_role": actor_role,
            **(properties or {}),
        }
    )
    AuditStore.log_event(event)
    # Also emit to PostHog / Segment when integrated
```

### Phase 2: Fix Placeholder Metrics (P1)

Replace `random.uniform()` calls with real computed values from stage transition timestamps. The pipeline_velocity computation in `metrics.py` already does this partially — extend it to cover avgResponseTime and per-stage timing.

### Phase 3: External Analytics Integration (P2)

Pick one of:
- **PostHog**: `pip install posthog`, initialize once, call `posthog.capture()` alongside existing logger
- **Custom webhook**: Emit events to a webhook for downstream processing

---

## 6. Summary

| # | Gap | Severity | Effort |
|---|-----|----------|--------|
| 1 | No operator action events | Critical | Medium |
| 2 | Random/hardcoded metrics | High | Low |
| 3 | No external analytics pipeline | Medium | Medium |
| 4 | Inconsistent event naming | Low | Low |
| 5 | No property taxonomy document | Low | Low |
| 6 | No conversion events | Medium | Low |

### Reference

This audit was conducted using the **analytics-tracking** skill at `~/.hermes/skills/agents/analytics-tracking/SKILL.md`. The skill provides:
- Event naming conventions (Section: Event Naming Conventions)
- Tracking plan framework (Section: Tracking Plan Framework)
- Event types taxonomy (Section: Event Types)
- Essential events by category (Section: Essential Events)
- Tool integration patterns (Section: Tool Integrations)
- Validation checklist (Section: Debugging and Validation)

---

## 7. Additional Metrics Worth Tracking

These metrics go beyond the analytics-tracking skill's scope. They cover AI performance, operational efficiency, pipeline health, and business metrics specific to an AI-powered travel agency product.

### 7.1 AI Performance Metrics

| Metric | Definition | How to Measure | Tracked? |
|--------|-----------|----------------|----------|
| **AI override rate** | % of trips where operator overrode the AI's decision (e.g., changed decision_state, edited packet, rejected recommendation) | Compare original `decision.decision_state` against final state after operator action | No — requires operator action events |
| **First-pass yield** | % of trips that complete all pipeline stages without any escalation or operator intervention | Count trips where `early_exit=false` AND no operator override occurred, divided by total runs | 🟡 Partial — `early_exit` exists in SpineResult but operator overrides are not tracked |
| **AI confidence distribution** | Histogram of confidence scores across all decisions, bucketed (0-25, 25-50, 50-75, 75-100) | Aggregate `ConfidenceScorecard` values from DecisionResult across all runs | 🟡 Partial — `ConfidenceScorecard` exists in decision.py but is not aggregated into analytics |
| **LLM cost per trip** | Sum of all LLM call costs incurred for a single trip | Aggregate `decision.telemetry.DecisionMetrics.cost_inr` across all decisions for a trip ID | 🟡 Partial — per-decision cost exists but no per-trip aggregation |
| **Decision source distribution** | % breakdown: cache vs rule-based vs LLM vs default fallback | Track `DecisionMetrics.source` for every decision | 🟡 Partial — per-decision source tracked in telemetry but no dashboard-level aggregation |
| **Cache hit rate** | % of decisions served from decision cache without LLM call | `cache_hit / total_decisions` over a time window | 🟡 Tracked per-decision in decision.telemetry but no aggregate |
| **Model fallback rate** | How often the primary LLM fails and a fallback model takes over | Count fallback chain invocations in decision.telemetry | No |
| **Average LLM latency per stage** | P50/P95/P99 latency for LLM calls in the decision stage | Already in `DecisionTelemetry.latency_ms` — just needs dashboard aggregation | 🟡 Available per-decision |

### 7.2 Operational Efficiency Metrics

| Metric | Definition | How to Measure | Tracked? |
|--------|-----------|----------------|----------|
| **Operator response time** | Time from trip assignment to operator's first action (review, reply, override) | Compute delta between `assigned_at` timestamp and first operator action event | No — `avgResponseTime` in metrics.py is `random.uniform()` with comment "Explicitly unavailable" |
| **Queue depth** | Number of trips awaiting operator attention at any point in time | Count trips in `new` or `assigned` status with no recent operator action | No |
| **Backlog age** | How long trips sit in queue without operator action | Compute (now - `created_at`) for unassigned trips | 🟡 Partial — created_at exists but unassigned-time window is not tracked |
| **SLA compliance rate** | % of trips where recovery actions completed within the SLA deadline | Count trips with `recovery_deadline` where recovery completed before deadline, divided by total SLA-tracked trips | 🟡 Partial — `sla_status` is tracked per trip (breached/at_risk/on_track) but no aggregate SLA rate |
| **Escalation recovery rate** | % of escalated trips (NB01/NB02) that eventually recover and proceed to booking | Track escalation event → eventual trip status (booked vs closed) | No |
| **Mean time to recovery** | Average time from escalation event to trip being unblocked | Compute delta between escalation timestamp and resolution timestamp | 🟡 Partial — `recovery_deadline` is a target, not actual recovery time |
| **Rework rate** | % of trips that require 2+ revision cycles before completion | Track `revision_count` in analytics payload, compute % where count > 1 | 🟡 Partial — `revision_count` exists in AnalyticsPayload but may not be reliably incremented |
| **Operator workload balance** | Distribution of active trips across operators | Group active trips by `assigned_to`, compute Gini coefficient or std deviation | 🟡 Partial — `workloadScore` in TeamMemberMetrics but uses linear formula |

### 7.3 Pipeline Health Metrics

| Metric | Definition | How to Measure | Tracked? |
|--------|-----------|----------------|----------|
| **Stage exit rate (real)** | % of trips that drop off at each pipeline stage, using real transition data | Count trips reaching stage N vs stage N+1 | ❌ Placeholder — `exitRate` in compute_pipeline_metrics() is `random.uniform()` |
| **Gate escalation rate** | % of trips that hit NB01 or NB02 escalations | `gate_escalations / total_runs` over a time window | 🟡 Tracked per-run in OTel spans but no dashboard aggregate |
| **Error rate per stage** | % of pipeline runs that throw per stage | Count `pipeline_extraction_failed`, `pipeline_decision_failed`, etc. | No — exceptions are caught but not counted |
| **Pipeline completion rate** | % of started pipelines that complete vs early exit | `completed_runs / (completed + early_exit)` | 🟡 `early_exit` boolean in SpineResult but no aggregate |
| **Suitability flag rate** | % of trips with critical suitability flags | `trips_with_critical_flags / total_trips` | 🟡 OTel span tracks critical_count per-run but no dashboard aggregate |
| **Stage duration trend** | Is each stage getting faster or slower over time? | Plot avg/p50/p95 duration per stage by day/week | 🟡 Pipeline velocity computes avg but not trending |
| **Gate verdict distribution** | % PASS vs DEGRADE vs ESCALATE per gate per period | Aggregate NB01/NB02 verdicts | 🟡 Per-run in OTel spans but no aggregate |

### 7.4 Business & Commercial Metrics

| Metric | Definition | How to Measure | Tracked? |
|--------|-----------|----------------|----------|
| **Cost to serve per trip** | Total cost (LLM calls + operator time) per booked trip | Sum `cost_inr` across all decisions + estimated operator time cost for the trip | No — operator time not tracked |
| **Revenue per operator** | Total booked revenue grouped by assigned operator | Aggregate `bookedRevenue` by `assigned_to` | 🟡 Partial — team metrics exist but avgResponseTime is random |
| **Margin by trip dimension** | Margin % broken down by destination, party size, trip stage | Group `calculate_margin()` output by destination / party_size / stage | 🟡 `calculate_margin()` in engine.py has real logic but no dimensional aggregation |
| **Deal velocity** | Time from inquiry to booked, by source/channel | Delta between `created_at` and `status=booked` timestamp, grouped by source | 🟡 Partially in pipeline_velocity but doesn't break down by source |
| **Win/loss by source** | Conversion rate by inquiry source/origin | `booked / total` per source value | No |
| **Quote-to-book ratio** | % of trips that receive a quote and then convert to booked | Track quote generation events vs booking events | No |
| **Revenue per pipeline stage** | Revenue value of trips currently at each stage | Aggregate `budget.value` by trip stage | 🟡 Partially — pipeline_value exists but per-stage breakdown is computed as `totalPipelineValue` only |
| **Average deal value by source** | Avg trip budget by inquiry channel | Group `budget.value` by source field | No |

### 7.5 Safety & Quality Metrics

| Metric | Definition | How to Measure | Tracked? |
|--------|-----------|----------------|----------|
| **Leakage rate** | % of pipeline runs that fail the traveler-safe leakage check | `leaks_found / total_runs` | 🟡 Tracked per-run (is_safe boolean) but no aggregate |
| **CSAT trend** | Average customer satisfaction rating over time (weekly/monthly) | Compute rolling average of feedback ratings across all trips | 🟡 Computed per-operator but no time-series trend |
| **Quality score trend** | Average overall quality_score over time | Rolling average of `AnalyticsPayload.quality_score` | No |
| **Negative feedback rate** | % of trips receiving feedback <= 2 out of 5 | `trips_with_rating_leq_2 / trips_with_feedback` | 🟡 feedback_reopen tracked per trip but no aggregate rate |
| **Safety bypass rate** | % of trips where operator bypassed a safety warning | Track safety override actions | No — requires operator action events |

### 7.6 Recommended Priority

| Priority | Metric | Why Now | Dependency |
|----------|--------|---------|------------|
| **P0** | AI override rate | Core signal of AI quality — tells you if the system is working | Operator action events (Gap 1 from Section 6) |
| **P0** | First-pass yield | Single-number health score for the entire pipeline | Early exit + escalation aggregation |
| **P0** | Real stage exit rates | Replace 3 `random.uniform()` calls — your dashboard is showing fake data | Stage transition timestamps (already exist) |
| **P0** | Operator response time | Replace `random.uniform()` — currently impossible to measure operator efficiency | Per-trip assignment-to-action tracking |
| **P1** | LLM cost per trip | You can't optimize costs without per-trip aggregation | Aggregation of existing decision.cost_inr data |
| **P1** | Escalation recovery rate | Are gate escalations useful or noise? | Escalation + trip outcome tracking |
| **P1** | Margin by destination | Which trip types make money vs lose money | Aggregation of existing margin logic |
| **P2** | Queue depth + backlog age | Operator workload and capacity planning | Timestamp queries on TripStore |
| **P2** | CSAT / Quality score trends | Is overall quality improving over time? | Rolling aggregate of existing scores |
| **P2** | Cost to serve | Unit economics by trip type | LLM cost + operator time tracking |

