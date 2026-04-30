# Local Transport & Destination Navigation — Getting Around

> Research document for customer-facing local transport guidance, destination navigation, transit card management, local commuting instructions, and getting-around intelligence for the Waypoint OS platform.

---

## Key Questions

1. **How do we help travelers navigate unfamiliar destinations?**
2. **What local transport information do customers need on arrival?**
3. **How do we provide real-time transit guidance during trips?**
4. **What destination-specific transport knowledge should the platform maintain?**

---

## Research Areas

### Local Transport & Navigation System

```typescript
interface LocalTransportNavigation {
  // Customer-facing guidance for getting around at travel destinations
  scope: {
    description: "Not booking transport (covered by GROUND_TRANSPORTATION_*) but guiding travelers on local transit options, routes, costs, and navigation at their destination";
    trigger: "Activated when customer arrives at destination; companion app shows local transport guide";
    value: "The #1 traveler anxiety after accommodation is 'how do I get around?' — especially for first-time international travelers";
  };

  destination_transport_profiles: {
    BANGKOK: {
      overview: "BTS Skytrain + MRT + tuk-tuk + taxi + boat";
      recommended: {
        from_airport: "Airport Rail Link to Phaya Thai → BTS to hotel area (₹200, 45 min)";
        daily_commute: "BTS Rabbit card (₹500/day unlimited) for main tourist areas";
        short_distance: "Walk (most tourist areas are walkable) or tuk-tuk (negotiate before ride)";
        river_areas: "Chao Phraya Express Boat (₹30-100, scenic and efficient)";
        nightlife: "Grab taxi (never street taxi at night — refuse meter)";
      };
      warnings: [
        "Tuk-tuk drivers may quote ₹500 for ₹100 ride — always negotiate or use meter taxi/Grab",
        "BTS and MRT close at midnight — plan late-night transport (Grab)",
        "Rush hour 7-9 AM and 5-7 PM — avoid BTS during these times",
      ];
      estimated_daily_transport_cost: "₹300-800 depending on mode";
    };

    SINGAPORE: {
      overview: "MRT + bus + Grab + walking";
      recommended: {
        from_airport: "MRT from Changi (₹100, 30 min to city) or Grab (₹800-1,200)",
        daily_commute: "Singapore Tourist Pass (₹600/day unlimited MRT + bus) or EZ-Link card",
        short_distance: "Walk (Singapore is very walkable with covered walkways)",
        sentosa: "Sentosa Express from VivoCity (₹200 round trip, included in some packages)",
        night: "MRT runs until midnight; Grab available 24/7",
      };
      warnings: [
        "No eating or drinking on MRT — ₹5,000 fine",
        "Durian not allowed on public transport",
        "Very safe at all hours — night walking is fine in tourist areas",
      ];
      estimated_daily_transport_cost: "₹400-800";
    };

    DUBAI: {
      overview: "Dubai Metro + tram + taxi + Careem";
      recommended: {
        from_airport: "Dubai Metro from Terminal 1/3 (₹100, 30 min) or taxi (₹500-800)",
        daily_commute: "Nol Card (₹300 day pass for metro + bus + tram)";
        mall_hopping: "Metro connects Dubai Mall, Mall of Emirates, Ibn Battuta",
        beach: "Tram to JBR + walk; taxi to Kite Beach",
        old_dubai: "Abra ride across Dubai Creek (₹5 — must-do experience)",
      };
      warnings: [
        "Metro has Gold Class carriage (premium, ₹100 extra — worth it for views)",
        "Women-only carriages available (pink signage)",
        "Friday is weekend — metro runs different schedule",
      ];
      estimated_daily_transport_cost: "₹500-1,200";
    };

    BALI: {
      overview: "Scooter rental + private driver + GoJek + taxi";
      recommended: {
        from_airport: "Pre-arranged hotel pickup (included in most packages)",
        daily_commute: "Hire driver for day (₹2,000-3,000/day) or rent scooter (₹400/day, license required)",
        short_distance: "GoJek/Grab bike taxi (₹50-200 per ride) — download app before trip",
        inter_area: "Private driver recommended (distances are large; roads are chaotic)";
      };
      warnings: [
        "Scooter riding without international license = illegal + insurance void",
        "Traffic in Seminyak/Kuta area is terrible — allow double the expected time",
        "Night driving is dangerous (poor lighting, drunk drivers)",
        "Download GoJek and Grab apps before arriving (essential for Bali)",
      ];
      estimated_daily_transport_cost: "₹800-3,000 (driver hire is most convenient)";
    };

    LONDON: {
      overview: "Tube + bus + Overground + Elizabeth Line + taxi + walking";
      recommended: {
        from_airport: "Elizabeth Line from Heathrow (₹1,200, 45 min) or Heathrow Express (₹2,500, 15 min)";
        daily_commute: "Visitor Oyster Card or contactless card (daily cap ₹1,500)";
        sightseeing: "Bus Route 15 (Tower Hill → Trafalgar Square — free sightseeing tour)";
        short_distance: "Walk (Central London is compact) or Santander Cycles (₹200/day)";
        river: "Uber Boat by Thames Clippers (₹400-800, scenic alternative to Tube)",
      };
      warnings: [
        "Stand on the RIGHT on escalators (left is for walking)",
        "Tube is extremely crowded 8-9:30 AM and 5-6:30 PM — avoid peak times",
        "Oyster daily cap means you never pay more than ~₹1,500/day",
      ];
      estimated_daily_transport_cost: "₹800-1,500 (with daily cap)";
    };
  };

  // ── Local transport guide — companion app view ──
  // ┌─────────────────────────────────────────────────────┐
  // │  🚇 Getting Around · Bangkok · Day 2                      │
  // │                                                       │
  // │  Your location: Near Siam BTS Station                    │
  // │                                                       │
  // │  How to get to:                                       │
  // │  🏯 Grand Palace:                                        │
  // │     BTS Siam → Saphan Taksin (3 stops)                    │
  // │     → Chao Phraya Boat to Tha Chang (15 min)             │
  // │     Total: ~30 min · ₹80                                  │
  // │     [Show Route on Map]                                   │
  // │                                                       │
  // │  🛍️ Chatuchak Market:                                    │
  // │     BTS Siam → Mo Chit (8 stops, 20 min)                 │
  // │     Total: ~25 min · ₹50                                  │
  // │     [Show Route on Map]                                   │
  // │                                                       │
  // │  Quick Tips:                                          │
  // │  💡 Your BTS Rabbit card has ₹340 balance                  │
  // │  💡 Rush hour now — expect crowded trains                  │
  // │  ⚠️ Tuk-tuk price check: Siam → Grand Palace              │
  // │     Fair price: ₹80-120 · Drivers may ask ₹500            │
  // │                                                       │
  // │  [🚕 Book Grab] [🗺️ Full Map] [🚇 BTS Map] [📞 Call Agent] │
  // └─────────────────────────────────────────────────────────┘
}
```

### Navigation & Guidance Features

```typescript
interface NavigationGuidance {
  // Real-time navigation support for travelers at destinations
  companion_app_features: {
    TRANSIT_CARD_TRACKER: {
      description: "Track transit card balance and top-up locations";
      cards: {
        bangkok: "BTS Rabbit Card — balance tracker + top-up locations near hotel",
        singapore: "EZ-Link / Tourist Pass — validity and balance tracker",
        dubai: "Nol Card — balance and top-up locations",
        london: "Oyster Card — daily cap tracker and balance",
        tokyo: "Suica / Pasmo — balance and charge locations",
      };
    };

    ROUTE_PLANNER: {
      description: "A-to-B routing using local transport";
      inputs: "Current location (GPS) + destination (from itinerary or manual)";
      output: "Step-by-step directions with estimated time, cost, and alternatives";
      special: "Walking directions optimized for tourists (scenic routes, avoid unsafe areas)";
    };

    FAIR_PRICE_INDICATOR: {
      description: "Know what a ride should cost before negotiating";
      mechanism: "Enter origin + destination → show estimated fare for each transport type";
      purpose: "Prevent tourist overcharging (especially tuk-tuks, taxis, auto-rickshaws)";
      data_source: "Crowd-sourced + agency-maintained fare database for each destination";
    };

    SAFETY_ALERTS: {
      description: "Transport-related safety information";
      examples: [
        "Don't take street taxis after midnight in Bangkok — use Grab",
        "Avoid unlicensed boats in Phuket — use agency-recommended operators",
        "Dubai Metro women-only carriage available if preferred",
        "London night bus routes — stay on well-lit routes only",
      ];
    };

    DOWNLOADABLE_GUIDES: {
      description: "Offline-accessible transport guides for each destination";
      content: [
        "Metro/subway map (PDF, works offline)",
        "Key station names in local script + English pronunciation",
        "Essential phrases for transport (How much? Where is...? Stop here)",
        "Emergency numbers and phrases",
      ];
      delivery: "Auto-downloaded to companion app when trip is confirmed";
    };
  };
}
```

---

## Open Problems

1. **Data maintenance for 50+ destinations** — Transport information changes frequently (new metro lines, route changes, fare updates). Keeping data current for every destination is a significant operational challenge.

2. **Real-time transit integration** — Connecting to live transit APIs (Google Transit, local metro APIs) for real-time arrival times and service alerts requires per-city API integrations.

3. **Offline accessibility** — Travelers often don't have data on arrival. Transport guides must be downloadable before departure and work offline.

4. **Language barriers** — Metro station names in Thai, Arabic, Japanese are incomprehensible to Indian travelers. Phonetic guides and visual maps are essential.

5. **Safety liability** — Recommending specific transport routes carries implicit safety endorsement. If a traveler is robbed on a recommended route, liability questions arise.

---

## Next Steps

- [ ] Build destination transport profile database with curated local transit guides
- [ ] Create companion app transport guide with route planner and fair price indicator
- [ ] Implement transit card balance tracker for major destination cards
- [ ] Design downloadable offline transport guides (metro maps, key phrases)
- [ ] Build safety alert system for destination-specific transport warnings
- [ ] Create fare database with fair price ranges for tourist transport at each destination
- [ ] Integrate with Google Maps / local transit APIs for real-time routing
