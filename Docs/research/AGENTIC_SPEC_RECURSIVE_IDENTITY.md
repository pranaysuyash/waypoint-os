# Agentic Spec: Recursive Identity Architecture (ID-001)

**Status**: Research/Draft
**Area**: Identity Intelligence & Contextual Reasoning

---

## 1. The Problem: "The Flattened Traveler"
Most travel systems treat a user as a single set of preferences (e.g., "Always prefers window seats"). However, a traveler's "Identity" changes based on the mission. A disruption during a "Solo Business Trip" requires a completely different recovery logic than a disruption during a "Family Vacation with Infants."

## 2. The Solution: 'Situational-Mode-Pivoting' (SMP)

The SMP protocol allows the agent to dynamically load different "Reasoning Templates" based on the traveler's active mode.

### Identity Modes:

1.  **Mode: EXECUTIVE (Efficiency Max)**:
    *   **Priorities**: Time > Cost > Directness.
    *   **Tolerance**: High for fatigue, Low for delays.
    *   **Recovery Action**: "Book the $2,000 private car if the 1-hour flight is delayed by 3 hours."
2.  **Mode: PROTECTOR (Safety/Comfort Max)**:
    *   **Priorities**: Security > Comfort > Time.
    *   **Tolerance**: Low for uncertainty, Zero for safety risks.
    *   **Recovery Action**: "Book a 5-star hotel near the airport immediately; do NOT wait at the gate with children."
3.  **Mode: COURIER (Asset Integrity Max)**:
    *   **Priorities**: Connection-Security > Luggage-Tracking > Comfort.
    *   **Tolerance**: High for layovers (if secure), Low for plane changes.
    *   **Recovery Action**: "Stay with the aircraft even if delayed 12 hours; do NOT risk checked-asset separation."

## 3. Data Schema: `Identity_Mode_Context`

```json
{
  "traveler_id": "T-9901",
  "active_mode": "PROTECTOR",
  "mode_weightings": {
    "safety": 0.95,
    "efficiency": 0.20,
    "cost_sensitivity": 0.10,
    "comfort": 0.85
  },
  "mode_triggers": [
    "TRAVELING_WITH_MINOR_TRUE",
    "NIGHT_ARRIVAL_TRUE"
  ],
  "reasoning_override": "PRIORITIZE_STABILITY_OVER_SPEED"
}
```

## 4. Key Logic Rules

- **Rule 1: Mode-Detection Inference**: If the PNR contains a "CHLD" (Child) SSR code, the agent MUST auto-pivot to "PROTECTOR" mode, regardless of the traveler's primary profile.
- **Rule 2: Conflict Resolution**: If a trip has "Mixed Modes" (e.g., Business trip where the spouse joins for the weekend), the agent uses the **'Strictest-Constraint'** logic (Safety/Protector wins over Efficiency).
- **Rule 3: Identity-Agnostic Core**: Legal and Financial "Hard-Guardrails" (e.g., spending limits, PII protection) are identity-agnostic and cannot be overridden by any mode.

## 5. Success Metrics (Personalization)

- **Mode Accuracy**: % of times the traveler confirmed the agent's "Identity-Mode" selection was correct.
- **Decision Alignment**: Reduction in "Decision-Rejection" rates by aligning recovery options with situational priorities.
- **Trust-Index Increase**: Improvement in long-term traveler retention for multi-purpose travelers (Business + Leisure).
