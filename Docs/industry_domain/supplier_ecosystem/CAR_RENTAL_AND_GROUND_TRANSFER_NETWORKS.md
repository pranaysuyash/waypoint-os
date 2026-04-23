# Domain Knowledge: Car Rental & Ground Transfer Networks

**Category**: Supplier Ecosystem  
**Focus**: GDS Car Integrations, Chauffeur services, and Airport Transfers.

---

## 1. GDS Car Integrations (The "Big Three")

Hertz, Avis/Budget, and Enterprise/National are the primary GDS-integrated providers.

### Key PNR Fields
- **CD Number (Corporate Discount)**: The most critical field for corporate rates and insurance inclusion.
- **Flight Info**: Must be linked to the car booking so the rental desk knows if the flight is delayed.
- **SOP**: Always confirm if the rate includes **LDW (Loss Damage Waiver)** and **ALI (Additional Liability Insurance)**.

---

## 2. Professional Chauffeur Services (Limo)

For VIPs (S1), standard Uber/Lyft is not acceptable.

### Quality Markers
- **"Meet & Greet"**: Driver waits at the gate with a name board.
- **"Buffer Time"**: Scheduling the pickup 30-45 mins *after* landing to allow for immigration.
- **SOP**: Use "GNET" or "LimoLink" integrated providers to ensure real-time tracking of the driver's location.

---

## 3. Airport Transfers (DMC / Wholesale)

In international markets, transfers are often booked via DMCs.

### The "No-Show" SOP
- **Logic**: If the traveler doesn't see the driver, they will take a taxi and demand a refund.
- **SOP**: Provide the traveler with the **Driver's WhatsApp/Phone Number** and the **Emergency Dispatch Number** in the Final Itinerary.

---

## 4. One-Way Rentals & Drop Fees

- **The "Drop-off" Trap**: Renting in one city and dropping in another can trigger a $500+ "Drop Fee" that isn't always visible in the initial GDS quote.
- **SOP**: Explicitly confirm "Drop-off Charges" for all multi-city car rentals.

---

## 5. Proposed Scenarios
- **The "Missing Driver"**: A VIP arrives at 2 AM in Istanbul; the driver is nowhere to be found. The agent must find an alternative "VIP Transfer" immediately.
- **The "LDW Dispute"**: A client returns a rental car with a scratch. The rental company charges their card $1000 because the "CD Number" didn't include insurance.
- **The "Size Mismatch"**: A family of 5 books a "Standard SUV," but with 10 suitcases, it doesn't fit. The agent must upgrade them to a "Minivan" or "Large SUV" at the airport.
- **The "Flight Delay" Loop**: A flight is delayed 6 hours. The car rental agency cancels the "No-Show" booking. The agent must ensure the rental desk holds the car.
