# Contract Challenge Note: NB01 v0.2 Implementation

**Date**: 2026-04-12
**Method**: Cross-checked schema, NB01 spec, NB02 spec, NB03 spec, governing principles for contradictions and implementation traps.

---

## Contradictions Found

### 1. `resolved_destination` is described but not in schema

The NB01 spec and NB02 spec both describe `resolved_destination` as the downstream planning target. But it is not in the schema's `FactsMap`. It IS needed for shortlist/proposal/booking stages.

**Decision**: Add `resolved_destination` to the schema's FactsMap now. It is set by NB02 (after traveler confirms), consumed by NB03 for proposal generation. NB01 never sets it, but the schema must define it.

### 2. Later-stage fields missing from schema

NB02 uses `selected_itinerary` (proposal stage hard blocker) and `payment_method` (booking stage hard blocker). Neither is in the schema's FactsMap.

**Decision**: Add both to schema FactsMap now. They are real fields the pipeline will need.

### 3. Schema validation is too loose on structured values

The schema defines `owner_constraints`, `sub_groups`, `passport_status`, and `visa_status` all as generic `FieldSlot` with unconstrained `value: {}`. The Python dataclasses define them structurally, but the JSON schema doesn't enforce the shape.

**Decision**: This is a known limitation of JSON Schema with dataclass payloads. The schema-level enforcement will be weak for these fields. The Python dataclasses + tests are the real enforcement mechanism. Documented, not blocking.

### 4. NB03 sanitization example uses wrong field name

The NB03 spec example code checks `packet.facts.get("owner_notes")` but the locked schema uses `agency_notes`.

**Decision**: Fix in NB03 spec. Not an NB01 concern.

### 5. NB03 spec treats `sub_groups` values as dicts, not SubGroup

The dynamic risk-generation example accesses `g.get("budget_share", 0)` on SubGroup objects. If SubGroup is a dataclass, access should be `g.budget_share`.

**Decision**: Fix in NB03 spec. Not an NB01 concern.

---

## Implementation Traps

### 1. Mock extraction that looks real

The current NB01 uses keyword-matching mock LLM. The v0.2 spec dramatically expands the field surface (30+ fact fields). A naive upgrade would be to add more keyword checks — which would feel like capability but be just pattern matching.

**Mitigation**: The 15 tests use realistic input text. The extraction must actually parse the text structure (regex patterns for budget, dates, composition) to pass them. Not an LLM, but not keyword matching either. Honest regex-based extraction.

### 2. Stubbed derived signals that look authoritative

`sourcing_path`, `estimated_minimum_cost`, `budget_feasibility`, `booking_readiness` are all derived signals with no real data backing them yet.

**Mitigation**: Every derived signal carries a `maturity` tag in its Slot notes: `stub`, `heuristic`, or `verified`. NB02/NB03 can check maturity before relying on the signal.

### 3. Test fixtures that pre-construct packets instead of testing extraction

The existing test suite constructs CanonicalPacket objects directly, bypassing extraction entirely.

**Mitigation**: The 15 NB01 tests all exercise the extraction pipeline (`ExtractionPipeline.extract()`), not packet construction.

### 4. Date-relative tests that break

The urgency test must not use a hardcoded date like "2026-03-15". It must compute relative to `datetime.now()`.

**Mitigation**: Test creates `date_end = today + 5 days` dynamically.

---

## Recommended Structural Change

**Move core NB01 logic into importable Python modules under `src/travel_agent/`**, with the notebook as a thin demo wrapper.

**Why**:
- Tests run against real imports, not notebook cell state
- Clearer boundary between schema definition, extraction, normalization, and validation
- The existing `src/` directory is empty scaffolding — no conflict
- Does NOT mean productionizing (no FastAPI, no DB, no auth)

**Module layout**:
```
src/travel_agent/
    __init__.py
    packet_models.py      # CanonicalPacket, Slot, EvidenceRef, Ambiguity, OwnerConstraint, SubGroup
    normalizer.py          # Normalizer with ambiguity detection, budget/date parsing
    extractors.py          # ExtractionPipeline with pattern-based extraction
    validation.py          # validate_packet + PacketValidationReport
```

**What the notebook becomes**: Import modules, run one clean demo extraction, show validation report. No re-embedding of logic.

---

## Verdict

The contracts are coherent enough to implement. The 5 contradictions above are either trivial to fix (add fields to schema) or fix in other notebooks. The 4 implementation traps have clear mitigations.

**Proceed to tests first, then implementation.**
