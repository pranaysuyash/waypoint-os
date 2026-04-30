# Trip Comparison Engine — Itinerary Side-by-Side

> Research document for side-by-side itinerary comparison, proposal comparison, trip option evaluation, decision support tools, and comparison-driven booking conversion for the Waypoint OS platform.

---

## Key Questions

1. **How do customers compare multiple trip proposals before choosing?**
2. **What comparison dimensions drive booking decisions?**
3. **How does the comparison tool help agents present options effectively?**
4. **What UX patterns make trip comparison intuitive and decisive?**

---

## Research Areas

### Trip Comparison Engine

```typescript
interface TripComparisonEngine {
  // Side-by-side comparison of travel itineraries to help customers decide
  use_cases: {
    PROPOSAL_COMPARISON: {
      description: "Customer received 2-3 proposals for same destination and needs to compare";
      example: "Bali honeymoon: Option A (luxury villas, ₹3.2L) vs. Option B (mid-range + more activities, ₹2.4L) vs. Option C (budget + longer stay, ₹1.8L)";
    };

    DESTINATION_COMPARISON: {
      description: "Customer choosing between 2-3 destinations for similar experience";
      example: "Beach holiday: Maldives (luxury, ₹4L) vs. Bali (culture + beach, ₹2.5L) vs. Thailand (value, ₹1.5L)";
    };

    UPGRADE_COMPARISON: {
      description: "Customer deciding whether to upgrade room, activity, or experience";
      example: "Singapore: Standard package (₹1.8L) vs. Premium (₹2.3L) — show exactly what the extra ₹50K buys";
    };

    SEASON_COMPARISON: {
      description: "Same trip at different times of year with different pricing and experience";
      example: "Europe trip: May (pleasant, ₹3.5L) vs. August (peak, ₹4.2L) vs. October (autumn, ₹3L)";
    };
  };

  comparison_dimensions: {
    PRICING: {
      total_cost: "All-inclusive price per person and total";
      breakdown: "Itemized cost (flights, hotel, activities, meals, transfers, insurance)";
      value_per_day: "Cost per day to normalize different trip lengths";
      inclusions: "What's included vs. what costs extra";
      payment_schedule: "When and how much to pay (EMMI options)";
    };

    ACCOMMODATION: {
      hotel_quality: "Star rating, review score, photos";
      room_type: "Standard, deluxe, suite, villa — with photo comparison";
      location: "Proximity to attractions, beach, city center — visual map";
      amenities: "Pool, spa, restaurant, gym, WiFi quality";
      meal_plan: "Room only, breakfast, half board, full board";
    };

    EXPERIENCE: {
      activities: "Number and type of included activities";
      highlights: "Signature experiences unique to each option";
      pace: "Relaxed (2 activities/day) vs. packed (4+ activities/day)";
      free_time: "How much unstructured time for exploration";
      uniqueness: "What makes this option different from the others";
    };

    LOGISTICS: {
      flights: "Direct vs. connecting, airline, departure time, duration";
      transfers: "Included or extra, private or shared, distance from airport";
      visa: "Required or visa-free, processing time, cost";
      connectivity: "SIM card included, WiFi availability";
    };

    REVIEWS_AND_SOCIAL: {
      hotel_reviews: "Google/TripAdvisor rating and recent reviews";
      destination_rating: "Agency's own rating and customer feedback score";
      photos: "Real customer photos from similar trips";
      testimonials: "Customer quotes from similar itineraries";
    };
  };

  // ── Trip comparison — customer view ──
  // ┌─────────────────────────────────────────────────────┐
  // │  ⚖️ Compare Your Bali Options                               │
  // │                                                       │
  // │              Luxury Escape    Cultural Explorer   Budget │
  // │              ─────────────    ────────────────── ────── │
  // │  💰 Price    ₹3.2L/couple     ₹2.5L/couple    ₹1.8L/couple│
  // │             ₹5,333/day       ₹4,167/day      ₹3,000/day│
  // │                                                       │
  // │  ✈️ Flight   Direct (Garuda)   1-stop (AirAsia) 1-stop  │
  // │             7h 30m            10h 45m          11h      │
  // │                                                       │
  // │  🏨 Hotel    5★ Pool Villa     4★ Boutique      3★ Resort│
  // │             ⭐ 4.7/5           ⭐ 4.3/5         ⭐ 4.0/5 │
  // │             Jimbaran          Ubud + Seminyak   Kuta     │
  // │             [📸 Photos]       [📸 Photos]       [📸 Photos]│
  // │                                                       │
  // │  🎯 Activities 6 included      8 included      5 included│
  // │             Couple spa        Rice terrace     Tanah Lot │
  // │             Candlelight din.   Cooking class   Beach day │
  // │             Photoshoot         Temple tour      Snorkel  │
  // │                                                       │
  // │  🍽️ Meals   Breakfast + 2D    Breakfast + 3D  Break fast│
  // │                                                       │
  // │  📝 Free    3 full days       2 full days      4 full   │
  // │     time                                           days    │
  // │                                                       │
  // │  ⭐ Our     ★★★★★ Best for    ★★★★☆ Best for   ★★★☆☆  │
  // │  Rating     honeymoon         culture lovers   budget   │
  // │                                                       │
  // │  [📋 Full Itinerary A] [📋 Full Itinerary B] [📋 Full C]│
  // │                                                       │
  // │  [💬 Discuss with Agent]  [⭐ Book Option A]              │
  // └─────────────────────────────────────────────────────────┘
}
```

### Comparison UX & Decision Support

```typescript
interface ComparisonDecisionSupport {
  // Helping customers make confident decisions
  decision_aids: {
    RECOMMENDATION_TAG: {
      description: "Each option tagged with who it's best for";
      tags: [
        "Best for Honeymoon",
        "Best Value",
        "Best for Families",
        "Most Activities",
        "Most Relaxing",
        "Best Food Experience",
        "Most Instagram-Worthy",
      ];
      mechanism: "Agent assigns tags or AI suggests based on customer profile matching";
    };

    HIGHLIGHT_DIFFERENCES: {
      description: "Visually emphasize what's different between options";
      technique: "Same items shown in neutral color; differences highlighted in accent color";
      categories: {
        better: "Green highlight — this option is better on this dimension";
        worse: "Orange highlight — this option is weaker on this dimension";
        unique: "Purple highlight — only this option has this feature",
      };
    };

    VALUE_SCORE: {
      description: "Proprietary value score combining price, quality, and experience";
      formula: "Value Score = (Experience Points × Quality Weight) / Price";
      experience_points: "Points for each activity, amenity, and convenience factor";
      purpose: "Help customers see which option delivers the most for their money";
    };

    MATCH_SCORE: {
      description: "How well each option matches the customer's stated preferences";
      inputs: "Customer's budget, travel style, interests, group composition";
      output: "Match percentage for each option (e.g., Option A: 92%, Option B: 78%, Option C: 65%)";
      purpose: "Customers trust recommendations that are personalized to their needs";
    };
  };

  agent_tools: {
    COMPARISON_BUILDER: {
      description: "Agent creates comparison from multiple proposals";
      workflow: [
        "Agent selects 2-3 proposals to compare",
        "System auto-populates comparison dimensions from proposal data",
        "Agent adds recommendation tags and notes",
        "Comparison sent to customer via WhatsApp (PDF) or web link (interactive)",
      ];
    };

    COMPARISON_ANALYTICS: {
      description: "Track which option customers choose to optimize proposals";
      metrics: [
        "Which option is selected most often (pricing sweet spot)",
        "How long customer takes to decide (decision timeline)",
        "Which dimension drives the decision (price, hotel, activities)",
        "Follow-up questions asked (indicates what's unclear in proposals)",
      ];
    };
  };

  sharing_features: {
    CO_DECISION: {
      description: "Share comparison with travel companions for group decision-making";
      mechanism: "Share link → each person can vote on preferred option → group sees results";
      use_case: "Honeymoon couple comparing options together; family voting on destination";
    };

    PARENTAL_REVIEW: {
      description: "Child sends comparison to parents for approval/budget approval";
      mechanism: "Share link (view-only) → parent sees comparison → approves or requests changes";
      use_case: "Young professional sending trip comparison to parents who are paying";
    };
  };
}
```

---

## Open Problems

1. **Information overload** — Too many comparison dimensions overwhelm customers. The comparison must highlight the 3-5 key differences that actually drive decisions, not show every detail.

2. **Apples-to-oranges comparison** — Different trip options may have different durations, destinations, or inclusions, making direct comparison difficult. Normalizing to "value per day" helps but isn't perfect.

3. **Analysis paralysis** — Some customers spend weeks comparing options without deciding. Time-limited proposals and gentle nudges ("Option A has limited availability") prevent indefinite comparison.

4. **Comparison used for price shopping** — Customers may use the detailed comparison to negotiate with competitors or book components separately. Revealing supplier names in comparisons enables this.

5. **Mobile comparison UX** — Side-by-side comparison is natural on desktop but challenging on phone screens. Card-based comparison with swipe or tab-based alternatives needed for mobile.

---

## Next Steps

- [ ] Build comparison engine with multi-dimensional side-by-side display
- [ ] Create comparison builder tool for agents to assemble comparisons from proposals
- [ ] Implement decision aids (recommendation tags, highlight differences, value score, match score)
- [ ] Design mobile-first comparison UX (card-based with swipe navigation)
- [ ] Build co-decision sharing with voting for group decision-making
- [ ] Create comparison analytics to track decision patterns and optimize proposals
- [ ] Implement comparison delivery via WhatsApp (PDF) and interactive web link
