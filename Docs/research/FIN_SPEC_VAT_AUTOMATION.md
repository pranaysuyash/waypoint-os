# Fin Spec: Global Tax-Incentive-Audit (FIN-REAL-005)

**Status**: Research/Draft
**Area**: Financial Recovery & International Trade

---

## 1. The Problem: "The Abandoned Refund"
International travelers often spend thousands on high-value goods (fashion, electronics, jewelry) in countries with high Value Added Tax (VAT), such as France, Italy, or the UK. While they are legally entitled to refunds of 12-20%, the process of collecting physical forms, getting customs stamps, and submitting paperwork at the airport is so friction-heavy that an estimated $2B+ in refunds goes unclaimed annually.

## 2. The Solution: 'Global-Tax-Incentive-Protocol' (GTIP)

The GTIP allows the agent to act as a "Tax-Recovery-Officer."

### Recovery Actions:

1.  **Receipt-Digitization-Audit**:
    *   **Action**: Analyzing the traveler's digital receipts (via email/photo) to identify items that exceed the "Minimum-Spend-Threshold" for a VAT refund in that specific country.
2.  **Digital-Form-Preparation**:
    *   **Action**: Autonomously pre-filling the digital refund forms (e.g., Global Blue, Planet) using the traveler's passport and address data from the secure vault (ID-REAL-001).
3.  **Customs-Kiosk-Routing**:
    *   **Action**: Identifying the exact location of the "Digital-Tax-Kiosk" (e.g., PABLO kiosks in France) at the traveler's departure airport and providing a map and "T-Minus-3h" reminder.
4.  **Refund-Status-Tracking**:
    *   **Action**: Monitoring the status of the refund via the provider's API until the funds are returned to the traveler's card, autonomously filing a "Follow-Up-Inquiry" if the refund is delayed >30 days.

## 3. Data Schema: `VAT_Refund_Engagement`

```json
{
  "engagement_id": "GTIP-88112",
  "traveler_id": "GUID_9911",
  "country": "FRANCE",
  "total_spend_eur": 2500.00,
  "estimated_refund_eur": 300.00,
  "provider": "GLOBAL_BLUE",
  "form_id": "GB-992211-Z",
  "customs_stamp_required": "DIGITAL_PABLO",
  "airport": "CDG",
  "status": "AWAITING_CUSTOMS_VALIDATION"
}
```

## 4. Key Logic Rules

- **Rule 1: The 'Eligibility-Threshold' Audit**: The agent MUST check the specific country's rules (e.g., in France, a single receipt must be >€100.01) before alerting the traveler.
- **Rule 2: The 'Physical-Goods-Constraint'**: The agent MUST remind the traveler that items being claimed MUST be "Unused" and "Available-for-Inspection" at the customs kiosk.
- **Rule 3: Refund-Method-Optimization**: The agent autonomously selects the most efficient refund method (e.g., Direct-to-Card vs Cash-at-Airport) based on the traveler's "Currency-Settlement-Preferences" (FIN-REAL-003).

## 5. Success Metrics (Financial)

- **Claim-Capture-Rate**: % of eligible high-value purchases successfully identified by the agent.
- **Refund-Recovery-Ratio**: Actual USD recovered vs. potential USD eligible for refund.
- **Administrative-Friction-Reduction**: Reduction in traveler time spent on tax paperwork (target: <5 mins).
