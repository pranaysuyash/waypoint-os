# Customer Segmentation 02: Personalization Engine

> Personalized trip recommendations, dynamic pricing, supplier matching, and India-specific personalization

---

## Document Overview

**Focus:** Personalization across trips, channels, and Indian market context
**Status:** Research Exploration
**Last Updated:** 2026-04-28

---

## Key Questions

### Personalization Engine
- How do we personalize trip recommendations by segment?
- What role does dynamic pricing play in personalization?
- How do we match customers to preferred suppliers?
- How do destination suggestions vary by segment?

### Cross-Channel Personalization
- How do we maintain consistent personalization across WhatsApp, email, and in-app?
- What personalization is appropriate per channel?
- How do we sync personalization state across channels?

### Indian Market Personalization
- How do Indian festivals (Diwali, summer vacation, wedding season) drive personalization?
- What are the festival-based recommendation patterns?
- How do we handle regional and linguistic personalization?

### Privacy & DPDP Act Compliance
- How do we personalize while respecting the Digital Personal Data Protection Act, 2023?
- What consent is needed for personalization?
- How do we handle data minimization while still personalizing effectively?
- What are the rights of the data principal (customer)?

---

## Research Areas

### A. Personalized Trip Recommendations

**Recommendation by Segment:**

| Segment | Recommendation Strategy | Example | Research Needed |
|---------|------------------------|---------|-----------------|
| **Budget Family** | Value packages, all-inclusive deals, family-friendly destinations | "Rajasthan family tour — INR 45,000 for 4" | Conversion rate by recommendation type? |
| **Luxury Honeymooner** | Curated romantic getaways, premium resorts, private experiences | "Overwater villa in Maldives with spa package" | Upsell acceptance rate? |
| **Corporate Exec** | Efficient itineraries, business hotels, seamless logistics | "Bengaluru-Mumbai same-day return with airport transfer" | Corporate rebooking rate? |
| **Pilgrim** | Pilgrimage circuits, group packages, religious calendar-based | "Char Dham Yatra — 12-day guided pilgrimage" | Pilgrim repeat rate? |
| **Adventure Seeker** | Offbeat destinations, activity-focused, flexible dates | "Ladakh bike trip — guided or self-drive" | Adventure segment loyalty? |
| **NRI** | Multi-city India + tourist combo, airport pickup/drop | "Delhi visit + Golden Triangle side trip" | NRI trip frequency? |

**Recommendation Engine Architecture:**

```
                    [Customer Profile]
                          |
            +-------------+-------------+
            |             |             |
     [Segment Match]  [RFM Score]  [Travel History]
            |             |             |
            +-------------+-------------+
                          |
                   [Feature Vector]
                          |
            +-------------+-------------+
            |             |             |
     [Collaborative] [Content-Based] [Rule-Based]
     Filtering        Filtering      Overrides
            |             |             |
            +-------------+-------------+
                          |
                  [Score & Rank]
                          |
            +-------------+-------------+
            |             |             |
     [Diversity]    [Seasonal]    [Inventory]
     Injection       Boost         Check
            |             |             |
            +-------------+-------------+
                          |
                 [Personalized Picks]
                 (Top 5-10 options)
                          |
                   [Agent Review]
                          |
              [Final Recommendations]
```

**Recommendation Signals:**

| Signal | Weight (Example) | Source | Research Needed |
|--------|-------------------|--------|-----------------|
| **Past destinations** | High | Booking history | Recency decay function? |
| **Wishlist / searches** | Medium | App/web analytics | Search-to-booking conversion? |
| **Segment defaults** | Medium | Segment assignment | Default relevance? |
| **Seasonal appropriateness** | High | Calendar + destination data | Seasonal model accuracy? |
| **Budget fit** | High | RFM + segment | Price elasticity per segment? |
| **Companion fit** | Medium | Family/group profile | Family recommendation logic? |
| **Trending destinations** | Low | Aggregated booking data | Trend detection sensitivity? |
| **Availability** | Required | Inventory system | Real-time vs. cached? |

### B. Dynamic Pricing by Segment

**Pricing Personalization:**

| Segment | Pricing Strategy | Example | Research Needed |
|---------|-----------------|---------|-----------------|
| **Budget Family** | EMI options, early-bird discounts, group savings | "Book 60 days early — save 15%" | Discount sensitivity threshold? |
| **Luxury Honeymooner** | Value-add over discount, room upgrades, complimentary experiences | "Free couples spa with honeymoon suite" | Value-add vs. discount preference? |
| **Corporate Exec** | Corporate negotiated rates, loyalty tiers, volume discounts | "Corporate rate applied — 12% off standard" | Corporate contract pricing models? |
| **Pilgrim** | Group discounts, off-season rates, simple transparent pricing | "Group of 10+ — INR 2,000 off per person" | Group size elasticity? |
| **Adventure** | Flash deals, last-minute offers, offbeat destination promos | "Last-minute Ladakh — 20% off" | Last-minute conversion rate? |
| **NRI** | Forex-inclusive pricing, dual-currency display, holiday packages | "USD 1,200 all-inclusive India visit package" | Currency display preference? |

**Pricing Rules Engine:**

| Rule Type | Trigger | Action | Research Needed |
|-----------|---------|--------|-----------------|
| **Segment discount** | Customer belongs to segment | Apply segment-specific rate | Discount ceiling? |
| **Loyalty tier** | Customer tier matched | Apply tier multiplier | Tier economics? |
| **Seasonal** | Travel date in festive period | Premium or promotional pricing | Festival price elasticity? |
| **Volume** | Group size > threshold | Group rate | Volume thresholds? |
| **Early bird** | Booking lead time > threshold | Early booking discount | Optimal lead time? |
| **Last-minute** | Departure within 7 days | Clearance pricing | Inventory risk model? |
| **Dynamic demand** | Demand exceeds supply | Surge pricing | Customer reaction? |

### C. Preferred Supplier Matching

**Supplier-Customer Matching:**

| Match Dimension | Data Source | Example | Research Needed |
|-----------------|-------------|---------|-----------------|
| **Budget alignment** | Customer spend + supplier tier | Budget family matched with 3-star partner | Tier mapping accuracy? |
| **Style match** | Customer preferences + supplier category | Luxury honeymooner matched with premium resort | Preference data availability? |
| **Service quality** | Customer expectations + supplier ratings | Corporate exec matched with high-rated business hotel | Rating reliability? |
| **Dietary match** | Food preference + supplier cuisine options | Pure veg family matched with veg-friendly hotel | Dietary data completeness? |
| **Location match** | Customer itinerary + supplier locations | Proximity to key attractions | Geolocation matching logic? |
| **Past satisfaction** | Previous trip feedback + supplier | Repeat supplier if rated well | Satisfaction tracking? |

**Supplier Preference Matrix (by Persona):**

| Supplier Type | BUD_FAM | LUX_HNY | CORP_EXEC | PIL_SPIR | ADV_SEEK | NRI_HOME |
|---------------|---------|---------|-----------|----------|----------|----------|
| **Budget hotel** | Primary | — | — | Secondary | Secondary | — |
| **Premium resort** | — | Primary | Secondary | — | — | Primary |
| **Business hotel** | — | — | Primary | — | — | Secondary |
| **Dharamshala** | Secondary | — | — | Primary | — | — |
| **Homestay** | Secondary | — | — | Secondary | Primary | Secondary |
| **Hostel** | — | — | — | — | Primary | — |
| **Heritage hotel** | Secondary | Primary | — | — | — | Primary |

### D. Cross-Channel Personalization

**Channel-Specific Personalization:**

| Channel | Personalization Level | Content Type | Example | Research Needed |
|---------|----------------------|-------------|---------|-----------------|
| **WhatsApp** | High (conversation context) | Rich messages, cards, quick replies | "Hi Sharma ji! Your Goa trip is confirmed. Here's your itinerary card." | WhatsApp API limits? |
| **Email** | Medium (template dynamic blocks) | Rich HTML, personalized recommendations | "Recommended summer vacation packages for your family" | Email open/click rates by segment? |
| **In-App** | High (full profile context) | Dynamic UI, personalized dashboard | "Welcome back! Continue planning your Kerala trip" | App engagement by segment? |
| **SMS** | Low (transactional only) | Booking confirmations, reminders | "Your flight AI-101 departs tomorrow 6:00 AM. Check-in online." | SMS delivery rates? |
| **Phone** | Agent-mediated | Agent sees full context, personalized script | Agent: "Mr. Sharma, based on your last Manali trip..." | Agent script personalization? |

**Personalization State Sync:**

```
[Customer Interaction on WhatsApp]
         |
         v
  [Personalization Store] <---> [Event Bus]
         |                            |
         v                            v
[Next Interaction on Email]    [Profile Updated]
         |                            |
         v                            v
[Next Interaction on App]     [Segment Re-evaluated]
```

### E. Festival-Based Personalization (India-Specific)

**Indian Festival Calendar for Travel:**

| Festival/Season | Period | Travel Pattern | Personalization Opportunity | Research Needed |
|-----------------|--------|---------------|---------------------------|-----------------|
| **Summer Vacation** | Apr-Jun | Peak family travel, hill stations, international | Family package recommendations, early-bird offers | Peak vs. off-peak pricing ratio? |
| **Diwali** | Oct-Nov | Long weekend trips, domestic + short international | Diwali getaway packages, gift-voucher promotions | Diwali trip booking lead time? |
| **Wedding Season** | Nov-Feb | Honeymoon bookings, destination weddings | Honeymoon packages, group wedding travel | Wedding-season booking volume? |
| **Christmas/New Year** | Dec | Party destinations, Goa, international | New Year party packages, year-end deals | New Year demand pattern? |
| **Holi** | Mar | Short trips, domestic | Holi weekend getaways | Holi travel volume? |
| **Ramadan/Eid** | Varies | Family reunions, pilgrimage | Group packages, iftar-savvy itineraries | Eid travel patterns? |
| **Pilgrimage seasons** | Varies by site | Massive pilgrim movement | Pilgrimage packages, group logistics | Pilgrim volume forecasting? |
| **Gurupurab/Baisakhi** | Varies | Regional travel, cultural tourism | Regional packages | Regional demand spikes? |
| **Long Weekends** | Throughout year | Short trips, getaways | Weekend getaway recommendations | Long weekend booking patterns? |

**Festival Recommendation Engine:**

```typescript
// Festival-triggered personalization flow

interface FestivalTrigger {
  festival: IndianFestival;
  startDate: Date;
  endDate: Date;
  leadTimeWeeks: number;      // When to start promotions
  applicableSegments: string[]; // Which persona codes
  travelPattern: FestivalTravelPattern;
}

interface FestivalTravelPattern {
  popularDestinations: string[];
  averageTripDuration: number; // days
  budgetRange: BudgetRange;
  groupSizeTypical: number;
  bookingLeadTime: LeadTimeCategory;
}

type IndianFestival =
  | 'summer_vacation'
  | 'diwali'
  | 'wedding_season'
  | 'christmas_new_year'
  | 'holi'
  | 'eid'
  | 'ramzan'
  | 'char_dham_yatra'
  | 'vaishno_devi'
  | 'tirupati_brahmotsavam'
  | 'amarnath_yatra'
  | 'long_weekend';
```

### F. Privacy-Respecting Personalization (DPDP Act)

**DPDP Act 2023 Requirements for Personalization:**

| Requirement | DPDP Section | Impact on Personalization | Research Needed |
|-------------|-------------|--------------------------|-----------------|
| **Consent** | Section 6 | Must obtain clear consent before profiling | Consent UX design? |
| **Purpose limitation** | Section 6(2) | Personalization data used only for stated purpose | Purpose definitions? |
| **Data minimization** | Section 7(1) | Collect only what is necessary for personalization | Minimum viable data? |
| **Data principal rights** | Section 12-14 | Right to access, correct, erase personalization data | Self-service portal? |
| **Grievance redressal** | Section 13 | Must have mechanism for personalization complaints | Grievance workflow? |
| **Cross-border transfer** | Section 16 | Restrictions on sending personalization data abroad | Cloud region requirements? |
| **Children's data** | Section 9 | Enhanced protection for minors' data | Family account implications? |

**Consent Framework:**

| Personalization Level | Data Used | Consent Required | Example |
|-----------------------|-----------|------------------|---------|
| **Basic** | Name, trip history | Booking consent | "Your upcoming trip details" |
| **Segment-based** | RFM score, persona | Opt-in profiling | "Travel packages matching your preferences" |
| **Behavioral** | Browsing, searches | Explicit opt-in | "Destinations you might like based on searches" |
| **Predictive** | CLV, churn prediction | Explicit opt-in with explanation | "We think you'd love..." |
| **Cross-channel** | Multi-channel behavior | Explicit opt-in per channel | "Consistent experience across WhatsApp and email" |

---

## Data Model Sketch

```typescript
// Research-level model — not final

interface PersonalizationEngine {
  engineId: string;
  agencyId: string;

  // Configuration
  models: PersonalizationModel[];
  rules: PersonalizationRule[];
  fallbackStrategy: FallbackStrategy;

  // State
  version: string;
  lastTrainedAt?: Date;
}

interface PersonalizationModel {
  modelId: string;
  name: string;
  type: ModelType;
  target: ModelTarget;

  // Training
  trainingDataFeatures: string[];
  trainingDataLabel?: string;
  lastTrainedAt?: Date;
  accuracy?: number;

  // Serving
  servingStrategy: 'batch' | 'realtime' | 'hybrid';
  cacheTTL: number; // seconds
}

type ModelType =
  | 'collaborative_filtering'
  | 'content_based'
  | 'hybrid_recommendation'
  | 'rule_based'
  | 'segment_default';

type ModelTarget =
  | 'destination'
  | 'hotel'
  | 'activity'
  | 'package'
  | 'pricing'
  | 'supplier';

interface PersonalizationRule {
  ruleId: string;
  name: string;
  priority: number;

  // Conditions
  conditions: SegmentCriteria[];
  segmentCode?: string;
  personaCode?: string;

  // Actions
  action: PersonalizationAction;
}

type PersonalizationAction =
  | { type: 'recommend'; items: string[]; reason: string }
  | { type: 'discount'; percentage: number; code?: string }
  | { type: 'upsell'; fromItem: string; toItem: string; incentive?: string }
  | { type: 'channel_message'; channel: string; templateId: string }
  | { type: 'feature_flag'; flag: string; value: boolean };

// --- Personalized Context ---

interface PersonalizationContext {
  customerId: string;

  // Snapshot at request time
  segmentAssignments: SegmentAssignment[];
  rfmScore: RFMScore;
  clvPrediction: CLVPrediction;
  activePersona: PersonaCard;

  // Behavioral signals
  recentSearches: SearchQuery[];
  recentViews: ViewedItem[];
  wishlist: WishlistItem[];

  // Festival context
  upcomingFestivals: FestivalTrigger[];

  // Consent
  personalizationConsent: ConsentLevel;
}

type ConsentLevel =
  | 'none'          // No personalization
  | 'basic'         // Name + booking history only
  | 'segment'       // Segment-based recommendations
  | 'behavioral'    // Full behavioral personalization
  | 'full';         // Predictive + cross-channel

// --- Personalized Output ---

interface PersonalizedRecommendation {
  customerId: string;
  generatedAt: Date;
  context: PersonalizationContext;

  // Recommendations
  destinations: PersonalizedItem[];
  packages: PersonalizedItem[];
  hotels: PersonalizedItem[];
  activities: PersonalizedItem[];

  // Pricing
  pricingAdjustments: PricingAdjustment[];

  // Channel content
  channelContent: Record<ChannelType, ChannelPersonalization>;
}

interface PersonalizedItem {
  itemId: string;
  type: 'destination' | 'package' | 'hotel' | 'activity';
  name: string;

  // Ranking
  score: number;          // 0-1 relevance
  reason: string;         // Why recommended (for display)
  model: string;          // Which model produced this

  // Segment match
  matchedSegments: string[];
  matchedPersona: string;

  // Festival relevance
  festivalRelevance?: FestivalTrigger;
}

interface PricingAdjustment {
  adjustmentId: string;
  type: 'discount' | 'premium' | 'value_add' | 'emi_option';
  amount: number;
  percentage: number;
  reason: string;
  applicableTo: string[]; // Item IDs

  // Conditions
  segmentCode: string;
  validFrom: Date;
  validTo: Date;
  maxUses?: number;
}

// --- Channel Personalization ---

interface ChannelPersonalization {
  channel: ChannelType;
  greetingStyle: 'formal' | 'casual' | 'hinglish' | 'regional';
  templateId?: string;
  dynamicBlocks: DynamicBlock[];
}

type ChannelType = 'whatsapp' | 'email' | 'in_app' | 'sms' | 'phone';

interface DynamicBlock {
  blockId: string;
  position: string; // 'hero' | 'body' | 'footer' | 'sidebar'
  content: string;
  fallbackContent: string;
  personalizationLevel: ConsentLevel;
}

// --- Festival Calendar ---

interface FestivalCalendar {
  year: number;
  agencyId: string;
  festivals: FestivalEntry[];
  updatedAt: Date;
}

interface FestivalEntry {
  festival: IndianFestival;
  startDate: Date;
  endDate: Date;

  // Personalization config
  promotionStartDate: Date;
  applicablePersonas: string[];
  recommendedDestinations: string[];
  specialPackages: string[];  // Package IDs

  // Historical data
  previousYearBookings: number;
  previousYearRevenue: number;
  averageGroupSize: number;
}

// --- Supplier Matching ---

interface SupplierCustomerMatch {
  matchId: string;
  customerId: string;
  supplierId: string;

  // Match scores
  overallScore: number;     // 0-1
  budgetMatch: number;
  styleMatch: number;
  qualityMatch: number;
  dietaryMatch: number;
  locationMatch: number;

  // History
  previousBookings: number;
  averageRating?: number;
  lastBookedAt?: Date;

  // Recommendation
  recommended: boolean;
  recommendationReason?: string;
}
```

---

## Open Problems

### 1. Cold-Start Personalization
**Challenge:** New customers have no behavioral data for recommendations

**Options:**
- Segment-default recommendations (all Budget Families see similar initial picks)
- Onboarding quiz to seed preferences
- Popular items in their segment as starting point
- Agent-driven initial personalization

**Research:** What is the minimum interaction needed before personalization outperforms defaults?

### 2. Festival Calendar Complexity
**Challenge:** Indian festivals follow lunar calendars and shift dates annually; regional festivals vary

**Options:**
- Maintain a master festival calendar updated annually
- Auto-generate from panchang (Hindu calendar) data
- Regional festival overlays by customer location
- Agent-configurable festival triggers

**Research:** How far in advance do customers book for festival travel?

### 3. WhatsApp Personalization Limits
**Challenge:** WhatsApp Business API has message template requirements and rate limits

**Options:**
- Template-based personalization with variable slots
- Interactive message buttons for preference collection
- Rich media cards for recommendations
- Conversation-based personalization within 24-hour window

**Research:** What personalization is possible within WhatsApp template constraints?

### 4. DPDP Act Compliance for Profiling
**Challenge:** The DPDP Act requires clear consent for profiling and automated decision-making

**Options:**
- Granular consent with personalization levels
- "Explain this recommendation" feature for transparency
- Easy opt-out of specific personalization types
- Audit trail of all personalization decisions

**Research:** What level of explanation satisfies DPDP "right to information"?

### 5. Personalization vs. Serendipity
**Challenge:** Over-personalization creates filter bubbles; customers may want surprise recommendations

**Options:**
- Inject "explore" recommendations (20% non-targeted)
- Segment-crossing suggestions ("You usually book hill stations, try a beach!")
- Seasonal novelty boost (new destinations get a discovery boost)

**Research:** Optimal ratio of targeted vs. exploratory recommendations?

### 6. Price Sensitivity Detection
**Challenge:** Dynamically detecting when a customer is price-sensitive vs. value-sensitive

**Options:**
- Track price comparison behavior
- Monitor negotiation patterns with agents
- Analyze discount usage frequency
- Segment-level price elasticity models

**Research:** How to distinguish between price sensitivity and budget constraint?

---

## Next Steps

1. Build festival calendar data source for 2026-2028
2. Design consent UX for personalization levels (DPDP compliant)
3. Implement segment-default recommendation rules
4. Prototype WhatsApp personalized message templates
5. Create supplier-customer matching score model
6. Design "explain this recommendation" transparency feature
7. Test dynamic pricing thresholds per segment
8. Map personalization data flows for DPDP data minimization audit
9. Build A/B testing framework for recommendation strategies

---

**Series:** [Customer Segmentation & Personalization](./SEGMENT_MASTER_INDEX.md)
**Previous:** [SEGMENT_01_PROFILES.md](./SEGMENT_01_PROFILES.md) — Customer Profiles & Models
**Next:** [SEGMENT_03_COMMUNICATION.md](./SEGMENT_03_COMMUNICATION.md) — Segment-Based Communication
