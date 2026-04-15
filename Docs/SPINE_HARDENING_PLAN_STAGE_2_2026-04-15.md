# Spine Hardening Plan: Stage 2 (Post-Review)

**Date**: 2026-04-15
**Status**: Planning
**Scope**: Broad spine-hardening pass (items 2-8 from todo list)

---

## Overview

Following the external review of the destination-ambiguity fixes, this plan implements the remaining spine-hardening items as a **coordinated pass** rather than isolated tickets.

**Review verdict**: All 5 bugs were correctly identified and fixed. The layer-ownership correction (NB01 captures, NB02 enforces, NB03 presents) is correct. Now we need to complete the broader spine integrity work.

---

## Items to Implement

### 1. Stage-Aware Destination-Vagueness Routing ✅ DECISION: IMPLEMENT

**Current**: `value_vague` on `destination_candidates` is flat `blocking` severity.

**Target**: Stage-escalated severity:
- **discovery**: `advisory` — vague destination can support `ASK_FOLLOWUP` or `BRANCH_OPTIONS` (traveler exploring)
- **shortlist/proposal/booking**: `blocking` — must have resolved destination to proceed

**Why**: A traveler saying "maybe Singapore" at discovery is exploring; the same statement at proposal is a hard blocker.

**Files**: `src/intake/decision.py:AMBIGUITY_SEVERITY`, `classify_ambiguity_severity()`

**Test**: Add `test_stage_aware_destination_vagueness` — discovery=advisory, shortlist+=blocking.

---

### 2. Budget-Stretch Preservation ✅ DECISION: IMPLEMENT

**Current**: `budget_stretch_present` ambiguity detected, but stretch amount and semantics lost in question generation.

**Target**: Two-case handling:

**Case A**: "2L, can stretch"
- `budget_min = 200000`
- `budget_flexibility = stretch`
- NO invented max
- Question: "What's the absolute upper limit?"

**Case B**: "2L, can stretch to 2.5L"
- `budget_min = 200000`
- `budget_soft_ceiling = 250000` (new field)
- `budget_flexibility = stretch`
- Question: "You mentioned 2L with flexibility up to 2.5L — is that the hard limit?"

**Files**: 
- `src/intake/extractors.py`: Parse stretch amount from text
- `src/intake/packet_models.py`: Add `budget_soft_ceiling` to facts
- `src/intake/decision.py`: Generate stretch-aware questions

**Test**: `test_budget_stretch_preserved_in_question` for both cases.

---

### 3. Contradiction Source Attribution ✅ DECISION: IMPLEMENT

**Current**: Contradiction has flat `sources: ["env1", "env2"]` list.

**Target**: Per-value source attribution:
```python
{
    "field_name": "budget",
    "values": [
        {"value": "3L", "source": "email", "authority": "explicit_user", "timestamp": "..."},
        {"value": "4L", "source": "whatsapp", "authority": "explicit_user", "timestamp": "..."}
    ]
}
```

**Why**: Enables reasoning about authority, recency, owner-vs-traveler disagreements. Critical for owner-review and audit modes.

**Files**: 
- `src/intake/packet_models.py`: Update `Contradiction` dataclass
- `src/intake/decision.py`: `add_contradiction()` signature change
- `src/intake/extractors.py`: Pass source info when creating contradictions

**Backward compatibility**: Keep flat `sources` as convenience property during transition.

**Test**: `test_contradiction_per_value_sources`.

---

### 4. Geography False Positives Audit ✅ DECISION: IMPLEMENT

**Current**: "We" was extracted as destination (false positive). Stop-word filter added, but underlying `is_known_destination()` may have issues.

**Target**: 
1. Audit `is_known_destination()` for false positives
2. Add adversarial geography test pack
3. Tighten plausibility filters

**Test pack**:
- Pronouns: We, I, My, Our (should be filtered)
- Common words: The, This, That (should be filtered)
- Month names: January, March (should NOT be destinations)
- Business names: ABC Travels (should NOT match unless in DB)
- Ambiguous tokens: "US" (country vs pronoun), "Indian" (nationality vs city)

**Files**: `src/intake/geography.py`, `tests/test_geography_edge_cases.py`

---

### 5. Central Hedge Lexicon ⚠️ DEFER to Phase B

**Review decision**: Do not grow regex zoo. Centralize hedging patterns, but move to Phase B semantic extraction.

**Rationale**: "Sort of X", "X probably", "X I guess", "not sure but X" are context-dependent. Better handled by NER/span layer than more regex.

**Action**: Document current hedging patterns in `HEDGE_PATTERNS.md` for Phase B reference. No code changes.

---

### 6. NB02 Telemetry ✅ DECISION: IMPLEMENT

**Target**: Emit telemetry when NB02 synthesizes ambiguity that NB01 missed.

**Why**: Measurable upstream extraction-quality signal. Helps identify systematic NB01 gaps.

**Implementation**:
```python
# In _synthesize_destination_ambiguity()
if synthesized:
    emit_telemetry("nb02.ambiguity_synthesis", {
        "field": "destination_candidates",
        "reason": "multi_value_without_ambiguity",
        "stage": packet.stage,
        "candidates": dest_candidates
    })
```

**Files**: `src/intake/decision.py`, new `src/intake/telemetry.py`

---

### 7. Phase B Merge Contract ✅ DECISION: DOCUMENT

**Target**: Document semantic-candidate → reconciler → canonical-packet architecture.

**Architecture**:
```
Source text
    ├── Step 1: Deterministic extraction (regex, current pipeline)
    │       → CanonicalPacket (authority: EXPLICIT_USER / INFERRED)
    ├── Step 2: Semantic candidate extraction (NER / LLM)
    │       → CandidatePacket (authority: SEMANTIC_CANDIDATE)
    └── Step 3: Reconciler
            → Merged CanonicalPacket (truth object, provenance preserved)
```

**Priority**: explicit structured input > regex extraction > semantic candidate

**Files**: `Docs/PHASE_B_MERGE_CONTRACT.md`

---

### 8. Session Writeup Update ⏳ PENDING

After all implementations, update `SESSION_WRITEUP_DESTINATION_AMBIGUITY_2026-04-15.md` with:
- Decisions taken
- What was implemented vs deferred
- Link to ADR-002 (already exists)

---

## Execution Order

**Block 1: Data Model Changes** (foundation, must be first)
1. Contradiction source attribution (packet_models.py change)
2. Budget soft ceiling field (packet_models.py change)

**Block 2: Decision Engine Enhancements**
3. Stage-aware ambiguity severity (decision.py)
4. Budget-stretch question generation (decision.py)
5. NB02 telemetry (decision.py + telemetry.py)

**Block 3: Extraction Improvements**
6. Budget stretch parsing (extractors.py)
7. Geography false positives (geography.py + tests)

**Block 4: Documentation**
8. Phase B merge contract (new doc)
9. Session writeup update

**Block 5: Verification**
10. Full test suite run
11. Regression test suite run

---

## Testing Strategy

- Unit tests for each modified function
- Integration tests for full pipeline paths
- Regression tests for previously fixed bugs
- Edge case tests for new functionality

---

## Estimated Scope

| Block | Files | Lines | Risk |
|-------|-------|-------|------|
| 1 | 2 | ~100 | Low (additive data model) |
| 2 | 3 | ~200 | Medium (decision logic) |
| 3 | 2 | ~150 | Medium (extraction changes) |
| 4 | 2 | ~100 | Low (documentation) |
| 5 | — | — | Low (verification) |

**Total**: ~550 lines, 9 files, 11 new tests.

**Completeness**: 9/10 — full edge case coverage, telemetry, documentation.