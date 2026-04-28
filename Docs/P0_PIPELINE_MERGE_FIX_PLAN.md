# P0 Fix Plan: Pipeline Data Destruction Bug

**Status:** BLOCKER — Must fix before Phase 3-6 deployment  
**Date:** 2026-04-28  
**Risk:** CRITICAL — Silent data loss in core extraction pipeline  
**Effort:** 3-4 hours (fix + test + verify)

---

## Problem Summary

The `ExtractionPacket.set_fact()` method **overwrites** extracted facts with no merge logic. When multiple text envelopes (customer message + agent notes) are processed sequentially, later empty extractions destroy earlier correct extractions.

### Evidence

**Test Scenario:** Singapore trip, 5 travelers, Feb 9-14, 2025

| Step | Input | Extraction | Result | Status |
|------|-------|-----------|--------|--------|
| 1 | Customer message: "Singapore, Feb 9-14, 5 people" | `destination=["Singapore"]` | ✅ Correct | ✅ |
| 2 | Agent notes: "Party: 6, nature parks" (no destination) | `destination=[]` | ❌ Empty | ❌ |
| **3** | **Pipeline applies step 2** | **`set_fact("destination", [])`** | **destination=[]** | **🔴 DESTROYED** |

Current code (`src/intake/packet_models.py:352`):
```python
def set_fact(self, field_name: str, slot: Slot) -> None:
    self.facts[field_name] = slot  # ← BLINDLY OVERWRITES
```

**Impact:** Any pipeline run with 2+ envelopes silently loses data. Operators cannot trust extraction. Feature is worse than useless.

---

## Root Cause Analysis

### Architectural Assumption (Wrong)
The pipeline was designed assuming each envelope is self-contained and complete. Each extraction is treated as a full replacement ("extraction 2 supersedes extraction 1").

### Reality
Customer messages and agent notes are **complementary**, not **redundant**. A complete trip extraction requires merging facts from multiple sources:
- Customer may mention destination + dates but not party size
- Agent notes may mention party size + budget but not destination
- Neither field should be destroyed by the absence of that field in the other source

### Why It Wasn't Caught Earlier
- Tests use single envelopes (customer message only, or agent notes only)
- Multi-envelope tests are missing
- There is no integration test replicating real-world intake (both sources)

---

## Fix Architecture

### Step 1: Replace `set_fact()` with `merge_fact()`

New method in `ExtractionPacket` that understands field types and merge semantics:

```python
# List fields that should be union-merged (deduplicated)
MERGE_UNION_FIELDS = {
    "destination_candidates",
    "interests", 
    "travel_dates",
    "accessibility_needs",
}

# Fields that should prefer non-empty (never overwrite populated with empty)
MERGE_PREFER_NONEMPTY_FIELDS = {
    "party_composition",  # agent notes provide detail, customer msg provides count
    "pace",              # both sources might mention
    "budget",            # explicit when stated
}

def merge_fact(self, field_name: str, new_slot: Slot) -> None:
    """Merge a fact, respecting multi-source extraction semantics.
    
    Rules:
    1. Union fields: combine values, deduplicate, keep all sources
    2. Prefer-nonempty fields: only overwrite if current is None/empty
    3. All fields: prefer explicit over inferred, source order respected
    """
    if new_slot.authority_level not in AuthorityLevel.FACT_LEVELS:
        raise ValueError(...)
    
    existing_slot = self.facts.get(field_name)
    
    # Rule 1: Union merge for list fields
    if field_name in MERGE_UNION_FIELDS:
        if existing_slot is None:
            self.facts[field_name] = new_slot
        else:
            existing_values = existing_slot.value or []
            new_values = new_slot.value or []
            merged = list(dict.fromkeys(existing_values + new_values))  # Union + dedup
            merged_slot = Slot(
                value=merged,
                authority_level=max(
                    existing_slot.authority_level,
                    new_slot.authority_level
                ) if hasattr(AuthorityLevel, '__gt__') else new_slot.authority_level,
                source=f"{existing_slot.source} + {new_slot.source}"
            )
            self.facts[field_name] = merged_slot
    
    # Rule 2: Prefer non-empty for scalar fields
    elif field_name in MERGE_PREFER_NONEMPTY_FIELDS:
        if existing_slot is None or not existing_slot.value:
            self.facts[field_name] = new_slot
        elif new_slot.value:
            # Both have values — use preference heuristic
            # For now: prefer more authoritative source
            if new_slot.authority_level >= existing_slot.authority_level:
                self.facts[field_name] = new_slot
    
    # Rule 3: Default (scalar fields, always overwrite)
    else:
        if new_slot.value is not None:
            self.facts[field_name] = new_slot
        # else: do NOT overwrite with None/empty
    
    self._emit_event("fact_merged", {
        "field_name": field_name,
        "value": self.facts[field_name].value,
        "merge_type": "union" if field_name in MERGE_UNION_FIELDS else "prefer_nonempty"
    })
```

### Step 2: Update ExtractionPipeline to Call `merge_fact()` Instead of `set_fact()`

File: `src/intake/orchestration.py` or extraction pipeline main

Change:
```python
# OLD (destroys data)
packet.set_fact("destination_candidates", extracted_destinations)

# NEW (preserves data)
packet.merge_fact("destination_candidates", extracted_destinations)
```

### Step 3: Add Comprehensive Tests

Create `tests/test_extraction_merge_semantics.py`:

```python
def test_multi_envelope_destination_preserved():
    """Destination from customer message is NOT destroyed by agent notes."""
    packet = ExtractionPacket()
    
    # Envelope 1: Customer message mentions Singapore
    customer_extraction = ExtractionResult(
        destination_candidates=["Singapore"],
        source="customer_message"
    )
    packet.merge_fact("destination_candidates", customer_extraction)
    assert packet.facts["destination_candidates"].value == ["Singapore"]
    
    # Envelope 2: Agent notes don't mention destination
    agent_extraction = ExtractionResult(
        destination_candidates=[],  # Empty!
        source="agent_notes"
    )
    packet.merge_fact("destination_candidates", agent_extraction)
    
    # BUG FIX VERIFICATION: Singapore should STILL be there
    assert packet.facts["destination_candidates"].value == ["Singapore"]
    print("✅ PASS: Multi-envelope merge preserves Singapore")


def test_multi_envelope_party_union():
    """Party composition unioned across sources."""
    packet = ExtractionPacket()
    
    # Customer: mentions 5 people (2 adults, 1 toddler, 2 seniors)
    customer_party = ["2 adults", "1 toddler", "2 seniors"]
    packet.merge_fact("party_composition", customer_party)
    
    # Agent notes: adds accessibility detail
    agent_party = ["accessible transport", "stroller-friendly"]
    packet.merge_fact("party_composition", agent_party)
    
    # All details preserved
    assert "2 adults" in packet.facts["party_composition"].value
    assert "stroller-friendly" in packet.facts["party_composition"].value
    print("✅ PASS: Party composition correctly unioned")


def test_singapore_real_scenario():
    """Replicate the exact failing scenario from the review."""
    packet = ExtractionPacket()
    
    # Customer message extraction
    customer_extraction = ExtractionResult(
        destination_candidates=["Singapore"],
        party_composition=["5 people"],
        travel_dates=["Feb 9-14, 2025"],
        pace="Relaxed",
        interests=["Universal Studios", "nature parks"]
    )
    for field, value in customer_extraction.items():
        packet.merge_fact(field, value)
    
    # Agent notes extraction (different fields, NO destination)
    agent_extraction = ExtractionResult(
        party_composition=["2 adults", "1 toddler aged 1.7y", "2 elderly parents"],
        accessibility_needs=["stroller-friendly", "accessible transport"],
        budget="Not discussed",
        follow_up="draft itinerary in 1-2 days"
    )
    for field, value in agent_extraction.items():
        packet.merge_fact(field, value)
    
    # VERIFY: All fields present, none destroyed
    assert packet.facts["destination_candidates"].value == ["Singapore"]
    assert "Universal Studios" in packet.facts["interests"].value
    assert "stroller-friendly" in packet.facts["accessibility_needs"].value
    assert len(packet.facts["party_composition"].value) >= 5
    
    print("✅ PASS: Singapore scenario extracts correctly (P0 FIX VERIFIED)")
```

---

## Fix Checklist

### Phase 1: Implement (30 min)
- [ ] Add `merge_fact()` method to `ExtractionPacket`
- [ ] Define `MERGE_UNION_FIELDS` and `MERGE_PREFER_NONEMPTY_FIELDS`
- [ ] Update extraction pipeline to call `merge_fact()` instead of `set_fact()`
- [ ] Update any direct `set_fact()` calls to use `merge_fact()`

### Phase 2: Test (45 min)
- [ ] Write `test_extraction_merge_semantics.py` with 3+ test cases
- [ ] Run tests — ALL must PASS
- [ ] Verify Singapore scenario test specifically passes
- [ ] Check no regressions in existing unit tests

### Phase 3: Integration Verify (30 min)
- [ ] Run full pipeline with Singapore test data (customer + agent notes)
- [ ] Confirm output JSON has all expected fields
- [ ] Check no empty values for fields that were extracted in either source
- [ ] Save result to `data/test_results/singapore_p0_fix_verification.json`

### Phase 4: Code Review & Merge (15 min)
- [ ] Self-review for clarity and correctness
- [ ] Merge to master
- [ ] Tag commit with `[P0-FIX]`

---

## Success Criteria

✅ **P0 Fix is Done When:**
1. `test_singapore_real_scenario()` passes (exact scenario from review)
2. All 3+ merge semantics tests pass
3. No regressions in Phase 1-2 baseline tests
4. Integration test with both envelopes shows all fields preserved
5. Code review approved

---

## Next Steps After P0 Fix

Once P0 is verified:
1. Fix P1 issues (user_id, analytics, tab routing) — 1 hour
2. Run full integration test with Singapore scenario
3. **Then** Phase 3-6 can be deployed (decision management depends on clean data)

---

## Deployment Timeline

| Task | Time | Blocker |
|------|------|---------|
| P0 fix implementation + test | 1.5 hours | 🔴 CRITICAL |
| P0 verification with real data | 30 min | 🔴 CRITICAL |
| P1 fixes (user_id, analytics) | 1 hour | 🟠 HIGH |
| Full regression test | 30 min | 🟠 HIGH |
| **Total before Phase 3-6 deploy** | **3.5 hours** | **BLOCKING** |

**Do NOT proceed with Phase 3-6 deployment until P0 is merged and verified.** The decision-management layer depends on reliable data input.

