# Agency Network & Franchise Management 01: Network Models

> Research document for agency network structures, ownership models, brand hierarchy, territory management, franchise agreement terms, commission structures, and network governance in the Indian travel market.

---

## Key Questions

1. **What network models exist for travel agencies scaling beyond a single office?**
2. **How do ownership structures (owned, franchised, consortium) affect platform architecture?**
3. **What is the brand hierarchy and how does it propagate across network nodes?**
4. **How do we model territory management and exclusivity?**
5. **What are the standard franchise agreement terms in Indian travel?**
6. **How do commission structures flow across network tiers?**
7. **What governance model balances franchisor control with franchisee autonomy?**

---

## Research Areas

### A. Network Models

```typescript
interface AgencyNetwork {
  networkId: string;
  networkType: NetworkType;
  brand: BrandEntity;
  nodes: NetworkNode[];
  governance: NetworkGovernance;
  createdAt: Date;
}

type NetworkType =
  | 'single_office'                    // One location, one team
  | 'multi_branch'                     // Corporate-owned branches
  | 'franchise'                        // Franchised locations
  | 'consortium'                       // Independent agencies alliance
  | 'hybrid';                          // Mix of owned + franchised + consortium

// Network model comparison:
//
// SINGLE OFFICE:
// ┌─────────────────────┐
// │   Agency HQ         │
// │   (1 location)      │
// │   Owner = Operator  │
// └─────────────────────┘
// Scale:     1 location
// Control:   Full
// Revenue:   100% owner
// Risk:      Concentrated
// Example:   Neighborhood travel agent in Jaipur
//
// MULTI-BRANCH (Corporate):
// ┌─────────────────────┐
// │   Agency HQ         │
// │   (Corporate Office)│
// └──────┬──────────────┘
//    ┌───┴───┬───────┐
// ┌───┴──┐┌──┴───┐┌──┴───┐
// │Br. 1 ││Br. 2 ││Br. 3 │
// │Delhi ││Mumbai││Chennai│
// │Owned ││Owned ││Owned  │
// └──────┘└──────┘└──────┘
// Scale:     2-20 locations
// Control:   Full (centralized)
// Revenue:   100% corporate
// Risk:      Capital intensive
// Example:   Thomas Cook (India) branch network
//
// FRANCHISE:
// ┌─────────────────────┐
// │   Franchisor HQ     │
// │   (Brand Owner)     │
// └──────┬──────────────┘
//    ┌───┴───┬───────┬────────┐
// ┌───┴──┐┌──┴───┐┌──┴───┐┌──┴───┐
// │Fr. 1 ││Fr. 2 ││Owned ││Fr. 3 │
// │Pune  ││Kolka-││Delhi ││Hyder-│
// │Fran. ││ta    ││HQ    ││abad  │
// └──────┘└──────┘└──────┘└──────┘
// Scale:     5-500+ locations
// Control:   Brand standards, ops autonomy
// Revenue:   Royalties + franchise fees
// Risk:      Brand risk, lower control
// Example:   Cox & Kings franchise network
//
// CONSORTIUM:
// ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐
// │Agency│ │Agency│ │Agency│ │Agency│
// │  A   │ │  B   │ │  C   │ │  D   │
// │Indep.│ │Indep.│ │Indep.│ │Indep.│
// └──┬───┘ └──┬───┘ └──┬───┘ └──┬───┘
//    └─────────┴────────┴────────┘
//        Consortium Agreement
//        (Shared buying power)
// Scale:     10-500 independent agencies
// Control:   Minimal (voluntary standards)
// Revenue:   Membership fees + volume rebates
// Risk:      Low commitment, low control
// Example:   TAFI consortium, UFTAA members
```

### B. Network Node & Ownership

```typescript
interface NetworkNode {
  nodeId: string;
  networkId: string;
  nodeType: NodeType;
  ownership: OwnershipModel;
  brand: NodeBrandConfig;
  territory: Territory;
  operationalStatus: OperationalStatus;
  performance: NodePerformance;
}

type NodeType =
  | 'headquarters'                     // Corporate HQ, primary operations
  | 'corporate_branch'                 // Company-owned branch
  | 'franchise'                        // Franchised location
  | 'satellite'                        // Small kiosk / counter
  | 'consortium_member'                // Independent member of consortium
  | 'master_franchise';                // Regional master franchisor

interface OwnershipModel {
  ownershipType: OwnershipType;
  owner: OwnerDetail;
  agreementId?: string;                // Franchise agreement ref
  parentNodeId?: string;               // Parent in hierarchy
  subsidiaryNodes?: string[];          // Child nodes
  acquiredDate: Date;
  legalEntity: string;                 // Registered company name
  gstRegistration: string;            // GST number (separate per entity)
  pan: string;                         // PAN for tax
}

type OwnershipType =
  | 'sole_proprietorship'              // Individual owner
  | 'partnership'                      // Partnership firm
  | 'private_limited'                  // Pvt Ltd company
  | 'llp'                              // Limited Liability Partnership
  | 'franchisee_company'               // Franchisee's legal entity
  | 'consortium_member';               // Independent entity in consortium

// Ownership implications for platform:
//
// ┌──────────────────┬──────────────────────────────────────────┐
// │ Ownership Type   │ Platform Implications                     │
// ├──────────────────┼──────────────────────────────────────────┤
// │ Proprietorship   │ Single user, no team hierarchy,          │
// │                  │ personal GST/PAN, simple commission      │
// ├──────────────────┼──────────────────────────────────────────┤
// │ Partnership      │ Multiple partners as stakeholders,       │
// │                  │ profit sharing per deed, joint GST       │
// ├──────────────────┼──────────────────────────────────────────┤
// │ Pvt Ltd          │ Full team management, salary payroll,    │
// │                  │ corporate GST, TDS compliance            │
// ├──────────────────┼──────────────────────────────────────────┤
// │ Franchisee       │ Brand compliance layer, royalty payouts, │
// │                  │ shared supplier contracts, separate P&L  │
// ├──────────────────┼──────────────────────────────────────────┤
// │ Consortium       │ Light integration, shared inventory,     │
// │                  │ referral tracking, joint marketing       │
// └──────────────────┴──────────────────────────────────────────┘
```

### C. Brand Hierarchy

```typescript
interface BrandEntity {
  brandId: string;
  brandName: string;                    // "TravelEase India"
  brandLevel: BrandLevel;
  parentBrandId?: string;
  brandGuidelines: BrandGuidelines;
  visualIdentity: VisualIdentity;
  communicationTone: CommunicationTone;
}

type BrandLevel =
  | 'master_brand'                     // Top-level brand (franchisor)
  | 'sub_brand'                        // Regional or segment sub-brand
  | 'co_brand'                         // Co-branded with partner
  | 'white_label'                      // Fully rebranded for franchisee
  | 'consortium_brand';                // Collective brand for consortium

interface NodeBrandConfig {
  nodeId: string;
  brandOverrides: BrandOverrides;      // What franchisee can customize
  brandLocked: BrandLockedConfig;      // What franchisor mandates
  complianceScore: number;             // 0-100 brand compliance score
}

interface BrandOverrides {
  localContactInfo: LocalContactInfo;  // Franchisee's address, phone
  localTestimonials: boolean;          // Can show local customer reviews
  localPromotions: boolean;            // Can run local area promotions
  officePhotos: boolean;               // Can add office/branch photos
  customGreeting: string;              // Welcome text on customer portal
}

interface BrandLockedConfig {
  logo: boolean;                       // Must use brand logo
  colorPalette: boolean;               // Must use brand colors
  emailTemplates: boolean;             // Must use brand email templates
  invoiceFormat: boolean;              // Must use brand invoice format
  serviceStandards: boolean;           // Must follow brand service SLAs
  customerCommunication: boolean;      // Must follow brand tone
  pricingVisibility: boolean;          // Brand controls price display rules
}

// Brand hierarchy example:
//
// TravelEase India (Master Brand)
// ├── TravelEase Delhi (Corporate HQ) — Full brand, no overrides
// ├── TravelEase Mumbai (Corporate Branch) — Full brand, local contact
// ├── TravelEase Pune (Franchise) — Brand + local office photos
// │   └── Can customize: phone, address, local testimonials
// │   └── Must keep: logo, colors, email format, invoice format
// ├── TravelEase Hyderabad (Franchise) — Brand + local contact
// └── TravelEase Lite — Kochi (White Label Franchise)
//     └── Can customize: logo, colors, name (with approval)
//     └── Must keep: email templates, service standards, invoice format
```

### D. Territory Management

```typescript
interface Territory {
  territoryId: string;
  nodeId: string;
  geography: TerritoryGeography;
  exclusivity: ExclusivityType;
  overlapRules: OverlapRule[];
  performance: TerritoryPerformance;
}

interface TerritoryGeography {
  type: GeographyType;
  regions: TerritoryRegion[];
  postalCodes?: string[];               // Pin code based (India)
  cities?: string[];
  states?: string[];
  radius?: RadiusConfig;                // For proximity-based territories
}

type GeographyType =
  | 'postal_code'                      // By pin code (most granular)
  | 'city'                             // By city/town
  | 'district'                         // By district
  | 'state'                            // By state
  | 'national'                         // Entire country
  | 'radius';                          // Radius around office location

type ExclusivityType =
  | 'exclusive'                        // No other node in this territory
  | 'non_exclusive'                    // Multiple nodes, open competition
  | 'primary'                          // Primary + secondary overlap allowed
  | 'category_exclusive';              // Exclusive for certain trip categories

// Territory example for Indian market:
//
// TravelEase Franchise — Pune Territory
//
// Geography:
//   Type: postal_code + city
//   City: Pune
//   District: Pune District
//   Pin codes: 411001-411060 (core city)
//   Excluded: Hinjewadi (corporate branch territory)
//
// Exclusivity: Exclusive
//   - No other TravelEase franchise in Pune city limits
//   - Corporate can refer Pune customers to this franchise
//   - Franchise cannot market in Mumbai territory
//
// Population: ~7M (Pune metro)
// Estimated market: 50,000 outbound trips/year
// Target market share: 2% (1,000 trips/year)
// Minimum guarantee: ₹25L annual revenue
```

### E. Franchise Agreement Terms

```typescript
interface FranchiseAgreement {
  agreementId: string;
  franchisorId: string;
  franchiseeId: string;
  territory: Territory;
  term: AgreementTerm;
  fees: FranchiseFees;
  obligations: FranchiseObligations;
  compliance: ComplianceRequirements;
  renewal: RenewalTerms;
  termination: TerminationTerms;
  executedDate: Date;
  status: AgreementStatus;
}

type AgreementStatus =
  | 'draft'
  | 'under_negotiation'
  | 'executed'
  | 'active'
  | 'suspended'
  | 'terminated'
  | 'expired';

interface AgreementTerm {
  startDate: Date;
  endDate: Date;
  durationMonths: number;               // Typically 36-60 months
  renewalOption: boolean;
  lockInPeriod: number;                 // Months before exit allowed
  exitNoticePeriod: number;             // Months of notice for termination
}

// Standard franchise terms in Indian travel:
//
// ┌──────────────────┬──────────────────────────────────────────┐
// │ Term Element     │ Typical Range                             │
// ├──────────────────┼──────────────────────────────────────────┤
// │ Agreement        │ 3-5 years (renewable)                     │
// │ Lock-in period   │ 12-24 months                              │
// │ Exit notice      │ 3-6 months                                │
// │ Territory        │ Exclusive city/district                   │
// │ Renewal          │ Auto-renewal with consent                 │
// │ Non-compete      │ 12 months post-termination               │
// └──────────────────┴──────────────────────────────────────────┘

interface FranchiseFees {
  // One-time fees
  franchiseFee: Money;                  // Joining fee: ₹2-10 lakh
  setupFee: Money;                      // Platform setup: ₹50K-2 lakh
  trainingFee: Money;                   // Initial training: ₹25K-1 lakh
  deposit: Money;                       // Security deposit: ₹1-5 lakh

  // Recurring fees
  royalty: RoyaltyStructure;            // Monthly royalty
  marketingFund: Money;                 // National marketing contribution
  technologyFee: Money;                 // Platform usage fee: ₹5-25K/month

  // Performance fees
  minimumGuarantee: Money;              // Min. monthly royalty guarantee
  performanceBonus: PerformanceBonus[]; // Bonus for exceeding targets
}

interface RoyaltyStructure {
  type: RoyaltyType;
  rate: number;                         // Percentage or fixed amount
  base: RoyaltyBase;                    // What the royalty is calculated on
  frequency: 'monthly' | 'quarterly';
  minimum: Money;                       // Floor amount
}

type RoyaltyType =
  | 'percentage_of_revenue'             // 5-15% of gross revenue
  | 'percentage_of_profit'              // 10-25% of net profit
  | 'fixed_monthly'                     // Fixed ₹ amount per month
  | 'tiered_percentage'                 // Slab-based % on revenue
  | 'per_booking';                      // Fixed ₹ per booking processed

type RoyaltyBase =
  | 'gross_revenue'                     // Total revenue before costs
  | 'net_revenue'                       // Revenue minus supplier payments
  | 'commission_income'                 // Only commission earned
  | 'service_fees';                     // Only service fee income

// Royalty tier example:
//
// ┌────────────────────┬─────────────┬───────────────┐
// │ Monthly Revenue    │ Royalty %   │ Min. Guarantee │
// ├────────────────────┼─────────────┼───────────────┤
// │ ₹0 - ₹5 lakh      │ 8%          │ ₹25,000       │
// │ ₹5 - ₹15 lakh     │ 6%          │ ₹40,000       │
// │ ₹15 - ₹30 lakh    │ 5%          │ ₹60,000       │
// │ ₹30 lakh+         │ 4%          │ ₹90,000       │
// └────────────────────┴─────────────┴───────────────┘
// Note: Slabs incentivize growth. Higher volume = lower royalty %.
```

### F. Commission Structures Across Network

```typescript
interface NetworkCommissionStructure {
  networkId: string;
  levels: CommissionLevel[];
  distributionRules: DistributionRule[];
  specialCases: CommissionSpecialCase[];
}

interface CommissionLevel {
  level: number;                        // 0 = customer-facing, 1 = agent, etc.
  recipient: CommissionRecipient;
  rate: number;                         // Percentage
  calculationBase: CommissionBase;
  conditions?: CommissionCondition[];
}

// Commission flow in a franchise network:
//
// Customer pays ₹1,00,000 for Kerala package
//
// ┌─────────────────────────────────────────────────────────┐
// │ Revenue Distribution                                     │
// ├─────────────────────────────────────────────────────────┤
// │ Supplier costs (hotels, flights, etc.):    ₹78,000      │
// │ GST (5% on tour package):                   ₹5,000      │
// │ Gross agency income:                       ₹17,000      │
// │                                                          │
// │ Distribution of ₹17,000:                                │
// │   Booking Agent commission (L1):     ₹2,550 (15%)       │
// │   Branch Manager override (L2):      ₹1,020 (6%)        │
// │   Franchisee retention:              ₹9,180 (54%)        │
// │   Royalty to Franchisor (8%):        ₹1,360              │
// │   Marketing fund (2%):                 ₹340              │
// │   Technology platform fee:             ₹500              │
// │   Net to franchisee:                 ₹9,180 - ₹2,550    │
// │                                      - ₹1,020 = ₹5,610  │
// └─────────────────────────────────────────────────────────┘
//
// In a consortium model:
//
// Customer pays ₹1,00,000 for Kerala package
//
// ┌─────────────────────────────────────────────────────────┐
// │ Revenue Distribution (Consortium)                        │
// ├─────────────────────────────────────────────────────────┤
// │ Supplier costs:                            ₹78,000      │
// │ GST:                                       ₹5,000      │
// │ Gross agency income:                       ₹17,000      │
// │                                                          │
// │ Distribution of ₹17,000:                                │
// │   Booking Agent:                           ₹2,550       │
// │   Agency retains:                         ₹13,750       │
// │   Consortium membership fee (monthly):      already paid │
// │   Consortium volume rebate (quarterly):     ₹850 (5%)    │
// │   Referral fee (if referred by another):    ₹500        │
// │   Net to agency:                         ₹13,750        │
// └─────────────────────────────────────────────────────────┘
```

### G. Network Governance

```typescript
interface NetworkGovernance {
  networkId: string;
  governanceModel: GovernanceModel;
  decisionBodies: DecisionBody[];
  policies: NetworkPolicy[];
  disputeResolution: DisputeResolution;
  reporting: GovernanceReporting;
}

type GovernanceModel =
  | 'centralized'                      // Franchisor decides everything
  | 'federal'                          // HQ sets standards, nodes have autonomy
  | 'democratic'                       // Consortium: members vote
  | 'advisory';                        // HQ advises, nodes decide

// Governance model comparison:
//
// CENTRALIZED (Franchise — strict):
// Franchisor sets: pricing, suppliers, branding, marketing, SLAs
// Franchisee controls: local hiring, daily operations, customer service
// Best for: Strong brand, premium positioning (e.g., luxury travel)
//
// FEDERAL (Franchise — flexible):
// Franchisor sets: brand guidelines, minimum standards, technology
// Franchisee controls: pricing (within range), local suppliers, marketing
// Best for: Mid-market, diverse geography (e.g., pan-India network)
//
// DEMOCRATIC (Consortium):
// Members vote on: shared suppliers, marketing campaigns, membership rules
// Individual controls: everything else (branding, pricing, operations)
// Best for: Independent agencies seeking buying power without brand sacrifice
//
// ADVISORY (Loose consortium / referral network):
// Network provides: recommendations, shared tools, best practices
// Members control: everything, participation is voluntary
// Best for: Informal alliances, referral groups

interface NetworkPolicy {
  policyId: string;
  category: PolicyCategory;
  title: string;
  description: string;
  applicability: PolicyApplicability;
  enforcement: EnforcementLevel;
}

type PolicyCategory =
  | 'brand_compliance'
  | 'pricing_guidelines'
  | 'supplier_usage'
  | 'customer_service'
  | 'data_privacy'
  | 'financial_reporting'
  | 'marketing'
  | 'technology';

type EnforcementLevel =
  | 'mandatory'                        // Violation = penalty / termination
  | 'recommended'                      // Best practice, no penalty
  | 'monitored';                       // Tracked, escalation if repeated

// India-specific regulatory context for network governance:
//
// 1. GST Registration:
//    - Each franchisee entity needs separate GST registration
//    - Franchisor collects royalty — must issue GST invoice (18% on services)
//    - Input tax credit flow: franchisee → franchisor on royalty
//    - E-invoicing mandatory if turnover > ₹5 crore
//
// 2. IATA Accreditation Transfer:
//    - IATA accreditation is tied to legal entity, not transferable
//    - Franchisee must apply for own IATA accreditation OR
//    - Use franchisor's BSP billing through sub-agent arrangement
//    - Sub-agent arrangement requires IATA Accredited Agent as guarantor
//
// 3. RBI Guidelines for Franchise Fees:
//    - Franchise fees are service receipts (not FDI)
//    - No prior RBI approval needed for domestic franchise
//    - International franchise (foreign brand) may need FDI compliance
//    - Royalty payments to foreign franchisor capped at sectoral limits
//    - TDS deduction at 10% on franchise fee payments (Section 194J)
//
// 4. Consumer Protection:
//    - Consumer Protection Act 2019 applies to franchisor AND franchisee
//    - Customer can sue either or both for service deficiency
//    - Franchise agreement must define liability allocation
//    - Unfair trade practice clauses in agreement
//
// 5. Competition Act:
//    - Territory exclusivity must not violate Competition Commission rules
//    - Price fixing across franchise network needs careful structuring
//    - RPM (Resale Price Maintenance) can be scrutinized
```

---

## Open Problems

### 1. Multi-Entity GST Compliance
Each franchisee is a separate legal entity with its own GST registration. The platform must track GST per entity, generate separate e-invoices, and handle inter-entity service billing (franchisor to franchisee). Complex when a single trip involves services from multiple network nodes.

### 2. IATA Sub-Agent Model Friction
Franchisees who lack IATA accreditation must ticket through the franchisor's BSP. This creates bottlenecks (batch ticketing), settlement delays, and agent-level commission tracking challenges. Platform needs a sub-agent ticketing workflow that feels seamless.

### 3. Territory Dispute Resolution
When a customer from Pune (franchise territory) books through the Delhi HQ website, who gets credit? Online bookings cross territory boundaries. Need clear digital territory rules, referral tracking, and automated revenue splitting.

### 4. Data Ownership Ambiguity
In a franchise model, who owns customer data — franchisor or franchisee? When a franchisee leaves the network, what happens to their customer history? Indian data protection (DPDP Act 2023) adds complexity. Agreement clauses need platform enforcement.

### 5. Hybrid Network Complexity
Many Indian travel agencies operate a hybrid model: some corporate branches, some franchises, some consortium partners. The platform must support all models simultaneously with different governance, commission, and compliance rules per node type. Avoiding a "config explosion" is a real architectural challenge.

---

## Next Steps

1. **Map existing Indian franchise networks** — Study Cox & Kings (pre-collapse), Thomas Cook, SOTC, MakeMyTrip offline store models for concrete patterns
2. **Design multi-entity financial model** — Extend the existing `FinanceProfitability` types to support inter-entity accounting, royalty calculations, and consolidated reporting
3. **Prototype territory engine** — Build a pin-code-based territory assignment service with overlap detection and digital referral tracking
4. **Research DPDP Act implications** — Specifically for multi-entity customer data, consent management across franchise network, and data portability when franchisees exit
5. **Interview franchise operators** — Talk to 3-5 franchise owners/managers in Indian travel to validate assumptions on royalty structures, pain points, and governance expectations
6. **Draft agreement template engine** — Design a document generation module for franchise agreements with variable terms, territory schedules, and fee structures

---

**Series:** Agency Network & Franchise Management
**Document:** 1 of 5 (Network Models)
**Last Updated:** 2026-04-28
**Status:** Research Exploration
