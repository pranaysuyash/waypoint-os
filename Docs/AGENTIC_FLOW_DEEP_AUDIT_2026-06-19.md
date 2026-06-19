# Agentic Flow Deep Audit — 2026-06-19

**Date:** 2026-06-19
**Repo:** `/Users/pranay/Projects/travel_agency_agent`
**Evidence Tier:** Tier 1 (static inspection of ~20 core files, 2000+ lines read in detail)
**Preceding:** `AGENTIC_FLOW_EVAL_AUDIT_2026-06-18.md`, `AGENTIC_FLOW_COMPREHENSIVE_AUDIT_2026-06-19.md` (superseded by this deeper pass)

---

## Part 1: Architecture Overview — What Actually Runs

### 1.1 The Spine Pipeline (the main entrypoint)

**File:** `src/intake/orchestration.py` (500+ lines)

The spine pipeline is a **single synchronous function** `run_spine_once()` that chains:
1. Extraction → Packet (L115-145)
2. Validation → NB01 Gate (L148-210)
3. Decision → NB02 Autonomy Gate (L213-260)
4. Suitability Assessment (L262-285)
5. Frontier Orchestration (L287-310) — gated by `enable_frontier_orchestration`
6. Strategy + Fee Calculation (L312-340)
7. Internal/Traveler Bundles (L342-370)
8. Sanitization + Leakage Check (L372-410)
9. Readiness Computation (L412-420)
10. Fixture Compare (optional) (L422-430)

**Critical observation:** This is a **monolithic pipeline** — no agent coordination, no parallel execution, no dependency graph. Each phase runs sequentially. The `stage_callback` parameter (L105) is the only extensibility point, and it's used for checkpointing, not agent coordination.

**Line 44-55:** `_emit_audit_event()` wraps `TripEventLogger.log_stage_transition()` — the audit trail is **best-effort** (catches Exception and logs warning at L54-55). If audit fails, the pipeline continues silently.

### 1.2 The Agent Supervisor Loop

**File:** `src/agents/runtime.py` (L255-430)

The `AgentSupervisor` runs a polling loop:
```
_run_loop() → sleep(interval_seconds) → run_once() → for each agent: scan() → acquire() → execute() → complete/fail
```

**Key lines:**
- **L295-300:** Exception in scan → emit AGENT_FAILED event → **continue to next agent** (no retry on scan failure)
- **L303-310:** For each work item, `coordinator.acquire()` returns `(acquired, reason, attempt)`
- **L311-328:** If not acquired → emit AGENT_RETRY or AGENT_DECISION with `skip` → **continue**
- **L341-356:** Execute → if exception → result = RETRY_PENDING with `str(exc)` as reason
- **L358-370:** If success → coordinator.complete(); if fail → coordinator.fail() with POISONED if terminal
- **L397-430:** `_emit_agent_event()` → wraps in `AgentEvent` → calls `self.audit.log()`

**Critical observation at L341:** When `agent.execute()` throws an exception, the error message becomes the `reason` string. There is **no structured error classification** — a network timeout and a data corruption error both become `str(exc)`.

### 1.3 The Extraction Service (Model Chain Fallback)

**File:** `spine_api/services/extraction_service.py` (700+ lines)

**The fallback loop (L310-440):**
```
models_to_try = _get_model_chain(extractor)  # returns [(model_name, extractor), ...]
for rank, (model_name, model_extractor) in enumerate(models_to_try):
    attempt = DocumentExtractionAttempt(...)  # DB row created
    try:
        result = await model_extractor.extract(...)
    except ExtractionProviderError as e:
        attempt.error_code = e.error_code
        # emit extraction_attempt_failed event
        if e.error_code not in RETRIABLE_ERRORS:
            break  # hard failure, stop chain
        continue  # retry with next model
    # success path
```

**Critical observations:**
- **L277:** `validate_pdf_pages()` runs **before** any DB mutation — good defensive design
- **L310:** `_get_model_chain()` (L169-183) normalizes any extractor into a list — handles ModelChain, NoopExtractor, and single extractors
- **L356-370:** Each failed attempt emits an `extraction_attempt_failed` event with full eval metadata including `failure_signature`, `failure_layer`, `next_fix_layer`
- **L393:** `logger.warning("Model %s failed with %s, trying next")` — **no cost tracking per failed attempt**
- **L442-449:** Unexpected exceptions (not ExtractionProviderError) → mark extraction as `failed` with `internal_error` → **re-raise** — the outer pipeline catches this

**Eval metadata emission (L184-201):**
```python
prompt_version = os.environ.get("EXTRACTION_PROMPT_VERSION", _EVAL_DEFAULTS["prompt_version"])
schema_version = os.environ.get("EXTRACTION_SCHEMA_VERSION", _EVAL_DEFAULTS["schema_version"])
```
**Line 184-188:** All version fields are **env-var defaults** — there is no runtime version tracking per extraction attempt. If you change `EXTRACTION_PROMPT_VERSION` between deploys, historical attempts have the new version, not the one that produced them.

### 1.4 The Eval Pipeline

**File:** `src/evals/agentic_feedback.py` (640+ lines)

**The aggregation function `aggregate_eval_records()` (L631-680):**
```
candidates = filter_eval_candidates(events)
filtered_by_window = [event for event in candidates if event.created_at >= window_start]
work_items = build_repeated_failure_signal(candidates, min_occurrences)
routing_metrics = build_routing_metrics(candidates, review_events)
canonical_records = build_canonical_evidence_records(candidates, review_events)
```

**Critical observations:**
- **L460-516:** `build_repeated_failure_signal()` groups by `failure_signature`, requires `min_occurrences` (default 3), then builds `AgenticEvalWorkItem` with severity, proposed_change, keep_if, revert_if, owner
- **L166-185:** `_build_work_item_routing()` maps failure_layer → recommendation profile from `_LAYER_RECOMMENDATIONS` (10 layers defined at L77-147)
- **L370-430:** `build_routing_metrics()` computes fallback_trigger_rate, review_correction_rate, false_escalation_rate, p50/p95 latency, cost_usd

**What's produced vs. what's consumed:**
- **Produced:** Work items with `failure_signature`, `severity`, `proposed_change`, `owner`, `keep_if`, `revert_if`
- **Consumed:** The API endpoint returns them. **Nothing in the codebase acts on them programmatically.** No agent reads work items and creates fix candidates. No scheduler triggers reruns. The loop is **open, not closed**.

### 1.5 The Recovery Agent

**File:** `src/agents/recovery_agent.py` (340 lines)

**Detection path (L115-165):**
```
_detect_stuck_trips():
    active_trips = self._trip_repo.list_active()
    for trip in active_trips:
        threshold_h = _get_stuck_thresholds().get(stage)  # intake: 48h, decision: 72h, review: 24h, booking: 336h
        hours_stuck = (now - updated_at).total_seconds() / 3600
        if hours_stuck >= threshold_h:
            stuck.append(StuckTrip(...))
```

**Recovery path (L168-200):**
```
_recover(trip):
    if self._is_trip_poisoned(trip.trip_id):
        return self._action_escalate(trip)
    if trip.requeue_attempts < MAX_REQUEUE_ATTEMPTS and self._requeue_enabled:
        return self._action_requeue(trip)
    return self._action_escalate(trip)
```

**Critical observations:**
- **L44-55:** Thresholds are **env-var configurable** but hardcoded defaults: intake=48h, decision=72h, review=24h, booking=336h
- **L57-58:** `_get_max_requeue_attempts()` defaults to 2
- **L173:** The recovery agent **only looks at `updated_at`** — it doesn't check if the trip is actually stuck or just idle. A trip that was updated 48h ago but is in a valid "waiting for customer" state gets flagged as stuck.
- **L245-251:** `_action_escalate()` calls `self._trip_repo.set_review_status(trip_id, "escalated")` — this is a **side effect** with no rollback path

### 1.6 The Frontier Orchestrator

**File:** `src/intake/frontier_orchestrator.py` (200 lines)

**5 subsystems, each wrapped in try/except:**
1. Emotional State Heuristic (L68-75) — keyword-based, **advisory only**
2. Ghost Concierge Trigger (L77-100) — gated by `enable_frontier_orchestration`
3. Intelligence Pool Lookup (L102-112) — federated risk query
4. Specialty Knowledge Detection (L114-135) — niche identification
5. Negotiation Engine (L137-150) — gated by `enable_auto_negotiation`

**Critical observation at L68-75:** The sentiment heuristic is a **toy implementation**:
```python
def _calculate_sentiment_heuristic(packet):
    score = 0.5
    for word in stress_keywords:
        if word in normalized:
            score -= 0.05
    for word in calm_keywords:
        if word in normalized:
            score += 0.05
    return max(0.1, min(0.9, score))
```
This is 10 words of keyword matching. The comment says "advisory only" but the `ANXIETY_ALERT_THRESHOLD = 0.3` at L15 means it **can trigger alerts** (L73-75).

### 1.7 Tool Contracts

**File:** `src/agents/tool_contracts.py` (100 lines)

```python
@dataclass(frozen=True, slots=True)
class ToolResult:
    tool_name: str
    query: dict[str, Any]      # ← unvalidated dict
    data: dict[str, Any]        # ← unvalidated dict
    evidence: ToolEvidence
    expires_at: Optional[str] = None
```

**Line 34-40:** `ToolResult` accepts **any** `dict[str, Any]` for both `query` and `data`. There is:
- No Pydantic validation on inputs
- No schema enforcement on outputs
- No type checking on nested fields
- `ToolFreshnessPolicy` (L17-19) only checks `max_age_seconds` — no semantic validation

### 1.8 Live Tools

**File:** `src/agents/live_tools.py` (500+ lines)

**4 tool types with Protocol interfaces:**
- `WeatherTool` (L21-24) — `.current_conditions(destination) -> ToolResult`
- `FlightStatusTool` (L26-29) — `.flight_status(flight) -> ToolResult`
- `PriceWatchTool` (L31-34) — `.quote_price(quote) -> ToolResult`
- `SafetyAlertTool` (L36-39) — `.destination_alerts(destination) -> ToolResult`

**Critical observation at L151-235:** `OpenMeteoWeatherTool` stores the full `provider_payload` in `ToolResult.data`:
```python
data = {
    "location": {...},
    "current": {...},
    "daily": {...},
    "mode": "live",
}
```
This is fine for weather, but `HTTPFlightStatusTool` (L236-274) does:
```python
data = {
    "status": status or "unknown",
    "delay_minutes": delay_minutes,
    "provider": self.provider_name,
    "provider_payload": payload,  # ← FULL provider response stored
    "mode": "live",
}
```
**Line 256:** `provider_payload: payload` — the **entire raw API response** is stored in the tool result, which flows into trip records. This could contain PII, API keys, or sensitive provider data.

---

## Part 2: Weakness Analysis with Line Evidence

### W1: Closed-Loop Learning Is Structurally Absent

**Evidence:**
- `src/evals/agentic_feedback.py` L467-516 builds `AgenticEvalWorkItem` with `proposed_change`, `keep_if`, `revert_if`, `owner`
- **Nothing in the codebase reads these work items to create fix candidates.** Grep for `work_items` in agent code returns zero hits outside `agentic_feedback.py` and its tests.
- `learn_from_overrides` flag exists at `src/intake/config/agency_settings.py` L70-74
- `src/decision/override_learning.py` handles severity downgrades (L185-203) but **no prompt/schema/dictionary mutation**

**The gap:** Work items are produced → returned by API → displayed nowhere → acted on by nothing. This is a **generator without a consumer**.

**Industry comparison:** Production systems (Galileo 2026, LangSmith) require: repeated failure → candidate fix → shadow test → measured comparison → promotion gate. This repo has step 1 only.

### W2: Extraction Version Tracking Is Snapshot-Based, Not Event-Sourced

**Evidence:**
- `spine_api/services/extraction_service.py` L184-201:
```python
prompt_version = os.environ.get("EXTRACTION_PROMPT_VERSION", "v1")
schema_version = os.environ.get("EXTRACTION_SCHEMA_VERSION", "v1")
```
- These are **read once at function call time** and embedded in the event metadata
- If `EXTRACTION_PROMPT_VERSION` changes between calls, historical events have the **new** version, not the one that produced them
- `CanonicalAgenticEvidenceRecord.from_event()` (L225-253) reads these from event metadata — so the version is correct **for that event**, but there's no way to know which prompt was actually used without the env var at call time

**The gap:** No immutable version snapshot per extraction attempt. Version drift is silent.

### W3: Agent Scan Is O(N×Trips) With No Prioritization

**Evidence:**
- `AgentSupervisor.run_once()` (L303-397): iterates all agents, each agent scans all trips
- `FrontDoorAgent.scan()` (L531-548): `for trip in trip_repo.list_active()` — iterates **every** active trip
- `QualityEscalationAgent.scan()` (L789-805): same pattern
- `ConstraintFeasibilityAgent.scan()` (L1464-1510): same pattern, plus `extract_context()` per trip

**With 13 agents and 100 active trips:** 13 × 100 = 1,300 trip iterations per supervisor pass (every 300s). Each `extract_context()` call does multiple `get_field()` lookups. No caching, no priority queue, no skip-if-not-changed logic beyond idempotency keys.

**The gap:** Linear scan doesn't scale. No agent knows about other agents' work. Two agents can scan the same trip simultaneously.

### W4: Frontier Orchestrator Silently Swallows All Errors

**Evidence:**
- `src/intake/frontier_orchestrator.py` L93-100:
```python
try:
    audit_result = checker_agent.audit(packet, decision)
    ...
except Exception:
    logger.exception("Checker Agent audit failed for packet %s", packet.packet_id)
    result.requires_manual_audit = True
    result.audit_reason = "Checker Agent audit failed — defaulting to manual review"
```
- **6 identical try/except blocks** (L93, L117, L134, L153, L174, L189) — every subsystem failure is caught and **silently converted to "requires manual audit"**
- The `sentiment_score` heuristic (L68-75) is marked "advisory only" but feeds into `anxiety_alert` which affects operator decisions

**The gap:** No subsystem failure is surfaced to operators. A broken Intelligence Pool looks identical to "no risks found." Silent degradation is worse than loud failure.

### W5: Requeue Port Has 4 Inconsistent Implementations

**Evidence:**
- `DisabledSpineRequeuePort` (L44-54): returns `accepted=False`
- `_RawCallableRequeuePort` (L60-75): wraps `spine_runner(trip_id)` — **no error classification**
- `InlineSpineRequeuePort` (L80-120): reconstructs pipeline context from trip record — **fragile**
- `SQLSpineJobQueueRequeuePort` (L130-176): durable queue with `enqueue()` + `trip_stats()`

**Critical at L80-120:** `InlineSpineRequeuePort.requeue_trip()` requires `raw_input` to exist in the trip record. If the trip was created via a different path (e.g., API import), `raw_input` may be absent → `accepted=False` with a cryptic reason. No fallback to SQL queue.

**The gap:** No unified fallback strategy. If inline fails, the recovery agent just escalates to human. No automatic degradation to SQL queue.

### W6: Execution Event Metadata Allowlist Is Incomplete

**Evidence:**
- `spine_api/models/tenant.py` L589-597 defines `ALLOWED_EVENT_METADATA_KEYS`
- `spine_api/services/execution_event_service.py` L100-120 validates metadata against this allowlist
- **But:** The allowlist is a static `frozenset` — adding a new metadata key requires a code change + migration
- **New keys added recently:** `review_workflow_unit_id`, `review_workflow_unit_id` (from the current git diff) — these are in the allowlist but the pattern shows every new eval field requires a code change

**The gap:** Metadata schema is not self-describing. Adding a new eval field requires: (1) add to allowlist, (2) update event emitters, (3) update consumers. No plugin/extension mechanism.

### W7: LLM Client Fallback Doesn't Track Per-Call Cost

**Evidence:**
- `src/llm/__init__.py` L138-157: `get_default_client()` falls back through providers:
```python
fallbacks = {"gemini": ["openai", "local"], "openai": ["gemini", "local"], ...}
for fallback_provider in fallbacks.get(provider, []):
    try: return create_llm_client(provider=fallback_provider)
    except LLMUnavailableError: continue
```
- `src/llm/usage_guard.py` tracks hourly/daily usage but **not per-call latency or cost per provider**
- `src/decision/telemetry.py` captures `default_fallback_rate` but not **which provider was used** or **what it cost**

**The gap:** When Gemini fails and OpenAI succeeds, we know "fallback happened" but not "OpenAI cost ₹X and took Yms." Cost attribution per provider is missing.

### W8: Agent Outputs Have No Validation Before Trip Record Write

**Evidence:**
- `FrontDoorAgent.execute()` (L550-630): writes `front_door_assessment` dict directly to trip
- `QualityEscalationAgent.execute()` (L806-850): writes `review_status=escalated` directly
- `ConstraintFeasibilityAgent.execute()` (L1510-1550): writes `constraint_feasibility_assessment` dict directly
- **No Pydantic model validates the output before `trip_repo.update_trip()`**
- **No schema check on the dict structure** — if an agent returns `{"status": "escalate"}` instead of `{"review_status": "escalated"}`, it's silently accepted

**The gap:** Agent outputs are typed as `dict[str, Any]` in `AgentExecutionResult.output` (L84-100). No contract enforcement on what the dict contains.

### W9: No Confidence Calibration Measurement

**Evidence:**
- Extraction results have `confidence_scores` and `overall_confidence` (extraction_service.py L380-390)
- `DecisionResult` has `confidence` with `data_quality`, `judgment_confidence`, `commercial_confidence`, `overall`
- Tool results have `confidence` field (tool_contracts.py L27)
- **But:** No system tracks predicted confidence vs. actual outcome
- `src/decision/telemetry.py` captures `default_fallback_rate` but not **overconfidence rate**

**The gap:** A confidence score of 0.9 that's right 60% of the time is worse than no score. Without calibration, confidence is decoration.

### W10: No Circuit Breaker for External Tools

**Evidence:**
- `DestinationIntelligenceAgent._call_weather()` (L1180-1190):
```python
def _call_weather(self, destination: str) -> ToolResult:
    try:
        return self.weather_tool.current_conditions(destination)
    except Exception as exc:
        logger.exception("DestinationIntelligenceAgent: weather tool failed for %s", destination)
        return ToolResult.from_static(..., confidence=0.1)
```
- **Same pattern** in FlightStatusAgent (L2617-2625), PriceWatchAgent (L2733-2740), SafetyAlertAgent (L2853-2860)
- **Every tool failure returns a ToolResult with low confidence** — no circuit breaker, no backoff, no "stop calling this tool for N minutes"

**The gap:** If OpenMeteo is down, every agent call to weather will timeout (10s each, per `OpenMeteoWeatherTool.__init__` L156), adding 10s × N trips to every supervisor pass. No circuit breaker to stop the bleeding.

---

## Part 3: Missing Agent Archetypes (Deep Justification)

### MA1: ClosedLoopLearningAgent (P0)

**Why:** Work items are produced but never consumed. This agent would:
1. Read `work_items` from agentic-eval summaries
2. Group by `failure_layer` and `owner`
3. For `prompt` layer: create candidate prompt variants
4. For `dictionary` layer: create dictionary patch candidates
5. For `routing` layer: create routing policy change candidates
6. Each candidate enters a `draft → shadow → measured → gating → default` pipeline

**Code path:** Would consume `aggregate_eval_records()` output → produce `ChangeCandidate` records → feed into `ShadowEvaluatorAgent`

### MA2: ShadowEvaluatorAgent (P0)

**Why:** No safe way to test changes. This agent would:
1. Accept a `ChangeCandidate` (prompt variant, routing rule, dictionary patch)
2. Run it against a sample of recent traffic in shadow mode
3. Compare quality/cost/latency delta vs. production baseline
4. Produce a `ShadowResult` with go/no-go recommendation

**Code path:** Would use `CanonicalAgenticEvidenceRecord` as baseline → run extraction/decision with candidate change → compare against production records

### MA3: ToolCallValidatorAgent (P1)

**Why:** No pre/post execution validation on tool calls. This agent would:
1. Define Pydantic input schemas for each tool type
2. Validate tool inputs before execution
3. Validate tool outputs after execution
4. Emit validation events for eval

**Code path:** Would wrap `ToolResult` creation → add `ToolCallValidation` event type → feed into eval pipeline

### MA4: CircuitBreakerAgent (P1)

**Why:** External tool failures cascade into agent latency. This agent would:
1. Track tool call success/failure rates per tool
2. When failure rate exceeds threshold → open circuit (stop calling)
3. Periodically test with probe calls → close circuit when healthy
4. Emit circuit-breaker state changes for operator visibility

**Code path:** Would wrap `live_tools.py` adapters → maintain circuit state in `ToolCircuitState` → feed into eval pipeline

### MA5: ConfidenceCalibrationAgent (P1)

**Why:** Confidence scores exist but aren't measured. This agent would:
1. Track predicted confidence vs. actual outcome for each extraction/decision
2. Compute calibration metrics (ECE, Brier score)
3. Detect overconfidence patterns by provider/model
4. Recommend confidence threshold adjustments

**Code path:** Would consume `CanonicalAgenticEvidenceRecord` with `overall_confidence` → join with review outcomes → produce calibration report

### MA6: AgentPriorityScheduler (P2)

**Why:** All agents scan all trips linearly. This agent would:
1. Maintain a priority queue of trips needing attention
2. Factor in: SLA deadlines, agent capability, current workload, dependency graph
3. Assign work to agents in priority order
4. Prevent redundant scanning

**Code path:** Would replace `for trip in trip_repo.list_active()` in each agent's `scan()` → provide `prioritized_trips()` method

### MA7: CrossAgentConsistencyChecker (P2)

**Why:** Agents write to trip records independently with no conflict detection. This agent would:
1. Detect when multiple agents write conflicting fields
2. Apply resolution rules (priority-based, latest-wins, merge)
3. Emit conflict events for audit

**Code path:** Would wrap `trip_repo.update_trip()` → detect field conflicts → apply resolution → log conflicts

### MA8: OperatorFeedbackCollector (P1)

**Why:** Operator corrections (review actions) are logged but not fed back to agents. This agent would:
1. Monitor review actions with `escalation_outcome`
2. When `false_escalation` → adjust the triggering agent's threshold
3. When `missed_escalation` → tighten the triggering agent's criteria
4. Produce adjustment candidates for human approval

**Code path:** Would consume `review_action` audit events → produce `AgentAdjustmentCandidate` → feed into ClosedLoopLearningAgent

---

## Part 4: Tool Calling Deep Analysis

### T1: No Input Schema Validation

**Current state:** `WeatherTool.current_conditions(destination: str)` accepts any string. No validation that destination is a real place, not empty, not malicious.

**Evidence:** `src/agents/live_tools.py` L151-235 — `OpenMeteoWeatherTool._geocode()` passes the destination directly to the API URL without sanitization beyond `urllib.parse.quote()`.

**Risk:** A destination like `'; DROP TABLE trips; --` would be URL-encoded and sent to OpenMeteo. Low risk for weather API, but the pattern is dangerous for any tool that constructs queries from user input.

### T2: No Output Semantic Validation

**Current state:** `ToolResult` (L34-40) accepts `data: dict[str, Any]` with no validation.

**Evidence:** If `OpenMeteoWeatherTool` returns `{"current": {"temperature_c": "hot"}}` instead of a number, the `DestinationIntelligenceAgent._assess_weather()` (L1195-1260) would:
```python
temperature = _as_float(current.get("temperature_c"))  # returns None for "hot"
if temperature is not None and (temperature >= 38 or temperature <= -10):
    ...
```
This would **silently skip** the temperature check. No error, no log, just a missing signal.

### T3: Provider Payload in Trip Records

**Current state:** `HTTPFlightStatusTool` (L236-274) stores `provider_payload: payload` in `ToolResult.data`.

**Evidence:** This flows through `DestinationIntelligenceAgent.execute()` → `trip_repo.update_trip()` → trip record. The full API response (potentially containing PII, booking references, internal IDs) is persisted.

**Fix:** Strip `provider_payload` before persistence. Add to `ToolResult` a `persisted_data` field that excludes sensitive fields.

### T4: No Tool Usage Metrics

**Current state:** Tool calls are not tracked as execution events.

**Evidence:** `DestinationIntelligenceAgent._call_weather()` (L1180-1190) catches exceptions but doesn't emit an execution event for the tool call itself. The agent emits `AGENT_ACTION` on success, but this doesn't include tool-specific metrics (latency, provider, success/failure).

**Fix:** Add `tool_call` event type to execution events. Track per-tool: call_count, success_rate, avg_latency, p95_latency, cost.

### T5: No Tool Freshness Cascading

**Current state:** `ToolResult.is_fresh()` (L42-49) checks freshness at creation time.

**Evidence:** `WeatherPivotAgent._has_fresh_evidence()` (L1400-1415) re-checks freshness of the intelligence snapshot. But `ConstraintFeasibilityAgent` (L1464-1510) reads `weather_pivot` from the trip record **without re-checking** whether the underlying weather data is still fresh.

**Fix:** Add `consumed_at` timestamp to `ToolResult`. Re-validate freshness at each consumption point.

---

## Part 5: What Exists vs. What Doesn't (Verified)

### Exists and Is Strong (12 items)

| Capability | File:Line | Evidence |
|------------|-----------|----------|
| Agent 5-contract definitions | `runtime.py:57-104` | `trigger_contract`, `input_contract`, `output_contract`, `idempotency_contract`, `failure_contract` on every agent |
| Canonical agentic evidence record | `agentic_feedback.py:192-253` | 20+ fields including version tracking, escalation outcome, latency, cost |
| Repeated failure work items | `agentic_feedback.py:467-516` | severity, proposed_change, keep_if, revert_if, owner per failure signature |
| Routing metrics | `agentic_feedback.py:370-430` | fallback_trigger_rate, review_correction_rate, false_escalation_rate, p50/p95 latency |
| Agentic eval API | `confirmations.py:303-322` | `GET /api/trips/{trip_id}/agentic-eval` with workflow filtering |
| Workflow-unit review linkage | `contract.py:282`, `review.py:42` | `review_workflow_unit_id` on ReviewActionRequest and audit events |
| Lease-based work coordination | `runtime.py:153-230`, `agent_work_coordinator.py` | SQL-based with idempotency, retry budget, poison handling |
| Recovery agent | `recovery_agent.py:91-340` | Stuck detection → requeue → escalation ladder, audit-logged |
| Tool freshness policies | `tool_contracts.py:17-19` | `ToolFreshnessPolicy(max_age_seconds=N, fail_closed=True)` |
| LLM usage guard | `usage_guard.py:74+` | Hourly/daily rate limits, budget tracking, warning thresholds |
| Privacy guard | `privacy_guard.py` | Blocks PII in agent notes |
| Execution event validation | `execution_event_service.py:80-120` | Allowlist + denylist for metadata keys |

### Exists but Is Weak/Incomplete (8 items)

| Capability | File:Line | Gap |
|------------|-----------|-----|
| `learn_from_overrides` | `agency_settings.py:70-74` | Flag exists; no pipeline to act on it |
| Override learning | `override_learning.py:185-203` | Severity downgrades only; no prompt/schema mutation |
| Shadow/golden_path constants | `constants.py:34-45` | Constants defined; no runtime implementation |
| Eval manifest with shadow/gating | `audit/manifest.py:15` | Structure exists; no runtime promotion |
| `escalation_outcome` tracking | `review.py:42,91` | New; not yet universal across review entrypoints |
| Version fields on events | `extraction_service.py:184-201` | Env-var defaults; not immutable per-attempt |
| Frontier orchestration | `frontier_orchestrator.py` | 6 try/except blocks silently swallowing errors |
| Sentiment heuristic | `frontier_orchestrator.py:68-75` | 10-word keyword matching; marked "advisory only" |

### Does Not Exist Anywhere (10 items)

| Capability | Priority | Evidence of Absence |
|------------|----------|-------------------|
| Closed-loop learning pipeline | P0 | No code reads work_items to create fix candidates |
| Shadow testing infrastructure | P0 | No shadow execution path exists |
| Tool input/output validation | P1 | No Pydantic schemas on tool boundaries |
| Agent health monitoring | P1 | No circuit breaker, no degradation detection |
| Confidence calibration | P1 | No predicted-vs-actual tracking |
| Agent priority scheduling | P2 | All agents scan all trips linearly |
| Cross-agent conflict resolution | P2 | No field-level conflict detection |
| Prompt versioning agent | P1 | No agent manages prompt lifecycle |
| Cost optimization agent | P2 | Cost tracked but not acted on |
| LLM-as-a-judge | P2 | No semantic quality evaluation |

---

## Part 6: Prioritized Roadmap (Deep)

### Phase 1: Close the Eval Loop (P0 — 2-3 weeks)

**1.1 Wire work items to fix candidates**
- File: New `src/evals/fix_candidate_builder.py`
- Reads: `aggregate_eval_records()` output
- Produces: `FixCandidate` records with layer, proposed_change, rerun_subset
- Trigger: when `work_items` has entries with `severity=high`

**1.2 Add immutable version snapshots per extraction attempt**
- File: `spine_api/services/extraction_service.py` L184-201
- Change: snapshot env vars at attempt creation time, store as `version_snapshot` field on `DocumentExtractionAttempt`
- Impact: historical attempts have correct version, not current env var

**1.3 Add rollout mode metadata**
- File: New `src/evals/rollout_modes.py`
- States: `draft → shadow → measured → gating → default`
- Wire to: extraction_service version fields, prompt registry, routing config

### Phase 2: Harden Tool Calling (P1 — 2-3 weeks)

**2.1 Add Pydantic input schemas to all tools**
- File: `src/agents/tool_contracts.py`
- Add: `ToolInputSchema` base class with per-tool subclasses
- Validate: before `tool.current_conditions()` call in each agent

**2.2 Strip provider_payload from tool results before persistence**
- File: `src/agents/live_tools.py` L256
- Change: `data.pop("provider_payload", None)` before returning `ToolResult`
- Keep: only normalized fields in persisted data

**2.3 Add tool usage metrics as execution events**
- File: New event type `tool_call` in `spine_api/models/tenant.py`
- Emit: in each agent's tool call wrapper
- Track: tool_name, latency_ms, success/failure, provider, cost

**2.4 Add circuit breaker for external tools**
- File: New `src/agents/circuit_breaker.py`
- Pattern: failure_count → threshold → open → probe_interval → half_open → close
- Wire: wrap each `Tool` adapter with circuit breaker

### Phase 3: Add Missing Agents (P1-P2 — 3-4 weeks)

**3.1 ClosedLoopLearningAgent** — consumes work items, produces fix candidates
**3.2 ShadowEvaluatorAgent** — runs candidates in shadow mode, measures delta
**3.3 ConfidenceCalibrationAgent** — tracks predicted vs. actual, detects overconfidence
**3.4 OperatorFeedbackCollector** — monitors review outcomes, feeds back to agents

### Phase 4: Advanced Capabilities (P2 — 4-6 weeks)

**4.1 AgentPriorityScheduler** — replaces linear scan with priority queue
**4.2 CrossAgentConsistencyChecker** — detects field conflicts
**4.3 LLM-as-a-judge** — semantic quality evaluation
**4.4 CostOptimizerAgent** — acts on cost metrics
**4.5 ComplianceAgent** — regulatory checking

---

## Part 7: Key Metrics to Track

### Agent Health
- `agent_success_rate` per agent per hour
- `agent_latency_p50/p95` per agent
- `agent_escalation_rate` per agent
- `agent_retry_rate` per agent

### Tool Calling
- `tool_call_success_rate` per tool
- `tool_call_latency_p50/p95` per tool
- `tool_freshness_hit_rate` per tool
- `tool_circuit_breaker_state` per tool

### Eval Loop
- `false_escalation_rate` per workflow
- `missed_escalation_rate` per workflow
- `work_item_to_fix_rate` (how many work items become fix candidates)
- `fix_to_improvement_rate` (how many fixes actually improve metrics)

### Business
- `time_to_first_response` per inquiry priority
- `cost_per_trip_processed`
- `operator_intervention_rate`

---

*This is a living document. Update as implementation progresses.*
