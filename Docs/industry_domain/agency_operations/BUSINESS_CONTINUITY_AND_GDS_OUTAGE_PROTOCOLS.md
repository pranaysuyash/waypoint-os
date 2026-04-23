# Domain Knowledge: Business Continuity & GDS Outage Protocols

**Category**: Quality, Resilience & Gig Economy  
**Focus**: What happens when the "Global Brain" (GDS) goes dark?

---

## 1. GDS Outage (The "Dark" Scenario)
- **Logic**: Amadeus, Sabre, or Travelport have a global system failure. No one can book, change, or cancel flights.
- **SOP**: **"The Offline Manual."**
    - **PNR Recovery**: Using locally cached PDFs of PNRs stored in the CRM.
    - **Direct-to-Airline**: Using the airline's own website or calling the "Airline Duty Manager" directly via a private line.

---

## 2. Agency "Redundancy" (Multi-GDS)
- **Logic**: A "Resilient" agency uses more than one GDS (e.g., Sabre for US, Amadeus for EU).
- **SOP**: If GDS A is down, move all "New" bookings to GDS B.

---

## 3. The "Manual" Ticket
- **Logic**: In an extreme crisis, "Paper" or "E-ticket" manual issuance.
- **SOP**: The agency has **"Blank Ticket Stock"** (virtual) and an agreement with the airline for manual reconciliation after the system is restored.

---

## 4. Cyber-Attack & "Clean Room" Ops
- **Logic**: The agency's network is compromised (Ransomware).
- **SOP**: Move operations to a **"Cloud-based Clean Room"** (Independent hardware) to continue servicing clients.

---

## 5. Proposed Scenarios
- **The "Total" Outage**: A client is at the airport. Their PNR is gone because the GDS is down. The agent must provide the **"Cached PNR History"** to the airline supervisor to manually board the client.
- **Ransomware Crisis**: All agency laptops are locked. The agent must use their **"Emergency Tablet"** with LTE connectivity to access the CRM and handle client calls.
- **The "Lost" Refund**: A refund was in progress when the GDS crashed. The agent must track the **"IATA Settlement"** manually to ensure the $10k didn't disappear into the void.
- **Satellite Phone Fallback**: All internet is down in the city. The agency uses a **"Satellite Link"** to connect to the GDS hub in a different continent.
