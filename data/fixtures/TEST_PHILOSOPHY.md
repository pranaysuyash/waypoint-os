# Test Suite Philosophy: First Principles Analysis

**Why 30 Scenarios? A First Principles Decomposition**

---

## The Core Insight

Testing a decision system is not about covering every possible input. It's about covering every possible **way the system can fail**.

There are only **5 fundamental failure modes** for a gap-and-decision pipeline. All 30 scenarios map to these 5 modes.

---

## The 5 Fundamental Failure Modes

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  FAILURE MODE 1: FALSE POSITIVE                                             │
│  The system thinks it knows, but it doesn't.                                │
│  Result: Bad quotes, angry customers, wasted bookings.                      │
├─────────────────────────────────────────────────────────────────────────────┤
│  FAILURE MODE 2: FALSE NEGATIVE                                             │
│  The system asks when it already knows.                                     │
│  Result: Wasted time, customer frustration, slow response.                  │
├─────────────────────────────────────────────────────────────────────────────┤
│  FAILURE MODE 3: CONTRADICTION BLIND                                        │
│  The system misses that two things conflict.                                │
│  Result: Impossible itineraries, price mismatches, refunds.                 │
├─────────────────────────────────────────────────────────────────────────────┤
│  FAILURE MODE 4: AUTHORITY INVERSION                                        │
│  The system trusts the wrong source.                                        │
│  Result: Wrong data, bad decisions, loss of trust.                          │
├─────────────────────────────────────────────────────────────────────────────┤
│  FAILURE MODE 5: STAGE BLINDNESS                                            │
│  The system doesn't know where it is in the process.                        │
│  Result: Wrong actions, pipeline chaos, missed conversions.                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## The State Space Math

The system has 3 dimensions of variability:

| Dimension | States | Description |
|-----------|--------|-------------|
| **Data Layer** | 4 | fact / derived / hypothesis / unknown |
| **Authority Level** | 7 | manual / user / imported / owner / derived / hypothesis / unknown |
| **Presence** | 3 | present / missing / conflicting |

**Total theoretical combinations**: 4 × 7 × 3 = **84 possible states**

But we don't need 84 tests. We need the **minimal set that covers all 5 failure modes**.

---

## Mapping Scenarios to Failure Modes

### Failure Mode 1: False Positive
**The system thinks it knows, but it doesn't.**

| Test | Scenario | How It Prevents False Positive |
|------|----------|-------------------------------|
| A3 | `basic_hypothesis_only` | Hypothesis (guess) doesn't fill blocker → must ask |
| C5 | `authority_unknown_rejected` | Unknown authority doesn't count → must verify |
| E3 | `edge_zero_confidence` | Zero confidence facts → low overall confidence |

**Principle**: *Never confuse guessing with knowing.*

**Real-world**: Agent gets WhatsApp: "Family of 4, going somewhere warm, maybe Bali." System must ASK for destination, not quote for Bali.

---

### Failure Mode 2: False Negative
**The system asks when it already knows.**

| Test | Scenario | How It Prevents False Negative |
|------|----------|-------------------------------|
| A2 | `basic_complete_discovery` | All facts present → can proceed |
| A4 | `basic_derived_fills` | Derived signal fills blocker → no need to ask |
| F2 | `hybrid_normalized` | Normalized value counts as known (blr → Bangalore) |

**Principle**: *Don't ask for what you can compute or normalize.*

**Real-world**: Customer entered "blr" as origin. System knows this is Bangalore. Shouldn't ask "Which city?"

---

### Failure Mode 3: Contradiction Blindness
**The system misses that two things conflict.**

| Test | Scenario | Severity | How It Catches Conflicts |
|------|----------|----------|-------------------------|
| B1 | `contradiction_date_critical` | STOP | Date mismatch is unresolvable by system |
| B2 | `contradiction_budget_branch` | BRANCH | Budget ambiguity has valid alternatives |
| B3 | `contradiction_destination_ask` | ASK | Destination conflict needs clarification |
| B4 | `contradiction_count_ask` | ASK | Count mismatch affects pricing |
| B5 | `contradiction_origin_ask` | ASK | Origin conflict affects flights |
| F1 | `hybrid_multi_source` | DETECT | Same field, different sources |

**Principle**: *Conflicts must be detected and routed appropriately.*

**Real-world**: Customer email says "March 15", call says "April 1". System must STOP, not guess.

---

### Failure Mode 4: Authority Inversion
**The system trusts the wrong source.**

| Test | Scenario | Authority Boundary Tested |
|------|----------|---------------------------|
| C1 | `authority_manual_override` | manual > everything |
| C2 | `authority_owner_vs_imported` | imported > owner |
| C3 | `authority_derived_vs_hypothesis` | derived > hypothesis |
| C4 | `authority_explicit_user_high` | user is near-highest |
| F3 | `hybrid_cross_layer` | fact > derived (cross-layer) |

**Principle**: *Trust order must be strict: manual > user > imported > owner > derived > hypothesis > unknown*

**Real-world**: Owner's call notes say "Bangalore", CRM says "Mumbai". System trusts CRM (imported_structured) over notes (explicit_owner).

---

### Failure Mode 5: Stage Blindness
**The system doesn't know where it is in the sales process.**

| Test | Scenario | Stage Transition | What's Needed |
|------|----------|------------------|---------------|
| D1 | `stage_discovery_to_shortlist` | discovery → shortlist | selected_destinations |
| D2 | `stage_shortlist_to_proposal` | shortlist → proposal | selected_itinerary |
| D3 | `stage_proposal_to_booking` | proposal → booking | traveler_details, payment |
| D4 | `stage_booking_complete` | booking complete | All requirements met |

**Principle**: *"Ready" means different things at different stages.*

**Real-world**: 
- Discovery: "I want a family trip" (need to narrow down)
- Shortlist: "Singapore or Bali?" (need to pick)
- Proposal: "Here's the package" (need to confirm)
- Booking: "Ready to pay" (need passport details)

---

### Edge Cases: Garbage In → Graceful Out
**Reality is messy. The system must not crash.**

| Test | Scenario | Messy Input | Graceful Output |
|------|----------|-------------|-----------------|
| A1 | `basic_empty` | Nothing | ASK_FOLLOWUP (don't crash) |
| E1 | `edge_null_values` | Null fields | Treat as missing |
| E2 | `edge_empty_strings` | Empty strings | Don't treat as valid |
| E4 | `edge_duplicate_layers` | Same field everywhere | Facts layer wins |
| E5 | `edge_unknown_stage` | Invalid stage | Default to discovery |
| F4 | `hybrid_confidence_boundary` | Exactly at threshold | Defined behavior |
| F5 | `hybrid_all_layers` | Maximum complexity | Correct priority |

**Principle**: *The system must degrade gracefully.*

---

## The Count: Why 30?

```
Failure Mode 1 (False Positive):     3 tests
Failure Mode 2 (False Negative):     3 tests
Failure Mode 3 (Contradiction):      6 tests
Failure Mode 4 (Authority):          5 tests
Failure Mode 5 (Stage):              4 tests
Edge Cases:                          7 tests
Additional (Soft Blockers):          2 tests (A5, A6)
──────────────────────────────────────────────
Total:                              30 tests
```

**Margin**: We have 2 extra tests beyond the minimal set. This provides coverage redundancy for critical paths.

---

## What We Did NOT Test (And Why)

### Not Tested: Every Possible Field
**Why**: The logic is the same regardless of field name. Testing "destination_city" tests the pattern for all fields.

### Not Tested: Every Possible Value
**Why**: "Singapore" vs "Thailand" doesn't exercise different code paths. The value is opaque to the decision logic.

### Not Tested: Every Possible Contradiction Combination
**Why**: 5 contradiction types cover the severity spectrum: STOP / BRANCH / ASK. Specific fields don't matter.

### Not Tested: Negative Contradictions (A = A)
**Why**: Agreement is the default. We test disagreement because that's where logic is required.

### Not Tested: Performance Under Load
**Why**: This is a functional test suite. Performance tests are a separate concern.

---

## The Real-World vs Code Distinction

Each scenario is **both**:

| Scenario ID | Real-World Situation | Code Validation |
|-------------|---------------------|-----------------|
| A3 | Agent guesses from vague WhatsApp | `is_hypothesis() → field_fills_blocker() = False` |
| B1 | Customer says conflicting dates | `classify_contradiction("travel_dates") → STOP_NEEDS_REVIEW` |
| C2 | Owner notes vs CRM conflict | `imported_structured (0.85) > explicit_owner (0.80)` |
| F2 | Customer types "blr" | `extraction_mode="normalized"` is valid |

**The Story**: What happens in a real travel agency.  
**The Rule**: What the code must enforce.  
**The Test**: Proof that the rule handles the story.

---

## Verification Checklist

If all 30 tests pass, we have proven:

- [ ] **FM1**: System asks when it should (doesn't guess)
- [ ] **FM2**: System proceeds when it can (doesn't waste time)
- [ ] **FM3**: System catches all conflicts (doesn't miss contradictions)
- [ ] **FM4**: System trusts right sources (doesn't invert authority)
- [ ] **FM5**: System knows its stage (doesn't misroute)
- [ ] **Edge**: System degrades gracefully (doesn't crash on bad data)

---

## Bottom Line

**30 is not an arbitrary number.** It is the minimal set that proves the system will not fail in the 5 fundamental ways a gap-and-decision pipeline can fail.

Each test has a specific purpose. Each prevents a specific failure. Together, they provide confidence that the system is trustworthy.

---

*Document Version: 1.0*  
*Analysis Date: 2026-04-09*  
*Scenarios: 30*  
*Failure Modes Covered: 5/5*
