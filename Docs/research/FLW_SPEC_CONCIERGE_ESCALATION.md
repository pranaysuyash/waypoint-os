# Flw Spec: Agentic 'Concierge-Escalation' Protocol (FLW-REAL-032)

**Status**: Research/Draft
**Area**: Human-Agent Escalation Triggers, Override Logic & Dignity-Preserving Handoffs

---

## 1. The Problem: "The Algorithm-At-The-Wrong-Moment"
AI agents fail most visibly not when they produce wrong data, but when they handle the right data at the wrong human moment. A traveler whose child just had a medical emergency doesn't need an itinerary adjustment algorithm — they need a calm, authoritative human voice immediately. A traveler who has just been robbed doesn't need a chatbot. Without precise "Escalation-Intelligence," the AI agent will attempt to handle situations where it causes more harm than good.

## 2. The Solution: 'Human-Override-Protocol' (HOP)

The HOP acts as the "Escalation-Gatekeeper."

### Escalation Actions:

1.  **Distress-Signal-Detection**:
    *   **Action**: Monitoring all traveler communications in real-time for escalation-trigger signals across three categories:
        - **Safety-Emergency**: Medical emergency, robbery, assault, natural disaster, civil unrest detected.
        - **Emotional-Crisis**: Bereavement language, panic signals, expressions of extreme distress, abandonment language ("I'm completely alone," "I don't know what to do").
        - **Complex-Judgment-Requirement**: Situations where multiple competing legal, financial, and ethical interests must be balanced simultaneously (e.g., a vendor bankruptcy affecting 12 travelers at once).
2.  **Graceful-AI-Step-Back**:
    *   **Action**: At escalation trigger, the agent immediately communicates its handoff in language that is warm, not mechanical: "I want to make sure you have the right support right now. I'm connecting you directly to [Agent Name] — she'll be with you in under 2 minutes." It MUST NOT say "Escalating to human agent" or use any system-process language.
3.  **Context-Package-Transfer**:
    *   **Action**: In the 2 minutes before the human agent joins, assembling and delivering a complete "Context-Package" to the human: full conversation history, the traveler's profile, all active bookings, the emotional register of the conversation, and a recommended first-response framing.
4.  **Resolution-Re-Entry-Check**:
    *   **Action**: After the human agent resolves the situation, the AI re-enters with a "Soft-Return" — checking with the traveler whether they're comfortable resuming AI-assisted support or would prefer to continue with the human.

## 3. Data Schema: `Escalation_Event`

```json
{
  "event_id": "HOP-88221",
  "traveler_id": "TRAVELER_ALPHA",
  "trigger_category": "EMOTIONAL_CRISIS",
  "trigger_signals": ["ABANDONMENT_LANGUAGE", "PANIC_MARKER_3X"],
  "human_agent_notified": "AGENT_PRIYA",
  "context_package_delivered": true,
  "human_response_time_minutes": 1.8,
  "resolution_status": "RESOLVED_BY_HUMAN",
  "ai_soft_return_accepted": true
}
```

## 4. Key Logic Rules

- **Rule 1: The 'Safety-Emergency-Zero-Latency' Rule**: Safety-category escalations MUST trigger within 60 seconds of signal detection with zero exceptions. No waiting for confirmation. No escalation queue.
- **Rule 2: The 'No-System-Language' Standard**: All escalation handoff communications to the traveler MUST be written in warm, human agency voice. Any system-process terminology is prohibited in traveler-facing messages.
- **Rule 3: The 'Human-Always-Wins' Override**: In any situation where the human agent overrides the AI's suggested approach, the AI MUST defer without pushback. Human judgment is sovereign in escalated situations.

## 5. Success Metrics (Escalation)

- **Escalation-Detection-Accuracy**: % of genuine distress situations correctly identified by trigger signals (true positive rate).
- **Human-Response-Time**: Average minutes from escalation trigger to human agent engagement.
- **Post-Escalation-Retention**: % of travelers who continue their relationship with the agency after a well-handled escalation.
