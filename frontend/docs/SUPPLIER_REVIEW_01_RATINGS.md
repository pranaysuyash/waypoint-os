# Supplier Ratings & Reviews — Customer-Driven Quality Intelligence

> Research document for supplier rating and review systems, customer feedback collection, quality scoring, supplier performance analytics, and data-driven supplier selection for the Waypoint OS platform.

---

## Key Questions

1. **How do customers rate and review suppliers (hotels, activities, transport)?**
2. **How do ratings influence future trip planning and supplier selection?**
3. **What supplier performance metrics are tracked beyond customer ratings?**
4. **How does rating data improve the supplier network over time?**

---

## Research Areas

### Supplier Rating System

```typescript
interface SupplierRatingReviews {
  // Customer-driven supplier quality intelligence
  rating_dimensions: {
    HOTEL_RATING: {
      dimensions: [
        { name: "Cleanliness", description: "Room and public area cleanliness", weight: 20 },
        { name: "Location", description: "Proximity to attractions, transport, restaurants", weight: 20 },
        { name: "Service", description: "Staff helpfulness, check-in experience, responsiveness", weight: 20 },
        { name: "Value for Money", description: "Quality relative to price paid", weight: 15 },
        { name: "Food Quality", description: "Breakfast, room service, nearby restaurants", weight: 15 },
        { name: "Family Friendly", description: "Child amenities, safety, activities for kids", weight: 10 },
      ];
      scale: "1-5 stars per dimension; overall = weighted average";
      context: "Rating captured per hotel per trip (not generic — tied to specific booking)";
    };

    ACTIVITY_RATING: {
      dimensions: [
        { name: "Enjoyment", description: "How much did you enjoy the activity?", weight: 30 },
        { name: "Value for Money", description: "Was it worth the price?", weight: 25 },
        { name: "Guide Quality", description: "Knowledge, engagement, language skills", weight: 20 },
        { name: "Organization", description: "Timeliness, pickup, flow of the activity", weight: 15 },
        { name: "Family Suitability", description: "Appropriate for children/elderly if applicable", weight: 10 },
      ];
    };

    TRANSPORT_RATING: {
      dimensions: [
        { name: "Punctuality", description: "On-time pickup and drop-off", weight: 25 },
        { name: "Vehicle Quality", description: "Cleanliness, comfort, AC, condition", weight: 25 },
        { name: "Driver Professionalism", description: "Polite, safe driving, helpful", weight: 25 },
        { name: "Communication", description: "Easy to contact, clear instructions", weight: 25 },
      ];
    };

    RESTAURANT_RATING: {
      dimensions: [
        { name: "Food Quality", description: "Taste, variety, freshness", weight: 30 },
        { name: "Vegetarian Options", description: "Indian veg food availability and quality", weight: 25 },
        { name: "Service Speed", description: "Order to table time, attentiveness", weight: 20 },
        { name: "Value for Money", description: "Price relative to quality", weight: 15 },
        { name: "Ambience", description: "Cleanliness, atmosphere, family-friendliness", weight: 10 },
      ];
    };
  };

  // ── Post-trip rating collection ──
  // ┌─────────────────────────────────────────────────────┐
  // │  ⭐ Rate Your Singapore Trip                               │
  // │                                                       │
  // │  🏨 Grand Mercure Singapore                              │
  // │  Overall: ⭐⭐⭐⭐☆                                         │
  // │  Cleanliness:    ⭐⭐⭐⭐⭐                                   │
  // │  Location:       ⭐⭐⭐⭐☆                                   │
  // │  Service:        ⭐⭐⭐⭐⭐                                   │
  // │  Value:          ⭐⭐⭐⭐☆                                   │
  // │  Food:           ⭐⭐⭐☆☆                                   │
  // │  Family:         ⭐⭐⭐⭐⭐                                   │
  // │  💬 "Great hotel, amazing location. Breakfast could    │
  // │     have more Indian veg options."                      │
  // │                                                       │
  // │  🎯 Gardens by the Bay                                   │
  // │  Overall: ⭐⭐⭐⭐⭐                                         │
  // │  Enjoyment: ⭐⭐⭐⭐⭐  Value: ⭐⭐⭐⭐⭐                       │
  // │  💬 "Kids loved the Cloud Forest! Must-do."              │
  // │                                                       │
  // │  [Continue Rating] [Skip] [Submit]                         │
  // └─────────────────────────────────────────────────────┘
}
```

### Supplier Quality Intelligence

```typescript
interface SupplierQualityIntelligence {
  // Analytics from customer ratings driving supplier decisions
  quality_scoring: {
    SUPPLIER_SCORECARD: {
      description: "Composite quality score for each supplier";
      calculation: {
        customer_rating: "Average of all customer ratings (weighted by recency — recent ratings count more)";
        repeat_usage: "How often the agency rebooks this supplier (proxy for reliability)";
        issue_rate: "Percentage of bookings with reported issues (complaints, refunds, no-shows)";
        responsiveness: "How quickly the supplier responds to booking requests and issues";
        price_competitiveness: "Supplier price vs. market average for same quality level";
      };
      grading: {
        A: "Preferred supplier — always use when available (score 90-100)";
        B: "Reliable supplier — use with confidence (score 75-89)";
        C: "Acceptable supplier — use when A/B unavailable, monitor closely (score 60-74)";
        D: "Underperforming — avoid unless no alternative; raise issues with supplier (score 40-59)";
        F: "Blacklisted — do not use; find alternative immediately (score <40)";
      };
    };
  };

  rating_driven_decisions: {
    ITINERARY_GENERATION: {
      integration: "AI itinerary engine prioritizes A-rated suppliers over B/C-rated";
      example: "For Singapore hotels, Grand Mercure (A) appears above Ibis (C) in itinerary suggestions";
    };

    SUPPLIER_NEGOTIATION: {
      use: "Aggregate ratings used to negotiate better rates with suppliers";
      example: "'Our customers rate you 4.8/5 — can we get a 5% volume discount?'";
      leverage: "High ratings = more bookings from agency = negotiating power";
    };

    QUALITY_ALERTS: {
      triggers: [
        "Supplier average rating drops below 3.5 → flag for quality review",
        "3+ complaints about same supplier in 30 days → immediate review",
        "Supplier fails to deliver on confirmed booking → automatic incident report",
        "New supplier added → provisional C grade until 5+ customer ratings collected",
      ];
    };
  };

  // ── Supplier quality dashboard ──
  // ┌─────────────────────────────────────────────────────┐
  // │  Supplier Quality · Singapore Hotels                       │
  // │                                                       │
  // │  🏨 Grand Mercure · Grade A · ⭐ 4.6 (89 ratings)        │
  // │     Cleanliness: 4.8 · Location: 4.7 · Service: 4.5     │
  // │     Issue rate: 2% · Repeat usage: 94%                    │
  // │     Customer quote: "Perfect location, great staff"       │
  // │                                                       │
  // │  🏨 Ibis Singapore · Grade C · ⭐ 3.4 (45 ratings)        │
  // │     Cleanliness: 3.8 · Location: 3.2 · Service: 3.0      │
  // │     Issue rate: 12% · Repeat usage: 45%                   │
  // │     ⚠️ Recent complaints: Small rooms, slow check-in      │
  // │     Action: Consider alternative for premium packages      │
  // │                                                       │
  // │  🏨 Marina Bay Sands · Grade B · ⭐ 4.5 (32 ratings)      │
  // │     Price: Premium · Value: 3.8 (expensive but excellent)  │
  // │     Best for: Premium/luxury packages only                │
  // │                                                       │
  // │  [Rate Supplier] [Find Alternatives] [Export Report]       │
  // └─────────────────────────────────────────────────────────┘
}
```

### Rating Collection Strategy

```typescript
interface RatingCollectionStrategy {
  // How ratings are collected without annoying customers
  collection_methods: {
    POST_TRIP_WHATSAPP: {
      timing: "2 days after trip return (give time to settle, not too long to forget)";
      format: "Short WhatsApp message with star rating tap — no forms, no links";
      incentive: "Complete all ratings → ₹500 credit on next booking";
      completion_rate_target: "60%+ of customers rate their trip";
    };

    COMPANION_APP: {
      timing: "Each day during trip — rate today's activities";
      format: "Quick star rating in companion app after each activity completes";
      advantage: "Captures in-the-moment feedback (more accurate than retrospective)";
    };

    AGENT_CALL: {
      timing: "Post-trip follow-up call";
      format: "Agent asks key ratings verbally and records in CRM";
      advantage: "Catches nuances (verbal tone, specific complaints) that star ratings miss";
    };
  };

  minimum_ratings_policy: {
    description: "Suppliers need minimum ratings before being fully trusted";
    rules: {
      new_supplier: "Provisional C grade; needs 5+ ratings before upgrade to B";
      trusted_supplier: "Maintains A/B grade with 20+ ratings and <5% issue rate";
      downgrade: "A/B supplier drops to C if average rating falls below 3.5 for 10+ recent ratings";
      blacklist: "F grade requires owner approval to use; alternative found immediately";
    };
  };
}
```

---

## Open Problems

1. **Rating bias** — Customers who had bad experiences are more motivated to leave ratings than satisfied ones. Need to actively solicit ratings from all customers, not just those who complain.

2. **Small sample sizes** — A supplier rated by 3 customers may look great (or terrible) based on too little data. Statistical confidence requires 10+ ratings for reliable assessment.

3. **Subjectivity** — A family with children rates a hotel differently than a solo business traveler. Ratings should be normalized by customer segment (family, couple, solo, business).

4. **Supplier retaliation** — Suppliers may pressure agencies not to share negative ratings. Need transparent but fair rating display that doesn't harm supplier relationships unnecessarily.

5. **Competitive sensitivity** — Supplier ratings are valuable competitive intelligence. Other agencies would love to see which hotels your customers rate highest. Rating data must be kept internal.

---

## Next Steps

- [ ] Build post-trip rating collection via WhatsApp and companion app
- [ ] Create supplier scorecard with multi-dimension quality scoring
- [ ] Implement supplier grading system (A through F) with automated alerts
- [ ] Design supplier quality dashboard with comparison and alternatives
- [ ] Integrate supplier ratings into itinerary generation engine
