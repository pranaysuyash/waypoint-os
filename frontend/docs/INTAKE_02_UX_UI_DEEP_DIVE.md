# Intake & Packet Processing UX/UI Deep Dive

> User experience for reviewing, correcting, and completing extracted trip data

**Document:** INTAKE_02_UX_UI_DEEP_DIVE.md
**Series:** Intake / Packet Processing Deep Dive
**Status:** ✅ Complete
**Last Updated:** 2026-04-23
**Related:** [INTAKE_01_TECHNICAL_DEEP_DIVE.md](./INTAKE_01_TECHNICAL_DEEP_DIVE.md)

---

## Table of Contents

1. [UX Philosophy](#ux-philosophy)
2. [Packet Panel Overview](#packet-panel-overview)
3. [Extraction Review UI](#extraction-review-ui)
4. [Field Editing Experience](#field-editing-experience)
5. [Follow-Up Workflows](#follow-up-workflows)
6. [Validation Display](#validation-display)
7. [Channel-Specific UX](#channel-specific-ux)
8. [Mobile Experience](#mobile-experience)
9. [Implementation Reference](#implementation-reference)

---

## 1. UX Philosophy

### Core Principles

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      INTAKE UX PHILOSOPHY                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PRINCIPLE 1: TRUST BUT VERIFY                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ • AI extraction is a starting point, not final                     │   │
│  │ • Make confidence visible so agents know where to focus             │   │
│  │ • Easy override and correction mechanisms                           │   │
│  │ • Learn from agent corrections                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  PRINCIPLE 2: SPEED WITH ACCURACY                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ • Default to AI-extracted values (speed)                           │   │
│  │ • Flag low-confidence fields for review (accuracy)                 │   │
│  │ • One-click fixes for common issues                                │   │
│  │ • Keyboard-first workflow for power users                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  PRINCIPLE 3: PROGRESSIVE DISCLOSURE                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ • Show most important info first                                   │   │
│  │ • Reveal complexity on demand                                       │   │
│  │ • Collapse sections to reduce cognitive load                       │   │
│  │ • Contextual help at point of need                                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  PRINCIPLE 4: CHANNEL CONTEXT                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ • Show original message alongside extracted data                    │   │
│  │ • Preserve channel-specific context (emojis, voice tone)            │   │
│  │ • Handle attachments prominently                                    │   │
│  │ • Enable quick channel-based responses                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### The Review Hierarchy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       REVIEW ATTENTION HIERARCHY                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  TIER 1: CRITICAL (Must Review)                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ • Low confidence critical fields (< 70%)                            │   │
│  │ • Validation errors (invalid dates, impossible combinations)        │   │
│  │ • Missing required fields                                          │   │
│  │ • High-value customer inquiries                                    │   │
│  │ Visual: Red badge, prominent placement                              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  TIER 2: IMPORTANT (Should Review)                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ • Medium confidence fields (70-85%)                                │   │
│  │ • Validation warnings (unusual but possible)                       │   │
│  │ • Ambiguous extractions                                           │   │
│  │ Visual: Yellow badge, visible but not distracting                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  TIER 3: GOOD TO KNOW (Optional Review)                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ • High confidence fields (> 85%)                                   │   │
│  │ • Inferred values with high certainty                              │   │
│  │ • Non-critical optional fields                                     │   │
│  │ Visual: No badge, subtle indicators on hover                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Packet Panel Overview

### Panel Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        PACKET PANEL LAYOUT                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ┌───┐  Goa Family Trip                     [●●●○○] 78% Complete  │   │
│  │  │ ◀ │  May 15-20, 2025 • 4 adults                              │   │
│  │  └───┘  Budget: ₹80,000                                           │   │
│  │                                                                 │   │
│  │  ┌────────────┬────────────┬────────────┬────────────┐            │   │
│  │  │ Extraction │ Validation │ Customer   │ Actions    │            │   │
│  │  │   92%     │   1 error  │  Returning  │            │            │   │
│  │  └────────────┴────────────┴────────────┴────────────┘            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌───────────────────────────────────────┬───────────────────────────────┐ │
│  │                                     │                               │ │
│  │  ┌─────────────────────────────┐     │   ┌─────────────────────┐    │ │
│  │  │   ORIGINAL MESSAGE         │     │   │   EXTRACTED DATA     │    │ │
│  │  ├─────────────────────────────┤     │   ├─────────────────────┤    │ │
│  │  │ "Planning trip to Goa in    │     │   │ Destination  ● Goa  │    │ │
│  │  │  May. 4 adults. Budget     │     │   │ Dates       ○ 15-20 │    │ │
│  │  │  around 80k. Want to       │     │   │ Travelers   ● 4     │    │ │
│  │  │  visit North Goa beaches.  │     │   │ Budget      ● ₹80k │    │ │
│  │  │  Need 3 rooms."            │     │   │                         │    │ │
│  │  │                             │     │   │ ▼ Show more fields      │    │ │
│  │  │ [Audio note 0:23]          │     │   └─────────────────────┘    │ │
│  │  └─────────────────────────────┘     │                               │ │
│  │                                     │   ┌─────────────────────┐    │ │
│  │                                     │   │   VALIDATION ISSUES  │    │ │
│  │                                     │   ├─────────────────────┤    │ │
│  │                                     │   │ ⚠ Start date       │    │ │
│  │                                     │   │   missing year      │    │ │
│  │                                     │   │   Assuming 2025     │    │ │
│  │                                     │   └─────────────────────┘    │ │
│  │                                     │                               │ │
│  └───────────────────────────────────────┴───────────────────────────────┘ │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  [Mark Complete]  [Request Info]  [Edit Fields]  [View Customer]   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Panel States

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PANEL STATES                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  STATE 1: EXTRACTING (Loading)                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                     │   │
│  │      ⏳ Extracting trip details...                                  │   │
│  │                                                                     │   │
│  │      ████████░░░░░░░░░░ 45%                                         │   │
│  │                                                                     │   │
│  │      Identifying destination...                                     │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  STATE 2: NEEDS REVIEW (Default)                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Shows: Extracted data, confidence indicators, validation issues    │   │
│  │  Focus: Fields needing agent attention highlighted                 │   │
│  │  Actions: Edit, confirm, request info                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  STATE 3: EDITING                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Shows: Editable form with all fields                               │   │
│  │  Focus: Inline editing with smart suggestions                       │   │
│  │  Actions: Save, cancel, auto-fix suggestions                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  STATE 4: AWAITING INFO                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Shows: What info we're waiting for, sent questions                │   │
│  │  Focus: Customer follow-up status                                   │   │
│  │  Actions: Send reminder, update with received info                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  STATE 5: COMPLETE                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Shows: Confirmed data, ready for decision engine                  │   │
│  │  Focus: Summary view                                               │   │
│  │  Actions: Proceed to strategy, re-open if needed                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Extraction Review UI

### Confidence Visualization

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      CONFIDENCE INDICATOR PATTERNS                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PATTERN 1: PER-FIELD CONFIDENCE BAR                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                     │   │
│  │  Destination                                                        │   │
│  │  ┌────────────────────────────────────┐                             │   │
│  │  │ Goa                      ████████░░ 92% │ ✓ High confidence     │   │
│  │  └────────────────────────────────────┘                             │   │
│  │                                                                     │   │
│  │  Dates                                                              │   │
│  │  ┌────────────────────────────────────┐                             │   │
│  │  │ May 15-20                ████░░░░░░ 67% │ ⚠ Medium confidence   │   │
│  │  │ [Year not specified]              │   Missing year assumed     │   │
│  │  └────────────────────────────────────┘                             │   │
│  │                                                                     │   │
│  │  Budget                                                             │   │
│  │  ┌────────────────────────────────────┐                             │   │
│  │  │ ₹80,000                  ██░░░░░░░░ 45% │ ⚠ Low confidence      │   │
│  │  │ [Implied from "around 80k"]        │   Verify with customer     │   │
│  │  └────────────────────────────────────┘                             │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  PATTERN 2: COLOR-CODED BADGES                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                     │   │
│  │  ● Goa        ████████░░ 92%    [High - Verified]                  │   │
│  │  ● May 15-20  ████░░░░░░ 67%    [Medium - Year assumed]            │   │
│  │  ● ₹80,000   ██░░░░░░░░ 45%    [Low - Needs verification]         │   │
│  │  ● 4 adults  ████████░░ 89%    [High - Explicit]                   │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  PATTERN 3: OVERALL EXTRACTION HEALTH                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                     │   │
│  │  Extraction Health    ●●●●●○○○○○○ 50%                              │   │
│  │                                                                     │   │
│  │  ┌─────────────────────────────────────────────────────────────┐   │   │
│  │  │ Fields: 8 extracted, 2 high confidence, 4 medium, 2 low    │   │   │
│  │  │                                                             │   │   │
│  │  │ ⚠ Action needed:                                          │   │   │
│  │  │ • Verify budget amount with customer                        │   │   │
│  │  │ • Confirm travel year (assumed 2025)                        │   │   │
│  │  │ • Clarify accommodation preferences                          │   │   │
│  │  └─────────────────────────────────────────────────────────────┘   │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Source Attribution

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       SOURCE ATTRIBUTION UI                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Show HOW each value was extracted for transparency                         │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Destination: Goa                                                  │   │
│  │  ┌─────────────────────────────────────────────────────────────┐   │   │
│  │  │ Source: Explicit text                                       │   │   │
│  │  │ "Planning trip to Goa..."                                   │   │   │
│  │  │ Extracted by: LLM                                           │   │   │
│  │  │ Confirmed by: Rules (pattern match)                          │   │   │
│  │  └─────────────────────────────────────────────────────────────┘   │   │
│  │                                                                     │   │
│  │  ┌─────────────────────────────────────────────────────────────┐   │   │
│  │  │ ●●● Both LLM and Rules agree — High confidence              │   │   │
│  │  └─────────────────────────────────────────────────────────────┘   │   │
│  │                                                                     │   │
│  ────────────────────────────────────────────────────────────────────  │   │
│  │                                                                     │   │
│  │  Budget: ₹80,000                                                   │   │
│  │  ┌─────────────────────────────────────────────────────────────┐   │   │
│  │  │ Source: Implied from context                                │   │   │
│  │  │ "Budget around 80k"                                          │   │   │
│  │  │ Extracted by: LLM (inference)                               │   │   │
│  │  │ Not found in: Rules (no explicit amount pattern)             │   │   │
│  │  │                                                             │   │   │
│  │  │ ⚠ Ambiguous: "around" suggests approximation                │   │   │
│  │  └─────────────────────────────────────────────────────────────┘   │   │
│  │                                                                     │   │
│  ┌─────────────────────────────────────────────────────────────┐       │   │
│  │  ●○ LLM only — Medium confidence, Rules didn't match       │       │   │
│  │  └─────────────────────────────────────────────────────────────┘       │   │
│  │                                                                     │   │
│  ────────────────────────────────────────────────────────────────────  │   │
│  │                                                                     │   │
│  │  Start Date: May 15                                                 │   │
│  │  ┌─────────────────────────────────────────────────────────────┐   │   │
│  │  │ Source: Explicit text (partial)                             │   │   │
│  │  │ "May 15-20"                                                 │   │   │
│  │  │ Extracted by: Rules (date pattern)                          │   │   │
│  │  │ Missing: Year                                               │   │   │
│  │  │ Assumption: Current year (2025) based on context             │   │   │
│  │  │                                                             │   │   │
│  │  │ ⚠ Incomplete: Year not specified, assumed                    │   │   │
│  │  └─────────────────────────────────────────────────────────────┘   │   │
│  │                                                                     │   │
│  ┌─────────────────────────────────────────────────────────────┐       │   │
│  │  [Edit to specify year] [Confirm 2025 assumption]           │       │   │
│  │  └─────────────────────────────────────────────────────────────┘       │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Field Editing Experience

### Inline Editing

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         INLINE EDITING UI                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  MODE 1: QUICK EDIT (Click to edit)                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                     │   │
│  │  Destination: Goa                        [Click field to edit]       │   │
│  │                ┌─────────────────────┐                              │   │
│  │                │ ✏ Edit │ ✓ Done │ ✗ Cancel                     │   │
│  │                └─────────────────────┘                              │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  MODE 2: INLINE EDIT (Click field transforms to input)                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                     │   │
│  │  Destination: [Goa                    ] ████░░░░ 92%  [Save│Cancel]│   │
│  │                └─ Suggested: ┌─┬─┬─┬─┬─┐                              │   │
│  │                           North Goa │South Goa│Panaji│Old Goa       │   │
│  │                           └─────────┴─────────┴──────┴───────────┘   │   │
│  │                                                                     │   │
│  │  Start Date:  [May 15, 2025            ] ████░░░░ 67%              │   │
│  │                 └─ Calendar ── Quick: ┌─┬─┬─┬─┐                    │   │
│  │                                     Today│Tomorrow│+1 week│+1 month  │   │
│  │                                     └─────┴────────┴───────┴─────────┘   │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  MODE 3: SMART SUGGESTIONS                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                     │   │
│  │  You're changing: "Goa" → "Gokarna"                                 │   │
│  │                                                                     │   │
│  │  💡 Suggested updates based on destination change:                   │   │
│  │  ┌─────────────────────────────────────────────────────────────┐   │   │
│  │  │ ✓ Update budget estimate: ₹80,000 → ₹65,000                   │   │   │
│  │  │ ✓ Update accommodation type: Beach resort → Homestay          │   │   │
│  │  │ ○ Update transportation: Flight → Train + Taxi                │   │   │
│  │  │                                                             │   │   │
│  │  │ [Apply all] [Apply selected] [Ignore suggestions]            │   │   │
│  │  └─────────────────────────────────────────────────────────────┘   │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  MODE 4: VALIDATION DURING EDIT                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                     │   │
│  │  Budget: [₹5,000                    ]                              │   │
│  │           ┌─────────────────────────────────────────┐              │   │
│  │           │ ⚠ Warning: This seems very low for Goa │              │   │
│  │           │   Typical 3-day trip: ₹25,000-50,000   │              │   │
│  │           │                                        │              │   │
│  │           │ Did you mean: ₹50,000? ₹15,000?       │              │   │
│  │           │ [Use suggested] [Keep original]      │              │   │
│  │           └─────────────────────────────────────────┘              │   │
│  │                                                                     │   │
│  │  End Date: [May 10, 2025             ]                              │   │
│  │            ┌─────────────────────────────────────────┐              │   │
│  │            │ ⚠ Error: End date before start date  │              │   │
│  │            │   Start: May 15, 2025                │              │   │
│  │            │                                        │              │   │
│  │            │ [Fix: Swap dates] [Edit start date]   │              │   │
│  │            └─────────────────────────────────────────┘              │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Bulk Operations

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        BULK EDIT OPERATIONS                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  SCENARIO: Multiple similar inquiries need same correction                   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ☐ 2025-05-001 | Goa | May 15-20 | ₹80k | 4 adults                 │   │
│  │  ☑ 2025-05-002 │ Goa│ May 20-25 │ ₹80k │ 4 adults    ⚠ Year missing│   │
│  │  ☑ 2025-05-003 │ Goa│ May 25-30 │ ₹80k │ 4 adults    ⚠ Year missing│   │
│  │  ☐ 2025-05-004 │ Goa│ Jun 01-06 │ ₹80k │ 4 adults                 │   │
│  │                                                                     │   │
│  │  [2 selected]                                                       │   │
│  │                                                                     │   │
│  │  Bulk actions:                                                       │   │
│  │  ┌─────────────────────────────────────────────────────────────┐   │   │
│  │  │ 📅 Add year to dates: [2025────] [Apply]                     │   │   │
│  │  │ 💰 Update budget:   [₹80,000──] [Apply]                      │   │   │
│  │  │ 👥 Set travelers:  [4 adults─] [Apply]                        │   │   │
│  │  │                                                            │   │   │
│  │  │ [Mark all reviewed] [Request info] [Export CSV]             │   │   │
│  │  └─────────────────────────────────────────────────────────────┘   │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  AUTO-FILL SUGGESTIONS:                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Based on similar inquiries, suggest:                               │   │
│  │                                                                     │   │
│  │  ┌─────────────────────────────────────────────────────────────┐   │   │
│  │  │ ✓ Accommodation: 3-star hotel in North Goa                   │   │   │
│  │  │ ✓ Transportation: Flight + Taxi (included in budget)          │   │   │
│  │  │ ○ Travel insurance: Not specified                            │   │   │
│  │  │                                                             │   │   │
│  │  │ [Apply to all 2] [Apply individually]                         │   │   │
│  │  └─────────────────────────────────────────────────────────────┘   │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Follow-Up Workflows

### Requesting Information from Customer

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CUSTOMER FOLLOW-UP WORKFLOW                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  STEP 1: IDENTIFY MISSING INFO                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                     │   │
│  │  Missing Information:                                                │   │
│  │  ┌─────────────────────────────────────────────────────────────┐   │   │
│  │  │ 🔴 CRITICAL:                                                  │   │   │
│  │  │   • Exact travel dates (year not specified)                  │   │   │
│  │  │   • Number of children (if any)                              │   │   │
│  │  │                                                             │   │   │
│  │  │ 🟡 IMPORTANT:                                                 │   │   │
│  │  │   • Hotel preference (budget/mid-range/luxury)               │   │   │
│  │  │   • Specific areas in Goa preferred                          │   │   │
│  │  │                                                             │   │   │
│  │  │ ⚪ NICE TO HAVE:                                              │   │   │
│  │  │   • Meal preferences                                         │   │   │
│  │  │   • Transportation preference                                 │   │   │
│  │  └─────────────────────────────────────────────────────────────┘   │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                │                                           │
│                                ▼                                           │
│  STEP 2: CHOOSE FOLLOW-UP CHANNEL                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                     │   │
│  │  Send follow-up via:                                                │   │
│  │  ┌────────────┬────────────┬────────────┬────────────┐              │   │
│  │  │ WhatsApp   │   Email    │   SMS      │  Call      │              │   │
│  │  │  (Recommended) │           │           │            │              │   │
│  │  └─────┬──────┴─────┬──────┴─────┬──────┴─────┬──────┘              │   │
│  │        │             │            │            │                     │   │
│  │        ▼             ▼            ▼            ▼                     │   │
│  │   Quick         Formal       Urgent      Complex                     │   │
│  │   response     record      alert       discussion                   │   │
│  │   (95% read)   (tracked)   (immediate)  (personal)                  │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                │                                           │
│                                ▼                                           │
│  STEP 3: CUSTOMIZE MESSAGE                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                     │   │
│  │  Template: Goa Trip - Missing Dates                                 │   │
│  │  ┌─────────────────────────────────────────────────────────────┐   │   │
│  │  │ Hi! 👋 We're excited to help plan your Goa trip! 🏖️          │   │   │
│  │  │                                                             │   │   │
│  │  │ Just need to confirm: Which year are you planning to        │   │   │
│  │  │ travel in May? (Assuming 2025)                               │   │   │
│  │  │                                                             │   │   │
│  │  │ Also, how many kids will be traveling?                     │   │   │
│  │  │                                                             │   │   │
│  │  │ [Edit message...]                                            │   │   │
│  │  └─────────────────────────────────────────────────────────────┘   │   │
│  │                                                                     │   │
│  │  Tone: ☐ Friendly ☐ Formal ☐ Casual                                │   │
│  │  Language: ☐ English ☐ Hindi ☐ Mixed                               │   │
│  │  Include: ☐ Quick reply buttons ☐ Calendar link                   │   │
│  │                                                                     │   │
│  │  [Preview] [Send] [Schedule]                                        │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                │                                           │
│                                ▼                                           │
│  STEP 4: TRACK RESPONSE                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                     │   │
│  │  Follow-up Status: Awaiting Response                                │   │
│  │  Sent: 2 hours ago via WhatsApp                                     │   │
│  │  ┌─────────────────────────────────────────────────────────────┐   │   │
│  │  │ Reminder scheduled: In 24 hours if no response               │   │   │
│  │  │                                                             │   │   │
│  │  │ Quick actions:                                               │   │   │
│  │  │ [Send reminder now] [Mark as unresponsive] [Call customer]   │   │   │
│  │  └─────────────────────────────────────────────────────────────┘   │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Quick Reply Templates

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       QUICK REPLY TEMPLATES                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  CATEGORY: Dates                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  "Could you please confirm the exact travel dates?"                  │   │
│  │  "Which year - 2025 or 2026?"                                        │   │
│  │  "Are your dates flexible? (+/- 3 days?)"                            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  CATEGORY: Budget                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  "What's your approximate budget per person?"                        │   │
│  │  "Is this budget flexible?"                                         │   │
│  │  "Does this include flights?"                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  CATEGORY: Travelers                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  "How many adults and children?"                                    │   │
│  │  "Ages of children?" (for pricing)                                  │   │
│  │  "Any seniors traveling?" (for discounts)                           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  CATEGORY: Destination                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  "Any specific areas you prefer?"                                   │   │
│  │  "Beach vs hill station?"                                          │   │
│  │  "Domestic or international?"                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  CATEGORY: Accommodation                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  "Hotel preference: Budget, 3-star, or luxury?"                    │   │
│  │  "Any specific amenities required?"                                 │   │
│  │  "Room configuration needed?"                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Validation Display

### Error & Warning Presentation

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      VALIDATION UI PATTERNS                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PATTERN 1: INLINE VALIDATION                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                     │   │
│  │  Start Date: [May 15, 2025            ]  ✓ Valid                    │   │
│  │  End Date:   [May 10, 2025            ]  ⚠ Before start date!      │   │
│  │                   ┌─────────────────────────────────────────┐       │   │
│  │                   │ Fix: Swap dates or edit start date       │       │   │
│  │                   │ [Swap] [Edit Start] [Ignore]            │       │   │
│  │                   └─────────────────────────────────────────┘       │   │
│  │                                                                     │   │
│  │  Budget:     [₹5,000                  ]  ⚠ Very low for Goa       │   │
│  │                   ┌─────────────────────────────────────────┐       │   │
│  │                   │ Typical range: ₹25,000-50,000            │       │   │
│  │                   │ Did you mean: ₹50,000?                   │       │   │
│  │                   │ [Use suggested] [Keep original]          │       │   │
│  │                   └─────────────────────────────────────────┘       │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  PATTERN 2: VALIDATION SUMMARY PANEL                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ⚠ 2 issues found                                             │   │
│  │  ┌─────────────────────────────────────────────────────────────┐   │   │
│  │  │                                                            │   │   │
│  │  │ 🔴 ERROR: End date before start date                       │   │   │
│  │  │    Start: May 15, 2025 → End: May 10, 2025                 │   │   │
│  │  │    [Fix now] [Ignore]                                       │   │   │
│  │  │                                                            │   │   │
│  │  │ 🟡 WARNING: Budget seems low                                │   │   │
│  │  │    ₹5,000 for Goa trip (typical: ₹25k-50k)                 │   │   │
│  │  │    [Confirm] [Edit]                                         │   │   │
│  │  │                                                            │   │   │
│  │  │ [Dismiss all] [Fix all errors]                              │   │   │
│  │  └─────────────────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  PATTERN 3: MISSING FIELD INDICATOR                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                     │   │
│  │  Trip completeness: ●●●○○○○○○○ 30%                                │   │
│  │                                                                     │   │
│  │  Required fields missing:                                           │   │
│  │  ┌─────────────────────────────────────────────────────────────┐   │   │
│  │  │ ○ Destination   │ "Planning a trip..." (no destination)     │   │   │
│  │  │ ○ Dates         │ "...in May" (which year? specific dates?) │   │   │
│  │  │ ○ Travelers     │ "...for the family" (how many people?)    │   │   │
│  │  │                                                            │   │   │
│  │  │ Suggested message:                                          │   │   │
│  │  │ "Could you please share:                                     │   │   │
│  │  │  1. Where would you like to go?                             │   │   │
│  │  │  2. Specific travel dates                                    │   │   │
│  │  │  3. Number of travelers"                                      │   │   │
│  │  │                                                            │   │   │
│  │  │ [Send via WhatsApp] [Customize] [Cancel]                     │   │   │
│  │  └─────────────────────────────────────────────────────────────┘   │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Completeness Visualization

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      COMPLETENESS VISUALIZATION                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  OVERVIEW:                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                     │   │
│  │  Packet Complete: 78%                                              │   │
│  │  ████████████████░░░░░░░░                                         │   │
│  │                                                                     │   │
│  │  Ready for decision engine with minor assumptions                   │   │
│  │                                                                     │   │
│  │  ┌─────┬──────┬───────┬───────┬────────┐                          │   │
│  │  │ Dest │ Dates │Budget │Travel.│Prefs  │                          │   │
│  │  │  ✓   │  ⚠   │   ✓   │   ✓   │   ○   │                          │   │
│  │  └─────┴──────┴───────┴───────┴────────┘                          │   │
│  │                                                                     │   │
│  │  Key: ✓ Complete  ⚠ Assumed  ○ Missing  ⊘ Invalid                 │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  DETAILED BREAKDOWN:                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                     │   │
│  │  DESTINATION ████████████████████ 100%                             │   │
│  │  ✓ Location: Goa                                                  │   │
│  │  ✓ Type: Domestic                                                 │   │
│  │  ✓ Region: West India                                             │   │
│  │                                                                     │   │
│  │  DATES ████████████████░░░░░ 70%                                   │   │
│  │  ✓ Month: May                                                     │   │
│  │  ✓ Start day: 15                                                  │   │
│  │  ✓ End day: 20                                                    │   │
│  │  ⚠ Year: Assumed 2025                                             │   │
│  │                                                                     │   │
│  │  TRAVELERS ████████████████████ 100%                               │   │
│  │  ✓ Adults: 4                                                     │   │
│  │  ✓ Children: 0 (explicitly stated "4 adults only")                 │   │
│  │                                                                     │   │
│  │  BUDGET ████████████████████ 100%                                  │   │
│  │  ✓ Amount: ₹80,000                                                │   │
│  │  ✓ Currency: INR                                                  │   │
│  │                                                                     │   │
│  │  PREFERENCES ████████░░░░░░░░░░░ 40%                                │   │
│  │  ✓ Area: North Goa                                                │   │
│  │  ○ Accommodation type: Not specified                              │   │
│  │  ○ Transportation: Not specified                                   │   │
│  │  ○ Activities: Not specified                                       │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Channel-Specific UX

### WhatsApp-Specific Features

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       WHATSAPP-SPECIFIC UX                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  WHATSAPP MESSAGE CONTEXT:                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ┌─────────────────────────────────────────────────────────────┐    │   │
│  │  │ Original WhatsApp Message                                    │    │   │
│  │  ├─────────────────────────────────────────────────────────────┤    │   │
│  │  │ From: +91 98765 43210                                       │    │   │
│  │  │ Time: Today, 2:34 PM                                        │    │   │
│  │  │                                                             │    │   │
│  │  │ "Hi! Planning trip to Goa in May. 4 adults. Budget         │    │   │
│  │  │  around 80k. Want to visit North Goa beaches. Need          │    │   │
│  │  │  3 rooms. Thanks! 🏖️"                                       │    │   │
│  │  │                                                             │    │   │
│  │  │ 📎 Audio note (0:23)  [Play] [Transcribe]                    │    │   │
│  │  │ 📎 Image (screenshot)  [View] [Extract text]                  │    │   │
│  │  └─────────────────────────────────────────────────────────────┘    │   │
│  │                                                                     │   │
│  │  💬 WhatsApp formatting preserved:                                 │   │
│  │  • Emojis indicate tone (🏖️ = vacation excitement)                │   │
│  │  • "Thanks!" indicates politeness, form response appropriate       │   │
│  │  • Short message suggests mobile user, prefer concise replies     │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  QUICK RESPONSE VIA WHATSAPP:                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Send response via WhatsApp:                                        │   │
│  │  ┌─────────────────────────────────────────────────────────────┐   │   │
│  │  │ Hi! Thanks for reaching out! 🙌                              │   │   │
│  │  │ We're excited to help plan your Goa trip!                    │   │   │
│  │  │                                                             │   │   │
│  │  │ Just to confirm: May 2025, correct?                          │   │   │
│  │  │ And any specific hotels you prefer?                          │   │   │
│  │  │                                                             │   │   │
│  │  │ [Edit] [Send] [Schedule for later]                            │   │   │
│  │  └─────────────────────────────────────────────────────────────┘   │   │
│  │                                                                     │   │
│  │  Quick reply buttons for customer:                                 │   │
│  │  ┌──────────┬──────────┬──────────┬──────────┐                    │   │
│  │  │ Yes, May │ Jun 2025 │ 3-star   │ 5-star   │                    │   │
│  │  │ 2025!   │          │ hotel    │ hotel    │                    │   │
│  │  └──────────┴──────────┴──────────┴──────────┘                    │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Email-Specific Features

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         EMAIL-SPECIFIC UX                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  EMAIL THREAD CONTEXT:                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ┌─────────────────────────────────────────────────────────────┐    │   │
│  │  │ Email Thread (3 messages)                                    │    │   │
│  │  ├─────────────────────────────────────────────────────────────┤    │   │
│  │  │                                                             │    │   │
│  │  │ 1. CUSTOMER (Apr 20)                                        │    │   │
│  │  │    "Planning a trip to Goa in May. Please suggest..."        │    │   │
│  │  │                                                             │    │   │
│  │  │ 2. AGENT (Apr 20)                                           │    │   │
│  │  │    "Thanks for your inquiry! We'd be happy to help..."       │    │   │
│  │  │                                                             │    │   │
│  │  │ 3. CUSTOMER (Today) ⬅ CURRENT                                │    │   │
│  │  │    "Great! Here are more details: 4 adults, budget          │    │   │
│  │  │     around 80k, want to visit North Goa beaches..."          │    │   │
│  │  │                                                             │    │   │
│  │  │ [Show full thread]                                           │    │   │
│  │  └─────────────────────────────────────────────────────────────┘    │   │
│  │                                                                     │   │
│  │  📎 Attachments:                                                   │   │
│  │  ┌─────────────────────────────────────────────────────────────┐   │   │
│  │  │ 📄 requirements.pdf (2 pages)  [View] [Extract text]         │   │   │
│  │  │ 🖼️ screenshot.png              [View] [Extract text]         │   │   │
│  │  └─────────────────────────────────────────────────────────────┘   │   │
│  │                                                                     │   │
│  │  💡 Email-specific insights:                                        │   │
│  │  • Customer provided detailed requirements → likely serious buyer   │   │
│  │  • Thread history shows previous engagement → prioritize            │   │
│  │  • Formal tone suggests professional, detailed response needed     │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  EMAIL RESPONSE:                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Draft email response:                                              │   │
│  │  ┌─────────────────────────────────────────────────────────────┐   │   │
│  │  │ Subject: Re: Goa Trip Planning - Itinerary Options           │   │   │
│  │  │                                                             │   │
│  │  │ Dear [Name],                                                │   │   │
│  │  │                                                             │   │   │
│  │  │ Thank you for providing the additional details. Based       │   │   │
│  │  │ on your requirements...                                      │   │   │
│  │  │                                                             │   │   │
│  │  │ [Edit email] [Send] [Schedule]                               │   │   │
│  │  └─────────────────────────────────────────────────────────────┘   │   │
│  │                                                                     │   │
│  │  Response style: ☐ Formal ☐ Semi-formal ☐ Casual                   │   │
│  │  Include: ☐ PDF attachment ☐ Itinerary preview                     │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Mobile Experience

### Mobile-Optimized Panel

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         MOBILE PACKET PANEL                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  VERTICAL STACK FOR MOBILE:                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ┌─────────────────────────────────────────────────────────────┐    │   │
│  │  │ ◀ Goa Family Trip                        [●●●○○] 78%     │    │   │
│  │  │                                           [⋯ Menu]       │    │   │
│  │  │ May 15-20 • 4 adults • ₹80k                              │    │   │
│  │  └─────────────────────────────────────────────────────────────┘    │   │
│  │                                                                     │   │
│  │  ┌─────────────────────────────────────────────────────────────┐    │   │
│  │  │ 📱 Original Message                                   [Expand]│    │   │
│  │  │ "Planning trip to Goa in May. 4 adults. Budget..."          │    │   │
│  │  └─────────────────────────────────────────────────────────────┘    │   │
│  │                                                                     │   │
│  │  ┌─────────────────────────────────────────────────────────────┐    │   │
│  │  │ EXTRACTION [Edit]                                            │    │   │
│  │  ├─────────────────────────────────────────────────────────────┤    │   │
│  │  │ Destination  ● Goa                    ████████░░ 92%        │    │   │
│  │  │ Dates       ⚠ May 15-20              ████░░░░░░ 67%        │    │   │
│  │  │             └─ Year assumed (2025)                          │    │   │
│  │  │ Travelers   ● 4 adults               ████████░░ 89%        │    │   │
│  │  │ Budget      ● ₹80,000                ████████░░ 87%        │    │   │
│  │  └─────────────────────────────────────────────────────────────┘    │   │
│  │                                                                     │   │
│  │  ┌─────────────────────────────────────────────────────────────┐    │   │
│  │  │ ⚠ 1 issue needs attention                                      │    │   │
│  │  │ Year not specified - assumed 2025                             │    │   │
│  │  │ [Confirm] [Request from customer]                             │    │   │
│  │  └─────────────────────────────────────────────────────────────┘    │   │
│  │                                                                     │   │
│  │  ┌─────────────────────────────────────────────────────────────┐    │   │
│  │  │ [Mark Complete]  [Request Info]  [More Options]               │    │   │
│  │  └─────────────────────────────────────────────────────────────┘    │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  MOBILE-SPECIFIC GESTURES:                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  • Swipe right → Mark complete                                     │   │
│  │  • Swipe left  → Request info                                      │   │
│  │  • Long press  → Open context menu                                 │   │
│  │  • Pull down  → Refresh/Check for new messages                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Thumb-Zone Optimization

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       THUMB-ZONE OPTIMIZATION                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PRIMARY ACTIONS (Bottom, easy thumb reach):                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                     │   │
│  │  ┌─────────────────────────────────────────────────────────────┐    │   │
│  │  │                    [Mark Complete]                           │    │   │
│  │  │                    (Green, prominent)                         │    │   │
│  │  └─────────────────────────────────────────────────────────────┘    │   │
│  │                                                                     │   │
│  │  ┌───────────────────────┬───────────────────────┐                  │   │
│  │  │   [Request Info]      │    [Edit Fields]      │                  │   │
│  │  └───────────────────────┴───────────────────────┘                  │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  SECONDARY ACTIONS (Top, requires stretch):                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  [≡ Menu]                                    [Customer Profile]      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  INFORMATION HIERARCHY (Scroll order):                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  1. Critical issues (if any) - at top, collapsible                 │   │
│  │  2. Key extracted fields (destination, dates, budget)               │   │
│  │  3. Confidence indicators (subtle, expandable)                     │   │
│  │  4. Original message (collapsible, below the fold)                 │   │
│  │  5. Validation warnings (collapsible)                              │   │
│  │  6. Customer history (bottom, expandable)                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 9. Implementation Reference

### React Component Structure

```typescript
// Packet Panel Component Structure
interface PacketPanelProps {
  packetId: string;
  mode: 'review' | 'edit' | 'complete';
  onStateChange: (state: PacketState) => void;
}

// Main Panel
function PacketPanel({ packetId, mode, onStateChange }: PacketPanelProps) {
  const { packet, loading, error } = usePacket(packetId);
  const [activeTab, setActiveTab] = useState<'extract' | 'validate' | 'customer'>('extract');

  if (loading) return <ExtractionLoader />;
  if (error) return <ErrorMessage error={error} />;

  return (
    <div className="packet-panel">
      {/* Header */}
      <PacketHeader packet={packet} mode={mode} />

      {/* Tabs */}
      <PacketTabs active={activeTab} onChange={setActiveTab} />

      {/* Content */}
      <div className="packet-content">
        {activeTab === 'extract' && <ExtractionTab packet={packet} />}
        {activeTab === 'validate' && <ValidationTab packet={packet} />}
        {activeTab === 'customer' && <CustomerTab packet={packet} />}
      </div>

      {/* Actions */}
      <PacketActions packet={packet} mode={mode} onAction={onStateChange} />
    </div>
  );
}

// Extraction Tab Component
interface ExtractionTabProps {
  packet: TripPacket;
}

function ExtractionTab({ packet }: ExtractionTabProps) {
  return (
    <div className="extraction-tab">
      {/* Original Message */}
      <OriginalMessageSection message={packet.source.rawMessage} />

      {/* Extracted Fields */}
      <ExtractedFieldsSection
        fields={packet.extracted.fields}
        confidence={packet.extracted.confidence}
        onEdit={handleFieldEdit}
      />

      {/* Source Attribution */}
      <SourceAttributionSection extraction={packet.extracted} />

      {/* Validation Issues */}
      {packet.validated.warnings.length > 0 && (
        <ValidationIssuesSection issues={packet.validated.warnings} />
      )}
    </div>
  );
}

// Confidence Bar Component
interface ConfidenceBarProps {
  value: number;
  label?: string;
  showPercentage?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

function ConfidenceBar({
  value,
  label,
  showPercentage = true,
  size = 'md'
}: ConfidenceBarProps) {
  const color = getConfidenceColor(value);
  const description = getConfidenceLabel(value);

  return (
    <div className={`confidence-bar confidence-bar--${size}`}>
      {label && <span className="confidence-bar__label">{label}</span>}
      <div className="confidence-bar__track">
        <div
          className={`confidence-bar__fill confidence-bar__fill--${color}`}
          style={{ width: `${value * 100}%` }}
          aria-label={`${description} confidence`}
        />
      </div>
      {showPercentage && (
        <span className="confidence-bar__percentage">{Math.round(value * 100)}%</span>
      )}
      <span className={`confidence-bar__indicator confidence-bar__indicator--${color}`}>
        {getConfidenceIcon(value)}
      </span>
    </div>
  );
}

function getConfidenceColor(value: number): 'high' | 'medium' | 'low' {
  if (value >= 0.85) return 'high';
  if (value >= 0.65) return 'medium';
  return 'low';
}

function getConfidenceLabel(value: number): string {
  if (value >= 0.85) return 'High';
  if (value >= 0.65) return 'Medium';
  return 'Low';
}

function getConfidenceIcon(value: number): string {
  if (value >= 0.85) return '✓';
  if (value >= 0.65) return '⚠';
  return '⚠';
}

// Editable Field Component
interface EditableFieldProps {
  field: keyof TripFields;
  value: any;
  confidence: number;
  validation?: FieldValidation;
  onEdit: (field: string, value: any) => void;
}

function EditableField({
  field,
  value,
  confidence,
  validation,
  onEdit
}: EditableFieldProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState(value);

  const handleSave = () => {
    onEdit(field, editValue);
    setIsEditing(false);
  };

  return (
    <div className="editable-field">
      <div className="editable-field__header">
        <Label>{formatFieldName(field)}</Label>
        <ConfidenceBar value={confidence} size="sm" />
      </div>

      {isEditing ? (
        <div className="editable-field__editing">
          <FieldInput
            field={field}
            value={editValue}
            onChange={setEditValue}
            validation={validation}
          />
          <div className="editable-field__actions">
            <Button onClick={handleSave} size="sm">Save</Button>
            <Button onClick={() => setIsEditing(false)} variant="ghost" size="sm">
              Cancel
            </Button>
          </div>
        </div>
      ) : (
        <div
          className="editable-field__display"
          onClick={() => setIsEditing(true)}
        >
          <span className="editable-field__value">{formatFieldValue(value)}</span>
          <Icon name="edit" className="editable-field__edit-icon" />
        </div>
      )}

      {validation?.errors.length > 0 && (
        <ValidationErrors errors={validation.errors} />
      )}
    </div>
  );
}

// Follow-Up Dialog Component
interface FollowUpDialogProps {
  packet: TripPacket;
  missingFields: MissingField[];
  onSend: (channel: MessageChannel, message: string) => void;
}

function FollowUpDialog({ packet, missingFields, onSend }: FollowUpDialogProps) {
  const [channel, setChannel] = useState<MessageChannel>('whatsapp');
  const [message, setMessage] = useState('');
  const [tone, setTone] = useState<'friendly' | 'formal'>('friendly');

  const handleGenerateMessage = () => {
    const generated = generateFollowUpMessage({
      missingFields,
      tone,
      channel,
      customerName: packet.enriched.customer?.name
    });
    setMessage(generated);
  };

  return (
    <Dialog>
      <DialogHeader>
        <DialogTitle>Request Information from Customer</DialogTitle>
      </DialogHeader>

      <DialogContent>
        {/* Missing Fields Summary */}
        <MissingFieldsList fields={missingFields} />

        {/* Channel Selection */}
        <ChannelSelector value={channel} onChange={setChannel} />

        {/* Tone Selection */}
        <ToneSelector value={tone} onChange={setTone} />

        {/* Message Editor */}
        <MessageEditor
          value={message}
          onChange={setMessage}
          onGenerate={handleGenerateMessage}
          placeholder="Select tone and click Generate..."
        />

        {/* Preview */}
        <MessagePreview channel={channel} message={message} />
      </DialogContent>

      <DialogActions>
        <Button variant="ghost" onClick={close}>Cancel</Button>
        <Button onClick={() => onSend(channel, message)}>
          Send via {channel === 'whatsapp' ? 'WhatsApp' : 'Email'}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
```

---

## Summary

The Intake UX/UI design focuses on:

1. **Trust Through Transparency**: Show confidence, sources, and validation clearly
2. **Speed with Accuracy**: AI defaults, easy overrides, one-click fixes
3. **Progressive Disclosure**: Critical info first, reveal complexity on demand
4. **Channel Context**: Preserve message context, enable quick channel-based responses

**Key UX Patterns**:
- Confidence bars with color coding (green/yellow/red)
- Source attribution showing how values were extracted
- Inline editing with smart suggestions
- Validation warnings with actionable fixes
- Follow-up workflows with template messages
- Mobile-optimized with thumb-zone primary actions

**Success Metrics**:
- Review time: Target <30 seconds per packet
- Correction rate: <15% of fields need correction
- Agent satisfaction: >4/5 on UX feedback
- Follow-up response rate: >70% within 24 hours

---

**Next Document:** INTAKE_03_CHANNEL_INTEGRATION_DEEP_DIVE.md — Deep dive into WhatsApp, Email, Web, and Phone integrations
