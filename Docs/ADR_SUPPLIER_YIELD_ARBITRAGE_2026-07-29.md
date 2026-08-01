# ADR: Supplier Yield Arbitrage & Margin Optimization Engine

**Status**: Accepted  
**Date**: 2026-07-29  
**Context**: Waypoint OS Commercial Yield Optimization (Priority #6)

---

## Context

Travel agencies operate across multiple sourcing channels (Direct Preferred Contracts, GDS Preferred Rates, Bedbanks/Wholesalers). Commission percentages and net rates vary significantly across providers for identical room types or flights.

Planners frequently lock bookings with lower-margin suppliers simply due to default search ordering, forfeiting agency profit.

---

## Decision

Implemented the Yield Arbitrage Engine & UI Drawer (`spine_api/routers/yield_arbitrage.py` and `YieldArbitragePanel.tsx`):

1. **Yield Opportunities Endpoint (`GET /api/v1/yield/arbitrage/{trip_id}`)**:
   - Scans supplier rate options and ranks them by net margin ($), commission %, and suitability match score.
   - Calculates `potential_margin_gain` representing the profit uplift between optimal vs lowest margin suppliers.
2. **1-Click Supplier Swap (`POST /api/v1/yield/swap-supplier`)**:
   - Allows planners to swap the selected supplier with 1-click on the agency workbench, persisting `selected_supplier` and locking higher yield.
3. **Workbench Integration (`YieldArbitragePanel.tsx`)**:
   - Renders visual rate cards with net profit highlights and suitability scores.

---

## Consequences

- Direct commercial margin uplift for travel agencies on every booked trip.
- Prevents accidental selection of low-commission wholesale channels when direct preferred contracts offer higher yield.
