# Travel Voucher, Coupon & Promotions — Coupon Management

> Research document for coupon code generation, redemption tracking, anti-fraud measures, and stacking rules for travel agencies.

---

## Key Questions

1. **How do we generate and manage coupon codes at scale?**
2. **What redemption limits and tracking prevent abuse?**
3. **How do we handle coupon stacking and conflict resolution?**
4. **What anti-fraud measures are essential for Indian travel?**

---

## Research Areas

### Coupon Code Management

```typescript
interface Coupon {
  id: string;
  agency_id: string;
  campaign_id: string | null;

  // Identity
  code: string;                        // "DIWALI2026" or auto-generated
  display_name: string;
  description: string;

  // Type & Value
  type: CouponType;
  value: number;
  max_discount: Money | null;
  min_booking_value: Money | null;

  // Validity
  valid_from: string;
  valid_until: string;
  is_active: boolean;

  // Limits
  usage_limits: CouponUsageLimits;

  // Restrictions
  applicable_to: CouponApplicability;

  // Tracking
  times_used: number;
  times_used_by_customer: Record<string, number>;

  created_at: string;
}

type CouponType =
  | "PERCENTAGE"        // 10% off
  | "FLAT"              // ₹2,000 off
  | "FREE_SERVICE"      // free airport transfer
  | "UPGRADE"           // room category upgrade
  | "NIGHT_FREE"        // stay 4, pay 3
  | "BOGO"              // buy one get one
  | "CREDIT"            // ₹1,000 travel credit
  | "WAIVED_FEE";       // no cancellation fee

interface CouponUsageLimits {
  total_uses: number | null;           // null = unlimited
  per_customer: number;
  per_day: number | null;
  per_booking: number;
  first_time_customer_only: boolean;
}

interface CouponApplicability {
  booking_types: BookingType[];        // empty = all
  vendors: string[];                   // empty = all
  destinations: string[];              // empty = all
  hotels: string[];                    // specific property IDs
  airlines: string[];
  routes: string[];                    // "DEL-SIN"
  travel_date_range: DateRange | null;
  booking_date_range: DateRange | null;
  channels: EnquirySource[];
  customer_segments: string[];
}

// ── Code generation strategies ──
// ┌─────────────────────────────────────────┐
// │  Code Generation Patterns                 │
// │                                            │
// │  Human-readable:  DIWALI2026, SUMMER50    │
// │  Semi-random:     SAVE-4X8K, TRIP-A7B2   │
// │  Fully random:    X8K2M9P4               │
// │  Referral:        TRAVEL-PRANAY           │
// │  Bulk series:     DIWALI-001..DIWALI-500  │
// │                                            │
// │  Rules:                                    │
// │  - 6-12 characters                        │
// │  - Avoid confusing: 0/O, 1/I/L           │
// │  - Uppercase + digits only                │
// │  - Prefix by campaign for analytics       │
// └───────────────────────────────────────────┘

interface CodeGenerationStrategy {
  type: "STATIC" | "UNIQUE" | "BULK" | "REFERRAL";
  prefix: string;                      // "DIWALI"
  length: number;                      // total code length
  character_set: "ALPHA_NUMERIC" | "ALPHA" | "NUMERIC";
  pattern: string | null;              // "XXXX-XXXX" for formatting
  count: number | null;                // for bulk generation
  collision_retries: number;
}
```

### Redemption Tracking & Validation

```typescript
interface CouponRedemption {
  id: string;
  coupon_id: string;
  booking_id: string;
  customer_id: string;

  code_applied: string;
  discount_type: CouponType;
  discount_value: number;
  discount_amount: Money;              // actual discount given
  booking_total_before: Money;
  booking_total_after: Money;

  redeemed_at: string;
  redeemed_by: string;                 // agent or customer
  channel: "AGENT_PORTAL" | "CUSTOMER_PORTAL" | "WHATSAPP" | "API";

  // Validation result at time of redemption
  validation: CouponValidationResult;

  status: "APPLIED" | "REVERSED" | "EXPIRED" | "CANCELLED";
  reversed_at: string | null;
  reversal_reason: string | null;
}

interface CouponValidationResult {
  valid: boolean;
  coupon_id: string | null;
  errors: CouponValidationError[];
  warnings: CouponValidationWarning[];
  applied_discount: Money | null;
}

interface CouponValidationError {
  code: "EXPIRED" | "NOT_STARTED" | "USAGE_EXCEEDED" | "CUSTOMER_LIMIT"
    | "MIN_BOOKING_NOT_MET" | "NOT_APPLICABLE" | "INACTIVE";
  message: string;
}

interface CouponValidationWarning {
  code: "STACKING_LIMIT" | "BETTER_COUPON_EXISTS" | "SIMILAR_CAMPAIGN_ACTIVE";
  message: string;
}

// ── Validation flow ──
// ┌─────────────────────────────────────────┐
// │  Validate Coupon                          │
// │       │                                    │
// │       ├── Coupon exists?                   │
// │       ├── Coupon active?                   │
// │       ├── Within valid dates?              │
// │       ├── Usage limits OK?                 │
// │       │    ├── Total uses < max?           │
// │       │    ├── Customer uses < max?        │
// │       │    └── Daily uses < max?           │
// │       ├── Min booking value met?           │
// │       ├── Applicable to booking type?      │
// │       ├── Applicable to destination?       │
// │       ├── Applicable to vendor?            │
// │       ├── Applicable to travel dates?      │
// │       ├── Customer segment eligible?       │
// │       ├── First-time check (if required)?  │
// │       └── Stacking rules satisfied?        │
// │              │                             │
// │              ▼                             │
// │       ┌──────────────┐                    │
// │       │ Calculate     │                    │
// │       │ discount      │                    │
// │       └──────────────┘                    │
// │              │                             │
// │              ▼                             │
// │       ┌──────────────┐                    │
// │       │ Check vs      │                    │
// │       │ max_discount  │                    │
// │       └──────────────┘                    │
// │              │                             │
// │              ▼                             │
// │       Return validation result             │
// └───────────────────────────────────────────┘
```

### Anti-Fraud Measures

```typescript
interface FraudDetectionRule {
  id: string;
  name: string;
  type: FraudRuleType;
  severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  action: "FLAG" | "BLOCK" | "REQUIRE_VERIFICATION" | "NOTIFY";
  enabled: boolean;
}

type FraudRuleType =
  | "SAME_PAYMENT_METHOD"     // same card for multiple accounts
  | "SAME_DEVICE"             // same device fingerprint
  | "SAME_IP_ADDRESS"         // multiple accounts from same IP
  | "RAPID_REDEMPTION"        // too many redemptions in short time
  | "SELF_REFERRAL"           // referring own alternate account
  | "DISCOUNT_STACKING_ABUSE" // gaming stacking rules
  | "MINIMUM_VALUE_GAMING"    // adding items to hit minimum, then removing
  | "PHANTOM_BOOKING"         // book to get discount, then cancel
  | "ACCOUNT_FARMING";        // creating multiple accounts for coupons

interface FraudCheck {
  coupon_id: string;
  customer_id: string;
  booking_id: string;
  checks: {
    rule: FraudRuleType;
    passed: boolean;
    score: number;                      // 0-1, higher = more suspicious
    details: string;
  }[];
  overall_risk_score: number;           // 0-1
  recommendation: "ALLOW" | "FLAG" | "BLOCK" | "MANUAL_REVIEW";
}

// ── Fraud detection flow ──
// ┌─────────────────────────────────────────┐
// │  Redemption Request                       │
// │       │                                    │
// │       ▼                                    │
// │  ┌──────────────────────────┐            │
// │  │ Check customer history   │            │
// │  │ - Previous redemptions   │            │
// │  │ - Account age            │            │
// │  │ - Device fingerprint     │            │
// │  │ - IP address             │            │
// │  │ - Payment methods used   │            │
// │  └──────────────────────────┘            │
// │       │                                    │
// │       ▼                                    │
// │  ┌──────────────────────────┐            │
// │  │ Run fraud rules engine   │            │
// │  │ - Score each rule        │            │
// │  │ - Weight by severity     │            │
// │  │ - Calculate composite    │            │
// │  └──────────────────────────┘            │
// │       │                                    │
// │       ├── Low risk (< 0.3): ALLOW         │
// │       ├── Medium risk (0.3-0.6): FLAG     │
// │       ├── High risk (0.6-0.8): REVIEW     │
// │       └── Critical (> 0.8): BLOCK         │
// └───────────────────────────────────────────┘
```

---

## Open Problems

1. **Code leakage** — Coupon codes shared on deal forums (e.g., DesiDime, CouponDunia) can be redeemed by non-target customers. Need single-use or customer-locked codes for high-value offers.

2. **Cancellation fraud** — Customer applies coupon, books trip, then cancels after using associated benefits (e.g., free lounge access, airport transfer). Need benefit clawback on cancellation.

3. **Agent coupon abuse** — Agents may apply coupons to their own bookings or to non-qualifying customers. Need agent-level redemption limits and audit trails.

4. **Cross-currency coupons** — A ₹5,000 flat coupon needs different values when applied to international bookings priced in USD/EUR. Need currency conversion at redemption time.

---

## Next Steps

- [ ] Build coupon code generator with collision detection
- [ ] Implement multi-layer validation engine (eligibility → limits → stacking → fraud)
- [ ] Create redemption tracking with audit trail
- [ ] Design fraud detection rules engine with configurable thresholds
- [ ] Study coupon fraud patterns in Indian e-commerce (Flipkart, Myntra case studies)
