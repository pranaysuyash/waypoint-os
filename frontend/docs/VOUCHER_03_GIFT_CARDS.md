# Travel Voucher, Coupon & Promotions — Gift Cards & Travel Credits

> Research document for gift card lifecycle, travel credit management, multi-currency support, and corporate bulk purchasing for travel agencies.

---

## Key Questions

1. **How do we manage gift card purchase, activation, and redemption?**
2. **What types of travel credits exist and how do they interact?**
3. **How do gift cards work across currencies for international travel?**
4. **What corporate gift card programs drive B2B revenue?**

---

## Research Areas

### Gift Card System

```typescript
interface GiftCard {
  id: string;
  agency_id: string;

  // Identity
  code: string;                        // activation code
  pin: string;                         // 4-digit security
  type: GiftCardType;

  // Value
  face_value: Money;                   // purchased amount
  balance: Money;                      // remaining balance
  currency: string;

  // Lifecycle
  status: GiftCardStatus;
  purchased_at: string | null;
  activated_at: string | null;
  first_used_at: string | null;
  expires_at: string | null;

  // Ownership
  purchaser_id: string | null;         // who bought it
  recipient_id: string | null;         // who received it
  recipient_email: string | null;
  recipient_phone: string | null;

  // Design
  template_id: string | null;          // visual design
  message: string | null;              // personal message
  delivery_method: "EMAIL" | "WHATSAPP" | "PHYSICAL" | "LINK";
  delivery_status: "PENDING" | "SENT" | "DELIVERED" | "FAILED";

  // Redemption
  redemptions: GiftCardRedemption[];
  total_redeemed: Money;

  created_at: string;
}

type GiftCardType =
  | "DIGITAL"          // email/WhatsApp delivery
  | "PHYSICAL"         // printed card
  | "E_LINK";          // shareable URL

type GiftCardStatus =
  | "CREATED"          // generated but not purchased
  | "PURCHASED"        // paid for, awaiting activation
  | "ACTIVE"           // ready to use
  | "PARTIALLY_USED"   // some balance remaining
  | "FULLY_USED"       // zero balance
  | "EXPIRED"          // past expiry date
  | "CANCELLED"        // refunded/voided
  | "FROZEN";          // fraud hold

// ── Gift Card Lifecycle ──
// ┌─────────────────────────────────────────┐
// │                                          │
// │  CREATED ──→ PURCHASED ──→ ACTIVE        │
// │                                │         │
// │                    ┌───────────┤         │
// │                    │           │         │
// │                    ▼           ▼         │
// │            PARTIALLY_USED  FULLY_USED    │
// │                                          │
// │  Any state ──→ CANCELLED (refund)        │
// │  Any state ──→ FROZEN (fraud hold)       │
// │  Active/Partial ──→ EXPIRED (date)       │
// └──────────────────────────────────────────┘

interface GiftCardRedemption {
  id: string;
  gift_card_id: string;
  booking_id: string;
  amount: Money;
  balance_after: Money;
  redeemed_at: string;
  redeemed_by: string;                 // customer or agent
}
```

### Travel Credit System

```typescript
interface TravelCredit {
  id: string;
  agency_id: string;
  customer_id: string;

  // Source
  type: CreditType;
  source_ref: string;                  // reference to source event
  reason: string;

  // Value
  amount: Money;
  original_amount: Money;              // before partial use
  balance: Money;
  currency: string;

  // Validity
  issued_at: string;
  expires_at: string;
  is_active: boolean;

  // Restrictions
  applicable_to: CreditApplicability;

  // Usage
  usages: CreditUsage[];

  created_at: string;
}

type CreditType =
  | "REFERRAL"         // earned from referring a friend
  | "CANCELLATION"     // refund as credit (instead of cash)
  | "COMPENSATION"     // service recovery credit
  | "LOYALTY"          // tier milestone reward
  | "PROMOTIONAL"      // campaign giveaway
  | "OVERPAYMENT"      // excess payment returned as credit
  | "GIFT";            // gifted by agency

interface CreditApplicability {
  booking_types: BookingType[];
  destinations: string[];
  vendors: string[];
  min_booking_value: Money | null;
  can_combine_with_cash: boolean;
  max_credit_per_booking: Money | null;
}

interface CreditUsage {
  id: string;
  credit_id: string;
  booking_id: string;
  amount: Money;
  balance_after: Money;
  used_at: string;
}

// ── Credit precedence rules ──
// ┌─────────────────────────────────────────┐
// │  When a customer has multiple credits:    │
// │                                           │
// │  1. Expiring soon first (FIFO by expiry) │
// │  2. Promotional credits before loyalty    │
// │  3. Referral credits last (highest value)│
// │  4. Cannot stack > 3 credits per booking │
// │                                           │
// │  Credit → Cash ratio:                     │
// │  - 1:1 for cancellation/overpayment      │
// │  - 1:1 for referral                      │
// │  - Promotional may have restrictions      │
// └───────────────────────────────────────────┘
```

### Corporate Gift Card Programs

```typescript
interface CorporateGiftCardOrder {
  id: string;
  agency_id: string;
  corporate_id: string;

  // Order details
  quantity: number;
  face_value_per_card: Money;
  total_value: Money;
  currency: string;

  // Customization
  design_template: string;
  custom_message: string | null;
  corporate_logo_url: string | null;
  branded: boolean;

  // Delivery
  delivery_method: "BULK_EMAIL" | "BULK_WHATSAPP" | "PHYSICAL_SHIP" | "CODES_ONLY";
  recipient_list: {
    name: string;
    email: string;
    phone: string;
    personal_message: string | null;
  }[];

  // Payment
  payment_status: PaymentStatus;
  discount_applied: number;            // bulk discount %
  invoice_id: string | null;

  // Tracking
  cards_generated: number;
  cards_delivered: number;
  cards_activated: number;
  cards_redeemed: number;

  created_at: string;
}

// ── Bulk pricing tiers ──
// ┌─────────────────────────────────────────┐
// │  Volume         | Discount  | Min Order  │
// │  ─────────────────────────────────────── │
// │  10-49 cards    | 5% off    | ₹25,000   │
// │  50-99 cards    | 10% off   | ₹1,00,000 │
// │  100-499 cards  | 15% off   | ₹2,50,000 │
// │  500-999 cards  | 18% off   | ₹10,00,000│
// │  1000+ cards    | 20% off   | ₹20,00,000│
// │                                           │
// │  Corporate gift cards are popular for:    │
// │  - Employee rewards (Diwali bonus)       │
// │  - Client gifting (year-end)             │
// │  - Incentive programs (sales targets)    │
// │  - Conference giveaways                  │
// └───────────────────────────────────────────┘
```

### Multi-Currency Gift Card Handling

```typescript
interface CurrencyConversion {
  from_currency: string;
  to_currency: string;
  rate: number;
  rate_source: "FIXED" | "LIVE";
  fixed_rate: number | null;
  conversion_fee_percentage: number;
}

// Gift card purchased in INR, used for international booking:
// ┌─────────────────────────────────────────┐
// │  Gift Card: ₹50,000 (INR)                │
// │  Booking: Singapore package (SGD 800)    │
// │                                           │
// │  Conversion:                              │
// │  ₹50,000 ÷ 16.2 (INR/SGD) = SGD 3,086  │
// │  Booking: SGD 800                         │
// │  Remaining: ₹50,000 - (800 × 16.2)      │
// │           = ₹50,000 - ₹12,960            │
// │           = ₹37,040                       │
// │                                           │
// │  Or: deduct in INR, maintain INR balance  │
// │  Gift card stays in INR, conversion at    │
// │  booking time with live rate              │
// └───────────────────────────────────────────┘
```

---

## Open Problems

1. **Partial redemption UX** — When a gift card covers only part of a booking, the remaining balance needs to be clearly shown. Customers often forget they have partial balances.

2. **Credit expiry ethics** — Expiring earned credits (cancellation refunds) may violate consumer protection norms in India. Need to differentiate between promotional credits (can expire) and refund credits (should not expire).

3. **Cross-border gift cards** — RBI regulations on prepaid instruments may classify travel gift cards differently. Need legal review for compliance.

4. **Physical gift card logistics** — Printed gift cards need manufacturing, shipping, and tracking. For agencies doing this at scale, logistics is a hidden cost center.

---

## Next Steps

- [ ] Build gift card lifecycle engine with activation and redemption
- [ ] Implement travel credit system with precedence rules
- [ ] Create corporate bulk order management
- [ ] Design multi-currency conversion for gift card redemptions
- [ ] Study Indian prepaid instrument regulations (RBI guidelines)
