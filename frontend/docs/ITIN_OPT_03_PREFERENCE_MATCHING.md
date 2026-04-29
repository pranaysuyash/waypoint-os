# Travel Itinerary Optimization — Preference Matching

> Research document for traveler preference extraction, profile-based scoring, group reconciliation, learning from past trips, and India-specific preferences.

---

## Key Questions

1. **How do we extract and model traveler preferences from inquiry data?**
2. **How do we score itinerary options against traveler profiles?**
3. **How do we reconcile conflicting preferences in group travel?**
4. **What India-specific preferences must the system understand?**

---

## Research Areas

### Preference Extraction Pipeline

```typescript
interface PreferenceExtractor {
  extractFromInquiry(raw_input: string, packet: CanonicalPacket): TravelerPreferences;
  extractFromHistory(trips: PastTrip[]): PreferenceLearning;
  extractFromBehavior(interactions: CustomerInteraction[]): PreferenceSignal;
}

interface TravelerPreferences {
  // Core
  pace: "RELAXED" | "MODERATE" | "PACKED";
  interests: InterestCategory[];
  budget_sensitivity: "PRICE_FIRST" | "VALUE_SEEKER" | "QUALITY_FIRST" | "LUXURY";

  // Travel style
  accommodation_preference: "HOSTEL" | "BUDGET_HOTEL" | "MID_RANGE" | "PREMIUM" | "LUXURY" | "HERITAGE" | "HOMESTAY";
  dining_preference: "STREET_FOOD" | "LOCAL_RESTAURANTS" | "FINE_DINING" | "HOTEL_MEALS" | "COOK_OWN";
  transport_preference: "PUBLIC" | "PRIVATE_CAR" | "MIXED" | "SELF_DRIVE";

  // Social
  travel_companion: "SOLO" | "COUPLE" | "FAMILY_WITH_KIDS" | "FAMILY_WITH_ELDERLY" | "FRIENDS" | "CORPORATE_GROUP";
  social_style: "MEET_LOCALS" | "FELLOW_TRAVELERS" | "PRIVATE" | "GUIDED_GROUPS";

  // Activities
  activity_intensity: "LIGHT" | "MODERATE" | "ADVENTUROUS" | "EXTREME";
  must_do: string[];                   // specific activities/experiences
  must_avoid: string[];                // deal-breakers
  novelty_preference: "COMFORT_ZONE" | "MODERATELY_NEW" | "ADVENTUROUS" | "EXTREMELY_NOVEL";

  // Practical
  dietary: DietaryPreference[];
  accessibility: string[];
  language_comfort: string[];
  photography_interest: "CASUAL" | "ENTHUSIAST" | "PROFESSIONAL";

  // India-specific
  religious_preferences: string[];     // vegetarian near temples, no beef, etc.
  festival_interest: boolean;
  shopping_interest: "NONE" | "CASUAL" | "SERIOUS";
  family_friendliness_required: boolean;
}

type InterestCategory =
  | "BEACH" | "MOUNTAINS" | "CULTURE" | "HISTORY" | "ADVENTURE"
  | "WILDLIFE" | "PHOTOGRAPHY" | "FOOD" | "NIGHTLIFE" | "WELLNESS"
  | "RELIGIOUS" | "ARCHITECTURE" | "ART" | "NATURE" | "SPORTS"
  | "SHOPPING" | "LOCAL_LIFE" | "LUXURY" | "ROMANCE";

type DietaryPreference =
  | "VEGETARIAN" | "NON_VEGETARIAN" | "VEGAN" | "JAIN"
  | "EGGETARIAN" | "HALAL" | "KOSHER" | "GLUTEN_FREE"
  | "NO_BEEF" | "NO_PORK";

// ── Preference extraction from inquiry ──
// ┌─────────────────────────────────────────┐
// │  Raw: "We're a couple looking for a      │
// │  relaxed beach holiday in Goa. 5 days.   │
// │  Budget around 40k total. Vegetarian.    │
// │  Want to avoid crowded places."          │
// │                                           │
// │  Extracted preferences:                   │
// │  - companions: COUPLE                     │
// │  - pace: RELAXED                          │
// │  - interests: [BEACH]                     │
// │  - destination: Goa                       │
// │  - duration: 5 days                       │
// │  - budget: ₹40K total (value seeker)     │
// │  - dietary: VEGETARIAN                    │
// │  - social: PRIVATE (avoid crowded)        │
// │  - accommodation: MID_RANGE (from budget) │
// │                                           │
// │  Confidence: 0.85                         │
// │  Missing: hotel preference, transport     │
// └───────────────────────────────────────────┘
```

### Profile-Based Scoring

```typescript
interface ItineraryScorer {
  scoreItinerary(itinerary: ProposedItinerary, preferences: TravelerPreferences): ItineraryScore;
  rankOptions(options: ProposedItinerary[], preferences: TravelerPreferences): RankedItinerary[];
}

interface ItineraryScore {
  overall: number;                     // 0-100
  breakdown: {
    interest_match: number;            // do activities match interests?
    pace_match: number;                // is daily schedule right pace?
    budget_match: number;              // within budget expectations?
    style_match: number;               // accommodation, dining, transport?
    practicality: number;              // dietary, accessibility, language?
    novelty_match: number;             // new experiences vs comfort zone?
    india_specific: number;            // religious, family, festival fit?
  };
  highlights: string[];                // what's great about this option
  concerns: string[];                  // potential mismatches
}

// ── Scoring visualization ──
// ┌─────────────────────────────────────────────────────┐
// │  Itinerary Option A: Goa Beach Getaway                │
// │                                                       │
// │  Overall Score: 87/100                                │
// │                                                       │
// │  Interest match    ████████████████████░░ 92%        │
// │  Pace match        █████████████████░░░░ 78%         │
// │  Budget match      ██████████████████████ 95%        │
// │  Style match       ██████████████████░░░░ 85%        │
// │  Practicality      ██████████████████████ 98%        │
// │  Novelty           ████████████████░░░░░░ 72%        │
// │  India-specific    ██████████████████████ 95%        │
// │                                                       │
// │  Highlights:                                          │
// │  ✅ Perfect beach + vegetarian restaurant options     │
// │  ✅ Well within ₹40K budget (₹37,500)               │
// │  ✅ Private beach resort (avoids crowds)             │
// │                                                       │
// │  Concerns:                                            │
// │  ⚠️ Day 3 might be too packed (3 activities)         │
// │  ⚠️ Limited new experiences for repeat Goa visitors  │
// └─────────────────────────────────────────────────────┘
```

### Group Preference Reconciliation

```typescript
interface GroupPreferenceReconciler {
  reconcile(members: TravelerPreferences[]): GroupPreferences;
  findConflicts(members: TravelerPreferences[]): PreferenceConflict[];
  suggestCompromises(conflicts: PreferenceConflict[]): Compromise[];
}

interface GroupPreferences {
  // Agreed
  common_interests: InterestCategory[];
  compatible_pace: "RELAXED" | "MODERATE" | "PACKED";
  dietary_union: DietaryPreference[];  // everyone can eat
  budget_range: BudgetRange;

  // Compromised
  conflicts: PreferenceConflict[];
  compromises: Compromise[];
}

interface PreferenceConflict {
  dimension: string;
  member_preferences: { member_id: string; preference: string }[];
  severity: "MINOR" | "MODERATE" | "MAJOR";
}

interface Compromise {
  conflict: string;
  solution: string;
  trade_off: string;

  // Example: "Split day - morning adventure for thrill-seekers,
  //           afternoon beach for relaxation-seekers"
}

// ── Group reconciliation example ──
// ┌─────────────────────────────────────────────────────┐
// │  Family of 4: Dad, Mom, Teen (16), Grandma (68)     │
// │                                                       │
// │  Dad:   ADVENTURE, NON_VEG, MODERATE pace            │
// │  Mom:   CULTURE, VEGETARIAN, RELAXED pace            │
// │  Teen:  BEACH, ADVENTURE, PACKED pace                │
// │  Grandma: RELIGIOUS, JAIN, RELAXED pace              │
// │                                                       │
// │  Conflicts:                                           │
// │  🔴 Dietary: Non-veg vs Vegetarian vs Jain           │
// │  🟡 Pace: Packed vs Relaxed                          │
// │  🟡 Interests: Adventure vs Religious                │
// │                                                       │
// │  Compromises:                                         │
// │  1. Jain-friendly restaurants (everyone can eat)     │
// │  2. Moderate pace with rest afternoons (grandma)     │
// │  3. Day split: AM adventure (dad+teen)               │
// │              AM temple (mom+grandma)                  │
// │              PM family activity together              │
// │  4. One beach day + one temple day                   │
// └─────────────────────────────────────────────────────┘
```

### Learning from Past Trips

```typescript
interface PreferenceLearner {
  learnFromTrip(trip: CompletedTrip, feedback: TripFeedback): PreferenceUpdate;
  getLearnedPreferences(customer_id: string): LearnedPreferences;
}

interface LearnedPreferences {
  customer_id: string;
  inferred_interests: { interest: string; confidence: number }[];
  avoided_activities: string[];        // booked but skipped/declined
  enjoyed_activities: string[];        // rated highly
  pace_preference_actual: string;       // inferred from behavior
  hotel_preference_actual: string;
  spending_pattern: string;
}

// ── Learning signals ──
// ┌─────────────────────────────────────────┐
// │  Signal                    | Learning    │
// │  ─────────────────────────────────────── │
// │  Skipped paid activity     | Remove interest │
// │  Extended stay at location | Increase interest│
// │  Replaced hotel restaurant | Prefer local food│
// │  Added extra rest day      | Prefer relaxed   │
// │  Spent extra on shopping   | Budget flexible  │
// │  Left negative review      | Avoid similar    │
// │  Rebooked same destination | Strong interest  │
// └───────────────────────────────────────────┘
```

### India-Specific Preferences

```typescript
// ── India-specific preference handling ──
// ┌─────────────────────────────────────────┐
// │  Category            | Consideration      │
// │  ─────────────────────────────────────── │
// │  Religious          │ Temple timings,    │
// │                     │ dress codes,       │
// │                     │ food restrictions  │
// │                     │ near holy sites    │
// │                                           │
// │  Dietary            │ Vegetarian majority│
// │                     │ Jain restrictions  │
// │                     │ Regional cuisine   │
// │                     │ spice levels       │
// │                                           │
// │  Seasonal           │ Festival dates     │
// │                     │ School holidays    │
// │                     │ Wedding season     │
// │                     │ Monsoon avoidance  │
// │                                           │
// │  Family             │ Multi-gen trips    │
// │                     │ Kids' activities   │
// │                     │ Elderly comfort    │
// │                     │ Family rooms       │
// │                                           │
// │  Social             │ Group travel norm  │
// │                     │ Photo opportunities│
// │                     │ WhatsApp sharing   │
// │                     │ Shopping for gifts │
// │                                           │
// │  Transport          │ Train preference   │
// │                     │ AC required        │
// │                     │ Driver preferences │
// │                     │ Flight meal types  │
// └───────────────────────────────────────────┘
```

---

## Open Problems

1. **Implicit preference inference** — Customers often can't articulate preferences. The system must infer from indirect signals (time spent on certain pages, types of questions asked).

2. **Preference drift** — Customer preferences change over time (post-marriage, with kids, after a bad experience). Learning must decay old data and weight recent signals.

3. **Group decision fatigue** — Asking 5 group members to rate 20 activity options is exhausting. Need smart sampling to infer group preferences from minimal input.

4. **Cultural sensitivity** — Some preferences (caste-based dining, gender-specific activities) are culturally sensitive. The system must handle these gracefully without being insensitive.

---

## Next Steps

- [ ] Build preference extraction from natural language inquiry parsing
- [ ] Implement multi-criteria itinerary scoring engine
- [ ] Create group preference reconciliation algorithm
- [ ] Design preference learning pipeline from trip history
- [ ] Build India-specific preference knowledge base
