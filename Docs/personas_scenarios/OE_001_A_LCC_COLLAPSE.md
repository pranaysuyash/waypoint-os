# OE-001-A: The 'LCC-332' Mid-Trip Collapse

**Persona**: Solo Agent (P1) + Traveler (S1)
**Scenario**: A low-cost carrier (LCC) goes bankrupt while a family of 4 is at the airport in Singapore. The system must detect the failure and trigger autonomous re-protection within the defined risk budget.

---

## 1. Situation

- **Travelers**: The Gupta family (2 adults, 2 children).
- **Location**: Changi Airport (SIN), Singapore.
- **Problem**: Their return flight to London (LHR) on 'LCC-332' is suddenly cancelled as the airline has ceased operations immediately.
- **Context**: The family is at the check-in desk. Stress levels are high. Local time is 9 PM.

### What is happening now
- The GDS issues an `HX` status for all segments of 'LCC-332'.
- The family is told by airport staff to "find their own way home."
- The primary agent is currently off-duty (9 PM).

---

## 2. What the System Should Do

### Step 1: Immediate Detection & Impact Analysis
- **Watchdog Signal**: The `IntegrityWatchdog` detects the `HX` status change in the `AuditStore`.
- **System Action**: Identify the trip as `CRITICAL` due to mid-trip displacement.

### Step 2: Autonomous Re-Protection Plan
- **Re-Shopping**: AI crawls GDS for immediate legacy carrier alternatives (e.g., Singapore Airlines, British Airways).
- **Constraint Check**: Ensure the new flight has 4 seats together and includes meals (Traveler Persona preference).
- **Risk Budgeting**:
  - Original Ticket: $1,200.
  - New Ticket: $1,800.
  - Delta: $600.
  - **Logic**: If `$600 < Risk_Budget` (Owner-defined), proceed to auto-book.

### Step 3: Crisis Communication
- **Traveler Notification**: Send a WhatsApp/SMS: "We've detected LCC-332 is grounded. Don't worry, we've secured 4 seats on SQ308 departing at 11 PM. Your new tickets are attached."
- **Internal Audit**: Log the autonomous action and the $600 spend for post-trip reconciliation.

---

## 3. Operational Logic & Rules

- **Rule 1**: Mid-trip travelers ALWAYS get prioritized for autonomous recovery.
- **Rule 2**: AI must not cancel the return leg of an existing booking unless the supplier failure is confirmed globally.
- **Rule 3**: Re-protection must include a "Traveler-Safe" rationale (e.g., "Re-booked on a legacy carrier for reliability").

---

## 4. Success Criteria

- **Latency**: Recovery plan generated within 120 seconds of GDS signal.
- **Accuracy**: New flight matches original class of service or better.
- **Commercial**: Spend is within the `Risk_Budget` threshold.
- **Sentiment**: Traveler sentiment score remains > 80 due to proactive response.

---

## 5. Case Study Execution Plan (Future)

- **Input**: `HX` status update via `POST /audit/events`.
- **System Trace**: Verify the transition from `Intake` -> `Crisis_Mode` -> `Autonomous_Booking`.
- **Verification**: Ensure the `AuditStore` shows the $600 debit from the `Risk_Budget` ledger.
