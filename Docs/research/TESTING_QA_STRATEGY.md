# Testing & QA Strategy

**Document ID**: #24  
**Status**: ✅ Complete  
**Last Updated**: 2026-06-26  
**Scope**: Full testing and quality assurance strategy for the Travel Agency AI Copilot — golden datasets, eval coverage targets, quality gates, regression prevention, and synthesis of all existing eval work (D6, agentic feedback, closed-loop learning, version snapshots)

---

## 1. Executive Summary

The codebase has strong foundations — 2,724 passing tests, a mature D6 audit scaffold, an agentic eval feedback loop, and explicit quality doctrine in `AGENTS.md`. But these pieces are not yet a **coherent strategy**. Tests exist without coverage targets. Evals exist without golden datasets. The CI pipeline reports 7 pre-existing failures and 203 remaining ruff violations that reduce its gating value.

This document synthesizes existing work into one framework covering:

1. **Golden Datasets** — labeled ground truth for extraction, decision, and agent accuracy
2. **Eval Coverage Targets** — what must be measured and what passing looks like
3. **Quality Gates** — where quality checks block progression (CI, deployment, promotion)
4. **Regression Prevention** — how to catch and prevent regressions across AI behavior
5. **Implementation Roadmap** — phased build-out with dependencies

---

## 2. Current State Assessment

### 2.1 What Exists (Good)

| Asset | Strength | Location |
|-------|----------|----------|
| **D6 Audit Scaffold** | Mature fixture-based eval for deterministic rules: fixtures, metrics, gates, manifest, snapshot | `src/evals/audit/` |
| **Agentic Feedback Loop** | `AgenticEvalRecord`, `build_routing_metrics()`, `build_repeated_failure_signal()` with layer recommendations | `src/evals/agentic_feedback.py` |
| **Closed-Loop Learning** | `FixCandidate`, `ShadowTestResult`, `ClosedLoopLearningAgent` (32 tests) | `src/agents/closed_loop_learning.py` |
| **Version Snapshots** | Immutable version tracking for prompt/schema/routing/dictionary/normalization | `src/intake/version_snapshot.py` |
| **Backend Tests** | 2,724 passing, 7 pre-existing failures | `tests/` (101 test files) |
| **Frontend Tests** | Vitest with React Testing Library, route-map guard test | `frontend/src/` |
| **CI Pipeline** | 4 jobs (docs, ruff lint, backend tests, frontend quality) | `.github/workflows/ci.yml` |
| **Extraction Smoke Tests** | Provider connectivity validation | `src/extraction/smoke_test.py` |
| **4-Phase Dev Workflow** | Fix → Review → Audit → Handoff with 11-dimension checklist | `AGENTS.md` |
| **D6 Gate Snapshot** | CI guard against snapshot drift | `scripts/verify_d6_gate_snapshot.py` |
| **API Contract Verification** | Mandatory curl-before-code for FE/BE integration | `AGENTS.md` |

### 2.2 What's Missing (Gaps)

| Gap | Impact | Location |
|-----|--------|----------|
| **No golden extraction dataset** | Extraction accuracy is unknown — no precision/recall/F1 | `data/fixtures/extraction/` does not exist |
| **D6 rule runners only for `activity`** | 4+ categories (routing, feasibility, document_readiness, destination_intelligence) have no rule runners | `src/evals/audit/rules/` |
| **No extraction accuracy metrics** | Smoke tests prove connectivity, not correctness | `src/extraction/smoke_test.py` |
| **No LLM-as-judge implementation** | No automated quality scoring for agent outputs | `src/evals/judge/` does not exist |
| **No cross-agent scan overlap detection** | Agents may produce redundant or conflicting actions | `src/agents/runtime.py` |
| **No end-to-end pipeline eval** | Full intake→extraction→decision→agent pipeline not evaluated as a whole | None |
| **7 pre-existing test failures** | CI is not green, reducing gating credibility | Tests listed below |
| **203 remaining ruff violations** | Lint gate is perpetually red | `src/`, `spine_api/`, `tests/` |
| **3 frontend typecheck errors, 67 lint issues** | Frontend quality gate is perpetually red | `frontend/src/lib/seasonalCampaigns.ts` + others |
| **No cost-per-trip tracking** | LLM costs not attributed to individual trips | `src/evals/agentic_feedback.py` |
| **No per-step latency breakdown** | Only aggregate p50/p95, not step-level | `src/evals/agentic_feedback.py` |
| **Fragmented telemetry** | Multiple event systems (SQL events, JSONL telemetry, run ledger, decision telemetry, checkpoint files) with no canonical join | Multiple locations |
| **No automated regression test generation** | Production failures don't auto-create test fixtures | None |
| **No human annotation loop** | No systematic capture of human review outcomes as labeled data | `src/analytics/review.py` |

### 2.3 Current Test/Quality Numbers

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Backend tests passing | 2,724 | 2,724+ | ✅ |
| Pre-existing test failures | 7 | 0 | ❌ |
| Skipped tests (external dep) | 47 | — | 🟡 |
| Ruff violations | 203 | 0 | ❌ |
| Frontend typecheck errors | 3 | 0 | ❌ |
| Frontend lint issues | 67 | 0 | ❌ |
| D6 audit categories with rule runners | 1 of 5+ | All | ❌ |
| Extraction accuracy (F1) | Unknown | ≥ 0.90 | ❌ |
| E2E pipeline eval coverage | 0% | Full | ❌ |
| Cost per trip tracking | None | Tracked | ❌ |

---

## 3. Testing Pyramid for an AI-Heavy Application

Standard testing pyramids don't work for AI — you can't assert `result == expected` when the output is probabilistic. This pyramid is adapted for an LLM-driven pipeline:

```
                    ┌─────────────────────────────────────┐
                    │   E2E PIPELINE EVALS                 │
                    │   (full intake→extraction→decision   │
                    │    →agent→output, golden trip sets)  │
                    │   Frequency: per CI run, per deploy   │
                    └─────────────────────────────────────┘
                                   ▲
                    ┌─────────────────────────────────────┐
                    │   LLM-AS-JUDGE QUALITY SCORING       │
                    │   (agent output quality, tone,       │
                    │    completeness, adherence)          │
                    │   Frequency: daily / per prompt change│
                    └─────────────────────────────────────┘
                                   ▲
                    ┌─────────────────────────────────────┐
                    │   PROBABILISTIC EVALS                │
                    │   (extraction accuracy F1, agent     │
                    │    scan precision/recall, routing    │
                    │    metrics, cost/latency budgets)    │
                    │   Frequency: per CI run               │
                    └─────────────────────────────────────┘
                                   ▲
                    ┌─────────────────────────────────────┐
                    │   CONTRACT & INTEGRATION TESTS       │
                    │   (API contracts, schema compliance, │
                    │    state machine transitions, event  │
                    │    shapes, boundary/edge cases)      │
                    │   Frequency: per CI run               │
                    └─────────────────────────────────────┘
                                   ▲
                    ┌─────────────────────────────────────┐
                    │   DETERMINISTIC UNIT TESTS           │
                    │   (functions, validators, helpers,   │
                    │    parsers, mappers, formatters)     │
                    │   Frequency: per commit               │
                    └─────────────────────────────────────┘
```

### 3.1 Layer Description

| Layer | What It Tests | What It Uses | Current Coverage |
|-------|---------------|-------------|-----------------|
| **Unit Tests** | Deterministic logic — parsers, validators, mappers, formatters, helpers | pytest, Hypothesis, standard assertions | ✅ Strong (~2,700 tests) |
| **Contract Tests** | API shapes, schema compliance, state transitions, event shapes | Pydantic validation, `test_*` fixtures, curl verification | ✅ Good but 7 pre-existing failures |
| **Probabilistic Evals** | Extraction accuracy (F1), agent precision/recall, routing metrics, cost/latency targets | D6 scaffold + golden datasets | ❌ Extraction accuracy not measured |
| **LLM-as-Judge** | Agent output quality, tone adherence, completeness ratings | LLM clients with rubrics | ❌ Not implemented |
| **E2E Pipeline Evals** | Full pipeline correctness on golden trips | Golden trip datasets + full pipeline run | ❌ Not implemented |

---

## 4. Golden Datasets

### 4.1 Purpose

Golden datasets provide **labeled ground truth** against which probabilistic behavior is measured. Without them, we can't answer "is extraction getting better or worse?"

### 4.2 Dataset Catalog

| Dataset | Contents | Records | Location | Priority |
|---------|----------|---------|----------|----------|
| **Extraction Golden** | Raw input → expected extracted fields with per-field ground truth | 50+ | `data/fixtures/extraction/golden.json` | P0 |
| **Decision Golden** | Extracted packet → expected decision state | 30+ | `data/fixtures/decision/golden.json` | P0 |
| **Agent Scan Golden** | Trips that should/shouldn't trigger each agent | 20+ per agent | `data/fixtures/agent_scan/` | P1 |
| **Pipeline Golden** | Raw input → expected extraction → expected decision → expected agent outputs | 15+ | `data/fixtures/pipeline/golden/` | P1 |
| **Regression Golden** | Past production failures with expected fix | Growing | `data/fixtures/regression/` | P2 |

### 4.3 Extraction Golden Dataset Schema

```json
{
  "fixtures": [
    {
      "id": "ext_family_bali_001",
      "description": "Family of 4 from Mumbai to Bali, July 10-16, INR 3-4L",
      "input": {
        "raw_note": "Family of 4 from Mumbai planning 8 nights in Bali in August. Budget USD 7000-9000. Beach resort, vegetarian meals, kids activities.",
        "document_type": "whatsapp_message"
      },
      "expected_fields": {
        "origin": { "value": "Mumbai", "confidence": "high" },
        "destination": { "value": "Bali", "confidence": "high" },
        "party_size": { "value": 4, "confidence": "high" },
        "travel_dates": { "value": "August 2026", "confidence": "medium" },
        "budget_min": { "value": 7000, "confidence": "high" },
        "budget_max": { "value": 9000, "confidence": "high" },
        "budget_currency": { "value": "USD", "confidence": "high" },
        "trip_purpose": { "value": "family", "confidence": "medium" },
        "preferences": { "value": "beach resort, vegetarian meals, kids activities", "confidence": "high" }
      },
      "expected_absent": ["origin_airport", "hotel_name"],
      "fields_with_hallucination_risk": ["trip_purpose"],
      "expected_decision_state": "PROCEED_INTERNAL_DRAFT",
      "expected_blockers": ["soft_preferences"]
    }
  ]
}
```

### 4.4 Dataset Maintenance

- **Creation**: Hand-curated from real test scenarios (30 persona scenarios in notebooks/)
- **Versioning**: Git-tracked JSON, version bumped when adding/modifying fixtures
- **Freshness check**: CI warns if golden dataset unchanged for >30 days
- **Expansion**: Production failures that pass review → new regression fixture
- **Ownership**: Maintained alongside the codebase, not as a separate artifact

---

## 5. Eval Coverage Targets

### 5.1 Extraction Pipeline

| Dimension | Metric | Current | Target | Gate |
|-----------|--------|---------|--------|------|
| **Field extraction accuracy** | Per-field F1 | Unknown | ≥ 0.90 | CI warning < 0.85, block < 0.80 |
| **Schema compliance** | % valid JSON matching schema | Unknown | ≥ 0.98 | CI block < 0.95 |
| **Hallucination rate** | % extractions with fabricated fields | Unknown | ≤ 0.05 | CI warning > 0.08, block > 0.10 |
| **Fallback trigger rate** | % extractions using fallback | Partial | ≤ 0.25 | CI warning > 0.30 |
| **Useful fallback rate** | % fallbacks producing correct result | Unknown | ≥ 0.60 | CI warning < 0.50 |
| **Multi-model agreement** | OpenAI vs Gemini agreement % | Unknown | ≥ 0.85 | CI warning < 0.80 |
| **Document type coverage** | F1 by document type (passport, visa, etc.) | Unknown | ≥ 0.85 per type | Block < 0.75 per type |

### 5.2 Agent Performance

| Dimension | Metric | Current | Target | Gate |
|-----------|--------|---------|--------|------|
| **Execute success rate** | % execute() returning success | Tracked | ≥ 0.95 | Block < 0.85 |
| **Scan precision** | % work items leading to meaningful action | Unknown | ≥ 0.80 | Block < 0.60 |
| **Scan recall** | % actionable trips detected | Unknown | ≥ 0.85 | Block < 0.70 |
| **Review correction rate** | % agent outputs needing human correction | Tracked | ≤ 0.15 | Warning > 0.20, block > 0.25 |
| **False escalation rate** | % escalations judged unnecessary | Partial | ≤ 0.10 | Warning > 0.15, block > 0.20 |
| **Missed escalation rate** | % necessary escalations not triggered | Unknown | ≤ 0.05 | Block > 0.10 |

### 5.3 Operational Health

| Dimension | Metric | Current | Target | Gate |
|-----------|--------|---------|--------|------|
| **p50 extraction latency** | Median ms | Tracked | ≤ 5,000ms | Warning > 6,000ms |
| **p95 extraction latency** | 95th percentile ms | Tracked | ≤ 15,000ms | Warning > 18,000ms |
| **Cost per extraction** | USD | Tracked | ≤ $0.05 | Warning > $0.08 |
| **Error rate** | % failed extractions | Tracked | ≤ 0.10 | Warning > 0.15 |
| **CI green rate** | % green CI runs over past 30 days | ~70% | ≥ 95% | Warning < 90% |

### 5.4 Output Quality (LLM-as-Judge)

| Dimension | Metric | Current | Target | Gate |
|-----------|--------|---------|--------|------|
| **Agent draft quality** | Mean score (1-5) across rubric | Unknown | ≥ 4.0 | Block < 3.5 |
| **Tone adherence** | % matching intended persona | Unknown | ≥ 0.85 | Warning < 0.80 |
| **Completeness** | % meeting output contract requirements | Unknown | ≥ 0.95 | Block < 0.90 |
| **Format compliance** | % valid output shape | Unknown | ≥ 0.98 | Block < 0.95 |

---

## 6. Quality Gates

### 6.1 Gate Hierarchy

```
┌────────────────────────────────────────────────────────────────────────┐
│                    QUALITY GATE HIERARCHY                               │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  GATE 1: COMMIT GATE (pre-commit, local)                               │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │  • Unit tests pass (local subset: < 30s)                      │   │
│  │  • Ruff lint on changed files (zero new violations)           │   │
│  │  • TypeScript typecheck on changed files                      │   │
│  │  • Motto attestation (motto_v3.md reviewed)                   │   │
│  └────────────────────────────────────────────────────────────────┘   │
│                               │                                        │
│                               ▼                                        │
│  GATE 2: CI PIPELINE GATE (per push/PR)                                │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │  • All unit + contract tests pass (2,724+ back, front tests)  │   │
│  │  • Ruff lint — zero violations target, warning-only interim   │   │
│  │  • TypeScript typecheck — zero errors target                   │   │
│  │  • ESLint — zero errors target, warning-only interim           │   │
│  │  • D6 gate snapshot verification                                │   │
│  │  • Extraction accuracy evals (F1 ≥ target thresholds)          │   │
│  │  • No new F821/F401/F841 violations introduced                  │   │
│  └────────────────────────────────────────────────────────────────┘   │
│                               │                                        │
│                               ▼                                        │
│  GATE 3: DEPLOYMENT GATE (pre-production deploy)                      │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │  • All CI gates pass                                            │   │
│  │  • E2E pipeline eval passes on golden trip dataset              │   │
│  │  • LLM-as-judge quality scores ≥ targets                        │   │
│  │  • Routing health metrics within thresholds                     │   │
│  │  • Cost/latency budgets not exceeded                            │   │
│  │  • No blocking security findings                                │   │
│  └────────────────────────────────────────────────────────────────┘   │
│                               │                                        │
│                               ▼                                        │
│  GATE 4: PROMOTION GATE (prompt/model/routing change promotion)      │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │  • Shadow run completed with evidence                          │   │
│  │  • Accuracy delta ≥ 0 (no regression)                          │   │
│  │  • Cost delta within budget                                    │   │
│  │  • False escalation rate not increased                         │   │
│  │  • Human review: no critical regressions                       │   │
│  └────────────────────────────────────────────────────────────────┘   │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

### 6.2 Gate Behavior

| Gate | Blocking | Warning | Bypass |
|------|----------|---------|--------|
| **Commit Gate** | ❌ Block on failures | — | `--no-verify` (documented risk) |
| **CI Gate** | ❌ Block on test failures, ❌ Block on new lint/type errors | Allow existing violations; degrade score | PR merge with `bypass-ci` label + owner approval |
| **Deployment Gate** | ❌ Block on any red | Yellow if any metric trending down | Owner override with documented rationale |
| **Promotion Gate** | ❌ Block on regression > 2% | Yellow on cost increase > 10% | Owner override + documented acceptance of risk |

### 6.3 Current CI Gate Issues (Immediate Fixes Needed)

| Issue | Fix | Owner | Priority |
|-------|-----|-------|----------|
| 7 pre-existing test failures | Investigate and fix root causes — likely contract drift | Backend | P0 |
| 203 ruff violations | Triage: auto-fix F841 (41), F401 (63), E712 (3); defer E402 (91) as pre-existing debt | Backend | P0 |
| 3 frontend typecheck errors | Fix nullable handling in `seasonalCampaigns.ts` | Frontend | P0 |
| 67 frontend lint issues | Auto-fix where possible, manual fixes for remaining | Frontend | P1 |
| No extraction accuracy gate | Build golden dataset + rule runner | Eval | P1 |

---

## 7. Regression Prevention Framework

### 7.1 Detection Mechanisms

| Mechanism | What It Catches | How | Response Time |
|-----------|----------------|-----|---------------|
| **D6 Gate Snapshot** | Drift in deterministic audit rule output | Compare `build_gate_snapshot()` output against committed snapshot in CI | Per CI run |
| **Route Parity Snapshot** | Route additions/removals/changes | `scripts/snapshot_server_routes.py` + test | Per CI run |
| **OpenAPI Path Snapshot** | API contract drift | `tests/test_server_openapi_path_parity.py` | Per CI run |
| **Version Snapshot Diff** | Runtime config changes (prompt/schema/routing) | `VersionSnapshot.diff()` + `changed_dimensions()` | Per deploy |
| **Routing Metrics Trends** | Degradation in escalation/false-positive/latency | `build_routing_metrics()` + threshold alerts | Per eval run |
| **Repeated Failure Signals** | Emerging failure patterns before they become systemic | `build_repeated_failure_signal()` | Per eval run |
| **E2E Pipeline Eval** | Full pipeline correctness changes | Golden trip dataset eval | Per deploy |

### 7.2 Regression Response Procedure

When a regression is detected (accuracy drop > 5%, new F1 < 0.80, latency increase > 20%):

```
1. DETECT: CI failure or metric alert fires
2. ISOLATE: Check VersionSnapshot.diff() to identify what changed (prompt? schema? routing?)
3. TRIAGE: Is this a transient (model API issue) or permanent (config change)?
   - Transient: Add to monitoring, no rollback
   - Permanent: Determine if rollback is feasible
4. FIX: 
   - If config revert fixes it: revert config, document root cause
   - If code change needed: create test fixture from the regression case, fix code, verify fix passes
5. VERIFY: Run regression test suite (includes past regression fixtures)
6. DOCUMENT: Record in regression log — what changed, what broke, how fixed, prevention strategy
```

### 7.3 Automated Regression Test Generation

When a production failure is identified and confirmed as a regression:

1. **Extract**: Capture the input (raw note / document) and expected output
2. **Create fixture**: Add to `data/fixtures/regression/` with ID, input, expected output, date, and PR link
3. **Add to eval set**: The new fixture is automatically included in the next eval run
4. **Verify fix**: The fixture must pass before the regression fix is accepted

This ensures that every regression ever fixed stays fixed.

---

## 8. Existing Eval Infrastructure — Synthesis

### 8.1 D6 Audit Scaffold (`src/evals/audit/`)

**Purpose**: Deterministic rule evaluation with fixtures, metrics, and manifest-based gating.

**Already Good**:
- Full fixture pipeline: load → run → compute metrics → compare to manifest thresholds
- Snapshot system for CI drift detection
- Public authority resolution for surface-level output
- 5+ categories defined in manifest

**Needs Work**:
- Only `activity` category has a rule runner — add runners for `routing`, `feasibility`, `document_readiness`, `destination_intelligence`
- No extraction accuracy rule runner — highest priority addition

### 8.2 Agentic Feedback Loop (`src/evals/agentic_feedback.py`)

**Purpose**: Runtime eval signal pipeline — produce, filter, aggregate, and act on eval signals.

**Already Good**:
- `AgenticEvalRecord` with canonical shape
- `build_routing_metrics()` with fallback/review trigger rates, latency, cost
- `build_repeated_failure_signal()` with layer-specific recommendations
- `aggregate_eval_records()` producing full summary

**Needs Work**:
- No threshold alerting on routing metrics
- No cost-per-trip attribution
- No proactive regression alerts (currently reactive — only fires when failures repeat)
- No canonical join across fragmented telemetry surfaces

### 8.3 Closed-Loop Learning (`src/agents/closed_loop_learning.py`)

**Purpose**: Convert repeated failures into fix candidates with shadow testing.

**Already Good**:
- `FixCandidate` with layer recommendations and owner
- `ShadowTestResult` with deterministic simulation (simulated_fixes, regressions, verdict)
- 32 tests covering unit, integration, and supervisor-level behavior

**Needs Work**:
- Shadow test is deterministic simulation only — no real LLM reprocessing
- No keep/revert/rollout gates in operator tooling
- No persistence of work items as backlog entries

### 8.4 Version Snapshots (`src/intake/version_snapshot.py`)

**Purpose**: Immutable tracking of extraction configuration dimensions at point of use.

**Already Good**:
- Tracks prompt, schema, routing, dictionary, normalization versions
- `diff()` and `changed_dimensions()` for regression root cause analysis
- Rollout mode tracking (shadow/canary/full/rolled_back/pending)

**Needs Work**:
- Not yet wired into extraction accuracy comparisons (no accuracy per snapshot)
- Not yet used for prompt A/B testing

### 8.5 Current Eval Coverage Map

```
                        EXISTING EVAL COVERAGE
        ┌────────────────────────────────────────────────┐
        │                                                │
        │  D6 AUDIT        AGENTIC FEEDBACK    CLOSED    │
        │  SCAFFOLD         LOOP                LOOP     │
        │                                                │
        │  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
        │  │ Activity │  │ Routing  │  │ Shadow   │     │
        │  │ ✓        │  │ Metrics  │  │ Testing  │     │
        │  │          │  │ ✓        │  │ ✓        │     │
        │  └──────────┘  └──────────┘  └──────────┘     │
        │                                                │
        │  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
        │  │ Routing  │  │ Failure  │  │ Work     │     │
        │  │ ✗        │  │ Signals  │  │ Items    │     │
        │  │          │  │ ✓        │  │ ✓        │     │
        │  └──────────┘  └──────────┘  └──────────┘     │
        │                                                │
        │  COVERAGE GAPS:                                │
        │  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
        │  │ Extra-   │  │ LLM-as-  │  │ Pipeline │     │
        │  │ ction F1 │  │ Judge    │  │ E2E Eval │     │
        │  │ ✗        │  │ ✗        │  │ ✗        │     │
        │  └──────────┘  └──────────┘  └──────────┘     │
        │                                                │
        └────────────────────────────────────────────────┘
```

---

## 9. Integration with Existing Frameworks

### 9.1 4-Phase Development Workflow (AGENTS.md)

The existing 4-Phase workflow (Fix → Review → Audit → Handoff) and 11-Dimension Audit checklist are **complementary** to this strategy — not competing. The mapping:

| Phase | Testing & QA Role |
|-------|-------------------|
| **Phase 1: Fix & Verify** | Run unit tests, contract tests. Ensure CI passes. |
| **Phase 2: Review & Iterate** | Apply eval framework: run D6 eval suite, check routing metrics, verify no regression. |
| **Phase 3: Audit & Assess** | 11-dimension checklist includes "Quality & Reliability" dimension using this strategy's metrics. |
| **Phase 4: Handoff** | Document eval results, regression checks, and coverage gaps in handoff doc. |

### 9.2 CI Pipeline

The existing `.github/workflows/ci.yml` should be extended with additional eval steps as they become available:

```yaml
# Proposed additions to CI pipeline:
- name: Extraction accuracy eval
  run: uv run python -m src.evals.audit.runners.run_extraction_eval

- name: Routing health check
  run: uv run python -m src.evals.agentic_feedback check_routing_health

- name: Pipeline golden trip eval
  run: uv run python -m src.evals.audit.runners.run_pipeline_eval
```

Not added yet because the rule runners don't exist. Added when Phase 1 implementation completes.

---

## 10. Implementation Roadmap

### Phase 0: Make CI Green (Week 1) — PREREQUISITE

Before any new eval infrastructure, the existing CI must be made to pass reliably. A red CI means evals run on broken foundations.

| Task | Effort | Dependencies |
|------|--------|-------------|
| Fix 7 pre-existing test failures | 1-2 days | Root cause investigation |
| Auto-fix 104 auto-fixable ruff violations (F841 + F401) | 30 min | None |
| Fix 3 frontend typecheck errors | 30 min | None |
| Fix 67 frontend lint issues (auto-fix + manual) | 1-2 hours | None |
| Change ruff CI gate to zero-new-violations (allow existing) | 10 min | Above fixes applied |

**Success criteria**: CI is green on `master` for 5 consecutive runs.

### Phase 1: Extraction & D6 Eval Foundation (Weeks 1-2)

| Task | Effort | Dependencies |
|------|--------|-------------|
| Create `data/fixtures/extraction/golden.json` (50+ fixtures) | 2 days | Existing persona scenarios |
| Add `src/evals/audit/rules/extraction.py` — rule runner with per-field F1 | 2 days | Golden dataset |
| Extend D6 manifest with extraction category + thresholds | 1 day | Rule runner |
| Add D6 rule runners for routing, feasibility, document_readiness | 3 days | Existing audit scaffold |
| Add `check_routing_health()` with threshold alerts | 1 day | Agentic feedback loop |

**Success criteria**: Extraction accuracy measured for first time. 4+ D6 categories active.

### Phase 2: Quality Scoring (Weeks 3-4)

| Task | Effort | Dependencies |
|------|--------|-------------|
| Create `src/evals/judge/` — LLM-as-judge module with per-agent rubrics | 3 days | Existing LLM clients |
| Wire version snapshots into extraction accuracy comparisons | 2 days | Version snapshot system |
| Add agent scan precision/recall eval fixtures | 2 days | Agent scan golden dataset |
| Add extraction accuracy eval to CI pipeline | 1 day | Phase 1 extraction eval |

**Success criteria**: Automated quality scoring for top 5 agents. Extraction F1 tracked in CI.

### Phase 3: Pipeline & Regression (Weeks 5-6)

| Task | Effort | Dependencies |
|------|--------|-------------|
| Create `data/fixtures/pipeline/golden/` — 15+ end-to-end golden trips | 3 days | Phase 1 extraction fixtures |
| Add `src/evals/audit/rules/pipeline.py` — e2e pipeline eval rule runner | 3 days | Pipeline golden dataset |
| Add regression fixture creation from production failures | 2 days | Phase 2 eval feedback loop |
| Add cost-per-trip attribution | 2 days | Agentic feedback loop |

**Success criteria**: E2E pipeline eval runs in CI. Regression fixtures prevent replay.

### Phase 4: Operational Intelligence (Weeks 7-8)

| Task | Effort | Dependencies |
|------|--------|-------------|
| Canonical telemetry join surface | 3 days | Execution event service + run ledger + decision telemetry |
| Latency regression detection per prompt version | 2 days | Version snapshot system |
| Per-step latency breakdown in routing metrics | 2 days | Agentic feedback loop |
| Deployment gate check automation | 2 days | All prior phases |

**Success criteria**: Deployment blocked if eval thresholds not met. Cost/latency tracked per trip.

### Phase 5: Continuous Improvement (Week 9+)

| Task | Effort | Dependencies |
|------|--------|-------------|
| Human annotation loop for LLM-as-judge calibration | 3 days | Phase 2 LLM-as-judge |
| Cross-agent orchestration eval | 3 days | Phase 3 pipeline eval |
| Automated regression test generation from failures | 3 days | Phase 3 regression system |
| Cross-provider agreement testing (OpenAI vs Gemini) | 2 days | Extraction eval |

**Success criteria**: Automated regression generation. Orchestration eval covers 10+ agent interaction scenarios.

---

## 11. File Index

### New Files to Create

| File | Purpose | Phase |
|------|---------|-------|
| `data/fixtures/extraction/golden.json` | 50+ labeled extraction test cases | P1 |
| `data/fixtures/decision/golden.json` | 30+ decision test cases | P1 |
| `data/fixtures/agent_scan/*.json` | Agent scan precision/recall fixtures | P2 |
| `data/fixtures/pipeline/golden/*.json` | End-to-end pipeline golden trips | P3 |
| `data/fixtures/regression/*.json` | Past regression regression fixtures | P3 |
| `src/evals/audit/rules/extraction.py` | Extraction accuracy rule runner | P1 |
| `src/evals/audit/rules/routing.py` | Routing rule runner | P1 |
| `src/evals/audit/rules/feasibility.py` | Feasibility rule runner | P1 |
| `src/evals/audit/rules/document_readiness.py` | Document readiness rule runner | P1 |
| `src/evals/audit/rules/pipeline.py` | E2E pipeline eval rule runner | P3 |
| `src/evals/judge/__init__.py` | LLM-as-judge module | P2 |
| `src/evals/judge/rubrics.py` | Per-agent evaluation rubrics | P2 |
| `src/evals/judge/evaluator.py` | LLM-as-judge evaluator | P2 |

### Existing Eval Files (Referenced)

| File | Purpose |
|------|---------|
| `src/evals/audit/__init__.py` | D6 audit scaffold exports |
| `src/evals/audit/fixtures.py` | AuditFixture, ExpectedFinding |
| `src/evals/audit/gates.py` | EvalGateReport, evaluate_report_against_manifest |
| `src/evals/audit/manifest.py` | EvalManifest, EvalCategoryConfig |
| `src/evals/audit/manifest.yaml` | Category thresholds |
| `src/evals/audit/metrics.py` | CategoryMetrics, compute_category_metrics |
| `src/evals/audit/runner.py` | EvalReport, run_eval_suite |
| `src/evals/audit/snapshot.py` | build_gate_snapshot, write_gate_snapshot |
| `src/evals/audit/public_authority.py` | resolve_public_authority |
| `src/evals/audit/rules/activity.py` | run_activity_fixture |
| `src/evals/agentic_feedback.py` | AgenticEvalRecord, routing metrics, failure signals |
| `src/agents/closed_loop_learning.py` | FixCandidate, ShadowTestResult, ClosedLoopLearningAgent |
| `src/intake/version_snapshot.py` | VersionSnapshot, capture_version_snapshot |
| `src/extraction/smoke_test.py` | Provider connectivity tests |

---

## 12. Appendix: Current Test Failure Inventory

### Pre-Existing Test Failures (7 total)

| Test | Failure | Likely Cause | Priority |
|------|---------|-------------|----------|
| `test_call_capture_phase2.py::test_patch_structured_field_with_null_clears_value` | Contract drift — null field behavior changed | P0 |
| `test_public_checker_contract_authority.py::test_public_checker_contract_keeps_advisory_weather_out_of_canonical_blockers` | Snapshot/public authority drift | P0 |
| `test_public_checker_contract_authority.py::test_public_checker_contract_promotes_weather_when_snapshot_marks_authoritative` | Snapshot/public authority drift | P0 |
| `test_stage_transitions.py::TestStageTransitionEndpoint::test_generic_patch_rejects_stage` | Stage transition endpoint change | P1 |
| (3 additional — see full test output) | — | P1 |

### Pre-Existing Ruff Violations (203 total)

| Code | Count | Description | Auto-Fixable | Action |
|------|-------|-------------|-------------|--------|
| E402 | 91 | Module import not at top | No | Defer — structural debt |
| F401 | 63 | Unused import | **Yes (51)** | Run `ruff check --fix --select F401` |
| F841 | 41 | Unused variable | **Yes (31)** | Run `ruff check --fix --select F841` |
| E712 | 3 | True/false comparison | **Yes** | Run `ruff check --fix --select E712` |
| E741 | 2 | Ambiguous variable name | No | Manual rename |
| F811 | 2 | Redefined while unused | **Yes** | Run `ruff check --fix --select F811` |
| F402 | 1 | Import shadowed by loop var | No | Manual rename |

**Total auto-fixable**: ~104 violations. CI gate should change to "zero new violations" rather than "zero total" to avoid blocking on pre-existing debt.

---

## 13. Appendix: Key References

| Document | Relevance |
|----------|-----------|
| `AGENTS.md` (4-Phase Workflow, 11-Dimension Audit) | Development process quality framework |
| `Docs/research/EVALUATION_FRAMEWORK.md` (#18) | 4-layer evaluation pyramid (Structural → LLM-as-Judge → Human → Business) |
| `Docs/research/AGENTIC_EVAL_CANONICAL_ROADMAP_2026-06-20.md` | Full component map + 16-phase implementation plan |
| `Docs/research/AGENTIC_FLOW_EVAL_AUDIT_2026-06-18.md` | Current-state audit: strong runtime contracts, fragmented telemetry, missing learning loop |
| `Docs/research/AGENTIC_EVAL_ARTICLE_TO_ACTION_MATRIX_2026-06-19.md` | Executable rules from eval doctrine |
| `Docs/EXPLORATION_TOPICS.md` (#24) | Original exploration topic stub |
| `.github/workflows/ci.yml` | Current CI pipeline |
| `Docs/research/DEPLOYMENT_OPERATIONS.md` | Deployment target decision (Render) and operations context |
| `/Users/pranay/Projects/AGENTIC_EVAL_RULES.md` | Shared Projects-level eval rules |
| `/Users/pranay/Projects/skills/agentic-eval-loop/SKILL.md` | Reusable agentic eval loop skill |

---

*This is a living strategy document. Update as implementation progresses and new eval capabilities are added.*
