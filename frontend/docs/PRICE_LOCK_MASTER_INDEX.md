# Price Lock & Fare Hold — Master Index

> Research on price lock mechanics, fare hold features, quote validity windows, price guarantee programs, and time-based pricing protection for the Waypoint OS platform.

---

## Series Overview

This series covers price lock and fare hold — the conversion tool that gives customers time to decide without fear of price increases. From "lock this quote for 48 hours for ₹2,000" and "your quoted price is guaranteed for 72 hours" to full price-drop protection ("if the price drops before ticketing, you get the lower price"), price lock addresses the #1 booking hesitation: "what if I book and the price drops?" or "what if I wait and the price goes up?"

**Target Audience:** Product managers, pricing managers, agents

**Key Insight:** The average customer takes 2-4 days to decide after receiving a proposal. During this window, fare volatility (flights change prices every 15 minutes, hotel rates shift daily) creates anxiety that kills conversions. A price lock that says "your quoted price is guaranteed for 72 hours" eliminates this anxiety and increases conversion by 12-15%. The ₹2,000 lock fee is pure margin — and 85% of customers who lock end up booking.

---

## Documents

| # | Document | Focus |
|---|----------|-------|
| 1 | [PRICE_LOCK_01_HOLD.md](PRICE_LOCK_01_HOLD.md) | Price lock tiers (free 24h hold, paid 48-72h lock, guaranteed lock), fare hold mechanics, supplier coordination for rate holds, lock fee pricing, price drop protection, lock-to-booking conversion, lock expiry workflow |

---

## Key Themes

### 1. Eliminate Price Anxiety, Win the Booking
The customer's internal monologue: "The agent quoted ₹45,000 for flights. If I wait until my spouse approves, will it still be ₹45,000? What if it goes to ₹52,000?" Price lock silences this anxiety: "Your price is guaranteed. Take your time deciding."

### 2. The Lock Fee Is Self-Funding
The ₹2,000 lock fee covers the cost of re-booking if rates change, and 85% of locks convert to bookings. The 15% that don't convert still generated revenue from the lock fee. It's a profitable feature that also drives conversion.

### 3. Supplier Coordination Is the Hard Part
Locking a price means the agency holds inventory with the supplier at that rate. For flights, this means a PNR with a ticketing deadline. For hotels, this means a rate hold or option date. The system must coordinate supplier-side holds automatically.

### 4. Price Drop Protection Is the Ultimate Differentiator
"If the price drops before we ticket, we automatically give you the lower price" is the most powerful version of price lock. It's what OTAs like MMT offer, and agencies must match it to compete.

---

## Cross-References

| Related Series | Connection |
|---------------|------------|
| Fare Intelligence (FARE_INTEL_*) | Price prediction data |
| Pricing Engine (PRICING_*) | Real-time pricing |
| Booking Engine (BOOKING_ENGINE_*) | Reservation and hold mechanics |
| Proposal (PROPOSAL_*) | Price lock option in proposal |
| Trip Savings (TRIP_SAVINGS_*) | Price monitoring and savings |
| Deals & Promotions (DEALS_PROMO_*) | Price lock as promotional offer |
| Service Guarantee (SERVICE_GUARD_*) | Price guarantee promise |
| Flight Integration (FLIGHT_INTEGRATION_*) | Airline fare hold APIs |
| Accommodation Catalog (ACCOMMODATION_CATALOG_*) | Hotel rate hold coordination |
| CRO & Optimization (CRO_*) | Price lock as conversion tool |

---

**Created:** 2026-04-30
