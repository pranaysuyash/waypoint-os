# Predict Spec: The Oracle (PREDICT-001)

**Status**: Research/Draft
**Area**: Predictive Intelligence & Alternative Data Mining

---

## 1. The Problem: "The Reactive Lag"
Official travel APIs (GDS, FlightStats) are reactive. By the time a flight is marked as "Cancelled," the best backup options are already gone. To win the "Scramble," the agent must act on "Probabilities," not just "Facts."

## 2. The Solution: 'Cascading-Probability-Forecasting' (CPF)

The CPF (nicknamed "The Oracle") mines alternative datasets to predict disruptions 2-12 hours in advance.

### Predictive Data Layers:

1.  **Labor Sentiment Mining**:
    *   **Action**: Analyzing social media and crew forum sentiment for signs of "Unannounced Strikes" or "Sick-outs" at specific hubs.
2.  **Climate-Logistics Correlation**:
    *   **Action**: Correlating high-resolution weather models with historical airport "Ground-Stop" thresholds (e.g., "This airport always closes if wind > 45 kts").
3.  **Aircraft-Age & Maintenance Telemetry**:
    *   **Action**: Tracking specific tail-number reliability and "Maintenance-Loop" duration to predict technical delays at departure.

## 3. Data Schema: `Disruption_Probability_Report`

```json
{
  "prediction_id": "ORC-9988",
  "target_event": "CANCEL_LH400_10MAY",
  "probability_score": 0.82,
  "confidence_interval": [0.75, 0.89],
  "signals": [
    {
      "source": "CLIMATE_MODEL_GFS",
      "impact": "HIGH",
      "description": "Wind gust forecast exceeds LHR-T5 safety threshold"
    },
    {
      "source": "SOCIAL_SENTIMENT_CREW",
      "impact": "MEDIUM",
      "description": "Increasing mention of 'Crew-Timeout' at Hub FRA"
    }
  ],
  "recommended_action": "PRE_EMPTIVE_SOFT_HOLD_BACKUP_FLIGHT"
}
```

## 4. Key Logic Rules

- **Rule 1: 'The Ghost-Booking'**: If probability > 0.80, the agent is authorized to "Soft-Hold" (book with 24h cancellation) a backup option BEFORE the primary flight is cancelled.
- **Rule 2: Probability-Weighted Budgeting**: The cost of "Soft-Holds" is balanced against the "Expected-Loss" of a full disruption.
- **Rule 3: Transparency-of-Inference**: Every predictive action must clearly state its "Sources of Inference" to the traveler (e.g., "I've held a backup because weather models suggest a high chance of a ground stop").

## 5. Success Metrics (Foresight)

- **Prediction Accuracy**: % of predicted disruptions that actually occurred (Precision).
- **Lead Time**: Average hours between "Agent-Action" and "Official-Cancellation-API-Alert."
- **Option Superiority**: % of times the "Pre-emptive" backup was better/cheaper than the "Reactive" options available after the cancellation.
