# Dynamic Packaging Engine — Customization & Personalization

> Research document for package customization workflows, preference-based personalization, intelligent upselling, and customer-facing package configuration for travel agencies.

---

## Key Questions

1. **How do customers customize pre-built packages?**
2. **What personalization creates the most value?**
3. **How do we intelligently upsell within packages?**
4. **What does the customer-facing package configurator look like?**

---

## Research Areas

### Package Customization Workflows

```typescript
interface PackageCustomization {
  // How agents and customers modify packages
  workflows: {
    AGENT_LED: {
      description: "Agent customizes package based on customer conversation";
      steps: [
        "Start with template or create from scratch",
        "Select components based on customer preferences",
        "Adjust for budget constraints (swap/downgrade)",
        "Apply personalization (dietary, accessibility, celebrations)",
        "Generate proposal with customization notes",
      ];
      tools: ["Component swap suggestions", "Budget optimizer", "Alternative finder"];
    };

    CUSTOMER_SELF_SERVICE: {
      description: "Customer customizes via website/WhatsApp";
      steps: [
        "Customer selects base package",
        "Presented with customization options per component",
        "Real-time price updates as they customize",
        "Save and share for family discussion",
        "Submit for agent review and confirmation",
      ];
      guardrails: [
        "Cannot remove mandatory components (flights, hotel)",
        "Budget alerts when exceeding stated range",
        "Agent review required before final booking",
      ];
    };

    HYBRID: {
      description: "Agent builds initial proposal, customer fine-tunes";
      steps: [
        "Agent creates tailored base package",
        "Customer receives interactive proposal (WhatsApp/web)",
        "Customer can swap activities, upgrade hotel, add meals",
        "Changes auto-priced and sent back to agent for approval",
        "Agent confirms or adjusts and locks package",
      ];
    };
  };

  // Customization options per component
  customization_options: {
    HOTEL: {
      swap: "Change hotel within same area";
      upgrade: "Upgrade room type or star category";
      meal_plan: "Add breakfast, half-board, full-board, all-inclusive";
      special_requests: "Early check-in, late checkout, adjoining rooms, accessibility";
      extension: "Add extra nights (pre-trip or post-trip)";
    };

    ACTIVITY: {
      swap: "Replace one activity with another of similar type";
      add: "Add activities (subject to schedule fit)";
      remove: "Remove activity (credit applied to package)";
      upgrade: "Standard → VIP/private tour";
      schedule: "Move activity to different day";
    };

    FLIGHT: {
      airline: "Change airline (price difference applies)";
      timing: "Earlier/later departure (subject to availability)";
      class: "Economy → Premium Economy → Business";
      route: "Direct vs. connecting (price and duration tradeoff)";
    };

    TRANSFER: {
      vehicle: "Sedan → SUV → Van (based on group size + luggage)";
      type: "Shared → Private → Luxury";
      add: "Add inter-city transfers or day-use vehicle";
    };

    ADD_ONS: {
      meals: "Add meal plan, restaurant reservations, food tour";
      insurance: "Upgrade coverage, add adventure sports rider";
      sim_card: "Add international SIM/eSIM";
      forex: "Add forex card delivery";
      photographer: "Add trip photography package";
      celebration: "Birthday/anniversary surprise package";
    };
  };
}

// ── Package customization UI ──
// ┌─────────────────────────────────────────────────────┐
// │  Customize Your Singapore Trip                           │
// │  Base: Singapore Family — 5N/6D · ₹2,23,500            │
// │                                                       │
// │  ┌─ Hotel ──────────────────────────────────────────┐│
// │  │ Currently: Village Hotel (3★) · ₹30,000          ││
// │  │                                                   ││
// │  │ Upgrade options:                                  ││
// │  │ ○ Village Hotel (3★) — included          ₹0       ││
// │  │ ● Pan Pacific (4★) — recommended      +₹12,500   ││
// │  │ ○ Marina Bay Sands (5★) — luxury      +₹38,000   ││
// │  │                                                   ││
// │  │ Meal plan:                                        ││
// │  │ ☑ Breakfast included                              ││
// │  │ ☐ Add half-board (breakfast + dinner) +₹8,500    ││
// │  └───────────────────────────────────────────────────┘│
// │                                                       │
// │  ┌─ Activities ─────────────────────────────────────┐│
// │  │ Selected:                                         ││
// │  │ ✅ Universal Studios · Day 2 · ₹6,800            ││
// │  │ ✅ Gardens by the Bay · Day 4 · ₹2,400           ││
// │  │                                                   ││
// │  │ Available to add:                                 ││
// │  │ ☐ Sentosa Luge + Beach · Day 3 · ₹1,800         ││
// │  │ ☐ River Safari · Day 4 · ₹2,200                  ││
// │  │ ☐ Night Safari (VIP) · Day 3 · ₹4,500            ││
// │  │                                                   ││
// │  │ [See All 12 Activities]                            ││
// │  └───────────────────────────────────────────────────┘│
// │                                                       │
// │  ┌─ Special Occasions ──────────────────────────────┐│
// │  │ ☐ Birthday surprise package · ₹3,500             ││
// │  │   (cake + decoration + photographer 1hr)          ││
// │  │ ☐ Anniversary dinner · ₹5,000                    ││
// │  │   (riverside restaurant + bouquet)                ││
// │  └───────────────────────────────────────────────────┘│
// │                                                       │
// │  Updated Total: ₹2,36,000 (+₹12,500 for hotel upgrade) │
// │                                                       │
// │  [Save Changes] [Reset to Base] [Submit for Review]     │
// └─────────────────────────────────────────────────────┘
```

### Preference-Based Personalization

```typescript
interface PreferencePersonalization {
  // Personalize packages based on customer profile
  personalization: {
    // Customer profile signals
    signals: {
      EXPLICIT: {
        source: "Customer tells agent or fills preference form";
        examples: ["We prefer vegetarian food", "Kids love animals", "We want luxury hotels", "Budget max ₹2.5L"];
        reliability: "HIGH — directly stated";
      };

      BEHAVIORAL: {
        source: "Past booking and browsing behavior";
        examples: ["Always books 4-star+", "Prefers morning flights", "Books 3+ months in advance", "Never adds adventure activities"];
        reliability: "MEDIUM — inferred from patterns";
      };

      DEMOGRAPHIC: {
        source: "Traveler demographics";
        examples: [
          "Family with kids under 10 → family-friendly activities, shorter travel days",
          "Couple 25-35 → romantic activities, Instagram-worthy spots",
          "Senior travelers → accessibility, comfortable pace, cultural sites",
          "Group of friends → adventure, nightlife, budget-conscious",
        ];
        reliability: "LOW-MEDIUM — generalizations";
      };

      SEASONAL: {
        source: "Time of year and destination conditions";
        examples: ["June in Singapore → indoor activities for midday heat", "December in Europe → Christmas markets, shorter sightseeing days"];
        reliability: "HIGH — objective conditions";
      };
    };

    // Personalization engine
    engine: {
      INPUT: "Customer profile + destination + dates + budget + traveler mix";
      PROCESS: [
        "Match against successful past packages for similar profiles",
        "Score each component by relevance to customer preferences",
        "Filter by budget constraints",
        "Apply seasonal adjustments",
        "Generate ranked component recommendations",
      ];
      OUTPUT: "Personalized package with confidence score per component";
    };
  };

  // Personalization examples
  examples: {
    FAMILY_YOUNG_KIDS: {
      profile: "2 adults + 2 children (ages 5, 8)";
      recommendations: {
        hotel: "Family suite with kids pool (vs. business hotel)";
        activities: ["Zoo/Safari", "Science Center", "Beach day", "Theme park (kiddie rides)"];
        pace: "Max 1 activity per day, return to hotel by 4 PM for rest";
        meals: "Restaurants with kids menus, avoid spicy/exotic";
      };
    };

    COUPLE_HONEYMOON: {
      profile: "Newlywed couple, ages 28-30";
      recommendations: {
        hotel: "Boutique resort with private pool/villa";
        activities: ["Sunset cruise", "Couples spa", "Photography session", "Fine dining"];
        pace: "Flexible — leisurely mornings, one highlight per day";
        meals: "Include at least 2 romantic/special dinners";
      };
    };

    SENIOR_COUPLE: {
      profile: "Couple, ages 60-65";
      recommendations: {
        hotel: "Central location, elevator, accessible bathroom";
        activities: ["Cultural sites", "Gardens", "Museums", "Guided tours (no self-drive)"];
        pace: "Slow — one morning activity, afternoon rest, optional evening activity";
        meals: "Include familiar Indian food options, avoid excessive walking to restaurants";
      };
    };
  };
}

// ── Personalization engine ──
// ┌─────────────────────────────────────────────────────┐
// │  Package Personalization                                 │
// │  Customer: Sharma Family · Profile: Family w/ kids       │
// │                                                       │
// │  Based on: 2 past trips + stated preferences            │
// │                                                       │
// │  Recommended package adjustments:                      │
// │  ┌───────────────────────────────────────────────┐   │
// │  │ 🏨 Hotel: Change to Village Hotel              │   │
// │  │ Why: Kid-friendly pool, playground, family      │   │
// │  │ rooms. Score: 92% match.                        │   │
// │  │ Confidence: HIGH (booked similar before)        │   │
// │  │ [Apply] [Keep Current]                           │   │
// │  │                                                 │   │
// │  │ 🎢 Activity: Replace Night Safari → Zoo          │   │
// │  │ Why: Kids 5 & 8 prefer animals they can see.    │   │
// │  │ Night Safari may be too dark/scary for 5yo.     │   │
// │  │ Score: 88% match. Saves ₹400.                   │   │
// │  │ [Apply] [Keep Current]                           │   │
// │  │                                                 │   │
// │  │ 🍽️ Add: Indian restaurant reservation           │   │
// │  │ Why: Day 3 dinner — previous trip feedback        │   │
// │  │ mentioned missing Indian food.                   │   │
// │  │ Cost: ₹2,200 for family.                         │   │
// │  │ [Add] [Skip]                                     │   │
// │  └───────────────────────────────────────────────┘   │
// │                                                       │
// │  If all applied: ₹2,25,700 (+₹2,200 for dinner)        │
// │  Personalization score: 94%                            │
// │                                                       │
// │  [Apply All] [Customize Further] [View Reasoning]       │
// └─────────────────────────────────────────────────────┘
```

### Intelligent Upsell Engine

```typescript
interface IntelligentUpsell {
  // Context-aware upselling within packages
  upsell_triggers: {
    HOTEL_UPGRADE: {
      trigger: "Customer selects 3-star hotel for honeymoon trip";
      suggestion: "Upgrade to boutique 4-star with pool (+₹12,500)";
      reasoning: "Honeymoon travelers in this segment upgrade 68% of the time";
      pitch: "Since it's your honeymoon, would you like a hotel with a private pool? Just ₹12,500 more for a much more special experience.";
      acceptance_rate: "42%";
      margin_impact: "+₹4,200 margin (34% margin on upgrade)";
    };

    ACTIVITY_UPGRADE: {
      trigger: "Customer selects standard theme park ticket";
      suggestion: "Upgrade to VIP express pass (+₹3,500/family)";
      reasoning: "June = peak season, queue times 60-90 min per ride";
      pitch: "June is peak season at Universal — queues can be 90 minutes. With the VIP express pass, you skip the lines. Worth it with kids!";
      acceptance_rate: "55%";
      margin_impact: "+₹1,400 margin";
    };

    INSURANCE_UPSELL: {
      trigger: "Customer books international trip without comprehensive insurance";
      suggestion: "Upgrade to comprehensive coverage with adventure sports (+₹1,200)";
      reasoning: "Trip includes activities that basic insurance doesn't cover";
      pitch: "Your trip includes Sentosa activities that aren't covered by basic insurance. For ₹1,200 more, you get full coverage including adventure activities.";
      acceptance_rate: "38%";
    };

    MEAL_PLAN: {
      trigger: "Customer on 5+ night trip with breakfast-only plan";
      suggestion: "Add half-board plan (+₹8,500 for family)";
      reasoning: "Families with kids benefit from pre-planned dinners, saves daily decision fatigue";
      pitch: "With the half-board plan, dinners are sorted at the hotel restaurant. No hunting for places after a long day of sightseeing — especially helpful with kids!";
      acceptance_rate: "35%";
    };

    PHOTOGRAPHY: {
      trigger: "Customer on honeymoon or special occasion trip";
      suggestion: "Add professional photography session (+₹5,000)";
      reasoning: "Couples on special trips value high-quality memories";
      pitch: "Capture your special moments with a professional photographer at Gardens by the Bay. 30 edited photos delivered within 48 hours.";
      acceptance_rate: "28%";
    };
  };

  // Upsell rules
  rules: {
    MAX_UPSELLS_PER_PACKAGE: 3;             // Don't overwhelm customer
    TOTAL_UPSELL_BUDGET_IMPACT: "Max 15% of base package price";
    TIMING: "Present after base package agreed, before final pricing";
    TONE: "Helpful suggestion, not pushy. Always include 'no thanks' prominently";
    VALUE_FIRST: "Lead with benefit, not price. Price is secondary information";
  };
}

// ── Upsell suggestions ──
// ┌─────────────────────────────────────────────────────┐
// │  Smart Add-ons — Sharma Singapore Trip                   │
// │                                                       │
// │  Based on your trip, here are some recommendations:   │
// │                                                       │
// │  ┌───────────────────────────────────────────────┐   │
// │  │ 🎢 Skip the queues at Universal!              │   │
// │  │ VIP Express Pass · +₹3,500 for family          │   │
// │  │ June = 90 min queues. VIP = walk right in.     │   │
// │  │ [Add to Package] [No Thanks]                    │   │
// │  └───────────────────────────────────────────────┘   │
// │                                                       │
// │  ┌───────────────────────────────────────────────┐   │
// │  │ 📸 Professional photos at Gardens by the Bay  │   │
// │  │ 30 edited photos · +₹5,000                     │   │
// │  │ Perfect for the family album!                  │   │
// │  │ [Add to Package] [No Thanks]                    │   │
// │  └───────────────────────────────────────────────┘   │
// │                                                       │
// │  ┌───────────────────────────────────────────────┐   │
// │  │ 🍽️ Pre-book Indian restaurant (Day 3)          │   │
// │  │ Family dinner at Punjab Grill · +₹2,200         │   │
// │  │ Kids-friendly options available                 │   │
// │  │ [Add to Package] [No Thanks]                    │   │
// │  └───────────────────────────────────────────────┘   │
// │                                                       │
// │  Total if all added: +₹10,700 (4.8% of base)          │
// │                                                       │
// │  [Skip All Add-ons] [Add Selected]                      │
// └─────────────────────────────────────────────────────┘
```

### Customer-Facing Package Configurator

```typescript
interface PackageConfigurator {
  // Customer-facing interactive package builder
  modes: {
    TEMPLATE_START: {
      flow: "Select template → Customize components → See live pricing → Submit for review";
      best_for: "Customers who want a guided experience with popular options";
    };

    DESTINATION_START: {
      flow: "Select destination → Select dates → Answer preferences quiz → Get personalized package → Customize";
      best_for: "Customers who know where they want to go but need help planning";
    };

    BLANK_CANVAS: {
      flow: "Select destination + dates → Add components one by one → Build from scratch";
      best_for: "Experienced travelers who know exactly what they want";
    };

    BUDGET_FIRST: {
      flow: "Enter budget → Select destination → Get best package within budget → Customize tradeoffs";
      best_for: "Price-sensitive customers who want to maximize value";
    };
  };

  // Interactive pricing
  live_pricing: {
    format: "₹{total} (+₹{delta} from base)";
    updates: "Real-time as customer adds/removes/swaps components";
    breakdown: "Tap total to see per-component pricing";
    savings: "Show 'You save ₹{X} vs booking individually'";
    emi: "Show EMI option: ₹{monthly} × {months} months";
  };

  // Sharing & collaboration
  sharing: {
    FAMILY_LINK: "Share package with family members for input";
    AGENT_REVIEW: "Submit customized package for agent review";
    WHATSAPP_SHARE: "Share package summary on WhatsApp for discussion";
    SAVE_FOR_LATER: "Save package to resume within 7 days";
  };
}

// ── Customer configurator (mobile/web) ──
// ┌─────────────────────────────────────────────────────┐
// │  ✈️ Build Your Singapore Trip                            │
// │  Jun 15-20 · 2 Adults + 2 Children                      │
// │                                                       │
// │  ┌─ Quick Builder ─────────────────────────────────┐│
// │  │                                                   ││
// │  │  Step 1 of 4: Choose your vibe ✨                 ││
// │  │                                                   ││
// │  │  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐               ││
// │  │  │ 🏖️  │ │ 🎢  │ │ 🍽️  │ │ 🌿  │               ││
// │  │  │Relax│ │Fun  │ │Food │ │Nature│              ││
// │  │  └─────┘ └─────┘ └─────┘ └─────┘               ││
// │  │  (Select all that apply)                          ││
// │  │                                                   ││
// │  │  Your budget range?                               ││
// │  │  [₹1.5L] ──────●────── [₹3.0L]                   ││
// │  │                                                   ││
// │  │  Hotel preference?                                ││
// │  │  ○ Budget-friendly  ● Comfortable  ○ Luxury       ││
// │  │                                                   ││
// │  │                         [Next: See Your Trip →]    ││
// │  └───────────────────────────────────────────────────┘│
// │                                                       │
// │  📱 Share with family: [WhatsApp] [Link]                 │
// │  💬 Questions? Chat with an agent                        │
// └─────────────────────────────────────────────────────┘
```

---

## Open Problems

1. **Customization vs. simplicity** — Too many options overwhelm customers. Need progressive disclosure: simple choices first, advanced options on request. The paradox of choice applies heavily to travel.

2. **Personalization privacy** — Using behavioral data for recommendations requires customer consent (DPDP Act). Need transparent "Why are you suggesting this?" explanations.

3. **Upsell fatigue** — Aggressive upselling damages trust. Need to limit suggestions to genuinely valuable add-ons and respect customer signals (if they say no once, stop suggesting).

4. **Price transparency in customization** — Customers want to see what each component costs, but revealing margins leads to negotiation on every item. Need to show "value" (save vs. individual booking) without revealing component-level margins.

---

## Next Steps

- [ ] Build package customization workflows (agent-led and self-service)
- [ ] Implement preference-based personalization engine
- [ ] Create intelligent upsell system with contextual triggers
- [ ] Design customer-facing package configurator with live pricing
