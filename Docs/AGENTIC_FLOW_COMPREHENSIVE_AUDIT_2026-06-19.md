# Agentic Flow Comprehensive Audit — 2026-06-19

**Date:** 2026-06-19
**Repo:** `/Users/pranay/Projects/travel_agency_agent`
**Scope:** Full agentic runtime, agent definitions, tool calling, evaluation loops, recovery, routing, and missing capabilities
**Evidence Tier:** Tier 1 (static inspection) + Tier 0 (industry research inference)
**Preceding audits:** `AGENTIC_FLOW_EVAL_AUDIT_2026-06-18.md`, `AGENTIC_EVAL_CANONICAL_ROADMAP_2026-06-19.md`, `AGENTIC_EVAL_ARTICLE_TO_ACTION_MATRIX_2026-06-19.md`

---

## Executive Summary

The Waypoint OS agentic system is **architecturally strong on contracts, runtime safety, and audit trails** but has **significant structural gaps** in closed-loop learning, agent-to-agent communication, tool calling validation, and missing specialized agents. This audit identifies **14 weakness categories**, **8 missing agent archetypes**, **6 tool calling gaps**, and **a prioritized roadmap** for hardening the system against industry failure modes (Sudjianto 2026: factual hallucination, tool misuse, policy violation, multi-hop inconsistency, confidence miscalibration, state corruption).

---

## Part 1: Current Agent Inventory

### 1.1 Product Agents (`src/agents/runtime.py`)

| Agent | Purpose | Strengths | Weaknesses |
|-------|---------|-----------|------------|
| **FrontDoorAgent** | Classifies fresh/incomplete inquiries | Explicit contracts, urgency detection | No LLM reasoning; heuristic-only |
| **SalesActivationAgent** | Schedules stage-aware follow-ups | Stage SLA awareness | No personalization; static drafts |
| **FollowUpAgent** | Marks overdue follow-ups as due | Idempotent, simple | No escalation path for chronic no-response |
| **QualityEscalationAgent** | Escalates high-risk/blocked trips | Catches suitability flags, decision_state | No confidence threshold; binary severity check |
| **DocumentReadinessAgent** | Builds passport/visa/insurance checklists | Static rules, Indian passport specialization | No live visa API; static seed data only |
| **DestinationIntelligenceAgent** | Attaches weather/risk intelligence | Live OpenMeteo integration, freshness policy | Weather-only; no cultural/event/political intelligence |
| **WeatherPivotAgent** | Converts weather intel into activity pivots | Depends on fresh intelligence snapshot | Keyword-based; no NLP on activity descriptions |
| **ConstraintFeasibilityAgent** | Detects impossible budget/date/pace combos | Comprehensive constraint checking, periodic refresh | Hardcoded thresholds; no learning from corrections |
| **FlightStatusAgent** | Monitors flight disruption risk | Protocol-based tool contracts | No proactive re-booking suggestions |
| **PriceWatchAgent** | Tracks quote price drift | Drift percentage calculation | No price prediction or trend analysis |
| **SafetyAlertAgent** | Monitors destination safety | Multiple provider adapters (State Dept, HTTP) | No real-time incident streaming |
| **PNRShadowAgent** | Compares PNR records against booking data | Name mismatch detection | No fare class or seat comparison |
| **SupplierIntelligenceAgent** | Assesses supplier reliability signals | Event-driven, idempotent | Static supplier profiles; no live feedback |

### 1.2 Recovery Agent (`src/agents/recovery_agent.py`)

- **Strengths:** Deterministic escalation ladder (requeue → escalate → alert), audit-logged, fail-closed
- **Weaknesses:** Only handles stuck trips; no proactive health monitoring, no circuit-breaker pattern

### 1.3 Frontier/Advanced Agents (`src/intake/frontier_orchestrator.py`)

- **Ghost Concierge:** Triggered on ESCALATE_RECOVERY; best-effort orchestration
- **Checker Agent:** Redundancy audit for Ghost workflows; gated by `enable_checker_agent`
- **Negotiation Engine:** Gated by `enable_auto_negotiation`; analyzes and triggers negotiation flows
- **Specialty Knowledge:** Identifies niche travel segments; urgency-based manual audit trigger
- **Intelligence Pool:** Federated risk lookup for destinations

---

## Part 2: Weakness Categories

### W1: No Closed-Loop Learning (Critical)

**What exists:**
- `learn_from_overrides` flag in `AiAgentSettings` (src/intake/config/agency_settings.py)
- `override_learning.py` handles severity downgrades and confidence hints
- Repeated failure work items with keep/revert gates (src/evals/agentic_feedback.py)

**What is missing:**
- **No system converts repeated review corrections into prompt/schema/dictionary/routing mutations.** The setting exists but the pipeline from correction → candidate fix → shadow test → promotion is entirely absent.
- **No promotion threshold.** Industry best practice: same correction repeated N times across M documents triggers a candidate fix.
- **No shadow mode for proposed changes.** Changes go from docs to production without measured comparison.
- **First-principles verdict:** This is the single highest-leverage gap. Without it, the eval system produces reports that nobody acts on systematically.

### W2: Fragmented Telemetry (High)

**What exists (5+ separate systems):**
1. `spine_api/services/execution_event_service.py` — SQL execution events (strongest)
2. `spine_api/run_events.py` — append-only JSONL per run
3. `spine_api/run_ledger.py` — checkpointed steps
4. `src/intake/telemetry.py` — JSONL quality telemetry
5. `src/decision/telemetry.py` — in-memory singleton decision metrics
6. `AuditStore` (file-based) — legacy audit trail

**What is missing:**
- **No single canonical eval join.** Computing false escalation rate requires reading SQL events + AuditStore + JSONL.
- **No consumer that merges all surfaces into one eval export.**
- **First-principles verdict:** Fragmentation is acceptable during growth, but now that canonical evidence records exist, a unified export layer should join them.

### W3: No Counterfactual Review (High)

**What exists:**
- `fallback_trigger_reason` and `fallback_result` on extraction events
- `review_trigger_reason` and `review_outcome` on review events

**What is missing:**
- **No "what would have happened without fallback" measurement.** We know fallback triggered, but not whether the primary path would have succeeded.
- **No "what would have happened without review" measurement.** We know review rejected, but not whether the AI output was actually wrong.
- **No A/B comparison framework** for routing/fallback policy changes.
- **First-principles verdict:** Without counterfactuals, we cannot distinguish useful fallback from wasteful fallback with confidence.

### W4: Agent-to-Agent Communication is Implicit (Medium)

**What exists:**
- Agents write to trip records; downstream agents read from trip records
- No explicit message passing between agents
- No shared blackboard or event bus

**What is missing:**
- **No agent can request work from another agent.** QualityEscalationAgent cannot ask DocumentReadinessAgent to re-check.
- **No priority negotiation.** All agents scan all trips independently.
- **No dependency graph.** WeatherPivotAgent depends on DestinationIntelligenceAgent output, but this is enforced by idempotency keys, not explicit dependencies.
- **Industry pattern:** Event-driven agents (Kafka/message bus) or graph-based orchestration (LangGraph) provide cleaner decoupling.
- **First-principles verdict:** The current scan-and-write pattern works at current scale but creates race conditions and redundant work as agent count grows.

### W5: Tool Calling Has No Validation Layer (High)

**What exists:**
- `ToolResult` and `ToolEvidence` contracts (src/agents/tool_contracts.py)
- `ToolFreshnessPolicy` with fail-closed semantics
- Mock and live tool adapters with Protocol-based interfaces

**What is missing:**
- **No pre-execution schema validation** on tool inputs. Agents pass dicts to tools without Pydantic validation.
- **No post-execution semantic validation.** If a tool returns malformed data, the agent silently proceeds.
- **No tool-call guardrail.** Industry practice (2025-2026): lightweight SLM classifiers sit between agent and tool to validate intended call before execution.
- **No tool usage metrics.** We track which tools are called but not tool accuracy, latency by tool, or tool failure patterns.
- **First-principles verdict:** Tool misuse is the #1 production failure mode for agentic systems (Sudjianto 2026). The current contracts are necessary but not sufficient.

### W6: Confidence Miscalibration (Medium)

**What exists:**
- Confidence scores on extraction results, tool results, and suitability flags
- `confidence` field on `DecisionResult` with `data_quality`, `judgment_confidence`, `commercial_confidence`, `overall`

**What is missing:**
- **No calibration measurement.** We don't track whether "90% confidence" predictions are correct 90% of the time.
- **No overconfidence detection.** Industry pattern: flag agents that are consistently overconfident on incorrect tasks.
- **No confidence→action mapping.** Confidence scores exist but don't deterministically trigger review, fallback, or escalation.
- **First-principles verdict:** Confidence without calibration is decoration. A 90% confidence that is right 60% of the time is worse than no confidence score.

### W7: No Agent Versioning or Rollout Modes (Medium)

**What exists:**
- `prompt_version`, `schema_version`, `routing_version`, `dictionary_version`, `normalization_version` fields on `CanonicalAgenticEvidenceRecord`
- These are mostly env-var defaults (`EXTRACTION_PROMPT_VERSION=v1`)

**What is missing:**
- **No rollout mode metadata** (`draft`, `shadow`, `measured`, `gating`, `default`) on prompt/schema/routing changes.
- **No version promotion workflow.** Changes go from env vars to production.
- **No canary or shadow deployment** for prompt/routing changes.
- **First-principles verdict:** Version fields exist as labels but don't drive behavior. The system cannot answer "which prompt version was used for this extraction" without looking at env vars.

### W8: No Proactive Health Monitoring (Medium)

**What exists:**
- `RecoveryAgent` detects stuck trips and requeues/escalates
- `AgentSupervisor.health()` returns running status and coordinator snapshot

**What is missing:**
- **No circuit-breaker pattern.** If an external tool (weather, flight status) is down, agents still call it repeatedly.
- **No agent performance degradation detection.** If an agent's success rate drops, no alert fires.
- **No cost/latency anomaly detection.** No system alerts when extraction cost spikes or latency degrades.
- **First-principles verdict:** Recovery is reactive (stuck trips). Proactive monitoring is needed before trips get stuck.

### W9: Missing Privacy/Safety Guardrails on Agent Outputs (High)

**What exists:**
- `privacy_guard.py` blocks PII in agent notes
- Extraction events forbid raw extracted fields, filenames, token payloads
- `FORBIDDEN_METADATA_PATTERNS` in execution event validation

**What is missing:**
- **No agent output sanitization before customer-facing exposure.** Agent assessments (destination intelligence, document readiness) go directly to trip records without a sanitization pass.
- **No prompt injection detection.** Raw customer input flows into extraction without adversarial testing.
- **No tool output redaction.** Live tool responses (especially provider_payload) are stored in trip records.
- **First-principles verdict:** Privacy guard catches notes-level PII but not structured data leaks in tool responses or agent assessments.

### W10: Eval Coverage is Extraction-Centric (Medium)

**What exists:**
- `agentic_feedback.py` is strongest for extraction/confirmation workflows
- Work items are generated from extraction failure signatures

**What is missing:**
- **No eval for agent decisions.** FrontDoorAgent, SalesActivationAgent, QualityEscalationAgent outputs are not evaluated.
- **No eval for constraint feasibility decisions.** The ConstraintFeasibilityAgent produces hard_blockers/soft_constraints but these are never measured for accuracy.
- **No eval for document readiness accuracy.** The static rule-based checklist is never validated against real visa/passport outcomes.
- **First-principles verdict:** The eval system covers ~30% of agent surface area. The remaining 70% operates without measurement.

### W11: No Inter-Agent Conflict Resolution (Low-Medium)

**What exists:**
- `InMemoryWorkCoordinator` provides lease-based single ownership
- `AgentWorkCoordinator` (SQL) provides durable idempotency

**What is missing:**
- **No priority arbitration.** If FrontDoorAgent and QualityEscalationAgent both want to update the same trip, priority is determined by scan order, not by urgency.
- **No conflict detection.** Two agents can write conflicting fields to the same trip record.
- **First-principles verdict:** At current agent count (~13), this is manageable. At 20+ agents, it becomes a data corruption risk.

### W12: No Agent Self-Assessment (Low)

**What exists:**
- Agent definitions include `failure_contract` strings
- Agent events emit `AGENT_FAILED`, `AGENT_ESCALATED` types

**What is missing:**
- **No agent self-evaluation.** Agents cannot assess their own confidence in their output.
- **No agent-to-supervisor feedback.** Agents cannot report "I'm not sure about this result."
- **Industry pattern:** Evaluator-Optimizer loop where a guardian agent checks outputs before they reach the user.
- **First-principles verdict:** The CheckerAgent exists for Ghost workflows only. No other agent has a self-assessment or peer-review mechanism.

### W13: No Agent Learning From Operator Actions (Medium)

**What exists:**
- `escalation_outcome` (false_escalation, missed_escalation, correct_escalation) is now tracked
- `review_workflow_unit_id` links review actions to execution events

**What is missing:**
- **No feedback loop from operator corrections to agent behavior.** When an operator corrects a QualityEscalationAgent decision, that correction is not fed back into the agent's scanning criteria.
- **No operator action pattern learning.** If operators consistently approve trips that the system flagged, no threshold adjustment occurs.
- **First-principles verdict:** The escalation_outcome tracking is new and excellent. The next step is making it drive agent behavior changes.

### W14: Missing LLM-as-a-Judge for Quality Assessment (Medium)

**What exists:**
- LLM clients (Gemini, OpenAI, Local) used by `HybridEngine` for decision-making
- `CheckerAgent` does basic audit on Ghost workflows

**What is missing:**
- **No LLM-as-a-judge for agent output quality.** Industry practice (2025-2026): use a more capable model to grade outputs of lighter models.
- **No semantic evaluation of agent assessments.** We check if fields are present but not if the assessment makes sense.
- **First-principles verdict:** Deterministic rules catch structural errors; LLM-as-a-judge catches semantic errors. Both are needed.

---

## Part 3: Missing Agent Archetypes

### MA1: PromptVersioningAgent (Specialized) — P0

**Purpose:** Manages prompt lifecycle — draft, shadow test, measure, promote, rollback.
**Why needed:** Prompt changes are the most common fix for extraction quality issues. Currently, prompt changes happen via env vars with no measurement.
**Inputs:** Repeated failure work items with `failure_layer=prompt`
**Outputs:** Prompt candidates with shadow test results, promotion recommendations
**Contract:** `trigger: work_item with prompt-layer failure; output: prompt_candidate with shadow_metrics`

### MA2: RoutingOptimizerAgent (Specialized) — P0

**Purpose:** Analyzes routing quality metrics and proposes routing policy adjustments.
**Why needed:** The `_LAYER_RECOMMENDATIONS` in agentic_feedback.py recommend "Retune routing" but no agent does this.
**Inputs:** `routing_metrics` from agentic-eval, false/missed escalation rates
**Outputs:** Routing policy change candidates with expected improvement
**Contract:** `trigger: routing_metrics show false_escalation_rate > threshold; output: routing_candidate with baseline_comparison`

### MA3: HealthMonitorAgent (Specialized) — P1

**Purpose:** Proactively monitors agent health, tool availability, cost anomalies, and performance degradation.
**Why needed:** RecoveryAgent is reactive. No system detects degradation before trips get stuck.
**Inputs:** Agent event stream, tool latency/cost metrics, extraction success rates
**Outputs:** Health alerts, degraded-agent notifications, circuit-breaker triggers
**Contract:** `trigger: periodic scan (60s); output: health_status with alerts and circuit_breaker_state`

### MA4: DataQualityAgent (Specialized) — P1

**Purpose:** Monitors extraction quality trends, dictionary accuracy, and normalization consistency.
**Why needed:** Dictionary and normalization layers have no dedicated monitoring. `failure_layer=dictionary` and `failure_layer=normalization` work items have no dedicated owner.
**Inputs:** Canonical evidence records, dictionary lookup rates, normalization conflict logs
**Outputs:** Dictionary patch candidates, normalization rule adjustments
**Contract:** `trigger: dictionary/normalization failure signatures exceed threshold; output: patch_candidate with rerun_results`

### MA5: CustomerCommunicationAgent (Generalist) — P2

**Purpose:** Drafts and reviews customer-facing messages (acknowledgments, follow-ups, status updates) with tone/accuracy checks.
**Why needed:** FrontDoorAgent drafts acknowledgments with heuristic logic. SalesActivationAgent uses static templates. No agent reviews these for tone, accuracy, or brand consistency.
**Inputs:** Trip context, agent assessment, operator preferences
**Outputs:** Customer-ready message with confidence score and compliance check
**Contract:** `trigger: trip needs customer communication; output: draft_message with tone_check and accuracy_score`

### MA6: CostOptimizerAgent (Specialized) — P2

**Purpose:** Monitors LLM/tool costs and proposes optimization strategies (model downgrade for simple tasks, prompt caching, batch processing).
**Why needed:** Cost tracking exists (`cost_usd` in canonical evidence) but no agent acts on it.
**Inputs:** Cost metrics from agentic-eval, extraction cost per document type, tool call costs
**Outputs:** Cost optimization recommendations with quality impact assessment
**Contract:** `trigger: avg_per_eval_event cost exceeds threshold; output: optimization_candidate with quality_impact`

### MA7: ComplianceAgent (Generalist) — P2

**Purpose:** Validates agent outputs against regulatory, legal, and business compliance rules before customer exposure.
**Why needed:** `privacy_guard.py` catches PII but not regulatory language, misleading claims, or unauthorized commitments.
**Inputs:** Agent assessments, customer-facing drafts, proposal content
**Outputs:** Compliance verdict with flagged items and required corrections
**Contract:** `trigger: any customer-facing output; output: compliance_verdict with flagged_items`

### MA8: ShadowEvaluatorAgent (Specialist) — P1

**Purpose:** Runs proposed changes (prompt, routing, schema) in shadow mode alongside production to measure impact.
**Why needed:** No shadow testing infrastructure exists. Changes go from idea to production without measured comparison.
**Inputs:** Proposed change candidates from other agents, production traffic sample
**Outputs:** Shadow comparison results (quality, cost, latency delta)
**Contract:** `trigger: change_candidate approved for shadow; output: shadow_result with delta_metrics`

---

## Part 4: Tool Calling Audit

### T1: No Tool Input Schema Validation

**Current state:** Agents pass `dict[str, Any]` to tool methods. Tools accept whatever they receive.
**Risk:** Tool misuse (FM-2) — malformed inputs cause silent failures or incorrect results.
**Fix:** Add Pydantic models for tool input schemas. Validate before execution.

### T2: No Tool Output Semantic Validation

**Current state:** `ToolResult.from_static()` accepts any `data: dict[str, Any]`.
**Risk:** Stale or malformed tool data propagates into agent assessments without detection.
**Fix:** Add post-execution validators per tool type (e.g., weather result must have `current.temperature_c` as numeric).

### T3: No Tool Usage Metrics

**Current state:** Tool calls are not tracked as execution events. No latency/cost/success metrics per tool.
**Risk:** Cannot answer "which tool is most unreliable" or "which tool adds the most latency."
**Fix:** Emit execution events for tool calls with tool_name, latency_ms, success/failure, and confidence.

### T4: No Tool Call Guardrails

**Current state:** No pre-execution check on whether a tool call is appropriate for the current context.
**Risk:** Agents call tools unnecessarily (wasted cost) or at inappropriate times (e.g., calling weather for a domestic trip).
**Fix:** Add tool appropriateness checks to agent scan logic (e.g., skip weather tool for domestic-only trips).

### T5: Provider Payload Leaking into Trip Records

**Current state:** `HTTPFlightStatusTool`, `HTTPPriceWatchTool`, `HTTPSafetyAlertTool` store `provider_payload` in `ToolResult.data`. This flows into trip records.
**Risk:** PII, API keys, or sensitive provider data in trip records accessible to operators.
**Fix:** Strip `provider_payload` before persisting. Keep only normalized fields.

### T6: No Tool Freshness Cascading

**Current state:** `ToolResult.is_fresh()` checks individual tool freshness. But downstream agents don't re-check freshness before using cached results.
**Risk:** WeatherPivotAgent uses a DestinationIntelligenceAgent snapshot that was fresh when created but stale when consumed.
**Fix:** Add freshness re-validation at each agent consumption point, not just at creation.

---

## Part 5: What Exists vs. What Doesn't

### Exists in Code (Verified)

| Capability | Location | Status |
|------------|----------|--------|
| Agent contract definitions (5 contracts per agent) | `src/agents/runtime.py` | ✅ Strong |
| Canonical agentic evidence record | `src/evals/agentic_feedback.py` | ✅ Strong |
| Repeated failure work items with keep/revert gates | `src/evals/agentic_feedback.py` | ✅ Strong |
| Routing metrics (fallback/review rates, latency, cost) | `src/evals/agentic_feedback.py` | ✅ Strong |
| Agentic eval API endpoint | `spine_api/routers/confirmations.py` | ✅ Strong |
| Workflow-unit review linkage | `spine_api/contract.py`, `src/analytics/review.py` | ✅ Strong |
| Lease-based work coordination | `src/agents/runtime.py`, `spine_api/services/agent_work_coordinator.py` | ✅ Strong |
| Recovery agent with escalation ladder | `src/agents/recovery_agent.py` | ✅ Strong |
| Tool freshness policies | `src/agents/tool_contracts.py` | ✅ Good |
| LLM usage guard | `src/llm/usage_guard.py` | ✅ Good |
| Privacy guard on agent notes | `src/security/privacy_guard.py` | ✅ Good |
| Execution event validation (allowlist + denylist) | `spine_api/services/execution_event_service.py` | ✅ Strong |

### Exists in Code (Weak/Incomplete)

| Capability | Location | Status |
|------------|----------|--------|
| `learn_from_overrides` flag | `src/intake/config/agency_settings.py` | 🟡 Flag exists, pipeline absent |
| Override learning logic | `src/decision/override_learning.py` | 🟡 Severity downgrades only |
| Shadow/golden_path constants | `src/intake/constants.py` | 🟡 Constants defined, not wired |
| Eval manifest with status=shadow/gating | `src/evals/audit/manifest.py` | 🟡 Structure exists, no runtime |
| `escalation_outcome` tracking | `src/analytics/review.py` | 🟡 New, not yet universal |
| Prompt/schema/routing version fields | `spine_api/services/extraction_service.py` | 🟡 Env-var defaults only |

### Exists in Docs Only (Not in Code)

| Capability | Doc Location | Status |
|------------|-------------|--------|
| Agentic eval rules | `/Users/pranay/Projects/AGENTIC_EVAL_RULES.md` | ❌ Referenced but no runtime |
| Agentic eval loop skill | `~/Projects/skills/agentic-eval-loop/SKILL.md` | ❌ Skill exists, not wired to pipeline |
| Shadow replay framework | `src/intake/constants.py` | ❌ Constant only |
| Counterfactual review | Docs/research/ | ❌ Concept only |
| Rollout mode metadata | Docs/research/ | ❌ Concept only |
| Agent self-assessment | Not found | ❌ Not implemented |
| Tool call validation layer | Not found | ❌ Not implemented |
| LLM-as-a-judge | Not found | ❌ Not implemented |
| Circuit-breaker pattern | Not found | ❌ Not implemented |
| Agent priority arbitration | Not found | ❌ Not implemented |

### Does Not Exist Anywhere

| Capability | Priority | Impact |
|------------|----------|--------|
| Closed-loop learning pipeline | P0 | Eval reports pile up without action |
| Shadow testing infrastructure | P0 | No safe way to test changes |
| Tool input/output validation | P1 | Tool misuse goes undetected |
| Agent health monitoring | P1 | Degradation detected only after failures |
| Prompt versioning agent | P1 | Prompt changes untracked |
| Cost optimization agent | P2 | Costs unmanaged |
| Customer communication agent | P2 | Draft quality unreviewed |
| Compliance agent | P2 | Regulatory risk unmonitored |
| Agent conflict resolution | P2 | Race conditions at scale |
| Confidence calibration | P2 | Confidence scores unreliable |

---

## Part 6: Industry Failure Mode Mapping

Based on Sudjianto (2026) "Six Ways Agentic AI Fails" and industry research:

| Failure Mode | Category | Current Coverage | Gap |
|-------------|----------|-----------------|-----|
| **Factual Hallucination** | Reasoning | Extraction validation, suitability scoring | No LLM-as-a-judge for semantic correctness |
| **Tool Misuse** | Execution | ToolResult contracts, freshness policy | No pre-execution validation, no guardrails |
| **Policy Violation** | Execution | Privacy guard, compliance rules | No agent output sanitization, no prompt injection detection |
| **Multi-Hop Inconsistency** | Reasoning | Constraint feasibility checks | No cross-agent consistency validation |
| **Confidence Miscalibration** | Reasoning | Confidence scores on extractions | No calibration measurement, no overconfidence detection |
| **State Corruption** | Execution | Idempotency keys, lease coordination | No conflict resolution, no version control on trip state |

---

## Part 7: Prioritized Roadmap

### Phase 1: Close the Eval Loop (P0 — 2-3 weeks)

1. **Wire `learn_from_overrides` to concrete mutation classes**
   - Repeated review correction → candidate prompt change
   - Repeated raw-value loss → schema split or parser/dictionary fix
   - Repeated hallucinated field → tighter routing/review rule
   - Repeated low-value fallback → fallback trigger change

2. **Add rollout mode metadata** on prompt/schema/routing changes
   - States: `draft → shadow → measured → gating → default`
   - Wire to extraction_service version fields

3. **Build ShadowEvaluatorAgent**
   - Run proposed changes alongside production
   - Measure quality/cost/latency delta
   - Gate promotion on positive delta

### Phase 2: Harden Tool Calling (P1 — 2-3 weeks)

4. **Add Pydantic input schemas to all tools**
   - Validate before execution
   - Reject malformed inputs with structured errors

5. **Add post-execution semantic validation per tool type**
   - Weather: temperature_c must be numeric
   - Flight: status must be in allowed set
   - Price: drift_percent must be finite

6. **Strip provider_payload from tool results before persistence**
   - Keep only normalized fields
   - Audit what data flows into trip records

7. **Add tool usage metrics as execution events**
   - tool_name, latency_ms, success/failure, confidence

### Phase 3: Add Missing Agents (P1-P2 — 3-4 weeks)

8. **HealthMonitorAgent** — proactive degradation detection
9. **PromptVersioningAgent** — prompt lifecycle management
10. **RoutingOptimizerAgent** — routing quality analysis
11. **DataQualityAgent** — dictionary/normalization monitoring
12. **ShadowEvaluatorAgent** — change impact measurement

### Phase 4: Advanced Capabilities (P2 — 4-6 weeks)

13. **Confidence calibration measurement** — track predicted vs. actual accuracy
14. **LLM-as-a-judge** for agent output quality
15. **Agent conflict resolution** with priority arbitration
16. **CustomerCommunicationAgent** for message quality
17. **ComplianceAgent** for regulatory checking
18. **CostOptimizerAgent** for cost management

---

## Part 8: Key Metrics to Track

### Agent Health Metrics
- Agent success rate (per agent, per time window)
- Agent latency (p50, p95, p99)
- Agent cost per execution
- Agent escalation rate
- Agent retry rate

### Tool Calling Metrics
- Tool call success rate (per tool)
- Tool call latency (per tool)
- Tool freshness hit rate
- Tool misuse rate (invalid inputs rejected)
- Tool cost per call

### Eval Loop Metrics
- False escalation rate
- Missed escalation rate
- Review correction rate
- Work item → fix promotion rate
- Fix → verified improvement rate

### Business Metrics
- Time to first response (per inquiry priority)
- Lead conversion rate (per agent classification)
- Customer satisfaction (per communication quality)
- Cost per trip processed
- Operator intervention rate

---

## Part 9: Decision Record

**Decision:** Document this audit as a durable reference for agentic system hardening.
**Date:** 2026-06-19
**Context:** The agentic system has grown to 13+ agents with fragmented eval coverage and no closed-loop learning.
**Options considered:**
1. Incremental fixes to existing agents (low risk, low impact)
2. Comprehensive audit + phased roadmap (medium risk, high impact)
3. Full rewrite of agent runtime (high risk, highest impact)
**Chosen path:** Option 2 — comprehensive audit with phased implementation.
**Tradeoffs:** Option 2 requires ~8-12 weeks of focused work but preserves existing strong contracts.
**Assumptions:** Agent count will grow to 20+ within 6 months. Current architecture scales to ~15 agents before conflict resolution becomes critical.
**Risks:** Phased approach may lose momentum if not scheduled into sprint cycles.
**Validation plan:** Each phase should produce measurable improvement in the corresponding metrics.
**Rollback:** Each phase is additive; no existing capability is removed.
**Owner:** Project owner
**What would cause revisiting:** Agent count exceeds 15, or a production incident traced to a gap identified here.

---

*This audit is a living document. Update as implementation progresses.*
*Checklist applied: IMPLEMENTATION_AGENT_REVIEW_HANDOFF_CHECKLIST.md*
