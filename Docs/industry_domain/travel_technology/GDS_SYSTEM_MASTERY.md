# Domain Knowledge: GDS System Mastery

**Category**: Travel Technology  
**Focus**: PNR structure, TST, and Queue management in Amadeus/Sabre.

---

## 1. The PNR (Passenger Name Record)

The PNR is the "Source of Truth" for every booking. It is a 6-character alphanumeric code (e.g., `Z9X2R4`).

### Mandatory Elements (PRINT)
- **P**: Phone (Agency or Traveler contact).
- **R**: Received From (Who requested the booking).
- **I**: Itinerary (Flight segments).
- **N**: Name (Exactly as per passport).
- **T**: Ticketing (Time limit or Ticket number).

### Critical Remarks
- **OSI (Other Service Information)**: General info for the airline (e.g., `OSI BA VIP TRAVELER`).
- **SSR (Special Service Request)**: Actionable requests (e.g., `SSR VGML` for Vegan Meal, `SSR WCHR` for Wheelchair).

---

## 2. Pricing & TST (Transitional Stored Ticket)

### Fare Calculation
- **TST**: The "Stored Fare" inside the PNR. It contains the Base Fare, Taxes, and Fees.
- **Auto-Pricing (FXP/WP)**: Commands to let the system find the best fare.
- **Manual Pricing**: Used for complex multi-city trips where auto-pricing fails.

### ADMs (Agency Debit Memos)
- **Risk**: If an agent issues a ticket with a lower fare than the airline rules allow, the airline issues an ADM to recover the difference + a penalty.
- **Operational SOP**: Every TST must be audited by a Senior Agent (P2) or an automated "Fare Audit" tool before issuance.

---

## 3. Queue Management

The GDS uses "Queues" (like digital mailboxes) to communicate.

### Essential Queues
- **Queue 0 (Schedule Change)**: Where the airline tells you they've moved a flight.
- **Queue 1 (Ticketing Time Limit)**: Warning that the booking will cancel if not ticketed.
- **Queue 23 (Waitlist Confirmation)**: When a waitlisted seat becomes available.

### SOP for Queue Clearing
1. **Morning Check**: Every agent must clear their assigned queues by 10 AM.
2. **Actioning**: If a flight is cancelled (UN status), the agent must find an alternative and re-book (TK status).
3. **Synchronization**: Update the traveler (Phase 3) and the internal CRM.

---

## 4. Operational Best Practices
- **Never "Fake" Names**: Airlines use AI to detect "Test" PNRs and will fine the agency.
- **Clean the PNR**: Remove "Cancelled" (HX) or "Waitlisted" (HL) segments immediately to avoid GDS churn fees.
- **Security**: Use "Terminal Emulators" with two-factor authentication.
