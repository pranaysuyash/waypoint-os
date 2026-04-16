# Discovery Gap Analysis: LLM/AI Integration Architecture

**Date**: 2026-04-16
**Gap Register**: #07 (P1 — the "AI" in the product name)
**Scope**: LLM provider abstraction, prompt registry, extraction enhancement, generation, evaluation, and multi-agent orchestration. NOT: deterministic pipeline logic (which exists and works).

---

## 1. Executive Summary

The product is called "travel_agency_agent" and the documentation describes an LLM-powered travel assistant. **There is zero LLM integration in the codebase.** Every "AI" operation is deterministic regex and heuristic rules. The architecture is correctly designed to accept LLM integration — hook parameters exist, PromptBundle is built as an LLM-ready data structure, safety guardrails are in place — but the engine itself is entirely absent.

~1,600 lines of specification cover LLM integration across prompt versioning, evaluation, proposal generation, and Phase B extraction. Implementation: **1 dead parameter** (`model_client=None` in ExtractionPipeline). The system is a sophisticated deterministic decision engine wrapped in an LLM-shaped architecture, with all the wiring ready but no engine installed.

---

## 2. Evidence Inventory

### What's Documented

| Doc | What It Says | Location |
|-----|-------------|----------|
| `INTEGRATIONS_AND_DATA_SOURCES.md` L31-45 | **"LLM API (Non-negotiable)"** — declares OpenAI/Anthropic as essential, specifies `LLMProvider` Protocol with `complete()` and `stream_complete()` | Docs/ |
| `FIRST_PRINCIPLES_FOUNDATION_2026-04-14.md` L47-53 | Stage 4: Selective LLM augmentation — deterministic backbone + LLM for ambiguity, nuance, personalization. **"LLM output cannot override hard constraints"** | Docs/ |
| `PROMPT_VERSIONING.md` (552 lines) | Complete prompt registry spec: `registry.yaml`, `PromptVersion`, `PromptRegistry`, A/B testing, rollback, prompt namespaces (`nb01.extract_traveler_info`, `nb03.ask_followup_template`, `nb03.branch_presentation`, `nb03.tone_guardrails.cautious`) | Docs/research/ |
| `EVALUATION_FRAMEWORK.md` L111-185 | Layer 2 "LLM-as-Judge" — `evaluate_proposal_with_llm()` using GPT-4/Claude, calibration targets >0.8 correlation | Docs/research/ |
| `NOTEBOOK_04_CONTRACT.md` (770 lines) | NB04 proposal generation: `TravelerProposal`, `DayPlan`, `PricingBreakdown`, `InternalQuoteSheet`. Three generation modes: template, constraint-assembly, research-intensive. **Zero implemented.** | Docs/research/ |
| `PHASE_B_MERGE_CONTRACT_2026-04-15.md` L150-155 | Phase B.3: "Implement LLM extractor — OpenAI, Anthropic, or local". Hybrid architecture: Step 1 regex, Step 2 NER/LLM semantic candidates, Step 3 reconciler. | Docs/ |
| `ADR-001-SCENARIO-HANDLING` L95-112 | Hybrid route parsing: regex first, LLM fallback. Notes ~500ms-2s latency, cost, caching needed. | Docs/architecture/adr/ |
| `DISCUSSION_LOG.md` L118 | "Established deterministic-first architecture with selective LLM usage" | Docs/ |
| `RISK_ANALYSIS.md` L33-56 | Risk: "LLM Hallucinates Bad Advice". Mitigation: "Never let LLM output go directly to traveler" | Docs/ |

### What's Implemented

| Code | What It Does | Status |
|------|-------------|--------|
| `extractors.py` L728-729 | `ExtractionPipeline.__init__(self, model_client=None)` — accepts parameter but **never uses it** | Dead hook |
| `extractors.py` L43-557 | 10+ regex patterns for destination, date, budget, party, intent, owner context extraction | Heuristic replacement for LLM |
| `decision.py` L370-683 | `BUDGET_FEASIBILITY_TABLE` and `BUDGET_BUCKET_RANGES` — 25+ destination cost estimates, hardcoded | Lookup table, not AI |
| `decision.py` L1484-1504 | `generate_question()` — static `QUESTIONS` dict lookup | Template, not generation |
| `decision.py` L1190-1339 | Lifecycle scoring — deterministic weighted averages with fixed thresholds | Algorithmic, not learned |
| `strategy.py` L117-142 | `PromptBundle` dataclass — `system_context`, `user_message`, `constraints`, `audience` | **Built for LLM consumption, never consumed by an LLM** |
| `strategy.py` L598-690 | `_build_traveler_safe_system_context()` and `_build_traveler_safe_constraints()` — generate complete LLM system prompts | **Prompts generated, never executed** |
| `safety.py` L516-544 | `sanitize_text_output()` — regex-based internal concept filtering | Safety net for LLM output that doesn't exist yet |
| `orchestration.py` L71-168 | `run_spine_once()` — chains extract→validate→decision→strategy→sanitize | No LLM step in chain |

### What's NOT Implemented

- No LLM API call anywhere (no `openai`, `anthropic`, `langchain` in dependencies)
- No API key configuration in `.env.example`
- No `LLMProvider` Protocol or any model abstraction
- No prompt templates in `prompts/templates/` (directory is empty)
- No prompt registry or versioning system
- No embedding/RAG/vector store code
- No proposal generation module (NB04)
- No evaluation framework (LLM-as-Judge)
- No multi-agent orchestration (`src/agents/` directory is empty)
- No caching layer for LLM responses
- No cost tracking for LLM usage
- No fallback chain (primary model → secondary model → deterministic)

---

## 3. Gap Taxonomy

### Structural Gaps

| Gap ID | Concept | Implementation | Blocks |
|--------|---------|----------------|--------|
| **AI-01** | LLM Provider Protocol | None — 0 lines | All generation, extraction enhancement, evaluation |
| **AI-02** | Prompt Registry & Versioning | `prompts/templates/` empty, `registry.yaml` not created | A/B testing, prompt iteration, quality tracking |
| **AI-03** | Prompt Templates | 0 YAML files in designated directory | Cannot execute any LLM step |
| **AI-04** | NB04 Proposal Generation | 770-line spec, 0 lines of code | End-to-end value proposition |
| **AI-05** | LLM-as-Judge Evaluation | 185-line spec, 0 lines of code | Quality monitoring, regression detection |
| **AI-06** | Embedding/RAG for Supplier Retrieval | Referenced in vendor docs, 0 lines of code | Historical pattern matching, supplier search |
| **AI-07** | Multi-Agent Orchestration | `src/agents/` empty, referenced in context docs | Scaling beyond single-turn |

### Computation Gaps

| Gap ID | What Needs Computing | Current State | Blocked By |
|--------|---------------------|---------------|------------|
| **AC-01** | Semantic extraction (destination disambiguation, intent from freeform text) | 10+ regex patterns, ~70% coverage estimated | AI-01, AI-03 |
| **AC-02** | Contextual question generation (personalized, conversation-aware) | Static `QUESTIONS` dict lookup | AI-01, AI-03 |
| **AC-03** | Natural language proposal generation (traveler-facing output) | Template strings stapled together by strategy.py | AI-01, AI-03, AI-04 |
| **AC-04** | Budget feasibility reasoning (dynamic, market-aware) | Hardcoded destination cost table | AI-01, vendor data (#01) |
| **AC-05** | Tone adaptation (adaptive language based on context) | Static `TONE_BY_CONFIDENCE` mapping | AI-01, AI-03 |
| **AC-06** | Extraction quality regression testing | No LLM to compare against | AI-05 |

### Integration Gaps

| Gap ID | Connection | Status | Blocked By |
|--------|-----------|--------|------------|
| **AI-01** | LLM Provider → ExtractionPipeline | `model_client` parameter exists but unused | AI-01 (self) |
| **AI-02** | PromptBundle → LLM | Strategy builds PromptBundle, never sends it | AI-01 |
| **AI-03** | LLM Output → Safety Sanitizer | safety.py sanitization exists, has no LLM output to sanitize | AI-01 |
| **AI-04** | Evaluation Framework → LLM Judge | Evaluation spec exists, no LLM to judge with | AI-01 |
| **AI-05** | Phase B Reconciler → LLM Candidates | Phase B contract specifies reconciler merging regex + LLM results | AI-01 |
| **AI-06** | NB04 Generator → Pricing/Budget Data | Proposal generation spec requires financial data that doesn't persist | AI-01, #02 (persistence), #04 (financial state) |

---

## 4. Dependency Graph

```
#02 Data Persistence ───── blocks AI-01 config storage, prompt versioning state
#07 LLM/AI Integration ── blocks ALL "AI" features:
  ├── AC-01: Semantic extraction enhancement
  ├── AC-02: Contextual question generation
  ├── AC-03: Natural language proposal output
  ├── AC-04: Dynamic budget reasoning
  ├── AC-05: Adaptive tone
  ├── AI-04: NB04 proposal generation
  └── AI-05: LLM-as-Judge evaluation

#01 Vendor/Cost ────────── blocks AI-04 (proposal gen needs supplier data)
#04 Financial State ───── blocks AI-04 (proposal gen needs quote/cost data)
```

**Key insight**: Gap #07 is unblocked by any other gap except #02 (for storing prompt versions and evaluation results). It can begin in parallel with persistence implementation.

---

## 5. Data Model (LLM Provider Abstraction)

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, AsyncIterator

@dataclass
class LLMConfig:
    """Configuration for LLM provider selection and behavior."""
    provider: str = "openai"  # "openai" | "anthropic" | "local"
    model: str = "gpt-4o-mini"  # Default cost-effective model
    temperature: float = 0.3  # Low for extraction, higher for generation
    max_tokens: int = 2000
    timeout_seconds: int = 30
    cost_limit_per_request: float = 0.10  # USD
    
    # Primary/fallback chain
    fallback_provider: Optional[str] = None
    fallback_model: Optional[str] = None

@dataclass
class LLMResponse:
    """Standardized LLM response."""
    content: str
    model: str
    provider: str
    usage: dict  # {"prompt_tokens": int, "completion_tokens": int, "total_cost": float}
    latency_ms: int
    cached: bool = False

class LLMProvider(ABC):
    """Protocol for LLM integration — matching INTEGRATIONS_AND_DATA_SOURCES spec."""
    
    @abstractmethod
    async def complete(self, system: str, user: str, config: LLMConfig) -> LLMResponse:
        """Single completion call."""
        
    @abstractmethod
    async def stream_complete(self, system: str, user: str, config: LLMConfig) -> AsyncIterator[str]:
        """Streaming completion for real-time output."""
        
    @abstractmethod
    async def complete_with_schema(self, system: str, user: str, 
                                     schema: dict, config: LLMConfig) -> dict:
        """Structured output via JSON schema or function calling."""

@dataclass
class PromptVersion:
    """From PROMPT_VERSIONING.md spec."""
    namespace: str  # "nb01.extract_traveler_info"
    version: str  # "v1.0.0"
    system_template: str
    user_template: str
    few_shot_examples: list = field(default_factory=list)
    output_schema: Optional[dict] = None
    metadata: dict = field(default_factory=dict)  # author, created_at, changelog
    active: bool = True
    a_b_group: Optional[str] = None  # "control" | "variant_a" | "variant_b"

@dataclass
class PromptRegistryConfig:
    """Where prompts live and how they're managed."""
    registry_path: str = "prompts/registry/registry.yaml"
    templates_path: str = "prompts/templates/"
    cache_ttl_seconds: int = 300
    enable_ab_testing: bool = False
```

---

## 6. Phase-In Recommendations

### Phase 1: LLM Provider + Prompt Infrastructure (P0, ~3-4 days, parallel with #02)

1. **Implement `LLMProvider` Protocol** with OpenAI as primary, Anthropic as fallback
2. **Add API key configuration** to `.env.example` and config module
3. **Install dependencies**: `openai`, `anthropic` (or `litellm` for unified interface)
4. **Implement `PromptRegistry`** with YAML-based version management
5. **Create initial prompt templates** for NB01 extraction and NB03 question generation
6. **Wire `model_client` parameter** in `ExtractionPipeline` to actual LLM calls (Phase B hybrid: regex first, LLM for low-confidence fields)
7. **Add cost tracking** — per-request cost logging to audit store

**Acceptance**: A single spine run can optionally use LLM for extraction enhancement (behind a feature flag). Prompt versions are tracked in YAML. Costs are logged.

### Phase 2: NB04 Proposal Generation (P1, ~5-7 days, blocked by #01 vendor data, #04 financial state)

1. **Implement proposal generation module** — consume PromptBundle from strategy.py, generate traveler-facing proposals via LLM
2. **Wire safety.py sanitization** — now has actual LLM output to sanitize
3. **Implement NB04 generation modes**: template-based (fast, deterministic), constraint-assembly (LLM-enhanced), research-intensive (full LLM)
4. **Add proposal quality evaluation** — implement Layer 1 (deterministic checks) of EVALUATION_FRAMEWORK
5. **Shadow mode testing** — run current deterministic output alongside LLM output, compare

**Acceptance**: LLM can generate a traveler-facing proposal from a PromptBundle. Output passes leakage detection. Shadow mode runs in parallel.

### Phase 3: LLM-as-Judge Evaluation (P2, ~3-4 days)

1. **Implement Layer 2 evaluation** — `evaluate_proposal_with_llm()` per EVALUATION_FRAMEWORK spec
2. **Calibration suite** — compare LLM judge scores against human evaluator scores
3. **Regression detection** — compare LLM output quality across prompt versions
4. **Red-team testing** — implement safety evaluation adversarial test cases

**Acceptance**: Every prompt version change is evaluated by an LLM judge before deployment. Correlation with human evaluators >0.8.

### Phase 4: Extraction Enhancement (P2, ~3-5 days, after Phase B contract is implemented)

1. **Implement Phase B reconciler** — merge regex extraction results with LLM semantic candidates
2. **Confidence-based routing** — use LLM for fields where regex confidence < threshold
3. **Add embedding/RAG for supplier matching** — vector search for historical supplier patterns
4. **Extraction quality regression tests** — compare regex-only vs. hybrid extraction on test suite

**Acceptance**: Extraction pipeline uses LLM for ambiguous fields, falls back to regex for high-confidence matches. Coverage increases from estimated 70% to >90%.

---

## 7. Key Decisions Required

| Decision | Options | Recommendation | Impact |
|----------|---------|----------------|--------|
| LLM Provider | (a) OpenAI only, (b) Anthropic only, (c) Both with fallback, (d) LiteLLM unified | **(d) LiteLLM unified** — single interface, easy provider switching, cost tracking built in | Defines AI-01 core |
| Prompt Storage | (a) YAML files, (b) Database, (c) Code constants | **(a) YAML files** for MVP — versioned in git, human-readable, easy rollback. Migrate to DB later. | Defines AI-02 |
| Extraction Strategy | (a) Replace regex with LLM, (b) Regex first + LLM enhancement, (c) Parallel + reconciler | **(b) Regex first + LLM enhancement** — matches deterministic-first architecture per FIRST_PRINCIPLES | Defines AC-01 |
| Generation Strategy | (a) Pure LLM generation, (b) Template + LLM polish, (c) Constraint-based assembly | **(c) Constraint-based assembly** — structured output, safety guarantees, predictable format | Defines AI-04 |
| Cost Management | (a) No limits, (b) Per-request cost cap, (c) Monthly budget, (d) Per-customer budget | **(b) Per-request cost cap + (c) Monthly budget** — prevent runaway costs | Defines operational cost |
| Evaluation | (a) LLM-as-Judge only, (b) Human evaluators only, (c) Hybrid LLM + human | **(c) Hybrid** — LLM judge for speed, human calibration for accuracy | Defines AI-05 |

---

## 8. Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| LLM hallucination in traveler-facing output | Critical | safety.py sanitization already exists; add LLM output validation layer. Never let LLM output go directly to traveler without deterministic guard. |
| Cost overruns — extraction calls per inquiry | High | Per-request cost cap in LLMConfig. Cache frequent patterns. Use cheapest model for extraction (gpt-4o-mini), reserve expensive model (claude-3.5-sonnet) for generation. |
| Latency — LLM adds 500ms-2s per call | High | Phase B architecture: regex completes in <50ms, LLM enhancement is optional/async. Shadow mode for gradual rollout. |
| Prompt drift — prompt versions degrade over time | Medium | Prompt versioning system (AI-02) with A/B testing and regression detection. |
| Vendor lock-in | Medium | LiteLLM provides unified interface. Prompt templates are provider-agnostic. |
| Deterministic regressions when adding LLM | Medium | Shadow mode testing. Regression test suite for every change. Deterministic baseline always available. |

---

## 9. What's Out of Scope

- Multi-agent orchestration with specialist agents (#08 scope) — LLM provider is prerequisite
- Autonomous booking actions — LLM suggests, human confirms
- Real-time streaming to WhatsApp — Phase 3+
- Fine-tuned models for travel domain — use base models first, evaluate need later
- Training custom embeddings — use off-the-shelf embeddings, evaluate need later