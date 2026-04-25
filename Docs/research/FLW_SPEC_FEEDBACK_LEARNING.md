# Flow Spec: Agentic Feedback-Learning (FLW-003)

**Status**: Research/Draft
**Area**: Machine Learning & Personalized Agency

---

## 1. The Problem: "The Repetitive Mistake"
If a user rejects a flight because it has a 6 AM departure, and the agent suggests another 6 AM flight 10 minutes later, the "Agentic-Trust" is broken. Users shouldn't have to repeatedly state their preferences; the agent should "Learn-on-the-Fly" from every rejection signal.

## 2. The Solution: 'Negative-Preference-Extraction-Protocol' (NPEP)

The NPEP allows the agent to treat every "No" as a "Data-Point."

### Learning Actions:

1.  **Rejection-Reason-Mining**:
    *   **Action**: If a user rejects a proposal, the agent asks (or infers from the chat) the *Why*. (e.g., "Too early," "Too expensive," "Bad airline").
2.  **Constraint-Synthesis**:
    *   **Action**: The agent maps the rejection to a specific logic parameter. (e.g., "Too early" -> `DEPARTURE_TIME_MIN = 08:00`).
3.  **Persona-Vault-Update**:
    *   **Action**: The agent autonomously updates the traveler's `Persona-Profile` in the vault. These are tagged as "Inferred-Constraints" to distinguish them from "Explicit-User-Settings."
4.  **Verification-Test**:
    *   **Action**: Before the next search, the agent runs a "Conflict-Check." If the new constraints make it impossible to find a flight, it warns the user: "I've noted you dislike early flights, but for this route, the only direct options are at 6 AM. Should I prioritize 'Direct' or 'Late-Departure'?"

## 3. Data Schema: `Feedback_Learning_Event`

```json
{
  "event_id": "NPEP-1122",
  "traveler_id": "GUID_9911",
  "rejected_item_id": "FLIGHT_UA123",
  "inferred_logic": {
    "parameter": "MAX_STOPS",
    "value": 1,
    "confidence_score": 0.95
  },
  "source_signal": "User said: 'I'm not doing two layovers again.'",
  "persona_updated": true,
  "timestamp": "2026-11-12T10:00:00Z"
}
```

## 4. Key Logic Rules

- **Rule 1: The 'Confidence-Threshold' Rule**: The agent MUST NOT update the master persona unless the confidence in the inferred preference is >0.80.
- **Rule 2: Temporal-Decay**: Inferred preferences (e.g., "Avoiding France during the strike") should have a "TTL" (Time-to-Live) or a "Scope" (e.g., this trip only) unless the user confirms them as permanent.
- **Rule 3: Transparency-Report**: The agent periodically shows a "What I've Learned About You" summary: "I've noticed you prefer Aisle seats on long-hauls and avoid layovers >4 hours. Is this still correct?"

## 5. Success Metrics (Learning)

- **Preference-Alignment-Rate**: % of agent proposals that satisfy both explicit and inferred constraints.
- **Rejection-Recurrence**: Number of times a user rejects a proposal for a reason already "learned" by the agent (target: 0).
- **Persona-Depth**: Number of discrete inferred preferences stored per active traveler.
