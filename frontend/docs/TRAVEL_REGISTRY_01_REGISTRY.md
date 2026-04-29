# Customer Travel Registry & Group Gifting — Registry Engine

> Research document for travel gift registries, contribution management, group gifting workflows, and registry-driven trip funding for travel agencies.

---

## Key Questions

1. **How do customers create and share travel registries?**
2. **What group gifting workflows convert contributions to trip credits?**
3. **How do honeymoon registries work as a travel agency product?**
4. **What's the financial and operational model for registry programs?**

---

## Research Areas

### Travel Registry Engine

```typescript
interface TravelRegistry {
  // Registry creation and management
  registry_types: {
    HONEYMOON_REGISTRY: {
      occasion: "Wedding honeymoon funding";
      creator: "Couple (either partner)";
      contributors: "Wedding guests, family, friends";
      typical_goal: "₹1.5-5L (honeymoon package cost)";
      avg_contribution: "₹2,000-5,000 per guest";
      avg_registry_size: "15-40 contributors";
      fulfillment_rate: "65-75% of goal reached";
      peak_season: "Oct-Feb (wedding season)";
      margin_for_agency: "Full package margin (12-18%)";
    };

    BIRTHDAY_TRIP: {
      occasion: "Milestone birthday travel (30th, 50th, etc.)";
      creator: "Family member or friend group";
      contributors: "Friends, family, colleagues";
      typical_goal: "₹50K-2L";
      avg_contribution: "₹3,000-10,000";
      avg_registry_size: "8-20 contributors";
      fulfillment_rate: "70% of goal reached";
      margin_for_agency: "Standard booking margin";
    };

    ANNIVERSARY_FUND: {
      occasion: "Wedding anniversary trip (25th, 50th)";
      creator: "Children or couple themselves";
      contributors: "Family members, close friends";
      typical_goal: "₹1-3L";
      avg_contribution: "₹5,000-15,000";
      avg_registry_size: "6-15 contributors";
      fulfillment_rate: "80% (higher commitment from family)";
      margin_for_agency: "Standard package margin";
    };

    GRADUATION_TRIP: {
      occasion: "College graduation or study abroad celebration";
      creator: "Parents or graduate";
      contributors: "Parents, relatives, family friends";
      typical_goal: "₹50K-1.5L";
      avg_contribution: "₹2,000-5,000";
      avg_registry_size: "10-25 contributors";
      fulfillment_rate: "60%";
      margin_for_agency: "Standard + optional add-ons";
    };

    RETIREMENT_TRIP: {
      occasion: "Retirement celebration travel";
      creator: "Colleagues or family";
      contributors: "Colleagues, family, friends";
      typical_goal: "₹1-3L";
      avg_contribution: "₹3,000-10,000";
      avg_registry_size: "10-30 contributors";
      fulfillment_rate: "55% (office collections are chaotic)";
    };
  };

  // Registry configuration
  registry_setup: {
    trip_linkage: "Registry linked to specific trip proposal or package";
    goal_amount: number;                      // total funding target
    contribution_visibility: "PUBLIC" | "AMOUNT_HIDDEN" | "ANONYMOUS";
    message_to_contributors: string;          // personal note on registry page
    deadline: string;                         // when contributions close
    auto_apply: boolean;                      // auto-apply funds to trip balance
    overflow_handling: "UPGRADE_TRIP" | "CASH_REFUND" | "AGENCY_CREDIT";
    shortfall_handling: "EXTEND_DEADLINE" | "ADJUST_TRIP" | "COVER_BALANCE";
  };
}

// ── Travel registry setup ──
// ┌─────────────────────────────────────────────────────┐
// │  Travel Registry — Create New                             │
// │                                                       │
// │  Registry type: [Honeymoon ▾]                          │
// │                                                       │
// │  Trip: Singapore Honeymoon Package (5N/6D)             │
// │  Package cost: ₹2,80,000                                 │
// │  Registry goal: ₹2,00,000                                │
// │  Couple contribution: ₹80,000 (balance)                 │
// │                                                       │
// │  Registry page:                                       │
// │  🎉 Help Priya & Rohan celebrate their love!              │
// │  "We'd love your help making our Singapore honeymoon      │
// │   even more special. Every contribution means the         │
// │   world to us!"                                           │
// │                                                       │
// │  Contribution tiers:                                  │
// │  🌴 Island Dinner — ₹3,000                               │
// │  🏊 Sentosa Experience — ₹5,000                          │
// │  🌃 Night Safari — ₹2,000                                │
// │  ✈️ Flight contribution — ₹10,000                        │
// │  💝 Any amount — Custom                                   │
// │                                                       │
// │  Share link: waypoint.travel/r/priya-rohan-2026          │
// │  [Copy Link] [WhatsApp Share] [QR Code]                   │
// │                                                       │
// │  Deadline: 15 days before travel date                  │
// │  [Create Registry]                                        │
// └─────────────────────────────────────────────────────┘
```

### Contribution Management

```typescript
interface ContributionManagement {
  // How contributions flow from giver to trip
  contribution_flow: {
    PAYMENT_METHODS: {
      UPI_DIRECT: {
        description: "Contributor pays via UPI directly to registry";
        processing: "Instant settlement to agency escrow";
        fee: "0% (UPI is free)";
        experience: "Scan QR or click link → Pay → Done";
      };

      LINK_PAYMENT: {
        description: "Payment link sent via WhatsApp/email";
        processing: "Payment gateway (Razorpay/PhonePe)";
        fee: "1.5-2% of contribution amount";
        experience: "Click link → Enter amount → Pay → Confirmation";
      };

      CASH_COLLECTION: {
        description: "Agent or coordinator collects cash offline";
        processing: "Manual entry in system";
        fee: "0%";
        experience: "Agent enters contribution against contributor name";
      };

      GIFT_CARD: {
        description: "Purchase agency gift card as contribution";
        processing: "Gift card issued → Applied to registry";
        fee: "0%";
        experience: "Buy ₹X gift card → Applied to couple's trip";
      };
    };

    CONTRIBUTOR_EXPERIENCE: {
      step1: "Click registry link → See couple's story + trip details";
      step2: "Choose contribution tier or enter custom amount";
      step3: "Add personal message (optional)";
      step4: "Pay via UPI / card / net banking";
      step5: "Receive confirmation + receipt via WhatsApp";
      post: "Get update when trip happens (photo/message from couple)";
    };
  };

  // Fund management
  fund_management: {
    ESCROW_MODEL: "Funds held in agency escrow until trip is confirmed";
    PARTIAL_USE: "If goal not met, couple can use partial funds + cover balance";
    REFUND_POLICY: "If trip cancelled, contributions refunded minus processing fee";
    TAX_IMPLICATION: "Gifts under ₹50K from non-relatives are tax-free for recipient";
    AGENCY_HOLDING: "Agency holds funds until trip dates confirmed and bookings made";
    SETTLEMENT: "Funds applied to trip invoice on booking confirmation";
  };
}

// ── Contribution tracker ──
// ┌─────────────────────────────────────────────────────┐
// │  Registry — Priya & Rohan's Honeymoon                    │
// │                                                       │
// │  Goal: ₹2,00,000 · Collected: ₹1,42,000 (71%)          │
// │  ██████████████░░░░░░  ₹1.42L of ₹2L                    │
// │  Contributors: 18 of 25 invited                           │
// │  Days remaining: 12                                      │
// │                                                       │
// │  Recent contributions:                                │
// │  💝 ₹5,000 — "Have a wonderful trip!" — Uncle Rajesh     │
// │  🌴 ₹3,000 — Island Dinner — College friend Neha        │
// │  ✈️ ₹10,000 — Flight gift — Mom & Dad                    │
// │  💝 ₹2,000 — "Enjoy every moment!" — Colleague Amit     │
// │                                                       │
// │  Fund allocation:                                     │
// │  ₹1,42,000 in escrow                                    │
// │  ₹0 processing fees (92% via UPI)                        │
// │  Auto-apply to trip: ON                                  │
// │                                                       │
// │  [Send Reminder] [Add Contributor] [Download Report]      │
// │  [Couple View] [Share Update]                              │
// └─────────────────────────────────────────────────────┘
```

### Honeymoon Registry as Agency Product

```typescript
interface HoneymoonRegistryProduct {
  // Honeymoon registry as a packaged offering
  product_design: {
    NAME: "Honeymoon Wishes by Waypoint";
    TAGLINE: "Your dream honeymoon, gifted by those who love you";
    POSITIONING: "Alternative to physical wedding gifts — contribute to experiences";

    INCLUDED_IN_PRODUCT: {
      personalized_registry_page: "Beautiful page with couple story, trip details, contribution tiers";
      whatsapp_invites: "Auto-generated WhatsApp invites with registry link";
      qr_code_printable: "QR code for wedding invitation card / reception display";
      contribution_tracking: "Real-time dashboard for couple and agency";
      thank_you_automation: "Auto thank-you message to contributors after payment";
      trip_fund_management: "Escrow management until trip booking confirmed";
      milestone_updates: "Updates to contributors when trip milestones happen";
      post_trip_share: "Couple can share 1 trip photo with all contributors";
    };

    AGENCY_REVENUE: {
      booking_margin: "Standard package margin on the honeymoon trip";
      convenience_fee: "Optional 2% convenience fee on contributions (absorbed or passed to contributor)";
      upgrade_revenue: "Upsell opportunities when registry exceeds goal";
      repeat_customers: "35% of honeymoon couples book anniversary trips within 2 years";
    };
  };

  // Wedding planner partnership
  partnerships: {
    WEDDING_PLANNER: {
      role: "Recommend honeymoon registry to couples during wedding planning";
      commission: "₹500-1,000 referral fee per registry created";
      integration: "Registry link included in wedding invitations";
    };

    WEDDING_WEBSITE: {
      role: "Registry widget on wedding website (WedMeGood, WeddingWire)";
      integration: "Embed registry on couple's wedding page";
      value: "Couples already using wedding websites for RSVP — natural fit";
    };

    HOTEL_PARTNER: {
      role: "Hotel offers special honeymoon amenities for registry couples";
      examples: "Room upgrade, candlelight dinner, spa session, cake";
      cost: "₹2-5K in value, ₹500 actual cost to hotel — high perceived value";
    };
  };
}

// ── Honeymoon registry product page ──
// ┌─────────────────────────────────────────────────────┐
// │  🎉 Honeymoon Wishes by Waypoint                          │
// │  Your dream honeymoon, gifted by those who love you       │
// │                                                       │
// │  How it works:                                       │
// │  1. Choose your honeymoon package                      │
// │     [Browse Destinations] or [Use Custom Itinerary]       │
// │                                                       │
// │  2. Set up your registry                               │
// │     Personal page · Contribution tiers · QR code          │
// │                                                       │
// │  3. Share with loved ones                              │
// │     WhatsApp · Wedding card QR · Wedding website          │
// │                                                       │
// │  4. We handle the rest                                 │
// │     Track contributions · Manage funds · Book trip        │
// │                                                       │
// │  Packages:                                            │
// │  🏝️ Bali Honeymoon — ₹1.8L (5N) · Most popular          │
// │  🗼 Singapore Romance — ₹2.2L (5N) · Top rated           │
// │  🏔️ Maldives Luxury — ₹3.5L (4N) · Premium               │
// │  🏰 Europe Discovery — ₹4.5L (7N) · Grand                │
// │  ✨ Custom — Your dream destination                       │
// │                                                       │
// │  [Start Your Registry] [Talk to Us]                       │
// └─────────────────────────────────────────────────────┘
```

---

## Open Problems

1. **Trust and transparency** — Contributors need confidence their money reaches the couple's trip. Need clear escrow model and real-time visibility into fund status.

2. **Social dynamics** — Some guests feel pressured by registry asks. The framing matters: "contribute to experiences" vs. "give us money." Messaging and design must handle this delicately.

3. **Competitive alternatives** — Wedding gift registries (Amazon, Ikea) and honeymoon funds (HoneyFund, Traveler's Joy) exist. Need differentiation through the actual trip planning value.

4. **Cash vs. digital** — Indian weddings still run heavily on cash gifts (₹50K-5L in envelopes). Converting physical gift-giving to digital contributions requires cultural sensitivity.

---

## Next Steps

- [ ] Build registry creation flow with trip linkage and contribution tiers
- [ ] Implement contribution payment processing with escrow management
- [ ] Design contributor experience with minimal friction (UPI-first)
- [ ] Create honeymoon registry as packaged agency product
