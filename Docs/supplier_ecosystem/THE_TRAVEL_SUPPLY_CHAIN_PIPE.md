# Domain Knowledge: The Travel Supply Chain "Pipe"

**Category**: Connectivity & Supply Chain  
**Focus**: The hierarchy of how inventory moves from the supplier to the traveler.

---

## 1. The Inventory Source (The Tier 1)
- **Entities**: Airlines, Hotels, Cruise Lines, Car Rentals.
- **Action**: They define the "Yield" (Price) and "Allotment" (Availability).

---

## 2. The Aggregators (The Tier 2 "Pipes")
- **GDS (Global Distribution Systems)**: Amadeus, Sabre, Travelport. (The "Old Guard").
- **Bedbanks / Wholesalers**: Hotelbeds, WebBeds. (Buy in bulk, sell at "Net").
- **DMCs**: Local experts who aggregate local tours/transfers.

---

## 3. The Retailers (The Tier 3)
- **OTAs (Online Travel Agencies)**: Expedia, Booking.com. (Volume, low-touch).
- **Traditional Agencies**: (High-touch, service-oriented).
- **Meta-search**: Skyscanner, Google Travel. (Marketing layer, not a booking layer).

---

## 4. The Payment Flow (The Reverse Supply Chain)
- **Flow**: Traveler -> Agency -> Aggregator -> Supplier.
- **Friction**: Every "Node" in the chain takes a 3–15% cut.
- **SOP**: The agent must know where they are in the chain. "Am I buying from the hotel directly (Commissions) or from a wholesaler (Markups)?"

---

## 5. Proposed Scenarios
- **The "Aggregator Failure"**: A bedbank goes bust. The hotel hasn't been paid, even though the traveler paid the agency. The agency must "Double Pay" to keep the traveler in the room and then fight the bedbank liquidator.
- **The "Over-aggregation" Error**: A room is sold through 4 different aggregators. By the time the agent hits "Book," the inventory is gone. The agent must find the "Source" (Tier 1) for a direct fix.
- **The "Markup Conflict"**: An agency accidentally lists the "Net" price on the client's invoice instead of the "Gross" price.
- **Direct vs. GDS**: A hotel offers a "Direct Only" special that isn't in the GDS. The agent must book it manually and charge a "Booking Fee" since there is no commission.
