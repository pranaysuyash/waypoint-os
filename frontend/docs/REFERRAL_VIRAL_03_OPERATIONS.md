# Referral & Viral Engine — Operations & Fraud Prevention

> Research document for referral program operations, fraud detection, ambassador management workflows, and referral program compliance for travel agencies.

---

## Key Questions

1. **How do we detect and prevent referral fraud?**
2. **What workflows manage the ambassador program?**
3. **How do we handle referral disputes and edge cases?**
4. **What compliance requirements apply to referral programs?**

---

## Research Areas

### Referral Fraud Detection

```typescript
interface ReferralFraudDetection {
  // Multi-layer fraud prevention
  fraud_signals: {
    SELF_REFERRAL: {
      detection: [
        "Same phone number / email on referrer and referee",
        "Same device fingerprint (browser cookies, app device ID)",
        "Same IP address at referral creation and redemption",
        "Same address or payment method",
      ];
      action: "Auto-reject referral, warn customer, flag account";
      prevalence: "15% of suspicious referrals";
    };

    FABRICATED_REFERRAL: {
      detection: [
        "Referee account created minutes after referral link shared",
        "Referee has no genuine travel inquiry patterns",
        "Referee uses temporary/disposable email",
        "Referee cancels immediately after reward issued",
      ];
      action: "Hold reward until trip completes, manual review if score > 0.7";
      prevalence: "8% of suspicious referrals";
    };

    REWARD_GAMING: {
      detection: [
        "Customer refers multiple people who book minimum-value trips",
        "Referrals cluster around reward tier thresholds",
        "Pattern of referrals immediately before own trip booking (using stacked credits)",
        "Multiple referrals from same IP/device in short window",
      ];
      action: "Flag for manual review, apply cool-down between referrals";
      prevalence: "5% of suspicious referrals";
    };

    CHANNEL_ABUSE: {
      detection: [
        "Referral code posted on public coupon/deal sites",
        "Referral link shared in spam WhatsApp groups",
        "Referral code used in paid advertising by customer",
        "Bulk message patterns from referrer's phone number",
      ];
      action: "Deactivate referral code, revoke pending rewards, notify customer";
      prevalence: "3% of suspicious referrals";
    };
  };

  // Fraud scoring model
  fraud_score: {
    formula: "weighted_sum(fraud_signals) * velocity_multiplier";
    thresholds: {
      LOW: { range: "0-0.3", action: "Auto-approve" };
      MEDIUM: { range: "0.3-0.6", action: "Hold reward until trip completes" };
      HIGH: { range: "0.6-0.8", action: "Manual review before reward" };
      CRITICAL: { range: "0.8-1.0", action: "Auto-reject, notify compliance" };
    };
  };
}

// ── Fraud detection dashboard ──
// ┌─────────────────────────────────────────────────────┐
// │  Referral Fraud Detection                                 │
// │                                                       │
// │  This month: 12 flagged · 8 resolved · 4 pending       │
// │  Fraud rate: 2.1% (down from 3.4% last month)          │
// │  Savings from prevention: ₹48K                         │
// │                                                       │
// │  ┌─ Flagged Referrals ──────────────────────────────┐│
// │  │ ⚠️ MEDIUM — Gupta → "Sneha Patel"                  ││
// │  │    Signal: Same IP address, 4min gap              ││
// │  │    Score: 0.45 · Status: Hold until trip complete ││
// │  │    Trip: Kerala (WP-502) · Booking: ₹52,000       ││
// │  │    [Approve] [Reject] [Investigate]                ││
// │  │                                                    ││
// │  │ 🔴 HIGH — Mehta → "Ravi Kumar"                     ││
// │  │    Signal: Disposable email, no travel inquiry     ││
// │  │    Score: 0.72 · Status: Manual review needed      ││
// │  │    [Approve] [Reject] [Investigate]                ││
// │  │                                                    ││
// │  │ 🟢 RESOLVED — Sharma → "Verma family"              ││
// │  │    Signal: Same city (false positive)              ││
// │  │    Score: 0.32 · Status: Approved after review     ││
// │  └────────────────────────────────────────────────────┘│
// │                                                       │
// │  Top fraud patterns this quarter:                      │
// │  Self-referral:      45% ████████████████████████      │
// │  Fabricated account: 30% █████████████                 │
// │  Reward gaming:      15% ███████                       │
// │  Channel abuse:      10% █████                         │
// │                                                       │
// │  [Rules Settings] [Export Fraud Report]                   │
// └─────────────────────────────────────────────────────┘
```

### Ambassador Management Workflow

```typescript
interface AmbassadorManagement {
  // End-to-end ambassador lifecycle
  lifecycle: {
    // Nomination & qualification
    nomination: {
      auto_nominate: {
        criteria: {
          min_trips: 3;
          min_spend: "₹5,00,000";
          min_nps: 9;
          min_referrals: 2;
          account_age_months: 12;
        };
        notification: "We'd love to have you as a Waypoint Ambassador! Enjoy priority booking, exclusive deals, and earn rewards for sharing your travel experiences.";
      };

      manual_nominate: {
        who: "Agent identifies exceptional customer";
        requires: "Manager approval + customer consent";
      };
    };

    // Onboarding
    onboarding: {
      steps: [
        "Welcome call from agency owner/manager",
        "Ambassador agreement signing (expectations + benefits)",
        "Dedicated agent assignment (concierge)",
        "Personalized referral code: WP-AMB-{name}",
        "Social media kit (branded templates, photos with consent)",
        "Ambassador WhatsApp group invite",
      ];
      duration: "30-minute call + email follow-up";
    };

    // Performance tracking
    tracking: {
      monthly_scorecard: {
        referrals_made: number;
        referrals_converted: number;
        conversion_rate: number;
        social_media_posts: number;
        reviews_submitted: number;
        engagement_score: number;           // 0-100
      };

      quarterly_review: {
        meeting: "30-minute call with assigned agent";
        agenda: ["Performance review", "Upcoming trips discussion", "Reward fulfillment", "Feedback collection"];
        adjustment: "Benefits adjusted based on performance";
      };
    };

    // Offboarding
    offboarding: {
      triggers: [
        "Customer explicitly requests to stop",
        "No referrals in 12 months",
        "Negative social media about agency",
        "Fraud detected in referral activity",
      ];
      process: "Graceful exit — thank you gift, retain as regular customer, no public announcement";
    };
  };
}

// ── Ambassador management ──
// ┌─────────────────────────────────────────────────────┐
// │  Ambassador Program Management                           │
// │                                                       │
// │  Active: 8 · Nominated: 3 · Under review: 1            │
// │                                                       │
// │  ┌─ Ambassador Scorecard — Rajesh Sharma ──────────┐  │
// │  │ Tier: GOLD · Member since: Jan 2026              │  │
// │  │ Assigned agent: Priya                             │  │
// │  │                                                   │  │
// │  │ This quarter:                                     │  │
// │  │ Referrals made: 5 · Converted: 3 (60%)            │  │
// │  │ Social posts: 4 · Reviews: 2                      │  │
// │  │ Engagement score: 92/100                          │  │
// │  │                                                   │  │
// │  │ Lifetime stats:                                   │  │
// │  │ Total referrals: 12 · Converted: 8 (67%)          │  │
// │  │ Revenue generated: ₹14.2L                          │  │
// │  │ Rewards earned: ₹45K (credits + upgrades)         │  │
// │  │ Ambassador ROI: 31.5x                             │  │
// │  │                                                   │  │
// │  │ Benefits used this year:                          │  │
// │  │ ✅ Priority booking (used 2x)                     │  │
// │  │ ✅ Airport lounge voucher (redeemed)              │  │
// │  │ ✅ Free upgrade (Singapore trip)                  │  │
// │  │ ⬜ Annual gift (due: birthday in Aug)             │  │
// │  │                                                   │  │
// │  │ Next review: Apr 30, 2026                          │  │
// │  │ [Schedule Review] [Send Reward] [View History]     │  │
// │  └───────────────────────────────────────────────────┘  │
// │                                                       │
// │  Nominated candidates:                                 │
// │  • Verma family — meets criteria, awaiting consent      │
// │  • Priya Iyer — 2 trips, ₹4.8L, NPS 10               │
// │  • Kapoor family — 4 trips, ₹6.2L, NPS 9, 1 referral  │
// │                                                       │
// │  [Nominate Customer] [Bulk Actions] [Export Report]      │
// └─────────────────────────────────────────────────────┘
```

### Referral Dispute Resolution

```typescript
interface ReferralDisputeResolution {
  // Common dispute types and resolution
  disputes: {
    MISSING_REFERRAL: {
      scenario: "Customer says they were referred but code wasn't applied";
      resolution_steps: [
        "Check if referral code was entered at inquiry stage",
        "Verify referrer account exists and code is active",
        "Check if customer's phone/email matches referee profile",
        "If valid: retroactively apply referral, issue rewards to both",
        "If invalid: explain why, offer standard discount as goodwill",
      ];
      sla: "Resolve within 24 hours";
    };

    REWARD_NOT_RECEIVED: {
      scenario: "Referrer claims they didn't receive credit after friend booked";
      resolution_steps: [
        "Verify referee trip is confirmed (not just inquiry)",
        "Check if minimum booking value threshold met",
        "Verify fraud score was below rejection threshold",
        "If all clear: issue reward immediately with apology",
        "If trip cancelled: explain reward is on confirmed bookings only",
      ];
      sla: "Resolve within 48 hours";
    };

    REFERRAL_CODE_ABUSE: {
      scenario: "Referral code found on public coupon site";
      resolution_steps: [
        "Screenshot evidence of public posting",
        "Deactivate referral code immediately",
        "Contact referrer: explain terms of use violation",
        "First offense: warning + new code issued",
        "Repeat offense: suspend referral privileges for 6 months",
      ];
      sla: "Code deactivated within 2 hours of detection";
    };

    DUPLICATE_REFERRAL: {
      scenario: "Two customers claim to have referred the same person";
      resolution_steps: [
        "Check attribution chain: first-touch gets the referral",
        "If both shared at same event (e.g., group dinner): split reward",
        "If neither can be clearly attributed: ask referee who referred them",
        "Document decision for audit trail",
      ];
      sla: "Resolve within 72 hours";
    };
  };
}

// ── Dispute resolution queue ──
// ┌─────────────────────────────────────────────────────┐
// │  Referral Dispute Queue                                   │
// │                                                       │
// │  Open: 3 · Avg resolution: 18 hours · SLA compliance: 94%│
// │                                                       │
// │  🟡 PENDING — Missing referral credit                    │
// │  Customer: Anita Desai says she was referred by Sharma   │
// │  Investigation: Code not entered at booking              │
// │  Evidence: WhatsApp screenshot shows Sharma shared code  │
// │  Recommendation: Apply retroactive referral              │
// │  SLA: 6 hours remaining                                  │
// │  [Approve] [Reject] [Request More Info]                  │
// │                                                       │
// │  🟡 PENDING — Reward not received                        │
// │  Referrer: Gupta (code WP-RAH-GUPTA)                     │
// │  Referee: Mehta family booked Kerala (₹68,000)           │
// │  Status: Trip confirmed, reward pending 5 days           │
// │  Issue: System flagged for fraud review (score 0.35)     │
// │  Recommendation: Approve — legitimate referral           │
// │  SLA: 24 hours remaining                                 │
// │  [Approve] [Reject] [Escalate]                           │
// │                                                       │
// │  [Resolved Today: 2] [SLA Breached: 0] [Export]           │
// └─────────────────────────────────────────────────────┘
```

### Referral Program Compliance

```typescript
interface ReferralCompliance {
  // Legal and regulatory requirements
  requirements: {
    TAX_COMPLIANCE: {
      description: "Referral rewards may have tax implications";
      rules: [
        "Travel credits: No tax implication (discount, not income)",
        "Cash rewards > ₹50,000/year: May require TDS under Section 194C",
        "Free trips: Considered benefit-in-kind, may need to be declared",
        "Ambassador free trips: Clearly document as promotional expense",
      ];
      action: "Annual review with CA; include in GST filings as promotional expense";
    };

    ADVERTISING_STANDARDS: {
      description: "ASCI (Advertising Standards Council of India) guidelines";
      rules: [
        "Referral claims must be truthful (real testimonials only)",
        "Disclose referral relationship in shared content",
        "Cannot claim 'best travel agency' without substantiation",
        "Testimonials must represent typical experience",
      ];
      action: "Template review process for all referral content";
    };

    DATA_PRIVACY: {
      description: "DPDP Act requirements for referral programs";
      rules: [
        "Cannot share referrer's name with referee without consent",
        "Cannot share referee's data with referrer",
        "Referral tracking data is 'derived data' — consent required",
        "Must provide opt-out from referral program",
        "Ambassador agreements must include data processing terms",
      ];
      action: "Include referral consent in terms of service";
    };

    CONSUMER_PROTECTION: {
      description: "Consumer Protection Act, 2019";
      rules: [
        "Referral terms must be clearly communicated before booking",
        "Cannot make referral rewards conditional on undisclosed requirements",
        "Must honor promised rewards within stated timeline",
        "Refund policy must address referral credits",
      ];
      action: "Clear terms page + FAQ for referral program";
    };
  };
}

// ── Compliance dashboard ──
// ┌─────────────────────────────────────────────────────┐
// │  Referral Program Compliance                              │
// │                                                       │
// │  Overall compliance: 96% · Last audit: Mar 2026         │
// │                                                       │
// │  Tax:     ✅ Compliant (CA review done FY25-26)        │
// │  ASCI:    ✅ Compliant (templates reviewed)             │
// │  DPDP:    ⚠️ Action needed — update consent flow       │
// │  Consumer: ✅ Compliant (terms updated Feb 2026)       │
// │                                                       │
// │  Pending actions:                                     │
// │  1. Update referral consent checkbox to include         │
// │     data sharing disclosure (DPDP requirement)          │
// │     Due: May 15, 2026                                  │
// │                                                       │
// │  2. Annual CA review for FY26-27 referral expenses      │
// │     Due: Apr 2027                                      │
// │                                                       │
// │  Quarterly audit checklist:                            │
// │  ☑ Terms of service include referral program            │
// │  ☑ Fraud detection system active and calibrated         │
// │  ☑ Reward fulfillment within SLA                        │
// │  ☑ Ambassador agreements signed and current             │
// │  ☑ Testimonial consent documented                       │
// │  ☑ Tax implications reviewed by CA                      │
// │  ☐ Consent flow update (pending May 15)                │
// │                                                       │
// │  [Run Audit] [Update Terms] [Export Compliance Report]   │
// └─────────────────────────────────────────────────────┘
```

---

## Open Problems

1. **Self-referral detection across devices** — Customers using different phones/emails for fake referrals. Device fingerprinting helps but isn't foolproof. Need behavioral pattern analysis.

2. **Ambassador motivation decay** — Ambassadors lose enthusiasm after initial excitement. Need ongoing engagement (exclusive events, early access, recognition) beyond transactional rewards.

3. **Cross-border referral tax** — When an Indian customer refers someone abroad, reward taxation becomes complex. Need jurisdiction-specific handling.

4. **Attribution in multi-touch world** — Customer sees Instagram post, visits website, then calls to book. Which referrer gets credit? Need fair multi-touch attribution model.

---

## Next Steps

- [ ] Build fraud detection engine with configurable scoring rules
- [ ] Create ambassador lifecycle management with automated scorecards
- [ ] Implement dispute resolution workflow with SLA tracking
- [ ] Design compliance audit system with quarterly checklists
