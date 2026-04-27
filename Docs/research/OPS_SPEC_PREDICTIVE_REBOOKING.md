# Ops Spec: Agentic 'Predictive-Rebooking' Engine (OPS-REAL-028)

**Status**: Research/Draft
**Area**: Proactive Demand Prediction & Pre-emptive Trip Curation

---

## 1. The Problem: "The Reactive-Booking-Cycle"
Most travel agencies operate in a "Reactive" mode — they wait for the traveler to reach out with a new request. This creates a passive relationship where the agency has no control over the booking pipeline. High-value travelers often go months between bookings, and the agency has no intelligence on when the next booking is coming, which means they can't prepare curated options in advance or lock in favorable rates.

## 2. The Solution: 'Anticipatory-Demand-Protocol' (ADP)

The ADP acts as the "Trip-Forecast-Engine."

### Predictive Actions:

1.  **Behavioral-Cadence-Modeling**:
    *   **Action**: Analyzing the traveler's historical booking cadence (e.g., "Books 2-3 times per year, always plans 3 months ahead, travel peaks in April and October").
2.  **Intent-Signal-Detection**:
    *   **Action**: Monitoring traveler-authorized signals that suggest upcoming travel intent: vacation leave requests (if integrated with corporate calendar), school holiday calendars for family travelers, anniversary dates, and seasonal sentiment in conversations.
3.  **Pre-emptive-Curation-Window**:
    *   **Action**: In the 6-8 weeks before a predicted booking window opens, the agent begins pre-curating 2-3 trip concepts. When the traveler's intent signals peak, it proactively presents: "We've been thinking about you — here are three experiences we think you'd love for April."
4.  **Early-Rate-Locking**:
    *   **Action**: For travelers with high-confidence rebooking predictions, the agent identifies "Early-Rate-Opportunities" (e.g., hotel flash sales, airline fare dips) that match the predicted trip concept and alerts the owner to consider pre-emptive holds.

## 3. Data Schema: `Predictive_Rebooking_Signal`

```json
{
  "signal_id": "ADP-77221",
  "traveler_id": "TRAVELER_ALPHA",
  "predicted_booking_window": "2026-10-01 to 2026-10-15",
  "prediction_confidence": 0.84,
  "predicted_trip_archetype": "LUXURY_NATURE_RETREAT",
  "pre_curated_concepts": ["PATAGONIA_TREKKING", "BHUTAN_DZONG_CIRCUIT"],
  "early_rate_alerts": 2,
  "status": "CURATION_READY"
}
```

## 4. Key Logic Rules

- **Rule 1: The 'No-Pressure' Presentation**: Pre-curated trips MUST be presented as thoughtful recommendations, not sales pushes. The tone should be "We've been thinking about you," not "Book now."
- **Rule 2: Confidence-Threshold-Gate**: The agent MUST NOT trigger pre-emptive rate holds unless prediction confidence exceeds 0.75 AND the agency owner approves the financial commitment.
- **Rule 3: Signal-Consent-Boundary**: Intent signals from personal calendars or corporate systems MUST only be monitored with explicit traveler consent.

## 5. Success Metrics (Predictive)

- **Prediction-Accuracy-Rate**: % of predicted booking windows that result in an actual booking within ±3 weeks.
- **Proactive-Booking-Share**: % of total annual bookings that originate from proactive curation vs. traveler-initiated requests.
- **Rate-Savings-Generated**: Total value of early-rate locks secured before predicted demand windows opened.
