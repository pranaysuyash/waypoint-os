# Feature: Revenue Management & Markup Engine

## POV: Business / Agency Owner

### 1. Objective
To maximize yield and ensure financial transparency while automating complex commission and markup calculations across disparate suppliers (GDS, LCC, BedBanks, DMCs).

### 2. Functional Requirements

#### A. Multi-Tier Markup Logic
- **Global Base Markup**: Default % or flat fee applied to all non-net bookings.
- **Supplier-Specific Overrides**: e.g., +2% for expensive BedBanks, +0% for direct GDS.
- **Category Overrides**: High markup for "Experiences," low markup for "Air."
- **Customer-Tier Pricing**: Automated discounts or premium fees based on customer "Genome" (Loyalty/VIP status).

#### B. Commission & Incentive Tracking
- **GDS Segments Tracking**: Real-time counter of segments flown to track volume-based backend incentives from GDS providers.
- **BSP/ARC Reconciliation**: Automatic matching of IATA statements against internal booking records to identify missing commissions.
- **Override commission modeling**: Calculating potential "Backend overrides" from airlines if targets are met.

#### C. Fee Transparency & Hidden Margins
- **Net Fare Masking**: Ability to display a "Gross Price" to the customer while maintaining "Net + Markup" in the back-end.
- **Merchant of Record (MoR) Selection**: Dynamic routing of payments to decide who charges the client (Agency vs. Supplier) based on credit card fee arbitrage.

### 3. Business Logic (The "Engine" Logic)
- **Arbitrage Detection**: If Supplier A (Expedia) is $200 and Supplier B (Direct) is $180, the system automatically prices to the user at $205 and captures the $25 margin without agent intervention.
- **Tax & GST/TCS Calculation**: Automated Indian TCS (Tax Collected at Source) for international travel or GST compliance for corporate invoices.

### 4. Failure Modes & Safety
- **Negative Margin Alert**: Hard-block if a manual edit by an agent results in a price lower than the net cost.
- **Currency Fluctuation Buffer**: Automatic +1% "Currency Volatility Fee" for bookings in volatile markets (e.g., TRY, ARS) to prevent margin erosion between booking and settlement.
