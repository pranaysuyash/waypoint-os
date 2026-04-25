# Operational Logic Spec: The 'Ghost Concierge' Handoff (OE-009)

**Status**: Research/Draft
**Area**: AI-Human Orchestration & User Experience Continuity

---

## 1. The Problem: "The Handoff Friction"
The most frustrating moment in customer service is when a user is moved from an AI to a human and has to repeat their entire story. In a luxury travel context, this "Repetition Tax" is a major trust-killer.

## 2. The Solution: Context Tunneling (Shadow Onboarding)

The system must implement **Context Tunneling**, a protocol that prepares the human agent *before* they send their first message, ensuring they are fully "synced" with the AI's previous interactions.

### Tunneling Mechanisms:

1.  **Sentiment Graphing**:
    *   Show the human a real-time graph of the traveler's emotional state (from `Sentiment_ROI_Multiplier`).
    *   Highlight "Friction Peaks" (where the traveler got upset).

2.  **Entity Summary Extraction**:
    *   AI extracts "Ground Truths" established so far (e.g., "The traveler wants a window seat," "They are allergic to peanuts").
    *   The human sees a "Bullet-Point Brief" instead of a raw transcript.

3.  **Draft-Ahead Ghosting**:
    *   The AI prepares a "Suggested First Response" for the human based on the current context.
    *   The human can "Tweak & Send" instead of "Read & Type."

## 3. Data Schema: `Handoff_Tunnel_Brief`

```json
{
  "trip_id": "T-8877",
  "traveler_id": "JENKINS-01",
  "ai_interaction_duration": "4m 12s",
  "established_facts": {
    "intent": "RE_BOOK_FLIGHT",
    "budget_flexibility": "UP_TO_500",
    "medical_needs": "NONE"
  },
  "current_sentiment": -0.6,
  "sentiment_trend": "DOWNWARD",
  "reason_for_handoff": "SLA_BREACH_DURING_CRITICAL_DELAY",
  "suggested_human_opener": "Hi Sarah, I've just reviewed your conversation with the AI. I'm taking over now. I see the AI found a Delta seat—I'm confirming that for you right now."
}
```

## 4. Key Logic Rules

- **Rule 1: No-Read Obligation**: The tunnel brief must be readable in < 10 seconds. If the brief is too long, the AI must further condense it using a "High-Urgency Summary" mode.
- **Rule 2: 'Jump-In' Visibility**: When a human enters the chat, the AI must immediately transition to "Observer Mode" (Silent) but continue to provide "Whisper Tips" (Private suggestions to the human).
- **Rule 3: Repetition Detector**: If the human agent asks a question that was already answered in the AI phase, the system triggers a "Internal Warning: Fact already established" to prevent redundancy.

## 5. Success Metrics

- **Repetition Rate**: Zero (measured by traveler feedback: "I had to repeat myself").
- **Handoff Latency**: Time from "Human Joined" to "Human First Message" < 30 seconds.
- **Trust Score Lift**: Sentiment improvement after human intervention.
