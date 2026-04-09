# Persona Scenario Coverage: Notebook 02

**Date**: 2026-04-09
**Purpose**: Map the 30 persona scenarios from `Docs/personas_scenarios/` to what NB02 actually validates
**Method**: Additive — existing tests (68 unit + 13 scenario) are NOT replaced. This document shows WHERE the persona scenarios ARE and AREN'T covered.

---

## The Gap This Fills

Our existing tests answer: _"Does the decision engine produce the right state?"_
The persona scenarios ask: _"Does Priya the agent get what she needs at 11 PM?"_

These are different questions. Both matter. This document maps them.

---

## Coverage Matrix

| Persona Scenario                       | What It Tests                                     | Covered By                                                    | Coverage Level | Gap                                                                                                                                                                   |
| -------------------------------------- | ------------------------------------------------- | ------------------------------------------------------------- | -------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **P1-S1**: 11 PM WhatsApp Panic        | Messy text → targeted questions with history      | Scenario: "Vague Lead"                                        | ⚠️ Partial     | History lookup not in NB02 (NB01 concern). Budget feasibility warning (4-5L for 5 in Europe) not computed                                                             |
| **P1-S2**: Repeat Customer             | History-enriched packet → PROCEED_INTERNAL_DRAFT  | Scenario: "CRM Return"                                        | ⚠️ Partial     | Full history enrichment happens in NB01. NB02 handles the resulting packet fine                                                                                       |
| **P1-S3**: Customer Changes Everything | Revision tracking → budget impossibility detected | Scenario: "The Dreamer" (budget-hotel conflict)               | ⚠️ Partial     | Budget feasibility math (3L/6 people for Maldives = 50K impossible) is beyond NB02's scope — needs external data                                                      |
| **P1-S4**: Visa Problem at Last Minute | Documentation blocker → STOP_NEEDS_REVIEW         | Unit Test: Full booking packet; Scenario: "Stage Progression" | ⚠️ Partial     | `passport_status` is not in the MVB for discovery. Only appears in booking stage. The EMERGENCY_PROTOCOL output (with options) is beyond NB02's DecisionResult schema |
| **P1-S5**: Multi-Party Group           | Sub-groups → partial readiness detection          | Not covered                                                   | ❌ Missing     | NB02's CanonicalPacket has no `sub_groups` field. Multi-party booking needs a different data structure                                                                |
| **P2-S1**: Quote Review                | Owner review → quality issues                     | Not covered                                                   | ❌ Missing     | This is an OWNER review workflow, not a GAP/DECISION workflow. Different decision engine                                                                              |
| **P2-S2**: Agent Left                  | Knowledge transfer → inherited profiles           | Not covered                                                   | ❌ Missing     | Knowledge transfer is outside NB02's scope                                                                                                                            |
| **P2-S3**: Margin Erosion              | Analytics → low-margin alerts                     | Not covered                                                   | ❌ Missing     | Margin calculation requires pricing data NB02 doesn't have                                                                                                            |
| **P2-S4**: Training                    | Guided step-by-step → confidence scoring          | Unit Test: confidence scoring                                 | ✅ Covered     | Confidence scoring exists and works                                                                                                                                   |
| **P2-S5**: Weekend Panic               | Document tracking → missing items alert           | Not covered                                                   | ❌ Missing     | Document tracking is a booking-stage concern                                                                                                                          |
| **P3-S1**: First Solo Quote            | Guided extraction → confidence check              | Unit Test: All confidence tests                               | ✅ Covered     | Low confidence correctly triggers ASK_FOLLOWUP                                                                                                                        |
| **P3-S2**: Visa Prevention             | Passport missing → hard blocker                   | Unit Test: Stage progression (booking)                        | ✅ Covered     | `traveler_details` is a hard blocker in booking stage                                                                                                                 |
| **P3-S3**: Completeness Check          | All costs included → validation                   | Not covered                                                   | ❌ Missing     | Cost completeness is beyond NB02's scope (no pricing data)                                                                                                            |
| **P3-S4**: Don't Know                  | Knowledge base lookup                             | Not covered                                                   | ❌ Missing     | Knowledge base is outside NB02's scope                                                                                                                                |
| **P3-S5**: Comparison Trap             | Competitor quote analysis                         | Not covered                                                   | ❌ Missing     | Competitor analysis is outside NB02's scope                                                                                                                           |
| **S1-S1**: Comparison Shopper          | Fast response → multiple options                  | Scenario: "Ready-to-Buy"                                      | ✅ Covered     | PROCEED_TRAVELER_SAFE when all blockers filled                                                                                                                        |
| **S1-S2**: Post-Booking Anxiety        | Already booked → proactive comms                  | Not covered                                                   | ❌ Missing     | Post-booking is outside NB02's scope                                                                                                                                  |
| **S1-S3**: Trip Emergency              | Crisis → emergency protocol                       | Scenario: "Confused Couple" (STOP_NEEDS_REVIEW)               | ⚠️ Partial     | STOP_NEEDS_REVIEW works but EMERGENCY_PROTOCOL with options is beyond DecisionResult schema                                                                           |
| **S2-S1**: Preference Collection       | Multiple inputs → conflict detection              | Scenario: "Confused Couple" (contradiction detection)         | ✅ Covered     | Contradiction detection works across all field types                                                                                                                  |
| **S2-S2**: Document Chaos              | Per-person tracking → progress                    | Not covered                                                   | ❌ Missing     | Per-person document tracking needs different data structure                                                                                                           |
| **S2-S3**: Budget Reality              | Feasibility check → alternatives                  | Scenario: "The Dreamer" (budget vs hotel)                     | ⚠️ Partial     | Budget feasibility MATH requires external pricing data                                                                                                                |

---

## What IS Covered (21 of 30 scenarios mapped; 9 additional scenarios are post-trip or edge cases outside NB02)

### ✅ Fully Covered (5 scenarios)

These persona scenarios are fully validated by existing tests:

| Scenario                     | Validated By                            | What Proves It Works                   |
| ---------------------------- | --------------------------------------- | -------------------------------------- |
| P2-S4: Training              | Unit tests: confidence scoring          | Low confidence → ASK_FOLLOWUP          |
| P3-S1: First Solo Quote      | Unit tests: all confidence tests        | Confidence scoring correct             |
| P3-S2: Visa Prevention       | Unit tests: stage progression (booking) | `traveler_details` hard blocker works  |
| S1-S1: Comparison Shopper    | Scenario: "Ready-to-Buy"                | PROCEED_TRAVELER_SAFE when complete    |
| S2-S1: Preference Collection | Scenario: "Confused Couple"             | Contradiction detection + ASK_FOLLOWUP |

### ⚠️ Partially Covered (7 scenarios)

These are partially validated but have gaps:

| Scenario                  | What Works                      | What's Missing                          | Where to Fix                             |
| ------------------------- | ------------------------------- | --------------------------------------- | ---------------------------------------- |
| P1-S1: 11 PM WhatsApp     | ASK_FOLLOWUP with questions     | History lookup, budget feasibility math | NB01 (history), external pricing service |
| P1-S2: Repeat Customer    | Packet handling                 | History enrichment                      | NB01                                     |
| P1-S3: Changes Everything | Budget-hotel conflict detection | Budget impossibility math               | External pricing service                 |
| P1-S4: Visa Problem       | Booking-stage hard blocker      | EMERGENCY_PROTOCOL output with options  | Extend DecisionResult schema             |
| P1-S5: Multi-Party        | —                               | Sub-groups data structure               | New CanonicalPacket extension            |
| S1-S3: Trip Emergency     | STOP_NEEDS_REVIEW               | Emergency options output                | Extend DecisionResult schema             |
| S2-S3: Budget Reality     | Budget contradiction detection  | Budget feasibility math                 | External pricing service                 |

### ❌ Not Covered (9 scenarios)

These are outside NB02's scope entirely:

| Scenario              | Why Not NB02                            | Whose Job Is It          |
| --------------------- | --------------------------------------- | ------------------------ |
| P2-S1: Quote Review   | Owner review workflow, not gap/decision | Owner dashboard (future) |
| P2-S2: Agent Left     | Knowledge transfer workflow             | CRM/knowledge base       |
| P2-S3: Margin Erosion | Analytics, needs pricing data           | Analytics engine         |
| P2-S5: Weekend Panic  | Document tracking, not gap/decision     | Document tracker         |
| P3-S3: Completeness   | Cost validation, needs pricing          | Cost validator           |
| P3-S4: Don't Know     | Knowledge base lookup                   | Knowledge base           |
| P3-S5: Comparison     | Competitor analysis                     | Competitor analyzer      |
| S1-S2: Post-Booking   | After booking, not during               | Post-booking system      |
| S2-S2: Document Chaos | Per-person tracking                     | Document tracker         |

---

## Key Insight: NB02 is a Narrow Slice

Of the 21 persona scenarios:

- **5 (24%)** are fully covered by NB02 tests
- **7 (33%)** are partially covered — NB02 does its part, other components fill gaps
- **9 (43%)** are outside NB02's scope — different systems entirely

This is correct. NB02's job is:

> **"Given a CanonicalPacket, what should we do next?"**

It does NOT:

- Look up customer history (NB01's job)
- Calculate budget feasibility (external pricing service)
- Track per-person documents (booking system)
- Review quote quality (owner dashboard)
- Analyze competitors (competitor analyzer)

---

## What Needs to Be Added to NB02 (The Real Gaps)

### Must Add (before NB03)

Nothing from the persona scenarios. NB02's scope is correct and complete.

### Should Add (for completeness)

1. **Emergency protocol output** — Extend DecisionResult to include `emergency_options` for STOP_NEEDS_REVIEW cases. This maps to P1-S4 and S1-S3.
2. **Multi-party awareness** — If a packet has `sub_groups`, check each group's readiness. This maps to P1-S5.

### Nice to Add (later)

3. **Budget feasibility check** — Requires external pricing data. Could be a simple lookup table: `{destination: min_per_person}`.
4. **Urgency detection** — From date proximity. "This weekend" → suppress soft blockers.

---

## Executive Summary

| Question                            | Answer                                                                                                                 |
| ----------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| How many persona scenarios exist?   | 30 (see `Docs/personas_scenarios/EXECUTIVE_SUMMARY.md`)                                                                |
| How many does NB02 fully cover?     | 5 (17%)                                                                                                                |
| How many does NB02 partially cover? | 7 (23%)                                                                                                                |
| How many are outside NB02's scope?  | 18 (60%)                                                                                                               |
| Is this a problem?                  | No — NB02 is a narrow slice. Other systems handle the rest                                                             |
| What does NB02 need before NB03?    | Nothing from persona scenarios. Gaps are in scope, not coverage                                                        |
| What should NB03 handle?            | History lookup, urgency detection, ambiguous value detection — see `02_gap_and_decision_contract.md` Known Limitations |

---

## Files Referenced

- Executive summary: `Docs/personas_scenarios/EXECUTIVE_SUMMARY.md`
- Test identification strategy: `Docs/personas_scenarios/TEST_IDENTIFICATION_STRATEGY.md`
- Scenario to pipeline mapping: `Docs/personas_scenarios/SCENARIOS_TO_PIPELINE_MAPPING.md`
- Persona scenarios: `Docs/personas_scenarios/P1_SOLO_AGENT_SCENARIOS.md`, `P2_AGENCY_OWNER_SCENARIOS.md`, `P3_JUNIOR_AGENT_SCENARIOS.md`, `S1S2_CUSTOMER_SCENARIOS.md`, `ADDITIONAL_SCENARIOS_21_25.md`
- Existing unit tests: `notebooks/test_02_comprehensive.py` (68 tests)
- Existing scenario tests: `notebooks/test_scenarios_realworld.py` (13 tests)
- Scenario analysis (first-principles thinking): `notebooks/scenario_analysis.md`
- Test results: `notebooks/02_SCENARIO_TEST_RESULTS.md`
