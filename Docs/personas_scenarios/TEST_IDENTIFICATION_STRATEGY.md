# Test Identification Strategy

**Purpose**: Define how to identify what needs testing, separate from how to code tests  
**Audience**: Future agents, product team, QA  
**Method**: First principles + scenario-driven

---

## The Core Problem

**Old way**: "Write tests for the code"
- Tests what the code does
- Misses what users actually need
- Technical validation, not value validation

**New way**: "Validate the scenarios"
- Tests real situations
- Validates user outcomes
- Behavior-driven, not code-driven

---

## Test Types: A Clear Taxonomy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         THREE TYPES OF TESTS                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. SCENARIO TESTS (User-Behavior)                                          │
│     ┌─────────────────────────────────────────────────────────────────┐    │
│     │ • Real-world situations                                         │    │
│     │ • Human inputs (WhatsApp, email, voice)                         │    │
│     │ • Human outputs (decisions, quotes, responses)                  │    │
│     │ • Question: "Does it handle Mrs. Sharma's 11 PM request?"       │    │
│     │ • Location: Docs/personas_scenarios/                            │    │
│     └─────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  2. PIPELINE TESTS (System-Behavior)                                        │
│     ┌─────────────────────────────────────────────────────────────────┐    │
│     │ • Data flow validation                                          │    │
│     │ • N01 → N02 handoff                                             │    │
│     │ • State transitions                                             │    │
│     │ • Question: "Does hypothesis correctly NOT fill blocker?"       │    │
│     │ • Location: notebooks/01_*, notebooks/02_*                      │    │
│     └─────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  3. CODE TESTS (Implementation)                                             │
│     ┌─────────────────────────────────────────────────────────────────┐    │
│     │ • Function correctness                                          │    │
│     │ • Edge cases (nulls, empty strings)                             │    │
│     │ • Performance                                                   │    │
│     │ • Question: "Does normalize_city('blr') return 'Bangalore'?"    │    │
│     │ • Location: tests/ (when created)                               │    │
│     └─────────────────────────────────────────────────────────────────┘    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

PURPOSE:
• Scenario tests = WHAT should work (user value)
• Pipeline tests = HOW it flows (system logic)  
• Code tests = THAT it works (implementation)

ORDER OF IMPORTANCE:
1. Scenario tests first (define success)
2. Pipeline tests second (validate flow)
3. Code tests third (ensure correctness)
```

---

## How to Identify Scenario Tests

### Step 1: Start with Personas, Not Code

**Wrong**: "Test the CanonicalPacket class"

**Right**: "What situations does Priya (Solo Agent) face daily?"

### Step 2: Extract Scenarios from Reality

For each persona, ask:

```
1. FREQUENCY: How often does this happen?
   - Daily? → Must test
   - Weekly? → Should test
   - Monthly? → Nice to test

2. SEVERITY: What if we get this wrong?
   - Lost booking? → Critical test
   - Wasted time? → Important test
   - Minor inconvenience? → Low priority

3. COMPLEXITY: How many variables?
   - Simple (1-2 factors) → Basic test
   - Medium (3-4 factors) → Standard test
   - Complex (5+ factors) → Priority test
```

### Step 3: Map to the Pipeline

For each scenario, identify:

```yaml
Scenario: [Name]

INPUTS:
  raw_input: "What the human sends"
  context: "What system should know (history, stage, etc.)"

NOTEBOOK_01_OUTPUTS:
  facts: "What should be extracted"
  hypotheses: "What should be guessed"
  unknowns: "What should be flagged as missing"
  contradictions: "What conflicts should be caught"

NOTEBOOK_02_OUTPUTS:
  decision_state: "ASK_FOLLOWUP / PROCEED / STOP / BRANCH"
  hard_blockers: "What's blocking"
  soft_blockers: "What's incomplete"
  follow_up_questions: "What should be asked"
  rationale: "Why this decision"

SUCCESS_CRITERIA:
  - "Customer gets appropriate response within X time"
  - "Agent is guided to correct action"
  - "No critical info is missed"
```

---

## Scenario Test Identification Template

Use this template for each scenario:

```markdown
## Test ID: [P1-S1, P2-S3, etc.]

### Scenario Name
[Short descriptive name]

### Real-World Situation
[Paragraph describing the real situation]

### Persona
- Primary: [Who is using the system]
- Affected: [Who is impacted]

### Frequency
[Daily / Weekly / Monthly / Rare]

### Severity if Wrong
[Critical / High / Medium / Low]

### Test This Because
[Why this scenario matters]

### Notebook 01 Test Points
- [ ] Fact extraction accuracy
- [ ] Authority level assignment
- [ ] Unknown identification
- [ ] Contradiction detection
- [ ] History/context integration

### Notebook 02 Test Points
- [ ] Correct decision state
- [ ] Blocker identification
- [ ] Question generation quality
- [ ] Rationale clarity
- [ ] Timing appropriateness

### Success Criteria
1. [Measurable outcome 1]
2. [Measurable outcome 2]
3. [Measurable outcome 3]

### Automation Potential
- Fully automatable? [Yes/No]
- Requires human judgment? [Yes/No]
- Needs periodic validation? [Yes/No]
```

---

## Example: Filled Template for P1-S1

```markdown
## Test ID: P1-S1

### Scenario Name
The 11 PM WhatsApp Panic

### Real-World Situation
Solo agent receives urgent WhatsApp from past customer at 11 PM.
Customer wants Europe trip for 5 people, vague dates, mentions snow
and elderly parents with mobility issues. Needs response by morning.

### Persona
- Primary: P1 Solo Agent (Anita)
- Affected: S2 Family Coordinator (Mrs. Sharma)

### Frequency
Weekly (late-night urgent requests common)

### Severity if Wrong
HIGH:
- Slow response = lost to competitor
- Wrong suggestions = bad fit = refund risk
- Missed constraints (elderly mobility) = disaster trip

### Test This Because
This is the "money moment" - fast, accurate response wins business.
Tests system speed, memory, and constraint awareness under pressure.

### Notebook 01 Test Points
- [x] Extracts: group=5, budget=4-5L, dates=June/July window
- [x] Recognizes: past customer (Singapore 2024)
- [x] Classifies: "snow"=preference, "can't walk"=constraint
- [x] Identifies unknowns: exact dates, specific destination, mobility details
- [x] Pulls history: knows family composition changed

### Notebook 02 Test Points
- [x] Decision: ASK_FOLLOWUP (not PROCEED - missing critical info)
- [x] Blockers: exact_dates, specific_destination
- [x] Questions: Targeted, prioritized, context-aware
- [x] Rationale: Notes budget-constraint warning (4-5L for 5 in Alps)
- [x] Timing: Flags as urgent (customer wants morning response)

### Success Criteria
1. System generates response suggestions within 2 minutes
2. Questions are specific (not generic "tell me more")
3. Budget warning is clear ("tight for 5 people")
4. History is used ("remember you loved Gardens by the Bay")
5. Agent feels supported, not overwhelmed

### Automation Potential
- Fully automatable? PARTIAL
n  - Fact extraction: Yes
  - Question generation: Yes
  - Response customization: Needs agent review
- Requires human judgment? YES (tone, final send)
- Needs periodic validation? YES (monthly spot-checks)
```

---

## How to Identify Pipeline Tests

Pipeline tests validate that data flows correctly between stages.

### Key Handoff Points to Test

```
┌─────────────────────────────────────────────────────────────────┐
│ HANDOFF 1: Raw Input → Notebook 01                             │
├─────────────────────────────────────────────────────────────────┤
│ • Does messy text become structured?                           │
│ • Are aliases resolved? ("blr" → "Bangalore")                  │
│ • Are contradictions preserved?                                │
│ • Is context attached?                                         │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ HANDOFF 2: Notebook 01 → Notebook 02                           │
├─────────────────────────────────────────────────────────────────┤
│ • Does CanonicalPacket have all required fields?               │
│ • Is stage correctly set?                                      │
│ • Are authority levels preserved?                              │
│ • Are unknowns explicit?                                       │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ HANDOFF 3: Notebook 02 → Action                                │
├─────────────────────────────────────────────────────────────────┤
│ • Is decision state valid?                                     │
│ • Are questions ordered correctly?                             │
│ • Is rationale clear enough for agent?                         │
│ • Are branch options complete?                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Pipeline Test Matrix

| Test | N01 Input | N01 Output | N02 Output | Validation |
|------|-----------|------------|------------|------------|
| Basic flow | WhatsApp text | Packet with facts | ASK_FOLLOWUP | Facts extracted correctly |
| Contradiction | Conflicting inputs | Packet with contradiction | STOP_NEEDS_REVIEW | Contradiction detected and routed |
| History | New msg from old customer | Packet with context | PROCEED_INTERNAL_DRAFT | History pulled and used |
| Revision | Changed requirements | Packet with changes flagged | ASK_FOLLOWUP + warning | Changes tracked |
| Emergency | "Medical emergency" | Packet with emergency flag | EMERGENCY_PROTOCOL | Keyword detected, protocol triggered |

---

## Test Priority Framework

### Priority 1: MUST TEST (Before Release)

**Criteria**:
- Frequency: Daily or multiple times per day
- Severity: Failure costs ₹10K+ or loses customer
- Persona: Affects Solo Agent (primary user)

**Scenarios**:
- P1-S1: 11 PM urgent request
- P1-S3: Revision tracking
- P1-S4: Visa/passport blockers
- P3-S2: Mistake prevention
- S1-S3: Emergency handling

### Priority 2: SHOULD TEST (Before Scale)

**Criteria**:
- Frequency: Weekly
- Severity: Failure wastes time or hurts reputation
- Persona: Affects Owner or Junior Agent

**Scenarios**:
- P2-S1: Quote quality control
- P2-S3: Margin protection
- P3-S1: First solo quote
- S2-S1: Preference collection
- S2-S3: Budget reality check

### Priority 3: NICE TO TEST (Ongoing)

**Criteria**:
- Frequency: Monthly or rare
- Severity: Failure is recoverable
- Persona: Edge cases

**Scenarios**:
- P2-S2: Agent departure (knowledge transfer)
- P2-S5: Weekend visibility
- P3-S5: Comparison handling
- S1-S2: Post-booking anxiety

---

## Test Coverage Checklist

Use this to ensure comprehensive coverage:

### Input Variety
- [ ] Text (WhatsApp, email)
- [ ] Structured (forms)
- [ ] Voice (call transcripts)
- [ ] Hybrid (text + attachments)

### Persona Coverage
- [ ] Solo Agent daily tasks
- [ ] Owner oversight needs
- [ ] Junior Agent learning
- [ ] Customer experience

### Decision Types
- [ ] ASK_FOLLOWUP (most common)
- [ ] PROCEED_INTERNAL_DRAFT
- [ ] PROCEED_TRAVELER_SAFE
- [ ] BRANCH_OPTIONS
- [ ] STOP_NEEDS_REVIEW
- [ ] EMERGENCY_PROTOCOL

### Data Layers
- [ ] Facts (explicit)
- [ ] Derived signals (computed)
- [ ] Hypotheses (guessed)
- [ ] Unknowns (missing)
- [ ] Contradictions (conflicting)

### Edge Cases
- [ ] Empty input
- [ ] Nonsense input
- [ ] Contradictory input
- [ ] Very long input
- [ ] Very short input
- [ ] Multiple languages

---

## For Future Agents: How to Add Tests

When you encounter a new situation:

### Step 1: Identify the Scenario
```
Ask:
1. Who is the persona?
2. What is the situation?
3. What is the input?
4. What is the expected output?
5. What happens if we get it wrong?
```

### Step 2: Document in Personas Folder
```
Add to appropriate file:
- Docs/personas_scenarios/P1_SOLO_AGENT_SCENARIOS.md
- Docs/personas_scenarios/P2_AGENCY_OWNER_SCENARIOS.md
- etc.

Follow format: Situation → Without System → With System → Pipeline Mapping
```

### Step 3: Create Test Identification
```
Fill out template:
- Test ID: [Next available]
- Frequency/Severity
- N01 test points
- N02 test points
- Success criteria
```

### Step 4: Map to Notebooks
```
Determine:
- Does this test N01 logic? (intake/normalization)
- Does this test N02 logic? (gap/decision)
- Does this test both? (end-to-end)
```

### Step 5: Validate with Real Users
```
Before finalizing:
- Show scenario to real travel agent
- Ask: "Does this match your reality?"
- Ask: "How would you handle this?"
- Adjust based on feedback
```

---

## Test Documentation Standards

### Every Test Must Have

1. **Clear Name**: "The [Situation] Scenario"
2. **Real Context**: Actual WhatsApp/email text
3. **Persona Tag**: Who is affected
4. **Pipeline Mapping**: N01 input/output, N02 input/output
5. **Success Criteria**: Measurable outcomes
6. **Failure Mode**: What happens if wrong

### Every Test Must NOT Have

1. **Code Implementation**: Don't write Python functions
2. **Technical Jargon**: No "serialize the protobuf"
3. **Assumptions**: Don't assume system capabilities
4. **Vagueness**: "Should work well" is not a criterion

---

## Summary: Test Identification Process

```
START: Real travel agency observation or request
       ↓
STEP 1: Identify persona + situation
       ↓
STEP 2: Determine frequency + severity
       ↓
STEP 3: Document in persona_scenarios/
       ↓
STEP 4: Fill test identification template
       ↓
STEP 5: Map to N01 and N02
       ↓
STEP 6: Validate with real users
       ↓
STEP 7: Priority classification (P1/P2/P3)
       ↓
STEP 8: Add to test suite tracking
       ↓
END: Scenario ready for pipeline implementation
```

---

## Current Status: 30 Scenarios Identified

| Category | Count | Coverage |
|----------|-------|----------|
| P1 Solo Agent | 5 | Daily workflows |
| P2 Agency Owner | 5 | Oversight & control |
| P3 Junior Agent | 5 | Learning & safety |
| S1/S2 Customers | 5 | Experience & service |
| Additional | 10 | Edge cases & advanced |
| **Total** | **30** | **Comprehensive** |

---

*Document Version: 1.0*  
*Method: First principles + scenario-driven*  
*Philosophy: Test behavior, not code*
