# Travel Package Lifecycle 01: Package Catalog System

> Research document for package catalog architecture, data modeling, search/discovery, and India-specific package types.

---

## Document Overview

**Focus:** Package catalog design, data models, and catalog management workflows
**Status:** Research Exploration
**Last Updated:** 2026-04-28

---

## Key Questions

1. **How do we model the three fundamental package types — fixed-departure, customizable, and dynamic packaging — in a unified catalog?**
2. **What data model captures inclusions/exclusions/variants without becoming unmanageable?**
3. **How do seasonal pricing tiers integrate into the catalog vs. the pricing engine?**
4. **What search and comparison UX works best for Indian travelers comparing packages?**
5. **How do we catalog India-specific package types (honeymoon, pilgrimage, educational, corporate offsite)?**
6. **What catalog management workflows do agencies need to create, update, and retire packages?**
7. **How do we handle multi-destination, multi-duration variants of the same base package?**

---

## Research Areas

### A. Package Type Taxonomy

```typescript
// Research-level model — not final

type PackageCatalogType =
  | 'fixed_departure'       // Set dates, set itinerary, guaranteed departure
  | 'customizable'          // Base itinerary with swap/add options
  | 'dynamic_packaging';    // Agent/customer assembles from components

interface PackageCatalogEntry {
  id: string;
  agencyId: string;
  code: string;                          // "KER-DELUXE-2026"
  name: string;                          // "Kerala Backwaters Deluxe"
  slug: string;                          // "kerala-backwaters-deluxe"
  type: PackageCatalogType;

  // Classification
  category: PackageCategory;
  themes: PackageTheme[];
  destinations: PackageDestination[];
  tags: string[];

  // Duration
  durationNights: number;
  durationDays: number;

  // Publishing
  status: CatalogStatus;
  publishedAt?: Date;
  archivedAt?: Date;

  // Variants
  variants: PackageVariant[];

  // Inclusions / Exclusions
  inclusions: Inclusion[];
  exclusions: string[];

  // Itinerary template
  itineraryDays: ItineraryDay[];

  // Media
  heroImage: string;
  gallery: MediaAsset[];
  brochure?: DocumentAsset;

  // SEO & Marketing
  metaTitle?: string;
  metaDescription?: string;
  highlights: string[];                  // ["Houseboat stay", "Ayurveda spa"]

  // Lifecycle
  createdAt: Date;
  updatedAt: Date;
  createdBy: string;
  version: number;
}

type CatalogStatus =
  | 'draft'
  | 'review'
  | 'published'
  | 'suspended'
  | 'retired';

type PackageCategory =
  | 'domestic'
  | 'international'
  | 'honeymoon'
  | 'pilgrimage'
  | 'educational'
  | 'corporate_offsite'
  | 'adventure'
  | 'wellness'
  | 'wildlife'
  | 'cultural'
  | 'beach'
  | 'hill_station';

type PackageTheme =
  | 'romantic'
  | 'family'
  | 'senior_citizen'
  | 'solo'
  | 'group'
  | 'luxury'
  | 'budget'
  | 'women_only'
  | 'photography'
  | 'culinary'
  | 'spiritual'
  | 'adventure'
  | 'eco';
```

### B. Fixed-Departure Packages

```typescript
// Fixed-departure: agency sets dates, group travels together
// Most common for group tours, pilgrimage, educational trips

interface FixedDeparturePackage extends PackageCatalogEntry {
  type: 'fixed_departure';

  // Departure schedule
  departures: FixedDeparture[];

  // Group constraints
  minPax: number;                        // Minimum to guarantee departure
  maxPax: number;                        // Coach/vehicle capacity
  guaranteedDeparture: boolean;          // Runs regardless of bookings?

  // Leader
  tourLeaderIncluded: boolean;
  tourLeaderLanguage?: string[];

  // Single supplement mandatory?
  singleSupplementAvailable: boolean;
  singleSupplementPrice?: Money;
}

interface FixedDeparture {
  id: string;
  startDate: Date;
  endDate: Date;
  departureCity: string;                 // "Mumbai", "Delhi"
  availabilityStatus: DepartureAvailability;
  seatsTotal: number;
  seatsBooked: number;
  seatsAvailable: number;
  waitlistCount: number;

  // Pricing override for this departure (seasonal)
  pricingOverride?: DeparturePricing;

  // Status
  isGuaranteed: boolean;                 // Min pax met?
  guaranteedDate?: Date;                 // When it was guaranteed
  cutOffDate: Date;                      // Last booking date
  cancellationDate?: Date;               // When operator might cancel
}

type DepartureAvailability =
  | 'available'         // Seats available
  | 'limited'           // < 5 seats
  | 'waitlist_only'     // Full, waitlist open
  | 'guaranteed'        // Min pax met, confirmed running
  | 'closed'            // Booking closed
  | 'departed'          // Trip in progress or completed
  | 'cancelled';        // Operator cancelled
```

**Fixed-Departure Lifecycle:**

```
  DRAFT ──► PUBLISHED ──► BOOKING_OPEN ──► GUARANTEED ──► DEPARTED ──► COMPLETED
                │              │                │              │
                │              │                │              └──► ARCHIVED
                │              │                └──► CANCELLED
                │              └──► CLOSING_SOON
                └──► SUSPENDED
```

### C. Customizable Packages

```typescript
// Customizable: base itinerary with swap/add/substitute options
// Common for honeymoon, family, FIT packages

interface CustomizablePackage extends PackageCatalogEntry {
  type: 'customizable';

  // Base itinerary (what's included by default)
  baseItinerary: ItineraryDay[];

  // Customization slots
  customizationSlots: CustomizationSlot[];

  // Valid date ranges (not fixed dates)
  validFrom: Date;
  validTo: Date;
  blackoutDates?: Date[];

  // Occupancy-based pricing
  occupancyPricing: OccupancyPricing[];
}

interface CustomizationSlot {
  id: string;
  dayNumber: number;                     // Which itinerary day
  slotType: CustomizationSlotType;
  label: string;                         // "Choose your hotel"
  required: boolean;
  defaultOption: string;                 // Option ID

  options: CustomizationOption[];
}

type CustomizationSlotType =
  | 'accommodation_upgrade'              // Standard → Deluxe → Luxury
  | 'activity_swap'                      // Replace included activity
  | 'activity_addon'                     // Add extra activity
  | 'meal_upgrade'                       // Breakfast → HB → FB
  | 'transport_upgrade'                  // Sedan → SUV → Tempo Traveller
  | 'guide_upgrade'                      // No guide → Shared → Private
  | 'insurance_addon';                   // Add travel insurance

interface CustomizationOption {
  id: string;
  name: string;
  description: string;
  priceModifier: PriceModifier;          // How this affects price
  includes?: string[];                   // What this option adds
  excludes?: string[];                   // What this option removes
  media?: MediaAsset[];
}

type PriceModifier =
  | { type: 'fixed'; amount: Money }
  | { type: 'percentage'; percent: number }
  | { type: 'replace'; newPrice: Money }
  | { type: 'per_night'; perNight: Money }
  | { type: 'per_person'; perPerson: Money };

interface OccupancyPricing {
  occupancy: 'single' | 'double' | 'triple' | 'quad';
  basePrice: Money;                      // Per person
  supplement?: Money;                    // Extra over double
}
```

**Customization UI Sketch:**

```
+-------------------------------------------------------------------+
|  Kerala Backwaters Deluxe — Customize Your Trip                    |
+-------------------------------------------------------------------+
|                                                                    |
|  Day 1-2: Kochi                                                    |
|  +-------------------------------------------------------------+  |
|  | Accommodation:  [Standard ★★★]  [Deluxe ★★★★]  [Luxury ★] |  |
|  |                 -- included --   +₹3,500/nt     +₹8,200/nt |  |
|  +-------------------------------------------------------------+  |
|  | Activity:  [City Tour ●]  [Spice Market Walk]  [Both +₹1K] |  |
|  +-------------------------------------------------------------+  |
|                                                                    |
|  Day 3-4: Munnar                                                   |
|  +-------------------------------------------------------------+  |
|  | Accommodation:  [Standard ●]  [Deluxe +₹2,800/nt]          |  |
|  +-------------------------------------------------------------+  |
|  | Activity Add-on:                                             |  |
|  | [✓] Tea plantation visit (included)                          |  |
|  | [ ] Jeep safari to Eravikulam          +₹1,800/person       |  |
|  | [ ] Kathakali performance              +₹1,200/person       |  |
|  +-------------------------------------------------------------+  |
|                                                                    |
|  Day 5-6: Houseboat (Alleppey)                                     |
|  +-------------------------------------------------------------+  |
|  | Houseboat:  [Deluxe ●]  [Premium +₹4,000]  [Luxury +₹9K]  |  |
|  +-------------------------------------------------------------+  |
|                                                                    |
|  ─────────────────────────────────────────────────────────────────  |
|  Base Price:     ₹42,000/person (double occupancy)                 |
|  Customization:  +₹7,000                                           |
|  GST (5%):       +₹2,450                                           |
|  ─────────────────────────────────────────────────────────────────  |
|  Total:          ₹51,450/person                                    |
|                                                                    |
|  [Save Quote]  [Book Now]                                          |
+-------------------------------------------------------------------+
```

### D. Dynamic Packaging

```typescript
// Dynamic: assemble from individual components
// Agent or customer picks flights + hotels + activities + transfers

interface DynamicPackage extends PackageCatalogEntry {
  type: 'dynamic_packaging';

  // Template rules (what components are required)
  requiredComponents: ComponentRequirement[];
  optionalComponents: ComponentRequirement[];

  // Pricing rules
  bundlingRules: BundlingRule[];

  // No fixed itinerary — generated from selected components
  templateItinerary?: ItineraryDay[];   // Suggested starting point
}

interface ComponentRequirement {
  componentType: 'flight' | 'accommodation' | 'activity' | 'transfer' | 'meal' | 'guide' | 'insurance';
  required: boolean;
  minCount: number;
  maxCount?: number;
  dateBinding?: 'fixed' | 'flexible' | 'range';

  // Supplier filters
  preferredSuppliers?: string[];
  excludedSuppliers?: string[];
  minRating?: number;
}

interface BundlingRule {
  id: string;
  name: string;                          // "Early Bird 10% off 3+ components"
  condition: BundlingCondition;
  discount: DiscountStructure;
}

type BundlingCondition =
  | { type: 'min_components'; count: number }
  | { type: 'early_booking'; daysBeforeTravel: number }
  | { type: 'destination_combo'; destinations: string[] }
  | { type: 'seasonal'; season: Season }
  | { type: 'loyalty_tier'; tier: string };
```

### E. Inclusions & Exclusions Model

```typescript
// Structured inclusions/exclusions that can be compared across packages

interface Inclusion {
  id: string;
  category: InclusionCategory;
  title: string;                         // "Airport transfers"
  description: string;                   // "Private AC sedan, both ways"
  quantity?: string;                     // "2 transfers", "5 breakfasts"
  tier?: string;                         // "Deluxe" hotel tier
  estimatedValue?: Money;                // For showing "worth ₹X"
  isHighlight: boolean;                  // Show prominently?
}

type InclusionCategory =
  | 'flights'              // Air travel
  | 'accommodation'        // Hotels, resorts, houseboats
  | 'transfers'            // Airport, inter-city, local
  | 'meals'                // Breakfast, lunch, dinner, snacks
  | 'activities'           // Sightseeing, adventures, experiences
  | 'guide'                // Tour guide, local expert
  | 'entrance_fees'        // Monuments, parks, attractions
  | 'insurance'            // Travel insurance
  | 'visa_assistance'      // Visa processing help
  | 'sim_card'             // Local SIM or int'l roaming
  | 'special_services'     // Welcome drinks, fruit basket, cake
  | 'equipment'            // Trekking gear, snorkeling, etc.
  | 'support';             // 24x7 helpline, on-tour coordinator

// Exclusions are simpler — just categorized text
interface Exclusion {
  category: InclusionCategory;
  text: string;                          // "International flights"
  optionalAddOn?: {
    available: boolean;
    price?: Money;
  };
}

// Package comparison uses InclusionCategory to align items
interface PackageComparison {
  packageIds: string[];
  alignedCategories: InclusionCategory[];
  matrix: Record<InclusionCategory, Record<string, Inclusion | null>>;
}
```

### F. Package Variants

```typescript
// Same base package with variations
// e.g., "Kerala Backwaters" has Budget/Standard/Deluxe/Luxury variants

interface PackageVariant {
  id: string;
  packageId: string;
  variantName: string;                   // "Deluxe", "Premium", "Luxury"
  tier: ServiceTier;

  // What changes between variants
  accommodationTier: string;             // "3-star", "4-star", "5-star"
  mealPlan: MealPlan;
  transportType: string;                 // "AC Sedan", "Innova", "Tempo Traveller"
  guideType: 'none' | 'shared' | 'private' | 'specialist';

  // Pricing
  priceDifferenceFromBase: Money;        // +₹5,000 over base

  // What's extra compared to base
  additionalInclusions: Inclusion[];
}

type ServiceTier = 'budget' | 'standard' | 'deluxe' | 'premium' | 'luxury';

type MealPlan =
  | 'room_only'
  | 'breakfast'
  | 'half_board'          // Breakfast + dinner
  | 'full_board'          // All three meals
  | 'all_inclusive';      // Meals + drinks + activities
```

### G. Seasonal Pricing Tiers

```typescript
// Seasonal pricing applied at catalog level (overrides by pricing engine)

interface SeasonalTier {
  id: string;
  packageId: string;
  name: string;                          // "Peak Winter", "Monsoon Value"
  season: Season;
  validFrom: Date;
  validTo: Date;
  priceMultiplier: number;               // 1.0 = base, 1.3 = +30%, 0.8 = -20%
  fixedAdjustment?: Money;               // Alternative: fixed amount change
  blackoutDates?: Date[];
  minBookingDays?: number;               // "Must book 7+ days in peak"
}

type Season =
  | 'peak_winter'         // Dec-Jan: Goa, Kerala, Rajasthan
  | 'summer'              // Apr-Jun: Hill stations, Ladakh
  | 'monsoon'             // Jul-Sep: Off-season deals, Kerala Ayurveda
  | 'shoulder'            // Feb-Mar, Oct-Nov: Moderate pricing
  | 'festive';            // Diwali, Holi, Christmas, New Year

// India-specific seasonal patterns:
//
// PEAK SEASON (October → March):
// - Rajasthan, Goa, Kerala, Tamil Nadu
// - Premium pricing (+20-40% over base)
// - Early booking recommended
// - Diwali, Christmas, New Year surcharges
//
// SHOULDER (February → March, October):
// - Moderate pricing
// - Best value window
// - Pleasant weather across most destinations
//
// SUMMER (April → June):
// - Hill stations peak (Shimla, Manali, Darjeeling, Ooty)
// - Ladakh season opens
// - Plains and south India off-season
// - School holidays drive family demand
//
// MONSOON (July → September):
// - Off-season for most destinations
// - Kerala Ayurveda packages (monsoon = ideal for treatment)
// - Ladakh still accessible
// - Significant discounts (20-40% off)
// - Some destinations closed (Andaman ferries)

interface FestiveSurcharge {
  festival: string;                      // "Diwali", "Christmas", "Holi"
  surchargeType: 'percentage' | 'fixed';
  value: number;
  applicableDates: DateRange;
  description: string;                   // "Mandatory gala dinner included"
}
```

### H. India-Specific Package Types

```typescript
// HONEYymoon packages
interface HoneymoonPackage extends CustomizablePackage {
  category: 'honeymoon';
  romanticInclusions: RomanticInclusion[];
  roomUpgradeGuaranteed: boolean;
  privacyLevel: 'standard' | 'exclusive' | 'ultra_private';
}

interface RomanticInclusion {
  type: 'candle_dinner' | 'spa_couple' | 'room_decoration' | 'cake' | 'flower_bouquet' | 'sunset_cruise' | 'photography_session';
  included: boolean;
  upgradeAvailable?: Money;
}

// Popular honeymoon destinations (India):
// - Kerala (Alleppey houseboat, Munnar tea gardens)
// - Goa (Beach resorts)
// - Rajasthan (Udaipur palace hotels)
// - Andaman (Havelock beaches)
// - Shimla/Manali (Hill station romance)
// - International: Maldives, Bali, Thailand, Switzerland

// PILGRIMAGE packages
interface PilgrimagePackage extends FixedDeparturePackage {
  category: 'pilgrimage';
  pilgrimageType: PilgrimageType;
  religiousTradition: 'hindu' | 'muslim' | 'sikh' | 'buddhist' | 'jain' | 'christian' | 'multi_faith';
  spiritualGuideIncluded: boolean;
  ritualAssistance: boolean;             // Help with rituals, pujas
  dietaryCompliance: 'strict_vegetarian' | 'sattvic' | 'halal' | 'vegan';
  accessibilityInfo: string;             // Terrain difficulty, elderly-friendly
}

type PilgrimageType =
  | 'char_dham'            // Yamunotri, Gangotri, Kedarnath, Badrinath
  | 'varanasi_prayagraj'   // Kashi Vishwanath, Sangam
  | 'tirupati'             // Balaji darshan
  | 'vaishno_devi'         // Katra trek/helicopter
  | 'rameshwaram'          // Rameshwaram temple
  | 'amarnath'             // Cave yatra (seasonal)
  | 'hajj_umrah'           // Saudi Arabia
  | 'golden_temple'        // Amritsar
  | 'buddhist_circuit'     // Bodh Gaya, Sarnath, Kushinagar
  | 'shirdi'               // Sai Baba temple
  | 'nathdwara'            // Srinathji temple
  | 'jagannath_puri'       // Rath Yatra
  | 'custom_temple_tour';  // Agent-curated

// Pilgrimage-specific considerations:
// - Darshan tickets / VIP darshan arrangements
// - Helicopter services (Vaishno Devi, Amarnath, Kedarnath)
// - Medical fitness certificates (Amarnath, Char Dham)
// - Registration requirements (Amarnath Yatra)
// - Senior citizen accessibility
// - Strict vegetarian/sattvic food
// - Pandit/priest services
// - Special puja booking

// EDUCATIONAL packages
interface EducationalPackage extends FixedDeparturePackage {
  category: 'educational';
  targetAudience: 'school' | 'college' | 'corporate_training';
  learningObjectives: string[];
  educationalComponents: EducationalComponent[];
  teacherRatio: string;                  // "1:15"
  safetyProtocols: string[];
  parentConsentRequired: boolean;
}

interface EducationalComponent {
  type: 'heritage_site' | 'museum' | 'science_center' | 'factory_visit' | 'nature_study' | 'adventure_learning' | 'cultural_immersion' | 'workshop';
  subject?: string;                      // "History", "Science", "Geography"
  duration: string;
  materials?: string;                    // Handouts, worksheets
}

// Popular educational destinations:
// - Delhi-Agra (Mughal history, Parliament visit)
// - Hyderabad (Science museums, Golconda, IT campuses)
// - Bangalore (ISRO, tech parks, science museum)
// - Kerala (Ecology, backwater ecosystems)
// - Rajasthan (Heritage, desert ecology)
// - Space Center visits (ISRO Sriharikota)

// CORPORATE OFFSITE packages
interface CorporateOffsitePackage extends CustomizablePackage {
  category: 'corporate_offsite';
  corporateInclusions: CorporateInclusion[];
  venueCapacity: number;
  avEquipment: AVEquipment[];
  teamBuildingOptions: TeamBuildingActivity[];
  meetingRoomConfigurations: MeetingRoomConfig[];
  mealPlanCustomization: CorporateMealPlan;
}

interface CorporateInclusion {
  type: 'conference_room' | 'projector' | 'whiteboard' | 'video_conferencing' | 'team_building' | 'bonfire' | 'treasure_hunt' | 'trek' | 'treasure_hunt' | 'adventure_sports';
  included: boolean;
  capacity?: number;
}

// Popular corporate offsite destinations:
// - Goa (Beach + conference resorts)
// - Jim Corbett (Nature + team building)
// - Jaipur/Udaipur (Heritage + luxury)
// - Lavasa (Hill station conference center)
// - Matheran (Quiet retreat)
// - Rishikesh (Adventure + yoga)
```

### I. Package Search & Discovery

```typescript
interface PackageSearchRequest {
  // Core filters
  destination?: string;                  // "Kerala", "Goa"
  travelDates?: DateRange;
  duration?: DurationRange;              // "3-5 nights"
  budget?: PriceRange;
  travelers: TravelerComposition;

  // Package-specific
  packageType?: PackageCatalogType[];
  categories?: PackageCategory[];
  themes?: PackageTheme[];

  // Quality filters
  serviceTier?: ServiceTier[];
  minRating?: number;
  mealPlan?: MealPlan[];

  // Departure filters (fixed-departure only)
  departureCity?: string[];
  availabilityStatus?: DepartureAvailability[];

  // Sorting
  sortBy: 'price_low' | 'price_high' | 'rating' | 'popularity' | 'departure_date' | 'duration' | 'relevance';
  sortDirection: 'asc' | 'desc';
}

interface PackageSearchResult {
  packages: PackageSearchHit[];
  facets: PackageSearchFacets;
  pagination: PaginationInfo;
  suggestions?: string[];                // "Try similar packages in..."
}

interface PackageSearchHit {
  packageId: string;
  variantId?: string;
  name: string;
  destination: string;
  duration: string;                      // "5N/6D"
  priceFrom: Money;
  priceLabel: string;                    // "per person, double occupancy"
  highlights: string[];
  heroImage: string;
  rating: number;
  reviewCount: number;
  nextDeparture?: Date;                  // For fixed-departure
  availabilityBadge?: string;            // "3 seats left", "Guaranteed departure"
  category: PackageCategory;
  themes: PackageTheme[];
  matchScore: number;                    // Relevance score
}

interface PackageSearchFacets {
  categories: FacetBucket<PackageCategory>[];
  themes: FacetBucket<PackageTheme>[];
  priceRanges: FacetBucket<string>[];
  durations: FacetBucket<string>[];
  serviceTiers: FacetBucket<ServiceTier>[];
  destinations: FacetBucket<string>[];
  departureCities: FacetBucket<string>[];
}
```

**Search UI Mockup:**

```
+-------------------------------------------------------------------+
| [Packages]  [Destinations]  [Themes]  [Deals]                     |
+-------------------------------------------------------------------+
|                                                                    |
|  +--------------------------------------------------------------+ |
|  | Where do you want to go?  |  Dates  |  Travelers  | [Search] | |
|  +--------------------------------------------------------------+ |
|                                                                    |
|  Filters:                                                          |
|  [x] Kerala   [ ] Goa   [ ] Rajasthan   [x] 3-5 nights           |
|  [x] Honeymoon  [x] Family  [ ] Budget  [ ] Luxury               |
|  Price: ₹15,000 ────────●──────── ₹80,000                         |
|                                                                    |
|  23 packages found, sorted by: [Relevance ▼]                       |
|                                                                    |
|  +--------------------------------------------------------------+ |
|  | [IMG] Kerala Backwaters Deluxe                                | |
|  |        5N/6D  |  Kochi - Munnar - Thekkady - Alleppey         | |
|  |        ★★★★☆ (142 reviews)                                   | |
|  |        Houseboat • Tea Gardens • Spice Plantation              | |
|  |        From ₹42,000/person                                    | |
|  |        Next departure: 15 Dec 2026 (5 seats left)             | |
|  |        [View Details] [Compare] [Quick Quote]                 | |
|  +--------------------------------------------------------------+ |
|  | [IMG] Kerala Romance Escape (Honeymoon)                       | |
|  |        4N/5D  |  Kochi - Munnar - Alleppey                    | |
|  |        ★★★★★ (89 reviews)                                    | |
|  |        Candle Dinner • Couple Spa • Room Decoration            | |
|  |        From ₹58,000/person                                    | |
|  |        Flexible dates (Oct - Mar)                             | |
|  |        [View Details] [Compare] [Quick Quote]                 | |
|  +--------------------------------------------------------------+ |
+-------------------------------------------------------------------+
```

### J. Package Comparison

```typescript
interface PackageComparisonView {
  packages: ComparedPackage[];
  comparisonCategories: ComparisonCategory[];
  verdict?: ComparisonVerdict;
}

interface ComparedPackage {
  packageId: string;
  variantId?: string;
  name: string;
  price: Money;
  priceBreakdown: PriceBreakdown;
  inclusionsByCategory: Record<InclusionCategory, Inclusion[]>;
  exclusions: string[];
  rating: number;
  departureDates?: Date[];
  duration: string;
  accommodationSummary: string;
  mealPlan: MealPlan;
}

type ComparisonCategory =
  | 'overview'            // Name, price, duration, rating
  | 'itinerary'           // Day-by-day comparison
  | 'inclusions'          // What's included side-by-side
  | 'accommodation'       // Hotels by night
  | 'meals'               // Meal plan details
  | 'transport'           // Flight, transfer details
  | 'activities'          // Activities and experiences
  | 'pricing'             // Price breakdown, hidden costs
  | 'terms';              // Cancellation, payment schedule

// Comparison UI allows selecting 2-4 packages and toggling categories
```

**Comparison UI Sketch:**

```
+-------------------------------------------------------------------+
| Compare Packages (3 selected)                                      |
+-------------------------------------------------------------------+
| [Overview] [Itinerary] [Inclusions] [Hotels] [Price] [Terms]       |
+-------------------------------------------------------------------+
|                          │ Kerala    │ Kerala      │ Kerala        |
|                          │ Deluxe    │ Romance     │ Express       |
+-------------------------------------------------------------------+
| Duration                 │ 5N/6D     │ 4N/5D       │ 3N/4D         |
| Price/person            │ ₹42,000   │ ₹58,000     │ ₹28,000       |
| Meal Plan               │ Breakfast │ HB          │ Breakfast     |
| Accommodation           │ 4★ avg    │ 5★          │ 3★ avg        |
| Houseboat               │ Deluxe    │ Premium     │ Standard      |
| Airport Transfer        │ ✓ Private │ ✓ Private   │ ✓ Shared      |
| Guide                   │ ✓ Full    │ ✓ Full      │ ✗             |
| Candle Dinner           │ ✗         │ ✓ Included  │ ✗             |
| Couple Spa              │ ✗         │ ✓ Included  │ ✗ (₹3,500)   |
| Cancellation            │ 30d full  │ 45d full    │ 15d full      |
+-------------------------------------------------------------------+
| GST (5% standalone)     │ ₹2,100    │ ₹2,900      │ ₹1,400        |
| Total incl. GST         │ ₹44,100   │ ₹60,900     │ ₹29,400       |
+-------------------------------------------------------------------+
```

### K. Catalog Management Workflow

```typescript
// Agency workflow for managing the package catalog

type CatalogWorkflowAction =
  | 'create_draft'
  | 'submit_for_review'
  | 'approve'
  | 'reject'
  | 'publish'
  | 'suspend'
  | 'update_pricing'
  | 'update_inclusions'
  | 'add_variant'
  | 'add_departure'
  | 'archive'
  | 'restore';

interface CatalogWorkflowRule {
  action: CatalogWorkflowAction;
  requiredRole: AgencyRole;
  approvalRequired: boolean;
  notifyRoles: AgencyRole[];
  auditLog: boolean;
}

// Typical catalog management flow:
//
// 1. AGENT creates draft package
//    - Fills in package details, itinerary, inclusions
//    - Uploads images, sets base pricing
//    - Saves as draft
//
// 2. SENIOR AGENT or MANAGER reviews
//    - Checks itinerary completeness
//    - Validates pricing (cost vs. selling price)
//    - Confirms supplier contracts
//    - Approves or sends back for revision
//
// 3. MANAGER publishes
//    - Package appears in search results
//    - Bookings can be taken
//    - SEO/metadata goes live
//
// 4. ONGOING maintenance
//    - Update pricing for new season
//    - Add/remove departure dates
//    - Adjust inclusions based on supplier changes
//    - Suspend during quality issues
//
// 5. RETIRE
//    - Package no longer sold
//    - Existing bookings honored
//    - Archived for reference

interface CatalogPermission {
  role: AgencyRole;
  canCreate: boolean;
  canEdit: boolean;                      // Own packages
  canEditAll: boolean;                   // Any package
  canApprove: boolean;
  canPublish: boolean;
  canSuspend: boolean;
  canArchive: boolean;
  canDelete: boolean;                    // Only drafts
  canManagePricing: boolean;
  canManageDepartures: boolean;
}
```

### L. Package Destination Model

```typescript
interface PackageDestination {
  id: string;
  name: string;                          // "Kerala"
  region: string;                        // "South India"
  country: string;                       // "India"
  type: 'domestic' | 'international';

  // Geographic hierarchy
  parentDestinationId?: string;          // "South India" → "Kerala"
  childDestinations?: string[];          // "Kerala" → ["Kochi", "Munnar", "Alleppey"]

  // Travel intelligence
  bestSeasons: Season[];
  peakMonths: number[];                  // [12, 1] = December, January
  languages: string[];
  currency: string;
  timezone: string;

  // India-specific
  nearestAirports: string[];             // ["COK", "TRV"]
  stateCode?: string;                    // "KL" for Kerala
  stateTourismTax?: TaxInfo;
  entryRestrictions?: string[];          // Protected area permits, etc.
}

interface TaxInfo {
  taxName: string;                       // "Kerala Tourism Cess"
  rate: number;                          // 1%
  applicableTo: string[];                // ["hotel_stay", "package"]
  collectionMethod: 'included' | 'separate';
}
```

---

## Open Problems

1. **Variant explosion** — A Kerala package with 4 hotel tiers, 3 meal plans, and 2 transport options creates 24 variants. How do we present this without overwhelming the customer?

2. **Seasonal pricing complexity** — Different seasons affect different components differently (hotels peak in winter, hill stations peak in summer). How does a single seasonal tier apply to multi-destination packages?

3. **Inventory coupling** — Fixed-departure packages tie hotel, transport, and activity inventory together. When one component sells out (coach seats), does the whole departure close?

4. **Comparison fairness** — Packages from different agencies may have different inclusion granularity. How do we normalize "includes breakfast" vs. "includes breakfast at 4-star hotel"?

5. **Pilgrimage package regulation** — Some pilgrimage packages (Char Dham, Amarnath) have government-mandated registration and safety requirements. How do we model regulatory compliance?

6. **Dynamic packaging profitability** — When customers assemble their own packages, how do we ensure the bundled price is profitable vs. individual component margins?

7. **Catalog migration** — Agencies with existing PDF/Excel catalogs need bulk import. How do we structure the import format to capture variants, seasons, and inclusions?

8. **Multi-language catalog** — Domestic pilgrimage packages may need Hindi/regional language descriptions alongside English. How does the catalog support i18n?

---

## Next Steps

1. **Validate data model** — Review the PackageCatalogEntry model with 2-3 Indian travel agencies to confirm it captures their package structures
2. **Study competitor catalogs** — Analyze how MakeMyTrip, SOTC, and Thomas Cook structure their package catalogs and comparison views
3. **Prototype search facets** — Build a mock search with realistic packages to test faceting and filtering behavior
4. **Design variant UX** — Prototype the customization UI to validate that the slot-based model works for agents
5. **Pilgrimage package deep dive** — Research regulatory requirements for Char Dham and Amarnath Yatra packages
6. **Seasonal pricing matrix** — Map out seasonal pricing patterns for top 10 Indian destinations
7. **GST impact modeling** — Document GST applicability on different package types and components (cross-reference PACKAGE_02_PRICING)
8. **Integration with existing series** — Map how Package Catalog connects to Package Tours provider integration (see PACKAGE_TOURS_MASTER_INDEX.md)

---

**Status:** Research exploration, not implementation
**Last Updated:** 2026-04-28
