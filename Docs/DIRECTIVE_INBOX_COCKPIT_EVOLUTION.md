# Inbox Intelligence & Efficiency Directives (P1-03, P1-04, P1-05)

**Date**: Wednesday, April 22, 2026
**Priority**: High (P1)
**Goal**: Transform the Inbox from a static link-list to an Active Inspection Portal.

---

## 1. Unified Status Legend (P1-04)
**Location**: `frontend/src/app/inbox/page.tsx` (Header)
- **Component**: Add an `Info` icon next to the "Inbox" title.
- **Interaction**: On hover, show a popover defining:
  - **Red Border**: `slaStatus === 'breached'` (Urgent intervention required).
  - **Critical Tag**: `priority === 'critical'` (Requires human-in-the-loop review).
  - **Amber Tag**: `stage === 'options'` (Branching logic awaiting selection).
- **Purpose**: Eliminate tribal knowledge. Onboard operators instantly.

## 2. Smart Inbox Card (P1-03)
**Location**: `frontend/src/app/inbox/page.tsx` (`TripCard` component)
- **Status Footer**: Add a row at the bottom of the card surfacing top-level signals:
  - **Suitability Signals**: Render small, badge-style icons (e.g., ♿, 👶) if `suitability_flags` are present.
  - **Confidence Bar**: A compact 4px bar showing `decision.confidence` (if available).
- **Design Constraint**: Use tokens from `DESIGN.md`. Do not add inline styles. 
- **Purpose**: Provide "At-a-glance" context without requiring navigation.

## 3. Actionable Quick-Look (P1-05)
**Location**: `frontend/src/app/inbox/page.tsx` (`TripCard` component)
- **Action Menu**: Add a "3-dot" kebab menu on card hover.
- **Quick Actions**:
  - `Triage`: "Approve & Move to Shortlist" (if `PROCEED_INTERNAL_DRAFT`).
  - `Audit`: "Flag for Human Audit."
  - `Deep Dive`: Navigate to Workspace (standard click).
- **Constraint**: Must remain hidden until hover to maintain a clean aesthetic (Distillation principle).

## 4. Operational Triage Shortcuts (Phase 2 Roadmap)
The following accelerators are designed to reduce "Dead Time" in travel operations by enabling 1-click triage directly from the Inbox. Further workflow patterns will be identified and added as we observe operator behavior.

| Accelerator | Action | Rationale |
| :--- | :--- | :--- |
| **"Reply & Resume"** | Inline email triage | Reduces context-switching for trivial customer clarifications. |
| **"Buffer Override"** | 1-click budget unblock | Allows senior agents to bypass tight feasibility constraints without Workspace entry. |
| **"Priority Promotion"** | Sentiment-based escalation | Allows instant promotion of angry/sensitive threads to `Critical` status. |

*Note: These workflows are slated for Phase 2 implementation. We will continue to explore and document further high-velocity patterns as the system matures.*

---

## Addendum — Superseded by Directive V2

**Date**: Thursday, April 23, 2026
**Status**: Superseded
**Superseded By**: [`DIRECTIVE_INBOX_INTELLIGENCE_LAYER_V2.md`](./DIRECTIVE_INBOX_INTELLIGENCE_LAYER_V2.md)

This directive identified the correct symptoms (new operator confusion, tag opacity, need for at-a-glance signals) but prescribed additive solutions without restructuring the underlying information architecture. The V2 directive retains the intent of P1-03, P1-04, and P1-05 while rethinking the card layout, filter architecture, and progressive disclosure strategy from first principles.

**What carries forward**:
- The goal: eliminate tribal knowledge, enable at-a-glance decision-making
- The need for legend/explanation of visual signals
- The need for hover-revealed quick actions
- The Phase 2 accelerator roadmap (Reply & Resume, Buffer Override, Priority Promotion)

**What changes**:
- P1-04's "Info icon popover" → replaced with inline micro-labels + persistent tooltips that teach by doing
- P1-03's "additive signals footer" → replaced with role-based card profiles that surface the right signals for the right user
- P1-05's "kebab menu" → retained but expanded into a persistent quick-action chip pattern on hover
- Filter tabs → replaced with fully composable filter panel using existing `InboxFilters` type
- Card layout → restructured with visual hierarchy, left accent bar, and progressive disclosure

This document is preserved for historical context. All new implementation work should reference the V2 directive.

