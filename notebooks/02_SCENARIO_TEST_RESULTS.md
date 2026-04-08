# Notebook 02: Real-World Scenario Test Results

**Date**: 2026-04-09
**Test file**: `notebooks/test_scenarios_realworld.py`
**Result**: 13/13 pass, 2 gaps identified

---

## What Was Tested

Not code mechanics. Real agency situations:

| # | Scenario | What It Represents |
|---|----------|-------------------|
| 1 | Vague Lead | Almost nothing known — "big family, international, maybe March" |
| 2 | Confused Couple | Husband and wife gave different notes with conflicting dates |
| 3 | The Dreamer | Wants 5-star Maldives, has backpacker budget (37.5k/person) |
| 4 | Ready-to-Buy | Everything confirmed, payment ready |
| 5 | WhatsApp Dump | Rich unstructured note with open destination ("Andaman or Sri Lanka?") |
| 6 | CRM Return | Old CRM data superseded by new explicit user call |
| 7 | Elderly Pilgrimage | 4 elderly, medical conditions, Char Dham Yatra |
| 8 | Last-Minute Booker | "This weekend!" — urgency over perfection |
| 9 | Stage Progression | Discovery-complete moving to shortlist |
| 10 | Partial Proposal | Shortlisted but hasn't chosen itinerary |
| 11 | Budget Stretch | "Around 2L, can stretch if it's good" |
| 12 | Inferred Destination | Destination derived from preferences, not explicitly stated |
| 13 | Multi-Envelope | 3 sources (CRM, owner notes, traveler form) merged |

---

## Results by Scenario

| # | Scenario | Decision | Correct? | Notes |
|---|----------|----------|----------|-------|
| 1 | Vague Lead | ASK_FOLLOWUP | ✅ | Asks 3 critical questions in right order |
| 2 | Confused Couple | STOP_NEEDS_REVIEW | ✅ | Date contradiction caught — agent must NOT call |
| 3 | The Dreamer | BRANCH_OPTIONS | ✅ | Budget-vs-luxury tension detected and surfaced |
| 4 | Ready-to-Buy | PROCEED_TRAVELER_SAFE | ✅ | Confidence 0.875, no blockers, no contradictions |
| 5 | WhatsApp Dump | PROCEED_INTERNAL_DRAFT | ⚠️ | **GAP**: treats "Andaman or Sri Lanka" as a valid destination. System can't tell "decided" from "undecided" |
| 6 | CRM Return | PROCEED_TRAVELER_SAFE | ✅ | New explicit_user data correctly overrides old CRM |
| 7 | Elderly Pilgrimage | PROCEED_TRAVELER_SAFE | ✅ | MVB satisfied, medical info in preferences (NB03 handles risk) |
| 8 | Last-Minute Booker | PROCEED_INTERNAL_DRAFT | ⚠️ | **GAP**: soft blockers (trip_purpose, traveler_preferences) block PROCEED_TRAVELER_SAFE even when urgency is extreme |
| 9 | Stage Progression | ASK_FOLLOWUP | ✅ | Correctly asks for selected_destinations at shortlist |
| 10 | Partial Proposal | ASK_FOLLOWUP | ✅ | Generates "Which itinerary option do you prefer?" |
| 11 | Budget Stretch | PROCEED_TRAVELER_SAFE | ⚠️ | Stretch signal captured in value string but not structurally parsed |
| 12 | Inferred Destination | PROCEED_TRAVELER_SAFE | ✅ | Derived signal fills blocker with lower confidence (0.812) |
| 13 | Multi-Envelope | PROCEED_TRAVELER_SAFE | ✅ | 3 sources merged, confidence 0.744 |

---

## Gaps Found

### Gap 1: Ambiguous Values Not Detected
**Scenario**: WhatsApp Dump
**Problem**: "Andaman or Sri Lanka" is stored as a string value in `destination_city`. The MVB checks "does this field exist?" — yes, it does. So the system considers the blocker filled. But in reality, the traveler hasn't decided.

**Why it matters**: The system treats "we want Singapore" (decided) and "maybe Andaman or Sri Lanka" (undecided) identically. Both are just strings.

**Where to fix**: Either:
- (a) Add a `destination_status` field (decided / semi-open / open) — per the context_deconstruction_pipeline spec
- (b) Add a contradiction detection for "or" patterns in value strings
- (c) NB03 should detect ambiguity during question generation

**Priority**: Medium. This is a Notebook 01 extraction issue — the intake layer should tag ambiguous values.

### Gap 2: No Urgency Handling
**Scenario**: Last-Minute Booker
**Problem**: "This weekend, flying Friday" → soft blockers `trip_purpose` and `traveler_preferences` remain unfilled, so the system returns `PROCEED_INTERNAL_DRAFT` instead of `PROCEED_TRAVELER_SAFE`.

**Why it matters**: For a last-minute trip, asking about trip purpose wastes time. The agent should book first, refine later.

**Where to fix**: Add an `urgency` or `rush` flag to the packet. When set, suppress soft blocker questions.

**Priority**: Low for now. This is a nice-to-have, not a correctness issue. The current behavior is conservative (safe), just annoying for urgent trips.

### Gap 3 (Minor): Budget Stretch Not Structured
**Scenario**: Budget Stretch
**Problem**: "200000 (can stretch)" is a string. The confidence scorer can't extract the numeric value separately from the flexibility signal.

**Why it matters**: Budget analysis (sourcing tier, hotel fit) works on the numeric part. The stretch signal is useful for NB03's question generation ("your budget is tight but you said you can stretch — should we explore options above 2L?").

**Where to fix**: Notebook 01 extraction should parse structured budget: `{base: 200000, stretch: true, max: null}`.

**Priority**: Low. Current behavior is correct, just loses signal.

---

## What This Means for NB03

NB03 takes the DecisionResult from NB02 and generates the session strategy. The gaps above mean:

1. **NB03 should detect ambiguous values** — If a destination value contains "or" or "maybe", the session strategy should ask for clarification even if NB02 said "proceed."

2. **NB03 should handle urgency** — If dates are within 7 days, suppress soft blocker questions regardless of NB02's decision.

3. **NB03 should parse budget stretch** — Extract the base budget and the stretch signal separately for better question generation.

These are NB03 concerns. NB02's job is done correctly given the data it receives. The gaps are in what NB01 extracts (or fails to extract) from raw notes.

---

## Files

- **Scenario analysis (thinking)**: `notebooks/scenario_analysis.md`
- **Scenario tests (code)**: `notebooks/test_scenarios_realworld.py`
- **This document (results)**: `notebooks/02_SCENARIO_TEST_RESULTS.md`
