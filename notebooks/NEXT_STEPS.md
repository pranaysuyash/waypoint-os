# Next Steps: Fixture-Driven Validation

**Date**: 2026-04-09
**Status**: Planned
**Prerequisites**: NB01, NB02, NB03 — all defined and tested

---

## Context

The pipeline spine is clean:

- **NB01**: Normalizes raw agency notes → CanonicalPacket
- **NB02**: Decides what's missing/blocked/branchable → DecisionResult
- **NB03**: Plans the next interaction → SessionStrategy + PromptBundle

Now we need to prove it works end-to-end against realistic data.

---

## Design Principle: Two Fixture Layers, Not One

We need **two fixture layers**, not one.

### Layer A: Raw-Input Fixtures (End-to-End)

```
raw note / structured input / hybrid input → NB01 → NB02 → NB03
```

- Tests the **real spine** — extraction + decision + planning
- Includes raw text, expected extracted fields, expected unknowns, expected contradictions, expected decision state, expected NB03 behavior

### Layer B: CanonicalPacket Fixtures (Policy-Only)

```
CanonicalPacket → NB02 → NB03
```

- Tests **decision logic in isolation** — easier to debug, faster to run
- Stress-tests blocker logic, contradiction classification, branch rules, tone/session planning, internal/external boundary

**Key rule**: Layer B fixtures are NOT a substitute for Layer A. They complement it.

---

## Task A1: Raw Fixture Set (10-12 fixtures)

### Why 10-12, not 20-30

- Enough coverage to expose real problems
- Small enough to finish and actually inspect
- The hard part is writing good expected outcomes, not generating bulk

### Suggested Spread

| Category                | Count | Examples                                                       |
| ----------------------- | ----- | -------------------------------------------------------------- |
| Clean / happy path      | 3     | Complete family booking, business trip, pilgrimages            |
| Messy / under-specified | 3     | Vague lead, WhatsApp dump, partial CRM entry                   |
| Hybrid conflict         | 2     | Old CRM + new call with changed details, multi-source mismatch |
| Contradiction-heavy     | 2     | Confused couple, budget impossibility                          |
| Branch-worthy ambiguity | 2     | "Andaman or Sri Lanka", "luxury wants + budget reality"        |

### Fixture Format

```python
{
    "fixture_id": str,
    "source_type": "freeform_text" | "structured_json" | "hybrid",
    "raw_input": str,              # The messy agency note
    "structured_input": dict,      # Optional (CRM data, form data)
    "expected": {
        "extracted_fields": {      # What NB01 should extract
            "origin_city": {"value": "Bangalore", "authority": "explicit_owner", "confidence": 0.9},
            ...
        },
        "expected_unknowns": List[str],
        "expected_contradictions": List[str],
        "nb02_decision_state": str,
        "nb02_hard_blockers": List[str],
        "nb03_behavior": str,      # Expected NB03 behavior summary
    }
}
```

### Where

- File: `data/fixtures/raw_fixtures.py`
- Format: Python file with fixture dicts + factory functions

---

## Task A2: CanonicalPacket Fixture Set (20-30 fixtures)

### Why More Fixtures Here

- Cheaper to build (no extraction expectations)
- Easier to target specific decision states and edge cases
- Useful for regression testing

### Coverage Requirements

| Decision State         | Count | Examples                                                                                                                                       |
| ---------------------- | ----- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| ASK_FOLLOWUP           | 8-10  | Vague lead, missing dates, missing destination, composition unknown, budget-only, origin-only, post-contradiction-ask, repeat-customer-partial |
| PROCEED_TRAVELER_SAFE  | 4-5   | Complete discovery, complete shortlist, complete proposal, last-minute-booker                                                                  |
| PROCEED_INTERNAL_DRAFT | 3-4   | Soft-blockers-only, low-confidence-complete, budget-stretch                                                                                    |
| BRANCH_OPTIONS         | 2-3   | Budget contradiction, destination ambiguity, pace conflict                                                                                     |
| STOP_NEEDS_REVIEW      | 2-3   | Date contradiction, visa crisis, impossible budget                                                                                             |

### Where

- File: `data/fixtures/packet_fixtures.py`
- Format: Python file with factory functions returning `CanonicalPacket` + expected outcomes

---

## Task B: Eval Runner (Two Modes)

### Mode 1: End-to-End

```
raw fixture → NB01 → NB02 → NB03
```

Checks:

1. Key extracted fields correct
2. Unknowns correct
3. Contradictions correct
4. Decision state correct
5. Top questions/branches sensible

### Mode 2: Policy-Only

```
CanonicalPacket fixture → NB02 → NB03
```

Checks:

1. Blocker logic correct
2. Contradiction routing correct
3. Branch generation correct
4. Confidence/tone behavior correct
5. Internal/external boundary correct (no leakage)

### Output

- Console summary: pass/fail count
- JSON report: `data/fixtures/eval_results.json`
- Per-fixture diff on failure: expected vs actual

### Where

- File: `notebooks/04_eval_runner.ipynb`
- Also runnable as script: `data/fixtures/run_eval.py`

---

## Task C: Golden Path Demo

### What

One **raw messy example**, narrated step by step:

```
1. Source intake (raw WhatsApp/email text)
2. Extracted packet (facts, hypotheses, unknowns)
3. Unknowns and contradictions flagged
4. Decision result (what to do next)
5. Session strategy (how to do it)
6. Prompt bundle (the actual text to send)
```

### Critical Rule

The golden path must start from **raw messy text**, not a hand-built CanonicalPacket. The point is proving the actual spine, not just the middle layers.

### Where

- File: `notebooks/05_golden_path.ipynb`

---

## Dependencies

```
Task A1 (Raw Fixtures)  ──┐
                           ├──→ Task B (Eval Runner, Mode 1)
Task A2 (Packet Fixtures) ─┤
                           ├──→ Task B (Eval Runner, Mode 2)
                           └──→ Task C (Golden Path Demo — uses one A1 fixture)
```

---

## Non-Goals (Explicitly Deferred)

- No supplier/vendor data integration
- No persona-specific strategy builders
- No LLM extraction improvements (fixtures test the extraction as-is)
- No voice orchestration
- No pricing/margin logic
- No tribal knowledge injection
- No UI polish

---

## Effort Estimate

Realistically **1-3 focused working sessions**:

- Session 1: Fixture taxonomy + first 10 raw fixtures + 15-20 packet fixtures
- Session 2: Eval runner (both modes) + initial run
- Session 3: Golden path demo + fix failures from eval

The hard part is **writing good expected outcomes**, not writing code.

---

## Success Criteria

1. 10-12 raw fixtures pass end-to-end eval
2. 20-30 packet fixtures pass policy-only eval
3. Golden path demo runs clean from raw text to prompt bundle
4. Internal vs external boundary is proven correct (no leakage)
5. Results are reproducible and auditable

---

## Status: v0.1 Spine Frozen

| Component                    | File                                          | Status             |
| ---------------------------- | --------------------------------------------- | ------------------ |
| NB01: Intake & Normalization | `notebooks/01_intake_and_normalization.ipynb` | Defined            |
| NB02: Gap & Decision         | `notebooks/02_gap_and_decision.ipynb`         | Defined + 81 tests |
| NB03: Session Strategy       | `notebooks/03_session_strategy.ipynb`         | Defined + 15 tests |
| Raw Fixtures (12)            | `data/fixtures/raw_fixtures.py`               | Complete           |
| Packet Fixtures (19)         | `data/fixtures/packet_fixtures.py`            | Complete           |
| Eval Runner (2 modes)        | `notebooks/04_eval_runner.ipynb`              | 31/31 pass         |
| Golden Path Demo             | `notebooks/05_golden_path.ipynb`              | Clean run          |

**All boundary checks pass. The spine is proven.**

---

## Shadow Mode — Ready

| Component            | File                                                           | Status          |
| -------------------- | -------------------------------------------------------------- | --------------- |
| Schema               | `data/shadow/SHADOW_MODE_SCHEMA.md`                            | Defined         |
| Input templates (10) | `data/shadow/inputs/shadow_001.json` through `shadow_010.json` | Ready for notes |
| Runner               | `notebooks/06_shadow_runner.ipynb`                             | Working         |
| Output dir           | `data/shadow/outputs/`                                         | Ready           |
| Evaluation dir       | `data/shadow/evaluations/`                                     | Ready           |

**To use:**

1. Paste real agency notes into `shadow_XXX.json` files (`raw_input` + `source_type`)
2. Run `notebooks/06_shadow_runner.ipynb` from project root
3. Review: fill `data/shadow/evaluations/shadow_XXX_eval.json`
4. Analyze: patterns → `Docs/SHADOW_MODE_REPORT.md`
