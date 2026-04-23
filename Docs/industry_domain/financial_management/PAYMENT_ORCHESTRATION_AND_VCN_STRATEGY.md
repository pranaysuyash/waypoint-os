# Domain Knowledge: Payment Orchestration & VCN Strategy

**Category**: Financial Management  
**Focus**: B2B payments, Virtual Card Numbers (VCNs), and cash flow optimization.

---

## 1. The "Virtual Card" (VCN) Revolution

Instead of using a single corporate credit card, agencies generate a unique VCN for every supplier payment.

### Benefits
- **Security**: The card is locked to a specific amount and a specific merchant (e.g., "Marriott Paris").
- **Reconciliation**: Every transaction is automatically linked to a PNR/Booking ID.
- **Rebates**: Agencies earn "Interchange Rebates" (0.5% - 1.5%) on every VCN transaction, creating a new revenue stream.

---

## 2. Payment Orchestration

### The "Split" Payment SOP
- **Logic**: A client pays $5,000. $4,000 goes to the airline, $800 to the hotel, and $200 is the agency's commission.
- **SOP**: Use a "Payment Orchestrator" (e.g., Stripe, Adyen, Airwallex) to automatically split the funds at the point of sale.

---

## 3. "Merchant of Record" (MoR) vs. "Agency of Record"

- **Merchant of Record**: The agency takes the payment and appears on the client's bank statement. (High risk, high control).
- **Agency of Record**: The client's card is passed directly to the supplier (e.g., the airline). The agency only takes a "Service Fee." (Low risk, low control).

---

## 4. Fraud Mitigation in B2B

- **The "Over-charge" Block**: VCNs can be set to allow only 5% tolerance above the quoted price to prevent suppliers from adding "Hidden extras" without approval.

---

## 5. Proposed Scenarios
- **The "VCN Rejection"**: A small boutique hotel in Italy refuses to accept a "Virtual Card" and demands a "Physical Card" or Bank Transfer.
- **The "Double Charge"**: Both the agency (via VCN) and the traveler (at checkout) are charged for the room. The agent must mediate the "Double Payment" recovery.
- **Rebate Audit**: The agency's finance team finds that $10,000 in "VCN Rebates" are missing from the monthly statement.
- **MoR Liability Crisis**: A client's data is breached, and since the agency is the "Merchant of Record," they are legally responsible for the credit card data loss.
