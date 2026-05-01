# WhatsApp Business Platform — Policy Compliance & Restrictions

> Research document for WhatsApp Business API policy compliance, messaging windows, template approval rules, commerce policy, opt-in requirements, rate limits, and account health management.

---

## Key Questions

1. **What are WhatsApp's messaging window rules and how do they affect trip communication?**
2. **What template categories exist and what are the approval criteria?**
3. **What does the Commerce Policy restrict for travel businesses?**
4. **What are the opt-in requirements before messaging a customer?**
5. **How do rate limits and quality scores work?**

---

## Research Areas

### 24-Hour Messaging Window

```typescript
interface MessagingWindow {
  // WhatsApp enforces a 24-hour window for free-form messages
  // Window opens when customer sends a message
  // After 24 hours, only approved templates can be sent

  window_duration: 86400;               // 24 hours in seconds

  // For travel agencies, common window scenarios:
  scenarios: {
    inquiry: {
      trigger: "Customer sends trip inquiry via WhatsApp",
      window: "24h from inquiry message",
      free_form_allowed: true,
      use_case: "Agent discusses trip options, shares itineraries"
    };
    booking_confirmation: {
      trigger: "Customer confirms booking",
      window: "24h from confirmation",
      free_form_allowed: true,
      use_case: "Agent shares booking details, payment links"
    };
    pre_departure: {
      trigger: "3 days before departure",
      window: "Expired (booking was days/weeks ago)",
      free_form_allowed: false,
      template_required: true,
      use_case: "Departure briefing, weather update, packing list"
    };
    post_trip: {
      trigger: "After trip completion",
      window: "Expired",
      free_form_allowed: false,
      template_required: true,
      use_case: "Feedback request, photo sharing, rebooking offer"
    };
  };
}
```

### Message Template Categories

```typescript
interface TemplateCategories {
  // WhatsApp has 3 template categories (updated Nov 2024):

  authentication: {
    purpose: "Verify identity via OTP",
    cost: "Lowest per-message",
    examples: ["Login OTP: {{1}}. Valid for 10 minutes."],
    approval: "Automatic if format matches",
    travel_use: "Rare — for platform login, not trip communication"
  };

  marketing: {
    purpose: "Promotions, offers, re-engagement",
    cost: "Highest per-message",
    examples: [
      "🌴 Goa packages starting ₹15,999! Book before {{1}} for early bird discount.",
      "Your dream Maldives trip is {{2}}% off this week. Reply to learn more."
    ],
    approval: "Manual review, 24-48h turnaround",
    restrictions: [
      "No misleading claims about pricing",
      "No urgency pressure ('limited time' requires actual deadline)",
      "Must include opt-out instruction",
      "Cannot promote gambling, alcohol, tobacco, weapons"
    ],
    travel_use: "Seasonal promotions, flash deals, referral programs"
  };

  utility: {
    purpose: "Transactional, account updates, alerts",
    cost: "Medium per-message",
    examples: [
      "Hi {{1}}, your trip to {{2}} departs in {{3}} days. Check your itinerary: {{4}}",
      "Payment of ₹{{1}} received for {{2}}. Booking confirmed. Ref: {{3}}",
      "Your visa for {{1}} has been approved. Collect documents from our office."
    ],
    approval: "Usually automatic if clearly transactional",
    travel_use: "Booking confirmations, visa updates, payment receipts, departure reminders"
  };
}
```

### Commerce Policy Restrictions

```typescript
interface CommercePolicy {
  // What travel agencies CANNOT sell or promote via WhatsApp:
  prohibited: {
    // Direct items
    illegal_substances: true,
    alcohol_direct_sale: true,           // Can mention wine tours, can't sell alcohol
    tobacco: true,
    weapons: true,
    gambling: true,
    adult_content: true,

    // Travel-specific restrictions
    unlicensed_travel_services: true,     // Agency must be licensed/registered
    misleading_pricing: true,            // "₹0 trip" type misleading ads
    fake_reviews: true,                  // Cannot pay for reviews via WhatsApp
    pyramid_schemes: true,              // Multi-level travel "clubs"
  };

  // What IS allowed:
  permitted: {
    tour_packages: true,                  // Domestic and international
    flight_booking: true,
    hotel_reservation: true,
    visa_services: true,
    travel_insurance: true,
    forex_services: true,                // Must be via authorized dealer
    cruise_packages: true,
    pilgrimage_tours: true,              // Hajj, Umrah, Tirupati, etc.
    adventure_activities: true,          // Trekking, scuba, etc.
  };

  // Gray areas requiring caution:
  caution: {
    timeshare_presentations: "May be flagged as solicitation",
    visa_guarantees: "Cannot guarantee visa approval in marketing",
    price_lock_guarantees: "Must have actual supplier confirmation, not aspirational pricing",
    last_minute_deals: "Must have real inventory, not bait-and-switch"
  };
}
```

### Opt-In Requirements

```typescript
interface OptInRequirements {
  // Before sending ANY WhatsApp message, customer must opt in:
  // 1. Explicit opt-in (not pre-checked boxes)
  // 2. Clear disclosure of what they'll receive
  // 3. Opt-in method must be documented

  methods: {
    whatsapp_initiated: {
      description: "Customer messages first",
      valid: true,
      proof: "WhatsApp conversation timestamp",
      best_for: "Trip inquiries, general questions"
    };
    web_form: {
      description: "Checkbox on website/booking form",
      valid: true,
      requirements: [
        "Not pre-checked",
        "Specific language: 'Receive trip updates via WhatsApp'",
        "Phone number field with country code"
      ],
      best_for: "Post-booking communication opt-in"
    };
    in_person: {
      description: "Customer agrees during office visit",
      valid: true,
      requirements: [
        "Documented in CRM",
        "Customer phone number confirmed"
      ],
      best_for: "Walk-in customers"
    };
    sms_to_whatsapp: {
      description: "Customer replies YES to SMS, then added to WhatsApp",
      valid: false,
      note: "WhatsApp does NOT accept SMS opt-in as valid WhatsApp opt-in"
    };
  };

  // Opt-out: Customer can type STOP, UNSUBSCRIBE, or any opt-out keyword
  // Must be processed within 24 hours
  // Customer blocked = permanent opt-out (cannot re-add without new opt-in)
}
```

### Rate Limits & Quality Score

```typescript
interface WhatsAppRateLimits {
  // Tier-based messaging limits:
  tiers: {
    tier_1: { limit: "1,000 customers/day", entry: "Default for new accounts" },
    tier_2: { limit: "10,000 customers/day", upgrade: "Quality rating + phone number quality" },
    tier_3: { limit: "100,000 customers/day", upgrade: "Consistent quality + volume" },
    tier_4: { limit: "Unlimited", upgrade: "Enterprise-level, manual approval" }
  };

  // Quality rating factors:
  quality: {
    good: "Low block rate, high read rate",
    medium: "Some blocks, moderate read rate",
    low: "High block rate, low read rate → rate limit downgrade",
    negative_impact: [
      "Customers blocking/reporting",
      "Template rejections",
      "Policy violations",
      "High opt-out rates"
    ]
  };

  // Travel agency specific concerns:
  travel_risks: {
    seasonality: "High volume during Diwali/summer → sudden spike may trigger limits",
    cold_messaging: "Promotional templates to non-opted-in numbers = immediate penalty",
    late_replies: "Slow agent response → customer frustration → reports"
  };
}
```

---

## Open Problems

### 1. Template Approval Latency
WhatsApp template approval takes 24-48h. For flash sales or last-minute deals, the template may be approved after the deal expires. Workaround: pre-approve seasonal templates.

### 2. Conversation-Based Pricing
WhatsApp charges per 24-hour conversation, not per message. For travel agencies with multi-day trip discussions, a single conversation may span multiple charge windows.

### 3. End-to-End Encryption Limits
WhatsApp is end-to-end encrypted. The platform cannot read customer messages for AI processing without the agent manually triggering extraction. This limits automated intake via WhatsApp.

### 4. Multi-Agent Handoff Within Window
Multiple agents may handle one customer. The 24-hour window is per-customer, not per-agent. Agent handoff must preserve conversation context without resetting the window.

---

## Next Steps

- [ ] Build template library with pre-approved seasonal templates
- [ ] Design opt-in flow in customer onboarding
- [ ] Implement quality score monitoring dashboard
- [ ] Map conversation-based pricing to billing
- [ ] Create compliance checklist for marketing campaigns

---

**Created:** 2026-05-01
**Series:** WhatsApp Business Platform (WHATSAPP_BIZ_05)
