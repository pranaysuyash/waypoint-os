# Travel Package Lifecycle Management — Master Index

> Series index for the Package Lifecycle Management research documents covering catalog, pricing, booking, and operations.

---

## Series Overview

**Focus:** End-to-end lifecycle management for travel packages, from catalog creation through operations and retirement
**Status:** Research Exploration
**Last Updated:** 2026-04-28

**Context:** This series addresses the **internal package management** lifecycle — how Indian travel agencies create, price, sell, operate, and analyze travel packages. This is distinct from the external Package Tours series (see below) which focuses on third-party tour operator integration.

---

## Document Series

| # | Document | Focus | Status |
|---|----------|-------|--------|
| 1 | [Package Catalog](./PACKAGE_01_CATALOG.md) | Package types, data models, variants, search, comparison, India-specific categories | Complete |
| 2 | [Package Pricing](./PACKAGE_02_PRICING.md) | Pricing strategies, seasonal/occupancy pricing, GST, TCS, channel markups | Complete |
| 3 | [Package Booking](./PACKAGE_03_BOOKING.md) | Booking lifecycle, inventory, waitlist, group bookings, amendments, cancellations | Complete |
| 4 | [Package Operations](./PACKAGE_04_OPERATIONS.md) | Supplier coordination, vouchers, departure prep, on-tour dashboard, feedback, analytics | Complete |

---

## Key Themes Across the Series

### 1. Package Type Spectrum

The series covers three fundamental package types that span the full flexibility spectrum:

```
FIXED-DEPARTURE          CUSTOMIZABLE             DYNAMIC PACKAGING
(Rigid, Group)           (Guided Choice)          (Full Freedom)

Set dates                Valid date range         Any dates
Set itinerary            Base + optional swaps    Build from scratch
Group travel             Individual/family        Individual/family
Tour leader              May include guide        Self-guided
Guaranteed departure     Flexible booking         Real-time inventory

Examples:                Examples:                Examples:
• Char Dham Yatra        • Kerala Honeymoon       • Agent-assembled
• Europe Group Tour      • Rajasthan Family       • Customer picks all
• School Trip            • Goa Weekend            • Multi-supplier combo
```

### 2. India-Specific Regulatory Context

| Regulation | Applicability | Key Rate | Document |
|------------|--------------|----------|----------|
| **GST (5%)** | Accommodation-centric bundled packages | 5% of package cost | PACKAGE_02_PRICING |
| **GST (18%)** | Activity-centric or non-accommodation packages | 18% of package cost | PACKAGE_02_PRICING |
| **TCS (5%)** | Overseas tour packages | 5% from first rupee | PACKAGE_02_PRICING |
| **State Tourism Cess** | Varies by state (Kerala 1%, Rajasthan 1.5%) | 1-2% of hotel stay | PACKAGE_02_PRICING |
| **Pilgrimage Registration** | Char Dham, Amarnath Yatra | Mandatory registration | PACKAGE_01_CATALOG |
| **Adventure Activity Regulation** | Trekking, rafting, paragliding | Safety certifications | PACKAGE_01_CATALOG |
| **Medical Fitness** | High-altitude pilgrimages, adventure | Doctor certificate required | PACKAGE_03_BOOKING |
| **HSN/SAC Codes** | Invoice compliance for all packages | Per-component classification | PACKAGE_02_PRICING |

### 3. India-Specific Package Categories

| Category | Target Audience | Key Considerations | Document |
|----------|----------------|--------------------|--------- ---------|
| **Honeymoon** | Newly married couples | Romantic inclusions, privacy, couple-centric | PACKAGE_01_CATALOG |
| **Pilgrimage** | Religious travelers (all faiths) | Dietary compliance, accessibility, ritual assistance | PACKAGE_01_CATALOG |
| **Educational** | Schools and colleges | Safety protocols, teacher ratios, learning objectives | PACKAGE_01_CATALOG |
| **Corporate Offsite** | Companies | Meeting rooms, AV equipment, team building | PACKAGE_01_CATALOG |
| **Adventure** | Youth, thrill-seekers | Safety certifications, equipment, fitness requirements | PACKAGE_01_CATALOG |
| **Senior Citizen** | Elderly travelers | Accessibility, medical support, slow pace | PACKAGE_01_CATALOG |

### 4. Technology Stack (Proposed)

| Layer | Technology Options | Rationale |
|-------|-------------------|-----------|
| **Package Catalog DB** | PostgreSQL + JSONB for flexible schema | Package variants and inclusions need flexible schema |
| **Pricing Engine** | Custom TypeScript service with rule engine | Complex markup, seasonal, occupancy rules need full control |
| **Search/Discovery** | PostgreSQL full-text + pg_trgm or Elasticsearch | Faceted search with package-specific filters |
| **Booking State Machine** | Custom state machine (XState or similar) | Complex lifecycle with many transitions and guards |
| **Inventory Management** | PostgreSQL with row-level locking | Concurrent holds and bookings need ACID guarantees |
| **Voucher Generation** | React-PDF or Puppeteer for PDF generation | Branded vouchers with QR codes and supplier details |
| **On-Tour Dashboard** | React + WebSocket for real-time updates | Live trip tracking with alert push notifications |
| **Feedback Collection** | WhatsApp Business API + Web form | WhatsApp-first survey delivery for Indian market |
| **Analytics** | PostgreSQL + materialized views or ClickHouse | Package performance metrics need efficient aggregation |
| **Document Delivery** | WhatsApp Business API + Email (SendGrid) + App push | Multi-channel delivery for Indian consumer preferences |

### 5. Cross-Series Data Flow

```
PACKAGE CATALOG                 PACKAGE PRICING
(PACKAGE_01)                    (PACKAGE_02)
    │                               │
    │  Package definition           │  Calculated price
    │  Inclusions/exclusions        │  Tax configuration
    │  Variants                     │  Markup rules
    │  Search facets                │  Seasonal tiers
    │                               │
    └───────────┬───────────────────┘
                │
                ▼
         PACKAGE BOOKING
         (PACKAGE_03)
                │
                │  Confirmed booking
                │  Payment schedule
                │  Traveler details
                │  Room allocation
                │
                ▼
         PACKAGE OPERATIONS
         (PACKAGE_04)
                │
                │  Supplier coordination
                │  Voucher generation
                │  On-tour monitoring
                │  Feedback collection
                │
                ▼
         PERFORMANCE ANALYTICS
         ┌──────┴──────┐
         │              │
         ▼              ▼
   Package updates   Package retirement
   (back to CATALOG) (archive)
```

---

## Cross-References to Related Series

### Directly Related

| Series | Relationship | Key Overlap |
|--------|-------------|-------------|
| **[Package Tours](./PACKAGE_TOURS_MASTER_INDEX.md)** | External tour operator integration | Provider landscape, API integration, commission structures |
| **[Trip Builder](./TRIP_BUILDER_MASTER_INDEX.md)** | Dynamic package assembly | Itinerary construction, multi-component pricing |
| **[Booking Engine](./BOOKING_ENGINE_MASTER_INDEX.md)** | Core booking infrastructure | Reservation state machine, inventory, cancellations |
| **[Pricing Engine](./PRICING_ENGINE_MASTER_INDEX.md)** | Dynamic pricing infrastructure | Margin management, competitive pricing |
| **[Accommodation Catalog](./ACCOMMODATION_CATALOG_MASTER_INDEX.md)** | Hotel component of packages | Property data, room types, meal plans |
| **[Activities](./ACTIVITIES_MASTER_INDEX.md)** | Activity component of packages | Activity providers, booking, scheduling |

### Supporting Series

| Series | Relationship | Key Overlap |
|--------|-------------|-------------|
| **[CRM](./CRM_MASTER_INDEX.md)** | Customer profiles for package buyers | Traveler history, preferences, repeat booking |
| **[Finance](./FINANCE_MASTER_INDEX.md)** | Financial reconciliation | GST filing, TCS remittance, supplier payments |
| **[Commission](./COMMISSION_MASTER_INDEX.md)** | Agent commission on package sales | Booking-based commission, markup sharing |
| **[Document Generation](./DOCUMENT_GENERATION_MASTER_INDEX.md)** | Voucher and itinerary generation | PDF templates, delivery channels |
| **[Notifications](./NOTIFICATION_MESSAGING_MASTER_INDEX.md)** | Booking and travel notifications | WhatsApp-first delivery, payment reminders |
| **[Regulatory](./REGULATORY_MASTER_INDEX.md)** | Compliance requirements | GST, TCS, licensing, pilgrimage regulations |
| **[Analytics/BI](./ANALYTICS_BI_MASTER_INDEX.md)** | Performance dashboards | Package performance, fill rate, profitability |
| **[Group Tours](./GROUP_MASTER_INDEX.md)** | Group-specific management | Group contracts, rooming lists, leader policies |
| **[Refund/Cancellation](./REFUND_CANCELLATION_MASTER_INDEX.md)** | Cancellation processing | Refund calculations, partial cancellations |
| **[Supplier Settlement](./SUPPLIER_SETTLEMENT_MASTER_INDEX.md)** | Supplier payment management | Invoice matching, payment scheduling |

---

## Series-Wide Open Problems

These problems span multiple documents and require cross-cutting solutions:

1. **GST Classification Engine** — Automatically determining 5% vs 18% GST based on package composition requires integration between the catalog (component breakdown) and pricing (tax calculation) modules.

2. **Unified Package Model** — Fixed-departure, customizable, and dynamic packages have fundamentally different booking flows but share common infrastructure (pricing, inventory, operations). Finding the right abstraction level is critical.

3. **Real-Time Availability Aggregation** — For dynamic packaging, real-time availability from hotels, flights, activities, and transfers must be aggregated into a single go/no-go decision. Latency and partial availability are challenges.

4. **Seasonal Pricing Complexity** — A multi-destination package (e.g., Golden Triangle + Goa) crosses different seasonal zones. How does the pricing engine apply different seasonal multipliers to different legs of the same package?

5. **Operational Scaling** — During peak season (October-March), a mid-size agency may operate 50+ simultaneous departures. The operations dashboard and supplier coordination system must scale accordingly.

6. **Channel Conflict** — Same package sold directly (₹42,000), via OTA (₹45,000 with commission), and through franchise (₹39,900 with revenue share). How do we manage price parity and channel conflict?

7. **Data Migration** — Existing agencies have packages in PDFs, Excel sheets, and agent memory. Structured catalog import and pricing configuration from unstructured sources is a significant challenge.

---

## Implementation Priority

### Phase 1: Foundation
- Package catalog data model (PACKAGE_01)
- Basic pricing calculator with GST (PACKAGE_02)
- Simple booking lifecycle (PACKAGE_03)
- Voucher generation (PACKAGE_04)

### Phase 2: Core Features
- Search and comparison (PACKAGE_01)
- Seasonal and occupancy pricing (PACKAGE_02)
- Waitlist and group bookings (PACKAGE_03)
- Departure checklist (PACKAGE_04)

### Phase 3: Intelligence
- Dynamic pricing (PACKAGE_02)
- Amendment management (PACKAGE_03)
- On-tour dashboard (PACKAGE_04)
- Package performance analytics (PACKAGE_04)

### Phase 4: Optimization
- Channel markup management (PACKAGE_02)
- Automated supplier coordination (PACKAGE_04)
- Feedback-driven package improvement (PACKAGE_04)
- Package lifecycle and retirement (PACKAGE_01, PACKAGE_04)

---

## Document Details

### PACKAGE_01_CATALOG.md
- Package type taxonomy (fixed-departure, customizable, dynamic)
- Data models for inclusions/exclusions/variants
- Seasonal pricing tier definitions
- Search and comparison UX
- India-specific package types (honeymoon, pilgrimage, educational, corporate)
- Catalog management workflow

### PACKAGE_02_PRICING.md
- Pricing strategy models (cost-plus, margin, competitive, dynamic)
- Markup configuration by category and channel
- Seasonal and demand-based pricing
- Occupancy-based pricing (single/double/triple/quad)
- Child pricing policy
- Early bird and last-minute pricing
- GST on package components (5% vs 18%, HSN/SAC codes)
- TCS on overseas packages (Section 206C(1G))
- State tourism taxes
- Multi-currency pricing for international packages

### PACKAGE_03_BOOKING.md
- Booking lifecycle stages (inquiry through completion)
- Inventory allocation and hold management
- Departure guarantee rules
- Cancellation policy tiers
- Group booking management (contracts, rooming lists, split payments)
- Waitlist management (priority rules, fairness, automation)
- Booking amendments and modifications
- Partial cancellation handling
- Payment schedules and milestones

### PACKAGE_04_OPERATIONS.md
- Supplier coordination timeline and reconfirmation
- Voucher and document generation
- Departure preparation checklist
- On-tour operations dashboard
- Ground handling and local coordination
- Customer feedback collection
- Post-tour analytics and cost reconciliation
- Package performance metrics (fill rate, profitability, repeat rate)
- Package retirement and archival

---

**Status:** All 4 research documents complete
**Last Updated:** 2026-04-28
