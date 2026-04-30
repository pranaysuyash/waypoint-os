# AI Itinerary Generation — Preference-to-Plan Engine

> Research document for AI-powered itinerary generation, transforming customer preference profiles into complete day-by-day travel plans with activity selection, time allocation, logistics optimization, and real-time adaptation for the Waypoint OS platform.

---

## Key Questions

1. **How does AI generate a complete itinerary from customer preferences?**
2. **What data inputs drive personalized activity selection?**
3. **How are logistics (transfers, meals, rest) optimized across days?**
4. **How does the itinerary adapt to real-time changes during the trip?**

---

## Research Areas

### AI Itinerary Generation Pipeline

```typescript
interface AIItineraryGenerator {
  // Transform customer profile → complete day-by-day itinerary
  generation_pipeline: {
    INPUT_LAYER: {
      description: "All data sources feeding into itinerary generation";
      inputs: {
        customer_profile: {
          demographics: "Age, family composition, travel party size, mobility needs";
          travel_history: "Past trips, destinations visited, activities completed";
          stated_preferences: "Beach vs mountain, adventure vs relaxation, culture vs nightlife";
          budget_range: "Total budget, daily spending comfort, luxury vs value preference";
          dietary: "Vegetarian, vegan, halal, allergies, spice tolerance";
          pace: "Packed schedule vs leisurely — activities per day preference";
        };

        destination_intelligence: {
          seasonal_factors: "Weather, crowd levels, festivals, closures, pricing";
          logistics: "Airport transfers, inter-city distances, visa checkpoints";
          local_knowledge: "Restaurant recommendations, hidden gems, tourist traps to avoid";
          safety: "Area safety ratings, scam warnings, health advisories";
          operating_hours: "Attraction hours, restaurant meal times, transport schedules";
        };

        supplier_inventory: {
          available_activities: "Bookable activities with real-time availability and pricing";
          hotel_options: "Room types, amenities, locations with live rates";
          transfer_options: "Private car, shared shuttle, public transport with duration/cost";
          restaurant_options: "Cuisine types, price ranges, reservation availability";
        };
      };
    };

    GENERATION_ENGINE: {
      description: "Multi-stage AI pipeline producing the itinerary";
      stages: {
        STAGE_1_CONSTRAINT_SOLVER: {
          description: "Determine feasible trip skeleton from hard constraints";
          inputs: "Dates, budget, destination, group size, visa validity";
          output: "Arrival/departure times, hotel nights, daily budget allocation";
          method: "Constraint satisfaction with optimization (flight arrival → hotel check-in → activity windows)";
        };

        STAGE_2_PREFERENCE_MATCHING: {
          description: "Score all available activities against customer preferences";
          method: "Embedding similarity between customer preference vector and activity vectors";
          scoring: {
            interest_match: "How well activity aligns with stated interests (0-1 score)";
            demographic_fit: "Age/family appropriateness (e.g., nightclub not for family with kids)";
            novelty_factor: "New experience vs repeat of past trips";
            seasonal_quality: "Is this the right time of year for this activity?";
            social_proof: "Rating and review sentiment from similar travelers";
          };
        };

        STAGE_3_SCHEDULE_OPTIMIZER: {
          description: "Arrange scored activities into optimal daily schedule";
          constraints: {
            geography: "Cluster activities by location to minimize travel time";
            energy_curve: "High-energy activities in morning, relaxed in afternoon";
            meal_windows: "Lunch 12-2 PM, dinner 7-9 PM in local cuisine areas";
            rest_periods: "Free time blocks every 2-3 days for spontaneity";
            opening_hours: "Activities only during operating hours";
            travel_time: "Buffer between geographically distant activities";
          };
          optimization_target: "Maximize preference satisfaction score within time and budget constraints";
        };

        STAGE_4_LOGISTICS_PLANNER: {
          description: "Add transfer, meal, and contingency logistics";
          additions: {
            airport_transfers: "Pickup on arrival, drop-off on departure, mode and timing";
            inter_activity_transit: "Walking time, taxi cost, public transport options";
            meal_planning: "Restaurant reservations or food court recommendations near activities";
            contingency: "Rainy day alternatives for outdoor activities";
            buffer_time: "30-min buffer between distant activities, 1-hour buffer for flights";
          };
        };

        STAGE_5_HUMAN_REVIEW: {
          description: "Agent review and refinement of AI-generated itinerary";
          agent_actions: [
            "Review AI itinerary for cultural sensitivity and appropriateness",
            "Adjust pacing based on personal knowledge of customer",
            "Add insider tips and local recommendations AI may miss",
            "Flag any logistical risks (tight connections, unreliable transport)",
            "Approve or request regeneration of specific days",
          ];
          turn_around: "AI generates in 30 seconds → agent reviews in 5-10 minutes";
        };
      };
    };
  };

  // ── AI itinerary generation — agent view ──
  // ┌─────────────────────────────────────────────────────┐
  // │  AI Itinerary Generator · Singapore 5D/4N                │
  // │  Customer: Sharma Family (2A, 1C age 8)                  │
  // │                                                       │
  // │  Customer Profile:                                     │
  // │  🎯 Interests: Culture · Nature · Food                    │
  // │  👨‍👩‍👦 Pace: Moderate (3-4 activities/day)                   │
  // │  💰 Budget: ₹1.2L total · ₹24K/day                        │
  // │  🥗 Diet: Vegetarian · Medium spice                       │
  // │  ♿ Mobility: Child stroller access needed                │
  // │                                                       │
  // │  Generated Itinerary:                                  │
  // │  ┌─ Day 1: Arrival & Marina Bay ────────────────────┐   │
  // │  │  2:00 PM  Airport pickup (private car)           │   │
  // │  │  3:30 PM  Hotel check-in · Grand Mercure         │   │
  // │  │  5:00 PM  Gardens by the Bay (free entry)        │   │
  // │  │  7:30 PM  Dinner at Komala Vilas (Indian veg)    │   │
  // │  │  Budget: ₹8K (transfer + dinner)                 │   │
  // │  └──────────────────────────────────────────────────┘   │
  // │  ┌─ Day 2: Culture & Heritage ─────────────────────┐   │
  // │  │  9:00 AM  Breakfast at hotel (included)          │   │
  // │  │  10:00 AM Little India & Sri Veeramakaliamman    │   │
  // │  │  12:30 PM Lunch at Banana Leaf Apolo             │   │
  // │  │  2:00 PM  National Museum of Singapore           │   │
  // │  │  5:00 PM  Clarke Quay walk + river cruise        │   │
  // │  │  7:30 PM  Dinner at Satay by the Bay             │   │
  // │  │  Budget: ₹5K (activities + meals)                │   │
  // │  └──────────────────────────────────────────────────┘   │
  // │  [Days 3-5 generated similarly]                        │
  // │                                                       │
  // │  AI Confidence: 87% · Agent review needed              │
  // │  [Approve All] [Edit Days] [Regenerate] [Send to Cust]  │
  // └─────────────────────────────────────────────────────────┘
}

### Customer Preference Profiling

```typescript
interface CustomerPreferenceProfile {
  // How customer preferences are captured and refined
  profiling_methods: {
    EXPLICIT_COLLECTION: {
      description: "Direct preference input from customer";
      methods: {
        intake_form: "Structured questionnaire during trip planning (travel style, interests, budget)";
        trip_briefing: "Agent conducts verbal preference interview (recorded + transcribed)";
        preference_cards: "Visual preference selection — tap images of liked activities";
        must_have_list: "Customer specifies non-negotiable items ('must see Marina Bay Sands')";
      };
    };

    BEHAVIORAL_INFERENCE: {
      description: "Inferred preferences from past behavior";
      signals: {
        past_trips: "Activities booked on previous trips indicate preference patterns";
        browsing_history: "Which destinations/activities customer viewed longest on website/app";
        search_queries: "What customer searched for ('family-friendly activities Singapore')";
        past_feedback: "Post-trip ratings indicate what worked and what didn't";
        abandonment: "Which activities were removed from draft itinerary (didn't want)";
      };
    };

    SIMILAR_TRAVELER_MODELING: {
      description: "Use similar travelers' preferences to fill gaps";
      method: "Collaborative filtering — travelers with similar demographics and trip history";
      use_case: "First-time customer with limited history → suggest what similar families enjoyed";
      caution: "Never assume — use as suggestions, not defaults; always confirm with customer";
    };

    PREFERENCE_REFINEMENT: {
      description: "Preferences get more accurate with each trip";
      feedback_loop: [
        "Trip 1: Broad preferences (beach, culture, food)",
        "Trip 2: Refined (culture → temples, food → street food, no adventure sports)",
        "Trip 3: Precise (Buddhist temples, hawker centres, prefers mornings for activities)",
        "Trip 4+: Predictive (suggest new destinations matching evolved taste profile)",
      ];
    };
  };

  // ── Preference card UI ──
  // ┌─────────────────────────────────────────────────────┐
  // │  Tell us what you love!                                  │
  // │                                                       │
  // │  Tap the experiences that excite you:                  │
  // │                                                       │
  // │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐               │
  // │  │ 🏛️   │ │ 🏖️   │ │ 🍜   │ │ 🌿   │               │
  // │  │Temples│ │Beach │ │Street │ │Nature│               │
  // │  │  ✓   │ │      │ │ Food✓│ │  ✓   │               │
  // │  └──────┘ └──────┘ └──────┘ └──────┘               │
  // │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐               │
  // │  │ 🎢   │ │ 🛍️   │ │ 🎭   │ │ 🏔️   │               │
  // │  │Theme │ │Shop- │ │Shows │ │Adven-│               │
  // │  │Parks │ │ping  │ │      │ │ture  │               │
  // │  └──────┘ └──────┘ └──────┘ └──────┘               │
  // │                                                       │
  // │  Pace: Slow ○──○──○──●──○ Packed                     │
  // │  Budget: Value ○──○──●──○──○ Luxury                   │
  // │  Travel style: Solo · Couple · Family ✓ · Friends     │
  // │                                                       │
  // │  [Next: Any must-see places?]                           │
  // └─────────────────────────────────────────────────────┘
}
```

### Real-Time Itinerary Adaptation

```typescript
interface ItineraryAdaptation {
  // How the itinerary adapts during the trip
  adaptation_triggers: {
    WEATHER_CHANGE: {
      trigger: "Rain forecast or extreme heat warning";
      response: "Swap outdoor activities to indoor alternatives (museum instead of garden tour)";
      notification: "Heads up! Rain expected after 3 PM. Moving Sentosa to tomorrow, National Museum today.";
      agent_approval: "Auto-adjust if within policy; notify agent if major change";
    };

    DELAY_DISRUPTION: {
      trigger: "Flight delayed, traffic jam, long queue at attraction";
      response: "Push back subsequent activities, compress or skip low-priority items";
      notification: "Your flight is delayed by 2 hours. Adjusted: skip Little India (moved to Day 4), direct to hotel.";
    };

    CUSTOMER_REQUEST: {
      trigger: "Traveler wants to add, skip, or change an activity";
      response: "System checks availability and price impact → proposes adjusted schedule";
      examples: [
        "I want to skip the museum and go shopping instead",
        "Can we add a night safari tonight?",
        "We're too tired for the evening activity",
      ];
    };

    SUPPLIER_ISSUE: {
      trigger: "Booked activity cancelled, restaurant closed, transfer no-show";
      response: "Immediately propose alternative with similar profile; agent notified";
      urgency: "During-trip supplier issues are HIGH priority — resolve within 30 minutes";
    };

    SPONTANEITY_DETECTION: {
      trigger: "Traveler is near an unlisted attraction or highly-rated restaurant";
      response: "Optional suggestion: 'You're 200m from Maxwell Food Centre — great chicken rice!'";
      opt_in: "Only if customer enabled spontaneous suggestions in preferences";
    };
  };

  // ── Real-time adaptation notification ──
  // ┌─────────────────────────────────────────────────────┐
  // │  ⚡ Itinerary Update · Day 2                              │
  // │                                                       │
  // │  🌧️ Rain expected after 3 PM                               │
  // │                                                       │
  // │  Original Plan:                                       │
  // │  2:00 PM  Sentosa Island (outdoor)                    │
  // │  5:00 PM  Beach walk                                   │
  // │                                                       │
  // │  Suggested Adjustment:                                │
  // │  2:00 PM  ArtScience Museum (indoor, nearby)           │
  // │  4:30 PM  Marina Bay Sands observation deck            │
  // │  → Sentosa moved to Day 4 (sunny forecast ✅)          │
  // │                                                       │
  // │  Budget impact: +₹200 (museum entry)                   │
  // │                                                       │
  // │  [Accept] [Keep Original] [Talk to Agent]               │
  // └─────────────────────────────────────────────────────┘
}
```

---

## Open Problems

1. **Cold-start problem** — First-time customers have no travel history, making preference matching imprecise. Need rich intake forms combined with similar-traveler modeling, but must clearly distinguish inferred preferences from stated ones.

2. **Activity database maintenance** — AI itineraries are only as good as the activity database. Attractions close, restaurants change hours, prices fluctuate. Need automated scraping + supplier API integration + traveler feedback to keep data current.

3. **Cultural sensitivity** — AI may suggest activities that are culturally inappropriate (e.g., suggesting a pub crawl to a teetotaler family, or a beach destination during a religious fasting period). Cultural awareness layer is essential for Indian travelers.

4. **Over-optimization trap** — Algorithmically perfect itineraries can feel rigid and impersonal. Need to inject serendipity — unexpected recommendations, local experiences, and "free time to wander" that make trips memorable rather than efficient.

5. **Agent trust in AI output** — Agents may distrust AI-generated itineraries, especially for premium customers. Need transparent confidence scores ("87% match to customer preferences") and easy editing tools so agents feel in control, not replaced.

---

## Next Steps

- [ ] Build customer preference profiling engine with behavioral inference
- [ ] Create itinerary generation pipeline with constraint solver and preference matching
- [ ] Implement real-time adaptation triggers for weather, delays, and customer requests
- [ ] Design agent review interface with confidence scores and one-click editing
- [ ] Build activity database with automated freshness monitoring
