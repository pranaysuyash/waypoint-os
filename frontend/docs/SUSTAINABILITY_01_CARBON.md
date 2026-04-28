# Sustainability & Green Travel — Carbon Footprint Tracking

> Research document for carbon emission calculation, offset integration, and environmental impact measurement.

---

## Key Questions

1. **How do we calculate carbon emissions for each trip component?**
2. **What carbon offset programs can we integrate with?**
3. **How do we present carbon impact to customers and agents?**
4. **What reporting is needed for corporate sustainability requirements?**
5. **How do we compare carbon footprints across trip alternatives?**

---

## Research Areas

### Carbon Calculation Model

```typescript
interface CarbonFootprint {
  tripId: string;
  totalEmissions: EmissionBreakdown;
  components: ComponentEmission[];
  offsets: CarbonOffset[];
  netEmissions: EmissionValue;
  comparisonToAverage: number;        // % vs average trip
  comparisonToSustainable: number;    // % vs green alternative
}

interface EmissionBreakdown {
  flights: EmissionValue;             // Usually 60-80% of total
  accommodation: EmissionValue;
  groundTransport: EmissionValue;
  activities: EmissionValue;
  food: EmissionValue;                // Estimated based on destination
  total: EmissionValue;
}

interface EmissionValue {
  kgCO2e: number;                     // Kilograms CO2 equivalent
  source: EmissionSource;
  confidence: 'measured' | 'calculated' | 'estimated';
  methodology: string;                // e.g., "DEFRA 2024", "ICAO Carbon Calculator"
}

// Flight emission calculation:
// Based on: ICAO Carbon Emissions Calculator methodology
// Factors: Distance, aircraft type, cabin class, load factor, RFI
//
// Short-haul (<1500km): ~0.255 kg CO2e per passenger-km (economy)
// Medium-haul (1500-4000km): ~0.187 kg CO2e per passenger-km (economy)
// Long-haul (>4000km): ~0.151 kg CO2e per passenger-km (economy)
// Business class multiplier: 1.5-3.0x (more space = more emissions)
// Radiative Forcing Index (RFI): 1.9x for high-altitude emissions
//
// Delhi → Mumbai (economy, 1,140km): ~290 kg CO2e
// Delhi → London (economy, 6,700km): ~1,010 kg CO2e
// Delhi → Singapore (business, 4,150km): ~1,680 kg CO2e

// Hotel emission estimation:
// Based on: Cornell Hotel Sustainability Benchmarking
// Factors: Location, star rating, length of stay, hotel type
//
// Budget hotel: ~10.6 kg CO2e per room-night (India average)
// Mid-range hotel: ~20.1 kg CO2e per room-night
// Luxury hotel: ~40.5 kg CO2e per room-night
// Eco-certified hotel: ~30% less than category average
//
// 5 nights luxury in Bali: ~202 kg CO2e
// 5 nights eco-resort in Bali: ~141 kg CO2e

// Ground transport estimation:
// Taxi/Cab: ~0.18 kg CO2e per km (India average)
// Private car: ~0.21 kg CO2e per km (petrol), 0.15 (diesel)
// Bus: ~0.089 kg CO2e per passenger-km
// Train: ~0.041 kg CO2e per passenger-km (Indian Railways)
// EV taxi: ~0.053 kg CO2e per km
```

### Carbon Offset Integration

```typescript
interface CarbonOffset {
  offsetId: string;
  provider: OffsetProvider;
  project: OffsetProject;
  amount: EmissionValue;
  price: Money;
  certificate?: OffsetCertificate;
  status: 'pending' | 'purchased' | 'retired' | 'expired';
}

interface OffsetProvider {
  name: string;
  certification: OffsetCertification[];
  apiIntegration: boolean;
  markupPercent: number;              // Platform margin on offset
}

type OffsetCertification =
  | 'gold_standard'                   // Gold Standard (WWF-backed)
  | 'VCS'                             // Verified Carbon Standard
  | 'CDM'                             // Clean Development Mechanism (UN)
  | 'plan_vivo';                      // Plan Vivo (community forestry)

interface OffsetProject {
  projectId: string;
  name: string;
  type: OffsetProjectType;
  location: string;
  coBenefits: string[];               // SDG alignment, community benefits
  verificationDate: Date;
  vintage: number;                    // Year of emission reduction
}

type OffsetProjectType =
  | 'reforestation'                   // Tree planting, forest restoration
  | 'renewable_energy'                // Solar, wind, hydro projects
  | 'cookstoves'                      // Clean cooking in developing nations
  | 'methane_capture'                 // Landfill, agricultural methane
  | 'ocean_cleanup'                   // Ocean plastic, blue carbon
  | 'community';                      // Community-based sustainability

// Offset cost estimation:
// Reforestation: $5-15 per tonne CO2e
// Renewable energy: $3-10 per tonne CO2e
// Cookstoves: $8-20 per tonne CO2e
// Gold Standard premium: +20-50% over base cost
//
// Example: Delhi → London round-trip
// Emissions: ~2,020 kg CO2e (economy)
// Offset cost (Gold Standard reforestation): ~$20-30 (~₹1,700-2,500)
// Platform adds to quote as optional line item

// Offset workflow:
// 1. Calculate trip carbon footprint
// 2. Present offset options to customer (optional add-on)
// 3. Customer selects offset project (or auto-select cheapest)
// 4. Offset purchased from provider API
// 5. Certificate generated (PDF, shareable)
// 6. Offset recorded in trip record
// 7. Post-trip: Send impact report to customer
```

### Carbon Comparison Engine

```typescript
interface CarbonComparison {
  tripOption: TripOption;
  emissions: EmissionBreakdown;
  alternatives: CarbonAlternative[];
  recommendation: CarbonRecommendation;
}

interface CarbonAlternative {
  description: string;                // "Take the train instead of flying"
  component: string;                  // Which component to replace
  currentEmissions: EmissionValue;
  alternativeEmissions: EmissionValue;
  savings: EmissionValue;
  savingsPercent: number;
  priceDifference?: Money;            // May be cheaper or more expensive
  feasibilityScore: number;           // 0-1, how practical is this alternative
}

// Comparison examples:
//
// Flight vs Train (Delhi → Mumbai):
//   Flight: 290 kg CO2e, ₹5,500, 2 hours
//   Train: 47 kg CO2e, ₹1,200, 16 hours
//   Savings: 243 kg CO2e (-84%), ₹4,300 cheaper
//   Feasibility: 0.6 (time tradeoff)
//
// Direct vs Connecting Flight (Delhi → London):
//   Connecting (via Dubai): 2,350 kg CO2e (extra takeoff/landing)
//   Direct: 2,020 kg CO2e
//   Savings: 330 kg CO2e (-14%)
//   Feasibility: 0.9 (if direct available)
//
// Hotel Comparison (5 nights in Singapore):
//   Standard hotel: 180 kg CO2e, ₹35,000
//   Green-certified hotel: 126 kg CO2e, ₹38,000
//   Savings: 54 kg CO2e (-30%), ₹3,000 more
//   Feasibility: 0.8
//
// Full trip alternative comparison:
//   Original trip: 3,500 kg CO2e
//   "Greenest option": 1,800 kg CO2e (-49%)
//   Changes: Train instead of domestic flight, eco-hotel, EV transfers

interface CarbonRecommendation {
  level: 'none' | 'minor' | 'moderate' | 'significant';
  suggestion: string;
  impactKgCO2: number;
  priceImpact: Money;
  badge?: SustainabilityBadge;
}

type SustainabilityBadge =
  | 'eco_conscious'                   // <50% of average emissions
  | 'green_choice'                    // <30% of average emissions
  | 'carbon_neutral'                  // Net-zero via offsets
  | 'carbon_negative';               // More offsets than emissions
```

### Corporate Sustainability Reporting

```typescript
interface SustainabilityReport {
  reportId: string;
  organizationId: string;
  period: DateRange;
  summary: SustainabilitySummary;
  breakdown: SustainabilityBreakdown;
  recommendations: string[];
  exportFormats: ('pdf' | 'xlsx' | 'csv')[];
}

interface SustainabilitySummary {
  totalTrips: number;
  totalEmissions: EmissionValue;
  emissionsPerTrip: EmissionValue;
  offsetsPurchased: EmissionValue;
  netEmissions: EmissionValue;
  yearOverYearChange: number;         // % change from previous year
  targetProgress: number;             // % toward corporate sustainability target
}

interface SustainabilityBreakdown {
  byDepartment: DepartmentEmission[];
  byTravelType: TravelTypeEmission[];
  byMonth: MonthlyEmission[];
  topRoutes: RouteEmission[];         // Highest-emission routes
  offsetSummary: OffsetSummary;
}

// Corporate sustainability features:
// - Annual carbon footprint report (for ESG reporting)
// - Department-level emission tracking
// - Sustainability targets with progress tracking
// - "Greenest trip" awards for employees
// - Integration with Scope 3 emission reporting
// - GST/HSA reporting for carbon tax compliance
// - Dashboard showing emissions trend over time
//
// India-specific regulatory context:
// - BRSR (Business Responsibility and Sustainability Reporting) for listed companies
// - SEBI mandates ESG disclosure for top 1,000 listed companies
// - Carbon credit trading scheme (CCTS) — upcoming
// - Energy Conservation (Amendment) Act, 2022 — carbon trading framework
```

---

## Open Problems

1. **Data accuracy** — Emission factors are estimates. Actual emissions vary by aircraft, load factor, weather. Over-claiming accuracy is greenwashing risk.

2. **Scope 3 complexity** — Corporate travel emissions are Scope 3 (indirect). Attribution models vary. Need to align with GHG Protocol standards.

3. **Offset quality** — Not all carbon offsets are equal. Some projects don't deliver real reductions. Need robust verification and vetting.

4. **Customer willingness** — Most Indian travelers don't prioritize carbon footprint yet. Presenting it as optional may lead to low adoption.

5. **Competitive pressure** — Booking.com, Skyscanner show CO2 per flight. Need matching capability without being a compliance burden on agents.

---

## Next Steps

- [ ] Design carbon calculation engine with DEFRA/ICAO methodology
- [ ] Integrate carbon offset providers (Gold Standard, VCS-certified)
- [ ] Build carbon comparison engine for trip alternatives
- [ ] Create corporate sustainability reporting module
- [ ] Study carbon calculators (Google Flights CO2, Skyscanner Greener Choices, ICAO Calculator)
