# Con Spec: Agentic 'Traveler-Sentiment' Real-Time Barometer (CON-REAL-035)

**Status**: Research/Draft
**Area**: Real-Time Emotional Intelligence, Frustration-Drift Detection & Proactive De-Escalation

---

## 1. The Problem: "The Invisible-Frustration-Accumulation"
Traveler dissatisfaction rarely arrives as a single explosion — it accumulates invisibly through dozens of small frustrations that no one notices or acts on. A slightly delayed response. A slightly incorrect hotel room. A slightly unhelpful vendor. Each is manageable in isolation. Together, they cross an invisible "Tipping-Point" that produces a scathing review or a churn decision. Without a "Sentiment-Barometer," the agency only discovers a problem when it's already a crisis.

## 2. The Solution: 'Emotional-Pulse-Protocol' (EPP)

The EPP acts as the "Emotional-Radar-System."

### Sentiment Actions:

1.  **Continuous-Sentiment-Scoring**:
    *   **Action**: Analyzing every traveler communication — message tone, response latency, emoji usage, word choice, punctuation patterns, and question frequency — to maintain a continuously updated "Sentiment-Score" (0–100, 0=extreme distress, 100=euphoric delight).
2.  **Drift-Detection**:
    *   **Action**: Monitoring the rate of sentiment change, not just the absolute score. A Sentiment-Score declining from 72 to 60 over 3 interactions is a "Drift-Signal" — even though 60 is not objectively negative. Early drift is the actionable signal.
3.  **Frustration-Source-Attribution**:
    *   **Action**: When a Drift-Signal is detected, analyzing the conversation to identify the probable frustration source: response delay, information gap, unmet expectation, vendor failure, or booking complexity.
4.  **Proactive-De-Escalation-Intervention**:
    *   **Action**: Before frustration reaches the "Tipping-Point" threshold (<50), the agent proactively intervenes: an unexpected upgrade offer, a personal check-in from the agency owner, a "we noticed and we're fixing it" message — with the specific frustration source addressed directly.

## 3. Data Schema: `Sentiment_Pulse_State`

```json
{
  "pulse_id": "EPP-77221",
  "traveler_id": "TRAVELER_ALPHA",
  "current_sentiment_score": 62,
  "drift_detected": true,
  "drift_rate": -4.0,
  "drift_period_interactions": 3,
  "probable_frustration_source": "RESPONSE_DELAY_PATTERN",
  "tipping_point_distance": 12,
  "intervention_triggered": true,
  "intervention_type": "PERSONAL_OWNER_CHECKIN"
}
```

## 4. Key Logic Rules

- **Rule 1: The 'Drift-Over-Absolute' Priority**: The agent MUST act on drift rate before absolute score. A score of 65 declining rapidly is more urgent than a score of 50 that has been stable for a week.
- **Rule 2: The 'Non-Intrusive-Intervention' Standard**: Proactive interventions MUST feel natural and caring, never like surveillance acknowledgment. The agent MUST NOT say "We noticed your messages seem frustrated." Instead: "We just wanted to check in and make sure everything feels right."
- **Rule 3: The 'Sentiment-Privacy' Boundary**: Sentiment analysis MUST operate on aggregate linguistic signals only — never claiming to diagnose emotional states definitively. The score is an operational signal, not a psychological assessment.

## 5. Success Metrics (Sentiment)

- **Pre-Crisis-Detection-Rate**: % of eventual negative reviews or churn events where the Sentiment-Barometer detected a Drift-Signal at least 48 hours prior.
- **Intervention-Recovery-Rate**: % of Drift-Signal interventions that result in the Sentiment-Score recovering above 70 within 24 hours.
- **Review-Score-Correlation**: Correlation between final Sentiment-Score and post-trip review rating (validation metric).
