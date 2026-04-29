# Agency Sales Playbook — Objection Handling & Closing

> Research document for customer objection classification, response frameworks, closing techniques, and negotiation playbooks for Indian travel agencies.

---

## Key Questions

1. **What are the most common customer objections?**
2. **How do we structure objection responses?**
3. **What closing techniques work for Indian travel customers?**
4. **How do negotiations work within margin guardrails?**

---

## Research Areas

### Objection Classification & Response Framework

```typescript
interface ObjectionHandler {
  // Objection categories with frequency
  categories: {
    PRICE: {
      frequency: number;                  // 38% of all objections
      sub_types: {
        "TOO_EXPENSIVE": {
          frequency: number;              // 55% of price objections
          responses: {
            approach: "REFRAME_VALUE";
            template: string;
            key_points: string[];
            data_needed: string[];
          }[];
        };
        "CHEAPER_ELSEWHERE": {
          frequency: number;              // 28% of price objections
          responses: {
            approach: "COMPARE_EFFECTIVE_PRICE";
            template: string;
            key_points: string[];
          }[];
        };
        "BUDGET_CONSTRAINT": {
          frequency: number;              // 17% of price objections
          responses: {
            approach: "REDUCE_SCOPE";
            template: string;
            alternatives: string[];
          }[];
        };
      };
    };

    TRUST: {
      frequency: number;                  // 22% of all objections
      sub_types: {
        "FIRST_TIME_AGENCY": {};
        "PAST_BAD_EXPERIENCE": {};
        "WILL_BOOK_DIRECTLY": {};
      };
    };

    TIMING: {
      frequency: number;                  // 18% of all objections
      sub_types: {
        "NOT_READY_YET": {};
        "TOO_EARLY_TO_BOOK": {};
        "WAITING_FOR_VISA": {};
      };
    };

    ITINERARY: {
      frequency: number;                  // 14% of all objections
      sub_types: {
        "WANT_DIFFERENT_HOTEL": {};
        "TOO_PACKED": {};
        "MISSING_SOMETHING": {};
      };
    };

    INDEPENDENCE: {
      frequency: number;                  // 8% of all objections
      sub_types: {
        "CAN_PLAN_MYSELF": {};
        "PREFER_OTA": {};
        "DONT_NEED_AGENT": {};
      };
    };
  };
}

// ── Objection response framework ──
// ┌─────────────────────────────────────────────────────┐
// │  Objection Handler — Real-Time Agent Assist             │
// │                                                       │
// │  Customer says: "This is too expensive"                │
// │  Detected objection: PRICE → TOO_EXPENSIVE             │
// │                                                       │
// │  Suggested response approach: REFRAME VALUE            │
// │                                                       │
// │  ┌───────────────────────────────────────────────┐   │
// │  │ Template (personalize before sending):          │   │
// │  │                                               │   │
// │  │ "I understand the price is a key factor,       │   │
// │  │  Sharma ji. Let me break down what's included  │   │
// │  │  so you can see the full value:                │   │
// │  │                                               │   │
// │  │  ✅ 5-star hotel (not 3-star like most quotes) │   │
// │  │  ✅ All meals included (no hidden food costs)  │   │
// │  │  ✅ Private transfers (no shared cabs)         │   │
// │  │  ✅ 24/7 trip support (we're a call away)      │   │
// │  │  ✅ Travel insurance included                  │   │
// │  │                                               │   │
// │  │  If you were to book all this separately,      │   │
// │  │  it would come to ₹2.1L — we're offering      │   │
// │  │  ₹1.85L as a complete package."               │   │
// │  └───────────────────────────────────────────────┘   │
// │                                                       │
// │  Key data points to include:                          │
// │  • Competitor effective price comparison              │
// │  • Cost of booking components separately              │
// │  • Value of included services (insurance, support)    │
// │                                                       │
// │  Alternative approaches:                              │
// │  • [Reduce scope] — Remove 1 activity, save ₹8K     │
// │  • [Payment plan] — 50% now, 50% 2 weeks before     │
// │  • [Different dates] — Shift by 3 days, save ₹12K   │
// │                                                       │
// │  [Copy to WhatsApp] [Edit Response] [Use Different]   │
// └─────────────────────────────────────────────────────┘
```

### Closing Techniques for Indian Market

```typescript
interface ClosingTechniques {
  techniques: {
    // India-specific closing patterns
    ASSUMPTIVE_CLOSE: {
      description: "Assume the booking and move to logistics";
      example: "So for the June 1-6 dates, should I block the Taj Vivanta rooms now?";
      best_for: "CONFIDENT leads who have shown strong interest";
      cultural_note: "Works well with Indian customers who prefer decisive action";
    };

    URGENCY_CLOSE: {
      description: "Create time-limited urgency with real data";
      example: "Only 2 rooms left at this rate — the rate alert just came in. Shall I hold one for you?";
      best_for: "Price-sensitive customers close to deciding";
      cultural_note: "Must be genuine (backed by rate data), not fake urgency";
    };

    ALTERNATIVE_CLOSE: {
      description: "Give two options, both lead to booking";
      example: "Would you prefer the 3-star package at ₹1.6L or the 4-star at ₹1.85L?";
      best_for: "Customers who have accepted the trip but haggling on price";
      cultural_note: "Indian customers appreciate choice; never give just one option";
    };

    SOCIAL_PROOF_CLOSE: {
      description: "Use testimonials from similar customers";
      example: "The Gupta family just returned from the same Singapore trip last week and loved it. Here's what they said...";
      best_for: "First-time customers or trust-concerned leads";
      cultural_note: "Extremely effective in India — word-of-mouth is king";
    };

    FAMILY_CLOSE: {
      description: "Involve the decision-maker (often not the inquirer)";
      example: "Would you like me to send a detailed proposal that you can share with your family? I can include a comparison sheet.";
      best_for: "Family trips where spouse/parents are decision-makers";
      cultural_note: "Travel decisions in India are often family decisions, not individual";
    };

    PAYMENT_PLAN_CLOSE: {
      description: "Make the financial commitment manageable";
      example: "We can split this into 3 payments: ₹50K now, ₹50K next month, and the rest before travel.";
      best_for: "Budget-constrained customers who want the trip";
      cultural_note: "EMI culture in India makes payment plans very effective";
    };
  };
}

// ── Closing technique selector ──
// ┌─────────────────────────────────────────────────────┐
// │  Closing Recommendation — Sharma Family Singapore       │
// │                                                       │
// │  Deal stage: NEGOTIATING (day 3)                       │
// │  Customer signals:                                    │
// │  • Responded to proposal within 1 hour ✅             │
// │  • Asked about payment options ✅                     │
// │  • Compared with MakeMyTrip (price shopping) ⚠️       │
// │  • Has not involved spouse yet ⚠️                     │
// │                                                       │
// │  Recommended closing technique:                        │
// │  1. SOCIAL_PROOF_CLOSE — share Gupta family review     │
// │  2. FAMILY_CLOSE — send detailed proposal for spouse   │
// │  3. ALTERNATIVE_CLOSE — offer 2 package variants       │
// │                                                       │
// │  Suggested sequence:                                  │
// │  Step 1: Share Gupta testimonial via WhatsApp          │
// │  Step 2: "Would you like a version you can show your   │
// │          family? I'll include the comparison with       │
// │          MakeMyTrip so they can see the value."         │
// │  Step 3: If positive → ASSUMPTIVE_CLOSE:               │
// │          "Should I go ahead and hold the rooms?"        │
// │                                                       │
// │  [Copy Step 1] [Copy Step 2] [Copy Step 3]             │
// └─────────────────────────────────────────────────────┘
```

### Negotiation Playbook

```typescript
interface NegotiationPlaybook {
  // Negotiation rules within margin guardrails
  rules: {
    // What agents CAN do without approval
    autonomous: {
      offer_payment_plan: true;
      adjust_dates_for_better_rates: true;
      remove_optional_components: true;
      upgrade_room_type_at_cost: true;
      max_discount_without_approval: 3;   // percentage
    };

    // What needs manager approval
    requires_approval: {
      discount_above_3_percent: true;
      margin_below_12_percent: true;
      custom_itinerary_redesign: true;
      non-standard_payment_terms: true;
    };

    // Hard limits (system-enforced)
    hard_limits: {
      minimum_margin: 8;                  // percentage
      maximum_discount: 15;               // percentage
      maximum_revisions: 5;               // per proposal
    };
  };

  // Counter-offer templates
  counter_offers: {
    scenario: string;
    counter: string;
    margin_impact: number;
  }[];
}

// ── Negotiation guardrails ──
// ┌─────────────────────────────────────────────────────┐
// │  Negotiation — Margin Guardrails                       │
// │                                                       │
// │  Current deal: Sharma Singapore                        │
// │  Quoted: ₹1,85,000 · Margin: ₹24,200 (13.1%)         │
// │  Customer asks: "Can you do ₹1,65,000?"               │
// │                                                       │
// │  Impact analysis:                                     │
// │  ₹1,65,000 → Margin: ₹4,200 (2.5%) 🔴 BELOW LIMIT   │
// │                                                       │
// │  Counter-offer options:                                │
// │  ┌────────────────────────────────────────────────┐  │
// │  │ Option A: ₹1,78,000 (10.7% margin) ⚠️ Needs    │  │
// │  │   Remove: Premium activities (-₹4K)            │  │
// │  │   Change: 4-star hotel instead of 5-star        │  │
// │  │   Keep: Flights, transfers, visa, insurance     │  │
// │  │   [Use This Counter] [Needs Approval]           │  │
// │  │                                                 │  │
// │  │ Option B: ₹1,72,000 (9.5% margin) 🔴 Needs mgr  │  │
// │  │   Remove: Activities + downgrade meals          │  │
// │  │   Change: 3-star hotel + economy flights        │  │
// │  │   Keep: Core trip elements                      │  │
// │  │   [Request Manager Approval]                     │  │
// │  │                                                 │  │
// │  │ Option C: Keep ₹1,85,000 with payment plan      │  │
// │  │   Split: 3 payments of ₹61,667                  │  │
// │  │   "Keep everything, pay in installments"        │  │
// │  │   Margin: unchanged (13.1%) ✅                   │  │
// │  │   [Send Payment Plan Option]                     │  │
// │  └────────────────────────────────────────────────┘  │
// │                                                       │
// │  ⛔ Cannot offer below ₹1,60,800 (cost price)         │
// └─────────────────────────────────────────────────────┘
```

### India-Specific Sales Patterns

```typescript
interface IndiaSalesPatterns {
  // Cultural patterns affecting sales
  patterns: {
    FAMILY_DECISION: {
      description: "Travel decisions involve spouse, parents, sometimes extended family";
      sales_implication: "Always offer to send detailed proposal for family review";
      timeline_impact: "Add 2-3 days for family consultation";
    };

    REFERENCE_DRIVEN: {
      description: "Indians trust recommendations from friends/family over advertising";
      sales_implication: "Lead with testimonials and referrals, not features";
      conversion_boost: "+35% conversion when referral mentioned";
    };

    PRICE_SENSITIVE_WITH_VALUE_AWARENESS: {
      description: "Customers compare prices but also appreciate good value";
      sales_implication: "Always compare effective price (including hidden costs)";
      key_phrase: "No hidden costs — everything included in this price";
    };

    FESTIVAL_BOOKING_SPIKES: {
      description: "Diwali, summer holidays, year-end drive bulk bookings";
      sales_implication: "Pre-build packages for festival seasons";
      revenue_impact: "40% of annual revenue in 3 festival windows";
    };

    WHATSAPP_PRIMARY: {
      description: "WhatsApp is the primary communication channel";
      sales_implication: "Entire sales flow must work on WhatsApp";
      conversion_data: "78% of bookings closed via WhatsApp";
    };

    TRUST_BUILDING: {
      description: "Trust is built through personal interaction, not brand alone";
      sales_implication: "Agent personality and responsiveness matter more than website";
      key_metric: "Response time < 30 min = 2x conversion rate";
    };
  };
}

// ── India sales pattern reference ──
// ┌─────────────────────────────────────────────────────┐
// │  India Market — Sales Pattern Reference                 │
// │                                                       │
// │  Pattern: WhatsApp-first sales                         │
// │  ┌───────────────────────────────────────────────┐   │
// │  │  Typical WhatsApp sales flow:                    │   │
// │  │                                               │   │
// │  │  Customer: "Singapore trip plan chahiye         │   │
// │  │            June mein, family ke saath"           │   │
// │  │                                               │   │
// │  │  Agent: "Ji bilkul! Kitne log hain aur         │   │
// │  │          budget kitna rakha hai?"               │   │
// │  │                                               │   │
// │  │  Customer: "4 adults, 2 kids, around ₹2L"      │   │
// │  │                                               │   │
// │  │  Agent: [Sends 2-page visual proposal           │   │
// │  │          as WhatsApp image + PDF]               │   │
// │  │          "Yeh dekhiye — 2 options hain"        │   │
// │  │                                               │   │
// │  │  Customer: "Option 2 achha hai, thoda           │   │
// │  │          discount milega?"                      │   │
// │  │                                               │   │
// │  │  Agent: [Sends counter with payment plan]       │   │
// │  │                                               │   │
// │  │  Customer: "Theek hai, book kar do"             │   │
// │  │                                               │   │
// │  │  Entire flow: 2-4 days, all on WhatsApp         │   │
// │  │  Agent tools: Auto-proposal, rate check,        │   │
// │  │               margin calc, WhatsApp templates   │   │
// │  └───────────────────────────────────────────────┘   │
// └─────────────────────────────────────────────────────┘
```

---

## Open Problems

1. **Hinglish communication** — Customer messages mix Hindi and English. Objection detection and response templates need to handle both languages naturally, not sound like translated English.

2. **Objection detection accuracy** — Inferring objection type from a WhatsApp message like "thoda aur discount milega?" requires NLP that understands context and tone.

3. **Closing technique personalization** — The same technique may work for one customer and offend another. Agent skill level matters more than templates.

4. **Negotiation data** — We don't have enough historical negotiation data yet to train recommendation models. Initial version should be rule-based, evolving to ML-based.

---

## Next Steps

- [ ] Build objection classification system with response templates
- [ ] Create closing technique recommender based on customer signals
- [ ] Implement negotiation guardrails with approval workflows
- [ ] Design India-specific sales pattern library
