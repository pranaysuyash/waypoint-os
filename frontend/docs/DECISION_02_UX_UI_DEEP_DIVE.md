# DECISION_02_UX_UI_DEEP_DIVE.md

## Decision Engine & Strategy System — UX/UI Deep Dive

> Comprehensive exploration of decision panel visualization, state indicators, and human-AI collaboration interfaces

---

## Table of Contents

1. [Design Philosophy](#design-philosophy)
2. [Decision Panel Architecture](#decision-panel-architecture)
3. [State Visualization System](#state-visualization-system)
4. [Confidence Display Patterns](#confidence-display-patterns)
5. [Recommendation Presentation](#recommendation-presentation)
6. [Override & Correction UX](#override-correction-ux)
7. [Decision History Timeline](#decision-history-timeline)
8. [Responsive & Adaptive Behavior](#responsive-adaptive-behavior)
9. [Accessibility Considerations](#accessibility-considerations)
10. [Animation & Motion Design](#animation-motion-design)
11. [Component Reference](#component-reference)

---

## 1. Design Philosophy

### Core Principles

```
┌─────────────────────────────────────────────────────────────────┐
│                    DECISION UX PHILOSOPHY                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. TRANSPARENT AI                                              │
│     ┌────────────────────────────────────────┐                  │
│     │ Every decision has a "Why" button      │                  │
│     │ Confidence scores are always visible   │                  │
│     │ Uncertainty is admitted, not hidden    │                  │
│     └────────────────────────────────────────┘                  │
│                                                                  │
│  2. HUMAN-IN-CONTROL                                            │
│     ┌────────────────────────────────────────┐                  │
│     │ AI suggests, human decides             │                  │
│     │ One-click override always available    │                  │
│     │ Overrides teach the system             │                  │
│     └────────────────────────────────────────┘                  │
│                                                                  │
│  3. PROGRESSIVE DISCLOSURE                                      │
│     ┌────────────────────────────────────────┐                  │
│     │ Start with conclusion, drill to detail │                  │
│     │ Novices see summary, experts see all   │                  │
│     │ Complexity unfolds on demand           │                  │
│     └────────────────────────────────────────┘                  │
│                                                                  │
│  4. ACTION-ORIENTED                                             │
│     ┌────────────────────────────────────────┐                  │
│     │ Every insight has a clear next action  │                  │
│     │ Decisions are not just displayed       │                  │
│     │ They enable work, not just inform      │                  │
│     └────────────────────────────────────────┘                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### The Trust Equation

```
                    TRUST = TRANSPARENCY × CONSISTENCY
                              ──────────────────────
                                    CONTROL

Where:
  TRANSPARENCY = How clearly the AI explains its reasoning
  CONSISTENCY  = How predictable and reliable the AI behaves
  CONTROL      = How much the human can override and guide

Low Control    → Suspicion, even if accurate
No Transparency → Black box anxiety
Inconsistent   → Learned helplessness
```

---

## 2. Decision Panel Architecture

### Panel Layout

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         DECISION PANEL                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  HEADER: Trip State & Confidence                                │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │    │
│  │  │ NEEDS REVIEW │  │  73% Conf    │  │ 🟢 Low Risk  │          │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘          │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  ┌───────────────────────────────────────┐ ┌─────────────────────────┐  │
│  │  AI RECOMMENDATION                    │ │  QUICK ACTIONS         │  │
│  │  ┌─────────────────────────────────┐  │ │  ┌───────────────────┐ │  │
│  │  │ Send Quote                       │  │ │  │ ✓ Approve & Send  │ │  │
│  │  │ The customer is ready to buy.    │  │ │  ├───────────────────┤ │  │
│  │  │ 89% probability of conversion.   │  │ │  │ ✏ Edit & Adjust  │ │  │
│  │  │                                  │  │ │  ├───────────────────┤ │  │
│  │  │ [Why?] [View Data] [Override]    │  │ │  │ ⏸ Defer Decision  │ │  │
│  │  └─────────────────────────────────┘  │ │  └───────────────────┘ │  │
│  └───────────────────────────────────────┘ └─────────────────────────┘  │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  DECISION BREAKDOWN (Expandable)                                 │    │
│  │  ┌───────────────────────────────────────────────────────────┐  │    │
│  │  │ 📊 COMPLETENESS ━━━━━━━━━━━━━━━━━━━━━ 85%                 │  │    │
│  │  │     ✓ Destination  ✓ Dates  ✓ Travelers  ⚠ Budget        │  │    │
│  │  ├───────────────────────────────────────────────────────────┤  │    │
│  │  │ 🎯 CONFIDENCE ━━━━━━━━━━━━━━━━━━━━━ 73%                   │  │    │
│  │  │     High intent signals, clear timeline                   │  │    │
│  │  ├───────────────────────────────────────────────────────────┤  │    │
│  │  │ ⚡ URGENCY ━━━━━━━━━━━━━━━━━━━━━ 60%                      │  │    │
│  │  │     Travel dates in 6 weeks                              │  │    │
│  │  ├───────────────────────────────────────────────────────────┤  │  │
│  │  │ ⚠️ RISK ━━━━━━━━━━━━━━━━━━━━━ 23%                         │  │    │
│  │  │     Budget range within market norms                      │  │    │
│  │  └───────────────────────────────────────────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  REASONING EXPLAINER (Click "Why?" to expand)                    │    │
│  │  ┌───────────────────────────────────────────────────────────┐  │    │
│  │  │ Top factors influencing this decision:                    │  │    │
│  │  │                                                            │  │    │
│  │  │ 1. 🔥 HIGH ENGAGEMENT                                     │  │    │
│  │  │    • Customer responded within 2 hours                    │  │    │
│  │  │    • Asked specific questions about itinerary             │  │    │
│  │  │    • Opened 3 previous emails                             │  │    │
│  │  │                                                            │  │    │
│  │  │ 2. ✅ COMPLETE INFORMATION                               │  │    │
│  │  │    • All required fields present                          │  │    │
│  │  │    • No ambiguous dates or destinations                   │  │    │
│  │  │                                                            │  │    │
│  │  │ 3. 📅 FAVORABLE TIMING                                   │  │    │
│  │  │    • 6 weeks lead time = optimal conversion window         │  │    │
│  │  │    • No holiday conflicts                                 │  │    │
│  │  │                                                            │  │    │
│  │  │ 4. ⚠️ ONE CONCERN                                        │  │    │
│  │  │    • Budget is 15% above typical for this route           │  │    │
│  │  │    • May indicate unrealistic expectations                │  │    │
│  │  │    → Suggestion: Confirm budget flexibility first          │  │    │
│  │  └───────────────────────────────────────────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  DECISION HISTORY                                                │    │
│  │  ┌───────────────────────────────────────────────────────────┐  │    │
│  │  │ 2h ago  │ State changed to PRICE_REQUEST_RECEIVED         │  │    │
│  │  │ 5h ago  │ AI suggested: Request budget confirmation        │  │    │
│  │  │         │ Agent approved: Override → Sent quote instead    │  │    │
│  │  │ 1d ago  │ State changed to INQUIRY_RECEIVED               │  │    │
│  │  └───────────────────────────────────────────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Panel States

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         PANEL STATE VARIATIONS                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  1. HIGH CONFIDENCE RECOMMENDATION                                      │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  ✅ SEND QUOTE NOW                                              │    │
│  │  All signals positive. 94% conversion probability.              │    │
│  │  ┌───────────────────────────────────────────────────────────┐ │    │
│  │  │ [Send Quote] [Override]                     Strong │    │
│  │  └───────────────────────────────────────────────────────────┘ │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  2. MEDIUM CONFIDENCE — NEEDS INPUT                                     │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  ⚠️ REQUEST BUDGET CONFIRMATION                                  │    │
│  │  Budget is unclear. 67% confidence.                             │    │
│  │  ┌───────────────────────────────────────────────────────────┐ │    │
│  │  │ [Ask Budget] [Send Anyway] [Override]        Medium │    │
│  │  └───────────────────────────────────────────────────────────┘ │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  3. LOW CONFIDENCE — HUMAN DECISION NEEDED                              │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  🔍 REQUIRES REVIEW                                             │    │
│  │  Conflicting signals. AI cannot decide.                        │    │
│  │  ┌───────────────────────────────────────────────────────────┐ │    │
│  │  │ [Review Details] [Mark as Reviewed]        Low │    │
│  │  └───────────────────────────────────────────────────────────┘ │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  4. RISK FLAGGED                                                        │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  ⚠️ BUDGET EXCEEDS THRESHOLD                                     │    │
│  │  Requested ₹5L for typical ₹2L trip. Manual approval needed.    │    │
│  │  ┌───────────────────────────────────────────────────────────┐ │    │
│  │  │ [Approve Anyway] [Reject] [Negotiate]        Risk │    │
│  │  └───────────────────────────────────────────────────────────┘ │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. State Visualization System

### Trip State Indicators

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       STATE VISUALIZATION TAXONOMY                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  STATE FAMILIES                                                          │
│  ┌────────────────────────────────────────────────────────────────┐     │
│  │                                                                  │     │
│  │  🟢 ACTIVE FLOW (Progressing normally)                           │     │
│  │  ├─ INQUIRY_RECEIVED         → 🔵 Blue circle                   │     │
│  │  ├─ PRICE_REQUEST_RECEIVED   → 🔵 Blue circle with ring         │     │
│  │  ├─ INFORMATION_GATHERING    → 🔄 Blue spinning ring            │     │
│  │  ├─ QUOTE_PREPARATION        → 📝 Blue document icon            │     │
│  │  ├─ QUOTE_SENT               → ✉️ Blue sent icon                │     │
│  │  ├─ NEGOTIATION_ACTIVE       → 💬 Blue chat bubbles             │     │
│  │  └─ AWAITING_CUSTOMER_DECISION → ⏸️ Blue pause icon            │     │
│  │                                                                  │     │
│  │  🟡 DECISION POINT (Needs human input)                           │     │
│  │  ├─ NEEDS_REVIEW             → ⚠️ Yellow triangle              │     │
│  │  ├─ AWAITING_OVERRIDE        → 🤔 Yellow thinking face          │     │
│  │  ├─ BUDGET_CONFIRMATION      → 💰 Yellow coins                  │     │
│  │  └─ CUSTOMER_RESPONSE_DUE    → ⏰ Yellow clock                  │     │
│  │                                                                  │     │
│  │  🔴 BLOCKED / RISK (Cannot proceed)                              │     │
│  │  ├─ BUDGET_EXCEEDED          → 🚫 Red circle with slash         │     │
│  │  ├─ COMPLIANCE_REVIEW        → ⚖️ Red scales                    │     │
│  │  ├─ PAYMENT_ISSUE            → 💳 Red card                      │     │
│  │  └─ MANUAL_INTERVENTION      → 👤 Red person icon               │     │
│  │                                                                  │     │
│  │  🟢 SUCCESS STATES (Positive outcomes)                            │     │
│  │  ├─ QUOTE_ACCEPTED           → ✅ Green checkmark               │     │
│  │  ├─ BOOKING_CONFIRMED        → 🎫 Green ticket                  │     │
│  │  ├─ PAYMENT_RECEIVED         → 💵 Green money bag               │     │
│  │  └─ COMPLETED                → 🏁 Green flag                    │     │
│  │                                                                  │     │
│  │  ⚫ TERMINAL STATES (Journey ended)                              │     │
│  │  ├─ CANCELLED                → ⛔ Black stop sign               │     │
│  │  ├─ LOST                     → ❌ Grey X                        │     │
│  │  ├─ ARCHIVED                 → 📦 Brown box                     │     │
│  │  └─ DUPLICATE                → 🔀 Grey merge icon               │     │
│  │                                                                  │     │
│  └────────────────────────────────────────────────────────────────┘     │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### State Transition Visualization

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       STATE TRANSITION FLOW                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│    INQUIRY                                                              │
│       │                                                                 │
│       ▼                                                                 │
│    ┌─────────┐                                                          │
│    │  🔵    │ ← START                                                   │
│    │Received│                                                          │
│    └────┬────┘                                                          │
│         │                                                                │
│         ├──────────────────────┐                                        │
│         ▼                      ▼                                        │
│    ┌─────────┐          ┌──────────┐                                   │
│    │  🔵    │          │  🟡     │ ← Missing info                       │
│    │Price   │          │Needs    │                                     │
│    │Request │          │Review   │                                     │
│    └────┬────┘          └────┬─────┘                                     │
│         │                     │                                          │
│         ▼                     │                                          │
│    ┌─────────┐                │                                          │
│    │  🔄    │                │                                          │
│    │Info    │                │                                          │
│    │Gathering│               │                                          │
│    └────┬────┘                │                                          │
│         │                     │                                          │
│         ▼                     │                                          │
│    ┌─────────┐                │                                          │
│    │  📝    │                │                                          │
│    │Quote   │                │                                          │
│    │Prep    │                │                                          │
│    └────┬────┘                │                                          │
│         │                     │                                          │
│         ▼                     │                                          │
│    ┌─────────┐                │                                          │
│    │  ✉️    │                │                                          │
│    │Quote   │                │                                          │
│    │Sent    │                │                                          │
│    └────┬────┘                │                                          │
│         │                     │                                          │
│    ┌────┴────┐                │                                          │
│    ▼         ▼                ▼                                          │
│ ┌───────┐ ┌───────┐     ┌──────────┐                                    │
│ │ ⏸️   │ │ 💬   │     │  ⏰     │                                    │
│ │Await │ │Negotia│     │Response │                                    │
│ │Decision│ │tion   │     │   Due   │                                    │
│ └───┬───┘ └───┬───┘     └────┬─────┘                                    │
│     │        │               │                                           │
│     └────────┴───────────────┘                                           │
│                  │                                                       │
│                  ▼                                                       │
│           ┌─────────────┐                                                │
│           │   ✅       │ ← POSITIVE PATH                                │
│           │  Accepted  │                                                │
│           └──────┬──────┘                                                │
│                  │                                                       │
│                  ▼                                                       │
│           ┌─────────────┐                                                │
│           │   🎫       │                                                │
│           │  Booked     │                                                │
│           └──────┬──────┘                                                │
│                  │                                                       │
│                  ▼                                                       │
│           ┌─────────────┐                                                │
│           │   💵       │                                                │
│           │  Paid       │                                                │
│           └──────┬──────┘                                                │
│                  │                                                       │
│                  ▼                                                       │
│           ┌─────────────┐                                                │
│           │   🏁       │                                                │
│           │  Completed  │                                                │
│           └─────────────┘                                                │
│                                                                          │
│    NEGATIVE PATH (from any state)                                        │
│    ┌─────────┐ ┌─────────┐ ┌─────────┐                                  │
│    │  🚫   │ │  ⛔   │ │  ❌   │                                  │
│    │Blocked │ │Cancelled│ │  Lost   │                                  │
│    └─────────┘ └─────────┘ └─────────┘                                  │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Compact State Display

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        COMPACT STATE VARIANTS                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  1. BREADCRUMB STYLE (For journey overview)                              │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │ Inquiry │ Price │ Quote │ Sent │ Decision │ Booking │ Complete  │    │
│  │    ✅   │   ✅   │   ✅   │  ✅  │    ⏸    │    ⏸   │    ⏸     │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  2. STEPPER STYLE (For multi-stage processes)                            │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                                                                  │    │
│  │    ┌─────┐     ┌─────┐     ┌─────┐     ┌─────┐     ┌─────┐      │    │
│  │    │  1  │ ──▶ │  2  │ ──▶ │  3  │ ──▶ │  4  │ ──▶ │  5  │      │    │
│  │    │ ✅  │     │ ✅  │     │ 🔄  │     │ ⏸  │     │ ⏸  │      │    │
│  │    └─────┘     └─────┘     └─────┘     └─────┘     └─────┘      │    │
│  │    Inquiry    Gathering   Quote      Sent      Decision          │    │
│  │                                                                  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  3. MINIMAL BADGE (For card lists)                                       │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                                                                  │    │
│  │  ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐  │    │
│  │  │  🔵 In Review  │   │ ⚠️ Budget Conf  │   │ ✅ Ready Book   │  │    │
│  │  └─────────────────┘   └─────────────────┘   └─────────────────┘  │    │
│  │                                                                  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  4. STATUS PILL (For headers)                                            │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                                                                  │    │
│  │  ┌──────────────────────────────────────────────────────────┐   │    │
│  │  │ 🔄 Quote Preparation • Last updated 2h ago by AI        │   │    │
│  │  └──────────────────────────────────────────────────────────┘   │    │
│  │                                                                  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Confidence Display Patterns

### Confidence Score Visualization

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      CONFIDENCE DISPLAY PATTERNS                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  1. LINEAR PROGRESS BAR (Standard)                                       │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  Confidence                                                       │    │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  73%                  │    │
│  │  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░    │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  2. SEMICIRCLE GAUGE (Compact, dashboard-style)                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                                                                  │    │
│  │        ╭──────────────────╮                                      │    │
│  │      ╭╭╮              ╰╰╮                                            │    │
│  │      │││    73%       │││     ← Confidence                         │    │
│  │      ╰╰╯              ╭╭╯                                            │    │
│  │        ╰──────────────────╯                                      │    │
│  │              Medium                                                │    │
│  │                                                                  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  3. CONFIDENCE PILLS (Quick scan, mobile-friendly)                       │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                                                                  │    │
│  │  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐          │    │
│  │  │   🟢 High    │  │  🟡 Medium   │  │   🔴 Low     │          │    │
│  │  │    85%+      │  │   50-84%     │  │    <50%      │          │    │
│  │  └───────────────┘  └───────────────┘  └───────────────┘          │    │
│  │                                                                  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  4. DETAILED METER (With confidence intervals)                           │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  Confidence Score                                                  │    │
│  │                                                                  │    │
│  │  ┌────────────────────────────────────────────────────────┐     │    │
│  │  │ 0%    25%    50%    75%   100%                         │     │    │
│  │  │ ├──────┼──────┼──────┼──────┤                          │     │    │
│  │  │        ┌────────────┐                                   │     │    │
│  │  │        │    ╱╲      │  ← Point estimate: 73%            │     │    │
│  │  │        │   ╱  ╲     │                                   │     │    │
│  │  │        │  ╱    ╲    │                                   │     │    │
│  │  │        └────────┘    │                                   │     │    │
│  │  │        68%       78%  ← 95% confidence interval          │     │    │
│  │  └────────────────────────────────────────────────────────┘     │    │
│  │                                                                  │    │
│  │  Most likely: 73% • Range: 68-78%                               │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Confidence Threshold Indicators

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    CONFIDENCE THRESHOLD BEHAVIOR                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ≥ 90%: AUTOMATE (Strong Confidence)                                     │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                                                                  │    │
│  │   ┌───────────────────────────────────────────────────────┐     │    │
│  │   │ ✅ AUTO-APPROVED                                       │     │    │
│  │   │                                                        │     │    │
│  │   │ Action completed automatically.                        │     │    │
│  │   │ Undo available in decision history.                    │     │    │
│  │   └───────────────────────────────────────────────────────┘     │    │
│  │                                                                  │    │
│  │   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  94%                │    │
│  │                                                                  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  70-89%: RECOMMEND (Medium Confidence)                                   │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                                                                  │    │
│  │   ┌───────────────────────────────────────────────────────┐     │    │
│  │   │ 💡 RECOMMENDED                                         │     │    │
│  │   │                                                        │     │    │
│  │   │ AI suggests this action. Review before proceeding.     │     │    │
│  │   │                                                        │     │    │
│  │   │ [Approve] [Override]                                   │     │    │
│  │   └───────────────────────────────────────────────────────┘     │    │
│  │                                                                  │    │
│  │   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  73%                │    │
│  │                                                                  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  50-69%: CAUTION (Low Confidence)                                       │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                                                                  │    │
│  │   ┌───────────────────────────────────────────────────────┐     │    │
│  │   │ ⚠️ REVIEW REQUIRED                                      │     │    │
│  │   │                                                        │     │    │
│  │   │ Confidence is low. Human review recommended.           │     │    │
│  │   │                                                        │     │    │
│  │   │ [Review Details] [Proceed Anyway]                      │     │    │
│  │   └───────────────────────────────────────────────────────┘     │    │
│  │                                                                  │    │
│  │   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  58%                │    │
│  │                                                                  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  < 50%: BLOCKED (Insufficient Confidence)                                │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                                                                  │    │
│  │   ┌───────────────────────────────────────────────────────┐     │    │
│  │   │ 🚫 CANNOT AUTOMATE                                     │     │    │
│  │   │                                                        │     │    │
│  │   │ Confidence too low. Manual decision required.         │     │    │
│  │   │                                                        │     │    │
│  │   │ [Review Full Context]                                  │     │    │
│  │   └───────────────────────────────────────────────────────┘     │    │
│  │                                                                  │    │
│  │   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  42%                │    │
│  │                                                                  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Recommendation Presentation

### Recommendation Card Structure

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     RECOMMENDATION CARD ANATOMY                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓  │    │
│  │  ┃                                                               │    │
│  │  ┃  [ICON]  PRIMARY RECOMMENDATION                              │    │
│  │  ┃   💡                                                          │    │
│  │  ┃                                                               │    │
│  │  ┃  Send Quote Now                                              │    │
│  │  ┃                                                               │    │
│  │  ┃  Brief explanation of why this action is recommended.        │    │
│  │  ┃  One sentence, clear and actionable.                         │    │
│  │  ┃                                                               │    │
│  │  ┃  ┌──────────────────────────────────────────────────────┐   │    │
│  │  ┃  │  73% Confidence • 89% Conversion Probability         │   │    │
│  │  ┃  └──────────────────────────────────────────────────────┘   │    │
│  │  ┃                                                               │    │
│  │  ┃  ┌────────────┐  ┌────────────┐  ┌────────────┐            │    │
│  │  ┃  │  📎 Send   │  │  ✏ Edit    │  │  ⏸ Defer   │            │    │
│  │  ┃  │    Quote   │  │            │  │            │            │    │
│  │  ┃  └────────────┘  └────────────┘  └────────────┘            │    │
│  │  ┃                                                               │    │
│  │  ┃  ┌─────────────────────────────────────────────────────┐    │    │
│  │  ┃  │ 💬 "Why?"  │  📊 "Data"  │  🔄 "Override"           │    │    │
│  │  ┃  └─────────────────────────────────────────────────────┘    │    │
│  │  ┃                                                               │    │
│  │  ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  CARD VARIATIONS                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                                                                  │    │
│  │  HIGH URGENCY PRIORITY                                           │    │
│  │  ┌──────────────────────────────────────────────────────────┐   │    │
│  │  │ 🔴 URGENT: Customer response due today                    │   │    │
│  │  │                                                            │   │    │
│  │  │ Follow up before opportunity closes.                       │   │    │
│  │  │                                                            │   │    │
│  │  │ [Send Follow-up]                                          │   │    │
│  │  └──────────────────────────────────────────────────────────┘   │    │
│  │                                                                  │    │
│  │  ALTERNATIVE OPTIONS                                             │    │
│  │  ┌──────────────────────────────────────────────────────────┐   │    │
│  │  │ Other actions to consider:                                 │   │    │
│  │  │                                                            │   │    │
│  │  │ ◦ Request budget confirmation (67% confidence)            │   │    │
│  │  │ ◦ Send itinerary preview (54% confidence)                 │   │    │
│  │  │ ◦ Schedule callback (48% confidence)                      │   │    │
│  │  │                                                            │   │    │
│  │  │ [View All Options]                                       │   │    │
│  │  └──────────────────────────────────────────────────────────┘   │    │
│  │                                                                  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Multi-Option Presentation

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       MULTI-OPTION DISPLAY                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  When multiple actions are viable:                                       │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  RECOMMENDED ACTIONS (Ranked by confidence)                      │    │
│  │                                                                   │    │
│  │  ┌────────────────────────────────────────────────────────────┐  │    │
│  │  │                                                             │  │    │
│  │  │  1️⃣  SEND QU NOW — RECOMMENDED                            │  │    │
│  │  │      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  89%         │  │    │
│  │  │      High engagement. Customer responded within 2 hours.    │  │    │
│  │  │                                                             │  │    │
│  │  │      [Send Quote] [Learn More]                             │  │    │
│  │  │                                                             │  │    │
│  │  ├────────────────────────────────────────────────────────────┤  │    │
│  │  │                                                             │  │    │
│  │  │  2️⃣  SEND ITINERARY PREVIEW                                │  │    │
│  │  │      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  67%         │  │    │
│  │  │      Customer has viewed itinerary 3 times.                │  │    │
│  │  │                                                             │  │    │
│  │  │      [Send Preview] [Learn More]                           │  │    │
│  │  │                                                             │  │    │
│  │  ├────────────────────────────────────────────────────────────┤  │    │
│  │  │                                                             │  │    │
│  │  │  3️⃣  REQUEST BUDGET CONFIRMATION                           │  │    │
│  │  │      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  54%         │  │    │
│  │  │      Budget range is wide. Narrow down first.              │  │    │
│  │  │                                                             │  │    │
│  │  │      [Ask Budget] [Learn More]                             │  │    │
│  │  │                                                             │  │    │
│  │  └────────────────────────────────────────────────────────────┘  │    │
│  │                                                                   │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Override & Correction UX

### Override Mechanism

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          OVERRIDE FLOW                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  1. OVERRIDE TRIGGER                                                     │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                                                                  │    │
│  │   AI Recommendation: Send Quote Now (89% confidence)             │    │
│  │                                                                  │    │
│  │   [Send Quote] [Edit & Adjust] [Override]                       │    │
│  │                                                                  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                │                                          │
│                                ▼                                          │
│  2. OVERRIDE MODAL                                                      │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  ┌───────────────────────────────────────────────────────────┐ │    │
│  │  │  Override AI Decision                                     │ │    │
│  │  │  ─────────────────────────────────                       │ │    │
│  │  │                                                           │ │    │
│  │  │  AI suggested: Send Quote Now                             │ │    │
│  │  │                                                           │ │    │
│  │  │  What would you like to do instead?                      │ │    │
│  │  │                                                           │ │    │
│  │  │  ┌────────────────────────────────────────────────────┐  │ │    │
│  │  │  │ ◉ Choose a different action                        │  │ │    │
│  │  │  │ ○ Modify the current action                        │  │ │    │
│  │  │  │ ○ Skip for now                                      │  │ │    │
│  │  │  │ ○ Block this suggestion for this trip              │  │ │    │
│  │  │  └────────────────────────────────────────────────────┘  │ │    │
│  │  │                                                           │ │    │
│  │  │  Alternative Action:                                     │ │    │
│  │  │  ┌────────────────────────────────────────────────────┐  │ │    │
│  │  │  │ [Select Action ▼]                                   │  │    │
│  │  │  │   • Request budget confirmation                     │  │    │
│  │  │  │   • Send itinerary preview                          │  │    │
│  │  │  │   • Schedule callback                               │  │    │
│  │  │  │   • Defer decision                                  │  │    │
│  │  │  │   • Custom...                                       │  │    │
│  │  │  └────────────────────────────────────────────────────┘  │ │    │
│  │  │                                                           │ │    │
│  │  │  Help us improve (optional):                            │  │    │
│  │  │  ┌────────────────────────────────────────────────────┐  │ │    │
│  │  │  │ Why are you overriding?                             │  │    │
│  │  │  │ ◉ I know the customer better                       │  │    │
│  │  │  │ ○ AI missed important context                      │  │    │
│  │  │  │ ○ Timing isn't right                               │  │    │
│  │  │  │ ○ Other reason                                     │  │    │
│  │  │  └────────────────────────────────────────────────────┘  │ │    │
│  │  │                                                           │ │    │
│  │  │  ┌────────────────────┐  ┌────────────────────┐          │ │    │
│  │  │  │   Cancel          │  │  Confirm Override  │          │ │    │
│  │  │  └────────────────────┘  └────────────────────┘          │ │    │
│  │  │                                                           │ │    │
│  │  └───────────────────────────────────────────────────────────┘ │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                │                                          │
│                                ▼                                          │
│  3. OVERRIDE CONFIRMATION                                               │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  ┌───────────────────────────────────────────────────────────┐ │    │
│  │  │                                                           │ │    │
│  │  │   ✅ Override Confirmed                                   │ │    │
│  │  │                                                           │ │    │
│  │  │   Action changed to: Request budget confirmation          │ │    │
│  │  │                                                           │ │    │
│  │  │   This feedback helps improve future recommendations.     │ │    │
│  │  │                                                           │ │    │
│  │  │   [Undo] [Close]                                          │ │    │
│  │  │                                                           │ │    │
│  │  └───────────────────────────────────────────────────────────┘ │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Feedback Collection UI

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       FEEDBACK COLLECTION UI                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  1. IMMEDIATE FEEDBACK (After override)                                  │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  ┌───────────────────────────────────────────────────────────┐ │    │
│  │  │  Quick feedback: Was the AI recommendation helpful?        │ │    │
│  │  │                                                           │ │    │
│  │  │  ┌────────────┐  ┌────────────┐  ┌────────────┐          │ │    │
│  │  │  │   👍      │  │   👎      │  │  Skip      │          │ │    │
│  │  │  │  Helpful  │  │  Not good │  │            │          │ │    │
│  │  │  └────────────┘  └────────────┘  └────────────┘          │ │    │
│  │  │                                                           │ │    │
│  │  └───────────────────────────────────────────────────────────┘ │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  2. DETAILED FEEDBACK (Optional expand)                                  │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  ┌───────────────────────────────────────────────────────────┐ │    │
│  │  │  Tell us more (optional):                                 │ │    │
│  │  │                                                           │ │    │
│  │  │  ┌────────────────────────────────────────────────────┐  │ │    │
│  │  │  │ What was wrong with the recommendation?            │  │    │
│  │  │  │                                                    │  │    │
│  │  │  │  ◉ Wrong action suggested                         │  │    │
│  │  │  │  ◉ Right action, wrong timing                     │  │    │
│  │  │  │  ○ Missed important context                       │  │    │
│  │  │  │  ○ Confusing explanation                          │  │    │
│  │  │  │  ○ Other                                         │  │    │
│  │  │  │                                                    │  │    │
│  │  │  │  Additional notes (optional):                     │  │    │
│  │  │  │  ┌──────────────────────────────────────────────┐ │  │    │
│  │  │  │  │                                              │ │  │    │
│  │  │  │  │                                              │ │  │    │
│  │  │  │  └──────────────────────────────────────────────┘ │  │    │
│  │  │  │                                                    │  │    │
│  │  │  │                                    [Submit] [Skip] │  │    │
│  │  │  └────────────────────────────────────────────────────┘  │ │    │
│  │  │                                                           │ │    │
│  │  └───────────────────────────────────────────────────────────┘ │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  3. LEARNING CONFIRMATION (After feedback)                               │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  ┌───────────────────────────────────────────────────────────┐ │    │
│  │  │                                                           │ │    │
│  │  │   🎓 Thanks for your feedback!                            │ │    │
│  │  │                                                           │ │    │
│  │  │   This will help improve recommendations for             │ │    │
│  │  │   similar situations in the future.                      │ │    │
│  │  │                                                           │ │    │
│  │  │   [Continue] [View What Changed]                         │ │    │
│  │  │                                                           │ │    │
│  │  └───────────────────────────────────────────────────────────┘ │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Decision History Timeline

### Timeline Visualization

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       DECISION HISTORY TIMELINE                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  DECISION HISTORY                                                │    │
│  │  ┌────────────────────────────────────────────────────────────┐  │    │
│  │  │                                                            │  │    │
│  │  │  TODAY                                                     │  │    │
│  │  │  ┌──────────────────────────────────────────────────────┐ │  │    │
│  │  │  │ 2h ago  │ State: AWAITING_CUSTOMER_DECISION         │ │  │    │
│  │  │  │         │ Trigger: AI detected 24h since quote sent  │ │  │    │
│  │  │  │         │ │                                           │  │    │
│  │  │  │         │ └─ Automated state transition             │  │    │
│  │  │  ├──────────────────────────────────────────────────────┤ │  │    │
│  │  │  │ 5h ago  │ AI: Recommend sending quote                │ │  │    │
│  │  │  │         │ Confidence: 89%                             │  │    │
│  │  │  │         │ │                                           │  │    │
│  │  │  │         │ ├─ Agent approved                           │  │    │
│  │  │  │         │ └─ Quote sent successfully                  │  │    │
│  │  │  │         │                                             │  │    │
│  │  │  │         │ 💬 Agent note: "Customer is very keen"      │  │    │
│  │  │  ├──────────────────────────────────────────────────────┤ │  │    │
│  │  │  │ 6h ago  │ State: QUOTE_PREPARATION                   │  │    │
│  │  │  │         │ Trigger: Budget confirmed                  │  │    │
│  │  │  │         │ │                                           │  │    │
│  │  │  │         │ └─ AI initiated quote generation            │  │    │
│  │  │  └──────────────────────────────────────────────────────┘ │  │    │
│  │  │                                                            │  │    │
│  │  │  YESTERDAY                                                 │  │    │
│  │  │  ┌──────────────────────────────────────────────────────┐ │  │    │
│  │  │  │ 4pm     │ AI: Request budget confirmation            │ │  │    │
│  │  │  │         │ Confidence: 67%                             │  │    │
│  │  │  │         │ │                                           │  │    │
│  │  │  │         │ ├─ Agent overrode                           │  │    │
│  │  │  │         │ └─ Sent quote instead                       │  │    │
│  │  │  │         │                                             │  │    │
│  │  │  │         │ Reason: "I know this customer, budget OK"   │  │    │
│  │  │  ├──────────────────────────────────────────────────────┤ │  │    │
│  │  │  │ 2pm     │ State: PRICE_REQUEST_RECEIVED              │  │    │
│  │  │  │         │ Trigger: New message from customer          │  │    │
│  │  │  └──────────────────────────────────────────────────────┘ │  │    │
│  │  │                                                            │  │    │
│  │  │  Show earlier events [+]                                   │  │    │
│  │  │                                                            │  │    │
│  │  └────────────────────────────────────────────────────────────┘  │    │
│  │                                                                   │    │
│  │  ┌────────────────────────────────────────────────────────────┐  │    │
│  │  │  Filter: [All] [AI Decisions] [Overrides] [State Changes]  │  │    │
│  │  │  Export: [Download CSV]                                    │  │    │
│  │  └────────────────────────────────────────────────────────────┘  │    │
│  │                                                                   │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Event Types & Icons

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         EVENT TYPE ICONOGRAPHY                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  AI DECISIONS                                                            │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  🤖 AI Recommendation                                           │    │
│  │     AI suggested an action                                      │    │
│  │                                                                  │    │
│  │  ✅ AI Approved                                                 │    │
│  │     Agent approved, action executed                             │    │
│  │                                                                  │    │
│  │  ↪️ AI Overridden                                               │    │
│  │     Agent chose different action                                │    │
│  │                                                                  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  STATE CHANGES                                                           │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  🔄 State Changed                                               │    │
│  │     Trip state transitioned                                     │    │
│  │                                                                  │    │
│  │  ⚡ Auto-transitioned                                            │    │
│  │     State changed by automation rules                           │    │
│  │                                                                  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  HUMAN ACTIONS                                                           │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  👤 Agent Action                                                │    │
│  │     Manual action by agent                                      │    │
│  │                                                                  │    │
│  │  💬 Agent Note                                                  │    │
│  │     Comment added by agent                                      │    │
│  │                                                                  │    │
│  │  📧 Customer Message                                            │    │
│  │     Communication from customer                                 │    │
│  │                                                                  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  SYSTEM EVENTS                                                           │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  🔔 Reminder Triggered                                          │    │
│  │     Scheduled reminder fired                                    │    │
│  │                                                                  │    │
│  │  ⚠️ Risk Flagged                                                │    │
│  │     Risk threshold exceeded                                     │    │
│  │                                                                  │    │
│  │  ✅ Task Completed                                              │    │
│  │     Background task finished                                    │    │
│  │                                                                  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Responsive & Adaptive Behavior

### Screen Size Adaptations

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         RESPONSIVE ADAPTATIONS                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  DESKTOP (> 1200px)                                                      │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  ┌──────────────────┐  ┌────────────────────────────────────┐   │    │
│  │  │                  │  │                                    │   │    │
│  │  │   State Panel    │  │      Decision Panel               │   │    │
│  │  │                  │  │                                    │   │    │
│  │  │  • State         │  │  • Recommendation                 │   │    │
│  │  │  • Confidence    │  │  • Breakdown                      │   │    │
│  │  │  • Scores        │  │  • Reasoning                      │   │    │
│  │  │  • History       │  │  • Actions                        │   │    │
│  │  │                  │  │                                    │   │    │
│  │  └──────────────────┘  └────────────────────────────────────┘   │    │
│  │                                                                  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  TABLET (768px - 1200px)                                                 │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  ┌─────────────────────────────────────────────────────────┐    │    │
│  │  │  STATE: Needs Review • 73% Conf • Low Risk              │    │    │
│  │  ├─────────────────────────────────────────────────────────┤    │    │
│  │  │                                                           │    │
│  │  │  Decision Panel                                          │    │    │
│  │  │  • Recommendation                                        │    │    │
│  │  │  • Breakdown                                             │    │    │
│  │  │  • Reasoning                                             │    │    │
│  │  │                                                           │    │    │
│  │  ├─────────────────────────────────────────────────────────┤    │    │
│  │  │                                                           │    │    │
│  │  │  [Scores] [History] [Details] ← Tabs                    │    │    │
│  │  │                                                           │    │    │
│  │  └─────────────────────────────────────────────────────────┘    │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  MOBILE (< 768px)                                                        │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  ┌─────────────────────────────────────────────────────────┐    │    │
│  │  │                                                          │    │    │
│  │  │  ⚠️ Needs Review                                    │    │    │
│  │  │  73% Confidence • Low Risk                            │    │    │
│  │  │                                                          │    │    │
│  │  ├─────────────────────────────────────────────────────────┤    │    │
│  │  │                                                          │    │    │
│  │  │  💡 Send Quote Now                                      │    │    │
│  │  │                                                          │    │    │
│  │  │  Customer is ready to buy. 89% probability.             │    │    │
│  │  │                                                          │    │    │
│  │  │  ┌─────────────────────────────────────────────────┐   │    │    │
│  │  │  │  [Send Quote]  [Why?]  [More]                    │   │    │    │
│  │  │  └─────────────────────────────────────────────────┘   │    │    │
│  │  │                                                          │    │    │
│  │  └─────────────────────────────────────────────────────────┘    │    │
│  │                                                                   │    │
│  │  ┌─────────────────────────────────────────────────────────┐    │    │
│  │  │  [Breakdown] [Reasoning] [History]  ← Bottom nav         │    │    │
│  │  └─────────────────────────────────────────────────────────┘    │    │
│  │                                                                   │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Adaptive Complexity Levels

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        ADAPTIVE COMPLEXITY                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  NOVICE MODE (First-time users, low activity)                            │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  ┌───────────────────────────────────────────────────────────┐ │    │
│  │  │                                                           │ │    │
│  │  │   💡 Send Quote Now                                      │ │    │
│  │  │                                                           │ │    │
│  │  │   The customer is ready to buy.                          │ │    │
│  │  │                                                           │ │    │
│  │  │   [Send Quote]  [Learn why]                              │ │    │
│  │  │                                                           │ │    │
│  │  └───────────────────────────────────────────────────────────┘ │    │
│  │                                                                  │    │
│  │  ⚙️ Settings: [Show advanced details]                          │    │
│  │                                                                  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  INTERMEDIATE MODE (Regular users, medium activity)                      │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  ┌───────────────────────────────────────────────────────────┐ │    │
│  │  │                                                           │ │    │
│  │  │   💡 Send Quote Now                                      │ │    │
│  │  │   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  89%               │ │    │
│  │  │                                                           │ │    │
│  │  │   High engagement • Complete info • Good timing          │ │    │
│  │  │                                                           │ │    │
│  │  │   [Send Quote]  [View breakdown]  [Override]             │ │    │
│  │  │                                                           │ │    │
│  │  └───────────────────────────────────────────────────────────┘ │    │
│  │                                                                  │    │
│  │  ┌───────────────────────────────────────────────────────────┐ │    │
│  │  │  📊 Completeness  ●●●●●●●●○○  85%                        │ │    │
│  │  │  🎯 Confidence    ●●●●●●●●○○  73%                        │ │    │
│  │  │  ⚡ Urgency       ●●●●●●○○○○  60%                        │ │    │
│  │  │  ⚠️ Risk          ●●○○○○○○○○  23%                        │ │    │
│  │  └───────────────────────────────────────────────────────────┘ │    │
│  │                                                                  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  EXPERT MODE (Power users, high activity)                                │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  ┌───────────────────────────────────────────────────────────┐ │    │
│  │  │  RECOMMENDATION                                           │ │    │
│  │  │  ┌─────────────────────────────────────────────────────┐ │ │    │
│  │  │  │ Action: SEND_QUOTE                                   │ │    │
│  │  │  │ Confidence: 89% (CI: 85-93%)                         │ │    │
│  │  │  │ P(Conversion): 94%                                   │ │    │
│  │  │  │ Model: ensemble_v4.2                                 │ │    │
│  │  │  │ Features: 47                                         │ │    │
│  │  │  └─────────────────────────────────────────────────────┘ │ │    │
│  │  │                                                           │ │    │
│  │  │  ┌─────────────────────────────────────────────────────┐ │ │    │
│  │  │  │ TOP FEATURES (SHAP values)                           │ │    │
│  │  │  │ • engagement_score: +0.32                            │ │    │
│  │  │  │ • response_time: +0.18                               │ │    │
│  │  │  │ • budget_alignment: +0.12                            │ │    │
│  │  │  │ • lead_time: +0.09                                   │ │    │
│  │  │  │ ─────────────────────────────────                    │ │    │
│  │  │  │ [Execute]  [Debug]  [Raw JSON]                       │ │    │
│  │  │  └─────────────────────────────────────────────────────┘ │ │    │
│  │  └───────────────────────────────────────────────────────────┘ │    │
│  │                                                                  │    │
│  │  ⚙️ Settings: [Simplify view]                                 │    │
│  │                                                                  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 9. Accessibility Considerations

### WCAG Compliance

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        ACCESSIBILITY FEATURES                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  VISUAL IMPAIRMENTS                                                      │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                                                                  │    │
│  │  COLOR BLINDNESS                                                  │    │
│  │  • Never use color alone to convey state                         │    │
│  │  • Always pair colors with icons/text                            │    │
│  │  • Use patterns for charts (stripes, dots)                       │    │
│  │                                                                  │    │
│  │  Example:                                                         │    │
│  │  ┌──────────────────────────────────────────────────────────┐   │    │
│  │  │ ✅ High Confidence (green)                                │   │    │
│  │  │ ⚠️ Medium Confidence (yellow)                             │   │    │
│  │  │ 🔴 Low Confidence (red)                                  │   │    │
│  │  │                                                            │   │    │
│  │  │ NOT: Green bar, Yellow bar, Red bar                       │   │    │
│  │  │                                                              │   │    │
│  │  └──────────────────────────────────────────────────────────┘   │    │
│  │                                                                  │    │
│  │  LOW VISION                                                      │    │
│  │  • All text is 200% zoomable without breaking                  │    │
│  │  • High contrast mode support (WCAG AAA)                        │    │
│  │  • Text remains readable at 400% zoom                           │    │
│  │                                                                  │    │
│  │  SCREEN READERS                                                  │    │
│  │  • All icons have aria-labels                                   │    │
│  │  • State changes announced live                                 │    │
│  │  • Confidence scores read as percentages                        │    │
│  │  • Progress bars have aria-valuenow                             │    │
│  │                                                                  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  MOTOR IMPAIRMENTS                                                       │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                                                                  │    │
│  │  KEYBOARD NAVIGATION                                             │    │
│  │  • All actions accessible via Tab                               │    │
│  │  • Visible focus indicators (never remove outline)              │    │
│  │  • Skip links for main content                                  │    │
│  │  • Escape closes modals                                         │    │
│  │                                                                  │    │
│  │  TOUCH TARGETS                                                   │    │
│  │  • Minimum 44×44px touch targets                                │    │
│  │  • Spacing between interactive elements                         │    │
│  │  • No hover-only critical information                           │    │
│  │                                                                  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  COGNITIVE ACCESSIBILITY                                                 │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                                                                  │    │
│  │  CLEAR LANGUAGE                                                  │    │
│  │  • Plain language explanations                                  │    │
│  │  • Avoid jargon or explain it                                   │    │
│  │  • Consistent terminology                                       │    │
│  │                                                                  │    │
│  │  ERROR PREVENTION                                                │    │
│  │  • Confirm destructive actions                                  │    │
│  │  • Clear undo options                                          │    │
│  │  • Reversible decisions when possible                          │    │
│  │                                                                  │    │
│  │  FOCUS MANAGEMENT                                                │    │
│  │  • Reduce distractions in focus mode                            │    │
│  │  • Pause animations on request                                  │    │
│  │  • Clear visual hierarchy                                       │    │
│  │                                                                  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Screen Reader Patterns

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      SCREEN READER ANNOUCEMENTS                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  STATE ANNOUNCEMENTS                                                     │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                                                                  │    │
│  │  aria-live="polite"                                              │    │
│  │  → "Trip state changed to Needs Review"                          │    │
│  │                                                                  │    │
│  │  aria-live="assertive" (for urgent changes)                      │    │
│  │  → "Attention: Budget exceeded threshold"                        │    │
│  │                                                                  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  CONFIDENCE ANNOUNCEMENTS                                               │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                                                                  │    │
│  │  <div role="progressbar"                                         │    │
│  │       aria-valuenow="73"                                        │    │
│  │       aria-valuemin="0"                                         │    │
│  │       aria-valuemax="100"                                      │    │
│  │       aria-label="Confidence score">                            │    │
│  │  → "Confidence: 73 percent"                                      │    │
│  │                                                                  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  RECOMMENDATION ANNOUNCEMENTS                                           │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                                                                  │    │
│  │  <div role="region" aria-label="AI Recommendation">             │    │
│  │  → "AI recommendation region. Send Quote Now. Confidence 89%.   │    │
│  │     Button: Send Quote. Button: Learn why."                      │    │
│  │                                                                  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 10. Animation & Motion Design

### Transition Patterns

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        MOTION DESIGN PRINCIPLES                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  STATE TRANSITIONS                                                      │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                                                                  │    │
│  │  Smooth morph between state indicators                           │    │
│  │  ┌─────────┐        ┌─────────┐                                  │    │
│  │  │  🔵   │  ────▶  │  🔄   │                                  │    │
│  │  │Received│   300ms │Preparing│                                │    │
│  │  └─────────┘   ease  └─────────┘                                  │    │
│  │                                                                  │    │
│  │  easing: cubic-bezier(0.4, 0.0, 0.2, 1)  // Material Decelerate   │    │
│  │                                                                  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  CONFIDENCE CHANGES                                                      │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                                                                  │    │
│  │  Animate bar fill, not text                                      │    │
│  │  ┌────────────────────────────────────────────────────────┐    │    │
│  │  │  58%  ─────────▶  73%                                     │    │    │
│  │  │  [████████████░░░░]  ──▶  [███████████████░░]            │    │    │
│  │  │        500ms ease-out                                   │    │    │
│  │  └────────────────────────────────────────────────────────┘    │    │
│  │                                                                  │    │
│  │  Text updates instantly (no counting animation)                  │    │
│  │                                                                  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  RECOMMENDATION APPEARANCE                                              │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                                                                  │    │
│  │  Stagger fade-in for recommendation card                         │    │
│  │  ┌──────────────────────────────────────────────────────────┐  │    │
│  │  │                                                           │  │    │
│  │  │  ┌────────────────────────────────────────────────────┐ │  │    │
│  │  │  │ 1. Icon fades in (0ms)                              │ │  │    │
│  │  │  │ 2. Title slides up (50ms)                           │ │  │    │
│  │  │  │ 3. Description fades in (100ms)                     │ │  │    │
│  │  │  │ 4. Confidence bar fills (150ms)                     │ │  │    │
│  │  │  │ 5. Buttons scale in (200ms)                          │ │  │    │
│  │  │  └────────────────────────────────────────────────────┘ │  │    │
│  │  │                                                           │  │    │
│  │  └──────────────────────────────────────────────────────────┘  │    │
│  │                                                                  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  REDUCED MOTION                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                                                                  │    │
│  │  @media (prefers-reduced-motion: reduce)                        │    │
│  │  • All transitions instant (0ms)                                │    │
│  │  • No auto-playing animations                                   │    │
│  │  • Preserve essential state changes (no motion)                 │    │
│  │                                                                  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 11. Component Reference

### TypeScript Interfaces

```typescript
// Decision Panel Component Interface

interface DecisionPanelProps {
  tripId: string;
  currentState: TripState;
  confidence: ConfidenceScore;
  recommendation: Recommendation | null;
  scores: {
    completeness: CompletenessScore;
    urgency: UrgencyScore;
    risk: RiskScore;
  };
  history: DecisionEvent[];
  onApprove: () => void;
  onOverride: (action: string, reason?: string) => void;
  onDismiss: () => void;
  complexityLevel?: 'novice' | 'intermediate' | 'expert';
}

interface Recommendation {
  id: string;
  action: string;
  title: string;
  description: string;
  confidence: number;
  conversionProbability?: number;
  reasoning: Reason[];
  alternatives?: AlternativeAction[];
  primaryAction: ActionButton;
  secondaryActions?: ActionButton[];
  metadata: {
    modelVersion: string;
    timestamp: Date;
    featureCount: number;
  };
}

interface Reason {
  type: 'positive' | 'concern' | 'neutral';
  icon: string;
  title: string;
  description: string;
  weight: number;
}

interface AlternativeAction {
  action: string;
  title: string;
  confidence: number;
  reasoning: string;
}

interface ActionButton {
  label: string;
  action: string;
  variant?: 'primary' | 'secondary' | 'ghost';
  icon?: string;
}

interface DecisionEvent {
  id: string;
  timestamp: Date;
  type: 'ai_recommendation' | 'ai_approved' | 'ai_overridden' | 'state_change' | 'agent_action';
  title: string;
  description?: string;
  actor: 'ai' | 'agent' | 'system' | 'customer';
  metadata?: Record<string, unknown>;
}
```

### Component Structure

```tsx
// Decision Panel Component Structure

<DecisionPanel>
  {/* Header */}
  <DecisionPanel.Header>
    <StateBadge state={currentState} />
    <ConfidenceIndicator score={confidence} />
    <RiskIndicator level={scores.risk.level} />
  </DecisionPanel.Header>

  {/* Recommendation */}
  <DecisionPanel.Recommendation>
    <RecommendationCard
      recommendation={recommendation}
      onApprove={onApprove}
      onOverride={onOverride}
    />
  </DecisionPanel.Recommendation>

  {/* Quick Actions */}
  <DecisionPanel.QuickActions>
    <ActionButton />
    <ActionButton />
    <ActionButton />
  </DecisionPanel.QuickActions>

  {/* Score Breakdown */}
  <DecisionPanel.ScoreBreakdown>
    <CompletenessMeter score={scores.completeness} />
    <ConfidenceMeter score={confidence} />
    <UrgencyMeter score={scores.urgency} />
    <RiskMeter score={scores.risk} />
  </DecisionPanel.ScoreBreakdown>

  {/* Reasoning Explainer */}
  <DecisionPanel.Reasoning>
    <ReasoningList reasons={recommendation.reasoning} />
  </DecisionPanel.Reasoning>

  {/* History Timeline */}
  <DecisionPanel.History>
    <DecisionTimeline events={history} />
  </DecisionPanel.History>
</DecisionPanel>
```

---

## Summary

The Decision Engine UX/UI is built on **transparency, control, and progressive disclosure**. Every AI decision is explainable, overridable, and traceable. The interface adapts to user expertise, from novice-friendly simplicity to expert-level detail. Accessibility is first-class, ensuring all users can understand and act on AI recommendations effectively.

**Key Design Decisions:**
1. **Never hide confidence** — Always show AI certainty levels
2. **One-click override** — No friction for human corrections
3. **Explain on demand** — Simple view first, detail on request
4. **Teach from overrides** — Every correction improves the system
5. **Multi-modal display** — Visual, text, and numerical representations
6. **Responsive adaptation** — Works seamlessly across all screen sizes
7. **Accessibility first** — WCAG AA compliant, screen reader friendly

---

**Next Document:** DECISION_03_BUSINESS_VALUE_DEEP_DIVE.md — Conversion impact, efficiency gains, and ROI
