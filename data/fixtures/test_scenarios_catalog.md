# Test Scenarios Catalog

**Project**: travel-agency-agent  
**System**: Notebook 02 Gap & Decision Pipeline  
**Total Scenarios**: 30  
**Last Updated**: 2026-04-09

---

## Scenario Categories

| Category | Count | Description |
|----------|-------|-------------|
| **Basic Flows** | 6 | Empty, complete, hypothesis-only, derived-only, soft-blockers |
| **Contradictions** | 5 | Date, budget, destination, traveler count, origin |
| **Authority Tests** | 5 | Manual override, explicit owner vs imported, derived vs hypothesis |
| **Stage Progression** | 4 | Discovery → Shortlist → Proposal → Booking |
| **Edge Cases** | 5 | Nulls, empty strings, malformed data, duplicates |
| **Complex Hybrid** | 5 | Multi-source, cross-layer conflicts, normalization |

---

## Category A: Basic Flows (6 scenarios)

### A1: Empty Packet
**ID**: `basic_empty`  
**Purpose**: Baseline - no data at all  
**Expected**: ASK_FOLLOWUP, 4 hard blockers (discovery)  
**Packet State**: Empty facts, empty hypotheses, empty derived_signals

### A2: Complete Packet - Discovery Stage
**ID**: `basic_complete_discovery`  
**Purpose**: All discovery fields filled with facts  
**Expected**: PROCEED_TRAVELER_SAFE  
**Fields**: destination_city, origin_city, travel_dates, traveler_count, budget_range, trip_purpose, traveler_preferences  
**Authority**: All explicit_user or explicit_owner

### A3: Hypothesis-Only Packet
**ID**: `basic_hypothesis_only`  
**Purpose**: Hypotheses do NOT fill blockers  
**Expected**: ASK_FOLLOWUP, 3 hard blockers remain  
**Structure**: 1 fact (origin), 3 hypotheses (destination, dates, count)

### A4: Derived Signal Fills Blocker
**ID**: `basic_derived_fills`  
**Purpose**: Derived signals CAN fill hard blockers  
**Expected**: PROCEED_INTERNAL_DRAFT (soft blockers remain)  
**Structure**: 3 facts + 1 derived_signal (destination)

### A5: Soft Blockers Only
**ID**: `basic_soft_only`  
**Purpose**: No hard blockers, only soft remain  
**Expected**: PROCEED_INTERNAL_DRAFT  
**Structure**: All 4 hard blockers filled, soft blockers empty

### A6: Minimum Viable Traveler-Safe
**ID**: `basic_minimal_safe`  
**Purpose**: Exactly at confidence threshold  
**Expected**: PROCEED_TRAVELER_SAFE (or INTERNAL_DRAFT depending on threshold)  
**Structure**: All hard blockers filled with low-confidence facts

---

## Category B: Contradictions (5 scenarios)

### B1: Date Contradiction - Critical
**ID**: `contradiction_date_critical`  
**Purpose**: Date conflict → STOP_NEEDS_REVIEW  
**Expected**: STOP_NEEDS_REVIEW  
**Conflict**: travel_dates = ["2026-03-15", "2026-04-01"] from different sources

### B2: Budget Contradiction - Branch Options
**ID**: `contradiction_budget_branch`  
**Purpose**: Budget conflict → BRANCH_OPTIONS  
**Expected**: BRANCH_OPTIONS  
**Conflict**: budget_range = ["budget", "premium"] from different sources

### B3: Destination Contradiction - Ask Followup
**ID**: `contradiction_destination_ask`  
**Purpose**: Destination conflict → ASK_FOLLOWUP  
**Expected**: ASK_FOLLOWUP  
**Conflict**: destination_city = ["Singapore", "Thailand"]

### B4: Traveler Count Contradiction
**ID**: `contradiction_count_ask`  
**Purpose**: Count mismatch → ASK_FOLLOWUP  
**Expected**: ASK_FOLLOWUP  
**Conflict**: traveler_count = [3, 5] from different sources

### B5: Origin Contradiction
**ID**: `contradiction_origin_ask`  
**Purpose**: Origin mismatch → ASK_FOLLOWUP  
**Expected**: ASK_FOLLOWUP  
**Conflict**: origin_city = ["Bangalore", "Mumbai"]

---

## Category C: Authority Tests (5 scenarios)

### C1: Manual Override Wins
**ID**: `authority_manual_override`  
**Purpose**: Manual override has highest authority  
**Expected**: PROCEED_TRAVELER_SAFE (manual values used)  
**Structure**: Facts with manual_override authority

### C2: Explicit Owner vs Imported Structured
**ID**: `authority_owner_vs_imported`  
**Purpose**: imported_structured > explicit_owner  
**Expected**: Uses imported value per policy  
**Conflict**: Same field, owner says "Bangalore", CRM says "Mumbai"

### C3: Derived Signal vs Hypothesis
**ID**: `authority_derived_vs_hypothesis`  
**Purpose**: derived_signal fills blocker, hypothesis doesn't  
**Expected**: ASK_FOLLOWUP (only 1 of 3 blockers filled by derived)  
**Structure**: 2 facts + 1 derived + 2 hypotheses

### C4: Explicit User vs All
**ID**: `authority_explicit_user_high`  
**Purpose**: explicit_user is near-highest authority  
**Expected**: PROCEED_TRAVELER_SAFE  
**Structure**: All fields explicit_user

### C5: Unknown Authority Rejected
**ID**: `authority_unknown_rejected`  
**Purpose**: Unknown authority does NOT fill blockers  
**Expected**: ASK_FOLLOWUP  
**Structure**: Fields with authority_level="unknown"

---

## Category D: Stage Progression (4 scenarios)

### D1: Discovery to Shortlist Transition
**ID**: `stage_discovery_to_shortlist`  
**Purpose**: selected_destinations becomes hard blocker in shortlist  
**Expected**: ASK_FOLLOWUP (missing selected_destinations)  
**Stage**: shortlist  
**Structure**: All discovery fields filled, but no selected_destinations

### D2: Shortlist to Proposal Transition
**ID**: `stage_shortlist_to_proposal`  
**Purpose**: selected_itinerary becomes hard blocker in proposal  
**Expected**: ASK_FOLLOWUP (missing selected_itinerary)  
**Stage**: proposal

### D3: Proposal to Booking Transition
**ID**: `stage_proposal_to_booking`  
**Purpose**: traveler_details and payment_method required in booking  
**Expected**: ASK_FOLLOWUP (2 new hard blockers)  
**Stage**: booking

### D4: Booking Complete
**ID**: `stage_booking_complete`  
**Purpose**: All booking fields filled  
**Expected**: PROCEED_TRAVELER_SAFE  
**Stage**: booking  
**Fields**: All hard + soft blockers filled

---

## Category E: Edge Cases (5 scenarios)

### E1: Null Values in Slots
**ID**: `edge_null_values`  
**Purpose**: Handle None values gracefully  
**Expected**: ASK_FOLLOWUP (null fields treated as missing)  
**Structure**: Slots with value=None

### E2: Empty String Values
**ID**: `edge_empty_strings`  
**Purpose**: Empty strings should be treated as missing  
**Expected**: ASK_FOLLOWUP  
**Structure**: Slots with value=""

### E3: Zero Confidence Facts
**ID**: `edge_zero_confidence`  
**Purpose**: Zero confidence should lower overall confidence  
**Expected**: PROCEED_INTERNAL_DRAFT (confidence too low)  
**Structure**: Facts with confidence=0.0

### E4: Duplicate Field Names Across Layers
**ID**: `edge_duplicate_layers`  
**Purpose**: Same field in facts, derived, AND hypotheses  
**Expected**: Uses facts (highest authority layer checked first)  
**Structure**: destination_city in all three layers

### E5: Unknown Stage Fallback
**ID**: `edge_unknown_stage`  
**Purpose**: Unknown stage defaults to discovery MVB  
**Expected**: Uses discovery blockers  
**Stage**: "unknown_stage"

---

## Category F: Complex Hybrid (5 scenarios)

### F1: Multi-Source Same Field
**ID**: `hybrid_multi_source`  
**Purpose**: Field with evidence from 2+ envelopes  
**Expected**: Detect multi-source conflict  
**Structure**: Single slot with 2 evidence_refs from different envelopes

### F2: Normalized Values
**ID**: `hybrid_normalized`  
**Purpose**: City codes normalized (blr → Bangalore)  
**Expected**: PROCEED_TRAVELER_SAFE, extraction_mode="normalized"  
**Structure**: origin_city="blr" with extraction_mode="normalized"

### F3: Cross-Layer Contradiction
**ID**: `hybrid_cross_layer`  
**Purpose**: Fact contradicts derived signal  
**Expected**: Fact wins (higher authority)  
**Structure**: facts.destination_city="Singapore", derived_signals.destination_city="Thailand"

### F4: Confidence Boundary - Exactly at Threshold
**ID**: `hybrid_confidence_boundary`  
**Purpose**: Test boundary condition  
**Expected**: Depends on implementation (>= vs >)  
**Structure**: Confidence calculated to exactly 0.6

### F5: All Layers Populated
**ID**: `hybrid_all_layers`  
**Purpose**: Facts, derived, hypotheses, AND unknowns all present  
**Expected**: Correct routing per layer rules  
**Structure**: Complex packet with all layers

