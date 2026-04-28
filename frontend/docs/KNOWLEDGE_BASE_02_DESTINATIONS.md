# Knowledge Base & Internal Wiki — Destination Intelligence

> Research document for destination data management, travel intelligence, and location-specific knowledge.

---

## Key Questions

1. **What destination data do agents need at their fingertips?**
2. **How do we structure destination intelligence for quick access?**
3. **What's the data sourcing model for destination information?**
4. **How do we handle seasonal and real-time destination changes?**
5. **How do agents access destination info during trip building?**

---

## Research Areas

### Destination Data Model

```typescript
interface Destination {
  destinationId: string;
  name: string;
  country: string;
  region: string;
  type: 'city' | 'region' | 'country' | 'island' | 'resort_area';
  coordinates: { lat: number; lng: number };
  timezone: string;
  language: string[];
  currency: string;
  population?: number;
  altitude?: number;
  climate: ClimateInfo;
  intelligence: DestinationIntelligence;
}

interface DestinationIntelligence {
  // Travel logistics
  airports: AirportInfo[];
  ports?: PortInfo[];
  trainStations?: StationInfo[];
  drivingFrom?: DrivingInfo[];

  // Travel requirements
  visa: VisaRequirement;
  vaccinations: VaccinationInfo[];
  travelAdvisory: AdvisoryLevel;

  // Local intelligence
  culture: CultureInfo;
  cuisine: CuisineInfo;
  customs: CustomInfo[];
  tippingGuide: string;
  dressCode: string;
  languagePhrases: PhraseEntry[];

  // Practical info
  electricityPlug: string;
  drinkingWaterSafe: boolean;
  internetConnectivity: string;
  atmAvailability: string;
  cardAcceptance: string;
  simCardAvailability: string;

  // Agent-specific
  preferredHotels: AgentRecommended[];
  preferredActivities: AgentRecommended[];
  hiddenGems: HiddenGem[];
  commonPitfalls: string[];
  customerFavorites: string[];
}

// Example: Singapore destination intelligence
// Airports: Changi (SIN), Seletar (XSP)
// Visa: Indian citizens — e-Visa or Visa-Free (30 days) depending on passport type
// Language: English, Mandarin, Malay, Tamil
// Currency: SGD (1 SGD ≈ ₹62)
// Tipping: Not expected (10% service charge at restaurants)
// Card acceptance: Excellent (even hawker centers accept cards)
// SIM: Changi recommends SIM at airport, ~$12 for 100GB
// Hidden gem: MacRitchie Treetop Walk (free, morning only)
// Common pitfall: No chewing gum, durian banned on public transport
// Customer favorite: Marina Bay Sands light show (free, 8PM/9PM)
```

### Seasonal Intelligence

```typescript
interface SeasonalIntelligence {
  destination: string;
  seasons: SeasonInfo[];
  events: SeasonalEvent[];
  pricePatterns: PricePattern[];
}

interface SeasonInfo {
  name: string;                      // "Peak Season", "Monsoon", "Shoulder"
  months: number[];
  weather: string;
  avgTempHigh: number;
  avgTempLow: number;
  rainfall: string;
  crowdLevel: 'low' | 'moderate' | 'high' | 'very_high';
  priceLevel: 'budget' | 'moderate' | 'high' | 'premium';
  recommendation: string;
}

interface SeasonalEvent {
  name: string;
  date: string;                      // Fixed or floating date description
  type: 'festival' | 'holiday' | 'sports' | 'conference' | 'natural';
  impactOnTravel: 'positive' | 'negative' | 'neutral';
  priceImpact: string;               // "Hotels 2x more expensive"
  notes: string;
}

// Seasonal intelligence examples:
// Singapore:
//   Peak: Dec-Jan (year-end, Christmas, New Year) — Prices +30%
//   Shoulder: Feb-Apr (post-holiday, good weather) — Best value
//   Hot: May-Jul (hot, humid, occasional rain) — Prices normal
//   Events: Chinese New Year (Jan/Feb), Great Singapore Sale (Jun-Aug),
//           F1 Night Race (Sep), Deepavali (Oct/Nov)
//
// Goa (India):
//   Peak: Nov-Feb (pleasant weather, tourist season) — Prices +50%
//   Shoulder: Oct, Mar (transitional) — Good value
//   Off-season: Apr-Sep (hot, monsoon) — Prices -40%, many restaurants closed
//   Events: Carnival (Feb), Sunburn Festival (Dec), Ganesh Chaturthi (Sep)

// Price patterns:
// When an agent selects travel dates, system shows:
// "Traveling in December (peak season). Expect hotel prices ~30% higher than usual.
//  Consider January for 20% savings with similar weather."
```

### In-Context Destination Access

```typescript
interface DestinationAccess {
  // Where destination info appears in the workbench
  accessPoints: AccessPoint[];
}

type AccessPoint =
  | { location: 'intake_panel'; trigger: 'destination_detected' }
  | { location: 'trip_builder'; trigger: 'add_destination' }
  | { location: 'activity_search'; trigger: 'search_activities' }
  | { location: 'hotel_search'; trigger: 'search_hotels' }
  | { location: 'customer_chat'; trigger: 'customer_question' }
  | { location: 'quick_reference'; trigger: 'agent_search' };

// In-context surfacing examples:
//
// Agent adds Singapore to itinerary:
// → Sidebar shows Singapore quick card:
//   "Singapore | +08:00 SGT (2.5 hrs ahead)
//    Best time: Feb-Apr | Current weather: 32°C, partly cloudy
//    Visa: e-Visa for Indians (48hr processing)
//    Currency: SGD (₹62 = 1 SGD)
//    [Full Guide] [Visa Details] [Hotels] [Activities]"
//
// Customer asks "Is it safe to drink the tap water?":
// → Agent sees in the quick reference: "Tap water: Safe to drink"
// → Agent responds immediately without research
//
// Agent searches for hotels:
// → Knowledge base shows: "Recommended areas for families: Sentosa, Orchard Road"
// → "Avoid Geylang area for family travelers"
```

---

## Open Problems

1. **Data freshness** — Visa rules change without notice. The platform could provide outdated visa info, leading to customer issues. Need clear disclaimers and sourcing.

2. **Scale** — Covering 500+ destinations with quality intelligence is a massive content operation. Need AI-assisted content generation with human review.

3. **Conflicting information** — Different sources say different things (best time to visit Bali varies by source). Need curated, authoritative content.

4. **Personalization** — A family's Singapore guide differs from a solo traveler's. Need segment-specific recommendations, not generic guides.

5. **Competitive intelligence** — Agents need to know what competitors charge for similar trips. Sourcing competitor pricing is ethically complex.

---

## Next Steps

- [ ] Design destination intelligence data model
- [ ] Build seasonal intelligence with pricing patterns
- [ ] Create in-context destination access points in workbench
- [ ] Design AI-assisted destination guide generation
- [ ] Study destination databases (Lonely Planet API, Google Travel, TripAdvisor)
