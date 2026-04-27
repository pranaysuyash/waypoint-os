# Research Area: Multi-Tier Extraction Architecture

**Date**: 2026-04-27
**Status**: Designed but unimplemented (0% code)
**Priority**: P0 — blocks real-world usage
**Gap Register**: #07 (LLM/AI integration)
**Blocks**: NB01 gate escalates on every real input because regex-only extraction misses required MVB fields

---

## 1. The Problem (Live Evidence)

On 2026-04-27, a Singapore family trip scenario was submitted with rich, well-structured input:

> Family of 4, 2 adults + kids (8 and 12), want to visit Singapore for 5 days in July.
> Interested in Sentosa, Gardens by the Bay, and Universal Studios.
> Budget around SGD 8000 total.

The regex-only extraction pipeline produced:

| Field | Expected | Actual | Why |
|-------|----------|--------|-----|
| `destination_candidates` | `["Singapore"]` | `["Nov", "Caller", "Pace"]` | Regex matched capitalized words from agent notes, not the destination |
| `origin_city` | (any value) | MISSING | No pattern to extract origin from Indian agent notes |
| `date_window` | `"July, 5 days"` | MISSING | Date patterns don't handle "in July" + "5 days" together |
| `budget_raw_text` | `"SGD 8000"` | MISSING | Budget pattern doesn't handle SGD currency code |
| `trip_purpose` | `"leisure"` | MISSING | No intent classification pattern |
| `hard_constraints` | `["not rushed"]` | `["it rushed"]` | Pattern captures "it rushed" fragment, misses negation |

Result: 4 missing MVB fields → NB01 gate escalates → pipeline returns empty result → run hangs.

**Root cause**: The extraction pipeline is entirely regex-based. It was designed as Step 1 of a 3-step hybrid system but Steps 2 (NER/LLM) and 3 (Reconciler) were never built.

---

## 2. What Was Designed vs What Exists

### Designed (Phase B Merge Contract, 2026-04-15)

A 3-step pipeline documented in `Docs/PHASE_B_MERGE_CONTRACT_2026-04-15.md`:

```
Step 1: Deterministic Extraction (Regex)
    → CanonicalPacket with authority: EXPLICIT_USER/INFERRED
    → Handles 70-80% of common patterns (CURRENT STATE)

Step 2: Semantic Candidate Extraction (NER/LLM)
    → CandidatePacket with authority: SEMANTIC_CANDIDATE
    → Confidence scores, evidence spans, alternative interpretations
    → NOT BUILT

Step 3: Reconciler
    → Merged CanonicalPacket
    → Priority: explicit input > regex > semantic
    → NOT BUILT
```

### What Exists in Code

| Component | File | Status |
|-----------|------|--------|
| `ExtractionPipeline` | `src/intake/extractors.py:760` | Regex-only, 1352 lines |
| `model_client` parameter | `extractors.py:771` | Dead hook — accepted but never used |
| `CandidatePacket` | Defined in Phase B contract | Not in `src/` |
| `CandidateValue` / `AlternativeValue` | Defined in Phase B contract | Not in `src/` |
| `Reconciler` | Defined in Phase B contract | Not in `src/` |
| `SEMANTIC_CANDIDATE` authority | Defined in Phase B contract | Not in authority enum |
| NER integration (spaCy/Stanford) | Planned in Phase B.2 | Zero code |
| LLM extraction | Planned in Phase B.3 | Zero code |

### Supporting Architecture (Built, Ready)

| Component | File | Status |
|-----------|------|--------|
| `HybridDecisionEngine` | `src/decision/hybrid_engine.py` (828 lines) | Cache → Rule → LLM chain (LLM not connected) |
| `CachedDecision` / cache storage | `src/decision/cache_*.py` | Disk-backed JSON cache working |
| `PromptBundle` | `src/intake/strategy.py` | Built for LLM consumption, never consumed |
| Safety guardrails | `src/intake/safety.py` | Regex-based filtering, ready for LLM output |
| Leakage detection | `src/intake/safety.py` | Structural check, ready for LLM output |
| LLM cache design | `Docs/ARCHITECTURE_DECISION_LLM_CACHE_NB05_NB06_2026-04-16.md` | Complete spec |

---

## 3. Research Areas to Explore

### RA-EXTRACT-01: LLM Provider Abstraction

**Question**: How do we connect an LLM provider without coupling to a specific vendor?

**Specs exist**: `INTEGRATIONS_AND_DATA_SOURCES.md` declares `LLMProvider` Protocol with `complete()` and `stream_complete()`.

**Research tasks**:
- Evaluate OpenAI API vs Anthropic vs local (Ollama/llama.cpp) for extraction use case
- Cost analysis: per-field extraction cost at scale (1000 trips/day)
- Latency budget: how much extraction time is acceptable before user experience degrades?
- Fallback strategy: if LLM fails/times out, regex-only extraction proceeds
- PII handling: raw notes contain phone numbers, emails, personal details — what gets sent to LLM?

**Relevant docs**:
- `Docs/research/PII_AND_LLM_MODEL_RISK_RESEARCH_2026-04-26.md`
- `Docs/ARCHITECTURE_DECISION_LLM_CACHE_NB05_NB06_2026-04-16.md`
- `Docs/research/ROUTING_SPEC_COMPLEXITY_AWARE_LLM.md`

### RA-EXTRACT-02: Extraction Prompt Engineering

**Question**: What prompts reliably extract structured travel data from messy agent notes?

**Current state**: `PromptBundle` is generated (system_context, user_message, constraints) but never sent to an LLM.

**Research tasks**:
- Design extraction prompts per field group (destination, dates, party, budget, preferences)
- Test single-prompt extraction vs per-field extraction (quality vs cost tradeoff)
- Structured output enforcement (JSON mode, function calling, or prompt-only)
- Handling multilingual input (Hinglish agent notes, Arabic, etc.)
- Few-shot examples: build a corpus of 50+ annotated agent notes with ground-truth extraction

**Relevant docs**:
- `Docs/research/PROMPT_VERSIONING.md` (552-line prompt registry spec)
- `Docs/research/PRM_SPEC_GROUNDED_PROMPTING.md`
- `Docs/research/PROMPT_SPEC_OPERATIONAL_FEW_SHOT.md`

### RA-EXTRACT-03: Reconciliation Algorithm

**Question**: How do we merge regex extraction results with LLM candidates when they conflict?

**Spec exists**: Phase B contract defines priority: `explicit input > regex > semantic`.

**Research tasks**:
- Conflict resolution: regex says "Singapore" but LLM says "Bali" — who wins and why?
- Confidence calibration: regex confidence is heuristic (0.7-0.9), LLM confidence is different — how to normalize?
- Authority hierarchy: `EXPLICIT_USER` > `INFERRED` > `SEMANTIC_CANDIDATE` — is this always correct?
- Edge case: regex extracts nothing, LLM extracts wrong thing — when to leave a field as unknown?
- Evidence provenance: every field value must trace back to source text span

**Relevant docs**:
- `Docs/PHASE_B_MERGE_CONTRACT_2026-04-15.md` (lines 104-131)
- `Docs/SESSION_WRITEUP_DESTINATION_AMBIGUITY_2026-04-15.md` (line 388)

### RA-EXTRACT-04: Regex Pattern Quality (Immediate Fix)

**Question**: Can we fix the most egregious regex failures without LLM?

**Current failures**:
- Destination extraction matches random capitalized words from agent notes
- Negation handling broken ("not rushed" → "it rushed")
- Currency patterns miss SGD, AED, THB, etc.
- Date patterns don't handle relative dates + duration combos
- Origin city extraction missing entirely

**Research tasks**:
- Audit all 10+ regex patterns against 20 real-world agent note samples
- Fix destination extraction to use known-destination lookup + context awareness
- Add negation-aware extraction for constraint parsing
- Expand currency pattern to cover 20+ currencies
- Add date range + duration co-extraction pattern
- Add origin city extraction pattern (closest airport, city name lookup)

**Impact**: This is the fastest path to making the pipeline work for real input. Even a 50% improvement in regex quality would allow many inputs to pass NB01 without LLM.

### RA-EXTRACT-05: Evaluation Framework for Extraction Quality

**Question**: How do we measure extraction quality systematically?

**Spec exists**: `Docs/research/EVALUATION_FRAMEWORK.md` defines evaluation layers.

**Research tasks**:
- Build golden dataset: 50+ annotated agent notes with ground-truth canonical packets
- Per-field accuracy metrics: precision/recall/F1 for each MVB field
- End-to-end metric: what % of real inputs pass NB01 gate after extraction?
- A/B testing framework: regex-only vs regex+LLM extraction quality
- Regression testing: ensure new extraction patterns don't break existing passing inputs

**Relevant docs**:
- `Docs/research/EVALUATION_FRAMEWORK.md`
- `Docs/research/REAL_WORLD_VALIDATION.md`

### RA-EXTRACT-06: Suitability Tier 3 (LLM Contextual Scoring)

**Question**: When should Tier 3 LLM scoring activate for activity suitability?

**Current state**: Tier 1 (tag-predicate) and Tier 2 (tour-context) are implemented. Tier 3 is designed but not built.

**Research tasks**:
- When do Tiers 1+2 produce borderline results that warrant LLM escalation?
- What does a Tier 3 prompt look like? (activity + traveler profile + tour context → suitability score)
- Cost budget: how many Tier 3 calls per trip? Can we cache results?
- Tier 3 output format: just a score, or structured reasoning?

**Relevant docs**:
- `Docs/ARCHITECTURE_DECISION_D4_SUBDECISIONS_ADDENDUM_2026-04-18.md` (lines 109-154)

---

## 4. Implementation Priority

| Priority | Area | Rationale | Estimated Effort |
|----------|------|-----------|-----------------|
| **P0** | RA-EXTRACT-04: Fix regex patterns | Fastest path to working pipeline. Fixes live bugs. | 2-3 days |
| **P0** | RA-EXTRACT-01: LLM provider connection | Required for real extraction quality. Dead hook exists. | 3-5 days |
| **P1** | RA-EXTRACT-02: Extraction prompts | Needs LLM provider first. Core intelligence layer. | 5-7 days |
| **P1** | RA-EXTRACT-03: Reconciler | Needs both regex and LLM extraction working. | 3-5 days |
| **P2** | RA-EXTRACT-05: Evaluation framework | Needed for regression testing as extraction evolves. | 3-5 days |
| **P3** | RA-EXTRACT-06: Suitability Tier 3 | Enhances existing working system, not blocking. | 3-5 days |

---

## 5. Dependency Graph

```
RA-EXTRACT-04 (fix regex) ─── independent, do first
         │
RA-EXTRACT-01 (LLM provider) ─── independent of regex fixes
         │
RA-EXTRACT-02 (prompts) ─── depends on EXTRACT-01
         │
RA-EXTRACT-03 (reconciler) ─── depends on EXTRACT-01 + EXTRACT-02
         │
RA-EXTRACT-05 (evaluation) ─── parallel with EXTRACT-02, feeds all
         │
RA-EXTRACT-06 (suitability T3) ─── independent, can start anytime
```

---

## 6. Related Documentation

| Document | Location | Relationship |
|----------|----------|-------------|
| Phase B Merge Contract | `Docs/PHASE_B_MERGE_CONTRACT_2026-04-15.md` | Primary architecture spec for 3-step pipeline |
| LLM/AI Integration Gap | `Docs/DISCOVERY_GAP_LLM_AI_INTEGRATION_2026-04-16.md` | Comprehensive gap analysis |
| D4 Suitability Subdecisions | `Docs/ARCHITECTURE_DECISION_D4_SUBDECISIONS_ADDENDUM_2026-04-18.md` | Tier 3 LLM scoring spec |
| LLM Cache Architecture | `Docs/ARCHITECTURE_DECISION_LLM_CACHE_NB05_NB06_2026-04-16.md` | Cache → Rule → LLM chain spec |
| Frozen Spine Status | `Docs/FROZEN_SPINE_STATUS.md` | Honest status: "regex-only, not production-grade NLP" |
| Prompt Versioning | `Docs/research/PROMPT_VERSIONING.md` | Prompt registry spec |
| PII/LLM Risk | `Docs/research/PII_AND_LLM_MODEL_RISK_RESEARCH_2026-04-26.md` | PII handling in extraction |
| Hybrid Engine | `src/decision/hybrid_engine.py` | Existing cache → rule → LLM infrastructure |
| Extraction Pipeline | `src/intake/extractors.py` | Current regex-only implementation |
