# Customer Credit & Wallet — Store Credit Management

> Research document for customer credit balances, store wallet, refund-as-credit, promotional credits, gift card balances, and credit lifecycle management for the Waypoint OS platform.

---

## Key Questions

1. **How do we manage customer credit balances across multiple credit sources?**
2. **When should refunds be issued as credit vs. cash refund?**
3. **How do promotional credits, loyalty credits, and refund credits interact?**
4. **What expiry, transfer, and redemption rules apply to different credit types?**

---

## Research Areas

### Customer Credit & Wallet System

```typescript
interface CustomerCreditWallet {
  // Unified credit management for customer account balances
  credit_sources: {
    REFUND_AS_CREDIT: {
      description: "Customer chooses store credit instead of cash refund";
      incentive: "10-15% bonus credit (₹10K refund → ₹11-11.5K credit)";
      trigger: "Cancellation or partial refund where customer opts for credit";
      expiry: "12 months from issue date";
      usage: "Can be used for any future booking with the agency";
    };

    PROMOTIONAL_CREDIT: {
      description: "Credits issued as part of promotions or compensation";
      types: {
        welcome_credit: "₹500 credit for new customer signup (first booking only)";
        apology_credit: "₹1K-5K credit for service failure compensation";
        referral_reward: "₹500 credit when referred friend makes first booking";
        review_reward: "₹200 credit for verified post-trip review";
        social_share_reward: "₹100 credit for sharing trip on social media",
      };
      expiry: "6 months from issue (promotional credits expire faster)";
      restrictions: "May be restricted to specific destinations or minimum booking value",
    };

    LOYALTY_CREDIT: {
      description: "Credits earned through loyalty program redemptions";
      mechanism: "Loyalty points convert to credit at defined rate (100 pts = ₹100)";
      expiry: "Per loyalty program terms (typically 24 months)";
      usage: "Any booking, no restrictions",
    };

    GIFT_CARD_BALANCE: {
      description: "Balance from purchased or received gift cards";
      source: "Agency gift cards (₹1K-50K denominations) purchased by customer or third party";
      expiry: "Gift cards valid for 24 months; no expiry on partially used balance";
      usage: "Any booking; can be combined with other payment methods",
    };

    VOUCHER_CREDIT: {
      description: "Credits from promotional vouchers or coupons";
      types: {
        fixed_value: "₹2,000 off coupon (redeemed as credit to wallet then applied)";
        percentage: "10% off booking (applied directly, not credited to wallet)";
        experience: "Free activity credit (₹3K for activities only)";
      };
      expiry: "Per voucher terms";
    };
  };

  // ── Customer wallet — agent view ──
  // ┌─────────────────────────────────────────────────────┐
  // │  💳 Credit Wallet · Sharma Family                         │
  // │                                                       │
  // │  Total Balance: ₹14,700                                 │
  // │                                                       │
  // │  Breakdown:                                           │
  // │  💰 Refund Credit: ₹8,800 (expires Jan 15, 2027)         │
  // │     From: Goa trip cancellation (Nov 2026)              │
  // │     + 10% bonus applied                                 │
  // │                                                       │
  // │  🎁 Promotional Credit: ₹500 (expires Aug 30, 2026)      │
  // │     From: Welcome bonus                                 │
  // │     ⚠️ Expiring soon!                                    │
  // │                                                       │
  // │  ⭐ Loyalty Credit: ₹2,400 (expires Dec 2027)             │
  // │     From: 2,400 points converted                        │
  // │                                                       │
  // │  🎀 Gift Card: ₹3,000 (expires Mar 2027)                  │
  // │     From: Anniversary gift from Rahul                    │
  // │                                                       │
  // │  Recent Activity:                                     │
  // │  Dec 15: +₹500 Referral reward (Priya booked)            │
  // │  Dec 10: -₹2,000 Applied to Singapore trip booking       │
  // │  Dec 5: +₹8,800 Refund credit (Goa cancellation)         │
  // │                                                       │
  // │  [Apply to Booking] [Send as Gift] [View History]        │
  // └─────────────────────────────────────────────────────────┘
}
```

### Credit Rules Engine

```typescript
interface CreditRulesEngine {
  // Rules governing credit issuance, usage, and expiry
  usage_rules: {
    COMBINATION: {
      description: "How multiple credit types can be combined";
      rules: [
        "Multiple credit types can be used in a single booking",
        "Credits consumed in order of soonest expiry first (FIFO by expiry)",
        "Credit cannot exceed booking value (no cash-out of credit balance)",
        "Maximum 3 credit types per booking (simplify UX)",
      ];
    };

    PARTIAL_USAGE: {
      description: "When credit doesn't cover full booking value";
      mechanism: "Credit covers part + remaining paid via payment method";
      example: "₹14,700 credit + ₹1,85,300 card payment = ₹2L booking";
    };

    RESTRICTIONS: {
      rules: [
        "Refund credits cannot be used for same destination/cancelled trip within 60 days",
        "Welcome credit requires minimum ₹15K booking value",
        "Apology credits have no restrictions (agency's goodwill gesture)",
        "Gift cards cannot be converted to cash or transferred to another wallet",
      ];
    };
  };

  expiry_management: {
    EXPIRY_NOTIFICATIONS: {
      schedule: [
        "30 days before expiry: 'Your ₹500 credit expires soon — use it!'",
        "14 days before expiry: Urgent reminder with booking suggestions",
        "7 days before expiry: Final reminder with quick-use options",
        "3 days before expiry: Last chance notification",
      ];
      channel: "WhatsApp (primary), email (backup), app push notification";
    };

    EXPIRY_EXTENSION: {
      description: "Agent can extend expiry for goodwill in special cases";
      authority: "Agent: extend up to 30 days; Manager: extend up to 90 days";
      logging: "All extensions logged with reason and approver",
    };
  };

  credit_analytics: {
    ISSUANCE_TRACKING: {
      metrics: [
        "Total credits issued by type (refund, promo, loyalty, gift)",
        "Credit issuance trend (are refund credits increasing = problem?)",
        "Average credit balance per customer",
        "Total outstanding credit liability",
      ];
    };

    REDEMPTION_TRACKING: {
      metrics: [
        "Credit utilization rate (issued vs. redeemed before expiry)",
        "Average time to redemption",
        "Credit expiry rate (% of credits that expire unused)",
        "Revenue impact (bookings driven by credit availability)",
      ];
    };

    BEHAVIORAL_INSIGHTS: {
      insights: [
        "Customers with credit balance book 40% more frequently",
        "Refund-as-credit (with bonus) retains 85% of cancelled-trip revenue",
        "Expiring credit notifications drive 15% immediate bookings",
        "Credit balance > ₹5K = high re-engagement probability",
      ];
    };
  };
}
```

---

## Open Problems

1. **Credit liability on balance sheet** — Outstanding customer credits are a financial liability. As the customer base grows, total credit liability can become significant. Finance team needs visibility into total outstanding credits.

2. **Fraud prevention** — Creating fake referrals for referral credits, or repeatedly cancelling to accumulate refund-credits with bonuses. Anti-abuse rules needed.

3. **Credit expiry sensitivity** — Expiring a customer's ₹5,000 credit creates negative sentiment. Automatic extensions for loyal customers or conversion to smaller loyalty points at expiry (instead of losing value entirely) can preserve goodwill.

4. **Cross-currency credits** — If a customer cancels a USD-priced international trip, should the credit be in INR or USD? Exchange rate fluctuations create complications.

5. **Regulatory compliance** — Gift cards and stored value instruments may fall under RBI guidelines for prepaid instruments. Legal review of credit wallet structure is needed.

---

## Next Steps

- [ ] Build customer wallet system with multi-source credit tracking
- [ ] Create credit rules engine with combination, partial usage, and restriction rules
- [ ] Implement expiry management with tiered notification schedule
- [ ] Design credit application flow during booking checkout
- [ ] Build credit analytics dashboard with issuance, redemption, and liability tracking
- [ ] Implement anti-fraud rules for referral and promotional credit abuse
- [ ] Create agent-facing credit management tools (issue, extend, adjust credits)
