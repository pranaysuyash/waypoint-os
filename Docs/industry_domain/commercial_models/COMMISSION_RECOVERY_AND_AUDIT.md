# Domain Knowledge: Commission Recovery & Audit

**Category**: Commercial Models  
**Focus**: Revenue leakage, hotel reconciliation, and automated recovery.

---

## 1. The "Commission Gap"

Industry data shows that **15-20% of hotel commissions** are never paid unless tracked and claimed.

### Common Failure Points
- **No-shows**: The hotel claims the guest didn't arrive.
- **Direct Bookings**: The hotel claims the guest booked direct (overriding the agent's IATA).
- **Early Departure**: The commission was calculated on 7 nights, but the guest stayed 3.

---

## 2. Recovery Strategies

### The "Onyx/Commission-Plus" Workflow
- **Logic**: Using a third-party consolidator to track all GDS hotel bookings.
- **Process**:
    1. Agent books in GDS.
    2. Data flows to the recovery tool.
    3. Tool waits for "Check-out Date" + 30 days.
    4. Tool sends an automated "Invoice" to the hotel.
    5. Hotel pays the tool; tool pays the agency (minus a 3-5% fee).

---

## 3. Manual Audit SOP (The "Last Resort")

For hotels not in the consolidated networks (e.g., small boutique hotels), the agency must perform manual recovery.

### The "Recovery Letter"
- **Timing**: 60 days post check-out.
- **Content**: Copy of the PNR, Guest Folio (if available), and the "Agreed Commission %."
- **Persistence**: If no response in 14 days, escalate to the "Director of Sales" at the hotel.

---

## 4. GDS Commission Tracking

### The "TST" (Transitional Stored Ticket) Audit
- **Logic**: Ensuring the commission % in the GDS matches the "Airlines Commission Agreement."
- **Risk**: If the agent enters "0" commission by mistake, the agency loses the revenue.
- **System Action**: Automated script to check for "$0" commission on non-economy fares.

---

## 5. Revenue Leakage: "The Invisible Drain"

### Credit Card Chargebacks
- **Logic**: If a client disputes a charge, the agency may lose the commission *and* the base fare.
- **Prevention**: Always get a signed "Credit Card Authorization Form" for every booking.

---

## 6. Proposed Scenarios
- **The "No-Commission" Trap**: An agent books a hotel at a "Net Rate" but forgets to add a markup. The agency performs the work for $0 profit.
- **Hotel "Direct-Capture"**: A hotel convinces the traveler to book their next stay "Direct" while they are on-site. The agent must detect this and contact the hotel for a "Referral Commission."
- **Commission Reclaim Failure**: A hotel has gone bankrupt. The agency must write off the commission.
