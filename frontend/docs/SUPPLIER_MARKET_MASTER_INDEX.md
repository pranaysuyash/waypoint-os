# Supplier Marketplace & Spot Buying — Master Index

> Research on travel supplier marketplace design, spot buying workflows, allotment exchange, and emergency inventory sourcing for the Waypoint OS platform.

---

## Series Overview

This series covers the supplier marketplace as an operational safety net — from spot buying when contracted inventory runs out, to flash deals on distressed inventory, allotment exchange between agencies, and emergency sourcing protocols. The marketplace turns supply constraints from deal-killers into manageable situations.

**Target Audience:** Operations teams, procurement managers, agency owners

**Key Insight:** 20% of trip bookings hit a supply constraint (sold out hotel, overbooked flight, unavailable activity). Without a spot buying workflow, agents scramble on WhatsApp and either lose the deal or accept terrible margins. A structured marketplace with instant comparison, margin impact analysis, and one-click booking turns these situations from crises into routine operations.

---

## Documents

| # | Document | Focus |
|---|----------|-------|
| 1 | [SUPPLIER_MARKET_01_SPOT.md](SUPPLIER_MARKET_01_SPOT.md) | Marketplace model (standard rates, flash deals, RFQ, allotment exchange), spot buying workflow with margin analysis, allotment management, emergency sourcing protocol |

---

## Key Themes

### 1. Overflow, Not Replacement
The marketplace supplements (not replaces) contracted supplier relationships. Agencies should source 70-80% from contracts and use the marketplace for the remaining 20-30% — peak season overflow, new destinations, and emergencies.

### 2. Speed Over Perfection
When a customer is on the phone and their hotel is sold out, the agent has 5 minutes to find an alternative. The marketplace must surface comparable options with instant booking — not require RFQ rounds that take hours.

### 3. Margin Visibility
Every spot buy decision is a margin decision. Showing the margin impact of each marketplace option ("this hotel saves you ₹600/night but is 0.5km further") lets agents make informed tradeoffs instead of blind choices.

### 4. Allotment as Asset
Committed hotel rooms are a liability if unsold (agencies pay penalties). An allotment exchange lets agencies trade unused inventory, recovering costs and helping other agencies serve last-minute demand.

---

## Cross-References

| Related Series | Connection |
|---------------|------------|
| Supplier Management (SUPPLIER_*) | Supplier contracts and relationship data |
| Dynamic Packaging (DYN_PACKAGE_*) | Package assembly using marketplace inventory |
| Pricing Engine (PRICING_ENGINE_*) | Spot rate impact on pricing |
| Trip Control (TRIP_CTRL_*) | Emergency sourcing for disruption recovery |
| Owner Command Center (OWNER_CMD_*) | Margin impact visibility for owner |

---

**Created:** 2026-04-29
