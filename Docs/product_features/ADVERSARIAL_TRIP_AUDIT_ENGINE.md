# Feature: Adversarial Trip Audit Engine

## POV: Business POV (Quality Control)

### 1. Objective
To deploy a "Red Team" AI that constantly attempts to find flaws, price-drops, or better alternatives to the current itinerary, ensuring the agency always provides the "Absolute Best" option.

### 2. Functional Requirements

#### A. Continuous Price-Drop Re-Shopping
- **The "Savings Bot"**: Every 4 hours, the engine re-checks prices for the exact PNR segments across all GDS and OTA sources. If a price drop >$50 is found (including change fees), it alerts the agent to "Re-issue & Save."
- **Markup Protection**: Ensuring that a price drop results in either a "Customer Refund" (Loyalty) or "Increased Agency Margin" (Profit) based on the specific agency policy.

#### B. The "Disruption Simulator"
- **"What-If" Stress Testing**: Before an agent sends an itinerary, the AI simulates 100 failure scenarios (e.g., "What if the 1-hour layover is missed?", "What if the driver is late?").
- **Friction-Point Identification**: Flagging itineraries with a "Friction Score" > 7 (e.g., "This route has 3 transfers and a 4 AM check-in; traveler will be exhausted").

#### C. Competitor Shadowing
- **Market Benchmarking**: AI crawls public OTA prices (Expedia, Booking.com) to ensure the agency's "Total Package Price" isn't being undercut by more than 5%.
- **Secret Shopper Logic**: Anonymously checking "Hidden Member Rates" on hotel sites to see if the agency's "Net Rate" is still competitive.

### 3. Business Logic
- **Self-Healing Itineraries**: If a flight is cancelled, the Adversarial Engine automatically finds the "Next Best 3 Options" before the agent even sees the notification.
- **Agent Performance Auditing**: Identifying "Lazy Booking" patterns (e.g., an agent always booking the first hotel in the list rather than the one with the best margin).

### 4. Safety & Governance
- **"Conflict of Interest" Check**: Ensuring the system isn't recommending a hotel *just* because it has a high commission, if the hotel has recent bad reviews for safety or cleanliness.
- **Audit Trail of Audits**: Logging every time the engine suggested a change and whether the human agent accepted or rejected it (Learning Loop).
