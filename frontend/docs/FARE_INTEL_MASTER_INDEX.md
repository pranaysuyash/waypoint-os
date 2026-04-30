# Flight Fare Intelligence — Master Index

> Research on AI-powered flight fare prediction, price alerts, booking timing optimization, and buy-now-vs-wait recommendations for the Waypoint OS platform.

---

## Series Overview

This series covers flight fare intelligence — the system that monitors, predicts, and alerts on flight pricing to help agents and customers book at optimal times. From historical fare analysis and real-time monitoring to AI-powered buy-now-vs-wait recommendations and flash sale alerts, fare intelligence saves customers money and gives the agency a competitive advantage over static-pricing competitors.

**Target Audience:** Product managers, data scientists, travel agents

**Key Insight:** Booking at the right time saves 15-30% on airfare — often ₹3K-10K per person on international routes. An agency that tells customers "wait 2 weeks, prices will drop" and is right builds enormous trust. An agency that tells customers "book now, prices are about to rise" and is wrong loses credibility. Fare intelligence makes timing advice data-driven instead of guessed.

---

## Documents

| # | Document | Focus |
|---|----------|-------|
| 1 | [FARE_INTEL_01_PREDICTION.md](FARE_INTEL_01_PREDICTION.md) | Data sources, prediction model (seasonal, advance-purchase, demand, anomaly), fare alert types, booking timing rules for Indian routes |

---

## Key Themes

### 1. Data-Driven Timing Advice
"The best time to book Delhi-Singapore for June is 6-8 weeks before departure" is infinitely more valuable than "you should book soon." Agents armed with data become trusted advisors, not salespeople.

### 2. Flash Sales Win Loyalty
Detecting an IndiGo flash sale (40% below normal) and alerting the customer within minutes creates a "my agent is looking out for me" moment that no booking platform can replicate.

### 3. Prediction Confidence Matters More Than Precision
Customers don't need to know the exact future price. They need to know: "Is this a good price? Should I book now or wait?" Direction + confidence > exact number.

### 4. Alerts Keep Customers Engaged
A customer who sets a target price of ₹20K for their route stays connected to the agency for weeks. Each alert is a touchpoint that keeps the agency top-of-mind and builds the relationship before the booking.

---

## Cross-References

| Related Series | Connection |
|---------------|------------|
| Flight Integration (FLIGHT_INTEGRATION_*) | GDS and airline API connections |
| Pricing Engine (PRICING_ENGINE_*) | Dynamic pricing for package pricing |
| GDS/NDC (GDS_NDC_*) | Fare data from GDS platforms |
| Customer Onboarding (CUSTOMER_ONBOARD_*) | Fare alerts as engagement tool |
| Email Marketing (EMAIL_MKTG_*) | Fare alert email delivery |
| WhatsApp Business (WHATSAPP_BIZ_*) | Fare alert WhatsApp delivery |
| Revenue Architecture (REVENUE_ARCH_*) | Fare intelligence as margin optimization |

---

**Created:** 2026-04-30
