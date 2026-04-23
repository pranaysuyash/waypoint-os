# Domain Knowledge: Route Types & PNR Logic

**Category**: Traveler Taxonomy  
**Focus**: The geometry of travel and how it is codified in the GDS.

---

## 1. Point-to-Point (The "Simple" Route)
- **Logic**: A to B and back.
- **GDS Code**: `LHR-JFK-LHR`.
- **SOP**: Focused on the "Best Time" vs. "Best Price."

---

## 2. Open-Jaw (The "Triangle")
- **Logic**: Fly into one city, depart from another.
- **Example**: Fly London -> New York. Take a train to Boston. Fly Boston -> London.
- **GDS Code**: `LHR-JFK // BOS-LHR` (The `//` represents the "Surface" segment).
- **SOP**: The agent must ensure the "Surface" segment is logged so the airline doesn't cancel the return leg for "No-show."

---

## 3. Circle Trip / Multi-Stop
- **Logic**: A-B-C-D-A.
- **Example**: London -> Dubai -> Singapore -> Sydney -> London.
- **SOP**: Use "Round-the-World" (RTW) fares (e.g., Star Alliance / OneWorld) which are often cheaper than booking separate segments.

---

## 4. The "Hidden City" (Skiplagging) - WARNING
- **Logic**: Booking A-B-C because it's cheaper than A-B, then getting off at B.
- **SOP**: **STRICTLY FORBIDDEN** in professional agencies. Airlines will bill the agency (ADM) for the price difference and may cancel the traveler's loyalty account.

---

## 5. Hub & Spoke vs. Non-stop
- **Logic**: Many corporate travelers (S1) demand "Non-stop" to save time.
- **SOP**: If a connection is required, ensure it is through a "Preferred Hub" (e.g., Munich/Singapore for ease of transfer) vs. a "Stress Hub" (e.g., CDG/JFK).

---

## 6. Proposed Scenarios
- **The "Surface" Deletion**: An agent books an Open-Jaw but forgets to mark the surface segment. The airline cancels the return ticket.
- **RTW Fare Break**: A client wants to change one leg of a 10-stop RTW trip. The agent must recalculate the "Mileage Logic" to ensure the entire ticket doesn't re-price to $20k.
- **Skiplagging Detection**: A client asks to skiplag to save $200. The agent must explain the "ADM Risk" and the risk of the traveler being "Blacklisted."
- **The "Impossible" Hub**: The system suggests a 45-minute connection in Heathrow (Terminal 2 to Terminal 5). The agent must manually override to a 90-minute connection.
