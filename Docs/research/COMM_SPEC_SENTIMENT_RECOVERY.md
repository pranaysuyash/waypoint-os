# Comm Spec: Post-Crisis Sentiment Recovery (CO-003)

**Status**: Research/Draft
**Area**: Reputation Management & Traveler Trust

---

## 1. The Problem: "The Residual Stress of Travel Failure"
Even if a traveler is successfully re-booked, the stress of the disruption lingers. If the agency does not acknowledge the "Pain" of the experience, the traveler's long-term trust in the AI system degrades.

## 2. The Solution: 'Emotional-Debt-Reconciliation' (EDR)

The EDR engine calculates the "Intensity" of the disruption and auto-authorizes a gesture of goodwill.

### EDR Calculation Factors:

- **Total Delay Duration**: (e.g., > 6 hours = High Debt).
- **Modality Downgrade**: (e.g., First Class to Economy = Critical Debt).
- **Missed Life Events**: (e.g., Wedding, Deal Signing = Maximum Debt).
- **Traveler Sentiment**: (Detected via WhatsApp/Slack logs using Tier 1 Flash).

### Make-Good Tiers:

1.  **Tier 1 (Mild Disruption)**: 
    - Personal apology message + "Coffee on us" ($10 digital voucher).
2.  **Tier 2 (Significant Delay)**: 
    - Personal apology + $50 "Stress-Relief" credit (Uber/Dining).
3.  **Tier 3 (Massive Failure)**: 
    - Apology call from a Human + $200 Future-Travel-Credit + Next-Trip VIP upgrade.

## 3. Data Schema: `Sentiment_Recovery_Action`

```json
{
  "recovery_id": "REC-9922",
  "traveler_id": "DOE-01",
  "disruption_id": "T-4433",
  "emotional_debt_score": 85,
  "gesture_authorized": "TIER_2_STRESS_RELIEF",
  "message_draft": "We know yesterday was rough. Thank you for your patience during the LHR closure. Please enjoy dinner on us tonight ($50 credit added to your card).",
  "status": "SENT"
}
```

## 4. Key Logic Rules

- **Rule 1: The 'Apology-Window'**: The EDR gesture must be sent within 2-4 hours of the traveler reaching their destination. Too early feels robotic; too late feels forgotten.
- **Rule 2: Contextual-Awareness**: The apology MUST reference the specific failure (e.g., "Sorry about the 4-hour Frankfurt layover").
- **Rule 3: Frequency-Cap**: Limit EDR gestures to 1 per 3-month period to avoid "Gaming the System."

## 5. Success Metrics (Reputation)

- **Sentiment Rebound**: Increase in CSAT scores from "Post-Disruption" to "Post-Make-Good."
- **Traveler Retention**: High retention rates for travelers who experienced a Tier 2/3 disruption.
- **Brand Trust**: Qualitative positive mentions of the "Caring AI" in internal surveys.
