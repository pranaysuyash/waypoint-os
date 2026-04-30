# GDS & NDC Integration — Master Index

> Research on Global Distribution System integration (Amadeus, Sabre, Travelport), New Distribution Capability (NDC) standard, API cost management, caching strategies, and multi-source inventory for the Waypoint OS platform.

---

## Series Overview

This series covers the technical backbone of travel inventory access — from GDS platforms (Amadeus, Sabre, Travelport) that provide 80%+ of flight inventory, to the emerging NDC standard that gives direct airline content access including ancillaries. For agencies processing 50+ bookings/month, API costs become a significant operational expense (₹10-20K/month) that requires active management through caching, batching, and rate limiting.

**Target Audience:** Backend engineers, integration architects, operations managers

**Key Insight:** Most small-to-mid Indian travel agencies access flight inventory through OTA portals (MakeMyTrip backend) rather than direct GDS connections, paying 2-5% commission on each booking. A direct GDS connection costs ₹5-10K/month in API fees but saves ₹15-50K/month in OTA commissions. The breakeven is 10-15 bookings/month — almost every active agency benefits from direct GDS access.

---

## Documents

| # | Document | Focus |
|---|----------|-------|
| 1 | [GDS_NDC_01_INTEGRATION.md](GDS_NDC_01_INTEGRATION.md) | GDS platforms (Amadeus, Sabre, Travelport) API suites and pricing, NDC standard and message flow, GDS vs NDC comparison, API cost management, caching strategies (flight 15min, hotel 60min), rate limiting, request queuing |

---

## Key Themes

### 1. GDS for Coverage, NDC for Richness
GDS provides complete airline coverage with reliable booking flows. NDC provides richer content (ancillaries, dynamic pricing, personalized offers) but limited airline participation. A hybrid approach gives agencies the best of both.

### 2. API Costs Are a Real Operational Expense
At ₹0.50-3 per API call, a busy agency making 200+ searches/day spends ₹10-20K/month on API costs alone. Smart caching (40-60% hit rate) and request batching (12% reduction) cut this nearly in half.

### 3. NDC Is the Future but Not Yet the Present
Airlines are investing heavily in NDC to bypass GDS intermediaries and offer direct, personalized content. Agencies that build NDC capability now will be ahead as the standard reaches critical mass (projected 2027-2028 for mainstream adoption in India).

### 4. Caching Is Not Optional
Travel API calls are expensive and relatively slow (200-500ms). Without aggressive caching, every customer inquiry triggers 3-5 API calls. With caching, 40-60% of requests are served from cache in <10ms.

---

## Cross-References

| Related Series | Connection |
|---------------|------------|
| Supplier Integration (SUPPLIER_INTEGRATION_*) | Low-level API integration patterns |
| Flight Integration (FLIGHT_INTEGRATION_*) | Flight-specific booking workflows |
| Pricing Engine (PRICING_ENGINE_*) | Dynamic pricing from GDS/NDC data |
| Dynamic Packaging (DYN_PACKAGE_*) | Package assembly using GDS inventory |
| Supplier Marketplace (SUPPLIER_MARKET_*) | Spot buying when GDS inventory exhausted |
| Booking Engine (BOOKING_ENGINE_*) | PNR/Order management |

---

**Created:** 2026-04-30
