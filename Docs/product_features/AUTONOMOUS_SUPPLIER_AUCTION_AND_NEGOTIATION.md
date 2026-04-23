# Feature: Autonomous Supplier Auction & Negotiation

## POV: Business POV (Margin Optimization)

### 1. Objective
To use AI to run real-time "Reverse Auctions" and negotiations with multiple suppliers (Hotels, DMCs, Charter Jets) to secure the lowest possible net price for group or high-value bookings.

### 2. Functional Requirements

#### A. The "Auction" Room
- **Automated RFP (Request for Proposal)**: When an agent identifies a group of 10+ travelers, the system sends an automated RFP to all vetted suppliers in the destination.
- **Real-time Bidding**: Suppliers can see (anonymously) the current "Best Bid" and can lower their price or add "Inclusions" (e.g., "Free Breakfast," "Late Check-out") to win the booking.
- **Dynamic Closing**: The auction closes automatically after 24 hours, and the system selects the "Best Value" bid based on the agency's "Sourcing Policy."

#### B. The "Negotiation Bot"
- **LLM-Driven Negotiation**: The AI chats with hotel sales managers via email or portal to "Haggle" for upgrades or fee waivers (e.g., "Our client is a regular at your chain; can you waive the resort fee?").
- **Margin "Squash" Prevention**: Ensuring that even in an auction, the agency maintains its "Minimum Required Margin."

#### C. Group-Pay Orchestration
- **The "Tilt" Model**: The booking is only "Locked" once a specific number of travelers have paid their deposit (Crowdfunding-style).
- **Individual Ledgering**: Even if it's one "Auctioned" package, every traveler in the group has their own invoice and payment plan.

### 3. Business Logic
- **Supplier "Desperation" Mapping**: Identifying which hotels have low occupancy for the specific dates and targeting them for "Aggressive" auctioning.
- **The "Waiver & Favor" Ledger**: Tracking "Favors" owed by suppliers (e.g., "The hotel cancelled our last group; they owe us a 10% discount on this one").

### 4. Safety & Governance
- **Supplier Vetting**: Only "Vetted" suppliers from the "Blacklist Network" are allowed into the auction room.
- **Legal Binding**: Every bid is a legally binding contract that is automatically "Injected" into the GDS if it wins.
