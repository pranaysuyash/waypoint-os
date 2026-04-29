# Referral & Viral Engine — Program Design & Mechanics

> Research document for referral program design, viral mechanics, ambassador programs, and word-of-mouth automation for travel agencies.

---

## Key Questions

1. **What referral program structure maximizes participation?**
2. **How do viral mechanics work for travel agencies?**
3. **What rewards motivate referrals without eroding margins?**
4. **How do we track and attribute referrals?**

---

## Research Areas

### Referral Program Architecture

```typescript
interface ReferralProgram {
  program_id: string;
  agency_id: string;

  // Program structure
  structure: {
    // Dual-sided reward (both parties benefit)
    referrer_reward: {
      type: "CREDIT" | "CASH" | "DISCOUNT" | "UPGRADE";
      value: number;                     // ₹2,000 travel credit
      conditions: {
        triggers_on: "REFERRAL_BOOKING_CONFIRMED";
        minimum_booking_value: number;    // ₹50,000
        valid_for_months: 12;
        stackable: false;                // can't combine with other credits
      };
    };

    referee_reward: {
      type: "DISCOUNT";
      value: number;                     // ₹2,000 off first booking
      conditions: {
        minimum_booking_value: number;
        new_customer_only: true;
        valid_for_months: 3;
      };
    };
  };

  // Referral code system
  referral_codes: {
    format: "WP-{agent_short}-{customer_hash}";
    examples: ["WP-PRI-SHARMA", "WP-RAH-GUPTA"];
    shareable_links: {
      whatsapp: string;                  // pre-filled WhatsApp message
      generic: string;                   // short URL with referral code
      social: string;                    // social media share link
    };
  };

  // Tiered rewards
  tiers: {
    BRONZE: { referrals: 1; reward: "₹2,000 credit" };
    SILVER: { referrals: 3; reward: "₹8,000 credit + airport lounge voucher" };
    GOLD: { referrals: 5; reward: "₹15,000 credit + free domestic weekend trip" };
    PLATINUM: { referrals: 10; reward: "₹30,000 credit + free international trip" };
  };
}

// ── Referral program dashboard ──
// ┌─────────────────────────────────────────────────────┐
// │  Referral Program — Waypoint Travel                      │
// │  Active referrers: 48 · Referrals this month: 12        │
// │  Revenue from referrals: ₹4.68L · Cost: ₹24K             │
// │                                                       │
// │  ┌─ Program Structure ─────────────────────────────┐  │
// │  │ Referrer gets: ₹2,000 travel credit              │  │
// │  │ Friend gets: ₹2,000 off first booking            │  │
// │  │ Minimum booking: ₹50,000                         │  │
// │  │ Validity: 12 months                              │  │
// │  │                                                 │  │
// │  │ Tiers:                                          │  │
// │  │ 🥉 1 referral: ₹2,000 credit                    │  │
// │  │ 🥈 3 referrals: ₹8,000 + lounge voucher          │  │
// │  │ 🥇 5 referrals: ₹15,000 + domestic trip          │  │
// │  │ 💎 10 referrals: ₹30,000 + international trip    │  │
// │  └─────────────────────────────────────────────────┘  │
// │                                                       │
// │  ROI: ₹4.68L revenue / ₹24K cost = 19.5x              │
// │  vs. paid ads: ₹50K spend / ₹1.2L revenue = 2.4x      │
// │                                                       │
// │  [Edit Program] [View Referrers] [Export Report]        │
// └─────────────────────────────────────────────────────┘
```

### Viral Mechanics for Travel

```typescript
interface ViralMechanics {
  // Built-in viral triggers
  triggers: {
    // Trip sharing (memory products)
    TRIP_MEMORY_SHARE: {
      trigger: "Customer shares memory book or highlight reel";
      viral_element: "Agency watermark + referral link on shared content";
      attribution: "UTM-tagged link in shared content";
      conversion_path: "Viewer sees memory → clicks link → lands on agency page → books";
    };

    // Group trip invitation
    GROUP_TRIP_INVITE: {
      trigger: "Customer plans group trip and invites friends";
      viral_element: "Each invitee gets agency introduction with referrer's endorsement";
      conversion_path: "Invitee joins trip → becomes customer → refers others";
    };

    // Review/recommendation
    POST_TRIP_REVIEW: {
      trigger: "Customer leaves positive review or rating";
      viral_element: "Public review with trip photos + referral code";
      conversion_path: "Reader sees review → clicks referral → books with discount";
    };

    // Social proof notification
    SOCIAL_PROOF: {
      trigger: "Customer completes trip";
      viral_element: "'Sharma family just returned from Singapore with Waypoint Travel!' (with consent)";
      channel: "WhatsApp status, Instagram story";
      conversion_path: "Network sees → asks about trip → referral link shared";
    };
  };
}

// ── Viral loop visualization ──
// ┌─────────────────────────────────────────────────────┐
// │  Viral Loop — Waypoint Travel                            │
// │                                                       │
// │  ┌─────────┐    books    ┌─────────┐                 │
// │  │ Customer │───────────→│   Trip   │                 │
// │  │  (A)     │            │ Complete │                 │
// │  └────┬────┘            └────┬─────┘                 │
// │       │                      │                        │
// │       │   memory products    │   reviews/recommend    │
// │       │   (share to network) │   (share to network)   │
// │       │                      │                        │
// │       ▼                      ▼                        │
// │  ┌─────────────────────────────────┐                  │
// │  │        Network sees content       │                  │
// │  │   (WhatsApp, Instagram, Facebook) │                  │
// │  └──────────────┬──────────────────┘                  │
// │                  │                                     │
// │     clicks referral link / asks about trip             │
// │                  │                                     │
// │                  ▼                                     │
// │  ┌─────────┐   converts   ┌─────────┐                 │
// │  │  New    │─────────────→│Customer │                 │
// │  │ Customer│   (B)        │  (B)    │                 │
// │  └─────────┘              └─────────┘                 │
// │       │                                               │
// │       └──────────→ Loop repeats ──→                   │
// │                                                       │
// │  Viral coefficient:                                   │
// │  Avg shares per customer: 2.3                         │
// │  Conversion per share: 8%                             │
// │  Viral coefficient (K): 0.18                          │
// │  (K < 1 = needs active promotion, not self-sustaining) │
// │                                                       │
// │  To reach K=1: need 5 shares per customer OR          │
// │  20% conversion per share (with referral incentives)  │
// └─────────────────────────────────────────────────────┘
```

### Ambassador Program

```typescript
interface AmbassadorProgram {
  // High-value customer ambassador track
  ambassadors: {
    // Qualification
    qualification: {
      min_trips: 3;
      min_spend: "₹5L";
      min_nps: 9;
      referral_count: 2;                 // must have referred at least 2
    };

    // Benefits
    benefits: {
      priority_booking: true;            // first access to new packages
      exclusive_deals: true;             // ambassador-only pricing
      free_upgrades: "1 per year";       // room/seat upgrade when available
      concierge_service: true;           // direct agent (no queue)
      annual_gift: true;                 // birthday/anniversary gift
      ambassador_badge: true;            // social media badge
    };

    // Responsibilities
    expectations: {
      min_referrals_per_year: 3;
      social_media_posts: "2 per trip (with consent)";
      review_per_trip: true;
      testimonial_availability: true;
    };
  };
}

// ── Ambassador program ──
// ┌─────────────────────────────────────────────────────┐
// │  Ambassador Program — Waypoint Travel                    │
// │  Active ambassadors: 8 · Referrals via ambassadors: 14   │
// │  Revenue: ₹5.6L · Ambassador cost: ₹45K                  │
// │                                                       │
// │  Top ambassadors:                                      │
// │  ┌───────────────────────────────────────────────┐   │
// │  │ 🥇 Rajesh Sharma · 5 referrals · 3 booked      │   │
// │  │    Status: GOLD · Next: PLATINUM (5 more)       │   │
// │  │    Last referral: Gupta family (Kerala trip)     │   │
// │  │    Lifetime value: ₹8.2L (own trips + referred) │   │
// │  │                                               │   │
// │  │ 🥈 Priya Gupta · 4 referrals · 2 booked        │   │
// │  │    Status: SILVER · Next: GOLD (1 more)          │   │
// │  │    Lifetime value: ₹5.1L                         │   │
// │  └───────────────────────────────────────────────┘   │
// │                                                       │
// │  Ambassador ROI: ₹5.6L revenue / ₹45K cost = 12.4x    │
// │                                                       │
// │  [Invite Ambassador] [View All] [Send Rewards]           │
// └─────────────────────────────────────────────────────┘
```

### Referral Attribution & Tracking

```typescript
interface ReferralAttribution {
  // Multi-touch referral tracking
  tracking: {
    referral_code: string;
    referrer_id: string;

    // Attribution chain
    attribution: {
      first_touch: {
        channel: "WHATSAPP_SHARE" | "SOCIAL_MEDIA" | "WORD_OF_MOUTH" | "WEBSITE" | "EVENT";
        timestamp: string;
        source_detail: string;            // "Rajesh Sharma's WhatsApp share"
      };
      last_touch: {
        channel: string;
        timestamp: string;
      };
      conversion_touch: {
        channel: string;
        timestamp: string;
        days_from_first_touch: number;
      };
    };

    // Reward status
    reward: {
      referrer_reward: "PENDING" | "EARNED" | "REDEEMED" | "EXPIRED";
      referee_reward: "PENDING" | "EARNED" | "REDEEMED" | "EXPIRED";
      reward_value: number;
    };
  };
}

// ── Referral tracking funnel ──
// ┌─────────────────────────────────────────────────────┐
// │  Referral Funnel — April 2026                           │
// │                                                       │
// │  Shares sent:          120                              │
// │  ████████████████████████████████████████              │
// │                                                       │
// │  Links clicked:        45 (37.5%)                       │
// │  █████████████████                                     │
// │                                                       │
// │  Inquiries received:   18 (15% of shares, 40% of clicks)│
// │  ████████                                              │
// │                                                       │
// │  Proposals sent:       12 (10% of shares)                │
// │  █████                                                 │
// │                                                       │
// │  Bookings closed:       4 (3.3% of shares)               │
// │  ██                                                    │
// │                                                       │
// │  Revenue: ₹4.68L · Cost: ₹24K · ROI: 19.5x            │
// │                                                       │
// │  Top referral sources:                                 │
// │  WhatsApp share:    65% of clicks                      │
// │  Instagram story:   20% of clicks                      │
// │  Word of mouth:     15% (tracked via code at booking)   │
// │                                                       │
// │  [View Details] [Export] [Optimize]                     │
// └─────────────────────────────────────────────────────┘
```

---

## Open Problems

1. **Word-of-mouth attribution** — Most referrals happen offline ("my friend told me"). Hard to track without a code. Need easy code redemption at booking.

2. **Reward gaming** — Customers creating fake referrals or self-referrals. Need fraud detection (different phone numbers, different addresses).

3. **Referral fatigue** — Asking too often annoys customers. Need smart timing (post-trip high NPS, not during issues).

4. **Margin impact** — ₹2,000 discount on both sides = ₹4,000 per referral. Need minimum booking value to ensure positive margin even after rewards.

---

## Next Steps

- [ ] Build referral program with dual-sided rewards and tier system
- [ ] Create viral mechanics integrated into memory products and reviews
- [ ] Implement ambassador program with qualification criteria
- [ ] Design multi-touch referral attribution system
