# Vendor, Package & Tie-Up Architecture — Explored Findings

**Date**: 2026-04-24  
**Status**: Exploratory / Recommendation-ready  
**Scope**: How the system should handle (1) agency-owned vendor data, package data, and tie-ups, and (2) the operational reality that agencies add new vendors *as they work*, not via a one-time bulk setup.

**Preceded by**: `VENDOR_COST_TRACKING_DISCOVERY_GAP_ANALYSIS_2026-04-16.md`  
**Related gaps**: Gap #01 (Vendor/Cost/Sourcing/Margin) — MASTER_GAP_REGISTER_2026-04-16.md

---

## Executive Summary

The Waypoint OS spine pipeline (NB01–NB03) is production-grade for intake, decision, and strategy generation. However, the commercial layer — the bridge between a structured trip packet and actual supplier selection, pricing, and margin management — is entirely missing or stubbed. This document explores the architecture, data models, operational flows, implementation phasing, and key decisions required to close this gap.

Three findings drive the design:
1. **Vendor data must be relational and tenant-isolated** (PostgreSQL), not JSON files or config blobs.
2. **Agencies add vendors dynamically during operations**, not in a pre-flight setup phase. The UX must support "quick-add" from the workbench without breaking trip-processing flow.
3. **The pipeline must be wired to real supplier data** — currently `sourcing_path` is always a stub (`open_market`, confidence 0.3).

---

## 1. Current State (Verified Evidence)

### 1.1 What Exists

| File | Evidence | Maturity |
|------|----------|----------|
| `src/intake/extractors.py:1263–1267` | `sourcing_path` set to `"open_market"` (or `"network"` if owner constraints exist). Explicit comment: *"Stub — enrich with internal package lookup and preferred supplier data"* | Stub |
| `src/intake/negotiation_engine.py` | `NegotiationEngine` with hardcoded supplier names (`"Grand {dest} Hotel"`, `"Premium Lounge Services"`). Returns mock negotiation logs. | Stub |
| `spine_api/contract.py:51–59` | `NegotiationLog` Pydantic model exists with `supplier_name`, `status`, `best_bid`, `savings`. | Contract only |
| `src/intake/config/agency_settings.py:148–149` | `enable_auto_negotiation: True`, `negotiation_margin_threshold: 10.0` — settings field exists but engine uses no real data. | Config only |
| `src/intake/safety.py:59–66` | `INTERNAL_ONLY_FIELDS` strips `owner_margins`, `commission_rate`, `net_cost` from traveler output. Safety boundary exists but no data to protect. | Safety filter |
| `src/intake/decision.py:365–399` | `BUDGET_FEASIBILITY_TABLE` — hardcoded per-destination minimum costs for 24 destinations. Used by `check_budget_feasibility()`. | Heuristic |
| `src/intake/validation.py:31–34` | `DERIVED_ONLY_FIELDS` registers `budget_feasibility`, `sourcing_path`, `preferred_supplier_available`, `estimated_minimum_cost`. Field definitions exist, no computation. | Registry |
| `spine_api/models/tenant.py` | `Agency`, `User`, `Membership` models exist. No vendor/package/tie-up models. | N/A |
| `spine_api/models/frontier.py` | GhostWorkflow, EmotionalStateLog, IntelligencePoolRecord, LegacyAspiration — advanced features exist, but no commercial models. | N/A |

### 1.2 What Does NOT Exist

- ❌ No `Vendor`, `Supplier`, `Package`, `Product`, `TieUp`, `Inventory`, `Rate`, or `Catalog` database tables or Pydantic models.
- ❌ No vendor management UI routes or API endpoints.
- ❌ No real supplier integration or inventory lookup.
- ❌ No markup, commission, or net-rate calculation logic beyond the basic risk-adjusted fee calculator (`src/fees/calculation.py` uses hardcoded base fees: `$500` flights, `$300/night` hotels).
- ❌ No preferred supplier matching — the field `preferred_supplier_available` exists in the schema but is never computed.

### 1.3 Test Evidence

- `tests/test_nb01_v02.py:462–464`: Asserts `sourcing_path` has `maturity == "stub"`.
- `tests/test_nb02_v02.py:266`: `test_stub_sourcing_path_does_not_affect_decision` — confirms stub is behaviorally isolated.
- `tests/test_nb03_v02.py:441, 682–695`: Tests supplier text in strategy input and asserts `owner_margins`/`commission_rate` are internal-only. Tests boundary filtering, not computation.

---

## 2. Core Architectural Decision: Storage Strategy

The project uses a **dual-storage architecture**:
- **PostgreSQL + SQLAlchemy async** — Auth/tenant data (`Agency`, `User`, `Membership`, etc.)
- **JSON files** — Trip data, assignments, overrides, audit logs, team members, pipeline config
- **SQLite** — Per-agency autonomy policies and settings

### Recommended 3-Tier Hybrid for Vendor Data

| Tier | Storage | What Lives Here | Rationale |
|------|---------|------------------|-----------|
| **Canonical Master** | PostgreSQL (relational, multi-tenant) | `Vendor`, `Package`, `TieUp`, `Rate` | Needs relational queries (search by destination, filter by star rating, check rate validity). Must support CRUD, audit trails, and tenant isolation. |
| **Operational Cache** | JSON / Redis (future) | Active vendor prices, quick lookups, in-session suggestion indices | Speed goal: sub-200ms catalog suggestions in the operator workbench. |
| **Session State** | Trip JSON files (existing pattern) | Per-trip vendor attachments, negotiated prices, cost ledgers, booking status | Matches existing trip persistence. Keeps trip state self-contained. |

**Why PostgreSQL for master data?**
- Vendor/package data is query-heavy (search by destination + type + price range + availability).
- Needs relationships: `Vendor → Packages → Rates → TieUps`.
- Needs multi-tenant isolation (`agency_id` on every row).
- JSON file-based storage cannot support filtered search at scale without loading everything into memory.
- Existing Alembic migration infrastructure can handle schema evolution.

**Why keep trip-level vendor attachments in JSON files?**
- Trip state is already JSON-backed. Adding vendor references (`attached_vendor_ids`, `selected_package_id`, `cost_ledger`) to the trip JSON preserves the existing pattern without introducing a new persistence layer for trip ops.
- A future migration to trip-in-Postgres (identified in Gap #02) can migrate these references cleanly.

---

## 3. Data Models (Minimal Viable)

These models are designed to satisfy the "atomic dependency" identified in the gap analysis: **G-01 (Supplier Entity)** must exist before any downstream features work.

### 3.1 Vendor

Represents a supplier/partner the agency works with: hotels, airlines, DMCs, guides, transport operators, activity providers, cruise lines, insurers.

```python
class Vendor(Base):
    __tablename__ = "vendors"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4)
    agency_id: Mapped[str] = mapped_column(ForeignKey("agencies.id", ondelete="CASCADE"), nullable=False)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)  # hotel, airline, dmc, guide, transport, activity, cruise, insurance
    destination: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    contact_info: Mapped[dict] = mapped_column(JSON, default=dict)  # email, phone, account_manager, address
    payment_terms: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # "15 days", "60 days", "on booking"
    currency: Mapped[Optional[str]] = mapped_column(String(3), nullable=True, default="INR")

    commission_default: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)  # e.g., 15.0
    margin_target: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)  # agency override per vendor
    reliability_score: Mapped[Optional[float]] = mapped_column(Numeric(3, 1), default=5.0)  # 0.0–10.0

    tier: Mapped[str] = mapped_column(String(50), default="network")  # internal_package | preferred | network | open_market
    tags: Mapped[list] = mapped_column(JSON, default=list)  # ["luxury", "family-friendly", "honeymoon"]
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(String(50), default="active")  # active | suspended | blacklisted | incomplete_profile
    last_booked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    booking_count: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
```

**Key design choice — `status = "incomplete_profile"`**: When an operator quick-adds a vendor from the workbench, the vendor is created with only 3 fields (name, type, destination). It enters the catalog immediately but is flagged as incomplete. The owner or a senior agent completes the full profile later.

### 3.2 Package

Represents a sellable product the agency has structured: tour packages, hotel+flight bundles, activity sets.

```python
class Package(Base):
    __tablename__ = "packages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4)
    agency_id: Mapped[str] = mapped_column(ForeignKey("agencies.id", ondelete="CASCADE"), nullable=False)
    vendor_id: Mapped[str] = mapped_column(ForeignKey("vendors.id", ondelete="CASCADE"), nullable=False)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    destination: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)  # honeymoon, family, adventure, wellness, etc.

    duration_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    duration_nights: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    inclusions: Mapped[list] = mapped_column(JSON, default=list)
    exclusions: Mapped[list] = mapped_column(JSON, default=list)

    base_price: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    price_per_person: Mapped[bool] = mapped_column(Boolean, default=True)
    price_currency: Mapped[str] = mapped_column(String(3), default="INR")

    commission_structure: Mapped[dict] = mapped_column(JSON, default=dict)  # percentage, flat_fee, slab-based
    markup_rules: Mapped[dict] = mapped_column(JSON, default=dict)  # percentage, minimum_markup, maximum_markup
    suitable_for: Mapped[list] = mapped_column(JSON, default=list)  # traveler segments

    status: Mapped[str] = mapped_column(String(50), default="draft")  # draft | active | archived | discontinued
    created_by: Mapped[str] = mapped_column(String(36), nullable=False)  # user_id
    approved_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)  # owner approval gate

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
```

### 3.3 TieUp (Contract / Negotiated Rate)

Represents the negotiated commercial terms between the agency and a vendor (or a specific package). A vendor can have multiple tie-ups over time (seasonal, promotional, volume-commitment).

```python
class TieUp(Base):
    __tablename__ = "tie_ups"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4)
    agency_id: Mapped[str] = mapped_column(ForeignKey("agencies.id", ondelete="CASCADE"), nullable=False)
    vendor_id: Mapped[str] = mapped_column(ForeignKey("vendors.id", ondelete="CASCADE"), nullable=False)
    package_id: Mapped[Optional[str]] = mapped_column(ForeignKey("packages.id", ondelete="CASCADE"), nullable=True)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)  # preferred | exclusive | volume_commitment | promotional | spot

    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    valid_to: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    negotiated_rates: Mapped[dict] = mapped_column(JSON, default=dict)  # adult_price, child_price, infant_price, group_discount_threshold, group_discount_percent
    commission_override: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # overrides vendor default
    payment_terms_override: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # credit_days, deposit_percent, balance_due_days
    exclusivity_scope: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # regions, destinations, traveler_types
    minimum_guarantee: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # annual_bookings, revenue_commitment

    status: Mapped[str] = mapped_column(String(50), default="draft")  # draft | active | expired | terminated
    created_by: Mapped[str] = mapped_column(String(36), nullable=False)
    approved_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
```

### 3.4 Rate (Seasonal / Inventory Pricing)

Represents time-bound pricing for a package. Supports seasonal variations, availability limits, and booking conditions.

```python
class Rate(Base):
    __tablename__ = "rates"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4)
    package_id: Mapped[str] = mapped_column(ForeignKey("packages.id", ondelete="CASCADE"), nullable=False)

    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    valid_to: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    adult_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    child_price: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    infant_price: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    single_supplement: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    triple_reduction: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)

    currency: Mapped[str] = mapped_column(String(3), default="INR")
    availability: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # rooms / seats / slots
    booking_conditions: Mapped[dict] = mapped_column(JSON, default=dict)  # min_advance_days, cancellation_policy, deposit_required

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
```

### 3.5 CostLedger (Per-Trip, Session-Level)

Not a PostgreSQL model — appended to the trip JSON file. Records actual costs incurred during booking and post-trip reconciliation.

```json
{
  "cost_ledger": {
    "currency": "INR",
    "components": [
      {
        "component_id": "cl_001",
        "vendor_id": "v_abc123",
        "vendor_name": "Bali DMC - Wayan",
        "category": "accommodation",
        "description": "3 nights Grand Bali Hotel - Deluxe Ocean View",
        "quoted_price": 95000.00,
        "net_cost": 78000.00,
        "margin_amount": 17000.00,
        "margin_pct": 17.9,
        "commission_earned": 0.00,
        "status": "confirmed",
        "confirmed_at": "2026-04-20T10:30:00Z",
        "added_by": "user_xyz789",
        "added_at": "2026-04-18T14:22:00Z"
      }
    ],
    "total_quoted": 185000.00,
    "total_net_cost": 148000.00,
    "total_margin": 37000.00,
    "total_margin_pct": 20.0
  }
}
```

---

## 4. The Critical Operational Flow: "Add New Ones As They Work"

This is the distinguishing requirement. Agencies do not complete supplier setup before processing trips. They get a query for Bhutan, realize their Bhutan DMC isn't in the system, and add it *while reviewing the trip*. The system must support this without breaking flow or forcing context switching.

### 4.1 Flow A: Quick-Add Vendor (from Operator Workbench)

```
Operator reviewing Trip #1234 (Bhutan, honeymoon, 6 pax)
    → Clicks "Search Catalog" sidebar panel
    → Enters: destination="Bhutan", type="DMC", budget_range="luxury"
    → No results match
    → Clicks "Quick Add Vendor" button in empty state
    → Modal appears with 3 required fields:
        - Name: "Bhutan Spirit Tours"
        - Type: [Dropdown: Hotel / DMC / Airline / Guide / Transport / Activity]
        - Destination: "Bhutan" (pre-filled from trip)
    → [Save] → POST /api/vendors (inline, synchronous)
    → Vendor created with status="incomplete_profile"
    → Immediately appears in trip sidebar
    → Operator attaches it to Trip #1234
    → Full profile completion remains in backlog for owner/senior agent
```

**Backend behavior of quick-add**:
- Minimal validation: name uniqueness per agency, type in allowed enum, destination non-empty.
- Auto-assigns `agency_id` from the operator's current session/membership.
- Returns vendor ID immediately so the frontend can attach it to the trip without a refresh.
- Sets `status = "incomplete_profile"`, `tier = "network"` (neutral default).
- Logs an audit event: `vendor.created.quick_add` with trip_id reference.

### 4.2 Flow B: Package Discovery → Create on Missing

```
Operator searching catalog: "Bali honeymoon November 4 pax under 3L"
    → 2 active packages found (displayed in sidebar with prices)
    → Operator clicks "View" → sees inclusions, exclusions, net cost (owner-only visibility)
    → None match perfectly
    → Clicks "Create Quick Package"
    → Modal pre-fills from trip data:
        - Destination: "Bali" (from trip)
        - Duration: 5 days (from trip date window)
        - Travelers: 4 adults (from trip party_size)
    → Operator adds:
        - Name: "Bali Honeymoon Premium 5D"
        - Vendor: [Select from existing or Quick-Add new]
        - Base price: ₹2,85,000
        - Inclusions: [list]
    → Package saved as status="draft"
    → Attached to Trip #1234
    → Owner reviews and approves to status="active" via /owner/catalog/packages
```

**Key design**: Packages do not need owner approval to be attached to a trip in draft form. The operator can quote from a draft package. Owner approval gates whether it appears in general catalog search for other trips.

### 4.3 Flow C: Tie-Up on First Use

```
Operator attaches "Bali DMC - Wayan" (existing vendor, no tie-up on file) to Trip #1234
    → System detects: vendor exists but no active tie-up for this agency
    → Sidebar shows: "No negotiated terms recorded. Add tie-up?"
    → Operator clicks "Add Tie-Up"
    → Modal:
        - Valid from: today
        - Valid to: 1 year from today
        - Adult price (net): ₹12,000 per person
        - Commission %: 12%
        - Credit period: 30 days
        - Group discount: 10% for 8+ pax
    → TieUp saved as status="active" (no approval for non-exclusive types)
    → All future trips with this vendor auto-suggest these terms
    → If type="exclusive", status="draft" pending owner approval
```

### 4.4 Flow D: Post-Booking Cost Capture

```
Trip moves to "booked" status
    → Operator opens cost ledger panel
    → Adds actual vendor costs for each component:
        - Vendor: "Grand Bali Hotel"
        - Quoted to customer: ₹32,000 (3 nights)
        - Net cost paid to vendor: ₹25,600
        → System auto-calculates: margin = ₹6,400 (20%)
    → CostLedger appended to trip JSON
    → Vendor record updated: last_booked_at, booking_count++
    → If margin < agency's MarginPolicy.min_margin_pct:
        → Flag: "Margin below floor" on trip
        → Alert to owner dashboard
```

### 4.5 Flow E: Rate Update During Season

```
Owner navigates to /owner/catalog/packages/[id]
    → Sees rate table with last season's prices
    → Clicks "Update Rates for Peak Season"
    → Bulk edit or CSV upload:
        - Peak: 15 Dec – 15 Jan → adult_price: ₹18,000
        - Shoulder: 16 Jan – 31 Mar → adult_price: ₹14,000
        - Low: 1 Apr – 30 Nov → adult_price: ₹11,000
    → New Rate rows created; old ones soft-expired (valid_to set)
    → System updates package price display
    → Future trip budget feasibility uses new rates automatically
```

---

## 5. Pipeline Integration Points

Once vendor data exists, these are the specific integration points in the NB01–NB03 pipeline.

### 5.1 NB01 (Intake) — Extractors

**Current**: `sourcing_path` = `"open_market"` or `"network"` at confidence 0.3 (stub).  
**Target**: Query `Vendor` table by `destination` extracted from the trip.

```python
# In src/intake/extractors.py:_enrich_derived_signals()
# After destination resolution:

dest = packet.facts.get("resolved_destination")
budget_raw = packet.facts.get("budget_raw_text")
party_size = packet.facts.get("pax_count", 1)

catalog_match = catalog_service.find_matching_tier(
    agency_id=packet.agency_id,
    destination=dest,
    budget_hint=budget_raw,
    party_size=party_size,
)

if catalog_match.tier == "internal_package":
    path = "internal_package"
    confidence = 0.85
elif catalog_match.tier == "preferred":
    path = "preferred_supplier"
    confidence = 0.80
elif catalog_match.tier == "network":
    path = "network"
    confidence = 0.60
else:
    path = "open_market"
    confidence = 0.40

packet.set_derived_signal("sourcing_path", Slot(
    value=path, confidence=confidence, authority_level=AuthorityLevel.DERIVED_SIGNAL,
    evidence=f"{catalog_match.match_count} vendor(s) matched for {dest}",
    extraction_mode="derived", maturity="verified" if confidence > 0.7 else "heuristic",
))

packet.set_derived_signal("preferred_supplier_available", Slot(
    value=catalog_match.preferred_count > 0,
    confidence=0.90 if catalog_match.preferred_count > 0 else 0.70,
    authority_level=AuthorityLevel.DERIVED_SIGNAL,
    evidence=f"{catalog_match.preferred_count} preferred vendor(s) for {dest}",
    extraction_mode="derived", maturity="verified",
))
```

### 5.2 NB02 (Decision) — Gap & Decision Engine

**Current**: Budget feasibility from hardcoded `BUDGET_FEASIBILITY_TABLE`. No margin signals.  
**Target**:
1. Compute `estimated_minimum_cost` from real vendor rates for destination + dates + party size.
2. Replace hardcoded `BUDGET_FEASIBILITY_TABLE` with cost query.
3. Add new gap signals:
   - `PACKAGES_FOUND` — number of matching packages
   - `RATE_VALIDITY_GAPS` — no rates loaded for requested dates
   - `PREFERRED_VENDOR_AVAILABLE` — active preferred vendor match
4. Add new risk flags:
   - `margin_risk: HIGH` — if trip estimated margin < `MarginPolicy.min_margin_pct`

### 5.3 NB03 (Strategy) — Strategy Builder

**Current**: Generic internal bundle with no vendor context.  
**Target**:
- Strategy suggestion includes: *"Vendor X has active tie-up with 20% commission — suggest this first (margin: ₹45,000)"*
- If no matching packages: *"No suitable packages found — flag for custom itinerary or add package to catalog"*
- Internal bundle includes vendor contact info, tie-up terms, and net rates (owner-only visibility, protected by `safety.py`).

---

## 6. API Design (REST Routes)

| Method | Endpoint | Description | Auth Role |
|--------|----------|-------------|-----------|
| GET | `/api/vendors` | List agency vendors. Query params: `type`, `destination`, `tier`, `status`, `q` (search) | Any agency member |
| POST | `/api/vendors` | Create vendor. Quick-add supports `minimal=true` (3 fields) | Operator+ |
| GET | `/api/vendors/{id}` | Vendor detail + packages + active tie-ups | Any agency member |
| PATCH | `/api/vendors/{id}` | Update vendor | Operator+ |
| DELETE | `/api/vendors/{id}` | Soft-delete (status → "archived") | Admin+ |
| GET | `/api/vendors/{id}/packages` | Packages for this vendor | Any agency member |
| GET | `/api/packages` | List packages. Query: `vendor_id`, `destination`, `type`, `price_min`, `price_max`, `status` | Any agency member |
| POST | `/api/packages` | Create package. Requires vendor_id | Operator+ |
| GET | `/api/packages/{id}` | Package detail + rates + active tie-ups | Any agency member |
| PATCH | `/api/packages/{id}` | Update package | Operator+ |
| GET | `/api/tieups` | List tie-ups. Query: `vendor_id`, `status`, `valid_from`, `valid_to` | Any agency member |
| POST | `/api/tieups` | Create tie-up. `exclusive` types need owner approval | Operator+ |
| GET | `/api/tieups/{id}` | Tie-up detail | Any agency member |
| GET | `/api/catalog/search` | Unified search: `q`, `destination`, `type`, `budget_max`, `travelers`, `dates` | Any agency member |
| POST | `/api/trips/{trip_id}/attach-vendor` | Attach vendor to trip (adds to trip JSON) | Operator+ |
| POST | `/api/trips/{trip_id}/attach-package` | Attach package to trip (adds to trip JSON) | Operator+ |
| POST | `/api/trips/{trip_id}/cost-ledger` | Record cost entry for trip | Operator+ |
| GET | `/api/trips/{trip_id}/cost-ledger` | Get cost ledger for trip | Any agency member |

**Tenant isolation**: Every query must filter by `agency_id` from the current user's `memberships`. Never rely on client-provided agency_id for queries.

---

## 7. Frontend Surface

### 7.1 New Owner Routes (`/owner/catalog/*`)

| Route | Purpose |
|-------|---------|
| `/owner/catalog` | Overview dashboard: vendor count, active packages, tie-ups expiring soon, margin trends |
| `/owner/catalog/vendors` | Vendor list table with search, filters, "incomplete profile" badge |
| `/owner/catalog/vendors/new` | Full vendor creation form |
| `/owner/catalog/vendors/[id]` | Vendor detail: profile, packages list, tie-up history, booking history |
| `/owner/catalog/packages` | Package list with search, filters, status badges |
| `/owner/catalog/packages/new` | Full package creation form |
| `/owner/catalog/packages/[id]` | Package detail: rates table (with season tabs), tie-ups, margin analysis |
| `/owner/catalog/tieups` | Tie-up list with status filters |
| `/owner/catalog/tieups/new` | Tie-up creation form |
| `/owner/catalog/tieups/[id]` | Tie-up detail with rate history |

### 7.2 Workbench Integration (Operator View)

| Component | Location | Behavior |
|-----------|----------|----------|
| `CatalogSuggestions` | Right sidebar (new panel) | Auto-suggests vendors/packages based on trip destination, dates, travelers, budget. Sorted by: destination match, margin potential, tie-up status. |
| `QuickAddVendorModal` | Triggered from CatalogSuggestions | 3-field minimal form (name, type, destination). Saves synchronously. |
| `QuickAddPackageModal` | Triggered from CatalogSuggestions | Pre-filled from trip data. Vendor select or quick-add inline. |
| `CostLedgerPanel` | Collapsible panel below trip details | Shows per-component costs, margin calculation, total margin %. Inline "Add cost" button. |
| `AttachVendorButton` | Inline in CatalogSuggestions list | One-click attach to current trip. Saves vendor reference to trip JSON. |

---

## 8. Implementation Phasing

Guided by the dependency graph from the gap analysis: **G-01 (Supplier) → G-06 (Sourcing Engine) → C-01 (real sourcing_path) → all downstream**.

| Phase | Goal | Deliverables | Est. Effort | Acceptance Criteria |
|-------|------|--------------|-------------|---------------------|
| **P0: Core Models** | Make supplier data exist | PostgreSQL models (`Vendor`, `Package`, `TieUp`, `Rate`). Alembic migration. CRUD API routes. Model registry updated. | 2–3 days | `POST /api/vendors` creates vendor. `GET /api/vendors` lists with agency filter. `GET /api/packages` returns packages. |
| **P0: Pipeline Wiring** | Make pipeline vendor-aware | Update `extractors.py` to query `Vendor` table for `sourcing_path` and `preferred_supplier_available`. Replace hardcoded `BUDGET_FEASIBILITY_TABLE` with rate query. | 1–2 days | `sourcing_path` returns `"preferred_supplier"` when matching vendor exists. Confidence >= 0.7. |
| **P1: Workbench Quick-Add** | Enable on-the-fly vendor creation | Frontend: `CatalogSuggestions` sidebar panel. `QuickAddVendorModal`. `QuickAddPackageModal`. Backend: inline synchronous save + immediate availability. | 2 days | Operator can create vendor from workbench in < 5 seconds. Vendor immediately attachable. |
| **P1: Cost Ledger**| Enable per-trip cost tracking | CostLedger schema in trip JSON. `POST/GET /api/trips/{id}/cost-ledger`. Frontend `CostLedgerPanel`. | 1–2 days | Operator can record net cost. Margin auto-calculated. Total margin % visible. |
| **P1: Tie-Up Flow** | Enable negotiated terms capture | Tie-up creation on first vendor use. Frontend modal in workbench. Approval gate for exclusive types. | 1–2 days | Operator adds tie-up from workbench. Future trips auto-suggest terms. |
| **P2: Smart Suggestions** | AI-powered catalog matching | Cross-search endpoint. Ranking by destination match + margin potential + suitability score. | 2–3 days | Search "honeymoon bali nov 4pax under 3L" returns ranked packages with margin visibility. |

**Total estimated effort**: ~8–12 days for full P0–P2 implementation.

---

## 9. Decisions Required & Recommendations

| # | Decision | Options | Recommendation | Rationale |
|---|----------|---------|----------------|-----------|
| 1 | Storage layer for master data | (a) PostgreSQL, (b) JSON files, (c) External CRM | **(a) PostgreSQL** | Relational queries, tenant isolation, CRUD, Alembic migrations. JSON files cannot support filtered search at scale. |
| 2 | Who enters initial vendor data? | (a) Owner via UI, (b) CSV bulk import, (c) Auto-extract from past bookings | **(b) CSV first, then (a)** | Most agencies have preferred hotel lists in Excel. Quick UI for spot additions. Auto-extraction is Phase 3+. |
| 3 | Is margin data visible to agents? | (a) Owner-only, (b) Owner + senior, (c) All | **(a) Owner-only** | Already modeled in `safety.py`. Margin visibility to agents risks selection bias (always picking highest margin, not best fit). |
| 4 | Should `sourcing_path` be overrideable? | (a) System decides, (b) Agent override with reason, (c) Agent decides freely | **(b) Override with reason** | Preferred suppliers are *preferred*, not *mandatory*. Operator judgment must be preserved. |
| 5 | Minimum margin floor | (a) 5%, (b) 10%, (c) Per-destination config | **(c) Per-destination config** | Bali honeymoon margins differ from domestic pilgrimage margins. Owner sets per-destination policy in `MarginPolicy`. |
| 6 | Quick-add vendor validation | (a) Strict (all fields required), (b) Minimal (3 fields), (c) Configurable | **(b) Minimal** | The goal is zero friction during trip processing. Incomplete profiles are completed later. |
| 7 | Package approval gate | (a) All packages need owner approval, (b) Draft packages attachable immediately, active status requires approval | **(b) Draft attachable immediately** | Operators need to quote from draft packages. Owner approval gates general catalog availability. |

---

## 10. Risks & Mitigations

| Risk | Severity | Mitigation |
|------|----------|------------|
| **Supplier data decays** — owner never updates stale rates | High | Add `last_verified` to `Vendor` and `Rate`. Flag rates > 90 days since update. Dashboard alert: "12 rates pending verification." |
| **Margin optimization gets gamed** — agents always pick highest-margin options | Medium | System ranks by *suitability first*, margin second. Margin is a tiebreaker, not primary sort. Owner sees margin-adherence dashboard per agent. |
| **Sourcing path bias** — system always recommends same 3 hotels | Medium | Add diversity score to ranking. Track unique suppliers used per destination. Alert on concentration risk: "80% of Bali bookings use same vendor." |
| **Cost data leaks to travelers** | High | Extend `safety.py` to strip cost ledger and margin fields from all traveler-facing API responses / bundles. Add integration test for every new catalog endpoint. |
| **Data entry burden** — owner never fills in supplier database | High | Start with CSV import + inline quick-add. Provide Excel template download in `/owner/catalog/vendors`. Track adoption metric: % of trips with catalog-attached vendors. |
| **Internal packages become rigid** — system prevents customization | Medium | `Package.flexibility` field marks hard vs soft components. Operators can swap soft components freely. Draft packages are inherently flexible. |

---

## 11. Files to Create / Modify

**New models**: `spine_api/models/vendor.py`
**Updated model registry**: `spine_api/models/__init__.py`
**New Alembic revision**: `alembic/versions/<revision>_add_vendor_package_tieup_rate_models.py`
**New routers**: `spine_api/routers/vendors.py`, `spine_api/routers/packages.py`, `spine_api/routers/catalog.py`
**Updated server**: `spine_api/server.py` (register new routers)
**Pipeline integration**: `src/intake/extractors.py` (sourcing_path query)
**Frontend routes**: `frontend/app/owner/catalog/*` (new route group)
**Frontend components**: `CatalogSuggestions.tsx`, `QuickAddVendorModal.tsx`, `QuickAddPackageModal.tsx`, `CostLedgerPanel.tsx`

---

## 12. Open Questions

1. **Should vendor data be shared across agencies in a network/consortium?** Current model is per-agency only. Multi-agency vendor sharing is a future feature.
2. **Should packages support versioning?** If a package is updated mid-season, do attached trips reference the old version or auto-migrate?
3. **How should rate validity interact with trip date windows?** If a trip spans two rate seasons (e.g., Dec 28 – Jan 3), should the system blend rates or require explicit split pricing?
4. **Should the `NegotiationEngine` stub be preserved or replaced by tie-up data?** The current mock negotiation engine can be replaced by checking active tie-ups for margin improvement opportunities.
5. **What is the P0 scope for MarginPolicy?** The simplest version: per-agency `min_margin_pct` stored in `agency_settings`. Per-destination floors are P1.

---

*End of document. Ready for review and implementation kickoff.*
