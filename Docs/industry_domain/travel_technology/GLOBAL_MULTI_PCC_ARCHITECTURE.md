# Domain Knowledge: Global Multi-PCC Architecture

**Category**: Advanced Architecture  
**Focus**: Managing a global agency presence across multiple "Pseudo City Codes" (PCCs).

---

## 1. What is a PCC / OID?
- **PCC (Pseudo City Code)**: A 3–4 character code (Sabre/Travelport) identifying an agency office.
- **OID (Office ID)**: The Amadeus equivalent (e.g., `LONS12100`).
- **Logic**: Each PCC is tied to a specific "Point of Sale" (POS) and currency.

---

## 2. Follow-the-Sun Support
- **Logic**: A client in London calls at 2 AM. The call is routed to the Sydney office.
- **Multi-PCC Access**: The Sydney agent must have **"Branch Access"** or **"Bridging"** to view and edit the London PNR.
- **SOP**: The London office must `ES` (End Segment) with "Received From" data so the Sydney office knows who made the last change.

---

## 3. Rate Arbitrage (POS Brackets)
- **Logic**: An agency has a PCC in London and a PCC in Dubai.
- **SOP**: The agent searches both PCCs for the same flight. If the Dubai PCC shows a lower tax or a "Local Market Fare," the agent books in the Dubai PCC but "Queues" the PNR back to London for servicing.

---

## 4. Queue Management (The "Inbox")
- **Logic**: GDS "Queues" are like email folders for PNRs.
- **Queue 0**: Ticketing.
- **Queue 1**: Schedule Changes.
- **Queue 7**: Waitlist Clearances.
- **SOP**: A global agency must have a **"Queue Sweep"** protocol where the night office clears the "Schedule Change" queue for the day office.

---

## 5. Proposed Scenarios
- **The "Bridge" Failure**: The Sydney office cannot access a VIP London PNR because the "Security Bridge" was not set up correctly. The client is waiting on the phone.
- **Queue Overload**: The "Schedule Change" queue has 5,000 PNRs due to a strike. The agency must use an **"Auto-Script"** to process the simple ones and leave the complex ones for the agents.
- **Currency Mismatch**: A PNR is booked in the Dubai PCC (AED) but the client wants to pay in GBP. The agent must perform a **"Currency Conversion"** in the GDS or re-book in the London PCC.
- **The "Lost" PNR**: A PNR was queued to the wrong office and "Timed Out" from the queue. The agent must find the PNR using the "Alpha-Search" by traveler name.
