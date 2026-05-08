# Priority Signal Model Analysis

**Date:** 2026-05-08
**Trigger:** Random Document Audit — D-001/D-003 Implementation Plan
**Question:** What constitutes priority in a travel agency pipeline, and how should it be visualized?
**Status:** Research complete — decision pending.

---

## What Sparked This

The D-001 task removed `CardAccent` (colored left-border bar on cards) as "AI slop pattern #8." The D-003 plan added a WorkspaceTable and view toggle. But the same left-border accent pattern was re-added **inline** in `TripCard.tsx:336-341` — a `<div>` with absolute positioning and a 3px colored bar. And again in `Shell.tsx:201-207` (nav active indicator), `overview/page.tsx:130,242` (error card), and `workbench.module.css:586` (review notes).

The `.impeccable.md` design system bans left-border stripes. The codebase violates its own design system in 4+ places.

But the deeper question: **what were those bars trying to communicate**? And if we remove them, what replaces them?

---

## Research Sources

### 1. IBM Carbon Design System — Status Indicator Pattern
- **Source:** https://carbondesignsystem.com/patterns/status-indicator-pattern/
- **Key finding:** Enterprise systems should use **shape indicators** (colored geometric shape + text label) or **icon indicators** (symbol in colored container). Never rely on color alone.
- **Severity levels:** High (immediate action), Medium (no immediate action), Low (informational)
- **Accessibility:** At least 2 of {color, shape, symbol, text} must be present. WCAG requires 3:1 contrast for non-text elements.
- **Recommendation:** Shape indicators are best for "prioritize tasks" and "show lifecycle phase" in high-scan contexts like inboxes.

### 2. Nielsen Norman Group — Indicators, Validations, Notifications
- **Source:** https://www.nngroup.com/articles/indicators-validations-notifications/
- **Key finding:** Indicators are **conditional** (appear only when relevant), **contextual** (near element), and **passive** (no action required).
- **Methods ranked:** Icon > Typography (bold, color) > Size/Animation
- **Warning:** Overusing indicators creates noise. Only use when the information is important enough to "take up space."

### 3. Eisenhower / Urgent-Important Matrix
- **Source:** Forbes, ProjectManager.com, academic literature on task prioritization
- **Core model:** Priority = Urgency × Importance. A 2-dimensional grid.
- **Urgency:** Time-sensitivity. How soon does this need attention?
- **Importance:** Consequence. How much does this matter if done/not done?
- **Why it matters for travel ops:** A $50k trip leaving next week (high urgency, high importance) is handled very differently from a $2k inquiry 6 months out (low urgency, variable importance). The current model treats them identically if they have the same SLA days.

### 4. Travel Agency Operations Patterns
- **Sources:** Nutshell CRM analysis, Travelopro CRM patterns, travel agency operations literature
- **Pipeline priority factors in travel:**
  - **Revenue/value** — trip price, commission potential
  - **Deadline proximity** — departure date, booking cutoff dates
  - **Customer relationship** — repeat vs new, VIP status, referral source value
  - **Complexity/risk** — multi-city, visa requirements, special needs
  - **Pipeline progress** — how far along the trip is (late-stage is harder to change)
  - **Blocker severity** — missing info, supplier delays, approval needed
  - **SLA compliance** — promised response time, follow-up commitments

---

## Current State: What the Codebase Actually Computes

### InboxTrip priority model (`spine_api/services/inbox_projection.py:364-377`)

```python
priority = "medium"       # DEFAULT
priority_score = 50

# ESCALATE TO HIGH if ANY of:
if sla_status == "at_risk"            # 5+ days in current stage
   or requires_review is True          # needs human review
   or is_valid is False                # validation failed
   or confidence_score < 50:           # AI decision confidence low
    priority = "high"
    priority_score = 75

# ESCALATE TO CRITICAL if ANY of (overrides high):
if sla_status == "breached"           # 8+ days in stage
   or escalation_severity == "critical":  # actively escalated
    priority = "critical"
    priority_score = 90
```

**This is a 1-dimensional urgency model disguised as priority.** Every single input factor feeds into a single axis. A $50k trip with 3 days in stage and a $2k trip with 3 days in stage get the same priority (`medium`). A trip with a breached SLA gets `critical` regardless of whether it's worth $500 or $50,000.

### What the model does NOT consider:
| Missing Factor | Where it lives | Why it matters |
|---|---|---|
| Trip value / revenue | `InboxTrip.value`, `BFF adapter:priorityScore` has unused signal | A $50k trip is more important than a $5k trip |
| Customer history | `trip_priorities` free-text field exists but unused in computation | Repeat VIP needs different attention |
| Lead source quality | `lead_source` field exists on Trip | Referral vs cold lead have different conversion potential |
| Departure date proximity | Not in model (dateWindow exists but free-text) | Trip leaving in 2 weeks is more urgent than 6 months |
| Party complexity | `party_composition` free-text | Family with infants needs more prep than solo |
| Owner priority signals | `owner_priority_signals` exists in schema, not linked to computation | Agent says "this is urgent" should have weight |
| Pipeline stage weight | Stage exists but no weighting for progress | Booking-stage trip has different risk than intake |

### Key bugs found during analysis:

1. **`low` priority is unreachable** — The code defines `low: 25` in the score table but **no code path ever assigns priority = "low"**. Every trip starts at `medium (50)` as the floor.

2. **Frontend/backend scale mismatch** — Frontend checks `confidence < 0.5` (0-1 scale, `bff-trip-adapters.ts:541`). Backend checks `_as_int(decision.get("confidence_score"), 0) < 50` (0-100 scale, `inbox_projection.py:371`). These are semantically the same ONLY if the stored value is 0-100. If the stored value is 0-1, the backend would treat `0.6` as `< 50` and incorrectly escalate. This is a latent bug.

3. **Duplicated priority computation** — Both frontend (`bff-trip-adapters.ts:529-543`) and backend (`inbox_projection.py:364-377`) implement the same algorithm independently. The backend (`/inbox` endpoint, added 2026-05-04) is canonical. The frontend BFF code is a legacy fallback.

4. **Three separate SLA systems** — Inbox day-based SLA (7/4 thresholds in `inbox_projection.py`), routing ownership hour-based SLA (in `sla_service.py`), and pipeline stage SLA hours (in `PipelineStageConfig`). None of them talk to each other.

---

## First-Principles: What Priority Actually Is

Priority is not one number. It's an answer to the question: **"What should I work on next?"**

In a travel agency pipeline, this question has two dimensions:

### Dimension 1: URGENCY — Time sensitivity

| Level | Meaning | Triggered by |
|-------|---------|-------------|
| Critical | Immediate action required, consequences now | SLA breached, departure within days, customer escalation |
| High | Action needed soon, consequences building | SLA at risk, follow-up due soon, pending supplier deadline |
| Normal | Standard processing time available | Within SLA, no pressing deadlines |
| Low | No time pressure | Long lead time, waiting on customer, seasonal planning |

### Dimension 2: IMPORTANCE — Business impact

| Level | Meaning | Triggered by |
|-------|---------|-------------|
| Critical | Top-priority account or deal | VIP client, >$50k value, strategic partner referral |
| High | Significant business impact | High-value trip, repeat customer, tight complexity |
| Normal | Standard transaction | Typical trip, moderate value |
| Low | Low impact | Low-value inquiry, exploratory, not yet qualified |

### Combined: Eisenhower-style 4-quadrant model

```
                IMPORTANCE →
                Low              High
       ┌─────────────────────────────────┐
U    C │  DO NOW (urgent+important)      │
R    r │  ─────────────────────────────  │
G    i │  Critical SLA breach +          │
E    t │  High-value trip.               │
N    i │  Drop everything.               │
C    c │                                 │
Y    a │  DELEGATE (urgent, not imp)     │  SCHEDULE (not urgent, important)
↓    l │  ─────────────────────────     │  ──────────────────────────────
       │  Breached SLA but low-value.    │  High-value trip comfortably
       │  Needs action but not YOU.      │  within SLA. Plan, don't panic.
       │                                 │
       │  DELETE (not urgent, not imp)   │  SCHEDULE (not urgent, important)
       │  ────────────────────────────   │  (same quadrant — two entry points)
       │  Low-value, no deadline.        │
       │  Don't prioritize.              │
       └─────────────────────────────────┘
```

This is the Eisenhower matrix adapted for travel operations. The current model collapses both axes into one score, which means:
- A low-value trip with breached SLA → `critical` (over-prioritized, displaces high-value work)
- A high-value trip comfortably within SLA → `medium` (under-prioritized, risks being forgotten until too late)

---

## Visual Indicator Design Principles

From the research, a good priority indicator in this context should:

1. **Show urgency AND importance** as separable signals (not one number)
2. **Not rely on color alone** — shape or icon must be paired (WCAG, NVDA)
3. **Be contextually relevant** — appear only when there's something to signal (`medium`/`normal` needs no indicator)
4. **Be scannable at a distance** — operators scan 20-50 trips
5. **Be accessible** — text label or tooltip for screen readers
6. **Be a reusable component** — not inline divs in 4+ places

### What the ban means

The `.impeccable.md` ban on left-border stripes is about a specific CSS pattern (`border-left > 1px`). It's not a ban on all visual indicators. The ban exists because:
- Left-border stripes are the #1 most recognizable AI design tell
- They're inaccessible (color-only, no shape/text)
- They waste horizontal space in cards

### Recommended: shape + color (dot/badge) + optional text

IBM Carbon's shape indicator pattern uses a small colored geometric shape (circle, diamond, square) paired with text. This is:
- Scannable (shape stands out in grid of cards)
- Accessible (color + shape, text label)
- Compact (fits in card header or metrics row)
- Reusable (one component, one color mapping)
- Not AI slop (validated enterprise pattern, not border stripe)

---

## Research Documentation

All research sources are cited inline above. Key URLs archived:
- https://carbondesignsystem.com/patterns/status-indicator-pattern/
- https://www.nngroup.com/articles/indicators-validations-notifications/
- Various Forbes/ProjectManager.com on Eisenhower Matrix

---

## Questions for Decision

1. **Should priority become 2-dimensional (urgency × importance)?** This changes the backend computation, the frontend type, the filter UI, the sort logic, and the visual indicator. It's a significant change — but the current 1D model is wrong.

2. **Or should we keep 1D priority but improve the indicator and fix the model gaps?** Fix the unreachable `low` tier, add value-based weighting, fix the confidence score scale mismatch, consolidate frontend/backend computation.

3. **For the visual indicator, which pattern?**
   - **Priority dot** (shape + color, no text unless hovered) — most compact
   - **Priority badge** (colored pill with text like "HIGH") — most accessible
   - **Eisenhower mini-matrix** (shows both urgency and importance visually) — most informative
   - **Remove entirely** (status is already in badges, as D-001 argued) — simplest

This analysis is saved at `Docs/PRIORITY_SIGNAL_MODEL_ANALYSIS_2026-05-08.md` for future reference.
