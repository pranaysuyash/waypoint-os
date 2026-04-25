# Financial Spec: Autonomous Reconciliation Loops (FI-003)

**Status**: Research/Draft
**Area**: Automated Reconciliation & Pricing Integrity

---

## 1. The Problem: "The Pricing Drift"
Between the time of "Booking" and "Settlement," prices can drift due to currency fluctuations, hidden vendor surcharges, or incorrect tax calculations. This "Drift" often ends up as uncollectible debt or lost margin.

## 2. The Solution: 'Pricing-Integrity-Engine' (PIE)

The PIE autonomously performs "Closing-the-Loop" between the Agency's projected cost and the Vendor's actual invoice.

### Reconciliation Tracks:

1.  **Currency-Drift Correction**:
    *   **Action**: If the settled amount differs from the projected amount by > 0.5% due to FX, the AI auto-allocates the delta to the "FX-Buffer-Account."
2.  **Tax-Mismatch Resolution**:
    *   **Action**: If a vendor charges a tax not seen in the original API response, the AI auto-audits the charge against the `Tax_Rule_Library` for that region.
3.  **Ghost-Charge Dispute**:
    *   **Action**: If a vendor bills for a "Cancelled" or "No-Show" segment that was already refunded, the AI auto-triggers a `Clawback_Claim` (SU-002).

## 3. Data Schema: `Reconciliation_Event`

```json
{
  "recon_id": "REC-1122",
  "vendor_id": "AIR-DELTA",
  "booking_ref": "PNR-XYZ123",
  "projected_cost": 850.00,
  "actual_invoice": 875.50,
  "delta": 25.50,
  "variance_type": "UNAUTHORIZED_FUEL_SURCHARGE",
  "resolution_action": "AUTO_DISPUTE_FILED",
  "status": "PENDING_VENDOR_RESPONSE"
}
```

## 4. Key Logic Rules

- **Rule 1: The 'Auto-Write-Off' Limit**: The AI can autonomously "Accept" a discrepancy up to `$5.00` to prevent the administrative cost of a dispute exceeding the recovery value.
- **Rule 2: Batch-Settlement Audit**: Instead of just per-transaction, the PIE performs "Batch-Level" audits to detect systemic vendor billing errors (e.g., "Vendor X is overcharging 1% on *all* LHR flights").
- **Rule 3: Feedback to Pricing**: Any systemic discrepancy (e.g., "Taxes in HKG are always 5% higher than API") is auto-fed back into the `Pricing_Model` to update future quotes.

## 5. Success Metrics (Reconciliation)

- **Unreconciled Balance**: Reduction in the total dollar amount of "Open/Unresolved" financial discrepancies.
- **Vendor Billing Accuracy**: Improvement in supplier invoice correctness over time.
- **Margin Protection**: Increase in net margin by capturing and disputing "Ghost-Charges."
