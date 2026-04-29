# Travel Voucher, Coupon & Promotions — Campaign Management

> Research document for promotional campaign management, seasonal campaigns, campaign lifecycle, and ROI analytics for Indian travel agencies.

---

## Key Questions

1. **How do we manage promotional campaigns across seasons and channels?**
2. **What campaign types drive the most conversions in Indian travel?**
3. **How do we prevent campaign fatigue while maximizing revenue?**
4. **What rules govern campaign eligibility, stacking, and usage limits?**

---

## Research Areas

### Campaign Management Architecture

```typescript
interface PromotionCampaign {
  id: string;
  agency_id: string;

  // Identity
  name: string;
  description: string;
  type: CampaignType;
  status: CampaignStatus;

  // Timing
  starts_at: string;
  ends_at: string;
  booking_window: DateRange | null;     // travel dates eligible

  // Rules
  eligibility: CampaignEligibility;
  usage_limits: CampaignUsageLimits;
  stacking_rules: StackingRules;

  // Offer
  offers: CampaignOffer[];

  // Budget
  budget: CampaignBudget | null;

  // Channels
  channels: EnquirySource[];
  target_segments: string[];

  // Analytics
  metrics: CampaignMetrics;

  created_at: string;
  updated_at: string;
}

type CampaignType =
  | "SEASONAL"        // Diwali, summer, winter
  | "FLASH"           // 24-72 hour sale
  | "LOYALTY"         // tier-based reward
  | "REFERRAL_BONUS"  // referrer + referee incentive
  | "WIN_BACK"        // dormant customer
  | "FIRST_BOOKING"   // new customer acquisition
  | "EARLY_BIRD"      // book early, save more
  | "LAST_MINUTE"     // unsold inventory
  | "FESTIVAL"        // Holi, Diwali, Christmas
  | "CORPORATE"       // B2B bulk deal
  | "DESTINATION"     // specific place promotion
  | "BUNDLE";         // multi-service package discount

type CampaignStatus =
  | "DRAFT" | "SCHEDULED" | "ACTIVE" | "PAUSED"
  | "EXPIRED" | "COMPLETED" | "CANCELLED";

// ── Campaign lifecycle ──
// ┌─────────────────────────────────────────┐
// │                                          │
// │  DRAFT ──→ SCHEDULED ──→ ACTIVE ──→ COMPLETED
// │                │           │              │
// │                │           ▼              │
// │                │         PAUSED ──→ ACTIVE│
// │                │           │              │
// │                ▼           ▼              │
// │            CANCELLED    CANCELLED         │
// │                │                          │
// │                ▼                          │
// │             EXPIRED ◄── (auto on end date)│
// │                                           │
// └───────────────────────────────────────────┘

interface CampaignEligibility {
  customer_segments: string[];          // empty = all
  min_booking_value: Money | null;
  max_booking_value: Money | null;
  destinations: string[];               // empty = all
  booking_types: BookingType[];         // empty = all
  channels: EnquirySource[];            // empty = all
  new_customers_only: boolean;
  existing_customers_only: boolean;
  min_previous_bookings: number;
  loyalty_tiers: string[];
}

interface CampaignUsageLimits {
  total_redemptions: number | null;     // null = unlimited
  per_customer: number;
  per_day: number | null;
  per_booking: number;
  budget_cap: Money | null;
}

interface StackingRules {
  stackable_with: string[];             // other campaign IDs
  max_stacked_offers: number;
  cannot_combine_with: string[];        // exclusion list
  priority_order: number;               // lower = higher priority
}

interface CampaignOffer {
  id: string;
  type: "PERCENTAGE_OFF" | "FLAT_OFF" | "FREE_UPGRADE" | "FREE_SERVICE"
    | "BOGO" | "EARLY_BIRD_TIERED" | "NIGHT_FREE";
  value: number;
  max_discount: Money | null;
  applies_to: "TOTAL" | "HOTEL" | "FLIGHT" | "ACTIVITY" | "TRANSPORT" | "SPECIFIC_VENDOR";
  vendor_ids: string[];
  description: string;
  display_text: string;                 // "Save ₹5,000 on Kerala trips!"
}

interface CampaignBudget {
  allocated: Money;
  spent: Money;
  remaining: Money;
  projected_spend: Money;
  roi_target: number;                   // e.g., 10x
}

interface CampaignMetrics {
  impressions: number;
  clicks: number;
  redemptions: number;
  revenue_generated: Money;
  discount_given: Money;
  net_revenue: Money;
  roi: number;
  conversion_rate: number;
  avg_order_value: Money;
  new_customers_acquired: number;
  repeat_customers_reactivated: number;
}
```

### Seasonal Campaign Calendar (India)

```typescript
// ── Indian Travel Campaign Calendar ──
// ┌─────────────────────────────────────────────────────┐
// │  Month    | Festival/Season    | Campaign Type       │
// │  ─────────────────────────────────────────────────── │
// │  January  | New Year           | LAST_MINUTE         │
// │           | Republic Day       | LONG_WEEKEND        │
// │  February | Valentine's Day    | HONEYMOON_DEAL      │
// │           |                    | EARLY_BIRD (summer)  │
// │  March    | Holi               | FESTIVAL_GETAWAY    │
// │           |                    | SUMMER_EARLY_BIRD    │
// │  April    | Summer Vacation    | EARLY_BIRD_PEAK     │
// │           |                    | FAMILY_PACKAGE      │
// │  May      | Peak Summer        | HILL_STATION        │
// │           |                    | INTERNATIONAL_SUMMER │
// │  June     | Monsoon            | OFF_SEASON_KERALA   │
// │           | Ladakh Opens       | ADVENTURE_SEASON    │
// │  July     | Monsoon Off-season | BUDGET_DEALS        │
// │           | Eid-ul-Adha        | FESTIVAL_GETAWAY    │
// │  August   | Independence Day   | LONG_WEEKEND        │
// │           | Onam               | KERALA_TOURISM      │
// │  September| Navratri           | GUJARAT_PACKAGES    │
// │           |                    | AUTUMN_INTERNATIONAL │
// │  October  | Diwali (BIGGEST)   | DIWALI_GETAWAY      │
// │           |                    | WINTER_HONEYMOON    │
// │  November | Wedding Season     | HONEYMOON_PEAK      │
// │           |                    | YEAR_END_INTERNATIONAL│
// │  December | Christmas/NY       | YEAR_END_DEALS      │
// │           | Winter Season      | RAJASTHAN_GOA       │
// └─────────────────────────────────────────────────────┘

interface SeasonalCampaignTemplate {
  name: string;
  period: { month: number; start_day: number; end_day: number };
  type: CampaignType;
  default_offer: CampaignOffer;
  target_segments: string[];
  recommended_budget: Money;
  historical_performance: {
    year: number;
    redemptions: number;
    revenue: Money;
    roi: number;
  }[];
}
```

### Campaign Analytics Dashboard

```typescript
// ┌─────────────────────────────────────────────────────┐
// │  Campaign Performance — October 2026                 │
// │                                                      │
// │  Active Campaigns: 8                                  │
// │  Total Budget: ₹15L    Spent: ₹8.2L (55%)           │
// │                                                      │
// │  ─── Campaign ──── ── Redemptions ── ── Revenue ──  │
// │  Diwali Getaway    120 (₹2.4L disc)   ₹42L (14x)   │
// │  Early Bird Winter  45 (₹0.9L disc)   ₹18L (18x)   │
// │  Honeymoon Nov      30 (₹0.6L disc)   ₹12L (17x)   │
// │  Win-back Q4        55 (₹1.5L disc)   ₹8L (5x)     │
// │  Referral Bonus     85 (₹1.7L disc)   ₹22L (12x)   │
// │  Last Min Goa       40 (₹0.8L disc)   ₹6L (7x)     │
// │  Corporate Bulk      8 (₹0.3L disc)   ₹15L (40x)   │
// │  Loyalty Gold+      25 (₹0.5L disc)   ₹9L (16x)    │
// │  ─────────────────────────────────────────────────   │
// │  TOTAL             408 (₹8.2L disc)   ₹132L (14x)  │
// │                                                      │
// │  Top performing: Corporate Bulk (40x ROI)            │
// │  Underperforming: Win-back Q4 (5x, below 10x target)│
// └──────────────────────────────────────────────────────┘

interface CampaignPerformanceReport {
  period: DateRange;
  campaigns: CampaignMetrics[];
  totals: {
    budget_allocated: Money;
    budget_spent: Money;
    total_redemptions: number;
    total_discount_given: Money;
    total_revenue: Money;
    net_revenue: Money;
    blended_roi: number;
    new_customers: number;
    repeat_customers: number;
  };
  insights: CampaignInsight[];
}

interface CampaignInsight {
  campaign_id: string;
  type: "OVERPERFORMING" | "UNDERPERFORMING" | "BUDGET_RISK" | "FATIGUE_RISK";
  message: string;
  recommendation: string;
}
```

---

## Open Problems

1. **Campaign fatigue detection** — Indian customers are sensitive to WhatsApp spam. Need intelligent frequency capping based on engagement signals (open rate drops, unsubscribes, complaint rate).

2. **Festival date variability** — Diwali, Holi, Eid shift dates annually based on lunar calendars. Campaign scheduling must auto-adapt to computed festival dates.

3. **Cross-campaign conflicts** — Multiple active campaigns targeting the same customer segment can create conflicting or overlapping offers. Need a conflict resolution engine.

4. **Flash sale infrastructure** — Flash campaigns (24-72 hours) can create traffic spikes. Need rate limiting and inventory reservation to prevent overselling.

---

## Next Steps

- [ ] Build campaign management CRUD with lifecycle state machine
- [ ] Create Indian festival calendar with auto-computed dates
- [ ] Implement campaign analytics dashboard with real-time metrics
- [ ] Design campaign fatigue detection algorithm
- [ ] Study campaign platforms (Braze, MoEngage, CleverTap, WebEngage)
