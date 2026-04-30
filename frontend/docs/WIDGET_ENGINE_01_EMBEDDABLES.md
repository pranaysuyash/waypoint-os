# Embeddable Widgets & Customer Tools — Booking Engine, Trip Planner, Cost Estimator

> Research document for embeddable travel widgets, booking search widgets, trip planner tools, cost estimators, destination comparison tools, and conversion-optimized embeddable components for the Waypoint OS platform.

---

## Key Questions

1. **What embeddable widgets drive customer engagement and conversion?**
2. **How does a booking search widget work on third-party sites?**
3. **What customer-facing calculators help the decision process?**
4. **How do widgets integrate with the agency's main platform?**

---

## Research Areas

### Widget Architecture

```typescript
interface EmbeddableWidgets {
  // Embeddable components for travel agency customer acquisition
  widget_types: {
    BOOKING_SEARCH_WIDGET: {
      description: "Search box that lets customers explore trip options";
      placement: "Agency website, blog posts, partner websites, social media landing pages";
      components: {
        search_fields: {
          destination: "Dropdown or autocomplete of available destinations";
          dates: "Date range picker with flexible date option (+/- 3 days)";
          travelers: "Adult/children counter with age selector";
          budget: "Optional budget range selector";
        };
        search_results: {
          display: "Package cards with: destination image, price, duration, key highlights";
          sorting: "By price (low-high), by popularity, by departure date";
          filtering: "By budget range, duration, inclusions, travel style";
        };
        cta: "'Get Custom Quote' → inquiry form pre-filled with search context";
      };
      embed_method: "JavaScript snippet or iframe; responsive design for all screen sizes";
      conversion_tracking: "Widget load → search → result click → inquiry → booking";
      // ── Booking search widget ──
      // ┌─────────────────────────────────────────────────────┐
      // │  🌍 Plan Your Trip                                         │
      // │                                                       │
      // │  Where?  [Singapore          ▾]                        │
      // │  When?   [Jun 15 - Jun 20    📅]                       │
      // │  Who?    [2 Adults] [+ Children ▾]                     │
      // │                                                       │
      // │  [🔍 Search Trips]                                        │
      // │                                                       │
      // │  ── Results ──                                        │
      // │  ┌──────┐  Singapore Explorer · 5D/4N                    │
      // │  │  🏙️  │  From ₹1.2L/person                             │
      // │  │  SG   │  ✈️ Flights · 🏨 4★ Hotel · 🎯 5 Activities    │
      // │  └──────┘  [Get Quote]                                   │
      // │  ┌──────┐  Singapore Premium · 5D/4N                     │
      // │  │  🏙️  │  From ₹1.8L/person                             │
      // │  │  SG   │  ✈️ Flights · 🏨 5★ Hotel · 🎯 7 Activities    │
      // │  └──────┘  [Get Quote]                                   │
      // └─────────────────────────────────────────────────────┘
    };

    TRIP_COST_ESTIMATOR: {
      description: "Interactive calculator for estimated trip cost";
      purpose: "Help customers understand pricing before contacting agent (reduces price shock)";
      inputs: {
        destination: "Select destination (pre-loaded with current pricing data)";
        duration: "Slider: 3-15 days";
        travelers: "Adult/children count";
        travel_class: "Economy / Premium Economy / Business";
        hotel_tier: "Budget (2-3★) / Standard (3-4★) / Premium (4-5★)";
        meal_plan: "Breakfast only / Half board / Full board";
        activities: "Select activity categories (culture, adventure, shopping, dining)";
      };
      output: {
        range: "'Estimated cost: ₹95,000 - ₹1,35,000 per person'";
        breakdown: "Flights: ₹28K | Hotel: ₹35K | Activities: ₹15K | Food: ₹12K | Visa: ₹5K";
        comparison: "Budget trip: ₹75K | Your selection: ₹1.1L | Premium: ₹1.8L";
        cta: "'Get an exact quote for your dates' → inquiry with pre-filled preferences";
      };
      data_source: "Real-time pricing from supplier contracts and GDS rates";
      embed_method: "JavaScript widget; embeddable on website, blog, partner sites";
      // ── Cost estimator widget ──
      // ┌─────────────────────────────────────────────────────┐
      // │  💰 Trip Cost Estimator                                    │
      // │                                                       │
      // │  Destination: [Singapore ▾]                            │
      // │  Duration:    [5] days   ◄━━━━●━━━━►  3──7──15       │
      // │  Travelers:   2 Adults · 1 Child                       │
      // │  Travel class: [Economy ▾]                              │
      // │  Hotel tier:   [Standard (3-4★) ▾]                     │
      // │                                                       │
      // │  Estimated Cost:                                      │
      // │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━              │
      // │  ₹75K     ₹1.12L ●     ₹1.8L                          │
      // │  Budget   Your trip    Premium                          │
      // │                                                       │
      // │  Breakdown:                                           │
      // │  ✈️ Flights:     ₹28K (economy round trip)              │
      // │  🏨 Hotel:       ₹35K (4★ × 5 nights)                   │
      // │  🎯 Activities:  ₹18K (5 activities)                     │
      // │  🍽️ Meals:       ₹12K (breakfast + 2 dinners)            │
      // │  📄 Visa + Ins:  ₹8K                                     │
      // │  ─────────────────────                                  │
      // │  Total: ₹1.01L per person (₹3.03L for 3)               │
      // │                                                       │
      // │  [Get Exact Quote] [Adjust Options]                      │
      // └─────────────────────────────────────────────────────┘
    };

    DESTINATION_COMPARISON: {
      description: "Side-by-side destination comparison tool";
      purpose: "Help undecided customers compare destinations on key criteria";
      comparisons: {
        destinations: "Select 2-3 destinations to compare";
        criteria: {
          cost: "Average trip cost per person (from real pricing data)";
          flight_time: "Hours from customer's nearest airport";
          visa: "Visa requirement and processing time";
          weather: "Expected weather for selected travel month";
          family_friendly: "Rating for families with children";
          food: "Vegetarian/Indian food availability rating";
          safety: "Safety rating for Indian travelers";
          best_for: "Tags: Beach, Culture, Adventure, Shopping, Nightlife, Nature";
        };
      };
      cta: "'I'm interested in {destination}' → inquiry with destination pre-selected";
      // ── Destination comparison ──
      // ┌─────────────────────────────────────────────────────┐
      // │  🔍 Compare Destinations                                   │
      // │                                                       │
      // │  Singapore      Bangkok        Dubai                     │
      // │  ─────────      ───────        ─────                    │
      // │  ₹1.2L/person   ₹85K/person    ₹1.1L/person            │
      // │  5.5 hrs flight  4.5 hrs        3.5 hrs                 │
      // │  E-visa (3 days) Visa on arr.   Visa (3 days)           │
      // │  🌧️ Jun: Rain    🌧️ Jun: Rain   🌡️ Jun: 40°C hot        │
      // │  ⭐⭐⭐⭐⭐ Family   ⭐⭐⭐⭐ Family   ⭐⭐⭐⭐ Family          │
      // │  ⭐⭐⭐⭐ Veg food  ⭐⭐⭐⭐⭐ Veg    ⭐⭐⭐⭐ Veg             │
      // │  Very safe       Safe           Very safe               │
      // │                                                       │
      // │  Best for:        Best for:       Best for:             │
      // │  Culture Nature   Food Shopping   Luxury Shopping       │
      // │  Family           Nightlife       Family Food           │
      // │                                                       │
      // │  [Plan Singapore]  [Plan Bangkok]  [Plan Dubai]           │
      // └─────────────────────────────────────────────────────┘
    };

    TRIP_PLANNER_WIDGET: {
      description: "Interactive trip planning tool that captures preferences";
      flow: {
        step_1: "Select destination → show top activities as image cards";
        step_2: "Drag-and-drop activities into preferred days";
        step_3: "Select hotel preference (location, tier, amenities)";
        step_4: "Review summary with estimated cost";
        step_5: "'Get a real itinerary from our agent' → inquiry with full plan attached";
      };
      value: "Customer does the dreaming; agent does the booking. Captures rich preference data before first conversation.";
      conversion: "Trip planner submissions convert at 30-40% (vs. 5-8% for generic inquiry forms)";
    };

    COUNTDOWN_WIDGET: {
      description: "Trip countdown timer for booked customers (embeddable/shareable)";
      display: "'12 days until your Singapore adventure! 🌏'";
      purpose: "Post-booking engagement; shareable on social media (brand visibility)";
      data: "Pulls trip dates from booking data; customizable message";
    };
  };
}
```

### Widget Integration & Analytics

```typescript
interface WidgetIntegrationAnalytics {
  // How widgets connect to the platform and measure performance
  integration: {
    EMBED_METHODS: {
      javascript_snippet: {
        description: "Copy-paste JS snippet into any website";
        advantage: "Full interactivity, responsive, same origin for analytics";
        setup: "<script src='https://waypoint.travel/widgets/search.js' data-agency='AGY001'></script>";
      };
      iframe: {
        description: "Embedded iframe for platforms that don't allow JS";
        advantage: "Works everywhere, sandboxed security";
        setup: "<iframe src='https://waypoint.travel/widgets/search?agency=AGY001'></iframe>";
      };
      whatsapp_deep_link: {
        description: "Widget that opens WhatsApp with pre-filled message";
        advantage: "Zero technical integration — just a link";
        use_case: "Instagram bio link, email CTA, social media posts";
        format: "https://wa.me/91XXXXXXXXXX?text=Hi! I'm interested in a Singapore trip for 3 people in June";
      };
    };

    ANALYTICS_PER_WIDGET: {
      metrics: {
        loads: "How many times the widget was loaded on a page";
        interactions: "Searches, selections, cost estimations performed";
        inquiries: "Inquiries submitted through the widget";
        bookings: "Bookings attributed to widget inquiry";
        revenue: "Total revenue from widget-attributed bookings";
      };
      attribution: "UTM parameters + widget ID + session tracking → booking attribution";
      optimization: "Widget with highest inquiry rate gets more prominent placement";
    };

    WHITE_LABEL: {
      description: "Widgets branded for each agency";
      customization: {
        colors: "Agency brand colors applied to widget theme",
        logo: "Agency logo in widget header",
        contact: "Agency phone/WhatsApp displayed in widget CTA",
        destinations: "Only show destinations the agency serves",
      };
    };
  };
}
```

---

## Open Problems

1. **Pricing data freshness** — Widgets showing trip costs need real-time or near-real-time pricing data. Stale prices (showing ₹1.2L when actual cost is ₹1.5L) erode trust. Need frequent price refresh from supplier APIs.

2. **Mobile widget performance** — JavaScript widgets add page load time. On slow mobile connections (common in India), heavy widgets may hurt the host page's performance. Lightweight versions for mobile are essential.

3. **Widget vs. WhatsApp preference** — Indian customers may prefer clicking a WhatsApp button over interacting with a complex widget. Need to A/B test widget engagement vs. simple WhatsApp CTA for different customer segments.

4. **Partner site control** — Widgets embedded on partner sites (bloggers, influencers) need to work reliably despite the partner's CMS limitations, ad blockers, and cookie consent requirements.

5. **Data privacy in widgets** — Widgets collect search data (destinations, dates, traveler count). This data is PII-adjacent and needs clear privacy disclosure. DPDP Act requires consent for data collection.

---

## Next Steps

- [ ] Build booking search widget with embeddable JavaScript snippet
- [ ] Create trip cost estimator with real-time pricing data
- [ ] Implement destination comparison tool with criteria scoring
- [ ] Design trip planner widget with drag-and-drop activity selection
- [ ] Build widget analytics dashboard with conversion tracking
