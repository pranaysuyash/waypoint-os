# Architecture Decision: LLM Output Caching + NB05/NB06 in D4/D6 Context

**Date**: 2026-04-16
**Status**: Decision document — pending review
**Companion to**: `ARCHITECTURE_DECISION_D4_D6_SUITABILITY_AUDIT_2026-04-16.md`
**Cross-references**:
- `V02_GOVERNING_PRINCIPLES.md` (NB05/NB06 layer ownership)
- `DISCOVERY_GAP_LLM_AI_INTEGRATION_2026-04-16.md` (Gap #07 — zero LLM integration exists)
- `src/decision/hybrid_engine.py` (existing cache→rule→LLM→cache pattern)
- `src/decision/cache_schema.py` (CachedDecision with feedback + success_rate)
- `Docs/research/REAL_WORLD_VALIDATION.md` (shadow mode design)

---

## Part 1: LLM Output Extraction and Reuse — "Call Once, Reuse Forever"

### The Principle

Every LLM call is expensive (latency + cost + non-determinism). The system must:
1. **Extract structured output** from every LLM response (not free text)
2. **Cache the extracted result** keyed by normalized inputs
3. **Reuse cached results** for similar future calls
4. **Learn from feedback** — cached decisions with low success rates get evicted; high-success ones become de facto rules

### What Already Exists

The `src/decision/` module already implements this exact pattern:

| Component | What It Does | Location |
|-----------|-------------|----------|
| `HybridDecisionEngine` | Cache → Rule → LLM → Cache-the-result chain | `src/decision/hybrid_engine.py` L111-640 |
| `CachedDecision` | Typed cache entry with `success_rate`, `feedback_count`, `use_count`, expiry | `src/decision/cache_schema.py` L17-136 |
| `DecisionCacheStorage` | Disk-backed JSON storage per decision type | `src/decision/cache_storage.py` |
| `generate_cache_key` | Deterministic hash from packet inputs | `src/decision/cache_key.py` |
| `record_feedback(success)` | Exponential moving average success rate update | `src/decision/cache_schema.py` L96-108 |
| `is_valid(max_age_days, min_success_rate)` | Cache eviction by age + success rate | `src/decision/cache_schema.py` L110-135 |
| Decision schemas | JSON Schema for 5 decision types (elderly mobility, toddler pacing, budget, visa, composition) | `src/decision/hybrid_engine.py` L132-178 |
| Rule engine fallbacks | Built-in deterministic rules before LLM | `src/decision/rules/` |

**This is a solid foundation.** The architecture just needs to be extended to cover ALL LLM touchpoints, not just decision-type risk assessments.

### What Needs to Extend

The hybrid engine currently handles **risk assessment decisions** only. But LLM calls will eventually happen across multiple touchpoints:

| Touchpoint | LLM Purpose | Caching Strategy |
|------------|-------------|------------------|
| **Risk assessment** (existing) | Elderly mobility, toddler pacing, budget, visa, composition | ✅ Already cached via `HybridDecisionEngine` |
| **Extraction enhancement** (Phase B) | Semantic field extraction where regex fails | Cache by `(raw_input_hash, field_name)` → extracted value |
| **Question generation** (NB03) | Contextual follow-up questions | Cache by `(decision_state, operating_mode, missing_fields_hash)` → question set |
| **Proposal generation** (NB04) | Traveler-facing itinerary text | Cache by `(packet_hash, option_archetype)` → proposal draft |
| **Activity suitability** (D4 Phase 2+) | Nuanced scoring where heuristic is insufficient | Cache by `(activity_id, participant_ref, context_hash)` → scored result |
| **Audit explanation** (D6) | Natural language audit finding explanation | Cache by `(finding_hash, audience)` → explanation text |
| **Tone adaptation** | Adjusting language for traveler vs. agency | Cache by `(content_hash, tone_profile)` → adapted text |

### The Generalized Cache Protocol

Extend the existing `HybridDecisionEngine` pattern into a reusable protocol:

```python
class LLMCacheable(Protocol):
    """Any operation that can use cache → rule → LLM → cache-result."""

    @property
    def cache_namespace(self) -> str:
        """e.g., 'extraction', 'question_gen', 'suitability', 'proposal'"""
        ...

    def compute_cache_key(self, inputs: Dict[str, Any]) -> str:
        """Deterministic key from normalized inputs."""
        ...

    def try_rule(self, inputs: Dict[str, Any]) -> Optional[Any]:
        """Deterministic rule attempt. Returns None if no rule applies."""
        ...

    def format_llm_prompt(self, inputs: Dict[str, Any]) -> str:
        """Build prompt for LLM fallback."""
        ...

    def extract_from_llm_response(self, response: str) -> Any:
        """Parse structured output from LLM response."""
        ...

    def output_schema(self) -> Optional[Dict[str, Any]]:
        """JSON schema for structured output enforcement."""
        ...
```

### The Cache Lifecycle (How "Everything Improves")

```
1. First call → cache miss → rule attempt → (hit? cache & return) → LLM call → extract structured output → cache result
2. Second similar call → cache hit → return cached result (₹0, <1ms)
3. Agent overrides result → record_feedback(success=False) → success_rate drops
4. Multiple overrides → success_rate < 0.7 → cache entry evicted
5. New LLM call with updated context → better result → cache with fresh success_rate
6. Pattern stabilizes → promote to deterministic rule (human or automated)
```

**The key insight**: LLM calls are a **bootstrap mechanism**. They produce initial answers. Feedback refines them. Stable patterns graduate to rules. Over time, the system needs fewer LLM calls, not more.

### Promotion: Cache → Rule

When a cached decision has:
- `use_count > 20`
- `success_rate > 0.95`
- `feedback_count > 5`

It's a candidate for promotion to a deterministic rule. This can be:
- **Automated**: System generates a rule from the cached pattern
- **Manual**: Agency owner or system admin reviews and promotes
- **Semi-automated**: System suggests, human approves

```python
@dataclass
class PromotionCandidate:
    """A cached decision ready for promotion to a deterministic rule."""
    cached_decision: CachedDecision
    input_pattern: Dict[str, Any]  # generalized from cache key
    proposed_rule: str             # generated rule logic (for review)
    promotion_confidence: float
    reviewer_action: Optional[Literal["approve", "reject", "modify"]] = None
```

### Cost Tracking Per Touchpoint

Every LLM call must log:

```python
@dataclass
class LLMCallLog:
    """Audit trail for every LLM call — feeds cost tracking and cache optimization."""
    call_id: str
    namespace: str          # "extraction", "suitability", "question_gen"
    cache_key: str
    cache_hit: bool
    rule_hit: bool
    llm_called: bool
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_inr: float = 0.0
    latency_ms: int = 0
    result_cached: bool = False
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
```

This feeds:
- Per-namespace cost dashboards
- Cache hit rate optimization
- Rule promotion candidates
- Budget guardrails (monthly/per-request caps per `DISCOVERY_GAP_LLM_AI_INTEGRATION_2026-04-16.md` L246)

---

## Part 2: NB05 — Honest Golden-Path Demos

### V02 Definition
> `NB05`: Honest golden-path demos
> — `V02_GOVERNING_PRINCIPLES.md` L20

### What NB05 Actually Is

NB05 is NOT a runtime pipeline stage. It's a **demonstration and validation system** that proves the end-to-end pipeline works correctly on curated scenarios.

### Purpose
- Prove that `NB01 → NB02 → NB03` produces correct, traveler-safe output for known-good inputs
- Detect regressions when any pipeline component changes
- Serve as the "sales demo" — the scenarios you show when presenting the product
- Validate leakage protection (internal data never appears in traveler-facing output)

### What Exists Today
- `notebooks/05_golden_path.ipynb` — referenced in docs but not verified as current
- Golden path test checks for leakage (`TEST_GAP_ANALYSIS.md` L116, L300)
- E2E freeze pack tests (`tests/test_e2e_freeze_pack.py`) — 3 scenarios with full pipeline assertions

### What NB05 Needs for Full Production

**NB05 is the eval suite's curated "showcase" subset.** It should be a proper module, not just a notebook.

```python
# src/evals/golden_path/
#   __init__.py
#   scenarios.py          # curated golden-path scenario definitions
#   runner.py             # run all scenarios, assert correctness
#   leakage_checker.py    # verify no internal data in traveler output
#   report.py             # generate human-readable demo report
```

#### Golden Path Scenario Structure

```python
@dataclass
class GoldenPathScenario:
    """A curated end-to-end scenario with known-correct outcomes."""
    scenario_id: str
    name: str                           # "Singapore Family Trip — Happy Path"
    description: str
    input_text: str                     # raw freeform or structured input
    input_source: SourceEnvelope        # properly wrapped input

    # Expected outcomes at each stage
    expected_operating_mode: str
    expected_stage: str
    expected_decision_state: str
    expected_facts: Dict[str, Any]      # key facts that MUST be extracted
    expected_risks: List[str]           # risk flags that MUST be present
    expected_absent_risks: List[str]    # risk flags that MUST NOT be present

    # Leakage assertions
    traveler_output_must_not_contain: List[str]  # internal terms, hypothesis markers
    traveler_output_must_contain: List[str]      # key traveler-relevant info

    # Prompt quality assertions
    prompt_bundle_checks: Dict[str, Any]  # system_context present, constraints present, etc.

    # Tags for filtering
    tags: List[str] = field(default_factory=list)  # "family", "audit", "emergency", etc.
    difficulty: Literal["simple", "moderate", "complex"] = "moderate"
```

#### NB05 ↔ D4/D6 Connection

| D4/D6 Component | NB05 Role |
|-----------------|-----------|
| `ActivitySuitability` (D4) | Golden path scenarios include families — verify suitability flags appear correctly |
| `SuitabilityBundle` (D4) | Verify wasted spend detection shows up in demo scenarios |
| Audit rules (D6) | Audit-mode golden path scenarios — verify findings match expected |
| `StructuredRisk` | Verify risks appear in golden path output with correct severity |

#### NB05 ↔ LLM Cache Connection

Golden path scenarios are **ideal cache-warming candidates**. After running NB05:
- Every LLM call made during the golden path gets cached
- Next run uses cached results → deterministic, fast, no cost
- If a pipeline change causes cache miss → that's a regression signal

```python
def warm_cache_from_golden_paths(scenarios: List[GoldenPathScenario]) -> CacheWarmReport:
    """Run golden path scenarios and populate LLM cache with known-good results."""
    ...
```

---

## Part 3: NB06 — Honest Shadow-Mode Replay

### V02 Definition
> `NB06`: Honest shadow-mode replay
> — `V02_GOVERNING_PRINCIPLES.md` L21

### What NB06 Actually Is

NB06 is a **shadow testing system** that replays real production inputs through the pipeline and compares outputs — without affecting production behavior.

### Purpose
- Compare deterministic-only output vs. LLM-enhanced output (side-by-side)
- Detect quality regressions when pipeline components change
- Validate new rules/scorers/LLM prompt versions before deploying
- Build the training data for rule promotion (cache → rule graduation)
- Measure real-world accuracy before going live with new capabilities

### The Shadow Mode Architecture

```
Real Production Flow:
  Input → NB01 → NB02 → NB03 → Output (served to user)
                    ↓ (copy)
Shadow Flow:
  Same Input → NB01' → NB02' → NB03' → Shadow Output (logged, never served)

Comparison:
  Production Output vs. Shadow Output → Diff Report
```

### What NB06 Needs for Full Production

```python
# src/evals/shadow/
#   __init__.py
#   collector.py          # capture real inputs (anonymized)
#   replayer.py           # replay through shadow pipeline
#   comparator.py         # diff production vs. shadow outputs
#   report.py             # generate comparison reports
```

#### Shadow Run Structure

```python
@dataclass
class ShadowRun:
    """One shadow replay — production vs. experimental pipeline."""
    run_id: str
    input_envelope: SourceEnvelope      # the real input (anonymized if needed)
    production_config: PipelineConfig    # what ran in production
    shadow_config: PipelineConfig       # what's being tested

    # Outputs
    production_result: Optional[Dict[str, Any]] = None
    shadow_result: Optional[Dict[str, Any]] = None

    # Comparison
    diff: Optional[ShadowDiff] = None
    verdict: Optional[Literal["match", "improved", "regressed", "different_but_acceptable"]] = None

    # Metadata
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    tags: List[str] = field(default_factory=list)

@dataclass
class ShadowDiff:
    """Structured comparison between production and shadow outputs."""
    decision_state_match: bool
    operating_mode_match: bool
    risk_flags_added: List[str]       # in shadow but not production
    risk_flags_removed: List[str]     # in production but not shadow
    facts_changed: Dict[str, Any]     # facts that differ
    severity_changes: List[Dict[str, Any]]  # risk severity differences
    llm_calls_production: int
    llm_calls_shadow: int
    cost_production_inr: float
    cost_shadow_inr: float
    latency_production_ms: int
    latency_shadow_ms: int
```

#### NB06 ↔ D4/D6 Connection

| D4/D6 Component | NB06 Role |
|-----------------|-----------|
| New `SuitabilityScorer` (D4) | Shadow-test new scorer against production heuristic before deploying |
| New `AuditRule` (D6) | Shadow-test new audit rule — does it flag things production missed? |
| `AgencySuitabilityPolicy` changes | Shadow-test policy weight changes before applying to production |
| Manifest status promotion (D6) | `shadow` status = shadow mode is actively measuring this category |

#### NB06 ↔ LLM Cache Connection

Shadow mode is the **primary feedback loop for cache quality**:

```
1. Production serves cached result (fast, cheap)
2. Shadow runs LLM on same input (slow, costly, but offline)
3. Compare cached result vs. fresh LLM result
4. If they match → cache is still valid
5. If they diverge → flag for review:
   a. LLM got better → update cache
   b. Cache was wrong → evict + update
   c. Difference is acceptable → no action
```

This means shadow mode:
- **Validates cache freshness** without affecting production
- **Discovers cache staleness** before users hit it
- **Generates feedback** for `record_feedback()` on cached decisions

---

## Part 4: How Everything Connects

### The Full Learning Loop

```
                    ┌────────────────────────────────────────┐
                    │        PRODUCTION (NB01→NB02→NB03)      │
                    │                                          │
                    │  Cache hit? ──yes──→ Return cached       │
                    │      │                                    │
                    │      no                                   │
                    │      │                                    │
                    │  Rule hit? ──yes──→ Cache + Return        │
                    │      │                                    │
                    │      no                                   │
                    │      │                                    │
                    │  LLM call ──→ Extract structured ──→ Cache│
                    └──────┬──────────────────────┬────────────┘
                           │                      │
                    ┌──────▼──────┐         ┌─────▼──────┐
                    │   NB05      │         │   NB06     │
                    │ Golden Path │         │ Shadow Mode│
                    │             │         │            │
                    │ • Warm cache│         │ • Replay   │
                    │ • Prove     │         │ • Compare  │
                    │   correctness│        │ • Validate │
                    │ • Demo      │         │   cache    │
                    └──────┬──────┘         └─────┬──────┘
                           │                      │
                           └──────────┬───────────┘
                                      │
                              ┌───────▼────────┐
                              │   NB04 Eval    │
                              │                │
                              │ • Measure      │
                              │   accuracy     │
                              │ • Gate CI      │
                              │ • Track trends │
                              │ • Promote      │
                              │   cache→rule   │
                              └────────────────┘
```

### The Evolution Flywheel

1. **Day 1**: Heuristic rules handle common cases. LLM handles edge cases. Results get cached.
2. **Week 2**: Cache hit rate climbs. LLM costs drop. Shadow mode validates cache quality.
3. **Month 1**: High-success cached decisions get promoted to rules. LLM calls become rare for known patterns.
4. **Month 3**: New capabilities (suitability scoring, pacing analysis) start as LLM-assisted → get cached → graduate to rules.
5. **Month 6**: Agency-specific patterns emerge from cache data → become agency-configurable policy weights.
6. **Ongoing**: Every LLM call is an investment that reduces future LLM calls. The system gets cheaper and faster over time.

---

## Part 5: Module Layout (Additions to D4/D6 Layout)

```
src/decision/                     # ✅ EXISTS — extend, don't replace
  hybrid_engine.py                # Extend with LLMCacheable protocol
  cache_schema.py                 # Add PromotionCandidate, LLMCallLog
  cache_storage.py                # Add namespace support
  cache_key.py                    # No changes needed
  rules/                          # Add promoted rules here

src/evals/
  golden_path/                    # NB05
    __init__.py
    scenarios.py
    runner.py
    leakage_checker.py
    report.py
    cache_warmer.py               # Warm LLM cache from golden paths

  shadow/                         # NB06
    __init__.py
    collector.py
    replayer.py
    comparator.py
    cache_validator.py            # Compare cached vs. fresh LLM results
    report.py

  audit/                          # D6 (already specified)
    ...
```

### Migration Note
`src/decision/hybrid_engine.py` already does the hard work. Extensions:
1. Add `cache_namespace` support (currently flat, needs per-touchpoint namespaces)
2. Add `LLMCacheable` protocol so new touchpoints (D4 suitability, D6 explanation, NB03 questions) can plug in
3. Add `PromotionCandidate` tracking for cache → rule graduation
4. Add `LLMCallLog` for cost tracking per namespace

---

## Part 6: Guardrails for LLM Caching

| Risk | Guardrail |
|------|-----------|
| Stale cache serves outdated info | `is_valid(max_age_days=30)` already exists. Shadow mode validates freshness. |
| Cache pollution from bad LLM output | `success_rate` tracking + eviction at <0.7. Human/agent feedback loop via `record_feedback()`. |
| Cache key collisions (different inputs, same key) | `generate_cache_key` uses deterministic hashing of normalized inputs. Add collision detection via output comparison. |
| Promoted rules become wrong over time | Shadow mode continuously validates rules against LLM. Rules have maturity tags (`heuristic` vs `verified`). |
| LLM cost spirals during cold start | Per-request cost cap in `LLMConfig`. Monthly budget. Deterministic fallback always available. |
| Cache becomes a black box | Every cached entry has provenance (`source`, `llm_model_used`, `created_at`). Audit trail via `LLMCallLog`. |
| Agency-specific cached results leak to other agencies | Cache key includes agency context when multi-tenant. Per-agency cache namespaces. |

---

*This architecture makes every LLM call a compounding investment. NB05 proves the system works correctly. NB06 proves it keeps working correctly as it evolves. The cache converts expensive LLM insights into cheap deterministic knowledge. The feedback loop ensures everything improves.*
