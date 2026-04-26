# Flow Spec: Human-Agent Augmentation-Protocol (FLW-008)

**Status**: Research/Draft
**Area**: Operational Support & Multi-User Collaboration

---

## 1. The Problem: "The Overwhelmed Human Agent"
Human travel agents spend 40-60% of their time on "Low-Value-Repetitive-Tasks" (searching availability, formatting itineraries, answering basic visa questions). This prevents them from focusing on high-value "Relationship-Building" and complex "Concierge-Work." A binary "AI vs Human" model is inefficient; the real power is in "AI-Supporting-Human."

## 2. The Solution: 'Ghost-Writer-Protocol' (GWP)

The GWP allows the agent to act as a "Co-Pilot" for the human professional.

### Augmentation Actions:

1.  **Draft-Generation-Service**:
    *   **Action**: For every user inbound, the AI autonomously generates a "Suggested-Response" (using the Agency-Tone-Voice) and pre-searches relevant options. The human agent simply reviews, edits, and sends.
2.  **Contextual-Decision-Support**:
    *   **Action**: While the human agent is viewing a trip, the AI surfaces "Critical-Intelligence" (e.g., "Note: This traveler had a bad experience with this airline last month," "Warning: The transit hotel is currently reporting a power outage").
3.  **Autonomous Task-Delegation (Reverse)**:
    *   **Action**: The AI identifies tasks it CANNOT solve (e.g., "The user wants a personal favor from the hotel manager") and autonomously flags it for the human agent's attention with a "Briefer."
4.  **Compliance-Shadowing**:
    *   **Action**: The AI monitors the human agent's manual bookings to ensure they align with the "Agency-Policy" (CORP-002) and "Traveler-Wisdom" (FLW-005), flagging potential errors before they are finalized.

## 3. Data Schema: `Augmentation_Session_Control`

```json
{
  "session_id": "GWP-11221",
  "agency_user_id": "AGENT_MARIA_S",
  "target_traveler_id": "GUID_9911",
  "ai_draft_status": "READY_FOR_REVIEW",
  "draft_content": "Dear Mr. Smith, I have found 3 boutique options in Kyoto that match your preference for garden views...",
  "decision_support_pings": [
    { "type": "PERSONA_MATCH", "message": "Matches TWO-55221 preference for 'Quiet-Floor'." }
  ],
  "control_mode": "HUMAN_LED_AI_SUPPORTED"
}
```

## 4. Key Logic Rules

- **Rule 1: The 'Attribution-Transparency' Rule**: In the agency dashboard, it MUST be clear which parts of a plan were AI-generated vs Human-modified to maintain an audit trail of professional liability.
- **Rule 2: Handoff-Seamlessness**: If a human agent takes over a conversation, the AI MUST provide a 3-sentence "Executive-Summary" of the entire interaction to date so the human can jump in instantly.
- **Rule 3: Escalation-Priority**: Tasks involving "Emotional-Distress" or "Complex-Conflict-Resolution" are autonomously escalated to a human agent with "High-Priority" status.

## 5. Success Metrics (Augmentation)

- **Agent-Efficiency-Gain**: Reduction in "Time-to-Response" for human-led interactions.
- **Support-Utility-Score**: How often human agents use the AI's "Suggested-Drafts" without major edits.
- **Error-Detection-Rate**: Number of manual booking errors caught by the AI's "Compliance-Shadowing."
