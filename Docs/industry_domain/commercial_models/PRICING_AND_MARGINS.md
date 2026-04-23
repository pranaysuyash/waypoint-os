# Pricing Models and Margins

Understanding the commercial logic of a travel agency is essential for the AI Agent to compute profitable and competitive quotes.

---

## 1. Rate Types

### Net Rates (Gross Minus Margin)
- **Definition**: The price the agency pays to the vendor. No commission is included.
- **Agency Action**: Adds a **Markup** (e.g., 10%) or a **Flat Fee** to arrive at the selling price.
- **Common For**: Hotels (via Bed Banks), DMCs, Packages.

### Commissionable Rates
- **Definition**: The "Public" price. The vendor pays the agency a percentage (e.g., 5-15%) after the traveler completes the trip.
- **Agency Action**: Sells at the public price. No markup needed, but cash flow is delayed.
- **Common For**: Direct Hotel bookings, Car rentals, some Cruise lines.

---

## 2. Revenue Streams

1. **Markup**: The difference between Net Rate and Selling Price. Usually 10-25% for international packages.
2. **Transaction Fees**: Flat fees for specific services (e.g., $50 visa assistance fee, $20 flight booking fee).
3. **Override / PLB (Productivity Linked Bonus)**: Extra commission paid by vendors if the agency hits a certain volume of bookings (e.g., 100 rooms/year).
4. **Cancellation/Change Fees**: Revenue generated from service fees when a traveler modifies a booking.

---

## 3. Financial Components of a Quote

A typical "Proposal" (NB03 output) includes:
- **Base Cost**: Flights + Hotels + Transport.
- **Add-ons**: Sightseeing, Insurance.
- **Statutory Taxes**: 
    - **GST (Goods and Services Tax)**: Varies by service (e.g., 5% on flights, 18% on service fees).
    - **TCS (Tax Collected at Source)**: Specific to outbound travel in certain jurisdictions (e.g., India 5-20%).
- **Margin**: The agency's profit.

---

## 4. Margin Protection Logic (NB02 focus)

The system must protect against **Margin Erosion**:
- **The "Floor"**: Minimum markup required to cover operational costs.
- **Dynamic Markup**: Increasing markup for high-effort/bespoke trips; reducing for price-sensitive "Price Shopper" (A1) personas.
- **Incentive Alignment**: Flagging high-commission vendors (e.g., "This hotel pays 15%, versus 10% for the other option").
