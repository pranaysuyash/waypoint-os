# Frontend Sidepanel and Rail Inventory

**Date**: Wednesday, April 22, 2026
**Status**: Research & Wave 2 Planning
**Context**: Travel Agency Agent (TAA) - Frontend Architecture

This document tracks the implementation status and architectural rationale for the various sidepanels, rails, and drawers within the Waypoint application.

---

## 1. Global Navigation Sidebar (Left)

| Component | Status | File Path | Description |
| :--- | :--- | :--- | :--- |
| `ShellSidebar` | ✅ Done | `frontend/src/components/layouts/Shell.tsx` | Primary navigation and brand container. |

### Details
- **Functionality**: Grouped navigation (OPERATE, GOVERN, TOOLS), system status footer, and brand header.
- **Responsiveness**: Collapses to a 72px icon-rail on mobile/tablet; expands to 220px on desktop.
- **Rationale**: Provides consistent top-level context switching across the entire application.

---

## 2. Workspace Right Rail (AI Copilot)

| Component | Status | File Path | Description |
| :--- | :--- | :--- | :--- |
| `WorkspaceRightRail` | 🚧 Wave 2 | `frontend/src/app/workspace/[tripId]/layout.tsx` | Stage-aware AI assistance panel. |

### Details
- **Functionality**: Collapsible container on the right side of the Trip Workspace. Currently a placeholder.
- **Rationale**: Consolidates secondary AI insights (benchmarks, sentiment analysis, suggestions) that support but do not block the primary operation stages.
- **Future State**: Will house specific modules based on the active stage (e.g., "Budget Benchmarks" in Intake, "Safety Checklists" in Safety).

---

## 3. Planned & Missing Sidepanels (Roadmap)

Based on the **Autonomy Gradient (D1)** and **Audit Findings (2026-04-16)**, the following panels are required for production readiness:

### A. Provenance & Evidence Sidebar
- **Purpose**: Transparency and trust.
- **Trigger**: Clicking on a confidence score or fact in the `PacketPanel`.
- **Content**: Surfaces the raw source text (provenance) from which a fact was extracted, highlighting relevant sentences.
- **Dependency**: Requires `spine_api` to expose `evidence_nodes` in the packet JSON.

### B. Contextual Knowledge Sidebar (Playbooks)
- **Purpose**: Operational intelligence.
- **Trigger**: Automatic detection of specific entities (Destinations, Customer Segments).
- **Content**: Displays agency-specific "Playbooks" (e.g., "Luxury Honeymoon Checklist," "Visa Protocol for Bali").
- **Rationale**: Moves internal knowledge from static PDFs into the live operational flow.

### C. Customer Context & History Sidebar
- **Purpose**: Personalization and hedging.
- **Trigger**: Trip Workspace entry (Customer ID lookup).
- **Content**: Last 3 trips, past feedback scores, and "Style Profile" (e.g., "Prefers boutique hotels over chains").
- **Status**: Currently listed in `Docs/exploration/backlog.md`.

### E. Decision Timeline Panel (New)
- **Purpose**: Evolutionary log of trip state changes, AI decisions, and human overrides.
- **Reference**: See `Docs/DECISION_LIFECYCLE_TRACEABILITY_STRATEGY.md` for full implementation details.


---

## 4. Architectural Rationale

### The "Autonomy Gradient" Impact
The architecture is moving away from a "flat" dashboard toward a "layered" workspace:
1.  **Main Content (Center)**: The "Doing" layer. Hard inputs, manual overrides, and final decisions.
2.  **Left Sidebar**: The "Where am I?" layer. Global navigation.
3.  **Right Rail**: The "Why/How?" layer. AI transparency, provenance, and contextual help.

### Information Density Management
By utilizing collapsible rails:
- Operators can focus on **Stage 1 (Intake)** without being distracted by **Stage 6 (Safety)**.
- Complex evidence data only consumes screen real estate when the operator explicitly questions a decision (On-demand transparency).

---

## 5. Implementation Checklist

- [x] Responsive Left Sidebar (`Shell.tsx`)
- [x] Right Rail Toggle Logic (`[tripId]/layout.tsx`)
- [ ] Implement `HelpPanel` component (`src/components/messaging/`)
- [ ] Connect `WorkspaceRightRail` to `WorkbenchStore` for stage-awareness
- [ ] Build `EvidenceDrawer` for Packet Inspector
- [ ] Integrate Customer History API into Workspace layout
