# Agency Sales Playbook — Automation & WhatsApp Sales

> Research document for automated sales workflows, WhatsApp-native sales flows, proposal generation automation, and follow-up sequencing for travel agencies.

---

## Key Questions

1. **What sales activities can be automated without losing the personal touch?**
2. **How does the entire sales flow work on WhatsApp?**
3. **How do we auto-generate and send proposals?**
4. **What follow-up sequences maximize conversion?**

---

## Research Areas

### Automated Sales Workflows

```typescript
interface SalesAutomation {
  // Trigger-based automation rules
  automations: {
    // New inquiry response
    NEW_INQUIRY: {
      trigger: "New WhatsApp message or inquiry form";
      actions: [
        "Categorize inquiry (destination, segment, urgency)",
        "Create CRM entry or update existing",
        "Assign to available agent (round-robin or skill-based)",
        "Send acknowledgment within 2 minutes",
        "Pull customer history if existing",
        "Check rate intelligence for requested destination",
      ];
      agent_notification: "New inquiry from {name}: {summary}";
    };

    // Proposal follow-up sequence
    PROPOSAL_FOLLOW_UP: {
      trigger: "Proposal sent, no response after X hours";
      sequence: [
        {
          delay_hours: 24;
          message: "Hi {name}, did you get a chance to review the {destination} proposal?";
          channel: "WHATSAPP";
        },
        {
          delay_hours: 48;
          message: "I noticed you haven't responded — would you like me to adjust anything? Happy to create a modified version.";
          channel: "WHATSAPP";
        },
        {
          delay_hours: 96;
          message: "Last check-in — the rates I quoted are still available but may change. Let me know if you'd like to proceed!";
          channel: "WHATSAPP";
        },
        {
          delay_hours: 168;
          action: "Mark as STALE · Schedule win-back touchpoint for 30 days";
          channel: "SYSTEM";
        },
      ];
    };

    // Rate change alert for active proposals
    RATE_CHANGE_PROPOSAL: {
      trigger: "Rate drop detected for destination in active proposal";
      actions: [
        "Calculate savings if rebooked at new rate",
        "Send proactive WhatsApp: 'Great news! Prices just dropped...'",
        "Update proposal with new rate",
        "Create urgency: 'This rate may not last'",
      ];
    };

    // Booking confirmation sequence
    BOOKING_CONFIRMED: {
      trigger: "Payment received and booking confirmed";
      sequence: [
        {
          delay_hours: 0;
          action: "Send booking confirmation with itinerary PDF";
          channel: "WHATSAPP";
        },
        {
          delay_hours: 1;
          action: "Send payment receipt";
          channel: "WHATSAPP";
        },
        {
          delay_hours: 24;
          action: "Send pre-trip checklist (visa, packing, weather)";
          channel: "WHATSAPP";
        },
      ];
    };
  };
}

// ── Automation dashboard ──
// ┌─────────────────────────────────────────────────────┐
// │  Sales Automation — Active Workflows                    │
// │                                                       │
// │  Running automations: 23                               │
// │                                                       │
// │  ┌───────────────────────────────────────────────┐   │
// │  │ 📨 Proposal Follow-ups (8 active)              │   │
// │  │                                               │   │
// │  │ Sharma SG:    Sent 24h ago → Follow-up today  │   │
// │  │ Patel Dubai:  Sent 2d ago → 2nd follow-up due │   │
// │  │ Mehta Goa:    Sent 4d ago → Final check-in    │   │
// │  │ [View All] [Pause] [Edit Sequence]             │   │
// │  └───────────────────────────────────────────────┘   │
// │                                                       │
// │  ┌───────────────────────────────────────────────┐   │
// │  │ 🔔 Rate Alerts Triggered (3 this week)         │   │
// │  │                                               │   │
// │  │ Taj Vivanta SGP: -15% → Alerted 2 customers  │   │
// │  │ IndiGo DEL-SIN: -10% → Alerted 3 customers   │   │
// │  │ Sentosa entry: +5% → Flagged 1 proposal       │   │
// │  │ [View All Alerts] [Configure Triggers]         │   │
// │  └───────────────────────────────────────────────┘   │
// │                                                       │
// │  ┌───────────────────────────────────────────────┐   │
// │  │ ✅ Automations Completed (12 this week)        │   │
// │  │                                               │   │
// │  │ 8 follow-up sequences completed                │   │
// │  │ 3 booking confirmations sent                   │   │
// │  │ 1 stale deal auto-categorized                  │   │
// │  └───────────────────────────────────────────────┘   │
// │                                                       │
// │  [Create Automation] [Templates] [Analytics]          │
// └─────────────────────────────────────────────────────┘
```

### WhatsApp-Native Sales Flow

```typescript
interface WhatsAppSalesFlow {
  // Complete sales conversation on WhatsApp
  conversation_stages: {
    STAGE_1_INQUIRY: {
      customer_message: string;           // "Singapore trip chahiye June mein"
      ai_categorization: {
        destination: string;
        month: string;
        language: "HINDI" | "ENGLISH" | "HINGLISH";
        intent: "STRONG" | "EXPLORING" | "TIRE_KICKING";
      };
      agent_assist: {
        suggested_response: string;
        customer_history: string | null;
        quick_replies: string[];
      };
    };

    STAGE_2_QUALIFY: {
      agent_messages: string[];           // qualification questions
      customer_responses: {
        budget_range: string | null;
        travelers: string | null;
        dates: string | null;
        purpose: string | null;
      };
      auto_actions: ["Create draft in workbench", "Check rates for dates"];
    };

    STAGE_3_PROPOSE: {
      auto_generated: {
        proposal_image: string;           // visual proposal as WhatsApp image
        proposal_pdf: string;             // detailed PDF
        summary_text: string;             // 3-line WhatsApp summary
      };
      agent_customization: string;        // personal note from agent
    };

    STAGE_4_CLOSE: {
      payment_link: string;               // WhatsApp payment link
      booking_confirmation: string;       // auto-sent on payment
    };
  };
}

// ── WhatsApp sales flow mockup ──
// ┌─────────────────────────────────────────────────────┐
// │  WhatsApp Sales Flow — Sharma Singapore                 │
// │                                                       │
// │  [Customer → Agent]                                    │
// │  ┌───────────────────────────────────────────────┐   │
// │  │ "Singapore trip plan chahiye June mein,        │   │
// │  │  family ke saath. 4 adults, 2 kids."           │   │
// │  └───────────────────────────────────────────────┘   │
// │                                                       │
// │  [AI Assist: Singapore · June · 6 pax · Family]       │
// │  [Suggested: "Ji bilkul! Budget kitna..."]            │
// │                                                       │
// │  [Agent → Customer]                                    │
// │  ┌───────────────────────────────────────────────┐   │
// │  │ "Ji bilkul, Sharma ji! Singapore is beautiful   │   │
// │  │  in June. Kitna budget rakha hai aur dates      │   │
// │  │  fix hain ya flexible?"                         │   │
// │  └───────────────────────────────────────────────┘   │
// │                                                       │
// │  [Customer → Agent]                                    │
// │  "Around ₹2 lakh, June 1-6"                           │
// │                                                       │
// │  [Auto: Draft created · Rates checked · 2 options]    │
// │                                                       │
// │  [Agent → Customer]                                    │
// │  ┌───────────────────────────────────────────────┐   │
// │  │ [Image: Visual proposal — Singapore 5N]        │   │
// │  │                                               │   │
// │  │ "2 options bhej rahi hoon:                     │   │
// │  │                                               │   │
// │  │  Option 1 (₹1.85L): 4-star, all meals,        │   │
// │  │  Universal Studios, Gardens by the Bay         │   │
// │  │                                               │   │
// │  │  Option 2 (₹1.55L): 3-star, breakfast,         │   │
// │  │  same activities, shared transfers             │   │
// │  │                                               │   │
// │  │  [PDF attached] Kya family ko dikhana hai?"    │   │
// │  └───────────────────────────────────────────────┘   │
// │                                                       │
// │  [Customer → Agent]                                    │
// │  "Option 1 achhi hai, family ne bhi dekh liya.        │
// │  Book kar do."                                        │
// │                                                       │
// │  [Agent → Customer]                                    │
// │  ┌───────────────────────────────────────────────┐   │
// │  │ "Great choice! Payment link bhej rahi hoon:    │   │
// │  │  [Payment Link: ₹50,000 advance]               │   │
// │  │                                               │   │
// │  │  Balance before May 15. Confirm hote hi         │   │
// │  │  itinerary share karungi! 🎉"                   │   │
// │  └───────────────────────────────────────────────┘   │
// │                                                       │
// │  Total flow time: 2 days 4 hours                      │
// │  Agent active time: ~45 minutes                       │
// │  Automation handled: Inquiry categorization,          │
// │  rate checking, proposal generation, payment link     │
// └─────────────────────────────────────────────────────┘
```

### Auto-Proposal Generation

```typescript
interface AutoProposalGenerator {
  // Generate visual proposal from workbench data
  generate(params: {
    trip_id: string;
    variant: "GOOD" | "BETTER" | "BEST";
    format: "WHATSAPP_IMAGE" | "PDF" | "BOTH";
    language: "ENGLISH" | "HINDI" | "HINGLISH";
  }): ProposalOutput;
}

interface ProposalOutput {
  // Visual proposal (WhatsApp-optimized)
  whatsapp_image: {
    url: string;
    dimensions: "1080x1920";             // story format
    pages: number;                       // 2-3 scrollable images
  };

  // PDF proposal (detailed)
  pdf: {
    url: string;
    pages: number;
    sections: ["Cover", "Itinerary", "Hotels", "Inclusions", "Pricing", "T&C"];
  };

  // WhatsApp summary text
  summary_text: string;
}

// ── Auto-proposal generation ──
// ┌─────────────────────────────────────────────────────┐
// │  Proposal Generator — Auto-Create                       │
// │                                                       │
// │  From: Workbench draft for Sharma Singapore            │
// │  Generating: 2 variants (Better + Best)                │
// │  Format: WhatsApp Image + PDF                          │
// │                                                       │
// │  ┌─ Variant 1: "Better" (₹1.85L) ──────────────────┐ │
// │  │  [Preview: Singapore 5N Family Package]           │ │
// │  │  ✅ 4-star hotel (Taj Vivanta)                    │ │
// │  │  ✅ All meals included                             │ │
// │  │  ✅ Universal Studios + Gardens by the Bay         │ │
// │  │  ✅ Private transfers                              │ │
// │  │  ✅ Travel insurance                               │ │
// │  │  📄 PDF: 6 pages · 📱 Image: 3 slides             │ │
// │  └───────────────────────────────────────────────────┘ │
// │                                                       │
// │  ┌─ Variant 2: "Best" (₹2.2L) ─────────────────────┐ │
// │  │  [Preview: Singapore 5N Premium Package]          │ │
// │  │  ✅ 5-star hotel (Marina Bay Sands)               │ │
// │  │  ✅ All meals + 2 fine dining experiences          │ │
// │  │  ✅ All activities + Night Safari VIP               │ │
// │  │  ✅ Private luxury transfers                       │ │
// │  │  ✅ Premium insurance + lounge access               │ │
// │  │  📄 PDF: 6 pages · 📱 Image: 3 slides             │ │
// │  └───────────────────────────────────────────────────┘ │
// │                                                       │
// │  WhatsApp text: "Ji Sharma ji, 2 options..."           │
// │  [Edit Text] [Send via WhatsApp] [Download PDFs]       │
// └─────────────────────────────────────────────────────┘
```

### Follow-Up Sequence Engine

```typescript
interface FollowUpSequence {
  sequence_id: string;
  trigger: string;
  steps: {
    step_number: number;
    delay_from_trigger: string;
    condition: string | null;            // only send if condition met
    channel: "WHATSAPP" | "EMAIL" | "CALL_REMINDER";
    content_type: "TEMPLATE" | "PERSONALIZED" | "AI_GENERATED";
    content: string;
    stop_condition: string | null;       // stop sequence if this happens
  }[];
}

// ── Follow-up sequence library ──
// ┌─────────────────────────────────────────────────────┐
// │  Follow-Up Sequences — Library                          │
// │                                                       │
// │  📋 Proposal Sent (default):                           │
// │  Step 1: +24h · WhatsApp · "Did you review?"          │
// │  Step 2: +48h · WhatsApp · "Happy to adjust"          │
// │  Step 3: +96h · WhatsApp · "Rates may change"         │
// │  Step 4: +168h · System · Mark stale                  │
// │  [Edit] [Duplicate] [Usage: 45 times, 28% response]   │
// │                                                       │
// │  📋 Price Sensitive Customer:                          │
// │  Step 1: +12h · WhatsApp · Value comparison            │
// │  Step 2: +36h · WhatsApp · "No hidden costs"          │
// │  Step 3: +72h · WhatsApp · Payment plan option         │
// │  [Edit] [Duplicate] [Usage: 18 times, 44% response]   │
// │                                                       │
// │  📋 Festival Season Urgency:                           │
// │  Step 1: +6h · WhatsApp · Availability alert          │
// │  Step 2: +24h · WhatsApp · Rate hold expiring          │
// │  Step 3: +48h · WhatsApp · Final chance                │
// │  [Edit] [Duplicate] [Usage: 8 times, 62% response]    │
// │                                                       │
// │  📋 Post-Trip Nurture:                                 │
// │  Step 1: +1 day · WhatsApp · "Welcome back!"          │
// │  Step 2: +7 days · WhatsApp · Memory book ready        │
// │  Step 3: +30 days · WhatsApp · Review request          │
// │  Step 4: +90 days · WhatsApp · Next trip suggestion    │
// │  [Edit] [Duplicate] [Usage: 32 times, 78% response]   │
// │                                                       │
// │  [+ Create Sequence] [Import] [Analytics]              │
// └─────────────────────────────────────────────────────┘
```

---

## Open Problems

1. **WhatsApp template approvals** — WhatsApp Business API requires pre-approved message templates. Sales messages may need frequent updates that are slow to approve.

2. **Automation vs. personal touch** — Over-automation can make the agency feel impersonal. Key moments (first response, proposal, negotiation) should remain human-driven.

3. **Proposal generation quality** — Auto-generated proposals must look professional. Poorly formatted WhatsApp images can damage agency credibility.

4. **Sequence fatigue** — Too many follow-ups can annoy customers. Need frequency caps and engagement-based throttling (stop if customer says "not interested").

---

## Next Steps

- [ ] Build trigger-based sales automation engine
- [ ] Create WhatsApp-native sales flow with agent assist
- [ ] Implement auto-proposal generator with visual output
- [ ] Design follow-up sequence engine with response tracking
