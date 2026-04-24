# Area Deep Dive: Complex Commercial Reconciliation

**Domain**: Commercial Operations  
**Focus**: Multi-party payment splitting, commission tracking, refund management, and multi-currency reconciliation.

---

## 1. Multi-Party Payment Splitting (The "Group Bill" Crisis)
When 5 families travel together (S2), they often want separate invoices but a single "Group Discount" or shared activity costs.

### Scenario A: Fractional Payment Failure
- **Trigger**: A group of 4 travelers splits a $10,000 villa booking. Three pay their share ($2,500 each), but the fourth traveler's card fails or they dispute the charge.
- **Complexity**: The agency has already committed the full $10,000 to the supplier.
- **System Action**:
    1. Detect the "Payment Delta" ($2,500).
    2. Identify the "Coordinator" (S2) responsible for the group.
    3. AI drafts a "Reconciliation Brief": "Group payment is 75% complete. Traveler D payment failed. Total exposure: $2,500. Propose solution: Hold booking for 24h or re-split the delta among remaining 3 parties."

---

## 2. Multi-Currency Margin Erosion
Agencies often buy in one currency (e.g., USD for hotels in Dubai) and sell in another (e.g., INR to an Indian traveler).

### Scenario B: The "FX Pivot" Loss
- **Trigger**: A trip is quoted when 1 USD = 83 INR. The traveler pays 30 days later when 1 USD = 85 INR.
- **Risk**: Margin erosion. The 2% shift might eat the agency's entire 5% commission.
- **System Action**:
    1. Track "Quote-Time FX" vs "Payment-Time FX".
    2. Flag "Margin Warning" to the Agency Owner (P2) if erosion exceeds 1%.
    3. Propose "Dynamic Pricing Adjustment" for future quotes on that route.

---

## 3. Commission & Kickback Tracking
Ensuring the agency actually *gets paid* by the suppliers.

### Scenario C: Post-Trip Commission Audit
- **Trigger**: 30 days after a traveler returns, the system checks if the hotel has paid the 10% commission.
- **Action**:
    1. Cross-reference `AuditStore` records with "Incoming Commission Reports".
    2. Flag missing payments.
    3. Autonomic Ghost Concierge (Playbook D) sends a "Commission Inquiry" to the hotel's finance desk.

---

## 4. Implementation Grounding: Commercial Models

To resolve these gaps, we propose a `CommercialLedger` model to track the flow of money distinct from the trip state:

| Entity | Purpose |
|-------|---------|
| `CommercialLedger` | (PROPOSED) Atomic transaction log: Who owes who, in what currency, and current status. |
| `PaymentSplitPlan` | (PROPOSED) Mapping of total trip cost to individual traveler shares. |
| `FXExposureLog` | (PROPOSED) Tracking real-time margin risk based on currency fluctuations. |

---

## 5. Targeted Evaluation Scenarios

The following scenarios should be generated to test these boundaries:
1. `sc_comm_group_split_partial_failure.json`
2. `sc_comm_fx_margin_erosion_alert.json`
3. `sc_comm_missing_commission_recovery.json`
4. `sc_comm_multi_tax_gst_invoice.json`
