# Referral & Viral Engine — Integration & Program Optimization

> Research document for referral program integration with sales pipeline, CLV impact modeling, cross-channel referral orchestration, and long-term program optimization for travel agencies.

---

## Key Questions

1. **How does the referral engine integrate with the sales pipeline?**
2. **What is the CLV impact of referred customers vs. organic?**
3. **How do cross-channel referrals work end-to-end?**
4. **How do we scale and optimize the program over time?**

---

## Research Areas

### Referral-Sales Pipeline Integration

```typescript
interface ReferralSalesIntegration {
  // Referral hooks in the sales pipeline
  pipeline_touchpoints: {
    // Stage: NEW_INQUIRY
    INQUIRY_CAPTURE: {
      trigger: "New inquiry received (WhatsApp, call, walk-in)";
      referral_check: [
        "Agent asks: 'How did you hear about us?'",
        "Auto-detect referral link in URL parameters",
        "Check if phone number matches an existing referral record",
        "WhatsApp: auto-detect referral code in conversation",
      ];
      action: "If referral detected → auto-tag lead source, notify referrer";
    };

    // Stage: PROPOSAL_SENT
    PROPOSAL_REFERRAL_HOOK: {
      trigger: "Proposal sent to referred customer";
      auto_actions: [
        "Apply referral discount (₹2,000 off) to proposal",
        "Note referral source on proposal for tracking",
        "Show referrer's name as personal recommendation (with consent)",
        "Flag proposal for priority agent follow-up",
      ];
      notification_to_referrer: "Great news! {friend_name} is exploring a {destination} trip. We'll take great care of them!";
    };

    // Stage: BOOKING_CONFIRMED
    BOOKING_REWARD_TRIGGER: {
      trigger: "Referred customer confirms booking (payment received)";
      auto_actions: [
        "Verify minimum booking value (₹50,000)",
        "Run fraud check (score < 0.6 required)",
        "Queue referrer reward (₹2,000 credit)",
        "Queue referee discount application",
        "Update referral funnel analytics",
      ];
      notifications: {
        referrer: "🎉 Your friend booked! ₹2,000 travel credit added to your account. You've now referred {count} travelers!",
        referee: "Your ₹2,000 referral discount has been applied. Welcome to Waypoint Travel!",
      };
    };

    // Stage: TRIP_COMPLETED
    POST_TRIP_REFERRAL_LOOP: {
      trigger: "Referred customer completes first trip";
      auto_actions: [
        "Send NPS survey",
        "If NPS ≥ 9: trigger referral request (new referrer!)",
        "Update CLV comparison (referred vs. organic)",
        "Send referrer a thank-you (your friend loved their trip!)",
      ];
    };
  };
}

// ── Referral-sales integration ──
// ┌─────────────────────────────────────────────────────┐
// │  Referral Pipeline Integration                            │
// │                                                       │
// │  Inquiry → Proposal → Booking → Pre-trip → Trip → Post│
// │    │          │          │         │         │      │ │
// │    ▼          ▼          ▼         │         ▼      │ │
// │  Detect    Apply      Reward     │      Loop      │ │
// │  referral  discount   triggers   │      restart   │ │
// │    │        ₹2K off    both      │      new code  │ │
// │    │          │       sides      │        │       │ │
// │    └──────────┴──────────────────┴────────┘       │ │
// │                                                       │
// │  Active referred leads in pipeline:                     │
// │  ┌───────────────────────────────────────────────┐   │
// │  │ Stage          │ Count │ Avg Days │ Conv Rate  │   │
// │  │ ───────────────────────────────────────────────│   │
// │  │ Inquiry        │   6   │   —      │    —       │   │
// │  │ Qualification  │   4   │  2.1     │   67%      │   │
// │  │ Proposal Sent  │   3   │  5.3     │   75%      │   │
// │  │ Negotiation    │   2   │  3.8     │   67%      │   │
// │  │ Booking        │   1   │  1.2     │   50%      │   │
// │  │ ───────────────────────────────────────────────│   │
// │  │ Total pipeline │  16   │  12.4    │   25%      │   │
// │  │ Non-referral   │  42   │  18.7    │   14%      │   │
// │  └───────────────────────────────────────────────┘   │
// │                                                       │
// │  Referral leads convert 1.8x faster and               │
// │  79% higher rate than organic leads                   │
// │                                                       │
// │  [View Pipeline] [Referral Dashboard] [Agent Stats]     │
// └─────────────────────────────────────────────────────┘
```

### CLV Impact Modeling

```typescript
interface ReferralCLVModel {
  // Customer lifetime value comparison
  clv_analysis: {
    // Base CLV comparison
    comparison: {
      organic_customer: {
        avg_first_trip_value: "₹72,000";
        repeat_rate: "22%";
        avg_trips_per_customer: 1.4;
        avg_lifetime_spend: "₹1,00,800";
        avg_acquisition_cost: "₹2,100";
        clv_to_cac_ratio: "48x";
      };
      referred_customer: {
        avg_first_trip_value: "₹78,000";          // 8% higher (trust from referral)
        repeat_rate: "35%";                         // 59% higher
        avg_trips_per_customer: 1.9;
        avg_lifetime_spend: "₹1,48,200";
        avg_acquisition_cost: "₹4,000";            // reward cost
        clv_to_cac_ratio: "37x";
        referral_source_value: "Each referrer generates ₹1.2L avg pipeline";
      };
      ambassador_referred: {
        avg_first_trip_value: "₹92,000";          // 28% higher
        repeat_rate: "48%";                         // highest trust
        avg_trips_per_customer: 2.3;
        avg_lifetime_spend: "₹2,11,600";
        avg_acquisition_cost: "₹6,500";            // ambassador cost allocation
        clv_to_cac_ratio: "32.5x";
      };
    };

    // Network effects
    network_value: {
      viral_coefficient: 0.18;                      // each customer generates 0.18 new
      referred_customer_viral_coefficient: 0.28;    // 55% higher — they refer more
      network_amplification: "Each referral generates 0.05 additional organic leads through word-of-mouth";
    };

    // Revenue attribution model
    attribution: {
      direct_referral_revenue: "Revenue from referred bookings";
      halo_effect_revenue: "Revenue from organic leads generated by referral content";
      retention_uplift: "Revenue from higher repeat rate of referred customers";
      total_referral_influenced: "Direct + halo + retention uplift";
    };
  };
}

// ── CLV comparison dashboard ──
// ┌─────────────────────────────────────────────────────┐
// │  Referral CLV Analysis — FY 2026-27                     │
// │                                                       │
// │  ┌──────────────────────────────────────────────────┐│
// │  │ Metric          │ Organic │ Referred │ Ambassador ││
// │  │ ─────────────────────────────────────────────────││
// │  │ First trip      │ ₹72K    │ ₹78K (+8%)│ ₹92K (+28%)││
// │  │ Repeat rate     │  22%    │  35% (+59%)│ 48% (+118%)││
// │  │ Avg trips       │  1.4    │  1.9       │  2.3       ││
// │  │ Lifetime spend  │ ₹1.0L   │ ₹1.5L (+47%)│ ₹2.1L (+110%)│
// │  │ Acquisition cost│ ₹2,100  │ ₹4,000     │ ₹6,500     ││
// │  │ CLV:CAC ratio   │  48x    │  37x       │  32.5x     ││
// │  │ Time to 2nd trip│ 14 mo   │ 9 mo       │ 7 mo       ││
// │  │ Referral rate   │  4%     │  12%       │  28%       ││
// │  └──────────────────────────────────────────────────┘│
// │                                                       │
// │  Key insight: Referred customers are worth 47% more    │
// │  over their lifetime despite higher acquisition cost.  │
// │                                                       │
// │  Network value:                                        │
// │  • Each referrer generates avg ₹1.2L pipeline          │
// │  • Referred customers refer 3x more than organic       │
// │  • Ambassador-referred: 2.1x higher LTV                │
// │  • Halo effect: ₹3.2L additional revenue from          │
// │    word-of-mouth not directly tracked                  │
// │                                                       │
// │  [Detailed Model] [Export] [Sensitivity Analysis]       │
// └─────────────────────────────────────────────────────┘
```

### Cross-Channel Referral Orchestration

```typescript
interface CrossChannelReferral {
  // Referral touchpoints across all channels
  channels: {
    WHATSAPP: {
      flow: "Customer shares referral link via WhatsApp";
      format: "Pre-filled message: 'I had a great trip with Waypoint! Use my code {CODE} for ₹2,000 off: {LINK}'";
      tracking: "UTM params + referral code in link";
      conversion_path: "Link click → WhatsApp chat with agent → Inquiry → Booking";
      attribution: "First-touch (WhatsApp share) gets credit";
    };

    INSTAGRAM: {
      flow: "Customer shares trip photo/reel with referral link in story";
      format: "Trip highlight photo + 'Book with WAYPOINT for ₹2K off! Link in bio: {CODE}'";
      tracking: "UTM params + unique story link";
      conversion_path: "Story view → Link click → Landing page → WhatsApp inquiry";
      attribution: "Instagram → WhatsApp cross-channel tracked via code";
    };

    WORD_OF_MOUTH: {
      flow: "Customer verbally recommends agency to friends/family";
      format: "Customer gives referral code verbally";
      tracking: "Referee enters code at inquiry or booking";
      conversion_path: "Verbal recommendation → Customer calls/WhatsApp → Mentions code";
      attribution: "Self-reported at inquiry; code validated against referrer";
    };

    MEMORY_PRODUCT: {
      flow: "Shared memory book/video contains referral link";
      format: "Watermark + QR code + referral link on shared content";
      tracking: "QR scan tracking + UTM-tagged link";
      conversion_path: "View memory → Scan QR / click link → Landing page → Inquiry";
      attribution: "Content share → click tracked automatically";
    };

    GOOGLE_REVIEWS: {
      flow: "Customer leaves review with referral code mention";
      format: "5-star review + 'Mention code {CODE} for ₹2,000 off your trip'";
      tracking: "Code redemption at booking";
      conversion_path: "Read review → Search agency → Book with code";
      attribution: "Code match at booking";
    };
  };

  // Attribution model
  attribution_model: {
    model: "First-touch with 90-day window";
    rules: [
      "First channel where customer encountered referral gets credit",
      "90-day attribution window (referral → booking must be within 90 days)",
      "If customer encounters multiple referral sources: first touch wins",
      "Ambassador referrals always attributed to ambassador regardless of channel",
    ];
  };
}

// ── Cross-channel attribution ──
// ┌─────────────────────────────────────────────────────┐
// │  Referral Attribution — Cross-Channel                    │
// │                                                       │
// │  Channel breakdown (April 2026):                       │
// │                                                       │
// │  WhatsApp shares:     52 (43%)  ████████████████████  │
// │  Word of mouth:       28 (23%)  ███████████           │
// │  Instagram story:     18 (15%)  ███████               │
// │  Memory product:      14 (12%)  ██████                │
// │  Google reviews:       8 (7%)   ███                   │
// │  ──────────────────────────────────────────────       │
// │  Total:              120 referrals this month          │
// │                                                       │
// │  Conversion by channel:                                │
// │  Memory product:    21% ██████████                     │
// │  WhatsApp share:    15% ███████                        │
// │  Instagram story:   11% █████                          │
// │  Google reviews:     8% ████                           │
// │  Word of mouth:      7% ███                            │
// │                                                       │
// │  Cross-channel paths (top 3):                          │
// │  1. WhatsApp → Direct booking with code (38%)          │
// │  2. Word of mouth → WhatsApp inquiry (24%)             │
// │  3. Memory product → Landing page → WhatsApp (18%)     │
// │                                                       │
// │  Attribution disputes this month: 2                    │
// │  Both resolved: first-touch applied correctly           │
// │                                                       │
// │  [Attribution Settings] [Dispute Queue] [Full Report]   │
// └─────────────────────────────────────────────────────┘
```

### Long-Term Program Optimization

```typescript
interface ReferralProgramOptimization {
  // Program maturity stages
  maturity_stages: {
    STAGE_1_LAUNCH: {
      timeline: "Month 1-3";
      focus: "Get first 50 referrers, validate mechanics";
      kpis: {
        participation_rate: "2-4% of customers";
        referral_conversion: "5-10%";
        cost_per_referral: "₹400-600";
      };
      actions: [
        "Launch with simple dual-sided reward",
        "Manual approval for all rewards",
        "Track basic funnel (share → click → book)",
        "Collect customer feedback on program",
      ];
    };

    STAGE_2_GROWTH: {
      timeline: "Month 4-9";
      focus: "Optimize conversion, introduce automation";
      kpis: {
        participation_rate: "6-10% of customers";
        referral_conversion: "10-15%";
        cost_per_referral: "₹300-400";
      };
      actions: [
        "Implement smart timing triggers",
        "Launch ambassador program (5-10 ambassadors)",
        "A/B test reward amounts and formats",
        "Automate fraud detection",
        "Integrate with sales pipeline",
      ];
    };

    STAGE_3_SCALE: {
      timeline: "Month 10-18";
      focus: "Scale virality, maximize ROI";
      kpis: {
        participation_rate: "12-18% of customers";
        referral_conversion: "15-20%";
        cost_per_referral: "₹250-350";
        revenue_share: "5-8% of total revenue";
      };
      actions: [
        "Full viral loop automation",
        "Ambassador program at scale (20+ ambassadors)",
        "Cross-channel attribution",
        "Social proof automation pipeline",
        "Referral leaderboard and gamification",
      ];
    };

    STAGE_4_OPTIMIZE: {
      timeline: "Month 18+";
      focus: "Continuous optimization, defensibility";
      kpis: {
        participation_rate: "20%+ of customers";
        referral_conversion: "20%+";
        revenue_share: "10%+ of total revenue",
        viral_coefficient: "0.25+",
      };
      actions: [
        "ML-driven optimization of triggers and templates",
        "Personalized reward structures by customer segment",
        "Referral program as competitive moat",
        "Partner referral programs (hotels, airlines, experiences)",
      ];
    };
  };

  // Optimization levers
  levers: {
    REWARD_STRUCTURE: "Adjust amounts, tiers, and reward types based on conversion data";
    TIMING_OPTIMIZATION: "ML model to predict optimal referral request moment per customer";
    CHANNEL_MIX: "Shift investment to highest-conversion channels";
    FRICTION_REDUCTION: "Simplify sharing flow (1-click share, auto-populated messages)";
    SOCIAL_PROOF: "More testimonials, better content, emotional storytelling";
    GAMIFICATION: "Leaderboards, badges, milestones, public recognition";
  };
}

// ── Program optimization roadmap ──
// ┌─────────────────────────────────────────────────────┐
// │  Referral Program — Optimization Roadmap                 │
// │                                                       │
// │  Current stage: STAGE 2 (Growth) · Month 6             │
// │  Next milestone: 15% participation rate (currently 8%)  │
// │                                                       │
// │  ──── ──── ──── ──── ──── ──── ──── ──── ──── ────  │
// │  LAUNCH ████████ GROWTH ████████ SCALE ██████ OPTIMIZE │
// │  ✓            ↑YOU                                    │
// │                                                       │
// │  Optimization experiments running:                    │
// │  🧪 Video vs photo share format (Week 3 of 4)         │
// │  🧪 ₹2K vs ₹3K referrer reward (Week 2 of 6)         │
// │  🧪 Memory share vs NPS timing trigger (Week 1 of 4)  │
// │                                                       │
// │  Next quarter priorities:                              │
// │  1. Launch ambassador program (target: 8 ambassadors)  │
// │  2. Automate social proof pipeline                     │
// │  3. Implement cross-channel attribution                │
// │  4. Integrate with post-trip engagement sequences      │
// │                                                       │
// │  Projected impact (next quarter):                     │
// │  • Referral revenue: ₹4.7L → ₹8.2L (+74%)            │
// │  • Active referrers: 48 → 80 (+67%)                   │
// │  • Participation rate: 8% → 15%                        │
// │  • Revenue share: 3.2% → 5.5%                         │
// │                                                       │
// │  [View Experiments] [Update Roadmap] [Export Plan]      │
// └─────────────────────────────────────────────────────┘
```

---

## Open Problems

1. **Attribution decay** — Referral links expire, cookies get cleared, customers forget codes. Need multiple attribution signals (code, phone match, self-report) to capture true referral volume.

2. **Reward inflation** — As referral programs scale, reward costs grow. Need dynamic reward adjustment based on customer segment value and marginal conversion benefit.

3. **Competitor copying** — Successful referral programs get copied. Need to build program uniqueness through experiences (memory products, ambassador community) rather than just reward amounts.

4. **Measurement of halo effect** — Referred customers improve team morale, social proof, and brand perception. These are hard to quantify but real. Need proxy metrics (social media mentions, inbound inquiry quality).

---

## Next Steps

- [ ] Build referral-sales pipeline integration with stage-based triggers
- [ ] Implement CLV tracking for referred vs. organic customer cohorts
- [ ] Create cross-channel attribution with first-touch model
- [ ] Design program optimization roadmap with maturity stages
