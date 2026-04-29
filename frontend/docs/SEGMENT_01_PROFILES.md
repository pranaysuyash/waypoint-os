# Customer Segmentation 01: Profiles & Models

> Customer segmentation models, Indian traveler personas, RFM scoring, and lifetime value prediction

---

## Document Overview

**Focus:** Customer segmentation models and persona architecture
**Status:** Research Exploration
**Last Updated:** 2026-04-28

---

## Key Questions

### Segmentation Models
- What segmentation models are most relevant for an Indian travel agency?
- How do demographic, behavioral, value-based, psychographic, and lifecycle models overlap?
- Which model produces the most actionable segments for travel?
- How do we combine multiple models into a unified segment assignment?

### Indian Traveler Personas
- What are the distinct Indian traveler personas?
- How do cultural factors (joint families, pilgrimage, wedding season) shape segments?
- What about NRIs visiting home — are they a unique segment?
- How do budget family, luxury honeymooner, corporate, pilgrim, and adventure personas differ?

### Persona Cards & Travel Patterns
- What data points belong on a persona card?
- How do we capture seasonal travel patterns unique to India (summer vacation, Diwali, wedding season)?
- What about regional variations (South India temple tours vs. North India hill stations)?

### Segment Assignment Engine
- How does a customer get assigned to a segment?
- Can a customer belong to multiple segments simultaneously?
- How often should segment membership be re-evaluated?
- What triggers a segment change?

### RFM Scoring & CLV
- How do we implement Recency, Frequency, Monetary value scoring?
- What RFM benchmarks apply to Indian travel customers?
- How do we predict customer lifetime value?
- What data is needed for accurate CLV prediction?

---

## Research Areas

### A. Segmentation Models

**Demographic Segmentation:**

| Factor | Data Points | Travel Relevance | Research Needed |
|--------|-------------|------------------|-----------------|
| **Age** | Date of birth, generation | Family trips vs. solo adventure | How age correlates with trip type in India? |
| **Income** | Declared, inferred from spend | Budget vs. luxury | Income brackets for Indian travel market? |
| **Family size** | Members, ages | Family packages vs. couples | Joint family impact on booking patterns? |
| **Location** | City, tier (1/2/3) | Departure hub, domestic vs. international | Tier-2 city travel growth? |
| **Occupation** | Profession, industry | Corporate travel, timing | IT professionals vs. government employees? |
| **Education** | Level, field | Destination preferences | Education-travel correlation? |

**Behavioral Segmentation:**

| Factor | Data Points | Travel Relevance | Research Needed |
|--------|-------------|------------------|-----------------|
| **Booking frequency** | Trips per year | Frequent vs. occasional | Average Indian traveler frequency? |
| **Advance planning** | Lead time before trip | Early bird vs. last-minute | Typical Indian booking lead times? |
| **Channel preference** | WhatsApp, phone, walk-in | Service model | Channel preference by segment? |
| **Loyalty behavior** | Repeat bookings, referrals | Retention strategy | Loyalty patterns in Indian market? |
| **Price sensitivity** | Discount usage, negotiation | Pricing strategy | Price elasticity by segment? |
| **Trip purpose** | Leisure, business, pilgrimage, medical | Package design | Purpose distribution in India? |

**Value-Based Segmentation:**

| Tier | Annual Spend Range | Percentage of Customers | Revenue Contribution | Research Needed |
|------|--------------------|------------------------|---------------------|-----------------|
| **Platinum** | > INR 5,00,000 | ~5% | ~35% | Exact thresholds? |
| **Gold** | INR 2,00,000 - 5,00,000 | ~15% | ~30% | Upgrade triggers? |
| **Silver** | INR 50,000 - 2,00,000 | ~30% | ~25% | Growth potential? |
| **Bronze** | < INR 50,000 | ~50% | ~10% | Conversion rate? |

**Psychographic Segmentation:**

| Psychographic | Characteristics | Travel Style | Research Needed |
|---------------|-----------------|-------------|-----------------|
| **Explorer** | Seeks new experiences, offbeat | Adventure, new destinations | Size of segment? |
| **Comfort seeker** | Values convenience, familiarity | Premium, repeat destinations | Price elasticity? |
| **Social traveler** | Group-oriented, family-first | Family packages, group tours | Booking patterns? |
| **Status traveler** | Premium experiences, Instagram-worthy | Luxury, trending spots | Influencer impact? |
| **Value maximizer** | Best deals, maximum coverage | Budget packages, group deals | Loyalty potential? |
| **Spiritual traveler** | Pilgrimage, wellness | Temple tours, yoga retreats | Seasonal patterns? |

**Lifecycle Stage Segmentation:**

| Stage | Definition | Typical Duration | Key Action | Research Needed |
|-------|-----------|------------------|------------|-----------------|
| **Prospect** | Inquiry but no booking | 0-30 days | Convert | Conversion rates? |
| **First-timer** | First booking completed | 0-3 months post-trip | Delight + re-engage | Repeat rate? |
| **Repeat** | 2-3 bookings | 6-12 months | Upsell | Upsell success rate? |
| **Loyal** | 4+ bookings, regular | Ongoing | Retain + refer | Referral rate? |
| **At-risk** | Declining engagement | Varies | Win-back | Churn signals? |
| **Churned** | No activity 12+ months | 12+ months | Reactivate | Reactivation rate? |

### B. Indian Traveler Personas

**Persona 1: Budget Family (Sharma Family)**

```
+-------------------------------------------+
|  PERSONA: Budget Family Traveler           |
|  Code: BUD_FAM                             |
+-------------------------------------------+
|  Age:       35-45 (primary decision maker) |
|  Family:    Spouse + 1-2 children          |
|  Income:    INR 8-15 LPA                    |
|  Location:  Tier-1/2 city                  |
|                                             |
|  TRAVEL PATTERNS:                           |
|  - 1 major trip/year (summer vacation)     |
|  - 1 short trip (long weekend/Diwali)      |
|  - Domestic preferred                      |
|  - Budget: INR 40,000-80,000/trip          |
|  - Researches heavily on YouTube/WhatsApp  |
|  - Books 2-3 months in advance             |
|  - Price-sensitive, negotiates              |
|  - Prefers all-inclusive packages          |
|  - Food: Pure veg preferred                |
|                                             |
|  CHANNEL: WhatsApp > Phone > Walk-in       |
|  PAYMENT:  EMI options, UPI, cash          |
|  LOYALTY:  Referral-driven, community trust |
+-------------------------------------------+
```

**Persona 2: Luxury Honeymooner (Newlywed Couple)**

```
+-------------------------------------------+
|  PERSONA: Luxury Honeymooner               |
|  Code: LUX_HNY                             |
+-------------------------------------------+
|  Age:       26-34                          |
|  Family:    Newly married couple            |
|  Income:    INR 15-40 LPA (combined)       |
|  Location:  Metro city                     |
|                                             |
|  TRAVEL PATTERNS:                           |
|  - 1 big honeymoon trip                    |
|  - International aspiration (Maldives,      |
|    Switzerland, Bali, Europe)              |
|  - Budget: INR 2,00,000-8,00,000           |
|  - Instagram/social media influenced        |
|  - Books 4-6 months in advance             |
|  - Values: Privacy, luxury, experiences    |
|  - Premium hotels, candle-light dinners    |
|  - Wants curated, photogenic itineraries   |
|                                             |
|  CHANNEL: Instagram > Website > Phone      |
|  PAYMENT:  Credit card EMI, loan options   |
|  LOYALTY:  Experience-driven repeat         |
+-------------------------------------------+
```

**Persona 3: Corporate Executive**

```
+-------------------------------------------+
|  PERSONA: Corporate Executive              |
|  Code: CORP_EXEC                           |
+-------------------------------------------+
|  Age:       30-50                          |
|  Family:    Varies                         |
|  Income:    INR 25-80+ LPA                 |
|  Location:  Metro / Tier-1                 |
|                                             |
|  TRAVEL PATTERNS:                           |
|  - Frequent business travel (6-12x/year)  |
|  - 1-2 leisure trips with family           |
|  - Business: Domestic + SE Asia/Middle East|
|  - Values: Efficiency, reliability, comfort|
|  - Last-minute bookings common             |
|  - Needs: Visa support, forex, insurance   |
|  - Expense policy aware                    |
|  - Time-poor, wants quick turnaround       |
|                                             |
|  CHANNEL: Email > Phone > App              |
|  PAYMENT:  Corporate card, invoicing       |
|  LOYALTY:  Service quality-driven          |
+-------------------------------------------+
```

**Persona 4: Pilgrim / Spiritual Traveler**

```
+-------------------------------------------+
|  PERSONA: Pilgrim / Spiritual Traveler     |
|  Code: PIL_SPIR                            |
+-------------------------------------------+
|  Age:       40-65+                         |
|  Family:    Spouse, sometimes group        |
|  Income:    Varies widely                  |
|  Location:  Pan-India                      |
|                                             |
|  TRAVEL PATTERNS:                           |
|  - 1-2 pilgrimages/year                    |
|  - Destinations: Vaishno Devi, Tirupati,   |
|    Varanasi, Amarnath, Char Dham, Mecca    |
|  - Often travels in groups (family/satsang)|
|  - Budget: Moderate (INR 20,000-60,000)    |
|  - Seasonal: Follows religious calendar    |
|  - Values: Simplicity, darshan, rituals    |
|  - Needs: Transport, basic accommodation   |
|  - Food: Satvik, vegetarian               |
|                                             |
|  CHANNEL: Phone > WhatsApp > Walk-in       |
|  PAYMENT:  Cash, UPI, bank transfer        |
|  LOYALTY:  Very high if trust established  |
+-------------------------------------------+
```

**Persona 5: Adventure Seeker**

```
+-------------------------------------------+
|  PERSONA: Adventure Seeker                 |
|  Code: ADV_SEEK                            |
+-------------------------------------------+
|  Age:       22-35                          |
|  Family:    Solo / friends / couple         |
|  Income:    INR 6-20 LPA                   |
|  Location:  Metro / college towns          |
|                                             |
|  TRAVEL PATTERNS:                           |
|  - Multiple short trips/year (4-6)         |
|  - Destinations: Himalayas, NE India,      |
|    international adventure hubs            |
|  - Activities: Trekking, scuba, skiing,    |
|    paragliding, road trips                 |
|  - Budget: INR 15,000-50,000/trip          |
|  - Flexible dates, last-minute friendly    |
|  - Influenced by: YouTube, travel blogs    |
|  - Values: Experiences over luxury         |
|  - Self-researches, compares online        |
|                                             |
|  CHANNEL: Website/App > Social > WhatsApp  |
|  PAYMENT:  UPI, credit card                |
|  LOYALTY:  Low — shops around              |
+-------------------------------------------+
```

**Persona 6: NRI Visiting Home**

```
+-------------------------------------------+
|  PERSONA: NRI Visiting Home                |
|  Code: NRI_HOME                            |
+-------------------------------------------+
|  Age:       30-55                          |
|  Family:    Spouse + children              |
|  Income:    USD 60,000-200,000+            |
|  Location:  US, UK, Gulf, Australia, Canada|
|                                             |
|  TRAVEL PATTERNS:                           |
|  - 1-2 India visits/year                   |
|  - Trip combines: Family + tourism         |
|  - Duration: 2-4 weeks                     |
|  - Budget: USD 3,000-10,000/trip           |
|  - Needs: Multi-city itinerary, flights,   |
|    hotels (near family + tourist spots)    |
|  - Often plans side trip (Goa, Kerala,     |
|    Rajasthan) with family                  |
|  - Values: Comfort, safety, convenience    |
|  - Dual-currency, timezone challenges      |
|                                             |
|  CHANNEL: Email > WhatsApp > Website       |
|  PAYMENT:  International card, wire        |
|  LOYALTY:  High if reliable agent found    |
+-------------------------------------------+
```

### C. Segment Assignment Engine

**Assignment Logic:**

| Component | Description | Research Needed |
|-----------|-------------|-----------------|
| **Rule engine** | Score-based assignment from profile data | Weight optimization? |
| **ML classifier** | Multi-label classification model | Training data availability? |
| **Override rules** | Manual agent assignment | Override audit trail? |
| **Confidence scoring** | How certain is the assignment? | Threshold calibration? |
| **Multi-segment** | Customers in multiple segments | Priority resolution? |

**Assignment Flow:**

```
Customer Interaction
       |
       v
  [Profile Data] -----> [Feature Extraction]
       |                        |
       v                        v
  [Booking History] --> [Scoring Engine]
       |                        |
       v                        v
  [Behavior Signals] -> [Segment Assignment]
       |                        |
       v                        v
  [Rule Overrides] ---> [Final Segment Map]
                                |
                                v
                    [Persona Card Match]
                                |
                                v
                    [Personalization Context]
```

**Re-evaluation Triggers:**

| Trigger | Frequency | Research Needed |
|---------|-----------|-----------------|
| **New booking** | On event | Immediate vs. batch? |
| **Profile update** | On event | Which fields matter? |
| **Inactivity period** | Weekly check | Inactivity threshold? |
| **Spend milestone** | On event | Milestone definitions? |
| **Seasonal refresh** | Quarterly | Seasonal model weights? |
| **Annual review** | Yearly | Full reclassification? |

### D. RFM Scoring

**RFM Framework:**

| Dimension | Score 1 (Low) | Score 2 | Score 3 | Score 4 | Score 5 (High) | Research Needed |
|-----------|---------------|---------|---------|---------|----------------|-----------------|
| **Recency** | > 18 months | 12-18 mo | 6-12 mo | 3-6 mo | < 3 months | India-specific thresholds? |
| **Frequency** | 1 trip ever | 1 trip/yr | 2 trips/yr | 3-4 trips/yr | 5+ trips/yr | Trip vs. booking count? |
| **Monetary** | < 25K | 25K-75K | 75K-2L | 2L-5L | > 5L INR/yr | Include ancillary spend? |

**RFM Segment Matrix:**

| RFM Score | Segment Label | Strategy | Research Needed |
|-----------|--------------|----------|-----------------|
| **555** | Champions | Reward, get referrals | Reward structure? |
| **5xx (R>=4)** | Recent customers | Upsell, convert to repeat | Upsell offers? |
| **x5x (F>=4)** | Frequent travelers | Loyalty, exclusive access | Loyalty benefits? |
| **xx5 (M>=4)** | Big spenders | Premium service, concierge | Service design? |
| **3xx-4xx** | Promising | Nurture, educate | Nurture sequence? |
| **2xx** | Need attention | Reactivate, special offers | Offer effectiveness? |
| **1xx** | Lost | Win-back campaigns | Win-back rate? |
| **511-515** | New high-value | Onboard carefully | Onboarding flow? |
| **151-155** | At-risk VIPs | Immediate intervention | Intervention model? |

### E. Customer Lifetime Value (CLV) Prediction

**CLV Data Requirements:**

| Data Category | Fields | Source | Research Needed |
|---------------|--------|--------|-----------------|
| **Transaction** | Booking value, frequency, margin | Booking engine | Margin calculation? |
| **Behavioral** | Engagement, channel usage, reviews | Analytics | Engagement scoring? |
| **Demographic** | Age, income, family stage | CRM profile | Income inference? |
| **Predictive** | Churn probability, next trip timing | ML model | Model accuracy? |
| **Referral** | Referrals made, conversion rate | Referral tracker | Referral value? |

**CLV Model Approaches:**

| Approach | Complexity | Accuracy | Data Needed | Research Needed |
|----------|-----------|----------|-------------|-----------------|
| **Historical CLV** | Low | Low | Past transactions only | Baseline accuracy? |
| **Predictive CLV (statistical)** | Medium | Medium | RFM + demographics | Best statistical model? |
| **ML-based CLV** | High | High | Full behavioral + transactional | Training data size? |
| **Cohort-based** | Medium | Medium | Cohort definitions + trends | Cohort definitions? |
| **Hybrid** | High | Highest | All of the above | Feature engineering? |

---

## Data Model Sketch

```typescript
// Research-level model — not final

interface CustomerSegment {
  segmentId: string;
  agencyId: string;
  name: string;
  code: string; // e.g., 'BUD_FAM', 'LUX_HNY'

  // Model
  model: SegmentationModel;
  description: string;

  // Definition
  criteria: SegmentCriteria[];
  scoringWeights?: ScoringWeights;

  // Membership
  dynamic: boolean;
  currentMembers: number;
  estimatedReach?: number;

  // Metadata
  tags: string[];
  parentSegmentId?: string;
  childSegmentIds: string[];

  // Status
  active: boolean;
  createdAt: Date;
  updatedAt: Date;
}

type SegmentationModel =
  | 'demographic'
  | 'behavioral'
  | 'value_based'
  | 'psychographic'
  | 'lifecycle'
  | 'hybrid';

interface SegmentCriteria {
  criteriaId: string;
  field: string;
  operator: SegmentOperator;
  value: any;
  weight: number; // 0-1, importance weight
  logicalOperator?: 'AND' | 'OR';
  nestedCriteria?: SegmentCriteria[];
}

type SegmentOperator =
  | 'equals'
  | 'not_equals'
  | 'greater_than'
  | 'less_than'
  | 'between'
  | 'in'
  | 'not_in'
  | 'contains'
  | 'is_null'
  | 'in_last'
  | 'not_in_last';

interface ScoringWeights {
  demographic: number;   // 0-1
  behavioral: number;    // 0-1
  value: number;         // 0-1
  psychographic: number; // 0-1
  lifecycle: number;     // 0-1
}

// --- Persona Card ---

interface PersonaCard {
  personaCode: string; // e.g., 'BUD_FAM'
  name: string;
  tagline: string;

  // Demographics
  targetAgeRange: [number, number];
  targetIncomeRange: [number, number]; // INR annual
  familyTypes: FamilyType[];
  targetLocations: string[]; // City tiers or specific cities

  // Travel Patterns
  tripFrequency: TripFrequency;
  averageBudget: BudgetRange;
  preferredDestinations: string[];
  bookingLeadTime: LeadTimeCategory;
  seasonalPeaks: IndianSeason[];

  // Preferences
  accommodationPreference: string[];
  foodPreference: FoodPreference;
  channelPreference: ChannelPreference[];
  paymentPreference: PaymentMethod[];

  // Psychology
  motivators: string[];
  painPoints: string[];
  decisionFactors: string[];

  // Loyalty Profile
  loyaltyPotential: 'low' | 'medium' | 'high';
  referralLikelihood: 'low' | 'medium' | 'high';
  priceSensitivity: 'low' | 'medium' | 'high';

  // Visual
  avatarUrl?: string;
  description: string;
}

type FamilyType =
  | 'single'
  | 'couple_no_kids'
  | 'couple_with_kids'
  | 'joint_family'
  | 'extended_group'
  | 'friends_group';

type TripFrequency =
  | 'rare'          // < 1/year
  | 'occasional'    // 1-2/year
  | 'regular'       // 3-4/year
  | 'frequent'      // 5-8/year
  | 'very_frequent'; // 8+/year

interface BudgetRange {
  min: number; // INR
  max: number;
  currency: 'INR' | 'USD';
  perTrip: boolean;
}

type LeadTimeCategory =
  | 'last_minute'    // < 1 week
  | 'short'          // 1-4 weeks
  | 'moderate'       // 1-3 months
  | 'planned'        // 3-6 months
  | 'advance';       // 6+ months

type IndianSeason =
  | 'summer_vacation'  // Apr-Jun
  | 'monsoon'          // Jul-Sep
  | 'festive_diwali'   // Oct-Nov
  | 'wedding_season'   // Nov-Feb
  | 'winter_holiday'   // Dec-Jan
  | 'spring'           // Feb-Mar
  | 'pilgrimage_season'; // Varied by site

type FoodPreference =
  | 'vegetarian'
  | 'non_vegetarian'
  | 'pure_veg'
  | 'satvik'
  | 'jain'
  | 'halal'
  | 'no_restriction';

type ChannelPreference =
  | 'whatsapp'
  | 'phone_call'
  | 'email'
  | 'walk_in'
  | 'website'
  | 'mobile_app'
  | 'social_media';

// --- RFM Scoring ---

interface RFMScore {
  customerId: string;
  calculatedAt: Date;

  // Individual scores (1-5)
  recencyScore: number;
  frequencyScore: number;
  monetaryScore: number;

  // Combined
  compositeScore: number; // 1-125 or weighted
  segment: string; // Derived from RFM matrix

  // Details
  lastTripDate: Date;
  totalTrips: number;
  totalSpend: number; // INR
  averageTripValue: number;

  // Period
  evaluationPeriod: '12_months' | '24_months' | 'lifetime';
}

interface RFMThreshold {
  agencyId: string;
  dimension: 'recency' | 'frequency' | 'monetary';
  score: number; // 1-5
  minValue: number;
  maxValue: number;
  unit: string; // 'months', 'trips', 'INR'
  updatedAt: Date;
}

// --- CLV Prediction ---

interface CLVPrediction {
  customerId: string;
  predictionDate: Date;

  // Values
  historicalCLV: number;         // INR — actual spend to date
  predictedCLV_12m: number;      // INR — predicted next 12 months
  predictedCLV_lifetime: number; // INR — predicted total lifetime

  // Model
  modelType: CLVModelType;
  confidence: number; // 0-1

  // Components
  averageOrderValue: number;
  purchaseFrequency: number;     // Trips/year
  customerLifespan: number;      // Predicted years
  churnProbability: number;      // 0-1

  // Segment
  valueTier: ValueTier;
  segmentCode: string;
}

type CLVModelType =
  | 'historical'
  | 'bg_nbd'           // Beta Geometric/NBD
  | 'gamma_gamma'      // Gamma-Gamma for monetary
  | 'ml_regression'
  | 'hybrid';

type ValueTier =
  | 'platinum'
  | 'gold'
  | 'silver'
  | 'bronze';

// --- Segment Assignment ---

interface SegmentAssignment {
  assignmentId: string;
  customerId: string;
  segmentId: string;
  personaCode?: string;

  // Assignment details
  method: 'auto_rule' | 'auto_ml' | 'manual' | 'hybrid';
  confidence: number; // 0-1
  matchingCriteria: string[];

  // Timing
  assignedAt: Date;
  assignedBy: string; // User ID or 'system'
  expiresAt?: Date;

  // History
  previousSegmentId?: string;
  changeReason?: string;
}

// --- Segment Dashboard ---

interface SegmentDashboardMetrics {
  segmentId: string;
  period: 'monthly' | 'quarterly' | 'yearly';

  // Size
  totalMembers: number;
  newMembers: number;
  churnedMembers: number;
  netGrowth: number;

  // Value
  totalRevenue: number;
  averageRevenue: number;
  averageCLV: number;

  // Engagement
  averageTripFrequency: number;
  averageBookingLeadTime: number;
  whatsappResponseRate: number;

  // Health
  satisfactionScore: number;  // NPS or CSAT
  referralRate: number;
  churnRisk: number; // 0-1 average
}
```

---

## Open Problems

### 1. Segment Overlap & Multi-Label Assignment
**Challenge:** A customer can be a corporate executive AND a pilgrim AND a family traveler

**Options:**
- Primary + secondary segment assignment
- Multi-label classification with confidence scores
- Context-dependent segmentation (segment changes by trip purpose)

**Research:** How do Indian agencies currently handle multi-faceted customers?

### 2. Cold-Start Problem
**Challenge:** New customers have no travel history for RFM or behavioral scoring

**Options:**
- Onboarding questionnaire to seed initial segment
- Demographic-only initial assignment
- "Prospect" segment with rapid graduation
- Look-alike modeling based on similar profiles

**Research:** What is the minimum data needed for reliable segment assignment?

### 3. Seasonal Segment Shifts
**Challenge:** Indian travel is highly seasonal — a budget family may book luxury for a special occasion

**Options:**
- Seasonal segment overlays
- Trip-level vs. customer-level segmentation
- Temporary segment upgrades for specific campaigns

**Research:** How often do customers shift segments seasonally?

### 4. Data Availability for RFM
**Challenge:** Many Indian travelers book through multiple agencies, making RFM incomplete

**Options:**
- Self-reported travel frequency
- Inferred from available data with confidence intervals
- Progressive enrichment over time

**Research:** What RFM thresholds work for the Indian market?

### 5. Cultural Nuance in Segmentation
**Challenge:** Indian market has unique factors: joint families, pilgrimage, wedding travel, regional differences

**Options:**
- India-specific segmentation dimensions
- Regional sub-segments
- Cultural event calendar as segmentation input

**Research:** Which cultural factors are most predictive of travel behavior?

### 6. Tier-2/3 City Segment Differences
**Challenge:** Tier-2/3 city customers may have different aspirations, channel preferences, and price sensitivity

**Options:**
- City-tier as a primary segmentation dimension
- Separate persona cards for tier-2/3 variants
- Graduated service models by tier

**Research:** How do tier-2/3 travel patterns differ from metro patterns?

---

## Next Steps

1. Validate persona cards with real agency data and agent interviews
2. Define RFM thresholds based on existing customer base
3. Build initial segment assignment rule engine
4. Design persona card UI component for agent workspace
5. Run CLV prediction pilot on historical booking data
6. Research tier-2/3 city customer behavior patterns
7. Map Indian seasonal calendar to segment triggers
8. Benchmark segmentation against existing CRM data

---

**Series:** [Customer Segmentation & Personalization](./SEGMENT_MASTER_INDEX.md)
**Next:** [SEGMENT_02_PERSONALIZATION.md](./SEGMENT_02_PERSONALIZATION.md) — Personalization Engine
