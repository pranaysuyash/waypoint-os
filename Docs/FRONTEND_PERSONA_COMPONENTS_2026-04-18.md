# Missing Frontend Components by Persona
**Date**: 2026-04-18
**Context**: While the foundational UI components (`layouts`, `shell`, `ui`) exist, the product lacks the specialized, business-logic-heavy components required to serve the three core personas: Agency Owners, Operators/Agents, and End Travelers.

---

## 1. Agency Owner (The "Governance & Growth" Persona)
The Owner needs bird's-eye visibility into team performance, margin adherence, and business health.

### Missing Components:
*   **`MarginPolicyGuard`**: A component that wraps quote-generation fields, visually flagging when an agent tries to price a package below the agency's baseline minimum margin.
*   **`AgentUtilizationHeatmap`**: A visual calendar component showing the workload of each agent (trips actively being worked on vs. stalled).
*   **`EscalationQueueTable`**: A specialized data table showing trips that hit a `STOP_NEEDS_REVIEW` state, highlighting the exact rule that triggered the block (e.g., "Budget $300 under minimum feasible limit").
*   **`ConversionFunnelSankey`**: A diagram component tracking leads from *Inquiry → Quote Sent → Deposit Paid → Fully Settled*.
*   **`SupplierExposureChart`**: A component showing how much of the agency's total revenue is tied to specific suppliers, helping owners negotiate better contracts or diversify risk.

---

## 2. Operator / Agent (The "Efficiency & Execution" Persona)
The Operator needs high-density, action-oriented components that reduce cognitive load and repetitive tasks.

### Missing Components:
*   **`SmartClarificationBuilder`**: An interactive form that takes the system's "missing info" gaps and allows the agent to construct a polite, conversational WhatsApp message by toggling specific questions on/off.
*   **`DragAndDropItineraryBuilder`**: A kanban-style day-by-day builder where agents can drag recommended activities or hotels from the `StrategyBundle` directly into a client's timeline.
*   **`ConfidenceBadgeRow`**: A horizontal metric bar attached to every incoming trip showing the system's confidence in Budget, Dates, and Destination, allowing the agent to triage at a glance.
*   **`SupplierAvailabilityPing`**: A small status indicator component next to a suggested hotel/flight that shows real-time or cached availability (Red/Yellow/Green).
*   **`ContextualKnowledgeSidebar`**: A collapsible drawer that surfaces agency-specific playbooks (e.g., "Visa requirements for Indian passports going to Turkey") exactly when the system detects that destination.

---

## 3. End Traveler / Client (The "Trust & Delight" Persona)
The Traveler needs a frictionless, beautiful, and confidence-inspiring interface that feels like a premium service, not a software tool.

### Missing Components:
*   **`MagicLinkAuthenticator`**: A passwordless entry component that allows a traveler to access their itinerary via a single click from an SMS or WhatsApp message.
*   **`InteractiveProposalView`**: A "Choose Your Own Adventure" component where a traveler can toggle between "Option A (Luxury)" and "Option B (Boutique)" and instantly see the price difference update.
*   **`MobileTimelineStepper`**: A mobile-optimized, day-by-day view of the itinerary that clearly shows check-in times, transfer instructions, and contact numbers.
*   **`OneClickApprovalButton`**: A high-conversion CTA component that captures the client's electronic signature/approval on the proposed itinerary and triggers the payment deposit flow.
*   **`TripCountdownWidget`**: A delightful, shareable component showing days until departure, integrating local weather forecasts for the destination.

---

## 4. Implementation Strategy
Currently, `frontend/src/components` only contains generic UI pieces (buttons, inputs, error boundaries). 

To scale efficiently, we should adopt a **Feature-Sliced Design (FSD)** or **Domain-Driven Component Architecture**. We need to create new directories for these business domains:
*   `src/components/owner-insights/`
*   `src/components/operator-workbench/`
*   `src/components/traveler-portal/`
