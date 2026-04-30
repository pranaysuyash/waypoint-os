# Travel Quiz & Destination Discovery — Interactive Matching Engine

> Research document for travel personality quizzes, destination matching algorithms, interactive discovery tools, and gamified destination selection for the Waypoint OS platform.

---

## Key Questions

1. **How do we help undecided customers discover their ideal destination?**
2. **What quiz formats work for travel personality matching?**
3. **How does destination matching use quiz results and behavioral data?**
4. **How do quizzes drive engagement and lead generation?**

---

## Research Areas

### Travel Personality Quiz Engine

```typescript
interface TravelQuizDiscovery {
  // Interactive destination discovery through quizzes and matching
  quiz_types: {
    TRAVEL_PERSONALITY: {
      description: "Discover your travel personality type";
      questions: [
        { q: "Your ideal morning on vacation?", options: ["Beach sunrise with coffee", "Exploring a local market", "Sleeping in, then brunch", "Hiking a scenic trail"] },
        { q: "You have a free evening. You...", options: ["Find the best local restaurant", "Visit a museum or gallery", "Hit the nightlife district", "Relax at the hotel spa"] },
        { q: "Your travel dealbreaker?", options: ["Bad food options", "No WiFi", "Crowded tourist traps", "Dirty hotel room"] },
        { q: "Budget approach?", options: ["Spare no expense", "Value for money", "Budget-friendly", "Mix of splurge and save"] },
        { q: "Your travel photo style?", options: ["Landscapes and nature", "Street photography and culture", "Selfies and group photos", "Food photography"] },
        { q: "Ideal travel companion?", options: ["Partner/spouse", "Family with kids", "Friends group", "Solo — just me"] },
      ];
      personality_types: {
        BEACH_BUM: { match: "Maldives, Bali, Phuket, Goa", tagline: "You chase sunsets, not schedules" },
        CULTURE_VULTURE: { match: "Japan, Europe, Istanbul, Egypt", tagline: "You travel to understand, not just see" },
        ADVENTURE_SEEKER: { match: "New Zealand, Switzerland, Iceland, Ladakh", tagline: "Your comfort zone is just a starting point" },
        FOOD_EXPLORER: { match: "Thailand, Italy, Japan, Mexico", tagline: "You book trips around restaurants, not attractions" },
        FAMILY_PLANNER: { match: "Singapore, Dubai, Thailand, Mauritius", tagline: "The best trips are the ones everyone enjoys" },
        LUXURY_LOVER: { match: "Maldives, Swiss Alps, Bora Bora, Dubai", tagline: "Why settle for good when you can have extraordinary" },
      };
    };

    DESTINATION_MATCHMAKER: {
      description: "Match customers to specific destinations based on preferences";
      inputs: {
        budget: "Slider: ₹30K - ₹5L per person";
        duration: "3-15 days";
        season: "When are you planning to travel?";
        vibe: "Select 3 from: Beach, Mountains, City, Culture, Adventure, Relaxation, Food, Shopping, Nightlife, Nature, Romance, Family";
        travelers: "Solo, Couple, Family, Friends, Group";
        dietary: "Any dietary requirements?";
      };
      output: {
        top_3_matches: "Ranked destinations with match percentage and reasoning";
        match_reasoning: "'Singapore matches 87% because: family-friendly (95%), within budget (90%), culture + food focus (85%)'";
        alternative: "'If you could stretch budget by ₹20K, Japan would be a 92% match'";
        cta: "'Let's plan your {destination} trip' → inquiry with quiz results attached";
      };
    };

    TRIP_VIBE_CHECK: {
      description: "Quick 3-question quiz for returning visitors";
      questions: [
        "Beach or mountains?",
        "Street food or fine dining?",
        "Packed itinerary or free time?"
      ];
      output: "Instant destination suggestion with one-tap inquiry";
      placement: "Website homepage, Instagram story, companion app home screen";
    };
  };

  // ── Quiz result page ──
  // ┌─────────────────────────────────────────────────────┐
  // │  🎉 Your Travel Personality: Culture Vulture               │
  // │                                                       │
  // │  "You travel to understand, not just see."              │
  // │                                                       │
  // │  Your top destinations:                               │
  // │  🇯🇵 Japan · 94% match                                   │
  // │     Ancient temples, bullet trains, world-class food     │
  // │     7 days from ₹1.8L per person                         │
  // │     [Plan My Japan Trip]                                  │
  // │                                                       │
  // │  🇹🇷 Turkey · 89% match                                  │
  // │     Where Europe meets Asia, history meets hospitality   │
  // │     6 days from ₹1.2L per person                         │
  // │     [Plan My Turkey Trip]                                 │
  // │                                                       │
  // │  🇪🇬 Egypt · 85% match                                   │
  // │     Pyramids, Nile cruises, ancient wonders              │
  // │     5 days from ₹95K per person                          │
  // │     [Plan My Egypt Trip]                                  │
  // │                                                       │
  // │  📊 Share your result:                                    │
  // │  [WhatsApp] [Instagram Story] [Save to Profile]           │
  // └─────────────────────────────────────────────────────┘
}
```

### Destination Matching Algorithm

```typescript
interface DestinationMatching {
  // Algorithm for matching customers to destinations
  matching_engine: {
    INPUT_WEIGHTS: {
      budget: 25;
      travel_style: 25;
      travelers_composition: 15;
      dietary_needs: 10;
      season: 15;
      past_trips: 10;
    };

    DESTINATION_VECTORS: {
      description: "Each destination scored across multiple dimensions";
      dimensions: [
        "beach_score", "mountain_score", "city_score", "culture_score",
        "adventure_score", "relaxation_score", "food_score", "shopping_score",
        "nightlife_score", "nature_score", "romance_score", "family_score",
        "budget_accessibility", "vegetarian_friendly", "safety_rating",
        "indian_food_availability", "english_speaking", "flight_accessibility"
      ];
      example: {
        singapore: { family: 95, culture: 75, food: 90, shopping: 85, budget: 60, veg_food: 80, safety: 95 },
        bali: { beach: 90, nature: 85, relaxation: 90, budget: 85, romance: 80, family: 70 },
        japan: { culture: 95, food: 95, adventure: 70, shopping: 80, budget: 40, family: 65 },
      };
    };

    MATCHING_LOGIC: {
      step_1: "Convert customer answers to preference vector";
      step_2: "Calculate cosine similarity between customer vector and each destination vector";
      step_3: "Filter by hard constraints (budget ceiling, visa difficulty, flight availability)";
      step_4: "Boost destinations not yet visited (novelty factor)";
      step_5: "Return top 3 matches with match percentage and reasoning";
    };
  };
}
```

### Quiz as Lead Generation

```typescript
interface QuizLeadGeneration {
  // How quizzes drive customer acquisition
  lead_capture: {
    BEFORE_RESULTS: {
      description: "Capture email/phone before showing full results";
      mechanism: "Show personality type for free; top 3 destinations require email or phone number";
      conversion: "60-70% of quiz-takers provide contact info to see results";
    };

    POST_QUIZ_FUNNEL: {
      flow: [
        "Quiz completed → results shown with top destinations",
        "WhatsApp message: 'Your Japan match was 94%! Want me to plan this trip?'",
        "Email with detailed destination guide based on quiz results",
        "Retargeting ad: Japan package specifically for this customer",
        "Agent follow-up within 24 hours with personalized proposal",
      ];
      conversion_rate: "8-12% of quiz-takers convert to inquiry (vs. 3-5% generic landing page)";
    };
  };

  social_sharing: {
    VIRAL_LOOP: {
      mechanism: "'I'm a Culture Vulture! Take the travel personality quiz → [link]'";
      effect: "Each shared quiz result generates 5-15 new quiz attempts";
      tracking: "Referral link embedded in shared quiz results";
    };
  };

  engagement_metrics: {
    quiz_completion_rate: "Target: 70%+ (who start, finish)";
    result_share_rate: "Target: 15-20% share their results",
    lead_capture_rate: "Target: 60%+ provide contact for full results",
    inquiry_conversion: "Target: 8-12% quiz-takers become inquiries",
    cost_per_lead: "₹20-50 per qualified lead (cheaper than paid ads)";
  };
}
```

---

## Open Problems

1. **Quiz fatigue** — Overly long quizzes (10+ questions) have 40%+ abandonment. Need to keep quizzes under 6 questions or use progressive disclosure (3 quick questions → results → optional deeper quiz).

2. **Match accuracy** — A quiz that recommends Japan to someone who can't afford it erodes trust. Hard budget and logistics constraints must filter before scoring.

3. **Cultural bias** — Quiz questions designed for Western travelers may not resonate with Indian travelers. Questions and personality types must be culturally relevant.

4. **Data freshness** — Destination scores (safety, budget accessibility, flight availability) change over time. Need regular updates to keep matching results accurate.

5. **Post-quiz engagement** — Most quiz-takers view results and leave. Converting quiz-takers to inquiries requires immediate, personalized follow-up within minutes.

---

## Next Steps

- [ ] Build travel personality quiz with 6 personality types
- [ ] Create destination matching algorithm with multi-dimensional scoring
- [ ] Implement lead capture flow integrated with quiz results
- [ ] Design quiz sharing mechanics for viral distribution
- [ ] Build quiz analytics with completion and conversion tracking
