# Ops Spec: Agentic 'Supplier-Intelligence' Network (OPS-REAL-030)

**Status**: Research/Draft
**Area**: Deep Vendor Intelligence, Operational Reliability & Hidden-Signal Tracking

---

## 1. The Problem: "The Star-Rating-Illusion"
Star ratings and OTA reviews are lagging, gamed, and surface-level. A hotel can maintain a 4.8-star rating while quietly cutting housekeeping staff, changing ownership to an inexperienced operator, or falling behind on maintenance. Agencies booking on "Reputation-Momentum" — trusting a vendor's past rating without current intelligence — are exposed to embarrassing failures. A single bad booking at a "trusted" property can destroy years of traveler trust.

## 2. The Solution: 'Vendor-Insight-Protocol' (VIP)

The VIP acts as the "Supplier-Intelligence-Analyst."

### Intelligence Actions:

1.  **Multi-Signal-Vendor-Profiling**:
    *   **Action**: Building a continuously updated intelligence profile for each supplier across dimensions beyond star ratings:
        - **Operational-Consistency**: Direct booking confirmation speed, response quality, error rates on past bookings.
        - **Staff-Stability-Index**: Key staff tenure signals (concierge, chef, GM) — stable staff is the single strongest predictor of consistent guest experience.
        - **Ownership-Change-Detection**: Company registry monitoring for ownership or management company changes that historically correlate with service quality dips.
        - **Maintenance-Signal-Tracking**: Planning application records, renovation permits, and seasonal closure patterns.
2.  **Real-Guest-Signal-Aggregation**:
    *   **Action**: Aggregating and semantically analyzing first-person guest accounts from the agency's own traveler feedback — not OTA reviews — to identify specific operational strengths and weaknesses with high confidence.
3.  **Vendor-Tier-Assignment**:
    *   **Action**: Dynamically assigning each vendor to an internal quality tier ("Preferred," "Approved," "Watch-Listed," "Suspended") based on the composite intelligence profile — independent of OTA star rating.
4.  **Proactive-Vendor-Watch-Alerts**:
    *   **Action**: When a previously "Preferred" vendor shows early deterioration signals (e.g., 3 consecutive traveler feedback scores below threshold, GM departure, ownership change), issuing a "Vendor-Watch-Alert" before any new bookings are made.

## 3. Data Schema: `Supplier_Intelligence_Profile`

```json
{
  "vendor_id": "RESORT_ALPHA_MALDIVES",
  "vendor_tier": "PREFERRED",
  "operational_consistency_score": 92,
  "staff_stability_index": 88,
  "ownership_change_detected": false,
  "last_real_guest_signal_date": "2026-04-15",
  "agency_traveler_avg_score": 4.7,
  "ota_star_rating": 5.0,
  "ota_rating_lag_days": 180,
  "watch_alert_active": false
}
```

## 4. Key Logic Rules

- **Rule 1: The 'Internal-Rating-Supremacy' Standard**: The agent MUST use the agency's internal vendor tier for booking decisions — never defaulting to OTA star ratings alone.
- **Rule 2: The 'Early-Warning-Threshold'**: A "Vendor-Watch-Alert" MUST trigger after any two of: (a) 3 consecutive below-threshold feedback scores, (b) key staff departure, (c) ownership/management change — regardless of OTA rating.
- **Rule 3: Vendor-Privacy-Balance**: Ownership and company registry monitoring MUST use only publicly available information sources. No access to non-public business intelligence.

## 5. Success Metrics (Supplier)

- **Early-Warning-Lead-Time**: Average days of advance warning before a vendor quality failure is confirmed by traveler feedback.
- **Preferred-Vendor-Satisfaction-Delta**: Difference in traveler satisfaction scores for "Preferred-Tier" vs. "Approved-Tier" vendor bookings.
- **Watch-Alert-Accuracy-Rate**: % of "Watch-Alert" vendors that subsequently confirmed quality degradation within 90 days.
