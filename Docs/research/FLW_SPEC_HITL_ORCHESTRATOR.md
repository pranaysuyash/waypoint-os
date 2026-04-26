# Flow Spec: Agentic Human-in-the-Loop (HITL) Orchestrator (FLW-REAL-017)

**Status**: Research/Draft
**Area**: Hybrid Intelligence & Escalation Logic

---

## 1. The Problem: "The AI Dead-End"
Even the most advanced AI agents will encounter "Edge-Cases" or "High-Stakes" situations that require human judgment, empathy, or complex negotiation. If an agent attempts to handle these situations poorly, it can lead to "Brand-Damage" or "Legal-Liability." Conversely, if an agent hands off *too many* simple tasks, it defeats the purpose of automation. There is a need for a "Precision-Escalation" engine.

## 2. The Solution: 'Hybrid-Intelligence-Protocol' (HIP)

The HIP manages the "Handshake" between AI and Humans.

### Escalation Actions:

1.  **Complexity-Threshold Detection**:
    *   **Action**: Monitoring the "Conversation-Depth" and "Entity-Complexity." If a traveler's request involves >3 interconnected changes (e.g., "Cancel flight, re-book hotel in a different city, and update my visa application"), the agent triggers an "Escalation-Warning."
2.  **Sentiment-Volatility Trigger**:
    *   **Action**: Monitoring the traveler's "Emotional-Tone" (via NLP). If the traveler displays "High-Frustration" (e.g., use of caps, repetitive questions, or negative sentiment tokens), the agent autonomously offers a "Human-Switch."
3.  **High-Value Incident Routing**:
    *   **Action**: Automatically escalating any incident involving "VIP-Travelers" or "High-Value-Claims" (e.g., >$2,000) to a senior human agent.
4.  **The 'Parallel-Support' Mode**:
    *   **Action**: Instead of a full handoff, the agent continues to "Draft-Responses" and "Fetch-Data" for the human agent, acting as a "Co-Pilot" during the manual resolution.

## 3. Data Schema: `HITL_Escalation_Event`

```json
{
  "event_id": "HIP-77221",
  "agency_id": "AGENCY_ALPHA_99",
  "traveler_id": "GUID_9911",
  "escalation_reason": "SENTIMENT_VOLATILITY_DETECTED",
  "incident_value_usd": 1200.00,
  "assigned_human_agent": "AGENT_SARAH_W",
  "ai_copilot_status": "DRAFTING_ACTIVE",
  "status": "ESCALATED_TO_HUMAN"
}
```

## 4. Key Logic Rules

- **Rule 1: The 'Golden-Handoff'**: When a handoff occurs, the agent MUST provide the human agent with a "3-Point-Summary" (Problem, Current Action, Recommendation) to minimize "Context-Regain-Latency."
- **Rule 2: The 'No-Loop' Rule**: The agent MUST NOT re-engage in autonomous mode for the same incident once a human has taken control, unless explicitly re-authorized by the human agent.
- **Rule 3: Transparency-Disclosure**: The traveler MUST be informed when they are transitioning from an AI agent to a human agent (e.g., "I'm bringing in one of our travel experts, Sarah, to help with this complex request").

## 5. Success Metrics (Escalation)

- **Escalation-Precision**: % of handoffs that were genuinely necessary vs. avoidable.
- **Resolution-Time (Hybrid)**: Total time from incident start to resolution in hybrid mode vs. full-manual mode.
- **Context-Transfer-Efficiency**: Human agent's rating of the AI-provided summary quality.
