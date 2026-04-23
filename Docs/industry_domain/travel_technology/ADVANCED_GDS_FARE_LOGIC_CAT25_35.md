# Domain Knowledge: Advanced GDS Fare Logic (Cat 25 & 35)

**Category**: Advanced Technical  
**Focus**: The hidden categories of fares that power agency profitability and specialized pricing.

---

## 1. ATPCO Categories (The "Code")
Airlines file their fares via **ATPCO** (Airline Tariff Publishing Company). There are 99 "Categories" of rules.
- **Category 25 (Fare-by-Rule)**: Used for "Dynamic" discounts (e.g., "Student Fares" or "Senior Fares").
- **Category 31 (Voluntary Changes)**: Defines how much it costs to change a ticket.
- **Category 33 (Voluntary Refunds)**: Defines the "No-show" penalty.

---

## 2. Category 35 (Negotiated/Net Fares)
- **Logic**: These are the "Secret Prices" given to specific agencies. 
- **The "Net" Price**: The price the agency pays the airline.
- **The "Selling" Price**: The price the agency charges the client.
- **SOP**: The agent must manually load the **"Account Code"** or **"Corporate ID"** into the GDS to "Trigger" the Cat 35 price.

---

## 3. "Auto-Pricing" vs. "Manual Construction"
- **Auto-Pricing**: The GDS calculates the fare based on the rules. (Safe).
- **Manual Construction**: The agent "Builds" the fare string line-by-line. (Risky).
- **Risk**: If the agent makes a mistake in "Manual Construction," the airline will issue an **ADM (Agency Debit Memo)** for the difference (often thousands of dollars).

---

## 4. The "Fare Quote" (FQ) Logic
- **Historical Fare Quote**: Used to calculate a refund for a ticket bought 6 months ago. The agent must "Re-wind" the GDS to the price on the day of purchase.

---

## 5. Proposed Scenarios
- **The "Account Code" Oversight**: An agent forgets to enter the corporate account code. The client is charged $5,000 instead of the negotiated $2,500. The agent must "Void & Re-issue" before the "Midnight Void" window closes.
- **The "Manual Construction" ADM**: An airline auditor discovers that an agent manually overrode a "Minimum Stay" rule. The airline sends an ADM for $1,200. The agency must decide whether to "Dispute" or "Pay."
- **Cat 35 "Privacy" Leak**: A net fare is accidentally printed on the client's receipt (IT/BT fare). The client sees the agency's 20% margin. The agent must explain the "Consolidated Value."
- **Historical Quote Mismatch**: A client wants a refund for a ticket from a bankrupt airline. The GDS cannot find the "Historical Fare." The agent must use the "Paper Ticket" archives to reconstruct the value.
