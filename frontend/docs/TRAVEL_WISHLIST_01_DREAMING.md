# Travel Wishlist & Bucket List — Trip Dreaming

> Research document for travel wishlists, destination bucket lists, price drop alerts, saved trip ideas, future trip planning, and dream destination tracking for the Waypoint OS platform.

---

## Key Questions

1. **How do we capture and nurture travelers' dream destinations?**
2. **What drives wishlist-to-booking conversion?**
3. **How do price drop alerts create urgency from aspiration?**
4. **What social and sharing features amplify wishlist engagement?**

---

## Research Areas

### Travel Wishlist & Bucket List System

```typescript
interface TravelWishlist {
  // Capturing, nurturing, and converting travel dreams into bookings
  wishlist_features: {
    DESTINATION_SAVES: {
      description: "Save destinations you want to visit";
      actions: [
        "Save from destination page (Maldives → Add to Wishlist)",
        "Save from Instagram/social (see friend's trip → save destination)",
        "Save from deal (see a Bali deal → save for later)",
        "Save from quiz result (Travel Personality Quiz → save matched destinations)",
        "Save from search (browsing destinations → save interesting ones)",
      ];
      data_captured: {
        destination: "Maldives, Bali, Switzerland, Japan...";
        priority: "Dream (someday) vs. Planning (next 6 months) vs. Ready (next 3 months)";
        budget_range: "What the traveler expects to spend";
        preferred_season: "When they'd like to go";
        companions: "Solo, couple, family, friends";
        notes: "Personal note about why they want to visit";
      };
    };

    TRIP_IDEAS: {
      description: "Save complete trip concepts, not just destinations";
      examples: [
        "Save a friend's shared itinerary ('Rahul's Bali itinerary' → save to my ideas)",
        "Save a curated trip from agency ('Best of Japan in 10 Days' → save)",
        "Save a custom draft itinerary (built in trip planner but not ready to book)",
        "Save from travel blog or content ('Santorini sunset itinerary' → save)",
      ];
    };

    BUCKET_LIST: {
      description: "Long-term travel goals and milestone trips";
      categories: {
        ONCE_IN_A_LIFETIME: "Northern Lights, Machu Picchu, African Safari, Great Barrier Reef";
        BY_AGE: "30 before 30, 40 before 40 — milestone travel goals";
        BY_EXPERIENCE: "See cherry blossoms, swim with dolphins, see midnight sun, attend Oktoberfest";
        BY_REGION: "Visit all 7 continents, every Indian state, every European capital";
      };
      gamification: {
        progress_tracking: "15/50 Indian states visited, 3/7 continents";
        badges: "Globe Trotter (10+ countries), Mountain Lover (5+ hill stations), Beach Bum (10+ beaches)";
        sharing: "Bucket list progress shared as social card (Instagram-worthy)";
      };
    };
  };

  // ── Wishlist — customer view ──
  // ┌─────────────────────────────────────────────────────┐
  // │  💫 My Travel Dreams                                       │
  // │                                                       │
  // │  🔥 Ready to Book (2):                                   │
  // │  ┌─ Maldives · Couple · ₹2.5-3L budget                   │
  // │  │  ✈️ Prices dropped 12% this week!                      │
  // │  │  Best deal: ₹2.35L (Aug 10-15)                        │
  // │  │  [View Deal] [Start Planning]                           │
  // │  └───────────────────────────────────────────────────── │
  // │  ┌─ Singapore · Family · ₹2-2.5L budget                   │
  // │  │  📅 Your preferred month: October (Diwali break)        │
  // │  │  💡 Book by July for early bird pricing                 │
  // │  │  [Start Planning] [Set Price Alert]                     │
  // │  └───────────────────────────────────────────────────── │
  // │                                                       │
  // │  🌟 Planning (3):                                        │
  // │  · Japan (cherry blossom 2027) · Couple                  │
  // │  · Switzerland (next summer) · Family                    │
  // │  · Turkey (hot air balloon!) · Friends                   │
  // │  [Set Alerts for All]                                     │
  // │                                                       │
  // │  💭 Dreaming (5):                                        │
  // │  · Northern Lights · Iceland                             │
  // │  · African Safari · Kenya                                │
  // │  · Machu Picchu · Peru                                   │
  // │  · Road Trip USA · West Coast                            │
  // │  · Greek Islands · Island Hopping                        │
  // │  [View Bucket List Progress]                              │
  // │                                                       │
  // │  🏆 Bucket List: 12/50 visited · Top 3% of travelers      │
  // │  [Share Progress Card] [Explore Destinations]             │
  // └─────────────────────────────────────────────────────────┘
}
```

### Price Drop & Booking Conversion

```typescript
interface WishlistConversion {
  // Converting wishlist dreams into actual bookings
  price_drop_alerts: {
    MECHANISM: {
      description: "Monitor prices for wishlisted destinations and alert on drops";
      monitoring: [
        "Flight prices (route + approximate dates from wishlist)",
        "Hotel prices (destination + budget range from wishlist)",
        "Package prices (combined flight + hotel for destination)",
        "Competitor pricing (if agency price > market, flag for price matching)",
      ];
      alert_trigger: "Price drops >10% below recent average OR price hits customer's budget range";
      frequency: "Max 2 alerts per destination per month (avoid alert fatigue)";
    };

    ALERT_FORMAT: {
      channel: "WhatsApp (primary), push notification (app), email (digest)";
      content: "Destination + new price + old price + savings amount + 'Book Now' button";
      urgency: "'Prices typically stay at this level for 3-5 days' — honest urgency, not fake scarcity";
    };
  };

  conversion_triggers: {
    SEASONAL_NUDGE: {
      description: "Remind wishlisters when their preferred season is approaching";
      timing: "3-4 months before preferred travel month";
      message: "You saved [Destination] for [Month] — booking window is opening! Best prices available now for advance booking.";
    };

    INSPIRATION_NUDGE: {
      description: "Share content about wishlisted destination to reignite interest";
      format: "Travel story, photo gallery, or video about the destination";
      timing: "When new content about wishlisted destination is published";
    };

    DEAL_MATCH: {
      description: "When a deal matches a wishlisted destination, notify immediately";
      priority: "Highest priority notification — wishlisted destination + good deal = highest conversion";
    };

    MILESTONE_NUDGE: {
      description: "Birthday, anniversary, or milestone → suggest wishlisted destination as celebration trip";
      timing: "30-45 days before milestone date";
    };

    SOCIAL_TRIGGERS: {
      description: "Friend booked same destination → nudge wishlister";
      message: "Your friend Rahul just booked a trip to Bali! Your Bali trip is still in your wishlist — [Start Planning]";
    };
  };

  analytics: {
    WISHLIST_METRICS: {
      popular_destinations: "Most wishlisted destinations (demand signal for deals and inventory)",
      wishlist_to_booking_rate: "What % of wishlisted items convert to bookings (target: 15-25% within 12 months)",
      average_time_to_book: "How long from wishlist save to booking (typical: 3-9 months)";
      price_sensitivity: "At what price point do wishlisters convert (optimize deal pricing)";
    };

    DEMAND_FORECASTING: {
      description: "Wishlist data predicts future demand";
      value: "If 500 customers wishlisted Japan for 2027 cherry blossom season, agency can pre-negotiate group rates and be ready with inventory";
    };
  };
}
```

### Social & Sharing Features

```typescript
interface WishlistSocial {
  // Social features that amplify wishlist engagement
  sharing: {
    WISHLIST_SHARING: {
      description: "Share wishlist with travel companions to plan together";
      mechanism: "Share link → companion sees shared destinations → can add or vote";
      use_case: "Couple planning honeymoon — both add destinations to shared wishlist and vote";
    };

    BUCKET_LIST_CARD: {
      description: "Shareable social card showing travel achievements";
      format: "Visual card with visited count, badges, and top destinations";
      platform: "Instagram Story, WhatsApp Status, LinkedIn";
      purpose: "Social proof + viral acquisition (friends see card → discover agency)";
    };

    TRIP_RECOMMENDATION: {
      description: "Recommend a destination from your wishlist to a friend";
      message: "I'm dreaming about [Destination] — [Friend] should add this to their wishlist too!";
      incentive: "Both get ₹500 credit if friend books within 90 days";
    };
  };

  collaborative_planning: {
    GROUP_WISHLIST: {
      description: "Group trip planning starts with shared wishlist";
      flow: [
        "Create group wishlist (e.g., 'College Reunion Trip 2027')",
        "All members add destinations they want",
        "Vote on top 3 choices",
        "Agent presents proposals for top-voted destinations",
        "Group votes on final choice → agent books",
      ];
    };
  };
}
```

---

## Open Problems

1. **Wishlist vs. intent signal** — Saving a destination doesn't mean the traveler is ready to book. Distinguishing "dreaming" from "planning" from "ready to book" requires behavioral signals (visited pricing page = planning, checked calendar = ready).

2. **Price monitoring at scale** — Monitoring flight and hotel prices for thousands of wishlisted destinations requires significant API calls and data processing. Cost-effective monitoring with acceptable accuracy is a technical challenge.

3. **Alert fatigue** — Too many price alerts condition customers to ignore them. Maximum 2 per destination per month with genuinely meaningful price drops (>10%) maintains alert value.

4. **Wishlist data privacy** — Wishlist data reveals travel intentions (honeymoon, relocation, expensive trip) that customers may not want shared. Privacy controls must be explicit.

5. **Conversion attribution** — Did the customer book because of the price drop alert, the seasonal nudge, or the deal match? Multi-touch attribution for wishlist conversion is complex but essential for optimizing the nudge strategy.

---

## Next Steps

- [ ] Build wishlist system with destination saves, trip ideas, and bucket list tracking
- [ ] Create price drop alert engine with destination-specific price monitoring
- [ ] Implement conversion trigger system (seasonal, inspiration, deal match, milestone, social)
- [ ] Design collaborative wishlist for group trip planning with voting
- [ ] Build bucket list gamification with badges and progress tracking
- [ ] Create shareable bucket list card for social media
- [ ] Build wishlist analytics dashboard with demand forecasting for operations
