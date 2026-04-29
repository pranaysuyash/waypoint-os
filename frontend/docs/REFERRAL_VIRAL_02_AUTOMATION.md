# Referral & Viral Engine — Automation & Optimization

> Research document for automated referral request timing, social proof generation, referral analytics, and viral engine optimization for travel agencies.

---

## Key Questions

1. **When is the optimal time to ask for referrals?**
2. **How do we automate social proof generation?**
3. **What analytics track referral program health?**
4. **How do we optimize the viral engine over time?**

---

## Research Areas

### Smart Referral Request Timing

```typescript
interface ReferralTimingEngine {
  // AI-driven referral request timing
  optimal_timing: {
    // Signal-based triggers (not calendar-based)
    triggers: {
      HIGH_NPS: {
        signal: "Customer rates trip 9 or 10";
        delay: "3 days after rating";
        template: "So glad you loved your trip! If any friends or family are planning travel, we'd love to help. Share your referral code for ₹2,000 off for them + ₹2,000 credit for you: {code}";
        conversion_rate: "12%";
      };

      MEMORY_SHARE: {
        signal: "Customer shares memory book externally";
        delay: "1 hour after share detected";
        template: "Your Singapore memories look amazing! Want to help friends create similar memories? Share your link: {link} — they get ₹2,000 off!",
        conversion_rate: "18%";
      };

      REPEAT_BOOKING: {
        signal: "Customer books second trip";
        delay: "After payment confirmation";
        template: "Welcome back! As a returning traveler, you can now earn ₹2,000 for every friend you refer. Your code: {code}",
        conversion_rate: "8%";
      };

      POSTIVE_WHATSAPP: {
        signal: "Customer sends positive message on WhatsApp";
        delay: "Same conversation, after acknowledging their feedback";
        template: "Thank you! 🙏 Your kind words mean a lot. If you know anyone planning a trip, we'd be grateful for the recommendation. Here's a ₹2,000 discount for them: {link}",
        conversion_rate: "6%";
      };

      ANNIVERSARY: {
        signal: "Trip return anniversary (1 year)";
        delay: "On anniversary date";
        template: "Happy anniversary! 🎉 It's been a year since your Singapore trip. Planning your next adventure? Here's ₹2,000 off — and if you bring a friend, they get ₹2,000 too!",
        conversion_rate: "4%";
      };
    };
  };
}

// ── Referral timing engine ──
// ┌─────────────────────────────────────────────────────┐
// │  Referral Timing — Smart Triggers                        │
// │                                                       │
// │  Active triggers this month: 34                         │
// │  Conversion rate by trigger:                            │
// │                                                       │
// │  📸 Memory share:     18% ████████████████████         │
// │  ⭐ High NPS:         12% ████████████                 │
// │  🔄 Repeat booking:    8% ████████                     │
// │  💬 Positive message:  6% ██████                       │
// │  📅 Anniversary:       4% ████                         │
// │                                                       │
// │  Do NOT ask for referrals when:                        │
// │  ❌ Customer has unresolved issues                     │
// │  ❌ Trip had major disruptions                         │
// │  ❌ Customer rated below 7                             │
// │  ❌ Asked in the last 90 days                          │
// │                                                       │
// │  Frequency limit: Max 1 referral ask per 90 days        │
// │  Per-customer lifetime limit: No limit                  │
// │                                                       │
// │  [View Queue] [Edit Triggers] [Test Template]           │
// └─────────────────────────────────────────────────────┘
```

### Social Proof Automation

```typescript
interface SocialProofAutomation {
  // Auto-generate social proof content
  generators: {
    // Testimonial from review
    TESTIMONIAL_FROM_REVIEW: {
      trigger: "Customer leaves 4+ star review";
      auto_actions: [
        "Extract key positive phrases",
        "Generate testimonial card (image with quote + photo)",
        "Request customer consent for public use",
        "If consented: add to website testimonial rotation",
      ];
      output_format: "Image card (1080x1080) + text testimonial";
    };

    // Trip success story
    TRIP_STORY: {
      trigger: "Trip completes with health score 85+";
      auto_actions: [
        "Compile trip highlights from timeline",
        "Generate before/after story (inquiry → trip photos)",
        "Create social media post draft",
        "Request customer approval",
        "If approved: schedule for social media",
      ];
    };

    // Number-based social proof
    METRICS_PROOF: {
      trigger: "Monthly threshold reached";
      auto_generated: [
        "🎉 500th trip completed! Thank you for trusting us.",
        "🌟 95% customer satisfaction this month.",
        "✈️ 120 happy families traveled with us this quarter.",
      ];
      channel: "WhatsApp status, Instagram, website footer";
    };
  };
}

// ── Social proof automation ──
// ┌─────────────────────────────────────────────────────┐
// │  Social Proof Engine — Content Pipeline                  │
// │                                                       │
// │  Pending approval (3):                                │
// │  ┌───────────────────────────────────────────────┐   │
// │  │ Sharma Family — Singapore Trip                   │   │
// │  │ Review: ⭐⭐⭐⭐⭐ "Best family trip ever!"          │   │
// │  │ Testimonial card generated:                      │   │
// │  │ ┌─────────────────────────────────────────────┐│   │
// │  │ │  [Trip photo: Gardens by the Bay]             ││   │
// │  │ │  "Waypoint made our Singapore trip            ││   │
// │  │ │   absolutely stress-free. From visa           ││   │
// │  │ │   to daily briefings, everything was          ││   │
// │  │ │   taken care of."                              ││   │
// │  │ │  — Rajesh Sharma, Delhi                       ││   │
// │  │ │  [Waypoint Travel logo]                       ││   │
// │  │ └─────────────────────────────────────────────┘│   │
// │  │ Consent: ✅ Customer approved public use         │   │
// │  │ [Post to Social] [Add to Website] [Edit]        │   │
// │  └───────────────────────────────────────────────┘   │
// │                                                       │
// │  Auto-posted this month: 6 testimonials                 │
// │  Engagement: 2,400 views · 89 likes · 12 DMs           │
// │  DMs converted to inquiries: 3 (₹1.2L pipeline)        │
// │                                                       │
// │  [Generate More] [Approval Queue] [Analytics]           │
// └─────────────────────────────────────────────────────┘
```

### Referral Analytics Dashboard

```typescript
interface ReferralAnalytics {
  // Comprehensive referral program metrics
  metrics: {
    // Program health
    program_health: {
      active_referrers: number;
      avg_referrals_per_referrer: number;
      program_participation_rate: number; // % of customers who've referred
      revenue_from_referrals: number;
      revenue_share: number;              // % of total revenue from referrals
    };

    // Funnel metrics
    funnel: {
      referral_requests_sent: number;
      links_shared: number;
      links_clicked: number;
      inquiries_from_referrals: number;
      bookings_from_referrals: number;
      conversion_rate_share_to_booking: number;
    };

    // Unit economics
    unit_economics: {
      avg_reward_cost_per_referral: number;
      avg_customer_value_from_referral: number;
      referral_roas: number;              // return on ad spend equivalent
      payback_period_months: number;
      lifetime_value_referred_vs_organic: number; // referred customers worth more?
    };
  };
}

// ── Referral analytics ──
// ┌─────────────────────────────────────────────────────┐
// │  Referral Analytics — FY 2026-27                        │
// │                                                       │
// │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐               │
// │  │  48  │ │  3.2%│ │19.5x │ │+28%  │               │
// │  │Refer.│ │Rev   │ │ROI   │ │LTV   │               │
// │  │Active│ │Share │ │     │ │Lift │               │
// │  └──────┘ └──────┘ └──────┘ └──────┘               │
// │                                                       │
// │  Revenue: ₹18.2L from referrals (3.2% of total)        │
// │  Cost: ₹96K (rewards + program costs)                   │
// │  ROI: 19.5x (best performing channel)                   │
// │                                                       │
// │  Referred customer behavior:                           │
// │  • 28% higher LTV than organic customers               │
// │  • 15% higher conversion rate on first inquiry          │
// │  • 22% more likely to refer others (viral loop)         │
// │  • 12% lower acquisition cost                           │
// │                                                       │
// │  Channel comparison:                                   │
// │  Referral:    19.5x ROI · ₹130 CAC · 28% repeat       │
// │  WhatsApp:    8.2x ROI · ₹850 CAC · 18% repeat        │
// │  Google Ads:  3.4x ROI · ₹2,500 CAC · 8% repeat       │
// │  Instagram:   2.1x ROI · ₹4,200 CAC · 5% repeat       │
// │  Walk-in:     N/A · ₹0 CAC · 35% repeat                │
// │                                                       │
// │  [Export] [Optimize] [A/B Test Rewards]                 │
// └─────────────────────────────────────────────────────┘
```

### Viral Engine Optimization

```typescript
interface ViralOptimization {
  // A/B test and optimize viral mechanics
  experiments: {
    REWARD_AMOUNT: {
      variants: [
        { reward: "₹1,000", participation_rate: "4%" },
        { reward: "₹2,000", participation_rate: "8%" },
        { reward: "₹3,000", participation_rate: "9%" },
      ];
      winner: "₹2,000 (best cost-per-referral)";
    };

    REFERRAL_ASK_TIMING: {
      variants: [
        { timing: "Immediately after trip", conversion: "5%" },
        { timing: "3 days after trip", conversion: "8%" },
        { timing: "After memory book shared", conversion: "18%" },
        { timing: "On trip anniversary", conversion: "4%" },
      ];
      winner: "After memory book shared (18%)";
    };

    SHARE_FORMAT: {
      variants: [
        { format: "Text + referral link", click_rate: "12%" },
        { format: "Trip photo + referral link", click_rate: "25%" },
        { format: "Memory book preview + link", click_rate: "38%" },
        { format: "Highlight reel video + link", click_rate: "42%" },
      ];
      winner: "Highlight reel video (42% click rate)";
    };
  };
}

// ── Optimization experiments ──
// ┌─────────────────────────────────────────────────────┐
// │  Viral Engine — A/B Test Results                         │
// │                                                       │
// │  Experiment 1: Reward Amount                             │
// │  ✅ Winner: ₹2,000 (8% participation, ₹250/referral)     │
// │  vs ₹1,000 (4%, ₹200/referral)                          │
// │  vs ₹3,000 (9%, ₹333/referral — diminishing returns)    │
// │                                                       │
// │  Experiment 2: Share Format                              │
// │  ✅ Winner: Video highlight reel (42% click rate)         │
// │  vs Photo (25%) · Text only (12%) · Memory book (38%)    │
// │                                                       │
// │  Experiment 3: Ask Timing                                │
// │  ✅ Winner: After memory share (18% conversion)           │
// │  vs 3 days post (8%) · Immediately (5%) · Anniversary (4%)│
// │                                                       │
// │  Running experiment:                                     │
// │  🧪 Dual-sided vs Referrer-only reward                    │
// │  Currently: Dual-sided (₹2K each)                       │
// │  Testing: Referrer gets ₹3K, friend gets nothing          │
// │  Hypothesis: Friend discount drives more conversions     │
// │  Results: In progress (need 50 more data points)         │
// │                                                       │
// │  [New Experiment] [View Full Results] [Apply Winners]    │
// └─────────────────────────────────────────────────────┘
```

---

## Open Problems

1. **Attribution across channels** — A referral may start on WhatsApp but convert via walk-in. Cross-channel attribution requires customer self-reporting or code redemption at booking.

2. **Testimonial consent at scale** — Getting consent for every testimonial is legally required but operationally heavy. Need streamlined opt-in flow.

3. **Ambassador program sustainability** — Free trips and upgrades are expensive. Need clear caps and ROI tracking to prevent program from becoming a cost center.

4. **Viral coefficient ceiling** — Travel is infrequent (1-2 trips/year). K factor may never reach 1.0 without significant incentives. Focus on quality referrals over quantity.

---

## Next Steps

- [ ] Build smart referral request timing engine with signal-based triggers
- [ ] Create social proof automation pipeline with consent management
- [ ] Implement referral analytics dashboard with channel comparison
- [ ] Design A/B testing framework for viral optimization
