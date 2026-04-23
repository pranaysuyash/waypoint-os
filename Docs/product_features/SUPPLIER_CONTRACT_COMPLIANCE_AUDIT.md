# Feature: Supplier Contract Compliance Audit

## POV: Business / Agency Operations

### 1. Objective
To automate the verification of every booking against supplier-specific contract terms (GDS, Airline, BedBank) to prevent costly ADMs (Agency Debit Memos) and maximize incentive capture.

### 2. Functional Requirements

#### A. Automated Rule Engine (The "Contract Parser")
- **Fare Rule Audit**: Real-time checking of the "Cat 16" (Penalties) and "Cat 31" (Voluntary Changes) rules from the GDS against the actual PNR state.
- **Ticketing Time Limit (TTL) Monitor**: Proactive alerts to agents 2 hours before a PNR auto-cancels if not ticketed.
- **Commission Validity**: Checking if the selected "Tour Code" or "IT Code" is valid for the specific route and airline to ensure commission isn't clawed back later.

#### B. ADM Prevention Dashboard
- **Risk Score**: Every booking gets a "Debit Risk Score" (e.g., High risk if it's a cross-border LCC with complex baggage rules).
- **Historical ADM Learning**: If an agency received a $500 fine for "Churning" (repeatedly booking/cancelling), the system flags similar agent behavior immediately.

#### C. Incentive Maximization
- **Contract Tier Progress**: A dashboard showing how many more "Delta" tickets are needed this quarter to hit the next override commission tier.
- **Supplier Preference Routing**: When an agent searches for "NYC to London," the system highlights the airline where the agency has the highest incentive margin.

### 3. Business Logic
- **"The Compliance Guardrail"**: If an agent tries to "Issue Ticket" on a route that violates a supplier contract (e.g., back-to-back ticketing), the system requires a Senior Agent override.
- **Automated Refund Audit**: Matching the airline's refund calculation against the GDS data before the agent submits the refund request to the BSP.

### 4. Safety & Governance
- **Zero-Churn Enforcement**: Hard-blocking the ability to cancel and re-book the same PNR within a 24-hour window if the airline forbids it.
- **Waitlist Monitoring**: Automated clearance of waitlisted segments to prevent "Dead Segments" (HX) from being left in the PNR.
