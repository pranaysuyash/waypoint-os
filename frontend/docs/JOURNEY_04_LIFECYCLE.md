# Customer Journey Orchestration — Lifecycle Marketing & Re-engagement

> Research document for lifecycle marketing automation, seasonal campaigns, re-engagement strategies, and long-term customer relationship management.

---

## Key Questions

1. **How do we automate lifecycle marketing across the customer journey?**
2. **What seasonal and event-based campaigns drive engagement?**
3. **How do we re-engage dormant customers effectively?**
4. **What referral and advocacy programs turn customers into promoters?**
5. **How do we measure lifecycle marketing ROI?**

---

## Research Areas

### Lifecycle Marketing Automation

```typescript
interface LifecycleMarketing {
  campaigns: LifecycleCampaign[];
  triggers: CampaignTrigger[];
  templates: CampaignTemplate[];
  calendar: MarketingCalendar;
}

// Lifecycle campaign types:
// ─────────────────────────────────────────
// TYPE              | TRIGGER                    | GOAL
// ──────────────────────────────────────────────────────────
// Welcome           | New inquiry                | Convert to consideration
// Abandoned quote   | Quote viewed, no response  | Recover lost interest
// Booking celebration | Trip confirmed           | Build excitement
// Pre-trip prep     | X days before travel       | Reduce anxiety
// Birthday offer    | Customer birthday          | Personal touch
// Anniversary trip  | Wedding anniversary        | Romantic travel
// Festival campaign | Diwali, summer, etc.       | Seasonal bookings
// Win-back          | 90+ days dormant           | Reactivate
// Referral ask      | Post-trip, high NPS        | Word of mouth
// Loyalty reward    | Tier milestone             | Retain VIPs
// Re-engage         | 30-90 days inactive        | Prevent dormancy
// ─────────────────────────────────────────

// Campaign orchestration flow:
// ┌──────────────────────────────────────────────────────────────────────┐
// │                                                                      │
// │  [Customer Event]                                                   │
// │       │                                                              │
// │       ▼                                                              │
// │  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐          │
// │  │ Check        │──→ │ Select       │──→ │ Personalize  │          │
// │  │ eligibility  │    │ campaign     │    │ content      │          │
// │  └──────────────┘    └──────────────┘    └──────────────┘          │
// │                                                 │                    │
// │       ┌─────────────────────────────────────────┤                    │
// │       │                                         │                    │
// │       ▼                                         ▼                    │
// │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐           │
// │  │WhatsApp  │  │ Email    │  │ SMS      │  │ Push     │           │
// │  │ (primary)│  │ (docs)   │  │ (alert)  │  │ (in-app) │           │
// │  └──────────┘  └──────────┘  └──────────┘  └──────────┘           │
// │       │                                                              │
// │       ▼                                                              │
// │  ┌──────────────┐    ┌──────────────┐                              │
// │  │ Track        │──→ │ If no response│                              │
// │  │ engagement   │    │ → follow-up   │                              │
// │  └──────────────┘    └──────────────┘                              │
// │                                                                      │
// └──────────────────────────────────────────────────────────────────────┘

// Campaign examples:
//
// CAMPAIGN: "Abandoned Quote Recovery"
// Trigger: Quote sent + 48 hours + no customer response
// Steps:
//   1. Day 2: WhatsApp — "Hi! Did you get a chance to review the Kerala quote?"
//   2. Day 4: WhatsApp — "I can adjust the itinerary if budget is a concern"
//   3. Day 7: WhatsApp — "Here's a similar Goa option at a lower price point"
//   4. Day 14: Mark as lost → Add to re-engagement queue
//
// CAMPAIGN: "Birthday Travel Offer"
// Trigger: Customer birthday - 14 days
// Steps:
//   1. Day -14: WhatsApp — "Happy birthday month! 🎁 ₹3000 off your next trip"
//   2. Day -7: WhatsApp — "Still thinking about that Kerala trip? Birthday discount applies!"
//   3. Day 0: WhatsApp — "Happy Birthday! Your travel gift is waiting"
//   4. Day +7: Offer expires if not used
//
// CAMPAIGN: "Post-Trip Re-Engagement"
// Trigger: Trip completed + 14 days
// Steps:
//   1. Day 14: WhatsApp — "Missing Kerala? Plan your next adventure"
//   2. Day 30: Email — Destination guide for similar trip type
//   3. Day 60: WhatsApp — Festival-based suggestion ("Diwali getaway ideas")
//   4. Day 90: Mark dormant if no engagement

// Seasonal marketing calendar for India:
// ┌─────────────────────────────────────────┐
// │  2026 Marketing Calendar                  │
// │                                            │
// │  JAN  • New Year trips (last-minute)      │
// │       • Republic Day long weekend         │
// │  FEB  • Valentine's Day honeymoon push    │
// │       • Spring break planning             │
// │  MAR  • Holi getaway packages             │
// │       • Summer vacation early bird        │
// │  APR  • Summer vacation booking peak      │
// │       • School holiday planning           │
// │  MAY  • Hill station season starts        │
// │       • International summer deals        │
// │  JUN  • Monsoon Kerala packages           │
// │       • Ladakh season begins              │
// │  JUL  • Monsoon off-season deals          │
// │       • Eid-ul-Adha (Bakrid) travel       │
// │  AUG  • Independence Day weekend          │
// │       • Onam (Kerala tourism)             │
// │  SEP  • Navratri packages (Gujarat)       │
// │       • Autumn international deals        │
// │  OCT  • Diwali getaway push (biggest)     │
// │       • Winter honeymoon planning         │
// │  NOV  • Wedding season honeymoon peak     │
// │       • Year-end international deals      │
// │  DEC  • Christmas/New Year trips          │
// │       • Winter Rajasthan/Goa season       │
// └─────────────────────────────────────────────┘
```

### Re-engagement & Win-back

```typescript
interface ReEngagementSystem {
  dormancyDetection: DormancyDetector;
  winBackCampaigns: WinBackCampaign[];
  referralProgram: ReferralProgram;
  advocacy: AdvocacyProgram;
}

// Dormancy detection:
// ─────────────────────────────────────────
// Level          | Days Inactive | Risk    | Action
// ──────────────────────────────────────────────────────────
// Active         | 0-30          | None    | Normal engagement
// Cooling        | 31-60         | Low     | Soft re-engage
// At Risk        | 61-90         | Medium  | Targeted campaign
// Dormant        | 91-180        | High    | Win-back campaign
// Cold           | 181-365       | V.High  | Aggressive win-back
// Lost           | 365+          | Critical| Last attempt + archive
// ─────────────────────────────────────────

// Win-back campaigns by dormancy level:
//
// COOLING (31-60 days):
// "Hey [name], it's been a while!
//  Here are some trending destinations for [season]."
// → Soft, helpful, no pressure
//
// AT RISK (61-90 days):
// "We miss you! Here's ₹2000 off your next trip.
//  Valid for 2 weeks. Where would you like to go?"
// → Incentive-based, time-limited
//
// DORMANT (91-180 days):
// "[Name], your exclusive offer expires in 48 hours!
//  ₹5000 off + free airport transfer on any trip.
//  This is our best offer this quarter."
// → High urgency, best incentive
//
// COLD (181-365 days):
// "We've updated our destination list!
//  New: Vietnam, Azerbaijan, Sri Lanka budget trips.
//  Reply to see what's new."
// → Information-based, new offerings
//
// LOST (365+ days):
// "Last chance: ₹5000 credit in your account expiring [date].
//  Use it or lose it. Any trip, any destination."
// → Final attempt, scarcity trigger

// Referral program:
// ┌─────────────────────────────────────────┐
// │  Referral Program                         │
// │                                            │
// │  How it works:                             │
// │  1. You share your referral link/code      │
// │  2. Friend books a trip (min ₹25K)         │
// │  3. Friend gets ₹2000 off                  │
// │  4. You get ₹2000 credit                   │
// │                                            │
// │  Your referral code: TRAVEL-[NAME]         │
// │                                            │
// │  Share via:                                │
// │  [WhatsApp] [Copy Link] [Email]           │
// │                                            │
// │  Your referrals:                           │
// │  • Sent: 8 invites                        │
// │  • Booked: 2 (₹4000 earned)              │
// │  • Credits available: ₹4000               │
// │                                            │
// │  Leaderboard (optional):                   │
// │  Top referrer this month: Rahul (5 trips)  │
// └─────────────────────────────────────────────┘
//
// Referral mechanics:
// - One-tap share via WhatsApp (pre-filled message)
// - Track: Sent → Opened → Inquired → Booked
// - Dual incentive: Both referrer and referee benefit
// - Credits: Applied to next booking automatically
// - Fraud prevention: Self-referral blocked, min trip value
// - Tiered bonus: 5+ referrals → ₹3000 per referral

// Advocacy program:
// - Google review request → ₹500 credit
// - Social media post with tagging → ₹500 credit
// - Video testimonial → ₹2000 credit
// - Blog post about trip → ₹3000 credit
// - Annual ambassador (10+ referrals) → Free weekend trip
```

### Lifecycle Analytics

```typescript
interface LifecycleAnalytics {
  cohortAnalysis: CohortAnalysis;
  campaignROI: CampaignROI;
  retentionCurve: RetentionCurve;
  lifetimeValue: LifetimeValueAnalysis;
}

// Cohort analysis:
// ┌─────────────────────────────────────────┐
// │  Customer Cohort Retention                │
// │  (% who made 2nd trip within 12 months)   │
// │                                            │
// │  Q1 2024: 35% ██████████████████░░░░      │
// │  Q2 2024: 38% ███████████████████░░░      │
// │  Q3 2024: 42% ██████████████████████░     │
// │  Q4 2024: 45% ████████████████████████    │
// │  Q1 2025: 48% ██████████████████████████  │
// │  Q2 2025: 52% ████████████████████████████│
// │                                            │
// │  Trend: ↑ Improving (lifecycle marketing) │
// │  Industry avg: 30-35%                     │
// │  Our target: 55% by Q4 2026              │
// └─────────────────────────────────────────────┘
//
// Retention curve:
// Month:  1    2    3    6    9    12   18   24
// Active: 95%  85%  72%  55%  45%  38%  28%  22%
// With lifecycle marketing:
// Active: 95%  90%  82%  68%  60%  52%  42%  35%
// Improvement: +5% +5% +10% +13% +15% +14% +14% +13%
//
// Campaign ROI:
// ┌─────────────────────────────────────────┐
// │  Campaign ROI — April 2026               │
// │                                            │
// │  Campaign          | Sent | Revenue | ROI  │
// │  ─────────────────────────────────────── │
// │  Festival (Diwali) | 450  | ₹28L   | 12x  │
// │  Birthday offers   | 85   | ₹8.5L  | 18x  │
// │  Win-back          | 120  | ₹5.2L  | 8x   │
// │  Referral program  | N/A  | ₹12L   | 25x  │
// │  Post-trip re-engage| 210 | ₹15L   | 15x  │
// │  ─────────────────────────────────────── │
// │  Total             |      | ₹68.7L | 14x  │
// │                                            │
// │  Cost per acquisition:                     │
// │  Lifecycle campaigns: ₹1,200/customer     │
// │  Paid ads (Google/Meta): ₹3,500/customer  │
// │  Referral: ₹800/customer                  │
// │  Overall: ₹2,100/customer                 │
// └─────────────────────────────────────────────┘
```

---

## Open Problems

1. **Campaign fatigue** — Even well-timed campaigns become annoying if overused. Indian customers are especially sensitive to WhatsApp spam. Frequency capping must be intelligent, not just rule-based.

2. **Festival timing variability** — Indian festivals follow lunar calendars and shift dates annually. Holi, Diwali, and Eid don't fall on the same date each year. Campaign timing must adapt dynamically.

3. **Referral fraud** — Self-referrals, fake accounts, and gaming the referral system are common. Robust fraud detection (same phone number, same address, same payment method) is needed.

4. **Win-back cost efficiency** — Aggressive discounts to win back dormant customers may attract deal-seekers who churn again after the discount. Quality of re-acquired customers matters, not just quantity.

5. **Cross-journey conflicts** — A customer in the "post-trip" stage for one trip may be in "consideration" for another. Lifecycle campaigns must handle overlapping journeys without conflicting messages.

---

## Next Steps

- [ ] Build lifecycle campaign engine with stage-based triggers and multi-step sequences
- [ ] Create seasonal marketing calendar with Indian festival and holiday integration
- [ ] Implement dormancy detection and tiered win-back campaigns
- [ ] Design referral program with fraud prevention and dual-incentive structure
- [ ] Study lifecycle marketing (Braze, Iterable, MoEngage, CleverTap, WebEngage)
