# Travel Voucher, Coupon & Promotions — Loyalty Rewards

> Research document for loyalty tier management, points accrual, redemption catalog, partner integration, and India-specific loyalty strategies.

---

## Key Questions

1. **How do we design tier-based rewards that incentivize repeat bookings?**
2. **What points accrual rules balance customer satisfaction with business costs?**
3. **How do we integrate with airline/hotel loyalty programs?**
4. **What India-specific loyalty strategies work best?**

---

## Research Areas

### Loyalty Tier System

```typescript
interface LoyaltyProgram {
  id: string;
  agency_id: string;

  tiers: LoyaltyTier[];
  points_config: PointsConfig;
  benefits: TierBenefit[];
  partner_integrations: PartnerIntegration[];
}

interface LoyaltyTier {
  level: number;
  name: "BRONZE" | "SILVER" | "GOLD" | "PLATINUM" | "DIAMOND";
  min_points: number;
  max_points: number;                  // null for highest tier

  // Qualification
  qualification_period: "YEAR" | "LIFETIME";
  qualification_criteria: {
    min_trips: number;
    min_spend: Money;
    min_points: number;
  };

  // Benefits
  benefits: TierBenefit[];
  upgrade_benefit: string | null;      // gift on tier upgrade
}

// ── Tier structure ──
// ┌─────────────────────────────────────────────────────┐
// │  Tier      | Points     | Trips | Benefits           │
// │  ──────────────────────────────────────────────────── │
// │  BRONZE    | 0-999      | 0     | Base earning       │
// │  SILVER    | 1,000-4,999| 2+    | +10% earn, priority │
// │  GOLD      | 5,000-14,999| 4+   | +25% earn, upgrades │
// │  PLATINUM  | 15,000-49,999| 8+  | +50% earn, lounge  │
// │  DIAMOND   | 50,000+    | 15+   | +100% earn, VIP     │
// │                                                       │
// │  India-specific:                                      │
// │  - Family pooling (up to 5 members)                  │
// │  - Festival bonus points (2x during Diwali/summer)   │
// │  - Group earning (group trip = all members earn)     │
// │  - WhatsApp-based points check                       │
// └─────────────────────────────────────────────────────┘

interface TierBenefit {
  tier: string;
  category: "EARNING" | "REDEMPTION" | "SERVICE" | "EXCLUSIVE";
  name: string;
  description: string;
  value: string;
}

// Example benefits by tier:
// BRONZE:  1x earning, birthday ₹500 credit
// SILVER:  1.1x earning, priority queue, free cancellation once/year
// GOLD:    1.25x earning, room upgrades, lounge access, dedicated agent
// PLATINUM: 1.5x earning, guaranteed upgrades, airport meet & greet
// DIAMOND: 2x earning, free weekend trip/year, personal concierge
```

### Points Accrual Engine

```typescript
interface PointsConfig {
  base_rate: number;                   // points per ₹100 spent
  earning_multipliers: EarningMultiplier[];
  bonus_events: BonusEvent[];
  expiry_rules: PointsExpiryRules;
}

interface EarningMultiplier {
  factor: string;
  multiplier: number;
  description: string;
}

// ── Earning multipliers ──
// ┌─────────────────────────────────────────┐
// │  Factor              | Multiplier        │
// │  ─────────────────────────────────────── │
// │  Base earn           | 1x (1 pt/₹100)   │
// │  Silver tier         | 1.1x             │
// │  Gold tier           | 1.25x            │
// │  Platinum tier       | 1.5x             │
// │  Diamond tier        | 2x              │
// │  Festival booking    | 1.5x             │
// │  Early bird          | 1.2x             │
// │  App/portal booking  | 1.1x             │
// │  Referral booking    | 2x              │
// │  Review submitted    | +50 pts flat     │
// │  Social media share  | +25 pts flat     │
// └──────────────────────────────────────────┘

interface BonusEvent {
  name: string;
  trigger: string;
  bonus_points: number;
  recurring: boolean;
  max_per_year: number | null;
}

interface PointsExpiryRules {
  type: "ROLLING_12_MONTHS" | "FIXED_YEAR" | "NEVER";
  grace_period_days: number;
  notification_before_expiry_days: number[];
}

// ── Points transaction ──
interface PointsTransaction {
  id: string;
  customer_id: string;
  type: "EARN" | "REDEEM" | "EXPIRE" | "ADJUST" | "TRANSFER";
  points: number;
  balance_after: number;

  // Source
  source_type: "BOOKING" | "REFERRAL" | "REVIEW" | "BONUS" | "TRANSFER" | "EXPIRY";
  source_ref: string;
  description: string;

  // Earning detail
  booking_id: string | null;
  booking_value: Money | null;
  base_points: number | null;
  multiplier_applied: number | null;
  bonus_points: number | null;

  created_at: string;
}
```

### Redemption Catalog

```typescript
interface RedemptionCatalog {
  items: RedemptionItem[];
  categories: RedemptionCategory[];
}

interface RedemptionItem {
  id: string;
  name: string;
  description: string;
  category: RedemptionCategory;
  points_cost: number;
  cash_value: Money;                   // equivalent INR value
  availability: "IN_STOCK" | "LIMITED" | "UNAVAILABLE";
  stock_count: number | null;

  // Applicability
  applicable_to: {
    booking_types: BookingType[];
    destinations: string[];
    vendors: string[];
  };

  // Restrictions
  min_tier: string | null;
  max_per_year: number | null;
  booking_required: boolean;
}

type RedemptionCategory =
  | "FLIGHT_DISCOUNT"     // points for flight discount
  | "HOTEL_DISCOUNT"      // points for hotel discount
  | "FREE_NIGHT"          // one free hotel night
  | "UPGRADE"             // room/seat upgrade
  | "ACTIVITY"            // free activity/experience
  | "AIRPORT_SERVICES"    // lounge, fast track
  | "TRAVEL_CREDIT"       // generic credit
  | "MERCHANDISE"         // travel accessories
  | "CHARITY"             // donate points
  | "PARTNER_TRANSFER";   // transfer to airline/hotel program

// ── Redemption value proposition ──
// ┌─────────────────────────────────────────┐
// │  Points Value Table                       │
// │                                           │
// │  1,000 pts = ₹100 (base value)           │
// │                                           │
// │  Best value redemptions:                  │
// │  - Airport lounge: 2,000 pts (₹400 value)│
// │  - Room upgrade: 5,000 pts (₹1,500 value)│
// │  - Free night: 15,000 pts (₹5,000 value) │
// │                                           │
// │  Partners give better value:              │
// │  - Transfer to airline: 1.5x value       │
// │  - Hotel loyalty: 1.3x value             │
// └───────────────────────────────────────────┘
```

### Partner Loyalty Integration

```typescript
interface PartnerIntegration {
  partner_type: "AIRLINE" | "HOTEL" | "CAR_RENTAL" | "CREDIT_CARD";
  partner_name: string;
  program_name: string;

  // Cross-earning
  earn_rate: {
    our_points_per_partner_point: number;
    partner_points_per_our_point: number;
  };

  // Transfer
  transfer_enabled: boolean;
  transfer_ratio: number;
  min_transfer: number;
  transfer_fee: Money | null;

  // Status match
  status_match_enabled: boolean;
  tier_mapping: {
    our_tier: string;
    partner_tier: string;
  }[];
}

// ── Partner ecosystem ──
// ┌─────────────────────────────────────────┐
// │  Indian Airline Partners:                 │
// │  - IndiGo (6E Rewards)                   │
// │  - Air India (Flying Returns)            │
// │  - Vistara (Club Vistara)                │
// │  - SpiceJet (SpiceClub)                  │
// │                                           │
// │  Hotel Partners:                          │
// │  - Taj InnerCircle                       │
// │  - Marriott Bonvoy                       │
// │  - IHG Rewards                           │
// │  - Accor Live Limitless                  │
// │                                           │
// │  Credit Card Partners:                    │
// │  - HDFC Diners/Infinia                   │
// │  - Amex Platinum Travel                  │
// │  - SBI Cards                             │
// │  - Axis Magnus                           │
// │                                           │
// │  Cross-earn example:                     │
// │  Book flight via us → earn our points    │
// │                  + airline miles         │
// │                  + credit card points    │
// │  (Triple dip)                            │
// └───────────────────────────────────────────┘
```

---

## Open Problems

1. **Points liability** — Outstanding points are a financial liability on the balance sheet. Need to estimate and provision for redemption rates.

2. **Family pooling complexity** — Indian families want to pool points, but ownership, transfer rules, and tax implications are complex. 5 members each earning differently but spending from one pool.

3. **Tier demotion sensitivity** — Downgrading a customer's tier (e.g., Gold → Silver) causes significant dissatisfaction. Need grace periods, soft landings, and clear communication.

4. **Partner program changes** — Airline/hotel programs frequently devalue points and change earning rates. Our loyalty program must absorb partner changes without impacting customer trust.

---

## Next Steps

- [ ] Build loyalty tier engine with automatic qualification/demotion
- [ ] Implement points accrual pipeline with multiplier stacking
- [ ] Create redemption catalog with inventory management
- [ ] Design partner integration layer for cross-earning
- [ ] Study Indian travel loyalty patterns (MakeMyTrip Black, Cleartrip, Goibibo)
