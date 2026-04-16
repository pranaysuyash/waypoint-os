# UX Terminology Audit & Translation Guide

**Date**: 2026-04-15  
**Status**: Critical Issue - User-Unfriendly Language  
**Priority**: P0 - Blocking UX Problem  

---

## Problem Statement

The current frontend uses engineering/internal jargon throughout the interface:
- **NB01, NB02, NB03, NB04, NB05** - Internal pipeline stage codes
- **Packet** - Opaque term for structured trip data
- **Spine** - Internal system name
- **Scenario** - Generic term instead of industry-standard "Trip" or "Booking"

**Impact**: Travel agency operators don't understand the interface. They won't use a product that speaks a language they don't know.

---

## Terminology Mapping

### Pipeline Stages (Current → Target)

| Code | Current Label | Current Description | Target Label | Target Description | Rationale |
|------|---------------|---------------------|--------------|-------------------|-----------|
| NB01 | **Intake** | Parse Input | **New Inquiry** | Capture customer request | "Inquiry" is what agents call incoming leads |
| NB02 | **Packet** | Extract Facts | **Trip Details** | Extract trip information | "Trip" is industry standard |
| NB03 | **Decision** | Validate & Decide | **Ready to Quote?** | Check if ready to price | Poses the actual question |
| NB04 | **Strategy** | Build Bundles | **Build Options** | Create travel options | "Options" is what agents present |
| NB05 | **Safety** | Final Check | **Final Review** | Last check before send | Clear action-oriented name |

### Core Concepts

| Engineering Term | Industry Term | Usage Context |
|------------------|---------------|---------------|
| Packet | **Booking Request** | The structured trip data |
| Scenario | **Trip** or **Booking** | Individual customer request |
| Raw Note | **Customer Message** | Original inquiry text |
| Owner Note | **Agent Notes** | Internal agent comments |
| Spine Run | **Process Trip** | Execute the analysis |
| Workbench | **Trip Pipeline** | Main working area |
| Intake | **New Leads** | Incoming inquiries tab |
| Decision | **Quote Status** | Decision state display |

### Decision States (Current → Target)

| Current State | Target Label | Color | Rationale |
|---------------|--------------|-------|-----------|
| PROCEED_TRAVELER_SAFE | ✅ **Ready to Book** | Green | Clear, actionable |
| PROCEED_INTERNAL_DRAFT | ⏸️ **Draft Quote** | Amber | Indicates status |
| BRANCH_OPTIONS | 🔀 **Needs Options** | Amber | Clear what to do |
| STOP_NEEDS_REVIEW | ⚠️ **Needs Attention** | Red | Urgent, needs action |
| ASK_FOLLOWUP | ❓ **Need More Info** | Blue | Indicates missing info |

---

## Files Requiring Changes

### Frontend Source Files

```
frontend/src/
├── app/workbench/
│   ├── page.tsx                    # Pipeline labels, button text
│   ├── IntakeTab.tsx               # Tab label, form labels
│   ├── PacketTab.tsx               # Tab label, table headers
│   ├── DecisionTab.tsx             # Tab label, state labels
│   ├── StrategyTab.tsx             # Tab label
│   └── SafetyTab.tsx               # Tab label
│
├── components/layouts/
│   └── Shell.tsx                   # Navigation labels
│
├── components/visual/
│   └── PipelineFlow.tsx            # Stage labels (NB01→NB05)
│
└── stores/
    └── workbenchStore.ts           # UI labels (keep code names)
```

### Documentation Files

```
Docs/
├── ARCHITECTURE.md                 # Concept explanations
├── CURRENT_STATE.md                # Feature descriptions
└── DESIGN.md                       # UI terminology
```

---

## Implementation Guidelines

### Rule 1: Code Names Stay, UI Changes

**Keep in code** (internal references):
- `NB01`, `NB02`, etc. in state management
- `spine.run()` API calls
- `packet` in data models
- `scenario` in database schemas

**Change in UI** (user-facing):
- All labels, headings, buttons
- Navigation items
- Status badges
- Tooltips and help text

### Rule 2: Context Matters

Same code concept, different UI labels:
- In pipeline visualization → "New Inquiry", "Trip Details"
- In status badge → "Ready to Book"
- In navigation → "New Leads"

### Rule 3: Test Against User Mental Model

Ask: "Would a travel agency owner understand this without training?"

**Good**: "Process Trip" (verb + noun, clear action)  
**Bad**: "Spine Run" (technical jargon)

---

## Examples of Changes

### Example 1: Pipeline Visualization

**Before**:
```
NB01 → NB02 → NB03 → NB04 → NB05
Intake  Packet  Decision  Strategy  Safety
```

**After**:
```
New Inquiry → Trip Details → Ready to Quote? → Build Options → Final Review
```

### Example 2: Status Badge

**Before**:
```
🔵 ASK_FOLLOWUP
```

**After**:
```
❓ Need More Info
```

### Example 3: Button

**Before**:
```
▶️ Run Spine
```

**After**:
```
▶️ Process Trip
```

### Example 4: Navigation

**Before**:
```
Dashboard | Inbox | Workbench | Reviews | Insights
```

**After**:
```
Dashboard | New Leads | Trip Pipeline | Pending Reviews | Analytics
```

---

## Acceptance Criteria

1. [ ] No "NB01-NB05" visible in UI (only in code)
2. [ ] No "Packet" visible in UI
3. [ ] No "Spine" visible in UI
4. [ ] No "Scenario" visible in UI (use "Trip" or "Booking")
5. [ ] All decision states show clear, actionable labels
6. [ ] Pipeline stages use travel industry terminology
7. [ ] Navigation uses terms agents recognize
8. [ ] Tooltips explain any necessary technical concepts

---

## Review Checklist

Before submitting for user review:

- [ ] Read every label aloud - does it sound natural?
- [ ] Ask: "Would my travel agent understand this?"
- [ ] Check that code references remain unchanged
- [ ] Verify no broken functionality
- [ ] Test all tab navigation
- [ ] Verify status badges display correctly
- [ ] Check mobile view labels aren't truncated

---

## Related Documents

- DESIGN.md - Visual design system
- ARCHITECTURE.md - Component structure
- Docs/PROJECT_NAMING_EXPLORATION.md - Product naming (Waypoint OS)

---

## Next Steps

1. Delegate implementation to subagent
2. Subagent reviews all changes
3. Present to user for final review
4. Commit and push
