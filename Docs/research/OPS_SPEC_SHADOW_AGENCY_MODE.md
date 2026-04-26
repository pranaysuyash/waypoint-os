# Ops Spec: Agentic 'Shadow-Agency' Mode (OPS-REAL-025)

**Status**: Research/Draft
**Area**: Operational Quality & Redundancy

---

## 1. The Problem: "The Human-AI Knowledge Gap"
As agencies transition to AI-agentic models, there is often a "Quality-Drift" between how a human agent handles an incident and how the AI would handle it. Human agents may miss "Agentic-Arbitrage" opportunities (e.g., a specific loyalty-point-plus-cash re-booking), while the AI might miss "Nuanced-Human-Preferences" (e.g., a traveler's unstated preference for a specific airport lounge). Without a "Parallel-Audit" system, the agency cannot measure the true ROI of its AI vs. Human workforce.

## 2. The Solution: 'Operational-Redundancy-Protocol' (ORP)

The ORP allows the agent to act as a "Digital-Twin" to the human agency.

### Shadow Actions:

1.  **Parallel-Incident-Processing**:
    *   **Action**: Running in the background for human-handled incidents. The agent "Drafts" its own solution and compares it against the human's "Final-Action."
2.  **Efficiency-Gap Identification**:
    *   **Action**: Quantifying the "Differential-in-Outcome" (e.g., "The AI identified a re-booking option that was $150 cheaper than the human's choice").
3.  **Agent-Burnout Prediction**:
    *   **Action**: Monitoring the human agent's "Decision-Latency" and "Sentiment-Fatigue." If a human agent starts making sub-optimal choices after 6h of active support, the AI flags "Potential-Burnout" to the owner.
4.  **Shadow-Training Loop**:
    *   **Action**: Using human decisions that outperformed the AI's draft to "Fine-Tune" the local agent's weights and preference models (TWO).

## 3. Data Schema: `Shadow_Audit_Record`

```json
{
  "audit_id": "ORP-77221",
  "human_agent_id": "AGENT_SARAH_W",
  "incident_id": "INC-9911",
  "human_decision": "REBOOK_LH_450",
  "ai_shadow_decision": "REBOOK_UA_221",
  "outcome_differential_usd": 145.00,
  "human_advantage_noted": ["PERSONAL_RAPPORT", "LOCAL_VEND_KNOWLEDGE"],
  "status": "AUDIT_LOGGED"
}
```

## 4. Key Logic Rules

- **Rule 1: The 'Non-Interference' Mandate**: In Shadow Mode, the agent MUST NOT communicate with the traveler or the human agent unless explicitly invited to "Assist."
- **Rule 2: Objective-Comparison-Schema**: Outcomes MUST be compared across multiple dimensions (Cost, Speed, Traveler Satisfaction, Compliance) to ensure a balanced audit.
- **Rule 3: Respectful-Feedback-Loop**: Audit reports for the agency owner MUST highlight human "Super-Powers" (e.g., high-EQ moments) alongside "AI-Efficiency-Wins."

## 5. Success Metrics (Redundancy)

- **Shadow-Decision-Alignment**: % of cases where the AI's shadow draft matched the human's final action.
- **Identified-Savings-Leakage**: Total USD identified in sub-optimal human decisions across a billing cycle.
- **Knowledge-Transfer-Rate**: Number of "Human-Edge-Cases" successfully ingested into the AI's logic per month.
