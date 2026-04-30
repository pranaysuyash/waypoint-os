# Quote & Proposal Generation — Sales Proposal Engine

> Research document for travel itinerary proposals, quote generation, proposal PDF creation, version management, customer-facing presentation, and sales proposal lifecycle for the Waypoint OS platform.

---

## Key Questions

1. **How do agents create and send professional travel proposals to customers?**
2. **What makes a travel proposal convert from quote to booking?**
3. **How do proposals handle pricing, alternatives, and customization?**
4. **What is the proposal lifecycle from creation to acceptance or rejection?**

---

## Research Areas

### Quote & Proposal Generation System

```typescript
interface QuoteProposalGeneration {
  // The sales proposal — the document that converts interest into booking
  proposal_lifecycle: {
    CREATION: {
      trigger: "Customer inquiry → agent builds itinerary → generates proposal";
      inputs: [
        "Customer requirements (destination, dates, budget, travelers, preferences)",
        "Itinerary details (days, activities, hotels, transport, meals)",
        "Pricing (per-item cost, margin, taxes, total)",
        "Terms and conditions (cancellation, payment schedule, inclusions/exclusions)",
      ];
      time_to_create: "Target: <30 minutes for standard proposal; <2 hours for complex custom";
    };

    PRESENTATION: {
      formats: {
        WHATSAPP_PDF: "Rich PDF sent via WhatsApp (primary format for Indian market)";
        EMAIL: "Branded email with PDF attachment and booking link";
        WEB_LINK: "Interactive web proposal with images, videos, and real-time pricing";
        COMPANION_APP: "In-app proposal view for existing customers";
      };
      content: {
        cover: "Agency branding + customer name + trip title + hero image";
        summary: "Trip overview (destination, dates, travelers, price summary)";
        itinerary: "Day-by-day breakdown with images and descriptions";
        accommodation: "Hotel details with photos, room type, star rating";
        inclusions: "Everything included in the price (clear, itemized)";
        exclusions: "What's NOT included (transparency builds trust)";
        pricing: "Itemized pricing + total + payment schedule + EMI options";
        terms: "Cancellation policy, booking conditions, validity (quote valid for 7 days)";
        cta: "Accept Proposal / Request Changes / Book Now button",
      };
    };

    ITERATION: {
      description: "Customer requests changes → agent modifies → new version";
      version_tracking: "Proposal v1 → v2 → v3... each version saved and comparable";
      change_highlighting: "Show what changed between versions (price difference, hotel change)";
      max_iterations: "Guideline: 3-4 versions before converting or qualifying out";
    };

    OUTCOME: {
      accepted: "Customer accepts → auto-creates booking with payment link";
      modified: "Customer requests changes → agent creates new version";
      rejected: "Customer declines → reason captured for agent learning";
      expired: "Quote validity period ends (7-14 days) → auto-expire with follow-up option";
    };
  };

  // ── Proposal builder — agent view ──
  // ┌─────────────────────────────────────────────────────┐
  // │  📋 Proposal Builder · Gupta Family Singapore Trip        │
  // │                                                       │
  // │  Version: 2 · Created: Dec 10 · Valid until: Dec 17     │
  // │                                                       │
  // │  Trip Summary:                                        │
  // │  Destination: Singapore · Oct 10-16, 2026 (6N/7D)      │
  // │  Travelers: 2 Adults + 1 Child (8 yrs)                  │
  // │  Budget: ₹2-2.5L                                        │
  // │                                                       │
  // │  Pricing:                                             │
  // │  Flights (DEL→SIN, 3 pax): ₹1,12,000                    │
  // │  Hotel (7N, Pan Pacific): ₹68,000                        │
  // │  Activities (Universal, Gardens, Zoo): ₹24,000           │
  // │  Transfers + SIM + Insurance: ₹18,000                    │
  // │  Agency fee: ₹15,000                                     │
  // │  ──────────────────────────                             │
  // │  Total: ₹2,37,000  (₹500 margin under budget)           │
  // │  Per person: ₹79,000                                     │
  // │  EMI available: ₹39,500 × 6 months                       │
  // │                                                       │
  // │  Changes from v1:                                     │
  // │  · Hotel changed: Marina Bay → Pan Pacific (saved ₹18K)  │
  // │  · Added: Night Safari (customer requested)              │
  // │  · Removed: Sentosa Cable Car (budget optimization)      │
  // │                                                       │
  // │  [Generate PDF] [Send via WhatsApp] [Create Web Link]     │
  // │  [Compare with v1] [Request Approval] [Save Draft]        │
  // └─────────────────────────────────────────────────────────┘
}
```

### Proposal Content & Design

```typescript
interface ProposalContentDesign {
  // What makes a proposal convert
  conversion_elements: {
    VISUAL_QUALITY: {
      description: "Professional appearance builds trust and justifies premium pricing";
      requirements: [
        "High-resolution destination and hotel photos (min 1200x800px)",
        "Consistent agency branding (logo, colors, fonts)",
        "Clean layout with ample white space",
        "Mobile-friendly (many customers view on phone)",
        "Map visualization of itinerary route",
      ];
    };

    TRANSPARENCY: {
      description: "Clear pricing and terms prevent post-booking disputes";
      rules: [
        "Itemized pricing — show cost of each component",
        "Explicit inclusions and exclusions — no surprises",
        "Cancellation policy prominently displayed",
        "Payment schedule with dates and amounts",
        "Visa and passport requirements clearly stated",
        "Price validity period (quote valid for X days)",
      ];
    };

    PERSONALIZATION: {
      description: "Show the customer this proposal was built for them specifically";
      elements: [
        "Customer name in greeting and on cover",
        "References to their preferences ('As you mentioned, vegetarian restaurants are included')",
        "Tailored recommendations ('Based on your interest in nature, we added Gardens by the Bay')",
        "Family-specific inclusions ('Child-friendly activities marked with 🧒')",
      ];
    };

    URGENCY: {
      description: "Encourage timely decision without pressure tactics";
      elements: [
        "Quote validity date (honest — prices change, this is real)",
        "Seasonal note ('October is peak season — availability limited')",
        "Early bird incentive if applicable",
        "Flight price note ('Current fare — subject to change until ticketed')",
      ];
    };
  };

  proposal_templates: {
    STANDARD_HOLIDAY: {
      use: "Most common — family or couple holiday package";
      sections: ["Cover", "Trip Summary", "Day-by-Day Itinerary", "Hotels", "Inclusions/Exclusions", "Pricing", "Terms", "Accept CTA"];
      pages: "8-15 pages";
    };

    HONEYMOON_SPECIAL: {
      use: "Romance travel proposals";
      additions: ["Romantic inclusions highlighted", "Couple photo gallery", "Upgrade options", "Love story themed design"];
      pages: "10-18 pages";
    };

    CORPORATE: {
      use: "B2B corporate travel proposals";
      additions: ["Company branding", "MICE-specific terms", "Group pricing breakdown", "Approval workflow", "GST invoice format"];
      pages: "12-20 pages";
    };

    QUICK_QUOTE: {
      use: "Fast WhatsApp-friendly quote for simple trips";
      format: "Rich text message with key details, not full PDF";
      content: "Destination + dates + price + inclusions + book now link";
      creation_time: "<5 minutes";
    };
  };
}
```

### Proposal Analytics

```typescript
interface ProposalAnalytics {
  // Tracking proposal performance to optimize conversion
  tracking_metrics: {
    PROPOSAL_FUNNEL: {
      created: "Total proposals generated in period";
      sent: "Proposals actually sent to customers (some drafted but not sent)";
      viewed: "Proposals opened/viewed by customer (web link tracking)";
      responded: "Customer responded (accepted, modified, rejected)";
      converted: "Customer accepted and paid advance";
    };

    AGENT_PERFORMANCE: {
      proposals_per_agent: "Volume of proposals created per agent";
      conversion_rate: "Accepted / Sent per agent (target: 40%+)";
      avg_time_to_create: "Minutes from inquiry to proposal sent";
      avg_versions: "Average versions before conversion (lower = better matching)";
      avg_deal_value: "Average accepted proposal value per agent",
    };

    LEARNING_ENGINE: {
      rejection_reasons: "Track why proposals are rejected (price, itinerary, hotel, competitor)";
      common_modifications: "What customers most often change (hotel, dates, activities)";
      price_sensitivity: "At what price point do customers accept vs. negotiate";
      competitor_mentions: "When customers cite competitor pricing — track for market intelligence",
    };
  };
}
```

---

## Open Problems

1. **Proposal quality vs. speed** — A beautiful 15-page proposal takes 2 hours to create. A quick quote takes 5 minutes. Balancing quality with response speed is a constant tension, especially when customers are comparing multiple agencies.

2. **Price volatility** — Flight prices change by the hour. A proposal with flight pricing valid for 7 days may have stale pricing by day 3. Dynamic pricing integration or clear disclaimers needed.

3. **Proposal leakage** — Customers sometimes use the agency's detailed proposal to book directly with suppliers or a cheaper competitor. How much detail to reveal vs. what to hold back until booking is a strategic decision.

4. **Version confusion** — After 3-4 iterations, customers may confuse versions ("But v2 had the better hotel!"). Clear version tracking and change summaries are essential.

5. **Multi-agent collaboration** — Complex proposals (corporate events, large groups) may involve multiple agents contributing different sections. Collaborative proposal editing is needed.

---

## Next Steps

- [ ] Build proposal builder with drag-and-drop itinerary and pricing assembly
- [ ] Create branded proposal templates (standard, honeymoon, corporate, quick quote)
- [ ] Implement PDF generation with professional design and agency branding
- [ ] Build proposal version tracking with change highlighting between versions
- [ ] Create WhatsApp-first proposal delivery with tracking and accept button
- [ ] Implement proposal analytics dashboard with conversion funnel tracking
- [ ] Build quick quote generation for fast WhatsApp-friendly pricing
- [ ] Design proposal-to-booking auto-conversion on customer acceptance
