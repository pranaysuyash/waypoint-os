# Customer Onboarding Journey — First-Touch to First-Trip

> Research document for the customer onboarding experience, from first inquiry and trust-building to profile creation, preference capture, payment setup, and first booking completion for the Waypoint OS platform.

---

## Key Questions

1. **What is the ideal first-time customer experience?**
2. **How do we build trust before the first booking?**
3. **What data needs to be captured during onboarding?**
4. **How does onboarding differ by channel (WhatsApp, website, walk-in)?**

---

## Research Areas

### Customer Onboarding Journey Map

```typescript
interface CustomerOnboardingJourney {
  // First-time customer experience from inquiry to first trip
  journey_stages: {
    STAGE_1_DISCOVERY: {
      description: "Customer discovers the agency and makes first contact";
      channels: {
        whatsapp_inquiry: "WhatsApp message from ad, referral link, or Google search";
        website_visit: "Landing page → chat widget or inquiry form";
        instagram_dm: "Instagram post/story → DM inquiry";
        phone_call: "Direct call from Google Business listing";
        walk_in: "Walk-in to agency office";
        referral: "Friend/family refers → WhatsApp or phone contact";
      };
      first_response_sla: "<30 minutes during business hours, <2 hours after hours";
      first_message_template: `
        Hi {name}! Thanks for reaching out to Waypoint Travel. 🌍
        I'm {agent_name}, and I'd love to help plan your trip.

        To get started, could you tell me:
        1. Where are you planning to travel?
        2. When are you planning to go?
        3. How many travelers?

        Or if you're still exploring, I can suggest some options!
      `;
    };

    STAGE_2_TRUST_BUILDING: {
      description: "Establish credibility before asking for commitment";
      trust_signals: {
        social_proof: "Share recent trip photos, customer testimonials, Google reviews link";
        credentials: "IATA accredited · Ministry of Tourism recognized · 500+ happy travelers";
        transparency: "Upfront about pricing, no hidden fees, clear cancellation policy";
        expertise: "Show destination knowledge — 'I've personally planned 50+ Singapore trips'";
      };
      micro_commitments: [
        "Free destination guide PDF sent via WhatsApp",
        "Quick budget estimate (no commitment needed)",
        "Customer portal access to browse packages",
        "Invite to WhatsApp broadcast for travel deals",
      ];
    };

    STAGE_3_PROFILE_CAPTURE: {
      description: "Collect customer details needed for trip planning";
      data_collected: {
        essential: {
          name: "Full name (as on passport)";
          phone: "Primary phone number (WhatsApp)";
          email: "Email for booking confirmations";
          travelers: "Number and ages of travelers";
        };
        preference: {
          travel_style: "Budget / Mid-range / Luxury / Mixed";
          interests: "Beach, culture, adventure, food, nightlife, nature, shopping";
          pace: "Relaxed / Moderate / Packed";
          dietary: "Vegetarian, vegan, halal, allergies";
          special_needs: "Mobility, infant, senior, accessibility needs";
        };
        deferred: {
          passport_details: "Collected after booking, not during onboarding";
          payment_info: "Collected at payment stage, not during profiling";
          id_proofs: "Collected during visa/booking process";
        };
      };
      principle: "Ask for the minimum needed to plan; collect more as trust builds";
    };

    STAGE_4_FIRST_PROPOSAL: {
      description: "Present first trip proposal to the customer";
      delivery: {
        format: "Rich WhatsApp message with itinerary summary + PDF attachment";
        content: {
          destination_summary: "3-4 line pitch for why this destination suits them";
          itinerary_highlights: "Day-by-day summary with key activities";
          pricing: "All-inclusive price with clear breakdown (flights, hotel, activities, visa)";
          inclusions: "What's included and what's extra (meals, transfers, insurance)";
          validity: "Quote valid for X days — prices may change after that";
        };
      };
      follow_up: "If no response in 24 hours → gentle follow-up with one modification";
    };

    STAGE_5_BOOKING_COMMITMENT: {
      description: "Convert proposal to confirmed booking";
      steps: {
        confirmation: "Customer confirms itinerary and pricing";
        advance_payment: "10-25% advance to lock booking (payment link via WhatsApp)";
        document_collection: "Passport copies, ID proofs for visa processing";
        booking_confirmation: "Detailed confirmation with booking references sent within 24 hours";
        portal_access: "Customer portal activated with trip details and documents";
      };
    };

    STAGE_6_PRE_TRIP_HANDHOLDING: {
      description: "Guide first-time customer through pre-trip preparation";
      touchpoints: {
        visa_update: "Visa status update via WhatsApp (applied → approved → collected)";
        payment_reminders: "Balance payment reminder 30 days, 15 days, 7 days before trip";
        packing_guide: "Destination-specific packing list and weather forecast";
        app_onboarding: "Companion app link with 'Add to Home Screen' instructions";
        pre_trip_call: "Agent calls 2-3 days before departure for final walkthrough";
        emergency_contacts: "Emergency card shared with all travelers before departure";
      };
    };
  };

  // ── Customer onboarding dashboard ──
  // ┌─────────────────────────────────────────────────────┐
  // │  Customer Onboarding · Sharma Family                       │
  // │  Source: WhatsApp · Agent: Priya · Stage: Proposal          │
  // │                                                       │
  // │  Journey Progress:                                    │
  // │  ✅ Inquiry received · Apr 25 · WhatsApp                  │
  // │  ✅ Trust building · Shared testimonials + 3 trip photos   │
  // │  ✅ Profile captured · Family of 3, culture + food focus   │
  // │  🔵 Proposal sent · Singapore 5D/4N · ₹1.2L · Apr 27      │
  // │  ○ Booking commitment · Awaiting response                 │
  // │  ○ Pre-trip handholding                                   │
  // │                                                       │
  // │  Customer Profile:                                     │
  // │  Rajesh Sharma · +91-98765-XXXX · rajesh@email.com        │
  // │  Family: 2 adults + 1 child (age 8)                       │
  // │  Style: Mid-range · Interests: Culture, Nature, Food       │
  // │  Diet: Vegetarian · Pace: Moderate                         │
  // │                                                       │
  // │  Next Actions:                                        │
  // │  • Follow up on proposal (sent 2 days ago)               │
  // │  • Customer viewed the PDF 3 times (high interest)        │
  // │  [Send Follow-up] [Modify Proposal] [Call Customer]       │
  // └─────────────────────────────────────────────────────────┘
}
```

### Channel-Specific Onboarding Flows

```typescript
interface ChannelOnboardingFlows {
  // Onboarding adapted for different first-contact channels
  channels: {
    WHATSAPP: {
      flow: "Inquiry → Agent greeting → Quick questions → Proposal → Booking";
      advantage: "Conversational, high engagement, rich media support";
      timeline: "3-7 days from inquiry to booking (if responsive)";
      conversion_rate: "30-40% of inquiries convert to first booking";
    };

    WEBSITE: {
      flow: "Landing page → Chat widget or inquiry form → Agent callback → Proposal";
      advantage: "Captures intent with destination/budget already specified";
      timeline: "5-10 days (includes callback scheduling)";
      conversion_rate: "15-25% (higher intent but more friction)";
    };

    INSTAGRAM: {
      flow: "Post/story view → DM inquiry → Agent responds → Move to WhatsApp";
      advantage: "Visual inspiration already established; customer is interested";
      timeline: "7-14 days (casual browsing → serious planning)";
      conversion_rate: "10-20% (younger demographic, longer decision cycle)";
    };

    REFERRAL: {
      flow: "Referrer shares agent contact → New customer reaches out → Agent mentions referrer";
      advantage: "Pre-built trust from friend/family recommendation";
      timeline: "2-5 days (fastest conversion — trust is pre-established)";
      conversion_rate: "50-60% (highest — trust transfer from referrer)";
      referral_incentive: "₹500-2000 credit for referrer on successful booking";
    };

    WALK_IN: {
      flow: "Walk-in → Agent greeting → Sit-down consultation → Proposal printed/emailed";
      advantage: "Face-to-face trust, immediate engagement, can show brochures";
      timeline: "1-3 days (fastest for on-premise conversion)";
      conversion_rate: "40-50% (high intent — they came to your office)";
    };
  };
}

// ── Onboarding conversion funnel ──
// ┌─────────────────────────────────────────────────────┐
// │  Onboarding Funnel · Last 30 days                          │
// │                                                       │
// │  Inquiries received:        120 ━━━━━━━━━━━━━━━━━━  │
// │  Profile captured:           89 ━━━━━━━━━━━━━━━     │
// │  Proposal sent:              72 ━━━━━━━━━━━━        │
// │  Booking confirmed:          31 ━━━━━━              │
// │  Pre-trip complete:          28 ━━━━━               │
// │                                                       │
// │  Conversion rates:                                     │
// │  Inquiry → Profile:      74%                          │
// │  Profile → Proposal:     81%                          │
// │  Proposal → Booking:     43%                          │
// │  Overall conversion:     26%                          │
// │                                                       │
// │  By channel:                                           │
// │  Referral:   55%  ████████████████                    │
// │  Walk-in:    48%  ██████████████                      │
// │  WhatsApp:   38%  ███████████                         │
// │  Website:    22%  ██████                              │
// │  Instagram:  17%  █████                               │
// │                                                       │
// │  [Improve Funnel] [A/B Test Proposals]                    │
// └─────────────────────────────────────────────────────┘
```

### Onboarding Optimization

```typescript
interface OnboardingOptimization {
  // Improving first-time customer conversion
  optimizations: {
    RESPONSE_SPEED: {
      finding: "Inquiries responded to within 15 minutes convert at 3x rate vs. 2+ hours";
      target: "<30 minutes for all channels during business hours";
      automation: "Auto-acknowledge WhatsApp inquiries immediately while agent prepares";
    };

    PROPOSAL_QUALITY: {
      finding: "Proposals with photos and day-by-day detail convert at 2x vs. text-only";
      components: [
        "Destination hero image (stunning photo of key landmark)",
        "Day-by-day itinerary with activity images",
        "Clear pricing breakdown with 'what's included' callout",
        "Customer testimonials from similar trip profiles",
        "Urgency element: 'Prices valid for 3 days' or 'Only 2 rooms left at this rate'",
      ];
    };

    TRUST_ACCELERATORS: {
      finding: "Customers who see social proof in first interaction convert 40% faster";
      tactics: [
        "Share Google Reviews link (4.8 stars, 200+ reviews)",
        "Show photos from recent similar trips (same destination, family type)",
        "Mention IATA accreditation and Tourism Ministry recognition",
        "Offer video call to walk through proposal personally",
      ];
    };

    FOLLOW_UP_CADENCE: {
      finding: "70% of conversions happen after the 3rd-5th follow-up contact";
      schedule: [
        "Day 0: Proposal sent",
        "Day 1: Follow-up with one modification option",
        "Day 3: Share a relevant article or tip about the destination",
        "Day 5: Gentle check-in — 'Still thinking about Singapore?'",
        "Day 7: Final follow-up or offer to modify the plan",
        "Day 14: Re-engage with different destination or deal if no response",
      ];
      principle: "Persistent but not pushy — provide value in each touchpoint, not just 'did you decide?'";
    };
  };
}
```

---

## Open Problems

1. **Data collection friction** — Asking too many questions upfront kills momentum. Need progressive profiling: collect essential data first, enrich profile over time. The customer should feel helped, not interrogated.

2. **Proposal-to-booking gap** — 43% proposal-to-booking conversion means 57% drop off. Common reasons: price shock, found cheaper option online, trip dates changed, just browsing. Need better price anchoring and urgency signals.

3. **Channel attribution** — Customer discovers on Instagram, inquires via WhatsApp, refers to spouse who calls — which channel gets credit? Multi-touch attribution needed for marketing budget allocation.

4. **First-time vs. repeat onboarding** — Repeat customers should skip all onboarding stages. The system should recognize returning customers and go directly to "Welcome back, what's next?" with pre-filled preferences.

5. **Digital reluctance** — Some customers (especially older demographics) resist portal/app adoption. Need to offer full-service WhatsApp-only experience as an alternative to self-service portal.

---

## Next Steps

- [ ] Build customer onboarding journey tracker in agent dashboard
- [ ] Create channel-specific onboarding templates (WhatsApp, website, Instagram)
- [ ] Implement progressive profiling with staged data collection
- [ ] Design proposal generator with photos, testimonials, and pricing breakdown
- [ ] Build onboarding funnel analytics with conversion tracking
