# Operational Logic Spec: Emotional Triage & Sentiment ROI (OE-005)

**Status**: Research/Draft
**Area**: Priority Optimization & Loyalty Engineering

---

## 1. The Problem: "Uniform Urgency"
Currently, the system treats a 2-hour delay as a "Medium" urgency for everyone. However, a 2-hour delay for a business traveler going to a routine meeting is an annoyance, while a 2-hour delay for a traveler going to a funeral or a wedding is a catastrophe.

## 2. The Solution: Emotional Weighting

The system must implement an **Emotional Triage** engine that modifies the `Base_Urgency` score using a `Sentiment_ROI_Multiplier`.

### Scoring Formula:

`Final_Urgency = Base_Urgency * Emotional_Multiplier * Tier_Multiplier`

### Multiplier Table:

| Life Event / Context | Multiplier | Description |
| :--- | :--- | :--- |
| **Grief/Medical** | 5.0x | Funeral, emergency medical repatriation. |
| **Milestone** | 3.0x | Wedding, Anniversary, Honeymoon, Graduation. |
| **High-Stakes Business** | 2.5x | Board Meeting, Keynote, $1M+ Deal closing. |
| **Standard Leisure** | 1.0x | Routine vacation. |
| **Routine Business** | 0.8x | Internal meeting, site visit. |

## 3. Data Schema: `Emotional_Context`

```json
{
  "trip_id": "T-5566",
  "life_event": "HONEYMOON",
  "sentiment_signals": [
    { "type": "WhatsApp", "score": -0.8, "text": "I'm so upset, our dinner was cancelled!" }
  ],
  "calculated_multiplier": 3.0,
  "priority_level": "CRITICAL",
  "loyalty_roi_potential": "HIGH",
  "recommended_action": "Auto-book replacement dinner + send $100 apology credit immediately."
}
```

## 4. Key Logic Rules

- **Rule 1: Proactive Sentiment Scraping**: The system must extract "Life Event" keywords from initial booking notes and chat history (e.g., "Celebrating my 50th").
- **Rule 2: Surprise-and-Delight Trigger**: If an `Emotional_Multiplier > 2.0` traveler experiences ANY disruption, the system is authorized to spend up to 10% of the `Risk_Budget` on "Trust Repair" gifts without human approval.
- **Rule 3: Queue Jumping**: Travelers with high `Emotional_Multiplier` move to the top of the `ReviewQueue`, even if their technical disruption is minor.

## 5. Success Metrics

- **Sentiment Recovery Rate**: Percentage of high-emotion travelers whose sentiment score returns to >0 within 2 hours of disruption.
- **Lifetime Value (LTV) Lift**: Tracking the re-booking rate of travelers who received "Emotional Triage" vs. those who didn't.
- **Zero-Insensitivity**: Ensuring the AI never sends a "Routine" automated message to a traveler in a "Grief" state.
