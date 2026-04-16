# Vendor/Cost Tracking Discovery Gap Analysis

**Date**: 2026-04-16
**Status**: Discovery — Full inventory and gap mapping
**Scope**: Vendor, supplier, package, cost, margin, sourcing, commission, and profitability concepts across the entire codebase
**Preceded By**: `VENDOR_COST_TRACKING_GAP_ANALYSIS_2026-04-16.md` (initial discussion capture)
**Supersedes**: Nothing — this extends, not replaces, the prior gap analysis

---

## 1. Executive Summary

**98 files** reference vendor/supplier/cost/margin concepts. **84 are documentation-only**. **6 contain implementation code** — all stubs or heuristics. **Zero files** contain production vendor/supplier/cost/margin logic.

The product vision, spec, UX mockups, research docs, and scenario definitions all describe a system where the sourcing hierarchy (Internal Packages -> Preferred Suppliers -> Network -> Open Market) is the core differentiator. The implementation has exactly none of it.

| Dimension | Documented Intent | Implemented Reality |
|-----------|------------------|---------------------|
| Sourcing hierarchy | 4-tier model in vision, spec, data model docs | Always returns `open_market` or `network` (stub, confidence 0.3) |
| Supplier database | `partner_profile` entity in spec, detailed models in research | No table, no schema, no API, no data |
| Internal packages | `internal_packages` entity in spec, templates in research | No package template system exists |
| Margin model | Margin floors, commission tracking, cost basis in vision, spec, UX | Budget captured as raw number; no margin calculation anywhere |
| Cost ledger | Detailed cost breakdowns in NB04 contract | No cost ledger, no cost tracking, no vendor contacts |
| Preferred supplier matching | Destination + budget tier matching in research, NB02 spec | Always returns `preferred_supplier_available: false` (not computed) |

**Bottom line**: The system can discover trips but cannot determine if they are profitable, which suppliers to use, or whether the agency should pursue them. This hollows out the core product thesis — "Operational Intelligence that systematizes the hidden knowledge of the agency."

---

## 2. Evidence Inventory

### 2.1 Where Intent Is Documented (by Layer)

#### Layer 1: Product Vision and Thesis

| Doc | What It Says | Location |
|-----|-------------|----------|
| `PRODUCT_VISION_AND_MODEL.md` | Sourcing Hierarchy: Internal Packages -> Preferred Suppliers -> Network/Consortium -> Open Market. Evaluates on Operational Fit (vendor reliability) and Commercial Fit (margin preservation). | Docs/ |
| `PROJECT_THESIS.md` | "Margin Quality: Ensuring the package is commercially viable" and "Operational Ease: Prioritizing a sourcing hierarchy." | Docs/ |
| `DATA_MODEL_AND_TAXONOMY.md` | Defines `package_suitable` and `custom_supplier` planning routes. Partner profile has "Commission band, Net cost, Markup potential." | Docs/ |
| `FIRST_PRINCIPLES_FOUNDATION_2026-04-14.md` | Lists "agency margin" as core principle. | Docs/ |

#### Layer 2: Product Spec

| Doc | What It Says | Location |
|-----|-------------|----------|
| `MASTER_PRODUCT_SPEC.md` | Defines `partner_profile` (Destination, star category, commission band, toddler-friendliness, reliability notes) and `internal_packages` (pre-built, high-conversion bundles). | Docs/ |

#### Layer 3: Research and Architecture

| Doc | What It Says | Location |
|-----|-------------|----------|
| `AGENCY_INTERNAL_DATA.md` | Full preferred supplier examples with commission/margin data per hotel. Package templates with margin (14%). Reliability scoring. Data capture strategies. Implementation priority phases. | Docs/research/ |
| `INTERNAL_DATA_INTEGRATION.md` | Integration architecture: `check_preferred_compatibility()`, `rank_branches_by_margin()`, `build_reliability_risk_flags()`, `generate_supplier_context()`. New decision states: `BRANCH_DESTINATION`, `ADVISORY_BRANCH`. 4-phase implementation plan. | Docs/research/ |
| `NOTEBOOK_04_CONTRACT.md` | `InternalQuoteSheet` with `VendorContact`, `DetailedCostBreakdown` (margin_by_component, total_margin_amount, total_margin_percent). `calculate_pricing()`, `test_margin_preservation()` (asserts >= 10%). | Docs/research/ |
| `INTEGRATION_ARCHITECTURE.md` | Phase 2: "Integration with 1-2 preferred suppliers." Hotelbeds/partnership for hotel data. | Docs/research/ |

#### Layer 4: NB Specifications

| Doc | What It Says | Location |
|-----|-------------|----------|
| `NB01_V02_SPEC.md` | Defines derived signals: `sourcing_path` (internal_package/preferred_supplier/network/open_market), `preferred_supplier_available`, `estimated_minimum_cost`, `budget_feasibility`. Owner fields: `margin_target: 0.15`. | Docs/ |
| `NB02_V02_SPEC.md` | `margin_risk` risk flag (advisory). `budget_feasibility_table` as external data. Sourcing path not computed. | notebooks/ |
| `NB03_V02_SPEC.md` | Owner review mode shows margin analysis. Destination resolution selects sourcing path. | notebooks/ |
| `15_MISSING_CONCEPTS.md` | Sourcing Hierarchy = MVP-now. Margin/Commercial = Later. Preferred Supplier = MVP-now. | notebooks/ |

#### Layer 5: UX and Frontend Specs

| Doc | What It Says | Location |
|-----|-------------|----------|
| `UX_DASHBOARDS_BY_PERSONA.md` | Detailed margin mockups (5-15% per trip). Sourcing labels. Margin risk indicators. Margin compression alerts. Owner margin policy enforcement ("below 5% threshold"). | Docs/ |
| `UX_AND_USER_EXPERIENCE.md` | Margin risk as commercial secret field. `margin_risk: HIGH` transformed to traveler-safe language. | Docs/ |
| `UX_REDESIGN_MASTERPLAN.md` | "Waiting for supplier" pipeline stage. Supplier connections in settings. "12 supplier quotes pending >24hrs" dashboard. | Docs/ |

#### Layer 6: Personas and Scenarios

| Doc | What It Says | Location |
|-----|-------------|----------|
| `P2_AGENCY_OWNER_SCENARIOS.md` | Margin monitoring: agent margins at 8%, 12%, 15%. Minimum margin enforcement. Per-quote margin display. "Try bundling to increase margin." | Docs/personas_scenarios/ |
| `P3_JUNIOR_AGENT_SCENARIOS.md` | "At Rs2.5L, your margin is 3% — not viable." Margin protection: "Don't drop below 10%." | Docs/personas_scenarios/ |
| `ADDITIONAL_SCENARIOS_21_25.md` | Booking margin weight 30%. Package margin recalculation (14% -> 13% after customization). | Docs/personas_scenarios/ |
| `SCENARIO_COVERAGE_GAPS.md` | P1-10: "Margin/commercial logic — no margin_risk, no sourcing hierarchy, no preferred supplier concept." | Docs/personas_scenarios/ |

#### Layer 7: Context and Institutional Memory

| Doc | What It Says | Location |
|-----|-------------|----------|
| `INSTITUTIONAL_MEMORY_LAYER_SYNTHESIS_2026-04-14.md` | SupplierProfile, SupplierPerformance, SupplierBooking models. "Rank suppliers by context, not just price." Margin tracking: "Compare quoted vs actual costs + margin over time." | Docs/context/ |
| `travel_agency_context_2_2026-04-14.txt` | `sourcing_path = internal_package | preferred_supplier | network | open_market`. Preferred supplier availability as derived signal. Margin protection: "Auto-prefer your Bali DMC (18% margin) over booking.com (8%)." | Archive/context_ingest/ |
| `RISK_AREA_CATALOG_2026-04-15.md` | "Vendor Risk" section: refund mismatches, child room sync, multiple vendor alignment, language barriers, poor service quality, local taxes, no backup vendor, cascading delays. | Docs/context/ |

---

### 2.2 Where Implementation Exists (Stub/Heuristic Only)

| File | Lines | What It Does | Maturity |
|------|-------|-------------|----------|
| `src/intake/extractors.py` | 1216-1227 | Sets `sourcing_path` to `"open_market"` (or `"network"` if owner_constraints present). Confidence 0.3. | **Stub** — "enrich with internal package lookup and preferred supplier data" |
| `src/intake/decision.py` | 365-399 | `BUDGET_FEASIBILITY_TABLE`: hardcoded per-destination min_per_person costs for 24 destinations. | **Heuristic** — marked as heuristic placeholder |
| `src/intake/decision.py` | 726-791 | `check_budget_feasibility()`: compares budget vs estimated_minimum_cost. Returns feasible/tight/infeasible/unknown. | **Heuristic** — uses hardcoded table |
| `src/intake/validation.py` | 31-34 | Registers `budget_feasibility`, `sourcing_path`, `preferred_supplier_available`, `estimated_minimum_cost` as DERIVED_ONLY_FIELDS. | **Registry only** — no computation logic |
| `src/intake/safety.py` | 59-66 | Lists `owner_margins`, `commission_rate`, `net_cost` as INTERNAL_ONLY_FIELDS. Strips "markup", "margin", "commission" from traveler output. | **Safety filter** — protects non-existent data from leaking |
| `src/intake/strategy.py` | 288, 303, 337, 622 | References "margin analysis" and "margin risks" in owner review mode. Checks for "margin" keyword in internal filtering. | **String references** — no margin data to analyze |

### 2.3 Where Schema Definitions Exist

| File | What It Defines | Backed By Real Data? |
|------|----------------|---------------------|
| `specs/canonical_packet.schema.json` | `sourcing_path`, `preferred_supplier_available`, `estimated_minimum_cost`, `budget_feasibility`, `budget_breakdown`, `booking_readiness` as FieldSlots under `derived_signals` | No — all stub/heuristic |
| `notebooks/FIELD_DICTIONARY_AND_MIGRATION.md` | Proposes adding `sourcing_path` to schema and NB02 | Partially — `sourcing_path` added but always stub |

### 2.4 Where Test Coverage Exists

| File | What It Tests | Significance |
|------|--------------|-------------|
| `tests/test_nb01_v02.py` (L462-464) | Asserts `sourcing_path` has `maturity == "stub"` | Confirms stub status in production |
| `tests/test_nb02_v02.py` (L266) | `test_stub_sourcing_path_does_not_affect_decision` | Proves stub has no real effect |
| `tests/test_nb03_v02.py` (L441, 682-695) | Tests supplier text in strategy input. Asserts `owner_margins` and `commission_rate` are internal-only. | Tests boundary filtering, not computation |
| `tests/test_budget_decomposition.py` | Budget decomposition per bucket | Tests heuristic budget splitting, not real costs |

---

## 3. Gap Taxonomy

### 3.1 Structural Gaps (No Entity Exists)

| Gap ID | Concept | Documented In | Implementation | Blocking For |
|--------|---------|---------------|----------------|---------------|
| **G-01** | Supplier/Partner entity | MASTER_PRODUCT_SPEC, AGENCY_INTERNAL_DATA, DATA_MODEL_AND_TAXONOMY | None — no table, no schema, no API, no CRUD | Preferred supplier matching, sourcing hierarchy, margin calc, vendor risk flags |
| **G-02** | Internal Package entity | MASTER_PRODUCT_SPEC, AGENCY_INTERNAL_DATA, DATA_MODEL_AND_TAXONOMY | None — no template system, no package store | Package-based proposal generation, fast quoting, predictable margins |
| **G-03** | Cost Ledger | NOTEBOOK_04_CONTRACT, INSTITUTIONAL_MEMORY_SYNTHESIS | None — no cost tracking, no vendor contacts, no net rates | Internal quote sheet, booking workflow, post-trip reconciliation |
| **G-04** | Margin Model | PRODUCT_VISION, NB01_V02_SPEC, UX_DASHBOARDS, P2_SCENARIOS | None — no margin_risk signal, no margin calculation, no margin floors | Profitability check, owner policy enforcement, commission tracking |
| **G-05** | Commission Tracking | AGENCY_INTERNAL_DATA, DATA_MODEL_AND_TAXONOMY | None — no commission data, no payment tracking | Margin optimization, cash flow management, supplier ranking |
| **G-06** | Sourcing Engine | PRODUCT_VISION, INTERNAL_DATA_INTEGRATION, 15_MISSING_CONCEPTS | All stubs — `sourcing_path` always returns `open_market` or `network` at 0.3 confidence | Sourcing-aware decision logic, supplier-first routing |

### 3.2 Computation Gaps (Field Defined But Not Computed)

| Gap ID | Signal | Field Definition | Current Value | Required For |
|--------|--------|-----------------|---------------|-------------|
| **C-01** | `sourcing_path` | NB01_V02_SPEC: 4-tier enum | Always `"open_market"` or `"network"` (stub, 0.3 confidence) | Supplier tier routing, margin-aware decisions |
| **C-02** | `preferred_supplier_available` | NB01_V02_SPEC: bool | Not computed — always absent | "Lead with preferred supplier" strategy |
| **C-03** | `estimated_minimum_cost` | NB01_V02_SPEC: int | Not computed — no real cost data | Budget feasibility, margin calculation |
| **C-04** | `budget_feasibility` | NB01_V02_SPEC: enum | Heuristic from hardcoded table — no real destination costs | Impossible proposal prevention |
| **C-05** | `margin_risk` | NB02_V02_SPEC: advisory risk flag | Generated only for infeasible budgets — no margin model | Margin floor enforcement, owner policy |
| **C-06** | `booking_readiness` | NB01_V02_SPEC: composite | Not computed — depends on supplier confirmation | Booking stage gate |
| **C-07** | `value_gap` | NB01_V02_SPEC: derived signal | Not computed | Audit mode, wasted spend detection |

### 3.3 Integration Gaps (Designed But Not Wired)

| Gap ID | Integration | Designed In | Current State | Required For |
|--------|-------------|------------|---------------|-------------|
| **I-01** | Preferred supplier filtering in NB02 | INTERNAL_DATA_INTEGRATION L56-105 | No supplier data to filter against | `BRANCH_DESTINATION` decision state |
| **I-02** | Historical confidence boost in NB02 | INTERNAL_DATA_INTEGRATION L132-180 | No booking history data | Pattern-matched confidence increases |
| **I-03** | Wasted spend detection in NB02 | INTERNAL_DATA_INTEGRATION L188-228 | No tribal knowledge base | `ADVISORY_BRANCH` decision state |
| **I-04** | Margin-aware branch ranking in NB02 | INTERNAL_DATA_INTEGRATION L304-335 | No margin data | Internal ranking of branches by profitability |
| **I-05** | Supplier reliability risk flags in NB03 | INTERNAL_DATA_INTEGRATION L257-287 | No reliability scores | Vendor-specific risk warnings in strategy |
| **I-06** | Customer memory enrichment in NB02+NB03 | INTERNAL_DATA_INTEGRATION L353-410 | No customer preference store | Personalization without re-asking |
| **I-07** | Pricing calculation in NB04 | NOTEBOOK_04_CONTRACT L300, L733 | No margin data → no `calculate_pricing()` | Internal quote sheet, margin preservation test |

### 3.4 Decision State Gaps (Specified But Not Implemented)

| Gap ID | Decision State | Specified In | Current State | Trigger Condition |
|--------|---------------|-------------|---------------|-------------------|
| **D-01** | `BRANCH_DESTINATION` | INTERNAL_DATA_INTEGRATION L108-129 | Not implemented | No preferred suppliers for chosen destination |
| **D-02** | `ADVISORY_BRANCH` | INTERNAL_DATA_INTEGRATION L233-253 | Not implemented | Wasted spend risk from tribal knowledge |

---

## 4. Dependency Graph

```
G-01 (Supplier Entity)
  ├── Required by: C-01 (sourcing_path), C-02 (preferred_supplier_available),
  │                I-01 (preferred filtering), I-05 (reliability flags),
  │                D-01 (BRANCH_DESTINATION)
  └── Blocks: All supplier-dependent features

G-02 (Internal Package Entity)
  ├── Required by: C-01 (sourcing_path), I-07 (pricing calc)
  └── Blocks: Package-based proposals, fast quoting

G-03 (Cost Ledger)
  ├── Required by: C-03 (estimated_minimum_cost), C-05 (margin_risk),
  │                I-04 (margin ranking), I-07 (pricing calc)
  └── Blocks: Margin calculation, booking workflow, reconciliation

G-04 (Margin Model)
  ├── Required by: C-05 (margin_risk), I-04 (margin ranking),
  │                I-07 (pricing calc)
  └── Blocks: Profitability check, owner policy enforcement

G-06 (Sourcing Engine)
  ├── Depends on: G-01, G-02 (must have suppliers and packages first)
  └── Blocks: C-01 (real sourcing_path), all sourcing-aware logic
```

**Critical path**: G-01 (Supplier Entity) -> G-06 (Sourcing Engine) -> C-01 (real sourcing_path) -> all downstream features.

Without G-01, nothing else moves. The supplier entity is the atomic dependency.

---

## 5. Priority Assessment

### 5.1 Priority from 15_MISSING_CONCEPTS.md

| Concept | Notebook Priority | This Analysis |
|---------|------------------|---------------|
| Sourcing Hierarchy | **MVP-now** | Agreed — without it, the system can't differentiate from OTAs |
| Margin / Commercial Logic | Later | **Disagree — should be MVP-now**. Without margin awareness, the system generates proposals that may be margin-negative. This is a business-survival concern, not a nice-to-have. |
| Preferred Supplier | **MVP-now** | Agreed — this is the search space reduction that makes the system useful |
| Budget Feasibility | **MVP-now** | Partially implemented (heuristic table exists). Needs real cost data, not hardcoded values. |

### 5.2 Revised Priority (Based on This Analysis)

| Priority | Gap ID | Concept | Rationale |
|----------|--------|---------|-----------|
| **P0** | G-01 | Supplier/Partner entity | Atomic dependency — nothing else works without it |
| **P0** | G-06 | Sourcing engine | Core differentiator — returns real `sourcing_path` |
| **P0** | G-04 | Margin model | Business survival — prevent margin-negative proposals |
| **P1** | G-02 | Internal package entity | Fast quoting, predictable margins, operational efficiency |
| **P1** | G-03 | Cost ledger | Booking workflow, reconciliation, post-trip learning |
| **P1** | G-05 | Commission tracking | Cash flow management, supplier ranking by real payment behavior |
| **P1** | C-01 through C-07 | Computation gaps | Wire existing field definitions to real data |
| **P2** | I-01 through I-07 | Integration gaps | NB02/NB03 enrichment — advisory states, branch ranking |
| **P2** | D-01, D-02 | Decision state gaps | `BRANCH_DESTINATION`, `ADVISORY_BRANCH` |

---

## 6. Impact by Product Surface

### Surface A: Operator Workbench

| Current Capability | Missing Capability | Blocking Gap |
|-------------------|--------------------|-------------|
| Can analyze trip feasibility | Cannot calculate profitability | G-04 |
| Can generate proposals | Cannot bias toward preferred suppliers (always open_market) | G-01, G-06 |
| Can assess budget vs. heuristic table | Cannot assess real cost basis | G-03 |
| Can flag budget risk | Cannot flag margin risk | G-04 |
| Can show decision state | Cannot show sourcing path with real data | C-01 |

### Surface B: Operator App

| Current Capability | Missing Capability | Blocking Gap |
|-------------------|--------------------|-------------|
| Can present options | Cannot rank by margin | G-04, I-04 |
| Can show risk flags | Cannot show vendor reliability warnings | G-01, I-05 |
| Can detect budget issues | Cannot detect wasted spend | I-03 |
| Can generate questions | Cannot ask sourcing-aware questions | C-01 |
| Can present branches | Cannot suggest alternative destinations with preferred suppliers | D-01 |

### Surface C: Owner Console

| Current Capability | Missing Capability | Blocking Gap |
|-------------------|--------------------|-------------|
| Can show trip intake pipeline | Cannot show margin trends | G-04 |
| Can show agent performance | Cannot show margin adherence per agent | G-04, G-05 |
| Can show risk flags | Cannot enforce margin floor policies | G-04 |
| Can show decision states | Cannot show supplier performance | G-01 |
| Can show pipeline metrics | Cannot show conversion-by-sourcing-path | C-01 |

---

## 7. Data Model Gaps: What Needs to Be Built

### 7.1 Entities That Must Be Created

Based on cross-referencing all spec, research, and contract docs, these are the minimum viable entities:

```
Supplier (Partner)
├── id: str
├── name: str
├── type: enum (hotel, airline, dmc, guide, transport, activity_provider)
├── destination: str
├── star_category: str
├── commission_band: str  (e.g., "10-15%")
├── net_cost_basis: Decimal
├── margin_pct: Decimal
├── reliability_score: float (0-10)
├── best_for: List[str]  (traveler segments)
├── avoid_for: List[str]
├── toddler_friendly: bool
├── elderly_friendly: bool
├── agent_notes: str  (freeform tribal knowledge)
├── owner_notes: str  (internal-only, not visible to agents)
├── last_booked: date
├── booking_count: int
├── issue_count: int
├── tier: enum (internal_package, preferred, network, open_market)
├── payment_terms: str  (e.g., "15 days", "60 days")
└── contact: VendorContact

InternalPackage
├── id: str
├── name: str
├── destination: str
├── target_segment: str
├── components: List[PackageComponent]
├── base_price: Decimal
├── margin_pct: Decimal
├── conversion_rate: Decimal
├── satisfaction_score: Decimal
├── booking_count: int
├── ease_of_execution: enum (high, medium, low)
└── flexibility: List[str]  (which parts can be customized)

CostLedger
├── id: str
├── packet_id: str
├── proposal_id: str
├── components: List[CostComponent]
├── total_cost: Decimal
├── total_quoted: Decimal
├── total_margin: Decimal
├── total_margin_pct: Decimal
├── margin_by_component: Dict[str, Decimal]
├── currency: str
└── created_at: datetime

MarginPolicy
├── id: str
├── owner_id: str
├── min_margin_pct: Decimal
├── min_margin_by_destination: Dict[str, Decimal]
├── margin_alert_threshold: Decimal
├── enforce_hard_floor: bool
└── created_at: datetime
```

### 7.2 Computed Signals That Must Be Wired

```
sourcing_path:     Supplier tier lookup by destination + budget tier + segment
                    (currently: always "open_market", confidence 0.3)

preferred_supplier_available:
                    Query Supplier table for matching destination + budget + segment
                    (currently: not computed)

estimated_minimum_cost:
                    Sum of minimum net costs from preferred suppliers for destination
                    (currently: not computed)

budget_feasibility: Compare budget against estimated_minimum_cost from real supplier data
                    (currently: hardcoded BUDGET_FEASIBILITY_TABLE)

margin_risk:        Compare estimated margin against MarginPolicy.min_margin_pct
                    (currently: only triggered for infeasible budgets)

booking_readiness:  Composite of document status + payment + supplier confirmation
                    (currently: not computed)
```

---

## 8. What Works Today (Stub Safety Net)

Despite the gaps, the existing code has structural scaffolding that will make implementation easier:

1. **Field registry exists**: `DERIVED_ONLY_FIELDS` in `validation.py` already lists all 7 vendor/cost signals. No schema changes needed — just computation logic.

2. **Safety boundary exists**: `safety.py` already strips `owner_margins`, `commission_rate`, `net_cost` from traveler output. Margin data won't leak.

3. **Schema types defined**: `canonical_packet.schema.json` already has `sourcing_path`, `preferred_supplier_available`, `estimated_minimum_cost`, `budget_feasibility`, `budget_breakdown`, `booking_readiness` as FieldSlots. Frontend can already render these.

4. **Budget feasibility has structure**: The `BUDGET_FEASIBILITY_TABLE` and `check_budget_feasibility()` function work — they just need real data replacing hardcoded values.

5. **Tests confirm stub status**: `test_stub_sourcing_path_does_not_affect_decision` proves the stub is isolated. When real logic arrives, removing this test and replacing with real assertions is a clean migration.

6. **NB04 contract has data models**: `InternalQuoteSheet`, `VendorContact`, `DetailedCostBreakdown` are fully specified in research docs. Implementation is a matter of coding from spec.

---

## 9. Phase-In Recommendations

### Phase 1: Data Foundation (P0)
**Goal**: Make supplier data exist in the system

1. Create `Supplier` entity with CRUD API
2. Create simple CSV/Sheet import for initial supplier data
3. Wire `sourcing_path` signal to query Supplier table instead of returning `open_market`
4. Wire `preferred_supplier_available` to actual matching logic
5. Create `MarginPolicy` entity (owner configurable)

**Tests**: `sourcing_path` returns real tier with confidence > 0.7. `preferred_supplier_available` returns true when matching supplier exists.

### Phase 2: Margin Engine (P0)
**Goal**: Make proposals margin-aware

1. Create `CostLedger` entity
2. Implement `estimated_minimum_cost` from supplier net costs
3. Replace `BUDGET_FEASIBILITY_TABLE` with real supplier cost queries
4. Wire `margin_risk` signal to MarginPolicy
5. Implement `calculate_pricing()` from NB04 contract

**Tests**: `margin_risk` triggers when margin falls below policy floor. Budget feasibility uses real costs, not hardcoded table.

### Phase 3: Package System (P1)
**Goal**: Enable fast quoting from templates

1. Create `InternalPackage` entity
2. Implement package template matching (destination + segment -> package)
3. Wire `sourcing_path` to return `internal_package` when match found
4. Implement package-based proposal generation in NB04

**Tests**: Matching trip input returns `sourcing_path = "internal_package"`. Package-based proposals generate in < 60 seconds.

### Phase 4: Integration Intelligence (P2)
**Goal**: NB02/NB03 enrichment from internal data

1. Implement `BRANCH_DESTINATION` decision state
2. Implement `ADVISORY_BRANCH` decision state
3. Wire margin-aware branch ranking
4. Wire supplier reliability risk flags in NB03
5. Implement wasted spend detection

**Tests**: `BRANCH_DESTINATION` triggers when no preferred suppliers for destination. `ADVISORY_BRANCH` triggers for wasted spend risk.

---

## 10. Key Decisions Required

| Decision | Options | Recommendation | Impact |
|----------|---------|----------------|--------|
| Where does supplier data live? | (a) New database table + API, (b) Config/JSON files, (c) External CRM integration | **(a)** — New table + API. Supplier data is query-heavy and needs CRUD. Config files won't scale. CRM integration is Phase 2+. | Defines G-01 implementation path |
| Who enters supplier data? | (a) Agency owner via UI, (b) CSV bulk import, (c) Auto-extracted from past bookings | **(a) + (b)** — Owner UI for single entries, CSV for bulk import. Auto-extraction from past bookings is Phase 3. | Defines data capture strategy |
| Is margin data visible to agents? | (a) Owner-only, (b) Owner + senior agents, (c) All agents | **(a)** — Owner-only (already modeled in `safety.py`). Margin visibility to agents risks gaming the optimization. | Defines safety boundary for G-04 |
| Should sourcing_path be overrideable? | (a) System decides, agent accepts, (b) Agent can override with reason, (c) Agent decides freely | **(b)** — Agent can override with documented reason. Preferred suppliers are *preferred*, not *mandatory*. | Defines C-01 computation policy |
| What is the minimum margin floor? | (a) 5%, (b) 10%, (c) Owner configurable per destination | **(c)** — Owner configurable. Different destinations have different margin profiles. | Defines G-04 default behavior |

---

## 11. Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Supplier data decays — owner never updates it | High | Add "last_verified" date. Flag suppliers > 90 days since update. Auto-deprecate stale entries. |
| Margin optimization gets gamed — agents always pick highest-margin options | Medium | Owner sets margin floor, not ceiling. System prioritizes customer fit first, margin is tiebreaker. |
| Sourcing path bias creates blind spots — system always recommends same 3 hotels | Medium | Add diversity score to ranking. Track unique suppliers used per destination. Alert on concentration risk. |
| Cost data leaks to travelers | High | Already mitigated by `safety.py`. Test boundary enforced. But must extend to new API endpoints. |
| Data entry burden — owner never fills in supplier database | High | Start with CSV import of existing spreadsheets. Most agencies already have preferred hotel lists in Excel. |
| Internal packages become rigid — system won't let agents customize | Medium | Package flexibility field (hard/soft components). Agents can swap soft components freely. |

---

## 12. Files Audited

**Total**: 98 files across 6 categories

**Key source files for this analysis**:
- `notebooks/15_MISSING_CONCEPTS.md` — Priority assignments
- `Docs/PRODUCT_VISION_AND_MODEL.md` — Sourcing hierarchy thesis
- `Docs/MASTER_PRODUCT_SPEC.md` — Data entity specs
- `Docs/DATA_MODEL_AND_TAXONOMY.md` — Planning routes, partner profiles
- `Docs/research/AGENCY_INTERNAL_DATA.md` — Full supplier/margin/package examples
- `Docs/research/INTERNAL_DATA_INTEGRATION.md` — Integration architecture with NB02/NB03
- `Docs/research/NOTEBOOK_04_CONTRACT.md` — InternalQuoteSheet, VendorContact, margin models
- `Docs/UX_DASHBOARDS_BY_PERSONA.md` — Margin UI mockups
- `Docs/NB01_V02_SPEC.md` — Derived signal definitions
- `Docs/NB01_V02_IMPLEMENTATION.md` — Implementation status
- `src/intake/extractors.py` — Sourcing path stub
- `src/intake/decision.py` — Budget feasibility heuristic
- `src/intake/validation.py` — DERIVED_ONLY_FIELDS registry
- `src/intake/safety.py` — INTERNAL_ONLY_FIELDS, margin text filtering
- `specs/canonical_packet.schema.json` — Schema definitions

**Prior gap analysis**: `Docs/VENDOR_COST_TRACKING_GAP_ANALYSIS_2026-04-16.md` — Initial discussion capture (this doc supersedes its analysis)