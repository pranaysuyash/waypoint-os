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

