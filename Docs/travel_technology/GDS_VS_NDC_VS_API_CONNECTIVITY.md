# Domain Knowledge: GDS vs. NDC vs. API Connectivity

**Category**: Connectivity & Technology  
**Focus**: The technical plumbing differences and their operational impact.

---

## 1. GDS (The Legacy "Blue Screen")
- **Tech**: EDIFACT (1960s protocol).
- **Pros**: Global standard; handles complex Interline re-bookings perfectly.
- **Cons**: High "GDS Fees" passed to agencies; limited rich content (no photos of seats).

---

## 2. NDC (New Distribution Capability)
- **Tech**: XML/JSON (Modern API standard by IATA).
- **Pros**: Airlines can sell "Ancillaries" (Wi-Fi, Baggage, Lounge) directly; no GDS surcharges.
- **Cons**: "Fragile" connections; hard to change/cancel an NDC ticket compared to GDS.
- **SOP**: Use NDC for simple point-to-point; stick to GDS for multi-city/interline.

---

## 3. Direct APIs (The "Silo")
- **Logic**: Connecting directly to a hotel's Central Reservation System (CRS) via a custom API.
- **Pros**: Real-time availability; bypasses all middlemen.
- **Cons**: Each supplier needs a different API; massive "Tech Debt" for the agency.

---

## 4. Aggregator APIs (The "Connector")
- **Logic**: Using a single API (e.g., Duffel, Travelfusion) to access 100+ LCCs (Low-Cost Carriers) and NDC sources.

---

## 5. Proposed Scenarios
- **The "NDC Servicing Nightmare"**: An agent books an NDC ticket for a client. The client wants to change the flight. The GDS "Change" command doesn't work. The agent must go to the airline's "Direct Portal" and perform a manual sync.
- **API Timeout**: A client is booking a $10,000 cruise via an API. The API times out at the payment stage. The agent must check the "Log" to see if the payment went through before trying again (preventing double charge).
- **The "Rich Content" Sell**: A client asks why the agency's price is $50 higher than the airline's site. The agent uses the **NDC "Rich Content"** to show that the agency price includes "Free Seat Selection and Priority Boarding" which the airline site hid.
- **GDS Surcharge Crisis**: An airline adds a $20 "GDS Fee" per segment. The agent must explain to the corporate client why the bill just went up by $40.
