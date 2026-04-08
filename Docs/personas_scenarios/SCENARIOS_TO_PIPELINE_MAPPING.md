# Scenarios to Pipeline Mapping

**Purpose**: Connect real-world scenarios to Notebook 01 (Intake) and Notebook 02 (Gap/Decision)  
**Goal**: Show how each scenario flows through the system

---

## Pipeline Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         THE TWO-NOTEBOOK PIPELINE                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  NOTEBOOK 01: INTAKE & NORMALIZATION          NOTEBOOK 02: GAP & DECISION   │
│  ┌──────────────────────────────────┐        ┌──────────────────────────┐   │
│  │ Input: Raw customer message      │        │ Input: CanonicalPacket   │   │
│  │        (WhatsApp/email/voice)    │───────▶│        from Notebook 01  │   │
│  │                                  │        │                          │   │
│  │ Process: Extract facts           │        │ Process: Check blockers  │   │
│  │          Classify authority      │        │          Detect conflicts│   │
│  │          Identify unknowns       │        │          Score confidence│   │
│  │                                  │        │                          │   │
│  │ Output: CanonicalPacket          │        │ Output: DecisionState    │   │
│  │         (structured state)       │        │         (what to do next)│   │
│  └──────────────────────────────────┘        └──────────────────────────┘   │
│                                                                             │
│  QUESTION: "What do we know?"                QUESTION: "What should we do?" │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Mapping by Persona

### P1: SOLO AGENT SCENARIOS

#### P1-S1: The 11 PM WhatsApp Panic

```yaml
Scenario: Mrs. Sharma messages at 11 PM about Europe trip

NOTEBOOK 01 (Intake):
  Input: 
    - Raw WhatsApp text: "Family of 5... Europe... June/July... 
      budget 4-5L... kids want snow... parents can't walk much..."
    - Context: Past customer (Singapore 2024)
  
  Process:
    - Extract facts: group_size=5, destination=Europe (semi-open), 
      dates=June/July (window), budget=4-5L
    - Classify: "kids want snow" → preference, "parents can't walk" → constraint
    - Recognize: Customer ID from phone number
    - Pull history: Singapore trip preferences
    - Identify unknowns: exact dates, specific destination, parent mobility details
  
  Output (CanonicalPacket):
    facts:
      origin_city: Bangalore (from history)
      group_composition: [adult x 2, child x 2, elderly x 1]
      date_window: June-July 2026
      budget_range: 4-5L
    
    derived_signals:
      trip_type: international
      budget_tier: mid-premium
      mobility_constraint: elderly_accessible_needed
    
    hypotheses:
      destination_candidate: Switzerland (from "snow")
      destination_alternative: Austria (also has snow)
    
    unknowns:
      - exact_travel_dates (hard blocker)
      - specific_destination (hard blocker)
      - elderly_mobility_details (soft blocker)
    
    contradictions: []

NOTEBOOK 02 (Gap & Decision):
  Input: CanonicalPacket above
  Stage: discovery
  
  Process:
    - Check hard blockers: missing dates, missing specific destination
    - Check soft blockers: missing mobility details
    - Calculate confidence: 45% (missing critical info)
    - Detect contradictions: "snow" + "elderly" + "June/July" = potential issue
    - Route: snow in summer = Alps = expensive = may not fit 4-5L for 5 people
  
  Output (DecisionState):
    decision_state: ASK_FOLLOWUP
    hard_blockers: [exact_dates, specific_destination]
    soft_blockers: [elderly_mobility_details, budget_confirmation]
    
    follow_up_questions:
      - field: exact_dates
        question: "Any specific dates in June/July? (Prices vary by week)"
        priority: critical
      
      - field: specific_destination  
        question: "For snow in summer: Switzerland, Austria, or open to others?"
        priority: critical
        note: "Switzerland fits budget but tight for 5 people"
      
      - field: elderly_mobility
        question: "For parents: wheelchair needed or just slower pace?"
        priority: high
        note: "Affects hotel selection significantly"
    
    rationale: 
      "Missing critical booking info (dates, destination). 
       Budget-constraint warning: 4-5L for 5 people in Alps is tight.
       Need clarification before quoting."
```

---

#### P1-S2: The Repeat Customer Who Forgot They Booked

```yaml
Scenario: Mr. Gupta messages 3 months after Dubai trip for "something new"

NOTEBOOK 01 (Intake):
  Input:
    - WhatsApp: "Dubai was great! Want something new. Family of 4. 
      International. Flexible budget. Suggestions?"
    - Phone number recognition
  
  Process:
    - Extract facts: group_size=4, trip_type=international, budget=flexible
    - Recognize customer: Mr. Gupta, Dubai Jan 2025
    - Pull complete history:
        * Past trip: Dubai, 5 nights, Atlantis
        * Budget spent: 3.2L (said "flexible", meant ~3L)
        * Preferences: water parks, vegetarian food, Jain options
        * Complaints: food expensive, afternoon heat
        * Passports: valid until 2029
    - No contradictions detected
  
  Output (CanonicalPacket):
    facts:
      customer_id: gupta_family
      group_composition: [adult x 2, child x 2]  # Ages updated from history
      trip_type: international
      budget_range: flexible (~3L based on history)
      passport_status: valid_until_2029
    
    derived_signals:
      repeat_customer: true
      previous_satisfaction: high
      preferred_style: luxury_resort_with_activities
      dietary_constraint: strict_vegetarian_jain
    
    hypotheses:
      interest: water_activities (from Atlantis love)
      avoid: extreme_heat (from Dubai complaint)
      preferred_region: middle_east_or_asia (proximity to Dubai)
    
    unknowns:
      - specific_destination (soft blocker - open to suggestions)
      - exact_dates (soft blocker)

NOTEBOOK 02 (Gap & Decision):
  Input: CanonicalPacket with rich history
  Stage: discovery
  
  Process:
    - Hard blockers: None critical (customer open to suggestions)
    - Soft blockers: destination, dates (but can suggest without)
    - Confidence: 75% (enough to proceed with suggestions)
    - Pattern match: Liked Atlantis → suggest similar (Sentosa, Gold Coast)
    - Avoid pattern: Complained about heat → avoid SE Asia summer
  
  Output (DecisionState):
    decision_state: PROCEED_INTERNAL_DRAFT
    
    hard_blockers: []
    soft_blockers: [specific_destination, exact_dates]
    
    follow_up_questions:
      - field: destination_preference
        question: "Based on your Dubai experience, considering: 
                  Singapore (Sentosa water park), 
                  Thailand (more activities but humid), 
                  or Gold Coast (beach + theme parks)?"
        priority: high
        suggested_values: [Singapore, Thailand, Gold_Coast]
    
    branch_options: []
    
    rationale:
      "Repeat customer with clear preference profile. 
       Enough info to suggest options. No critical blockers.
       Can proceed with internal draft based on history."
    
    internal_notes:
      "Customer spent 3.2L on Dubai, expect similar budget.
       Must include Jain food options in all suggestions.
       Highlight water activities (pattern from Atlantis love).
       Avoid peak summer for SE Asia (previous heat complaint)."
```

---

#### P1-S3: The Customer Who Changes Everything

```yaml
Scenario: Customer changes requirements 4 times in 4 days

NOTEBOOK 01 (Intake) - Day 1 (Rev 1):
  Input: "Family of 4, Maldives, March 15-20, budget 3L, honeymoon vibe"
  Output: Facts clear, no contradictions

NOTEBOOK 01 (Intake) - Day 2 (Rev 2):
  Input: "Actually can we do Bali instead? Same dates."
  Process: 
    - Detect change: destination Maldives → Bali
    - Keep: dates, group, budget
    - Flag: revision #2
  Output: Updated CanonicalPacket, change logged

NOTEBOOK 01 (Intake) - Day 3 (Rev 3):
  Input: "Parents want to join, so 6 people now. And dates shifted to April."
  Process:
    - Detect changes: group 4→6, dates March→April
    - Flag: revision #3
    - Contradiction check: dates changed (but old dates not booked)
  Output: Updated CanonicalPacket

NOTEBOOK 01 (Intake) - Day 4 (Rev 4):
  Input: "Back to Maldives but for 6. But budget still 3L. Can we do it?"
  Process:
    - Detect changes: destination Bali→Maldives, group 6
    - Budget unchanged: 3L
    - CRITICAL: 3L for 6 people in Maldives = ₹50K/person = IMPOSSIBLE
    - Minimum realistic: ₹80K/person = ₹4.8L
    - Flag: budget feasibility contradiction

NOTEBOOK 02 (Gap & Decision) - Day 4:
  Input: Day 4 CanonicalPacket
  
  Process:
    - Revision count: 4 changes in 4 days
    - Budget math: 3L / 6 = 50K per person
    - Maldives minimum: 80K per person
    - Shortfall: ₹1.8L (60% under budget)
    - Detect contradiction: stated_budget vs destination_requirements
  
  Output (DecisionState):
    decision_state: ASK_FOLLOWUP  # (not STOP because still solvable)
    
    hard_blockers: [realistic_budget_confirmation]
    
    contradictions:
      - type: budget_feasibility
        field: budget_range
        issue: "Maldives for 6 people requires ~₹4.8L minimum, 
                stated budget ₹3L"
        severity: blocking
    
    follow_up_questions:
      - field: budget_clarification
        question: "Maldives for 6 people: ₹50K/person won't cover 
                  flights + hotel. Realistic budget: ₹4.5-5L. 
                  Can we adjust budget or consider alternatives 
                  (Andaman Islands, similar vibe, fits 3L)?"
        priority: critical
        suggested_values: [increase_budget_to_5L, consider_andamans, reduce_to_4_people]
    
    agent_alerts:
      - "Customer has made 4 revisions in 4 days"
      - "Suggest confirming requirements before next quote"
      - "Consider planning fee for excessive revisions"
    
    rationale:
      "Budget constraint makes current request impossible.
       Revision pattern suggests unclear requirements.
       Must resolve budget or change destination before proceeding."
```

---

#### P1-S4: The Visa Problem at Last Minute

```yaml
Scenario: 19 days before travel, discover passports expired

NOTEBOOK 01 (Intake) - Initial (March 1):
  Input: First contact about Dubai trip
  
  Output:
    facts:
      destination_city: Dubai
      travel_dates: March 20-25  # 19 days away
      group_composition: [adult x 2, child x 2]
      # passport_status: UNKNOWN (not asked)
    
    unknowns:
      - passport_status (hard blocker for booking stage)

NOTEBOOK 02 (Gap & Decision) - Initial:
  Stage: discovery → shortlist → proposal
  Output: ASK_FOLLOWUP (need passport for booking)
  
  Note: At proposal stage, still ASK_FOLLOWUP because passport unknown

NOTEBOOK 01 (Intake) - Booking Stage (Crisis):
  Input: Agent realizes passport expired 2 months ago
  
  Process:
    - Extract fact: passport_expired = true
    - Calculate: Today March 1, expiry Jan 2025, travel March 20
    - Visa requirement: Dubai visa takes 5-7 working days
    - Passport renewal: Tatkal takes 7-10 days
    - Math: 19 days - 10 days renewal - 7 days visa = 2 days buffer
    - Risk: EXTREMELY HIGH
  
  Output (CanonicalPacket):
    facts:
      passport_status: EXPIRED_JAN_2025
      visa_requirement: required_for_18_days
      days_until_travel: 19
    
    contradictions:
      - type: documentation_impossible
        field: passport_validity
        issue: "Passport expired, travel in 19 days, 
                renewal + visa = 17 days minimum"
        severity: critical

NOTEBOOK 02 (Gap & Decision) - Crisis:
  Input: Crisis CanonicalPacket
  Stage: booking (attempted)
  
  Process:
    - Hard blocker: passport_valid = false
    - Time math: 19 days insufficient for renewal + visa
    - Options analysis:
        * Option 1: Tatkal passport (7-10 days) + visa (5-7 days) = RISKY
        * Option 2: Change dates to April = rebook everything
        * Option 3: Change to domestic (no passport) = major change
  
  Output (DecisionState):
    decision_state: STOP_NEEDS_REVIEW
    
    hard_blockers: [valid_passport, valid_visa]
    
    contradictions:
      - type: impossible_timeline
        description: "Cannot obtain valid passport + visa in 19 days"
    
    rationale:
      "CRITICAL: Travel in 19 days but passport expired.
       Timeline insufficient for renewal + visa processing.
       Requires human intervention and customer decision."
    
    emergency_options:
      - option: emergency_tatkal
        description: "Tatkal passport (₹5000 extra) + expedited visa"
        risk: "May not complete in time, ₹80K+ at risk"
        probability_success: 40%
      
      - option: change_dates
        description: "Move trip to April 15+"
        cost: "Rebooking fees, hotel change fees"
        probability_success: 95%
      
      - option: domestic_alternative
        description: "Switch to Kashmir or Himachal"
        cost: "Full replanning"
        probability_success: 90%
    
    agent_instructions:
      "Call customer IMMEDIATELY. Explain situation.
       Present 3 options with risks. Document their decision.
       Do NOT proceed with any booking until resolved."
```

---

#### P1-S5: Group Trip with Different Paying Parties

```yaml
Scenario: 3 families, different payment terms, need to track separately

NOTEBOOK 01 (Intake):
  Input: Mrs. Reddy coordinating for 3 families
  
  Process:
    - Extract: group_size=11 (6 adults, 5 kids)
    - Identify: 3 sub-groups (families A, B, C)
    - Payment terms:
        * Family A: Full upfront
        * Family B: EMI (3 installments)
        * Family C: 50% now, 50% later
    - Documents: Track per family
  
  Output (CanonicalPacket):
    facts:
      destination_city: Singapore
      travel_dates: May 15-20
      total_group_size: 11
      total_budget: 8L
    
    # Extended structure for multi-party
    sub_groups:
      family_a_reddy:
        size: 4
        budget_share: 3L
        payment_terms: full_upfront
        payment_status: paid ✅
        documents_status: complete ✅
      
      family_b_kumar:
        size: 4
        budget_share: 2.5L
        payment_terms: emi_3_instalments
        payment_status: instalment_2_of_3_pending
        documents_status: incomplete (missing 1 passport)
      
      family_c_shah:
        size: 3
        budget_share: 2.5L
        payment_terms: fifty_fifty
        payment_status: first_50_paid
        documents_status: not_submitted
    
    derived_signals:
      group_type: multi_family_coordination
      payment_complexity: high
      coordinator: Mrs. Reddy

NOTEBOOK 02 (Gap & Decision):
  Input: Multi-party CanonicalPacket
  Stage: booking
  
  Process:
    - Check individual sub-groups:
        * Family A: Ready ✅
        * Family B: Payment pending, documents incomplete ❌
        * Family C: Payment pending, documents missing ❌
    
    - Check group readiness:
        * Can book for Family A alone? No (shared trip)
        * Can book for all? No (B and C not ready)
        * Minimum for booking: All families 50% paid + documents
    
    - Calculate: 2 of 3 families not ready
  
  Output (DecisionState):
    decision_state: ASK_FOLLOWUP
    
    hard_blockers: 
      - family_b_payment_instalment_2
      - family_b_documents_passport_missing
      - family_c_payment_final_50
      - family_c_documents_all_missing
    
    follow_up_questions:
      - target: family_b_kumar
        question: "Payment reminder: Instalment 2 of ₹8,333 due March 1. 
                  Also need passport copy for child."
        priority: critical
        deadline: "March 1 (14 days)"
      
      - target: family_c_shah
        question: "Payment reminder: Final 50% (₹1.25L) due March 1. 
                  Also need all passport copies."
        priority: critical
        deadline: "March 1 (14 days)"
    
    coordinator_dashboard:
      - family_a: "Ready ✅"
      - family_b: "Payment + docs pending ⚠️"
      - family_c: "Everything pending 🚨"
      - group_status: "CANNOT BOOK until B and C ready"
    
    rationale:
      "Multi-party booking requires all parties ready.
       Family A ready but cannot book alone.
       Families B and C have critical blockers.
       Coordinator (Mrs. Reddy) needs to chase."
    
    risk_flags:
      - "If Family B/C don't pay by March 1, entire trip at risk"
      - "Suggest: Collect Family A's money only after B+C confirm"
```

---

## Summary Table: All 20 Scenarios Mapped

| ID | Scenario | N01 Role | N02 Role | Key Output |
|----|----------|----------|----------|------------|
| P1-S1 | 11 PM WhatsApp | Extract facts from messy text, pull history | ASK_FOLLOWUP (missing dates/destination) | Targeted questions with context |
| P1-S2 | Repeat customer | Recognize, pull full profile | PROCEED_INTERNAL_DRAFT (use history) | Personalized suggestions |
| P1-S3 | Revision loop | Track changes, detect budget contradiction | ASK_FOLLOWUP (budget impossible) | Alternative options + revision alert |
| P1-S4 | Visa crisis | Detect passport expiry, calculate timeline | STOP_NEEDS_REVIEW (impossible) | Emergency options + agent alert |
| P1-S5 | Multi-party | Parse sub-groups, track individually | ASK_FOLLOWUP (B & C not ready) | Coordinator dashboard |
| P2-S1 | Quote review | Compare to customer request | N/A (owner review) | Quality issues detected |
| P2-S2 | Agent left | Transfer knowledge | N/A (transition) | Inherited customer profiles |
| P2-S3 | Margin erosion | Calculate per-quote margin | N/A (analytics) | Low-margin alerts |
| P2-S4 | Training | Guide step-by-step | Confidence scoring | Suggested responses |
| P2-S5 | Weekend panic | Track document delivery | N/A (monitoring) | Missing items alert |
| P3-S1 | First solo quote | Guided extraction | Confidence check | Approval workflow |
| P3-S2 | Visa prevention | Flag passport missing | Hard blocker | "Cannot proceed" message |
| P3-S3 | Completeness check | Validate all costs included | Validation warnings | Missing items list |
| P3-S4 | Don't know | Knowledge base lookup | N/A (lookup) | Suggested answer |
| P3-S5 | Comparison trap | Analyze competitor quote | N/A (analysis) | Value comparison |
| S1-S1 | Comparison shopper | Extract requirements fast | PROCEED (multiple options) | 3 options with breakdown |
| S1-S2 | Post-booking anxiety | N/A (already booked) | N/A (proactive comms) | Automated status update |
| S1-S3 | Trip emergency | N/A (crisis mode) | STOP_NEEDS_REVIEW + options | Emergency protocol |
| S2-S1 | Preference collection | Aggregate multiple inputs | Conflict detection | Consensus suggestion |
| S2-S2 | Document chaos | Track per-person status | ASK_FOLLOWUP (incomplete) | Progress dashboard |
| S2-S3 | Budget reality | Calculate feasibility | ASK_FOLLOWUP (budget low) | Reality check + alternatives |

---

## Key Pipeline Insights

### Notebook 01 is about "UNDERSTANDING"
- What did the customer actually say?
- What's fact vs guess vs unknown?
- What's the history/context?

### Notebook 02 is about "DECIDING"
- Can we quote now or need more info?
- Are there dangerous conflicts?
- What's the next best action?

### The Handoff
```
N01: "Here's what I know (and don't know)"
       ↓
N02: "Based on that, here's what we should do"
       ↓
Action: Ask / Proceed / Stop / Branch
```

---

*Next: Test identification strategy documentation*
