# Vendor/Package/Cost Tracking Gap Analysis

**Date**: 2026-04-16  
**Status**: Identified as intentional deferral  
**Severity**: Critical architectural gap

---

## Discussion Summary

**User Question**: "i dont see anything in the flow where agencies track their internal vendors/packages/costs etc?"

**Findings**: Correct. There is NO implementation of vendor/supplier/package/cost management anywhere in the system, and this is documented as an intentional omission.

---

## The Three Critical Gaps

### 1. Sourcing Hierarchy
**Status**: Not modeled  
**Priority**: MVP-now (according to `notebooks/15_MISSING_CONCEPTS.md`)

**What it is**: The agency doesn't search open market first. The sourcing path is:
```
Internal Packages → Preferred Suppliers → Network/Consortium → Open Market
```

**Current State**: 
- NB02 has no concept of sourcing path
- NB03 has no sourcing-aware strategy
- No sourcing selection logic anywhere

**Why it matters**: A "family of 4, Singapore, 3 lakh budget" is fundamentally different if there's an internal package available vs searching open market. The sourcing path determines the agent's entire approach.

---

### 2. Margin / Commercial Logic
**Status**: Not modeled  
**Priority**: Later (according to `notebooks/15_MISSING_CONCEPTS.md`)

**What it is**: Every quote has a margin. The agency needs to know if a trip is worth doing, and at what price point.

**Current State**:
- Budget is captured as a raw number only
- No margin model anywhere
- No profitability check
- No commission tracking
- No cost basis visibility (quote vs cost vs margin)

**Why it matters**: The agency goes out of business if every quote is margin-negative. This must be modeled before booking stage.

---

### 3. Preferred Supplier / Partner Fit
**Status**: Not modeled  
**Priority**: MVP-now (according to `notebooks/15_MISSING_CONCEPTS.md`)

**What it is**: The agency has preferred suppliers (hotels, DMCs, transport) who give better rates and reliability. The system should bias toward them.

**Current State**:
- No supplier database
- No preferred vs open market distinction
- No supplier relationship tracking
- No contract rate management

**Why it matters**: This is the "internal packages" concept from the product spec. It's what makes the agency competitive vs OTAs.

---

## Where This Shows Up (or Doesn't)

### What's Documented But Not Implemented

**In PRODUCT_VISION_AND_MODEL.md** (foundational):
```
Sourcing Hierarchy (Section 2):
1. Internal Standard Packages
2. Preferred Supplier Inventory (contracted hotels, partners, guides)
3. Network/Consortium Inventory (wholesalers, DMCs)
4. Open Market (last resort)

Commercial Optimization axes:
- Traveler Fit
- Operational Fit (vendor reliability, coordination ease)
- Commercial Fit (margin preservation, competitiveness)
```

**In MASTER_PRODUCT_SPEC.md** (Section 4.1):
```
Supplier Inventory:
- `partner_profile`: Destination, star category, commission band, toddler-friendliness, reliability notes
- `internal_packages`: Pre-built, high-conversion bundles
```

**In UX_DASHBOARDS_BY_PERSONA.md** (P2 Agency Owner, P1 Operator):
- Detailed mockups of margin tracking (target: 5-15%)
- Preferred supplier selection by destination
- Margin risk alerts
- Cost basis visibility (Quote vs. Cost vs. Margin breakdown)
- Margin compression warnings
- Sourcing strategy (preferred vs. open market choice)

### Implementation Status by Layer

| Layer | Status | Evidence |
|-------|--------|----------|
| **Frontend UI** | None | No vendor management screens, no supplier selection UI, no margin display |
| **API Routes** | None | No endpoints for vendor CRUD, package templates, cost ledger, margin calculation |
| **Data Models** | None | No Pydantic schemas for Partner, Package, CostLedger, Sourcing, Margin |
| **Database** | Unknown | Unclear if schema exists; not exposed via API |
| **Notebooks (NB01-03)** | None | Not integrated into intake, decision, or strategy logic |

---

## Why It's Missing: Intentional Deferral

**Source**: `notebooks/15_MISSING_CONCEPTS.md`

The document explicitly lists these concepts as "missing" with priority levels:

```
Sourcing Hierarchy → Priority: MVP-now (not implemented)
Margin / Commercial Logic → Priority: Later (not implemented)
Preferred Supplier / Partner Fit → Priority: MVP-now (not implemented)
```

**From the doc**:
> "This is not a blocking concern for v0.1 discovery, but it must be modeled before booking stage."

**Interpretation**: The team chose to ship trip discovery without the commercial/operational layer. The current approach: **let the AI figure out sourcing and margins**, rather than modeling real supplier relationships and cost constraints.

---

## Impact on Product Surfaces

| Surface | Impact |
|---------|--------|
| **A (Workbench)** | Can analyze trips but can't calculate profitability, can't bias toward preferred suppliers, can't protect margins |
| **B (Operator App)** | Can't surface "use preferred hotel X" recommendations, can't show margin warnings, can't track vendor relationships |
| **C (Owner Console)** | Can't show margin trends, can't show supplier performance, can't show margin risk alerts, can't enforce margin policies |

---

## Business Model Gap

This is **not a bug**—it's a **scope decision that hollowed out a core value prop**.

The product vision (PRODUCT_VISION_AND_MODEL.md) is fundamentally about:
> **"Operational Intelligence": Systematizes the "hidden" knowledge of the agency (e.g., which hotels are actually good for Indians, which vendors respond fastest on WhatsApp).**

But the implementation skips the system that would capture and use that knowledge.

---

## Implications

### Workflows That Can't Work Today

- Agency owner can't build/maintain a preferred supplier list
- Agents can't see "use our preferred hotel for this destination"
- Operator can't calculate margin on a quote
- Owner can't get margin alerts or supplier performance data
- Booking workflow can't check supplier availability against confirmed rates
- Cost ledger doesn't exist for post-trip reconciliation

### What This Means for MVP

**Current MVP assumption**: Trip discovery works without operational intelligence.

**Reality**: The system can identify that a trip is feasible, but can't tell if it's **profitable** or whether it should use the agency's **preferred network**.

---

## Notes

- Vendor/package/cost tracking is documented as deferred, not forgotten
- The team consciously chose trip discovery over commercial optimization for v0.1
- This must be addressed before full booking workflow is implemented
- The data models and UI specs exist in the documentation but are not coded
