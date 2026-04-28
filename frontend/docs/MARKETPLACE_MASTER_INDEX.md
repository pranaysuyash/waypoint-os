# Travel Marketplace & Aggregator — Master Index

> Comprehensive research on travel deal aggregation, price comparison, dynamic deal generation, and multi-channel deal distribution.

---

## Series Overview

This series explores how Waypoint OS aggregates travel inventory from multiple suppliers, compares prices across sources, detects and generates deals, and distributes them through multiple channels. Aggregation and deal intelligence are key differentiators — helping agents find the best prices for clients and creating revenue opportunities through deal distribution.

**Target Audience:** Backend engineers, product managers, business development, affiliate managers

**Scale Target:** 10+ inventory sources, 500+ deals active at any time, 50+ distribution partners

---

## Documents

| # | Document | Focus |
|---|----------|-------|
| 1 | [MARKETPLACE_01_AGGREGATION.md](MARKETPLACE_01_AGGREGATION.md) | Multi-source inventory, data normalization, caching, unified search |
| 2 | [MARKETPLACE_02_COMPARISON.md](MARKETPLACE_02_COMPARISON.md) | Side-by-side comparison, TOPSIS value scoring, comparison UX |
| 3 | [MARKETPLACE_03_DEALS.md](MARKETPLACE_03_DEALS.md) | Deal detection, dynamic pricing, price forecasting, alerts |
| 4 | [MARKETPLACE_04_DISTRIBUTION.md](MARKETPLACE_04_DISTRIBUTION.md) | Multi-channel distribution, affiliate program, API marketplace |

---

## Key Themes

### 1. Multi-Source Intelligence
No single supplier has the best price on every route and hotel. Aggregating from 10+ sources and normalizing the data gives agents confidence they're offering the best available price.

### 2. Value Over Price
The cheapest option isn't always the best. TOPSIS-based value scoring balances price against quality, timing, inclusions, and flexibility — matching each traveler's priorities.

### 3. Deal as Revenue Channel
Deals aren't just discounts — they're a revenue channel. Flash deals drive urgency, affiliate distribution expands reach, and the API marketplace enables partner integrations.

### 4. Price Transparency
Price history, forecasting, and alerts give agents data-backed pricing advice. "Book now — prices will rise" or "Wait — expect a 15% drop" builds trust and saves clients money.

---

## Cross-References

| Related Series | Connection |
|---------------|------------|
| Supplier Integration (SUPPLIER_INTEGRATION_*) | Supplier API connectivity |
| Pricing Engine (PRICING_*) | Dynamic pricing algorithms |
| Agency Marketplace & Storefront (STOREFRONT_*) | Deal display on public storefront |
| Search Architecture (SEARCH_*) | Unified search across aggregated inventory |
| Destination Intelligence (DESTINATION_*) | Destination-specific deal context |
| Commission Management (COMMISSION_*) | Deal commission tracking |
| Partner & Affiliate Management (PARTNER_*) | Affiliate program infrastructure |

---

## Inventory Source Map

```
Travel Inventory Sources:
                    ┌─────────────┐
                    │   Amadeus    │ ← GDS (Flights)
                    └──────┬──────┘
                           │
┌─────────────┐    ┌──────┴──────┐    ┌─────────────┐
│  Hotelbeds   │ ←  │ Aggregation │ →  │    TBO      │ ← Consolidator
│  (Bedbank)  │    │   Engine    │    │ (Flights+   │
└─────────────┘    └──────┬──────┘    │  Hotels)    │
                          │           └─────────────┘
┌─────────────┐    ┌──────┴──────┐
│ Direct       │ ←  │ Normalized  │ →  Comparison & Deals
│ Connect      │    │   Search    │
│ (Taj/Marriott│    │   Index     │
└─────────────┘    └──────┬──────┘
                          │
                    ┌──────┴──────┐
                    │ Distribution │ → Storefront, WhatsApp, API, Affiliates
                    └─────────────┘
```

---

**Created:** 2026-04-28
