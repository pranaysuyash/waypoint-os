# Domain Knowledge: Mid & Back-Office Integration

**Category**: Travel Technology  
**Focus**: Data synchronization, commission tracking, and financial reconciliation.

---

## 1. The "Data Flow" Architecture

A booking travels through three distinct layers:
1. **Front-Office (The Booking)**: GDS (Amadeus), NDC (Direct), or Aggregator (TBO).
2. **Mid-Office (The Management)**: CRM and Itinerary management (e.g., Umapped, Travefy).
3. **Back-Office (The Accounting)**: Financial settlement and commission tracking (e.g., TravelWorks, Agresso).

---

## 2. Interface Cards (I-Cards)

When a PNR is ticketed in the GDS, it generates an **Interface Record** (also called an I-Card or Interface Message).

### The Handshake
- **Process**: The GDS sends a data packet containing:
    - Ticket Number
    - Passenger Names
    - Itinerary Details
    - Base Fare, Taxes, and **Commission Amount**.
- **System Action**: The Back-Office system "consumes" this packet and automatically creates a "Sales Ledger" entry.

---

## 3. Commission Tracking & Reconciliation

This is where agencies lose the most money if not automated.

### The "Claim" Workflow
- **Issue**: Hotels often "forget" to pay commissions after a guest checks out.
- **SOP**: The system must track every hotel booking and trigger a "Commission Claim" if the payment is not received within 60 days of check-out.
- **Consolidation**: Using services like **Onyx CenterSource** to aggregate and collect global hotel commissions.

---

## 4. Reconciliation with Banks (BSP/ARC)

### BSP (Billing and Settlement Plan)
- **Logic**: Every Tuesday, IATA sends a "Billing Statement" showing all tickets issued by the agency.
- **SOP**: The Back-Office team must reconcile the IATA statement against the internal "Sales Ledger" before the cash is pulled from the bank account on Wednesday.

---

## 5. Operational Best Practices
- **Unique IDs**: Every trip must have a "Master Trip ID" that links the GDS PNR, the CRM lead, and the Back-Office invoice.
- **Error Logs**: Monitor the "Interface Error Log" daily for I-Cards that failed to sync (e.g., due to a misspelled name or missing tax code).
- **Automation**: Automate the "Commission Receipt" entry for airfares, as these are usually deducted at the time of ticketing (Instant Commission).
