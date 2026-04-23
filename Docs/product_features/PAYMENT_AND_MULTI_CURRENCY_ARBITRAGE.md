# Feature: Payment & Multi-Currency Arbitrage

## POV: Business / System Core

### 1. Objective
To optimize the financial flow of bookings by navigating global currency markets, payment gateways, and credit card fee structures to maximize agency margin.

### 2. Functional Requirements

#### A. Multi-Currency Ledger
- **Parallel Market Pricing**: Ability to book in a foreign currency (e.g., EUR) while charging the client in their local currency (e.g., INR) using a real-time "Spread-Managed" exchange rate.
- **FX Risk Mitigation**: Locked exchange rates for 24-48 hours during the "Option Selection" phase to prevent quote slippage.

#### B. Intelligent Payment Routing
- **Merchant of Record (MoR) Selection**: Choosing whether the Agency charges the card (and pays supplier later) or the Supplier charges directly (and pays agency commission), based on card processing fees (e.g., Amex vs. Visa).
- **Split Payments**: Ability for a group of 5 travelers to each pay their portion of a single PNR/Booking.

#### C. Compliance & Tax Automation
- **GST/TCS Calculation (India Specific)**: Automated calculation of GST on service fees and TCS on international remittances for Indian agencies.
- **Invoice Orchestration**: Generating multi-entity invoices (e.g., one for the Corporate entity, one for the Traveler for "Personal Upgrades").

### 3. Business Logic
- **"The Yield Engine"**: If the system detects that a hotel is 10% cheaper if booked in its local currency (e.g., THB), it automatically executes the foreign currency booking and pockets the arbitrage.
- **Chargeback Defense**: Automatically capturing digital signatures and "Terms of Service" acceptance for every booking to provide evidence in case of a credit card dispute.

### 4. Safety & Security
- **PCI-DSS Compliance**: No credit card data is stored on-platform; all payments are tokenized via secure gateways (Stripe, Razorpay, Adyen).
- **Fraud Detection**: Flagging high-value, last-minute bookings from new customers for manual fraud review.
