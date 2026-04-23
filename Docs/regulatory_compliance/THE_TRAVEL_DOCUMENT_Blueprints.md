# Domain Knowledge: The Travel Document Ecosystem

**Category**: Documentation & Health  
**Focus**: The essential artifacts that move a traveler through the supply chain.

---

## 1. The PNR (Passenger Name Record)
- **Logic**: The "Digital Soul" of the trip. A 6-digit alphanumeric code (e.g., `H8J2K9`).
- **Data Points**: Itinerary, Passenger data (APIS), Payment status, and "Remarks."
- **SOP**: The agent must distinguish between the **"Agency PNR"** and the **"Airline PNR"** (which are often different).

---

## 2. The Voucher (Service Confirmation)
- **Logic**: A "Guarantee of Payment" for hotels, cars, and transfers.
- **SOP**: The voucher must include the **"Confirmation Number"** from the hotel's own system (not just the agency's).
- **Format**: Digital (PDF/App) is standard, but some "Remote" DMCs still require a physical printout.

---

## 3. The Manifest (Passenger List)
- **Logic**: Required for Cruises, Charters, and Group Tours.
- **SOP**: Must match the **"Passport Name"** exactly. One typo can prevent boarding on a private jet or ship.

---

## 4. The E-Ticket (Electronic Ticket)
- **Logic**: Different from a PNR. The E-Ticket is the **"Financial Proof"** (13-digit number).
- **SOP**: If a PNR says "Confirmed" but has no "E-Ticket Number," the traveler cannot fly. The agent must verify the **"Ticket Status"** (Open/Used/Void).

---

## 5. APIS (Advance Passenger Information System)
- **Logic**: Mandatory passport/visa data sent to governments before the flight.
- **SOP**: The agent must enter APIS data into the GDS `DOCS` field to avoid check-in delays.

---

## 6. Proposed Scenarios
- **The "Un-ticketed" PNR**: A client arrives at the airport with a "Confirmation Code," but the agency never "Issued" the E-ticket. The client is denied boarding.
- **Voucher Rejection**: A hotel refuses to check in a guest because the voucher doesn't have the hotel's internal "Confirmation ID."
- **Manifest Mismatch**: A traveler is denied entry to a cruise ship because their middle name was missing from the manifest.
- **Remark Overload**: A PNR has too many "Remarks" (Free-text fields), causing the airline's system to crash the file. The agent must "Clean" the PNR.
