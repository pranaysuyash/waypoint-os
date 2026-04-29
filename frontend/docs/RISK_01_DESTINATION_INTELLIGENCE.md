# Travel Risk Assessment 01: Destination Intelligence

> Research document for destination risk scoring, real-time advisory integration, and risk classification across political, health, environmental, and security dimensions.

---

## Document Overview

**Focus:** Destination risk scoring and intelligence gathering
**Status:** Research Exploration
**Last Updated:** 2026-04-28

---

## Key Questions

### 1. Risk Dimensions
- How do we score destination risk across political stability, health, natural disasters, crime, and terrorism?
- What is the relative weight of each risk dimension for different traveler profiles?
- How do risk scores change during seasons, elections, or known events?
- What is the minimum viable risk model vs. the ideal comprehensive model?

### 2. Data Sources
- Which government advisories are authoritative and machine-readable? (MEA India, US State Dept, UK FCDO, WHO, IMD)
- How do we handle conflicting risk assessments from different sources?
- What commercial travel intelligence feeds exist and what do they cost?
- How do we ingest real-time weather (IMD), health (WHO/IHR), and security data?

### 3. Risk Classification
- What is the right granularity for risk levels? Is 1-5 sufficient or do we need sub-levels?
- How do we represent risk at country vs. city vs. neighborhood level?
- How do we handle regions where risk varies dramatically within short distances?
- What is the relationship between risk score and insurance premium / travel policy compliance?

### 4. Historical & Seasonal Patterns
- How do we build and maintain a historical incident database for destinations?
- Can we predict seasonal risk patterns (monsoon flooding, dengue season, tourist-targeted crime)?
- How do historical patterns inform forward-looking risk scores?

### 5. Dashboard & UX
- What does a destination risk dashboard look like for agents?
- How do we present risk information without overwhelming or causing unnecessary alarm?
- How do agents use risk information in the sales and trip-planning process?

---

## Research Areas

### A. Risk Dimension Model

```typescript
interface DestinationRiskScore {
  destinationId: string;               // ISO country code + optional city/region
  destinationName: string;
  overallRiskLevel: RiskLevel;         // 1-5 composite
  dimensions: RiskDimension[];
  lastUpdated: Date;
  dataSourceCount: number;
  confidenceScore: number;             // 0-1, how confident are we in the score
  validUntil: Date;                    // Score expiry
}

type RiskLevel = 1 | 2 | 3 | 4 | 5;
// 1 = Minimal Risk   — Normal safety precautions
// 2 = Low Risk        — Exercise normal security awareness
// 3 = Medium Risk     — Exercise increased caution
// 4 = High Risk       — Reconsider travel
// 5 = Critical Risk   — Do not travel

interface RiskDimension {
  type: RiskDimensionType;
  level: RiskLevel;
  trend: 'improving' | 'stable' | 'worsening';
  description: string;
  lastIncidentDate?: Date;
  sources: RiskDataSource[];
  subFactors: RiskSubFactor[];
}

type RiskDimensionType =
  | 'political_stability'    // Government stability, civil unrest, elections
  | 'health'                 // Disease outbreaks, healthcare quality, vaccination needs
  | 'natural_disaster'       // Earthquakes, floods, hurricanes, volcanic activity
  | 'crime'                  // Violent crime, petty crime, tourist-targeted crime
  | 'terrorism'              // Terror threat level, recent attacks, active groups
  | 'infrastructure'         // Road safety, aviation safety, telecom, power
  | 'environmental'          // Air quality, water safety, extreme weather
  | 'regulatory'             // Visa policy changes, entry restrictions, customs
  | 'conflict';              // Active armed conflict, border tensions

interface RiskSubFactor {
  name: string;                        // "Petty theft at tourist sites"
  severity: RiskLevel;
  description: string;
  affectedAreas?: string[];            // Specific neighborhoods or zones
  timePatterns?: TimePattern[];        // When is this risk elevated?
}

interface TimePattern {
  type: 'seasonal' | 'time_of_day' | 'event_based' | 'recurring';
  description: string;                 // "Monsoon season Jun-Sep"
  months?: number[];                   // [6, 7, 8, 9]
  hours?: [number, number];            // [22, 5] = nighttime
}
```

### B. Government Advisory Sources

```typescript
interface AdvisorySource {
  sourceId: string;
  name: string;
  country: string;                     // Issuing country
  coverage: 'global' | 'regional' | 'country';
  format: 'rest_api' | 'rss' | 'web_scraping' | 'csv' | 'email';
  updateFrequency: string;             // "event-driven", "daily", "weekly"
  severityScale: number;               // How many levels in their scale
  reliability: number;                 // 0-1 based on track record
  latency: string;                     // "2-4 hours after event"
  cost: 'free' | 'freemium' | 'paid';
}

// India-specific sources:

// 1. MEA India (Ministry of External Affairs)
//    - Travel advisories for Indian citizens
//    - URL: mea.gov.in/travel-advisories
//    - Format: Website (scraping needed), no public API
//    - Coverage: Country-level, event-driven updates
//    - Special: advisories during Hajj, Nepal border issues, etc.
//    - MEA helpline: +91-11-2301 2113 (for Indian citizens abroad)

// 2. IMD (India Meteorological Department)
//    - Weather warnings and cyclone tracking
//    - URL: mausam.imd.gov.in
//    - Format: RSS + public data feeds
//    - Coverage: India + Indian Ocean region
//    - Critical for: Monsoon patterns, cyclone warnings, heat waves
//    - Special: District-level warnings, color-coded (Green/Yellow/Orange/Red)

// 3. WHO (World Health Organization)
//    - Disease outbreak notifications (IHR mechanism)
//    - URL: who.int/emergencies
//    - Format: RSS, API (WHO Global Health Observatory)
//    - Coverage: Global
//    - Critical for: Pandemic declarations, PHEIC alerts, vaccination requirements

// 4. US State Department
//    - Travel advisories (4-level system)
//    - URL: travel.state.gov
//    - Format: REST API available
//    - Coverage: Global, country-level
//    - Well-structured, frequently updated, widely referenced

// 5. UK FCDO (Foreign, Commonwealth & Development Office)
//    - Travel advice
//    - Format: API available (via GOV.UK)
//    - Coverage: Global, country-level + regional detail
//    - Often includes specific city/region advisories within countries

// 6. National Disaster Management Authority (NDMA India)
//    - Disaster alerts within India
//    - URL: ndma.gov.in
//    - Format: RSS + mobile app alerts
//    - Coverage: India domestic
//    - Critical for: Domestic trip risk assessment

// Advisory normalization mapping:
// MEA:         "Advisory" / "Caution" / "Warning" / "Do Not Travel"
// US State:    Level 1 / Level 2 / Level 3 / Level 4
// UK FCDO:     "Standard" / "Exercise caution" / "Avoid all but essential" / "Do not travel"
// Our scale:   1 / 2 / 3 / 4 / 5
```

### C. Destination Risk Dashboard

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  DESTINATION RISK DASHBOARD                                        [Refresh] │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  Search: [ Singapore                     ] [Search]                             │
│                                                                                 │
│  ┌─ SINGAPORE ───────────────────────────────────────────────────────────────┐  │
│  │                                                                            │  │
│  │  Overall Risk: ● LOW (2/5)    Trend: → Stable    Updated: 2 hours ago     │  │
│  │                                                                            │  │
│  │  DIMENSIONS                                                                │  │
│  │  ┌──────────────────┬───────┬─────────┬──────────────────────────────────┐  │  │
│  │  │ Dimension        │ Level │ Trend   │ Notes                            │  │  │
│  │  ├──────────────────┼───────┼─────────┼──────────────────────────────────┤  │  │
│  │  │ Political        │ ● 1   │ → Stable│ Stable government                │  │  │
│  │  │ Health           │ ● 1   │ → Stable│ Excellent healthcare             │  │  │
│  │  │ Natural Disaster │ ● 2   │ → Stable│ Low seismic risk; haze from IDN │  │  │
│  │  │ Crime            │ ● 2   │ → Stable│ Low violent crime; petty theft   │  │  │
│  │  │ Terrorism        │ ● 2   │ → Stable│ Low threat; general vigilance    │  │  │
│  │  │ Infrastructure   │ ● 1   │ → Stable│ World-class transport            │  │  │
│  │  │ Environmental    │ ● 2   │ ↑ Worsen│ Periodic haze (PSI monitoring)   │  │  │
│  │  └──────────────────┴───────┴─────────┴──────────────────────────────────┘  │  │
│  │                                                                            │  │
│  │  ACTIVE ADVISORIES: None                                                   │  │
│  │  SOURCES: MEA ✓  US State ✓  UK FCDO ✓  WHO ✓                             │  │
│  │                                                                            │  │
│  └────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                 │
│  ┌─ RISK COMPARISON ────────────────────────────────────────────────────────┐  │
│  │                                                                            │  │
│  │  Trip Destinations:                                                        │  │
│  │  ● Singapore      2/5  Low                                                 │  │
│  │  ● Bangkok        3/5  Medium  ↑ Flooding season (Sep-Nov)                │  │
│  │  ● Bali           2/5  Low     ↑ Volcanic activity advisory               │  │
│  │                                                                            │  │
│  └────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                 │
│  [View Historical Data]  [Export Risk Report]  [Set Alert Thresholds]           │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### D. Historical Incident Database

```typescript
interface HistoricalIncident {
  incidentId: string;
  destinationId: string;
  type: RiskDimensionType;
  category: IncidentCategory;
  description: string;
  startDate: Date;
  endDate?: Date;                      // Ongoing if null
  severity: RiskLevel;
  impact: IncidentImpact;
  sources: string[];
  tags: string[];
}

interface IncidentImpact {
  travelersAffected?: number;
  casualties?: number;
  regionsAffected: string[];
  travelDisruption: 'none' | 'minor' | 'moderate' | 'severe' | 'total';
  economicImpact?: string;
}

type IncidentCategory =
  | 'earthquake'
  | 'flood'
  | 'cyclone'
  | 'hurricane'
  | 'volcanic_eruption'
  | 'tsunami'
  | 'terrorist_attack'
  | 'civil_unrest'
  | 'epidemic'
  | 'pandemic'
  | 'political_crisis'
  | 'mass_shooting'
  | 'transport_accident'
  | 'industrial_disaster'
  | 'cyber_attack'
  | 'extreme_weather'
  | 'wildfire';

interface SeasonalRiskPattern {
  destinationId: string;
  riskType: RiskDimensionType;
  pattern: 'monsoon' | 'cyclone_season' | 'dengue_season' | 'tourist_peak'
         | 'election_period' | 'religious_festival' | 'heat_wave' | 'cold_wave';
  months: number[];
  typicalLevel: RiskLevel;
  description: string;
  preparationAdvice: string[];
  lastOccurrence: Date;
}

// India-specific seasonal patterns:
//
// MONSOON (Jun-Sep):
//   - Kerala: Heavy rainfall, landslides, flooding. Risk 3-4.
//   - Mumbai: Urban flooding, transport disruption. Risk 3.
//   - Northeast: Landslides, road closures. Risk 3-4.
//   - Rajasthan: Minimal impact, some flooding in low areas. Risk 2.
//
// CYCLONE SEASON (Oct-Dec, Apr-May):
//   - East coast (Odisha, AP, TN): Cyclone risk, evacuations. Risk 4.
//   - West coast (Gujarat, Maharashtra): Less frequent but severe. Risk 3.
//
// DENGUE SEASON (Sep-Nov, post-monsoon):
//   - Delhi, Mumbai, Chennai: Outbreaks common. Risk 3.
//   - Prevention advice: Mosquito repellent, long sleeves, avoid stagnant water.
//
// HEAT WAVE (Apr-Jun):
//   - North India (Rajasthan, UP, Delhi): 45°C+ temperatures. Risk 3-4.
//   - Vulnerable: Elderly, children, pre-existing conditions.
//
// FOG (Dec-Jan):
//   - North India: Dense fog disrupts flights and trains. Risk 2-3.
//   - Delhi IGI Airport: Frequent diversions and cancellations.
//
// HAJJ SEASON (variable, Islamic calendar):
//   - Jeddah/Mecca: Stampede risk, heat exhaustion. Risk 3-4.
//   - MEA issues specific advisories for Indian Hajj pilgrims.
//
// KUMBH MELA (every 12 years, next major: 2037):
//   - Allahabad/Prayagraj: Massive crowds, stampede risk. Risk 3-4.
//   - State government issues special safety guidelines.
```

### E. Risk Score Computation

```typescript
interface RiskComputationEngine {
  computeScore(request: RiskScoreRequest): RiskScoreResult;
}

interface RiskScoreRequest {
  destinationId: string;
  travelDates: DateRange;
  travelerProfile?: TravelerRiskProfile;
  tripType?: TripType;
}

interface TravelerRiskProfile {
  age: number;
  healthConditions?: string[];
  travelExperience: 'first_time' | 'occasional' | 'experienced';
  travelingWithChildren: boolean;
  travelingWithElderly: boolean;
  nationality: string;                 // Affects consular support availability
}

type TripType =
  | 'leisure_beach'
  | 'leisure_adventure'
  | 'business'
  | 'pilgrimage'
  | 'educational'
  | 'medical_tourism'
  | 'family_vacation';

interface RiskScoreResult {
  overall: RiskLevel;
  dimensions: RiskDimension[];
  activeAdvisories: AdvisorySummary[];
  seasonalFactors: SeasonalRiskPattern[];
  recommendations: RiskRecommendation[];
  confidence: number;
}

interface RiskRecommendation {
  category: string;
  action: string;                      // "Purchase comprehensive travel insurance"
  urgency: 'informational' | 'recommended' | 'required';
  reason: string;
  relatedDimension: RiskDimensionType;
}

// Scoring algorithm sketch:
//
// baseScore = weightedAverage(dimensions, weights)
// where weights depend on:
//   - Traveler profile (elderly → health weighted higher)
//   - Trip type (adventure → natural_disaster weighted higher)
//   - Seasonality (monsoon → natural_disaster boosted)
//   - Travel duration (longer → risk compounds)
//
// adjustments:
//   - activeAdvisories: +1 or +2 per active advisory
//   - seasonalFactors: +0.5 to +1.5 for in-season risks
//   - conflictingSources: reduce confidence, don't reduce score
//   - recentIncidents (30 days): +0.5 to +2.0
//
// finalScore = clamp(round(baseScore + adjustments), 1, 5)
```

---

## Open Problems

1. **Conflicting advisory sources** — MEA India may rate a destination differently from the US State Dept. How do we present conflicting information without confusing agents? Weight by traveler nationality? Show both?

2. **Sub-national granularity** — Country-level scores are too coarse. Mexico City is very different from Cancun. But neighborhood-level data is hard to source and maintain. What is the right granularity?

3. **Real-time vs. historical scoring** — Real-time events (protests, earthquakes) spike risk temporarily. How do we blend real-time signals with baseline historical risk without creating wild score oscillations?

4. **Bias in risk assessment** — Crime and terrorism scores can reflect stereotypes rather than data. How do we ensure our scoring is evidence-based and doesn't unfairly penalize destinations?

5. **Haze/transboundary pollution** — Singapore/Malaysia haze from Indonesian forest fires (PSI > 200) is a recurring, unpredictable risk. Not political, not natural disaster — how to classify?

6. **Indian traveler-specific risk** — Indian citizens face specific risks abroad (racial profiling in some regions, visa-on-arrival restrictions, limited consular presence). How to factor nationality into risk scoring?

7. **Domestic India risk coverage** — For domestic trips, how do we get district-level data for 700+ districts? IMD provides weather but what about crime, health, and infrastructure at district level?

8. **Advisory latency gap** — Government advisories can be hours or days behind events. Social media is faster but unreliable. How to bridge this gap for time-critical situations?

---

## Next Steps

- [ ] Map all available free advisory APIs (MEA, US State Dept, UK FCDO, WHO, IMD)
- [ ] Prototype risk score computation for top 20 destinations booked by Indian agencies
- [ ] Design advisory normalization pipeline (different scales → unified 1-5)
- [ ] Build historical incident database schema and seed with 3 years of data
- [ ] Research commercial travel intelligence providers (International SOS, Riskline, Sitata)
- [ ] Design seasonal risk pattern model for India-specific patterns (monsoon, cyclone, dengue)
- [ ] Prototype destination risk dashboard UI component
- [ ] Study geo-fencing approaches for sub-national risk granularity
- [ ] Evaluate IMD weather API integration for real-time domestic risk feeds
- [ ] Research PSI/haze monitoring for Southeast Asian destinations
