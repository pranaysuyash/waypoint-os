# Flw Spec: Agentic 'Memory-Inheritance' Engine (FLW-REAL-031)

**Status**: Research/Draft
**Area**: Longitudinal Traveler Memory & Agent Context Continuity

---

## 1. The Problem: "The Amnesia-Agent"
Most AI travel agents have "Session-Memory" only. When a new conversation starts, the agent effectively starts fresh. This creates a deeply frustrating experience for a long-term traveler: they must re-explain their preferences, re-justify their quirks, and re-establish context that a human agent would remember for years. A truly great travel companion should feel like it's known the traveler for their entire travel life.

## 2. The Solution: 'Longitudinal-Memory-Protocol' (LMP)

The LMP acts as the "Traveler's Living-Memory-Vault."

### Memory Actions:

1.  **Episodic-Memory-Crystallization**:
    *   **Action**: After each trip, the agent synthesizes key "Memory-Crystals" — the specific moments, preferences, frictions, and delights that were unique to that traveler's experience. These aren't raw logs; they're distilled, narrative-quality memories.
    *   **Example**: "The traveler hated the buffet breakfast at the Maldives resort but was deeply moved by the private sunset dhow cruise — sunset-on-water moments are high-resonance."
2.  **Life-Event-Integration**:
    *   **Action**: Monitoring for traveler life signals (e.g., "Had a baby," "Retired," "Got married," "Lost a parent") shared in conversations and updating the traveler's "Life-Context-Profile" to shift trip recommendations accordingly.
3.  **Memory-Inheritance-on-Agent-Change**:
    *   **Action**: When the traveler's primary human agent changes (e.g., staff turnover), the AI agent provides the new human agent with a full "Context-Inheritance-Brief" — all relevant memory crystals, preferences, and life context — so the traveler never has to re-explain themselves.
4.  **Proactive-Anniversary-Intelligence**:
    *   **Action**: Monitoring for meaningful dates (e.g., "Last year the traveler did their honeymoon to Bali") and proactively suggesting anniversary experiences or milestone upgrades.

## 3. Data Schema: `Memory_Crystal`

```json
{
  "crystal_id": "LMP-55221",
  "traveler_id": "TRAVELER_ALPHA",
  "trip_id": "MALDIVES-2024-03",
  "crystal_type": "HIGH_RESONANCE_MOMENT",
  "memory_content": "Private sunset dhow cruise — emotional peak, traveler spontaneously tipped captain extra",
  "resonance_signal": "WATER_SUNSET_PRIVATE_EXPERIENCE",
  "weight": 0.92
}
```

## 4. Key Logic Rules

- **Rule 1: The 'Dignity-of-Memory' Standard**: Memory crystals MUST capture the spirit and emotional texture of an experience, not just transactional data. "Liked the hotel" is insufficient; "felt genuinely at home in the Ryokan's quiet garden" is the target.
- **Rule 2: Consent-Governed-Retention**: Travelers MUST be able to review, edit, and delete any memory crystal. Memory is a service, not surveillance.
- **Rule 3: Memory-Decay-Prevention**: The agent MUST surface relevant memory crystals in each new trip planning session, not bury them in an archive. Memory only has value if it's actively used.

## 5. Success Metrics (Memory)

- **Context-Re-Establishment-Time**: Average reduction in time spent re-explaining preferences in new sessions for travelers with active memory profiles.
- **Anniversary-Experience-Conversion**: % of proactive anniversary suggestions that result in a booking.
- **Agent-Handover-Satisfaction**: Traveler satisfaction scores for the first trip with a new human agent when a Context-Inheritance-Brief was provided.
