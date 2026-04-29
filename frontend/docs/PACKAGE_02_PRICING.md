# Travel Package Lifecycle 02: Package Pricing Engine

> Research document for package pricing strategies, GST/TCS compliance, seasonal and occupancy-based pricing, and channel markup management for Indian travel agencies.

---

## Document Overview

**Focus:** How travel packages are priced, taxed, and distributed across channels
**Status:** Research Exploration
**Last Updated:** 2026-04-28

---

## Key Questions

1. **What pricing models work for Indian travel agencies — cost-plus, margin-based, competitive, or dynamic?**
2. **How does seasonal and demand-based pricing apply across multi-destination packages?**
3. **How do we model occupancy-based pricing (single/double/triple/quad) for Indian family travel?**
4. **What are the GST implications on package components (5% standalone vs. 18% bundled)?**
5. **What are TCS implications on overseas packages under Section 206C(1G)?**
6. **How do we manage markups across distribution channels (B2B, B2C, OTA, franchise)?**
7. **How do early bird and last-minute pricing strategies affect booking patterns?**
8. **What India-specific taxes apply — state tourism cess, pilgrimage levies, adventure activity taxes?**

---

## Research Areas

### A. Pricing Strategy Models

```typescript
// Research-level model — not final

type PricingStrategy =
  | 'cost_plus'             // Cost + fixed markup percentage
  | 'margin_target'         // Target margin %, adjust selling price
  | 'competitive'           // Match/beat competitor pricing
  | 'dynamic';              // Demand-based, real-time adjustment

interface PackagePricingEngine {
  packageId: string;
  variantId?: string;

  // Pricing strategy
  strategy: PricingStrategy;

  // Cost components
  costBreakdown: PackageCostBreakdown;

  // Markup configuration
  markup: MarkupConfig;

  // Resulting price
  calculatedPrice: CalculatedPrice;

  // Tax configuration
  taxConfig: PackageTaxConfig;
}

interface PackageCostBreakdown {
  // Direct costs (what the agency pays suppliers)
  accommodation: CostLineItem[];
  transport: CostLineItem[];              // Flights, transfers, coach
  activities: CostLineItem[];
  meals: CostLineItem[];
  guides: CostLineItem[];
  entranceFees: CostLineItem[];
  insurance: CostLineItem[];
  miscellaneous: CostLineItem[];          // SIM cards, welcome kits

  // Indirect costs (allocated per booking)
  tourLeaderCost?: CostLineItem;          // For group tours
  coordinationCost?: CostLineItem;        // Operations team
  communicationCost?: CostLineItem;       // Pre-departure calls, WhatsApp

  // Total
  totalDirectCost: Money;
  totalIndirectCost: Money;
  totalCost: Money;
}

interface CostLineItem {
  description: string;
  supplierId?: string;
  unitCost: Money;
  quantity: number;                       // Nights, transfers, pax
  totalCost: Money;
  currency: string;
  markupEligible: boolean;                // Can agency apply markup?
}

// COST-PLUS PRICING:
// Selling Price = Total Cost × (1 + Markup%)
//
// Example: Kerala Backwaters (per person, double occupancy)
//   Accommodation:  ₹15,000 (5 nights @ ₹6,000/night ÷ 2 pax)
//   Transport:      ₹4,000  (AC sedan, shared)
//   Activities:     ₹5,500  (3 activities)
//   Meals:          ₹3,000  (5 breakfasts + 2 dinners)
//   Guide:          ₹2,500  (3 days, shared)
//   Coordination:   ₹1,000
//   ────────────────────────
//   Total Cost:     ₹31,000
//   Markup (35%):   ₹10,850
//   ────────────────────────
//   Selling Price:  ₹41,850 → rounded to ₹42,000
//   GST (5%):       ₹2,100
//   ────────────────────────
//   Customer pays:  ₹44,100

// MARGIN-TARGET PRICING:
// Selling Price = Total Cost ÷ (1 - Target Margin%)
//
// Example: Same Kerala package with 25% target margin
//   Total Cost:     ₹31,000
//   Target Margin:  25%
//   Selling Price:  ₹31,000 ÷ 0.75 = ₹41,333 → ₹41,500
//   Actual Margin:  ₹10,500 (25.3%)

// COMPETITIVE PRICING:
// Agent checks competitor prices and positions accordingly
//   Competitor A: ₹45,000 (similar itinerary)
//   Competitor B: ₹39,000 (lower tier hotels)
//   Our position: ₹42,000 (match quality, beat price)

// DYNAMIC PRICING:
// Price adjusts based on demand, time to departure, availability
//   Base price:     ₹42,000
//   Demand factor:  1.1 (high demand period)
//   Time factor:    0.95 (30+ days to departure, early incentive)
//   Availability:   0.9 (< 5 seats, urgency discount expired)
//   ────────────────────────
//   Dynamic price:  ₹42,000 × 1.1 × 0.95 = ₹43,890 → ₹44,000
```

### B. Markup Configuration

```typescript
interface MarkupConfig {
  // Default markup rules
  defaultMarkupType: 'percentage' | 'fixed';
  defaultMarkupValue: number;            // 35% or ₹5,000

  // Category-specific markups (override default)
  categoryMarkups: CategoryMarkup[];

  // Channel-specific markups
  channelMarkups: ChannelMarkup[];

  // Seasonal adjustments
  seasonalAdjustments: SeasonalMarkupAdjustment[];

  // Volume discounts (reduce markup for large groups)
  volumeDiscounts: VolumeDiscount[];
}

interface CategoryMarkup {
  category: PackageCategory;
  markupType: 'percentage' | 'fixed';
  value: number;
  rationale: string;                     // "Honeymoon clients less price-sensitive"
}

// Typical Indian agency markups by category:
//
// | Category          | Typical Markup | Notes                         |
// |-------------------|---------------|-------------------------------|
// | Domestic group    | 20-30%        | Competitive, volume-driven    |
// | Honeymoon         | 30-40%        | Premium, customization value  |
// | Pilgrimage        | 15-25%        | Price-sensitive, volume       |
// | Educational       | 10-20%        | School budgets, competition   |
// | Corporate offsite | 25-35%        | Company budgets, service-led  |
// | International     | 25-40%        | Higher value, complexity      |
// | Adventure         | 30-45%        | Niche, specialized            |
// | Luxury            | 35-50%        | Service premium               |

interface ChannelMarkup {
  channel: DistributionChannel;
  markupAdjustment: number;              // +5% for OTA, -3% for direct B2B
  reason: string;
}

type DistributionChannel =
  | 'direct_b2c'           // Agency's own website / walk-in
  | 'direct_b2b'           // Referral from partner agency
  | 'ota_makemytrip'       // Listed on MakeMyTrip
  | 'ota_yatra'            // Listed on Yatra
  | 'ota_goibibo'          // Listed on Goibibo
  | 'franchise'            // Sold through franchise outlet
  | 'whatsapp'             // Direct WhatsApp booking
  | 'phone'                // Phone booking
  | 'storefront';          // Agency's physical storefront

// Channel markup example:
// Base selling price: ₹42,000
//
// | Channel        | Adjustment | Final Price | Notes                    |
// |----------------|-----------|-------------|--------------------------|
// | Direct B2C     | +0%       | ₹42,000     | Standard price           |
// | Direct B2B     | -3%       | ₹40,740     | Partner discount         |
// | MakeMyTrip     | +8%       | ₹45,360     | OTA commission ~10-15%   |
// | Franchise      | -5%       | ₹39,900     | Franchise margin sharing |
// | WhatsApp       | +0%       | ₹42,000     | Same as direct           |
// | Storefront     | +0%       | ₹42,000     | In-person, same price    |

interface VolumeDiscount {
  minPax: number;                        // Group size threshold
  maxPax?: number;
  discountPercent: number;               // -5% for 6+ pax
  discountType: 'on_markup' | 'on_total';
}

// Volume discount example:
// 2 pax:  ₹42,000/person
// 4 pax:  ₹42,000/person (no discount)
// 6 pax:  ₹39,900/person (-5% on markup)
// 10 pax: ₹37,800/person (-10% on markup)
// 20+ pax: ₹35,700/person (-15% on markup, custom quote)
```

### C. Seasonal & Demand-Based Pricing

```typescript
interface SeasonalPricing {
  packageId: string;
  variantId?: string;
  basePrice: Money;                      // Shoulder season reference price
  seasonalTiers: SeasonalPriceTier[];
  demandPricing?: DemandPricingConfig;
}

interface SeasonalPriceTier {
  tierName: string;                      // "Peak Winter", "Monsoon Deal"
  season: Season;
  validFrom: Date;
  validTo: Date;

  // Price adjustment from base
  adjustmentType: 'multiplier' | 'fixed';
  adjustmentValue: number;               // 1.3 = +30%, or ₹5,000 surcharge

  // Booking conditions
  minAdvanceBookingDays?: number;
  maxAdvanceBookingDays?: number;

  // Special conditions
  blackoutDates?: Date[];
  minimumStay?: number;                  // Nights
  dayOfWeekSurcharge?: DayOfWeekSurcharge;
}

interface DayOfWeekSurcharge {
  // Weekend surcharges common at resort destinations
  friday: number;                        // +10%
  saturday: number;                      // +15%
  sunday: number;                        // +5%
}

// Seasonal pricing example — Kerala Backwaters Deluxe:
//
// | Season         | Dates              | Multiplier | Price/person |
// |----------------|--------------------| -----------|-------------|
// | Peak Winter    | Dec 15 - Jan 15    | 1.35       | ₹56,700     |
// | Festive (Xmas) | Dec 23 - Jan 2     | 1.50       | ₹63,000     |
// | Shoulder       | Oct - Nov, Feb-Mar | 1.00       | ₹42,000     |
// | Summer         | Apr - Jun          | 0.85       | ₹35,700     |
// | Monsoon        | Jul - Sep          | 0.75       | ₹31,500     |
// | Diwali         | Diwali week        | 1.25       | ₹52,500     |

interface DemandPricingConfig {
  enabled: boolean;
  algorithm: 'linear' | 'stepped' | 'ml_based';

  // Demand signals
  signals: DemandSignal[];

  // Price bounds
  maxMultiplier: number;                 // Never exceed 2x base
  minMultiplier: number;                 // Never go below 0.7x base
}

interface DemandSignal {
  signal: 'seats_remaining' | 'days_to_departure' | 'inquiry_volume' | 'competitor_price';
  weight: number;                        // Importance 0-1
  thresholds: DemandThreshold[];
}

interface DemandThreshold {
  when: string;                          // "seats_remaining < 5"
  adjustment: number;                    // +5%
}
```

### D. Occupancy-Based Pricing

```typescript
// Indian travel is heavily family/group-oriented
// Same room shared by different numbers of people

interface OccupancyPricing {
  packageId: string;
  variantId?: string;
  baseOccupancy: 'double';               // Reference: 2 adults sharing

  // Per-person pricing by occupancy
  occupancyRates: OccupancyRate[];

  // Child pricing
  childPolicy: ChildPricingPolicy;

  // Extra bed / rollaway
  extraBedPolicy?: ExtraBedPolicy;
}

interface OccupancyRate {
  occupancy: RoomOccupancy;
  perPersonPrice: Money;
  supplementOrDiscount: Money;           // vs. double occupancy base
  label: string;                         // "Save ₹4,200/person (triple share)"
  available: boolean;
}

type RoomOccupancy =
  | 'single'              // 1 adult in a room
  | 'double'              // 2 adults in a room
  | 'triple'              // 3 adults in a room (extra bed)
  | 'quad';               // 4 in a room (2 extra beds)

// Occupancy pricing example — Kerala Backwaters (per night per person):
//
// | Occupancy | Room Rate  | Per Person  | vs. Double  | Notes              |
// |-----------|-----------|-------------|-------------|--------------------|
// | Single    | ₹6,000    | ₹6,000      | +₹3,000     | Full room cost     |
// | Double    | ₹6,000    | ₹3,000      | Base        | Standard rate      |
// | Triple    | ₹7,500    | ₹2,500      | -₹500       | Extra bed added    |
// | Quad      | ₹9,000    | ₹2,250      | -₹750       | Two extra beds     |
//
// Family scenario (2 adults + 2 children):
//   Room rate:    ₹7,500 (triple) + child bed ₹1,000 = ₹8,500
//   Adult share:  ₹3,500/adult
//   Child share:  ₹750/child (with child discount)
//   Total room:   ₹8,500/night

interface ChildPricingPolicy {
  // Age-based pricing (standard in Indian hospitality)
  ageBrackets: ChildAgeBracket[];

  // Maximum children per room
  maxChildrenPerRoom: number;

  // Child bed policy
  childBedPolicy: 'existing_bedding' | 'extra_bed' | 'crib' | 'mattress';
}

interface ChildAgeBracket {
  ageRange: string;                      // "0-2", "3-5", "6-11", "12+"
  priceType: 'free' | 'fixed' | 'percentage';
  value: number;                         // 0, ₹2,000, or 50%
  includesMeals: boolean;
  includesActivities: boolean;
  bedRequired: boolean;
}

// Common Indian hotel child pricing:
//
// | Age     | Accommodation     | Meals        | Activities   |
// |---------|-------------------|--------------|--------------|
// | 0-2     | Free (no bed)     | Free         | Free         |
// | 3-5     | Free (no bed)     | 50% of adult | 50% of adult |
// | 6-11    | Extra bed charge  | 75% of adult | 75% of adult |
// | 12+     | Full adult rate   | Full adult   | Full adult   |

interface ExtraBedPolicy {
  available: boolean;
  costPerNight: Money;
  maxExtraBedsPerRoom: number;           // Usually 2
  beddingType: 'rollaway' | 'sofa_bed' | 'mattress' | 'folding_bed';
}
```

### E. Early Bird & Last-Minute Pricing

```typescript
interface EarlyBirdPricing {
  packageId: string;
  tiers: EarlyBirdTier[];

  // Early bird conditions
  minAdvanceDays: number;                // Must book 60+ days ahead
  nonRefundableDeposit: boolean;         // Often non-refundable
  combinableWithOffers: boolean;         // Can stack with seasonal discounts?
}

interface EarlyBirdTier {
  name: string;                          // "Super Early Bird", "Early Bird"
  minDaysBeforeTravel: number;           // 90, 60, 45
  discountPercent: number;               // 15%, 10%, 5%
  maxSeatsAtThisPrice: number;           // Limited inventory at this price
  seatsRemaining: number;
}

// Early bird pricing example:
//
// | Tier              | Book By       | Discount | Max Seats | Status  |
// |-------------------|---------------|----------|-----------|---------|
// | Super Early Bird  | 90+ days      | 15% off  | 5         | 2 left  |
// | Early Bird        | 60-89 days    | 10% off  | 8         | 5 left  |
// | Standard          | 30-59 days    | 0%       | --        | Open    |
// | Last Minute       | < 30 days     | +5-10%   | --        | Open    |

interface LastMinutePricing {
  packageId: string;
  strategy: LastMinuteStrategy;
  config: LastMinuteConfig;
}

type LastMinuteStrategy =
  | 'discount'             // Reduce price to fill seats
  | 'premium'              // Increase price (high demand, limited seats)
  | 'dynamic';             // Algorithm decides based on demand

interface LastMinuteConfig {
  // When to activate
  activateDaysBefore: number;            // 14 days before departure

  // Pricing rules
  minPriceFloor: Money;                  // Never sell below cost
  maxDiscountPercent: number;            // Cap at 25% discount

  // Urgency indicators
  showSeatsRemaining: boolean;           // "Only 3 seats left!"
  showBookingCount?: boolean;            // "17 people booked this week"

  // Notification
  notifyWaitlist?: boolean;              // Alert waitlisted customers
  notifyPastCustomers?: boolean;         // Offer to repeat travelers
}

// Last-minute pricing flow:
//
// 30 days before departure:
//   - Normal pricing applies
//   - 5 seats remaining out of 20
//
// 14 days before departure:
//   - 3 seats remaining
//   - Last-minute pricing activates
//   - If demand high: +5% (scarcity premium)
//   - If demand low: -10% (fill the seats)
//
// 7 days before departure:
//   - 1 seat remaining
//   - Dynamic: may increase or decrease
//   - Urgency messaging: "Last seat available!"
//
// 3 days before departure:
//   - Must sell at any price above cost
//   - Fire sale: up to 25% off
//   - Notify waitlist first
```

### F. GST on Package Components

```typescript
// India GST on tour packages — critical compliance area
// Rates vary based on how the package is structured

interface PackageTaxConfig {
  packageId: string;

  // Tax classification
  taxClassification: PackageTaxClassification;

  // Component-level GST
  componentGST: ComponentGSTConfig[];

  // Package-level GST (if bundled)
  bundledGST?: BundledGSTConfig;

  // State-specific taxes
  stateTaxes: StateTaxConfig[];

  // TCS (Tax Collected at Source) for overseas packages
  tcsConfig?: TCSConfig;
}

interface PackageTaxClassification {
  // GST rate depends on how the service is billed
  classification: TaxClassificationType;
  rationale: string;
  effectiveGSTRate: number;              // 5% or 18%
}

type TaxClassificationType =
  | 'standalone_accommodation'           // 5% GST (no ITC)
  | 'standalone_transport'               // 5% GST (with ITC on GT, 18% on air)
  | 'standalone_activity'                // 18% GST
  | 'bundled_tour_package'               // 5% GST if accommodation is primary component
  | 'bundled_mixed';                     // 18% GST if non-accommodation dominant

// KEY GST RULES FOR TOUR PACKAGES:
//
// 1. ACCOMMODATION-CENTRIC BUNDLES (5% GST):
//    - Package includes hotel + breakfast + local transport
//    - Accommodation is the "dominant" component (>50% of value)
//    - No input tax credit (ITC) available to the agency
//    - Example: Kerala tour with hotel, breakfast, transfers
//
//    Base price:    ₹42,000
//    GST @ 5%:      ₹2,100
//    Total:         ₹44,100
//
// 2. ACTIVITY/SERVICE-CENTRIC BUNDLES (18% GST):
//    - Package is primarily experiences/activities
//    - Accommodation is incidental
//    - ITC may be available
//    - Example: Adventure camping, trekking expedition
//
//    Base price:    ₹35,000
//    GST @ 18%:     ₹6,300
//    Total:         ₹41,300
//
// 3. COMPONENT-WISE BILLING:
//    - Agency bills each component separately
//    - Each component attracts its own GST rate
//    - More transparent but more complex invoicing
//
//    Hotel (5%):    ₹15,000 + ₹750  = ₹15,750
//    Transport (5%): ₹8,000  + ₹400  = ₹8,400
//    Activities (18%):₹12,000 + ₹2,160= ₹14,160
//    Meals (5%):     ₹5,000  + ₹250  = ₹5,250
//    ──────────────────────────────────
//    Total:          ₹40,000 + ₹3,560= ₹43,560
//
//    vs. bundled @ 5%: ₹40,000 + ₹2,000 = ₹42,000
//    Bundled saves customer ₹1,560 in this case

interface ComponentGSTConfig {
  componentType: InclusionCategory;
  gstRate: number;                       // 5%, 12%, 18%
  hsnSacCode: string;                    // HSN/SAC code for invoicing
  itcAvailable: boolean;                 // Input tax credit
  reverseCharge: boolean;                // Reverse charge mechanism?
}

// HSN/SAC codes relevant to travel packages:
//
// | Service               | SAC Code  | GST Rate | ITC   |
// |-----------------------|-----------|----------|-------|
// | Hotel accommodation   | 996321    | 5%       | No    |
// | Tour operator service | 998511    | 5%       | No    |
// | Air travel            | 9964      | 5%       | Yes   |
// | Rail travel           | 9964      | 5%       | Yes   |
// | Road transport        | 9966      | 5%       | Yes   |
// | Restaurant/meals      | 9963      | 5%       | No    |
// | Adventure activities  | 9985      | 18%      | Yes   |
// | Guide services        | 9985      | 18%      | Yes   |
// | Travel insurance      | 9971      | 18%      | Yes   |

interface BundledGSTConfig {
  // When package is sold as a bundle
  bundleTreatment: 'dominant_component' | 'component_wise' | 'flat_rate';
  dominantComponent: InclusionCategory;
  dominantThreshold: number;             // Must be >50% of total value
  gstRate: number;
}

interface StateTaxConfig {
  stateCode: string;                     // "KL" = Kerala
  taxName: string;                       // "Kerala Tourism Cess"
  rate: number;                          // 1%
  applicability: 'per_night' | 'per_booking' | 'per_person';
  collectionBy: 'agency' | 'hotel';      // Who collects and remits
  includedInPrice: boolean;              // Shown as included or separate line?
}

// State-specific tourism taxes:
//
// | State       | Tax Name                | Rate  | Applies To        |
// |-------------|------------------------|-------|-------------------|
// | Kerala      | Tourism Cess            | 1%    | Hotel stays       |
// | Uttarakhand | Eco/Tourism Cess        | 2%    | All tourism       |
// | Rajasthan   | Tourism Development Fee | 1.5%  | Hotel stays       |
// | Goa         | Goa Tourism Tax         | Variable | Varied          |
// | Himachal    | Green Tax               | Fixed | Per vehicle/entry |
// | J&K         | Tourism Fee             | 2%    | Hotel stays       |
// | Karnataka   | Karnataka Tourism Cess  | 1%    | Hotel > ₹1,000    |
```

### G. TCS on Overseas Packages

```typescript
// Tax Collected at Source (TCS) — Section 206C(1G) of Income Tax Act
// Applicable when selling overseas tour packages

interface TCSConfig {
  applicable: boolean;
  reason: string;                        // "Overseas package: includes international flights"
  threshold: Money;                      // ₹7 lakh per financial year (LRS limit)
  rateBelowThreshold: number;            // 5% (0.5% if PAN/Aadhaar available)
  rateAboveThreshold: number;            // 5% (no change for tour packages)

  // Collection details
  collectedBy: 'travel_agent' | 'airline' | 'remittance_service';
  remittedTo: 'income_tax_department';
  quarterDue: string;                    // Quarterly filing

  // Customer classification
  panAvailable: boolean;                 // PAN reduces rate
  residentialStatus: 'resident_individual' | 'resident_hindu_undivided' | 'non_resident';
  existingRemittanceFY: Money;           // How much already remitted this FY
}

// TCS RULES FOR OVERSEAS TOUR PACKAGES:
//
// Section 206C(1G)(b): TCS on overseas tour packages
//
// | Scenario                          | TCS Rate | Notes                    |
// |-----------------------------------|----------|--------------------------|
// | Overseas package (any amount)     | 5%       | On full package value    |
// | PAN/Aadhaar not available         | 10%      | Penalty rate             |
// | Package below ₹7L + no other LRS  | 5%       | Collected by agent       |
// | Package above ₹7L aggregate LRS   | 5%       | Same rate for tour pkgs  |
//
// IMPORTANT DISTINCTIONS:
// - TCS on overseas TOUR PACKAGES: 5% from first rupee (no ₹7L threshold)
// - TCS on overseas REMITTANCES (LRS): 5% above ₹7L threshold
// - The ₹7L threshold does NOT apply to overseas tour packages
// - This makes overseas packages more expensive and agents must collect TCS
//
// Example: Singapore package ₹1,50,000
//   Package price:    ₹1,50,000
//   GST (5%):          ₹7,500
//   TCS (5%):          ₹7,500
//   ────────────────────────────
//   Customer pays:    ₹1,65,000
//
//   TCS can be claimed as credit against income tax liability
//   Agent must deposit TCS with IT department quarterly
//   Agent must issue TCS certificate (Form 27D) to customer

interface TCSCompliance {
  // Agent responsibilities
  agentTanRequired: boolean;             // TAN mandatory for TCS collection
  quarterlyFiling: boolean;
  certificateIssuance: boolean;          // Form 27D
  customerDeclaration: string[];         // PAN, address, purpose of travel

  // Invoice requirements
  invoiceFormat: 'gst_invoice_with_tcs';
  separateLineItem: boolean;             // TCS shown separately on invoice
  gstinRequired: boolean;
}
```

### H. Calculated Price Result

```typescript
interface CalculatedPrice {
  packageId: string;
  variantId?: string;
  departureId?: string;                  // For fixed-departure

  // Occupancy
  occupancy: RoomOccupancy;
  paxCount: number;
  childCount: number;

  // Price computation
  baseCost: Money;                       // Total direct + indirect costs
  markup: Money;                         // Applied markup
  preTaxPrice: Money;                    // Base + markup

  // Seasonal adjustment
  seasonalAdjustment: SeasonalAdjustmentDetail;

  // Early bird / last minute
  promotionalAdjustment?: PromotionalAdjustment;

  // Occupancy adjustment
  occupancyAdjustment: OccupancyAdjustmentDetail;

  // Volume discount
  volumeDiscount?: VolumeDiscountDetail;

  // Taxes
  gst: TaxBreakdown;
  stateTaxes: TaxBreakdown[];
  tcs?: TaxBreakdown;                    // For overseas packages

  // Final price
  totalPricePerPerson: Money;
  totalPriceForGroup: Money;

  // Price breakdown for display
  displayBreakdown: PriceDisplayBreakdown;

  // Validity
  priceValidUntil: Date;                 // Prices may change
  priceGuaranteedAtBooking: boolean;
}

interface TaxBreakdown {
  taxName: string;                       // "GST", "Kerala Tourism Cess", "TCS"
  rate: number;
  taxableAmount: Money;
  taxAmount: Money;
  hsnSacCode?: string;
  itcAvailable?: boolean;
}

interface PriceDisplayBreakdown {
  // How to show price to customer
  lineItems: PriceLineItem[];
  subtotals: PriceSubtotal[];
  grandTotal: Money;
  finePrint: string[];                   // "GST included", "TCS additional"
}

interface PriceLineItem {
  label: string;                         // "Package cost"
  amount: Money;
  optional: boolean;
  tooltip?: string;                      // Hover explanation
}

// Price display example:
//
// Kerala Backwaters Deluxe (5N/6D)
// ────────────────────────────────
// Package cost (per person, double):  ₹42,000
// Early bird discount (-10%):        -₹4,200
// Seasonal surcharge (Peak +15%):    +₹5,670
// ────────────────────────────────
// Subtotal:                           ₹43,470
// GST @ 5%:                           ₹2,174
// Kerala Tourism Cess @ 1%:          ₹435
// ────────────────────────────────
// Total per person:                   ₹46,079
// Total for 2 adults:                 ₹92,158
//
// Child (6-11 years): ₹21,735
//   (50% of adult rate with extra bed)
```

### I. Multi-Currency Pricing

```typescript
// International packages may need multi-currency pricing

interface MultiCurrencyPricing {
  baseCurrency: 'INR';

  // Forex-pegged components
  forexComponents: ForexPricedComponent[];

  // Exchange rate protection
  rateLockPolicy: RateLockPolicy;

  // Display currencies (for international customers)
  displayCurrencies: string[];
}

interface ForexPricedComponent {
  componentId: string;
  originalCurrency: string;              // "USD", "EUR", "SGD"
  originalAmount: Money;
  exchangeRate: number;
  inrAmount: Money;
  rateSource: string;                    // "RBI reference rate"
  rateDate: Date;
  markupOnForex: number;                 // Additional spread %
}

interface RateLockPolicy {
  lockAtBooking: boolean;                // Lock rate when customer books
  lockDuration: number;                  // Days
  rateFluctuationBuffer: number;         // Absorb ±2% fluctuation
  passThroughAbove: number;              // Pass through if > 2% change
}
```

---

## Open Problems

1. **GST classification ambiguity** — When does a "bundled tour package" shift from 5% to 18% GST? The "dominant component" test is subjective and may be challenged during audit.

2. **TCS on split invoices** — If an overseas package is split into domestic (flights from India) and overseas (land arrangements) invoices, does TCS still apply to the full amount?

3. **Dynamic pricing transparency** — Indian consumers expect stable pricing. How do we implement demand-based pricing without eroding trust? Should we show "demand pricing" as a separate line?

4. **Occupancy pricing for non-standard families** — Indian joint families may book 3-4 rooms with varying occupancy. How do we price a group with 2 adults, 2 children, 2 elderly, and 1 infant across rooms?

5. **Competitive pricing data** — How do we reliably collect competitor pricing for comparison? Is web scraping legal/ethical? Can we partner with a pricing intelligence service?

6. **Seasonal pricing across multi-destination packages** — A "Golden Triangle + Goa" package spans Rajasthan (winter peak) and Goa (winter peak), but a "Hill Stations" package spans Shimla (summer peak) and Ooty (year-round). How do we apply seasonal tiers when destinations have different peaks?

7. **Markup erosion on OTAs** — OTA commissions (10-20%) eat into margins. If the agency sells at ₹42,000 directly but the OTA takes 15%, the net drops to ₹35,700. Do we price higher on OTAs or accept lower margins?

8. **State tax compliance at scale** — Each state has different tourism taxes. For a package spanning 4 states (e.g., Golden Triangle: Delhi-Rajasthan-Agra), which state taxes apply where?

---

## Next Steps

1. **GST ruling research** — Find advance rulings and circulars specifically on tour package GST classification to resolve the 5% vs 18% ambiguity
2. **TCS compliance checklist** — Build a compliance checklist for agents collecting TCS on overseas packages
3. **Pricing engine prototype** — Build a calculator that takes cost inputs, occupancy, season, channel, and produces the final customer-facing price with all taxes
4. **Competitive pricing study** — Collect pricing data for top 20 Indian domestic packages from 3+ OTAs to establish competitive benchmarks
5. **State tax database** — Compile a database of tourism-related taxes for all Indian states and union territories
6. **Markup strategy workshop** — Interview 3-5 Indian travel agency owners about their actual markup strategies and channel pricing
7. **Early bird effectiveness analysis** — Study whether early bird discounts actually shift bookings earlier or just reduce revenue
8. **Cross-reference with Package Catalog** — Validate that pricing model supports all package types defined in PACKAGE_01_CATALOG.md
9. **Cross-reference with Booking Engine** — Ensure pricing integrates with deposit and payment schedule in PACKAGE_03_BOOKING.md

---

**Status:** Research exploration, not implementation
**Last Updated:** 2026-04-28
