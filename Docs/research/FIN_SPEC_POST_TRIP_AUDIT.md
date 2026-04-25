# Fin Spec: Post-Trip Reconcile & Audit (FIN-REAL-004)

**Status**: Research/Draft
**Area**: Financial Settlement & Consumer Protection

---

## 1. The Problem: "The Sneaky Charge"
Post-trip, travelers rarely check their itemized folios for errors. Hotels frequently "Double-Bill" for resort fees, add "Erroneous" minibar charges, or fail to apply prepaid credits. By the time the traveler notices on their credit card statement, the dispute window is narrowing. The agency needs to "Close-the-Loop" financially.

## 2. The Solution: 'Folio-Fidelity-Protocol' (FFP)

The FFP allows the agent to act as a "Post-Trip-Auditor" by reconciling final receipts against the original booking contract.

### Auditor Actions:

1.  **OCR-Folio-Ingestion**:
    *   **Action**: Autonomously requesting (or accepting from the traveler) the itemized PDF/Image of the final receipt.
2.  **Contract-to-Folio-Mapping**:
    *   **Action**: Comparing every line-item (Room Rate, Taxes, Resort Fees, Parking) against the `Itinerary Object` (ITIN-001).
3.  **Discrepancy-Auto-Flagging**:
    *   **Action**: Identifying "Unrecognized-Charges" (e.g., "$14 for a bottle of water" that the traveler claims they didn't touch).
4.  **Autonomous-Dispute-Assembly**:
    *   **Action**: Generating a "Draft-Dispute-Letter" or "Support-Email" to the vendor citing the specific discrepancy and the booking contract.

## 3. Data Schema: `Folio_Audit_Result`

```json
{
  "audit_id": "FFP-88221",
  "itinerary_id": "ITIN-9911",
  "vendor": "MARRIOTT_NYC",
  "booked_total": 450.00,
  "actual_folio_total": 492.50,
  "discrepancies": [
    {"type": "DOUBLE_TAX", "amount": 22.50, "status": "CONFIRMED_ERROR"},
    {"type": "UNRECOGNIZED_F_B", "amount": 20.00, "status": "NEEDS_TRAVELER_REVIEW"}
  ],
  "recovery_action": "EMAIL_SENT_TO_HOTEL_BILLING"
}
```

## 4. Key Logic Rules

- **Rule 1: The 'Tolerance-Threshold'**: Discrepancies < $2.00 are logged but not actioned (to avoid "Noise").
- **Rule 2: The 'Resort-Fee-Watchdog'**: If a resort fee was listed as "Included" in the booking but appears on the folio, the agent MUST flag this as a "Critical-Contract-Violation."
- **Rule 3: Evidence-Packet-Handoff**: If the vendor refuses to refund, the agent MUST package the audit as an "Evidence-Packet" for a bank chargeback (FIN-SPEC-CHARGEBACK-DEFENSE).

## 5. Success Metrics (Recovery)

- **Recovery-Yield**: Total $ value recovered for travelers through folio audits.
- **Audit-Completion-Rate**: % of trips where a final receipt was successfully reconciled.
- **Vendor-Correction-Speed**: Average time from "Audit-Flag" to "Vendor-Refund."
