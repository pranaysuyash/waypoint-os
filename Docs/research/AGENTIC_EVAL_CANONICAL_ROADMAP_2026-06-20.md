# Agentic System Eval Canonical Roadmap

**Date:** 2026-06-20  
**Scope:** Full evaluation landscape for the travel agency agent system  
**Goal:** Comprehensive eval plan covering prompts, inputs, outputs, agents, extraction, routing, and orchestr

---

## 1. Existing Eval Infrastructure (What Exists)

### 1.1 D6 Audit Scaffold (`src/evals/audit/`)

A mature fixture-based eval framework for deterministic rule evaluation.

| Component | File | Purpose |
|-----------|------|---------|
| **Fixtures** | `fixtures.py` | `AuditFixture` with `ExpectedFinding` / `ExpectedAbsentFinding` — JSON test cases with expected flags and severities |
| **Metrics** | `metrics.py` | `compute_category_metrics()` → precision, recall, severity accuracy per category |
| **Runner** | `runner.py` | `run_eval_suite()` — runs fixtures against rule runners, produces `EvalReport` |
| **Gates** | `gates.py` | `evaluate_report_against_manifest()` — compares metrics against manifest thresholds (min_precision, min_recall, min_severity_accuracy) |
| **Manifest** | `manifest.py` + `manifest.yaml` | Category config with `planned/shadow/gating` status and thresholds |
| **Rules** | `rules/activity.py` | `run_activity_fixture()` — evaluates itinerary activity utility and wasted spend |
| **Snapshot** | `snapshot.py` | `build_gate_snapshot()` — produces deterministic gate snapshot for public-surface authority |
| **Authority** | `public_authority.py` | `resolve_public_authority()` — runtime authority resolution from snapshot or manifest fallback |

**Current coverage:** Only `activity` category has a rule runner. Categories `routing`, `feasibility`, `document_readiness`, `destination_intelligence` are defined in manifest but have no rule runners.

**Tests:** `tests/evals/test_d6_audit_scaffold.py`, `tests/evals/test_d6_gate_snapshot.py`, `tests/evals/test_public_authority.py`

### 1.2 Agentic Feedback Loop (`src/evals/agentic_feedback.py`)

The core runtime eval signal pipeline — production-grade and well-tested.

| Component | Purpose |
|-----------|---------|
| `AgenticEvalRecord` | Normalized eval signal from `ExecutionEvent` — captures workflow, failure_signature, failure_layer, provider, model |
| `AgenticEvalWorkItem` | Actionable work item from repeated failures — severity, proposed_change, regression_risk, owner |
| `CanonicalAgenticEvidenceRecord` | Cross-system eval record — prompt_version, schema_version, routing_version, latency, cost |
| `filter_eval_candidates()` | Selects events with eval-relevant metadata keys |
| `build_routing_metrics()` | Computes fallback_trigger_rate, review_trigger_rate, false_escalation_rate, latency percentiles, cost |
| `build_repeated_failure_signal()` | Groups by failure_signature, emits work items when occurrences ≥ min_occurrences |
| `aggregate_eval_records()` | Full summary: routing_metrics + canonical_evidence_records + work_items |
| `_LAYER_RECOMMENDATIONS` | 10 failure-layer routing profiles (model, prompt, parser, schema, routing, fallback, review, dictionary, normalization, unknown) |

**Tests:** `tests/evals/test_agentic_feedback.py` (comprehensive: 15+ tests covering records, filtering, aggregation, routing metrics, work items)

### 1.3 Closed-Loop Learning Agent (`src/agents/closed_loop_learning.py`)

Consumes `AgenticEvalWorkItem` instances and produces fix candidates with shadow testing.

| Component | Purpose |
|-----------|---------|
| `FixCandidate` | Proposed fix with candidate_id, layer recommendations, owner |
| `ShadowTestResult` | Deterministic simulation: simulated_fixes, regressions, verdict (proceed/defer/reject) |
| `build_fix_candidate()` | Converts work item → fix candidate with layer-specific recommendations |
| `run_shadow_test()` | Simulates fix against sample events, counts fixes/regressions/unchanged |
| `ClosedLoopLearningAgent` | scan() discovers repeated failures, execute() builds candidate + runs shadow test |

**Tests:** `tests/test_closed_loop_learning_agent.py` (32 tests: unit, integration, supervisor-level)

### 1.4 Version Snapshot System (`src/intake/version_snapshot.py`)

Immutable version tracking for all mutable extraction dimensions.

| Dimension | Env Var | Purpose |
|-----------|---------|---------|
| Prompt | `EXTRACTION_PROMPT_VERSION` + `EXTRACTION_PROMPT_TEXT` | Which prompt template was active |
| Schema | `EXTRACTION_SCHEMA_VERSION` | Which output schema was enforced |
| Routing | `EXTRACTION_ROUTING_VERSION` | Which model routing policy was active |
| Dictionary | `EXTRACTION_DICTIONARY_VERSION` | Which normalization dictionary was used |
| Normalization | `EXTRACTION_NORMALIZATION_VERSION` | Which normalization rules were active |

Supports `diff()`, `changed_dimensions()`, `detect_rollout_change()`, and rollout mode tracking (shadow/canary/full/rolled_back/pending).

### 1.5 Extraction Smoke Tests (`src/extraction/smoke_test.py`)

Provider connectivity validation — verifies each configured extraction provider can process a trivial document.

- Tests OpenAI and Gemini providers with synthetic JPEG/PDF
- Measures latency and field extraction count
- Gated by `EXTRACTION_SMOKE_TEST=1` and blocked in production
- **No accuracy measurement** — only connectivity proof

### 1.6 API Endpoint Tests (`tests/evals/test_agentic_eval_endpoint.py`)

Tests the `/api/trips/{trip_id}/agentic-eval` endpoint:
- Returns summary from mocked service
- Rejects unknown workflows
- Merges execution and review events
- Accepts workflow_unit_id filter

### 1.7 Notebook Eval Runner (`notebooks/04_eval_runner.ipynb`)

Decision-making model evaluation — simulates intake → extraction → decision pipeline and analyzes results.

---

## 2. Complete Agentic System Component Map (What Exists)

### 2.1 Registered Agents (17 total)

| Agent | Category | Evaluable Aspects |
|-------|----------|-------------------|
| `front_door_agent` | Intake | Classification accuracy, acknowledgment draft quality, priority assignment |
| `sales_activation_agent` | Sales | Follow-up scheduling timing, draft quality, SLA adherence |
| `follow_up_agent` | Sales | Overdue detection accuracy, status transitions |
| `quality_escalation_agent` | Quality | Escalation precision (false positive rate), reason accuracy |
| `document_readiness_agent` | Compliance | Checklist completeness, visa/passport risk detection, disclaimer accuracy |
| `destination_intelligence_agent` | Intelligence | Weather assessment accuracy, risk level calibration, recommendation relevance |
| `weather_pivot_agent` | Intelligence | Activity/transfer pivot detection, packet completeness |
| `constraint_feasibility_agent` | Feasibility | Hard/soft blocker detection, missing fact identification, route fatigue analysis |
| `proposal_readiness_agent` | Quality | Readiness status accuracy, missing element detection |
| `booking_readiness_agent` | Quality | Data completeness assessment, blocking risk detection |
| `flight_status_agent` | Intelligence | Delay detection accuracy, risk level assessment |
| `ticket_price_watch_agent` | Intelligence | Quote drift detection, price alert accuracy |
| `safety_alert_agent` | Intelligence | Alert packet accuracy, traveler impact assessment |
| `gds_schema_bridge_agent` | Data | Canonical object normalization accuracy |
| `pnr_shadow_agent` | Quality | Name/segment mismatch detection, risk classification |
| `supplier_intelligence_agent` | Intelligence | Supplier reliability assessment, risk flagging |
| `closed_loop_learning_agent` | Eval Loop | Fix candidate generation, shadow test accuracy, verdict correctness |

### 2.2 Extraction Pipeline

| Component | Files | Evaluable Aspects |
|-----------|-------|-------------------|
| OpenAI Vision Extractor | `src/extraction/openai_vision_extractor.py` | Extraction accuracy, field completeness, latency |
| Gemini Vision Extractor | `src/extraction/gemini_vision_extractor.py` | Extraction accuracy, field completeness, latency |
| Model Chain | `src/extraction/model_chain.py` | Fallback ordering, retry behavior |
| Vision Clients | `src/extraction/vision_client.py`, `gemini_vision_client.py` | Error classification, timeout handling |
| Extraction Service | `spine_api/services/extraction_service.py` | End-to-end extraction quality, version snapshot attachment, event emission |
| Version Snapshots | `src/intake/version_snapshot.py` | Snapshot capture accuracy, diff detection |

### 2.3 LLM Clients

| Client | File | Evaluable Aspects |
|--------|------|-------------------|
| OpenAI Client | `src/llm/openai_client.py` | Response quality, latency, cost, error handling |
| Gemini Client | `src/llm/gemini_client.py` | Response quality, latency, cost, error handling |

### 2.4 Supervisor Infrastructure

| Component | File | Evaluable Aspects |
|-----------|------|-------------------|
| AgentSupervisor | `src/agents/runtime.py` | run_once() coordination, lease management, audit emission, retry/poison behavior |
| InMemoryWorkCoordinator | `src/agents/runtime.py` | Idempotency, single-owner lease, retry policy |
| AgentRegistry | `src/agents/runtime.py` | Registration completeness, definition contracts |

---

## 3. Existing Eval Coverage Matrix

| Dimension | What Exists | Coverage | Gap |
|-----------|-------------|----------|-----|
| **D6 Audit Rules** | Activity rule runner | 1/7+ categories | routing, feasibility, document_readiness, destination_intelligence rules missing |
| **Extraction Accuracy** | Smoke tests (connectivity only) | 0% accuracy | No precision/recall/f1 for extracted fields |
| **Prompt Quality** | Version snapshots, hash tracking | Tracking only | No prompt A/B testing, no quality scoring |
| **Agent Scan Precision** | Unit tests per agent | High (per agent) | No cross-agent scan overlap detection |
| **Agent Execute Quality** | Unit tests per agent | High (per agent) | No output quality scoring beyond pass/fail |
| **Routing Metrics** | `build_routing_metrics()` | Good | No threshold alerting, no trend tracking |
| **Failure Signal Aggregation** | `build_repeated_failure_signal()` | Good | No automated re-run scheduling |
| **Shadow Testing** | `run_shadow_test()` (deterministic) | Good | No real LLM reprocessing, simulation only |
| **Cost Tracking** | `cost_usd` in routing metrics | Partial | No per-agent cost attribution, no budget alerts |
| **Latency Tracking** | `latency_ms` in routing metrics | Partial | No per-step latency breakdown |
| **End-to-End Pipeline Eval** | None | 0% | No golden dataset eval of full intake→extraction→decision |
| **Cross-Agent Orchestration** | None | 0% | No eval of agent delegation accuracy |
| **Output Quality Scoring** | None | 0% | No LLM-as-judge, no human annotation loop |
| **Regression Detection** | Closed-loop learning (reactive) | Partial | No proactive regression alerting on metric changes |

---

## 4. Evaluable Dimensions — Full Taxonomy

### 4.1 Extraction Pipeline Eval

| Sub-dimension | Metric | Implementation |
|---------------|--------|----------------|
| **Field Extraction Accuracy** | Per-field precision/recall/F1 | Golden dataset: 50+ labeled documents with expected fields |
| **Schema Compliance** | % valid JSON matching expected schema | Deterministic validator against extraction output schema |
| **Hallucination Rate** | % of extracted fields not present in source | Ground-truth comparison on labeled documents |
| **Multi-Model Agreement** | % agreement between OpenAI and Gemini | Run both providers on same documents, compare outputs |
| **Fallback Effectiveness** | Success rate after fallback trigger | Routing metrics: useful_fallback_rate vs wasteful_fallback_count |
| **Prompt Version Impact** | Accuracy delta between prompt versions | A/B comparison using version snapshots as grouping key |
| **Document Type Coverage** | Accuracy per document type (passport/visa/insurance) | Stratified golden dataset by document type |

### 4.2 Agent Eval

| Sub-dimension | Metric | Implementation |
|---------------|--------|----------------|
| **Scan Precision** | % of yielded work items that lead to meaningful actions | Track work_item → execution_result → trip_update chain |
| **Scan Recall** | % of actionable trips that were detected | Inject trips with known issues, verify detection |
| **Execute Success Rate** | % of execute() calls returning success=True | Already tracked in routing metrics |
| **Output Completeness** | Required fields present in agent output | Schema validator per agent output contract |
| **Trip State Correctness** | State transitions match expected business rules | State machine validator for trip.status/stage transitions |
| **Idempotency** | Same work_item produces same result | Replay test with same idempotency_key |
| **Cross-Agent Dedup** | No two agents modify same field simultaneously | Coordinator lease + field-level conflict detection |

### 4.3 Prompt Eval

| Sub-dimension | Metric | Implementation |
|---------------|--------|----------------|
| **Extraction Prompt Quality** | Field completeness rate per prompt version | Group by prompt_hash, compare field extraction rates |
| **System Prompt Adherence** | Agent output follows instruction contract | LLM-as-judge scoring against agent definition |
| **Prompt Regression Detection** | Accuracy drop after prompt change | Version snapshot diff → accuracy comparison |
| **Prompt Robustness** | Consistency across varied input formats | Test same intent expressed in different phrasings |

### 4.4 LLM Output Quality Eval

| Sub-dimension | Metric | Implementation |
|---------------|--------|----------------|
| **Factuality** | Extracted facts match source document | Golden dataset with labeled ground truth |
| **Completeness** | All required fields extracted | Per-field recall on golden dataset |
| **Format Compliance** | Output matches expected JSON schema | Deterministic schema validation |
| **Tone/Persona** | Agent drafts match intended tone | LLM-as-judge with rubric per agent type |
| **Grounding** | Output references source data, not hallucinated | Citation tracking in extraction output |

### 4.5 Orchestration Eval

| Sub-dimension | Metric | Implementation |
|---------------|--------|----------------|
| **Agent Selection Accuracy** | Right agent handles right trip type | Simulated trips with known optimal agent sequence |
| **Delegation Efficiency** | Minimal redundant agent runs | Track agent overlap per trip lifecycle |
| **Pipeline Latency** | End-to-end time from intake to decision | Per-trip timing instrumentation |
| **Recovery Effectiveness** | Stuck trips resolved by recovery agent | Track recovery_agent intervention success rate |

### 4.6 Operational Eval

| Sub-dimension | Metric | Implementation |
|---------------|--------|----------------|
| **Cost Per Trip** | Total LLM cost attributed to trip | Aggregate cost_usd from routing metrics per trip |
| **Latency Distribution** | p50/p95/p99 latency per workflow | Already in routing_metrics, need alerting |
| **Error Rate** | % of extraction attempts failing | Already tracked as event_type=extraction_attempt_failed |
| **Review Load** | % of extractions requiring human review | review_trigger_rate from routing metrics |
| **Escalation Accuracy** | false_escalation_rate, missed_escalation_rate | Already tracked in routing_metrics |

---

## 5. Recommended Eval Framework Stack

Based on research and codebase compatibility:

| Need | Recommendation | Rationale |
|------|----------------|-----------|
| **Golden Dataset Management** | JSON fixtures in `data/fixtures/` (extend existing D6 pattern) | Already proven, version-controllable, no external deps |
| **LLM-as-Judge** | Custom evaluator using OpenAI/Gemini clients already in codebase | No new dependency, uses existing API keys |
| **A/B Prompt Testing** | Version snapshot diffing + routing metrics comparison | Already have version_snapshot infrastructure |
| **Shadow Testing** | Extend `run_shadow_test()` with real LLM reprocessing | Already have deterministic simulation, add live mode |
| **Dashboard/Alerting** | Extend `build_routing_metrics()` with threshold checks | Already compute metrics, add alerting layer |
| **CI Integration** | Gate snapshots in CI (already exists) + add extraction accuracy gate | Extend D6 manifest to include extraction categories |

---

## 6. Implementation Roadmap

### Phase 1: Foundation (Week 1-2) — Immediate Value

**Priority: HIGH — Quick wins with existing infrastructure**

1. **Build Golden Extraction Dataset** (50+ labeled documents)
   - Create `data/fixtures/extraction/` with passport, visa, insurance documents
   - Each fixture: input document + expected extracted fields + expected values
   - Extend D6 manifest to include `extraction` category

2. **Add Extraction Accuracy Metrics**
   - New rule runner: `src/evals/audit/rules/extraction.py`
   - Per-field precision/recall/F1 computation
   - Schema compliance check (deterministic)
   - Integrate into existing `run_eval_suite()` framework

3. **Extend D6 Audit Rule Runners**
   - Add `routing.py` rule runner for constraint feasibility
   - Add `document_readiness.py` rule runner for visa/passport checks
   - Add `destination_intelligence.py` rule runner for weather assessment
   - Add `feasibility.py` rule runner for budget/date/route feasibility

4. **Add Threshold Alerting to Routing Metrics**
   - Define alert thresholds: fallback_trigger_rate > 0.3, false_escalation_rate > 0.1
   - Add `check_routing_health()` function to `agentic_feedback.py`
   - Integrate with notification system

### Phase 2: Quality Scoring (Week 3-4) — Agent Output Quality

**Priority: HIGH — Measures what matters**

5. **LLM-as-Judge for Agent Outputs**
   - Create `src/evals/judge/` module
   - Rubric per agent type (e.g., front_door: classification accuracy, priority correctness)
   - Score agent execution results against expected outcomes
   - Add to `run_once()` pipeline as optional quality gate

6. **Prompt Version A/B Testing**
   - Extend `VersionSnapshot` to track accuracy per snapshot
   - Create `src/evals/prompt_comparison.py`
   - Compare extraction accuracy across prompt versions using canonical evidence records
   - Surface results via agentic-eval endpoint

7. **Agent Scan Precision/Recall**
   - Create `data/fixtures/agent_scan/` with trips that should/shouldn't trigger each agent
   - Track work_item → execution → outcome chain
   - Compute scan precision (meaningful actions / total work items)

### Phase 3: Shadow Testing (Week 5-6) — Live Validation

**Priority: MEDIUM — Requires production traffic**

8. **Live Shadow Testing for Extraction**
   - Extend `run_shadow_test()` to accept optional LLM client
   - When available, reprocess sample_events through current prompt/provider
   - Compare shadow output against original extraction output
   - Track shadow verdict accuracy over time

9. **Cross-Provider Agreement Testing**
   - Run same documents through OpenAI and Gemini in shadow mode
   - Compute inter-rater agreement (Cohen's kappa or simple %)
   - Surface disagreement patterns for prompt improvement

10. **End-to-End Pipeline Eval**
    - Create golden trips: raw input → expected extraction → expected decision
    - Run through full pipeline (intake → extraction → agents → decision)
    - Compare actual vs expected at each stage
    - Add to D6 gate snapshot as `pipeline` category

### Phase 4: Operational Intelligence (Week 7-8) — Production Monitoring

**Priority: MEDIUM — Production maturity**

11. **Cost Attribution Per Trip**
    - Extend `CanonicalAgenticEvidenceRecord` to include agent-level cost breakdown
    - Create cost-per-trip dashboard data
    - Alert on cost anomalies (sudden increase per extraction)

12. **Latency Regression Detection**
    - Track p50/p95 latency per prompt_version/provider combination
    - Alert on latency regression (>20% increase from baseline)
    - Correlate with version changes via snapshot diffing

13. **Recovery Agent Effectiveness**
    - Track recovery_agent interventions: what triggered, what resolved
    - Compute recovery success rate by failure type
    - Feed back into agent tuning

### Phase 5: Advanced Eval (Week 9+) — Continuous Improvement

**Priority: LOW — Long-term investment**

14. **Human Annotation Loop**
    - Route random sample of extraction results to owner review
    - Capture review_outcome and escalation_outcome as labeled data
    - Use labeled data to calibrate LLM-as-judge scorers
    - Feed into golden dataset expansion

15. **Automated Regression Test Generation**
    - Use failure_signature patterns from `build_repeated_failure_signal()`
    - Auto-generate test fixtures from real production failures
    - Add to golden dataset with owner review

16. **Cross-Agent Orchestration Eval**
    - Simulate complex multi-agent scenarios
    - Verify agent sequencing (front_door → document_readiness → constraint_feasibility)
    - Detect redundant or conflicting agent actions

---

## 7. Key Metrics Dashboard (Proposed)

### Extraction Health
| Metric | Current | Target | Alert Threshold |
|--------|---------|--------|-----------------|
| Field extraction accuracy (F1) | Unknown | ≥ 0.90 | < 0.80 |
| Schema compliance rate | Unknown | ≥ 0.95 | < 0.90 |
| Hallucination rate | Unknown | ≤ 0.05 | > 0.10 |
| Fallback trigger rate | Tracked | ≤ 0.25 | > 0.35 |
| Useful fallback rate | Tracked | ≥ 0.60 | < 0.40 |

### Agent Health
| Metric | Current | Target | Alert Threshold |
|--------|---------|--------|-----------------|
| Execute success rate | Tracked | ≥ 0.95 | < 0.85 |
| Scan precision | Unknown | ≥ 0.80 | < 0.60 |
| Review correction rate | Tracked | ≤ 0.15 | > 0.25 |
| False escalation rate | Tracked | ≤ 0.10 | > 0.20 |

### Operational Health
| Metric | Current | Target | Alert Threshold |
|--------|---------|--------|-----------------|
| p50 latency (extraction) | Tracked | ≤ 5000ms | > 8000ms |
| p95 latency (extraction) | Tracked | ≤ 15000ms | > 20000ms |
| Cost per extraction | Tracked | ≤ $0.05 | > $0.10 |
| Error rate (extraction) | Tracked | ≤ 0.10 | > 0.20 |

---

## 8. Immediate Next Steps

1. **Create `data/fixtures/extraction/golden_dataset.json`** — 50 labeled extraction test cases
2. **Add `src/evals/audit/rules/extraction.py`** — extraction accuracy rule runner
3. **Extend `manifest.yaml`** — add extraction category with thresholds
4. **Add `check_routing_health()`** — threshold alerting for routing metrics
5. **Create `src/evals/judge/`** — LLM-as-judge module with per-agent rubrics

---

## 9. File Index

### Existing Eval Files
```
src/evals/
  __init__.py                    # "Offline evaluation scaffolds for trust gates."
  agentic_feedback.py            # Agentic eval records, work items, routing metrics, failure signals
  audit/
    __init__.py                  # D6 audit scaffold exports
    fixtures.py                  # AuditFixture, ExpectedFinding, load_fixtures
    gates.py                     # CategoryGateDecision, EvalGateReport, evaluate_report_against_manifest
    manifest.py                  # EvalManifest, EvalCategoryConfig, load_manifest
    manifest.yaml                # Category thresholds (planned/shadow/gating)
    metrics.py                   # CategoryMetrics, compute_category_metrics
    public_authority.py          # CategoryPublicAuthority, resolve_public_authority
    runner.py                    # EvalReport, run_eval_suite
    snapshot.py                  # build_gate_snapshot, write_gate_snapshot
    rules/
      __init__.py
      activity.py                # run_activity_fixture

src/agents/closed_loop_learning.py  # FixCandidate, ShadowTestResult, ClosedLoopLearningAgent
src/intake/version_snapshot.py       # VersionSnapshot, capture_version_snapshot
src/extraction/smoke_test.py         # Provider smoke tests (connectivity only)

tests/evals/
  test_agentic_feedback.py
  test_agentic_eval_endpoint.py
  test_d6_audit_scaffold.py
  test_d6_gate_snapshot.py
  test_public_authority.py

tests/test_closed_loop_learning_agent.py  # 32 tests including supervisor integration

notebooks/
  04_eval_runner.ipynb           # Decision-making model evaluation
```

### Key Agentic System Files
```
src/agents/runtime.py            # 17 agent classes, AgentSupervisor, AgentRegistry
src/agents/recovery_agent.py     # Self-healing agent
src/agents/risk_contracts.py     # Structured risk payloads
src/agents/tool_contracts.py     # Tool evidence contracts
src/extraction/                  # OpenAI/Gemini extractors, ModelChain
src/llm/                         # OpenAI/Gemini clients
src/intake/                      # Version snapshots, extraction pipeline
spine_api/services/
  extraction_service.py          # End-to-end extraction orchestration
  agentic_eval_service.py        # Eval API service
  agent_runtime_factory.py       # Runtime configuration
  agent_work_coordinator.py      # SQL-backed work coordination
  agent_runtime_adapters.py      # TripStore/AuditStore bridges
```
