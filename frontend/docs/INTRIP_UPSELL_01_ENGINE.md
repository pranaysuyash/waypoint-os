# In-Trip Upsell Engine — During-Trip Revenue Opportunities

> Research document for the in-trip upsell engine, identifying and presenting upgrade opportunities during active trips — room upgrades, activity add-ons, trip extensions, companion additions, and last-minute experiences for the Waypoint OS platform.

---

## Key Questions

1. **What upsell opportunities exist during an active trip?**
2. **How are upsell suggestions triggered and timed?**
3. **How does the upsell engine balance revenue with customer experience?**
4. **What percentage of trip revenue can come from in-trip upsells?**

---

## Research Areas

### In-Trip Upsell Engine Architecture

```typescript
interface InTripUpsellEngine {
  // During-trip revenue opportunities
  upsell_categories: {
    ROOM_UPGRADE: {
      description: "Upgrade hotel room during stay";
      trigger: "Day 1 check-in experience or mid-trip special occasion";
      offers: {
        category_upgrade: "Deluxe → Suite: 'Treat yourself to a Suite for your anniversary night'";
        view_upgrade: "City view → Marina view: 'Your hotel has stunning bay views available'";
        extra_night: "4 nights → 5 nights: 'Love Singapore? Extend one more night at 30% off'";
      };
      margin: "40-60% margin on room upgrade differentials";
      timing: "Day 1 evening (after check-in) or day before special occasion";
    };

    ACTIVITY_ADDON: {
      description: "Add activities not in original itinerary";
      trigger: "Free time blocks, proximity to attractions, weather changes";
      offers: {
        missing_experiences: "Customer didn't book night safari → offer with pickup arranged";
        premium_version: "Standard walking tour → private guided tour with photographer";
        weather_alternative: "Outdoor plan rained out → offer indoor premium experience";
        group_deal: "Family of 3 → add 4th activity at group discount";
      };
      margin: "25-45% margin on add-on activities";
      timing: "Evening before (for next day) or 2 hours before activity start";
    };

    DINING_UPGRADE: {
      description: "Upgrade meal experiences during trip";
      trigger: "Scheduled meal time approaching, special occasion, cuisine interest";
      offers: {
        restaurant_upgrade: "Hawker centre → Michelin-star restaurant: 'Celebrating tonight?'";
        dining_experience: "Regular dinner → dinner cruise or rooftop dining";
        cuisine_specialty: "In Little India → offer special thali feast at top-rated restaurant";
      };
      margin: "30-50% margin on dining experiences";
      timing: "3-4 hours before meal time";
    };

    TRIP_EXTENSION: {
      description: "Extend trip duration or add destination";
      trigger: "Day 3+ of trip, customer expressing enjoyment, availability detected";
      offers: {
        extra_night: "Add 1 night at current hotel (negotiated last-minute rate)";
        add_city: "5 days Singapore → add 2 days Kuala Lumpur (short flight)";
        layover_experience: "Return flight has layover → offer city tour during layover";
      };
      margin: "Highest margin upsell — 50-70% on extension components";
      timing: "Day 3-4 of trip (after customer has positive experience)";
    };

    COMPANION_ADDITION: {
      description: "Add a person to existing booking";
      trigger: "Customer mentions friend/family wanting to join, posts on social media";
      offers: {
        add_person: "'Your friend wants to join? Add them to your booking — we'll handle everything'";
        child_addition: "Add child to family booking (extra bed, activity adjustment)";
        group_member: "Group trip → add late joiner at prorated cost";
      };
      margin: "Variable — mostly incremental cost with small margin";
      timing: "When customer mentions or when social activity detected";
    };

    INSURANCE_URGENT: {
      description: "Sell or upgrade insurance during trip";
      trigger: "Customer has no insurance or basic plan; incident occurs";
      offers: {
        upgrade_coverage: "Basic → comprehensive: 'Your basic plan doesn't cover this medical expense'";
        activity_insurance: "Adventure activity not covered → offer activity-specific coverage";
        device_protection: "Phone/camera insurance for expensive equipment during trip";
      };
      margin: "70-80% margin on insurance products";
      timing: "When customer faces uncovered situation or before high-risk activity";
    };
  };

  // ── In-trip upsell — agent dashboard ──
  // ┌─────────────────────────────────────────────────────┐
  // │  In-Trip Upsell · Sharma Family · Singapore Day 2        │
  // │                                                       │
  // │  💡 Suggested Upsells (AI-scored):                       │
  // │                                                       │
  // │  ⭐ HIGH (87% match):                                     │
  // │  Night Safari — Tomorrow 7:30 PM                         │
  // │  Not in itinerary · Family-friendly · ₹3,500 for 3       │
  // │  Margin: ₹1,400 (40%) · Reason: Free evening + child     │
  // │  interest in animals from profile                        │
  // │  [Send Offer] [Skip]                                      │
  // │                                                       │
  // │  📊 MEDIUM (62% match):                                   │
  // │  Marina Bay Sands SkyPark — Day 4 evening                │
  // │  Upgrade from Gardens by the Bay · ₹2,800 for 3          │
  // │  Margin: ₹900 (32%) · Reason: Anniversary trip            │
  // │  [Send Offer] [Skip]                                      │
  // │                                                       │
  // │  🍽️ LOW (41% match):                                     │
  // │  Jubilee Dining Cruise — Day 3 dinner                    │
  // │  Replace planned hawker centre · ₹5,200 for 3            │
  // │  Margin: ₹2,100 (40%) · Reason: Special occasion         │
  // │  [Send Offer] [Skip]                                      │
  // │                                                       │
  // │  Session Revenue: ₹4,400 from 2 accepted offers          │
  // │  Total trip upsell: ₹8,200 (7% of base trip value)       │
  // └─────────────────────────────────────────────────────────┘
}
```

### Upsell Trigger System

```typescript
interface UpsellTriggerSystem {
  // When and how upsell opportunities are detected
  triggers: {
    SCHEDULE_BASED: {
      description: "Upsells triggered by itinerary schedule position";
      rules: [
        "Free evening → suggest dinner experience or night activity",
        "Last day → suggest trip extension or airport lounge",
        "Lunch break near attraction → suggest quick visit",
        "Weather forecast rain → suggest indoor premium alternative",
      ];
    };

    BEHAVIOR_BASED: {
      description: "Upsells triggered by customer behavior signals";
      signals: [
        "Customer opens itinerary app 5+ times in a day (engaged → receptive)",
        "Customer sends positive chat message ('Having a great time!')",
        "Customer checks budget tracker and is under budget",
        "Customer takes many photos at specific activity type (deep interest)",
        "Customer mentions wanting more time at a location",
      ];
    };

    OCCASION_BASED: {
      description: "Upsells triggered by special dates and occasions";
      triggers: [
        "Birthday during trip → offer birthday dinner/cake/experience",
        "Anniversary during trip → suggest couple's spa or romantic dinner",
        "Festival during trip (Diwali abroad) → cultural celebration experience",
        "Child's birthday → kid-friendly special activity",
      ];
    };

    AVAILABILITY_BASED: {
      description: "Upsells triggered by supplier inventory opportunities";
      opportunities: [
        "Hotel has unsold suites → offer flash upgrade at 50% off rack rate",
        "Activity has last-minute availability → offer at discounted rate",
        "Restaurant has cancellation → offer premium slot",
        "Flight has empty seats → offer last-minute extension",
      ];
    };
  };

  // Customer communication channels
  channels: {
    WHATSAPP: {
      primary: "Main channel for upsell offers during trip";
      format: "Rich message with image, price, and one-tap accept";
      frequency: "Max 2 offers per day; max 1 per channel per day";
    };

    APP_NOTIFICATION: {
      secondary: "In-app notification for companion app users";
      format: "Card in trip dashboard with accept/dismiss";
      timing: "Shown when customer opens app, not push notification";
    };

    AGENT_CHAT: {
      personal: "Agent suggests during active conversation";
      format: "Natural conversation, not sales pitch";
      effectiveness: "Highest conversion (40-50%) vs WhatsApp (15-20%) vs app (10-15%)";
    };
  };
}

// ── Customer-facing upsell message (WhatsApp) ──
// ┌─────────────────────────────────────────────────────┐
// │  💬 Waypoint Travel · Singapore                             │
// │                                                       │
// │  Hi Mr. Sharma! Hope Day 2 is going great. 🌟          │
// │                                                       │
// │  I noticed you have a free evening tomorrow.          │
// │  The Night Safari is a must-do with kids!              │
// │                                                       │
// │  🦁 Night Safari · Tomorrow 7:30 PM                      │
// │  👨‍👩‍👦 Family ticket (2A + 1C): ₹3,500                      │
// │  🚐 Includes pickup from hotel at 7:00 PM                │
// │  ⏰ Limited slots available                               │
// │                                                       │
// │  [Yes, Book It] [No Thanks] [Tell Me More]                │
// └─────────────────────────────────────────────────────┘
```

### Upsell Revenue Analytics

```typescript
interface UpsellAnalytics {
  // Revenue tracking and optimization for in-trip upsells
  metrics: {
    REVENUE_METRICS: {
      upsell_revenue_per_trip: "Average ₹3K-15K per trip (5-12% of base trip value)";
      upsell_margin: "Average 35-50% margin (higher than base booking margin)";
      acceptance_rate: "25-35% of presented offers accepted";
      revenue_by_category: {
        activity_addon: "40% of upsell revenue";
        room_upgrade: "25% of upsell revenue";
        dining_upgrade: "15% of upsell revenue";
        trip_extension: "10% of upsell revenue";
        insurance: "10% of upsell revenue";
      };
    };

    EXPERIENCE_GUARDRAILS: {
      description: "Prevent upsell fatigue and protect customer experience";
      rules: {
        max_offers_per_day: 2;
        max_offers_per_trip: 8;
        never_on_arrival_day: "Day 1 = settle in, no sales";
        never_on_departure_day: "Last day = wrap up, no extensions";
        never_during_emergency: "Emergency = support only, no offers";
        cooldown_after_rejection: "24 hours after customer declines an offer";
        sentiment_check: "If customer expressed frustration → pause all offers";
      };
    };

    AGENT_INCENTIVE: {
      description: "Agent earns commission on successful upsells";
      structure: "10-15% of upsell margin as agent commission";
      benefit: "Agent motivated to suggest relevant upgrades = better customer experience + more revenue";
    };
  };
}
```

---

## Open Problems

1. **Upsell fatigue** — Too many offers annoy customers and damage trust. The 2-offers-per-day cap helps, but even 2 may be too many if the customer isn't in a buying mindset. Need sentiment-aware throttling.

2. **Cultural sensitivity** — Upselling feels different across cultures. Indian customers may find direct upsell offers transactional; wrapping the offer in "I noticed you'd enjoy..." feels more personal and less salesy. The framing matters more than the offer.

3. **Pricing transparency** — If a customer discovers the hotel upgrade is available cheaper on Booking.com than the upsell price, trust is broken. Upsell pricing must be competitive with public rates while maintaining margin.

4. **Agent vs. automation balance** — Fully automated upsells feel impersonal; fully agent-driven upsells don't scale. The sweet spot is AI-detected opportunities with agent-personalized delivery — the AI finds the moment, the agent makes the pitch.

5. **Attribution** — If a customer upgrades their room, was it the WhatsApp offer, the agent's suggestion, or the customer's own idea? Multi-touch attribution is needed to optimize channel effectiveness.

---

## Next Steps

- [ ] Build upsell opportunity detection engine with trigger rules
- [ ] Create customer-facing upsell message templates for WhatsApp and app
- [ ] Implement experience guardrails with sentiment-aware throttling
- [ ] Build upsell revenue analytics dashboard for agents and owners
- [ ] Design agent incentive structure for upsell commissions
