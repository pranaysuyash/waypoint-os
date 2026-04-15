# Phase B: Hybrid Extraction Merge Contract

**Date**: 2026-04-15
**Status**: Design specification (not yet implemented)
**Version**: 1.0

---

## Purpose

Define the architecture for integrating NER/LLM-based semantic extraction with the existing deterministic regex-based extraction pipeline. This contract governs Phase B of the spine hardening plan.

## Problem Statement

**Current State (Phase A - Complete)**
- Regex-based extraction provides deterministic, fast results
- Handles 70-80% of common patterns (destinations, dates, party composition)
- Struggles with:
  - Complex semantic expressions: "somewhere warm with good beaches near Bangalore"
  - Context-dependent intent: "looking for a relaxing family trip"
  - Implicit preferences: "not too expensive but not cheap either"

**Target State (Phase B)**
- Hybrid extraction: deterministic parser + semantic candidate suggestions
- Maintain regex as baseline/fallback (guaranteed floor)
- Add NER/LLM as enhancement layer (ceiling expansion)
- Preserve backward compatibility and auditability

---

## Architecture

### Three-Step Pipeline

```
Input: Raw traveler text
    │
    ├── Step 1: Deterministic Extraction (Regex)
    │       └── CanonicalPacket with authority: EXPLICIT_USER/INFERRED
    │
    ├── Step 2: Semantic Candidate Extraction (NER/LLM)
    │       └── CandidatePacket with authority: SEMANTIC_CANDIDATE
    │           - Confidence scores
    │           - Evidence spans
    │           - Alternative interpretations
    │
    └── Step 3: Reconciler
            └── Merged CanonicalPacket
                - Truth object with provenance
                - Priority: explicit input > regex > semantic
```

### Step 1: Deterministic Extraction

**Role**: Fast, reliable baseline extraction
**Technology**: Current regex patterns in `src/intake/extractors.py`
**Output**: `CanonicalPacket` with fields populated where patterns match
**Authority Level**: 
- `EXPLICIT_USER` for direct matches
- `INFERRED` for derived/computed values

**Guarantees**:
- O(1) to O(n) complexity per field
- No hallucination (only extracts what matches)
- Always produces results (may be empty)

### Step 2: Semantic Candidate Extraction

**Role**: Extract meaning from unstructured/nuanced text
**Technology**: NER + optional LLM (schema-constrained)
**Output**: `CandidatePacket` with suggestions
**Authority Level**: `SEMANTIC_CANDIDATE`

**Structure**:
```python
@dataclass
class CandidatePacket:
    """Semantic extraction suggestions with provenance."""
    
    # Each field has confidence and alternatives
    destination_candidates: List[CandidateValue]
    budget_range: Optional[CandidateValue]
    trip_intent: Optional[CandidateValue]
    
@dataclass
class CandidateValue:
    value: Any
    confidence: float  # 0.0 - 1.0
    evidence_span: str  # "looking for a relaxing family trip"
    alternatives: List[AlternativeValue]  # Other possible interpretations
    
@dataclass
class AlternativeValue:
    value: Any
    confidence: float
    reason: str  # Why this is an alternative
```

**Example**:
- Input: "somewhere warm with good beaches near Bangalore"
- Regex: `destination_candidates=[]` (no match)
- NER: `CandidateValue("Goa", 0.7, "warm beaches, near Bangalore region", alternatives=[("Kerala", 0.5), ...])`

### Step 3: Reconciler

**Role**: Merge deterministic and semantic results into canonical truth
**Technology**: Rule-based merger with confidence thresholds
**Output**: Final `CanonicalPacket`

**Priority Rules**:
1. **Explicit structured input** (highest) — always wins
2. **Regex extraction with fact authority** — baseline truth
3. **Semantic candidates with high confidence (>0.8)** — add if regex empty
4. **Semantic candidates with medium confidence (0.5-0.8)** — suggest as hypothesis
5. **Low confidence (<0.5)** — ignore or add as ambiguity

**Merge Strategies per Field**:

| Field | Regex Result | Semantic Result | Action |
|-------|-------------|-------------------|--------|
| destination | `["Singapore"]` | `["Singapore"]` (0.9) | Keep regex, semantic confirms |
| destination | `[]` | `["Goa"]` (0.8) | Add semantic as hypothesis |
| budget | `200000` | `250000` (0.6) | Keep regex, flag ambiguity |
| dates | `"March 2026"` | `"April 2026"` (0.7) | Keep regex, semantic contradicts → flag |
| intent | (not extracted) | `"family leisure"` (0.8) | Add as derived signal |

**Conflict Resolution**:
- Regex value vs semantic value: Keep regex unless semantic has >0.9 confidence
- Regex empty, semantic suggests: Add as hypothesis with semantic authority
- Both disagree: Flag contradiction, keep regex (conservative)

---

## Implementation Phases

### Phase B.1: Infrastructure (Week 1)

1. **Define CandidatePacket schema** — dataclasses, validation
2. **Create semantic extraction interface** — abstract base class
3. **Implement null/stub semantic extractor** — returns empty candidates
4. **Build reconciler** — merge logic with configurable thresholds

### Phase B.2: NER Integration (Week 2-3)

1. **Select NER library** — spaCy, Stanza, or domain-specific
2. **Train/fine-tune on travel domain** — destinations, dates, budgets
3. **Implement NER extractor** — wraps NER library
4. **Eval suite** — compare NER vs regex on gold test set

### Phase B.3: LLM Integration (Optional, Week 4-6)

1. **Design schema-constrained prompts** — "Extract these fields from text..."
2. **Implement LLM extractor** — OpenAI, Anthropic, or local
3. **Add fallback chain** — NER first, LLM if NER empty
4. **Cost monitoring** — track per-request cost

### Phase B.4: Evaluation & Rollout (Week 7-8)

1. **A/B evaluation** — compare hybrid vs regex-only on held-out data
2. **Confidence threshold tuning** — optimize merge rules
3. **Gradual rollout** — feature flag, monitor telemetry
4. **Documentation** — operator guidance on semantic candidates

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         RAW INPUT                               │
│  "Planning a family trip to somewhere warm near Bangalore       │
│   for 4 people, budget around 2L, can stretch to 2.5L,          │
│   flexible dates in March or April"                             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 1: DETERMINISTIC EXTRACTION (Regex)                       │
│                                                                 │
│  destination_candidates: []  ← no direct match                  │
│  budget_min: 200000  ← "2L" extracted                           │
│  budget_soft_ceiling: 250000  ← "stretch to 2.5L"              │
│  party_size: 4  ← "4 people"                                   │
│  date_window: "March or April"  ← extracted                   │
│  trip_purpose: (not extracted)                                  │
│                                                                 │
│  Authority: EXPLICIT_USER                                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 2: SEMANTIC CANDIDATE EXTRACTION (NER/LLM)              │
│                                                                 │
│  destination_candidates: [                                    │
│    CandidateValue("Goa", 0.75, "warm beaches, near Bangalore") │
│    CandidateValue("Kerala", 0.60, "warm, family-friendly")   │
│  ]                                                              │
│  trip_intent: CandidateValue("family leisure", 0.85, "family   │
│               trip, relaxing destination")                     │
│  budget_flexibility: CandidateValue("stretchable", 0.90,     │
│                      "can stretch to 2.5L")                     │
│                                                                 │
│  Authority: SEMANTIC_CANDIDATE                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 3: RECONCILER                                            │
│                                                                 │
│  destination_candidates: []  ← regex empty                     │
│    → Add semantic top candidate as hypothesis:                   │
│       hypotheses["destination_candidates"] =                    │
│         Slot("Goa", 0.75, SOFT_HYPOTHESIS)                       │
│                                                                 │
│  budget_min: 200000  ← regex present, keep                      │
│  budget_soft_ceiling: 250000  ← regex present, keep             │
│                                                                 │
│  trip_purpose: (not in regex)                                   │
│    → Add semantic as derived signal:                             │
│       derived_signals["trip_purpose"] =                        │
│         Slot("family leisure", 0.85, DERIVED_SIGNAL)             │
│                                                                 │
│  Final Authority Mix:                                           │
│  - facts: budget_min, budget_soft_ceiling, party_size, dates  │
│  - hypotheses: destination_candidates                          │
│  - derived_signals: trip_purpose                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Telemetry & Observability

**Metrics to Track**:

| Metric | Purpose |
|--------|---------|
| `semantic.candidate_count` | Avg candidates per extraction |
| `semantic.regex_agreement` | % where semantic matches regex |
| `semantic.regex_gap` | % where regex empty, semantic found |
| `semantic.regex_conflict` | % where semantic contradicts regex |
| `semantic.confidence_distribution` | Histogram of confidence scores |
| `merge.decisions` | Count of merge rule invocations |
| `merge.semantic_adopted` | % of semantic candidates kept |

**Debugging**:
- Full candidate packet logged at debug level
- Merge decisions traceable per field
- A/B test capability (route % traffic to semantic)

---

## Backward Compatibility

**Guarantees**:
- Regex pipeline unchanged and always runs first
- Existing tests pass without modification
- Semantic layer can be disabled (feature flag)
- API contract unchanged — extra fields in hypotheses/derived_signals

**Migration Path**:
1. Deploy reconciler with null semantic extractor (no-op)
2. Enable semantic extractor in shadow mode (log only)
3. Gradual rollout: 1% → 10% → 50% → 100%
4. Monitor metrics, tune thresholds
5. Full production deployment

---

## Open Questions

1. **NER Library Choice**: spaCy (fast, local), Stanza (accurate), or train custom?
2. **LLM Cost Budget**: What's acceptable cost per request? ($0.01? $0.001?)
3. **Confidence Threshold**: Is 0.8 the right cutoff, or field-dependent?
4. **Fallback Chain**: NER → LLM → ??? What if both fail?
5. **Training Data**: Do we have labeled data for NER fine-tuning?

---

## References

- `src/intake/extractors.py` — Current regex extraction
- `src/intake/packet_models.py` — Data model
- `SPINE_HARDENING_PLAN_STAGE_2_2026-04-15.md` — This work's origin
- `FROZEN_SPINE_STATUS.md` — Post-freeze rules (Phase A/B separation)