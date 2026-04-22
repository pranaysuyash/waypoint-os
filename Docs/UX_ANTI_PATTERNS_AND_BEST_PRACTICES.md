# UX Architecture: Best Practices & Anti-Patterns

**Status**: Active / Foundational
**Date**: Wednesday, April 22, 2026

This document formalizes the UX and UI design philosophy for the Travel Agency Agent (TAA) dashboard. As we move from basic tools to an operational cockpit, these principles ensure we avoid common industry pitfalls and scale effectively.

---

## 1. Core UX Patterns (The "North Star")

### Progressive Disclosure (Information Density)
*   **Philosophy**: Start simple; reveal complexity on demand. 
*   **Implementation**: High-level charts show the "What." Clicking an agent/card reveals the "Why" (Decision Log). Expanding the log reveals the "How" (Provenance JSON).
*   **Benefit**: Minimizes cognitive load, keeping the operator focused on the current decision.

### Operational Workspace Model (Context Persistence)
*   **Philosophy**: Operators should never "lose" their context.
*   **Implementation**: Use drawers/side-rails (Right Rail) rather than modals or navigation-away patterns for drill-downs. The primary workspace remains visible and "in-focus" while evidence is audited.

### Actionable Analytics ("So What?")
*   **Philosophy**: A metric without an action is noise.
*   **Implementation**: Every analytical card (e.g., Low CSAT, High Response Time) must have an immediate "Action Pathway" (e.g., "View Trip Details", "Escalate to Human").

### Stateful "Drafting"
*   **Philosophy**: AI-generated work is never "final."
*   **Implementation**: Clearly demarcate the "Agent State" (AI-Drafted, Human-Verified, Rejected) using consistent badges and color-coding.

---

## 2. Industry Anti-Patterns (The "Avoid" List)

### The "Dashboard Graveyard"
*   **Definition**: Building dozens of charts simply because the data is available.
*   **The Trap**: Metric blindness. If a chart doesn't lead to a clear "yes/no" operational decision, remove it. 
*   **Correction**: Metrics must be tied to a specific business outcome (Throughput, Quality, Safety).

### Modal Fatigue
*   **Definition**: Opening a centered, focus-stealing modal for every sub-interaction.
*   **The Trap**: The user loses situational awareness of the main workspace.
*   **Correction**: Use the **Right Rail** pattern. It allows users to browse data *while still viewing the main content*.

### False Precision
*   **Definition**: Displaying metrics with excessive granularity (e.g., 72.834% conversion rate).
*   **The Trap**: Users lose trust; the numbers feel like they were hallucinated rather than calculated.
*   **Correction**: Use semantic confidence levels (e.g., "High", "Medium", "Low") or rounded ranges.

---

## 3. The Traceability Roadmap

To move from "Display" to "Investigation," all future frontend components must implement the following drill-down pipeline:

| Tier | UI Component | Interaction Target |
| :--- | :--- | :--- |
| **Macro** | Performance Charts | Agent-Level Insights |
| **Meso** | Agent Drill-down Page | Historical Decision Logs |
| **Micro** | Packet Inspector/Provenance | Raw Source Data/JSON |

---

## 4. Operational Guardrails (Self-Enforcing)
*   **No "Click Here"**: All links must have descriptive anchor text.
*   **Persistent Context**: If a user navigates to a drill-down page, a "Back to Dashboard" button must always be present (or provide breadcrumbs).
*   **Keyboard First**: All actionable data (cards, rows) must be focusable and navigable via keyboard (Tab, Enter).

---

## 5. Future Evolution
As we scale:
- **Phase A**: Traceability (Linking Charts to Packets).
- **Phase B**: Intelligent Defaults (System learns from manual overrides).
- **Phase C**: Anomaly Detection (UI automatically surfaces "unusual" data instead of requiring a manual search).
