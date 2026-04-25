# Fin Spec: Post-Trip Expense-Harmonization (FIN-REAL-009)

**Status**: Research/Draft
**Area**: Financial Integrity & Corporate Automation

---

## 1. The Problem: "The Expense-Report-Nightmare"
For business travelers, the "Post-Trip-Expense-Report" is a massive administrative burden. Receipts are lost, currency conversions are inconsistent, and "Phantom-Charges" (erroneous mini-bar fees, double-billed room service) often go unchallenged because the traveler is too busy to audit every line item. Corporations lose millions to these small, aggregated errors.

## 2. The Solution: 'Receipt-Integrity-Sync-Protocol' (RISP)

The RISP allows the agent to act as a "Post-Trip-Auditor."

### Harmonization Actions:

1.  **Multi-Source Receipt-Matching**:
    *   **Action**: Autonomously matching PNR data (flights/hotels) with digital receipts from the agent's internal vault and the traveler's bank/credit-card statement.
2.  **Phantom-Charge-Detection**:
    *   **Action**: Auditing the final hotel "Folio" against the traveler's "Event-Log" (e.g., "Traveler was at a dinner meeting at 8 PM; mini-bar charge at 8 PM is likely an error").
3.  **Autonomous-Charge-Challenging**:
    *   **Action**: If a discrepancy is found, the agent autonomously pings the hotel's billing department with a "Correction-Request," citing the evidence from the traveler's verified itinerary.
4.  **Submission-Ready-Report-Generation**:
    *   **Action**: Generating a perfectly formatted expense report (CSV/PDF) that maps every expense to the specific corporate project code, including automated tax-categorization for VAT recovery (FIN-REAL-007).

## 3. Data Schema: `Expense_Integrity_Audit`

```json
{
  "audit_id": "RISP-88221",
  "traveler_id": "GUID_9911",
  "itinerary_id": "ITIN-9911",
  "total_spend_detected_usd": 4250.00,
  "discrepancies_identified": [
    {"vendor": "MARRIOTT_NYC", "type": "MINI_BAR", "amount_usd": 45.00, "status": "CHALLENGED_RECOVERED"}
  ],
  "project_code_mapping": "PROJECT-ALPHA-2026",
  "vat_reclaim_ready": true,
  "harmonization_status": "SYNCED_100_PERCENT"
}
```

## 4. Key Logic Rules

- **Rule 1: The 'Evidence-Based-Challenge'**: The agent MUST NOT challenge a charge unless it has a high-confidence "Itinerary-Conflict" (e.g., traveler was not in the room during the charge timestamp).
- **Rule 2: Currency-Basis-Sync**: All expenses MUST be harmonized using the exact exchange rate from the traveler's bank statement at the time of the transaction, not the generic daily rate.
- **Rule 3: Sovereign-Compliance-Check**: The agent MUST ensure that all receipts meet the specific tax-compliance requirements of the traveler's home country (e.g., IRS vs. HMRC rules).

## 5. Success Metrics (Efficiency)

- **Admin-Hours-Saved**: Average time reduction for the traveler to file a report.
- **Recovery-Yield**: Total $ value of "Phantom-Charges" successfully challenged and refunded.
- **Report-Accuracy**: % of expense reports accepted by corporate finance on the first pass (Target: 99%+).
