# Legal Spec: AI-Led Liability Assessment (LE-001)

**Status**: Research/Draft
**Area**: Risk Attribution & Indemnification

---

## 1. The Problem: "The Liability Vacuum"
In complex travel disruptions, the "Cause" is often multi-party. If the agency is blamed for a failure it didn't cause (e.g., a supplier outage), it can lead to massive legal costs or insurance premiums.

## 2. The Solution: 'Fault-Attribution-Matrix' (FAM)

The FAM is a logic engine that evaluates the `CanonicalPacket` against the "Terms & Conditions" to assign a `Liability_Percentage`.

### Attribution Categories:

1.  **Supplier Failure (External)**: (e.g., GDS outage, Airline technical fault).
    *   **Action**: Auto-trigger the `Indemnification_Notice` to the supplier.
2.  **Agency Error (Internal)**: (e.g., AI logic bug, database inconsistency).
    *   **Action**: Auto-notify the `Insurance_Agent` and prepare the `Settlement_Offer`.
3.  **Traveler Contributory Negligence**: (e.g., Traveler arrived late, provided wrong PII).
    *   **Action**: Preserve the `Traveler_Input_Log` as defense against refund requests.
4.  **Force Majeure (Act of God)**: (e.g., Volcano, Hurricane).
    *   **Action**: Trigger the `Natural_Disaster_Protocol` and limit liability per the "Standard Terms."

## 3. Data Schema: `Liability_Assessment`

```json
{
  "assessment_id": "LIAB-9988",
  "incident_id": "OE-1122",
  "fault_attribution": {
    "supplier": 0.90,
    "agency": 0.10,
    "traveler": 0.00
  },
  "primary_cause": "Supplier API Timeout during confirmation",
  "legal_posture": "DEFENSIVE_EXTERNAL",
  "next_action": "ISSUE_DEMAND_LETTER_TO_SUPPLIER_X",
  "confidence_score": 0.94
}
```

## 4. Key Logic Rules

- **Rule 1: The 'Duty-to-Mitigate'**: The AI must demonstrate that it took "Reasonable Steps" to fix the issue before accepting liability (e.g., "AI attempted re-booking 3 times on alternative carriers").
- **Rule 2: High-Value Threshold**: Any incident with a projected liability > $10,000 must be auto-escalated to "Human Legal Counsel" immediately.
- **Rule 3: Settlement-Ceiling**: The AI can autonomously authorize "Settlement-Goodwill" up to $500 to prevent escalation, provided the FAM score for 'Agency' is < 30%.

## 5. Success Metrics (Liability)

- **Unjustified Refund Rate**: % reduction in refunds paid for failures not caused by the agency.
- **Defense Readiness**: Time taken to produce a "Legally-Defensible Evidence Bundle" (Target: < 5 minutes).
- **Insurance Premium Stability**: Maintaining or reducing premiums by demonstrating robust AI risk-management.
