# Fin Spec: Tax-Compliance & VAT-Recovery (FIN-REAL-007)

**Status**: Research/Draft
**Area**: Financial Compliance & Corporate Recovery

---

## 1. The Problem: "The Lost 20%"
International business travelers (B2B) often overpay for their trips because they fail to reclaim Value Added Tax (VAT) on eligible expenses like hotels, meals, and transport. Reclaiming VAT across different jurisdictions (UK, EU, Japan) is a complex, manual task requiring specific "Tax-Compliant" invoices. Most companies leave this money on the table.

## 2. The Solution: 'Tax-Fulfillment-Protocol' (TFP)

The TFP allows the agent to act as a "Virtual-Tax-Accountant" by optimizing the itinerary for tax recovery.

### Recovery Actions:

1.  **VAT-Eligible-Expense-Identification**:
    *   **Action**: Categorizing every expense in the `Itinerary Object` (ITIN-001) by its VAT-reclaim eligibility in the specific destination country.
2.  **Tax-Compliant-Invoice-Request**:
    *   **Action**: At check-out, the agent autonomously pings the hotel's billing API to ensure the final invoice contains the necessary corporate tax-ID and address required for a valid reclaim.
3.  **VAT-Claim-Packet-Generation**:
    *   **Action**: Consolidating all compliant invoices and traveler data into a "Submission-Ready-Packet" for the traveler's finance department or a third-party VAT reclaim provider (e.g., Taxback International).

## 3. Data Schema: `VAT_Recovery_Audit`

```json
{
  "audit_id": "TFP-88221",
  "traveler_id": "GUID_9911",
  "itinerary_id": "ITIN-9911",
  "jurisdiction": "UNITED_KINGDOM",
  "total_spend_local": 4500.00,
  "est_vat_reclaimable_usd": 680.00,
  "invoice_compliance_status": "7/8_COMPLIANT",
  "missing_data_actions": [
    {"target": "HILTON_LON", "missing": "VAT_NUMBER", "status": "REQUESTED"}
  ],
  "recovery_verdict": "READY_FOR_RECLAIM"
}
```

## 4. Key Logic Rules

- **Rule 1: The 'B2B-Tax-ID-Auto-Injection'**: For all corporate bookings, the agent MUST autonomously inject the company's VAT/Tax-ID into the booking PNR to ensure compliant invoicing from the start.
- **Rule 2: Minimum-Threshold-Filter**: To avoid "Noise," the agent only flags VAT-reclaim opportunities where the net recovery is > $50.
- **Rule 3: Jurisdictional-Update-Watchdog**: The agent MUST continuously update its logic based on changes in international tax laws (e.g., new VAT reciprocity agreements between countries).

## 5. Success Metrics (Compliance)

- **VAT-Recovery-Yield**: Total $ value recovered/identified for corporate clients.
- **Invoice-Compliance-Rate**: % of final invoices that meet jurisdictional tax requirements.
- **Audit-Latency**: Time from "Trip-Completion" to "VAT-Packet-Ready" (Target: < 24 hours).
