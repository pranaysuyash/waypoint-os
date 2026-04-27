# Fin Spec: Agentic 'Traveler-Trust-Score' Engine (FIN-REAL-032)

**Status**: Research/Draft
**Area**: Relationship Equity Scoring, Credit Policy & Service-Tier Governance

---

## 1. The Problem: "The Flat-Trust-Model"
Most agencies treat all travelers the same regardless of their history. A first-time traveler with an unclear intent profile gets the same level of credit extension and service autonomy as a 12-year loyalty client who has completed 40 trips. This "Flat-Trust-Model" both over-extends risk to unreliable travelers and under-serves elite loyal travelers who deserve a fundamentally different service tier.

## 2. The Solution: 'Relationship-Equity-Protocol' (RQP)

The RQP acts as the "Trust-Ledger-Manager."

### Trust Scoring Actions:

1.  **Multi-Dimension-Trust-Calculation**:
    *   **Action**: Calculating a dynamic "Traveler-Trust-Score" (0–100) across five dimensions:
        - **Longevity** (years as a client, weighted by recency)
        - **Financial-Reliability** (payment history, chargeback frequency, deposit discipline)
        - **Booking-Integrity** (cancellation rate vs. industry baseline, no-show history)
        - **Communication-Quality** (responsiveness, clarity, good-faith dealing)
        - **Advocacy-Value** (referrals generated, community contributions, testimonials)
2.  **Service-Tier-Assignment**:
    *   **Action**: Mapping Trust-Score bands to automatic service tiers:
        - **0–40 ("Emerging")**: Standard terms, deposits required, no credit extension.
        - **41–70 ("Established")**: Reduced deposit, priority response, early access to inventory.
        - **71–90 ("Trusted")**: Deferred payment options, VIP vendor introductions, dedicated concierge slot.
        - **91–100 ("Sovereign")**: Full credit flexibility, proactive luxury upgrades, direct owner hotline.
3.  **Risk-Flag-Detection**:
    *   **Action**: Automatically flagging patterns associated with high-risk traveler behavior: unusual last-minute booking spikes, repeated cancellations near penalty deadlines, mismatched identity signals across booking profiles.
4.  **Trust-Score-Transparency**:
    *   **Action**: Providing travelers with a plain-language "Relationship-Equity-Brief" on request — explaining what drives their score and what behaviors would elevate them to the next tier.

## 3. Data Schema: `Traveler_Trust_Profile`

```json
{
  "profile_id": "RQP-77221",
  "traveler_id": "TRAVELER_ALPHA",
  "trust_score": 87,
  "service_tier": "TRUSTED",
  "dimension_scores": {
    "longevity": 92,
    "financial_reliability": 95,
    "booking_integrity": 78,
    "communication_quality": 88,
    "advocacy_value": 82
  },
  "risk_flags_active": 0,
  "next_tier_gap": "4 points to Sovereign — driven by advocacy_value",
  "credit_extension_usd": 8000
}
```

## 4. Key Logic Rules

- **Rule 1: The 'No-Punitive-Secret-Scoring' Standard**: The Trust-Score framework MUST be disclosed to travelers. No hidden scoring that silently disadvantages them without their knowledge.
- **Rule 2: Score-Recovery-Pathway**: Any traveler whose score drops (e.g., after a cancellation) MUST be provided with a clear, actionable path to score recovery — not a permanent penalty.
- **Rule 3: Bias-Audit-Requirement**: The Trust-Score algorithm MUST be audited periodically for demographic bias. Dimensions MUST be behavior-based, never identity-based.

## 5. Success Metrics (Trust)

- **Tier-Upgrade-Velocity**: Average time for a new traveler to reach "Established" tier.
- **Sovereign-Tier-Retention-Rate**: % of "Sovereign" tier travelers who rebook year-over-year.
- **Risk-Flag-Accuracy**: % of risk-flagged travelers who subsequently exhibit the predicted problematic behavior (precision metric).
