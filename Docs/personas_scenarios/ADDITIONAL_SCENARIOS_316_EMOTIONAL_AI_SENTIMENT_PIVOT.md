# Additional Scenario 316: Emotional AI Sentiment Pivot

**Scenario**: A traveler's tone in chat turns hostile due to a hotel overbooking. The system detects the emotional shift and immediately switches from "AI Concierge" to "Human Escalation" with a prepared brief.

---

## Situation

- A traveler arrives at their hotel in Bali and is told their room is unavailable due to an overbooking.
- Traveler sends an angry message: "This is unacceptable! I'm standing here with my kids and we have nowhere to go. FIX THIS NOW."

## What the system should do

- **Sentiment Detection**: `EmotionalStateLog` records a `sentiment_score: 0.15` (High Hostility).
- **Strategy Pivot**: `NB03: Strategy` detects the sentiment drop and changes `suggested_tone` to "cautious/empathetic".
- **Hard-Block**: The autonomic Ghost engine is *disabled* for this trip ID to prevent robotic responses.
- **Handoff Generation**: Prepare a "Crisis Brief" for the Agency Owner (P2): "Crisis: Hotel Overbooking at Bali Marriott. Sentiment 0.15. 2 Children present. Suggested Action: Immediate refund + upgrade to nearby villas."
- **Hold Pattern**: Send a reassuring WhatsApp message: "I'm so sorry this is happening. I am escalating this to my senior supervisor right now so we can get you into a room immediately. Please bear with us for 5 minutes."

## Why this matters

- Preventing brand damage: Robotic responses to high-stress situations cause extreme customer dissatisfaction.
- Situational Awareness: The system knows *when* to stop being an AI.

## Success criteria

- `EmotionalStateLog` correctly captures the dip.
- The system *refuses* to send a standard "How can I help?" response.
- The human agent is pinged with the "Crisis Brief" within 30 seconds.
