# Third-Party Travel API Connectors — Master Index

> Research on activity aggregators (Viator, Klook, GetYourGuide), hotel bedbanks (Hotelbeds, WebBeds), transfer APIs, insurance APIs, eSIM APIs, and unified API architecture for the Waypoint OS platform.

---

## Series Overview

This series covers the API ecosystem beyond GDS — the activity aggregators, hotel bedbanks, transfer providers, and insurance platforms that provide the non-flight components of travel packages. While GDS covers flights, these APIs cover everything else: tours, experiences, hotels, transfers, insurance, visas, and connectivity. A unified API architecture that searches across all providers, deduplicates results, and routes bookings optimally is the technical foundation for competitive pricing and comprehensive inventory.

**Target Audience:** Backend engineers, integration architects, product managers

**Key Insight:** The same hotel room can cost ₹22,000 via direct contract, ₹24,500 via Hotelbeds, or ₹28,000 via Booking.com. The same activity costs ₹2,800 on Klook or ₹3,200 on Viator. Multi-source comparison across APIs finds the best rate every time, saving ₹2,000-8,000 per booking — margin that goes directly to the agency's bottom line.

---

## Documents

| # | Document | Focus |
|---|----------|-------|
| 1 | [THIRD_PARTY_API_01_CONNECTORS.md](THIRD_PARTY_API_01_CONNECTORS.md) | Activity aggregators (Viator, Klook, GetYourGuide, Tiqets), hotel bedbanks (Hotelbeds, WebBeds, Stuba), transfer APIs, insurance APIs (Tata AIG, Chola MS), visa APIs, eSIM APIs (Airalo), unified API architecture with normalization and caching |

---

## Key Themes

### 1. Multi-Source Always Beats Single-Source
No single API has the best rate for every component. Direct contracts win for top destinations; bedbanks win for breadth; aggregators win for last-resort availability. Searching all sources and picking the best is the only way to guarantee competitive pricing.

### 2. Net Rate > Commission for Hotels
Hotel bedbanks provide net rates (agency controls markup), while OTAs provide commission (fixed percentage). For high-volume agencies, net rate access through bedbanks generates 2-3x more margin per booking than OTA commission.

### 3. Activities Are High-Margin Add-Ons
Activity aggregators pay 8-18% commission on experiences that cost ₹1,500-5,000. Bundling 3-4 activities into a package adds ₹500-2,000 commission per customer at near-zero operational cost (instant API booking, no supplier coordination).

### 4. Unified API Is Infrastructure, Not Feature
A unified API gateway that normalizes, deduplicates, and optimally routes bookings is foundational infrastructure. Every feature (dynamic packaging, price comparison, booking engine) depends on it. Building it once, well, unlocks everything else.

---

## Cross-References

| Related Series | Connection |
|---------------|------------|
| GDS & NDC (GDS_NDC_*) | GDS for flights + third-party for everything else |
| Dynamic Packaging (DYN_PACKAGE_*) | Package assembly using multi-source inventory |
| Supplier Marketplace (SUPPLIER_MARKET_*) | Spot buying when contracted + API inventory exhausted |
| Supplier Integration (SUPPLIER_INTEGRATION_*) | Low-level API integration patterns |
| Revenue Architecture (REVENUE_ARCH_*) | API commission as revenue stream |
| Pricing Engine (PRICING_ENGINE_*) | Multi-source rate comparison feeds pricing |
| Activities & Experiences (ACTIVITIES_*) | Activity-specific booking workflows |

---

**Created:** 2026-04-30
