# Personas & Scenarios - Master Index

**For Future Agents**: Start here when asked to "review test coverage" or "identify what to test"

---

## Quick Start (TL;DR)

### If You're Asked To...

**"Review what scenarios we have"**  
→ Read: [README.md](README.md) → Check [SCENARIOS_TO_PIPELINE_MAPPING.md](SCENARIOS_TO_PIPELINE_MAPPING.md)

**"Identify what else needs testing"**  
→ Read: [TEST_IDENTIFICATION_STRATEGY.md](TEST_IDENTIFICATION_STRATEGY.md) → Follow the 8-step process

**"Create tests for [persona]"**  
→ Read: [STAKEHOLDER_MAP.md](STAKEHOLDER_MAP.md) → Open [P1_SOLO_AGENT_SCENARIOS.md](P1_SOLO_AGENT_SCENARIOS.md) (or appropriate file)

**"Map scenarios to notebooks"**  
→ Read: [SCENARIOS_TO_PIPELINE_MAPPING.md](SCENARIOS_TO_PIPELINE_MAPPING.md)

---

## Document Map

```
personas_scenarios/
│
├── INDEX.md ← YOU ARE HERE (Master navigation)
│
├── README.md
│   └── Overview of all 30 scenarios, quick reference tables,
│       key insights, design principles
│
├── STAKEHOLDER_MAP.md
│   └── Persona definitions (P1, P2, P3, S1, S2)
│       Demographics, pain points, goals, quotes
│       Stakeholder matrix (power vs interest)
│
├── P1_SOLO_AGENT_SCENARIOS.md
│   └── 5 real scenarios:
│       P1-S1: 11 PM WhatsApp Panic
│       P1-S2: Repeat Customer Who Forgot
│       P1-S3: Customer Changes Everything
│       P1-S4: Visa Problem at Last Minute
│       P1-S5: Group with Different Paying Parties
│
├── P2_AGENCY_OWNER_SCENARIOS.md
│   └── 5 real scenarios:
│       P2-S1: Quote Disaster Review
│       P2-S2: Agent Who Left
│       P2-S3: Margin Erosion Problem
│       P2-S4: Training Time Problem
│       P2-S5: Weekend Panic (No Visibility)
│
├── P3_JUNIOR_AGENT_SCENARIOS.md
│   └── 5 real scenarios:
│       P3-S1: First Solo Quote
│       P3-S2: Visa Mistake Prevention
│       P3-S3: "Is This Right?" Check
│       P3-S4: Don't Know Answer
│       P3-S5: Comparison Trap
│
├── S1S2_CUSTOMER_SCENARIOS.md
│   └── 5 real scenarios:
│       S1-S1: Comparison Shopper
│       S1-S2: Post-Booking Anxiety
│       S1-S3: Trip Emergency
│       S2-S1: Preference Collection Nightmare
│       S2-S2: Document Chaos
│       S2-S3: Budget Reality Conversation
│
├── ADDITIONAL_SCENARIOS_21_25.md
│   └── 10 advanced scenarios (21-30):
│       21: Ghost Customer (No Response)
│       22: Scope Creep (Free Consulting)
│       23: Influencer Request
│       24: Medical Emergency During Trip
│       25: Competing Family Priorities
│       26: Last-Minute Cancellation
│       27: Referral Request
│       28: Seasonal Rush
│       29: Package Customization
│       30: Review Request (Post-Trip)
│
├── SCENARIOS_TO_PIPELINE_MAPPING.md
│   └── Each scenario mapped to:
│       - Notebook 01 inputs/outputs
│       - Notebook 02 inputs/outputs
│       - Decision flow
│       - Success criteria
│
├── TEST_IDENTIFICATION_STRATEGY.md
│   └── How to identify new tests:
│       - 3 types of tests (Scenario/Pipeline/Code)
│       - Test template
│       - Priority framework
│       - 8-step process for adding tests
│
└── INDEX.md (this file)
    └── Navigation, quick start, checklist
```

---

## The 30 Scenarios at a Glance

### By Persona (5 personas, 30 scenarios)

| Persona | Scenarios | Focus |
|---------|-----------|-------|
| **P1 Solo Agent** | 5 + 5 shared | Daily workflows, memory, speed |
| **P2 Agency Owner** | 5 | Oversight, control, standardization |
| **P3 Junior Agent** | 5 | Learning, safety, confidence |
| **S1 Individual Traveler** | 2 + shared | Experience, speed, transparency |
| **S2 Family Coordinator** | 3 + shared | Group management, consensus |

### By Priority (P1 = Must Test)

**P1 - Must Test (8 scenarios)**:
- P1-S1: 11 PM WhatsApp Panic
- P1-S3: Revision tracking
- P1-S4: Visa/passport blockers
- P3-S2: Mistake prevention
- S1-S3: Emergency handling
- P2-S1: Quote quality
- P2-S3: Margin protection
- S2-S1: Preference collection

**P2 - Should Test (12 scenarios)**:
- P1-S2, P1-S5
- P2-S2, P2-S4, P2-S5
- P3-S1, P3-S3, P3-S4, P3-S5
- S1-S1, S1-S2, S2-S2

**P3 - Nice to Test (10 scenarios)**:
- S2-S3
- Scenarios 21-30 (edge cases)

### By Pipeline Stage

| Stage | Scenarios | Key Test |
|-------|-----------|----------|
| **N01 Intake** | All 30 | Fact extraction accuracy |
| **N02 Decision** | All 30 | Correct decision state |
| **End-to-End** | All 30 | Scenario plays out correctly |

---

## Key Concepts to Understand

### 1. The Two-Notebook Pipeline

```
NOTEBOOK 01: INTAKE          NOTEBOOK 02: DECISION
  Raw Input  ─────────────▶  Structured State  ─────────────▶  Action
  (WhatsApp)                  (CanonicalPacket)                (Ask/Proceed/Stop)
```

### 2. The Five Failure Modes

Every scenario tests one or more of:
1. **False Positive** - System thinks it knows, doesn't
2. **False Negative** - System asks when it knows
3. **Contradiction Blind** - Misses conflicts
4. **Authority Inversion** - Trusts wrong source
5. **Stage Blindness** - Wrong action for pipeline stage

### 3. Test Types (3 Types)

1. **Scenario Tests** - User behavior (30 scenarios documented)
2. **Pipeline Tests** - System flow (N01→N02 handoffs)
3. **Code Tests** - Implementation (functions work correctly)

**Order**: Scenario → Pipeline → Code

---

## Checklist: When Asked to "Review Test Coverage"

### Step 1: Understand What's There
- [ ] Read README.md (get overview)
- [ ] Count scenarios (should be 30)
- [ ] Check coverage by persona (all 5 covered?)
- [ ] Check coverage by priority (P1s all covered?)

### Step 2: Check Pipeline Mapping
- [ ] Each scenario mapped to N01?
- [ ] Each scenario mapped to N02?
- [ ] Inputs clearly defined?
- [ ] Outputs clearly defined?

### Step 3: Identify Gaps
- [ ] Any persona under-represented?
- [ ] Any failure mode not covered?
- [ ] Any decision state not tested?
- [ ] Any edge cases missing?

### Step 4: Prioritize New Tests
- [ ] Use priority framework (frequency × severity)
- [ ] Fill test identification template
- [ ] Get user validation (ask real agents)

---

## Checklist: When Asked to "Create New Tests"

### Step 1: Identify the Scenario
- [ ] Who is the persona?
- [ ] What is the situation?
- [ ] What is the input?
- [ ] What is the expected output?
- [ ] What if we get it wrong?

### Step 2: Document in Right File
- [ ] Solo Agent → P1_SOLO_AGENT_SCENARIOS.md
- [ ] Agency Owner → P2_AGENCY_OWNER_SCENARIOS.md
- [ ] Junior Agent → P3_JUNIOR_AGENT_SCENARIOS.md
- [ ] Customer → S1S2_CUSTOMER_SCENARIOS.md

### Step 3: Map to Pipeline
- [ ] What does N01 produce?
- [ ] What does N02 decide?
- [ ] What is the final action?

### Step 4: Validate
- [ ] Show to real travel agent
- [ ] Ask: "Does this happen?"
- [ ] Ask: "How do you handle it?"
- [ ] Adjust based on feedback

---

## Common Questions

### Q: Should I write code tests or scenario tests?
**A**: Scenario tests first. They define WHAT should work. Code tests ensure it works.

### Q: How detailed should scenarios be?
**A**: Real WhatsApp text, real decisions, real consequences. Vague scenarios = vague tests.

### Q: What if a scenario covers multiple personas?
**A**: Put in primary persona's file, note secondary impact in scenario.

### Q: How do I know if I've tested enough?
**A**: Cover all 5 failure modes for all 3 personas. That's the minimum.

### Q: Can I combine scenarios?
**A**: Only if they test the same thing. Don't combine just to reduce count.

---

## Red Flags (What to Avoid)

### Bad Scenario
```
"Test that the system handles customer input"
- Too vague
- No persona
- No input example
- No expected output
```

### Good Scenario
```
"P1-S1: Solo agent gets 11 PM WhatsApp from past customer
 Input: 'Family of 5... Europe... June/July... 4-5L... snow... elderly'
 Expected: System recognizes customer, pulls history, flags budget warning,
           generates 3 specific questions, ready in 2 minutes"
- Specific
- Clear persona
- Real input
- Measurable output
```

---

## Contact / Context

**Project**: Travel Agency AI Copilot  
**System**: Two-notebook pipeline (N01 Intake, N02 Decision)  
**Users**: Travel agencies (solo, small team)  
**Goal**: Compress workflow from lead to quote

**When in doubt**: 
- Think from user perspective first
- Ask: "What would Anita (Solo Agent) need here?"
- Test behavior, not implementation

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-04-09 | Initial 30 scenarios, full documentation |

---

**Next Steps for Future Agents**:
1. Pick a persona you want to understand
2. Read their scenario file
3. Pick a scenario that interests you
4. Read its pipeline mapping
5. Ask: "Does this match real-world travel agency work?"
6. If yes, implement. If no, adjust scenario.

**Remember**: Scenarios are living documents. Update them as you learn from real users.

---

*Start with the user, end with the test, never the other way around.*
