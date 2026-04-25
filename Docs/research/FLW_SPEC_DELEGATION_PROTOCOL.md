# Flow Spec: Agentic Delegation-Protocol (FLW-004)

**Status**: Research/Draft
**Area**: Human-Agent Collaboration & Delegation

---

## 1. The Problem: "The Over-Confident Agent"
Autonomous agents often try to solve problems they lack the "Real-World-Nuance" or "Relationship-Access" to handle. For example, an agent can find a table at a generic restaurant via OpenTable, but it cannot "Bribe-the-Maitre-d" for a specific anniversary table at a Michelin-starred venue. An agent that doesn't know when to delegate to a human concierge will provide a sub-optimal "generic" experience.

## 2. The Solution: 'Multi-Stakeholder-Handoff-Protocol' (MSHP)

The MSHP allows the agent to act as a "Delegation-Manager."

### Delegation Triggers:

1.  **Relationship-Access-Trigger**:
    *   **Action**: If a request requires "High-Trust-Access" (e.g., invitation-only event, sold-out table), the agent autonomously delegates to the **Hotel-Concierge** or a **Local-Human-Expert**.
2.  **Creative-Nuance-Trigger**:
    *   **Action**: If the user's request is ambiguous (e.g., "Something romantic but not cliché"), the agent prepares a "Draft-Menu" and asks the **User** for a directional steer rather than guessing.
3.  **Physical-Constraint-Trigger**:
    *   **Action**: If a task requires physical presence (e.g., "Check if my luggage arrived at the carousel"), the agent delegates to a **Ground-Handling-Agent** or a **Courier-Service** via API.
4.  **Specialist-Verification-Trigger**:
    *   **Action**: If a task involves high legal or medical stakes (e.g., "Is my visa valid for this layover?"), the agent generates the "Hypothesis" but delegates the "Final-Verification" to a **Human-Legal-Auditor**.

## 3. Data Schema: `Delegation_Handoff_Audit`

```json
{
  "handoff_id": "MSHP-77221",
  "traveler_id": "GUID_9911",
  "task": "SECURE_TABLE_AT_OSTERIA_FRANCESCANA",
  "delegatee": "AMEX_CENTURION_CONCIERGE",
  "reason": "HIGH_RELATIONSHIP_ACCESS_REQUIRED",
  "context_passed": "Anniversary trip, preference for quiet corner.",
  "status": "HANDED_OFF",
  "callback_hook": "https://api.waypoint.os/callback/77221"
}
```

## 4. Key Logic Rules

- **Rule 1: The 'Context-Preservation' Rule**: When delegating to a human, the agent MUST provide the "Full-Context-Dossier" (Traveler persona, past rejections, current itinerary) so the human doesn't ask the user redundant questions.
- **Rule 2: The 'Follow-Up-Loop'**: The agent remains the "Orchestrator." It MUST follow up with the human delegatee T+1h to ensure the task is progressing.
- **Rule 3: Cost-Benefit-Audit**: If a human specialist requires a fee (e.g., $50 concierge fee), the agent MUST check the traveler's "Discretionary-Spend-Limit" (INT-001) before confirming the delegation.

## 5. Success Metrics (Collaboration)

- **Delegation-Precision**: % of handoffs that resulted in a successful outcome that the agent could not have achieved alone.
- **Handoff-Linguistics**: User satisfaction score with the transition from Agent to Human.
- **Context-Continuity**: How many times the user had to repeat information to a human delegatee (target: 0).
