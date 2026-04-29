# Travel Exposition & Event Marketing — Events & Lead Capture

> Research document for travel expo participation, booth management, event lead capture, post-event follow-up, and event ROI tracking for travel agencies.

---

## Key Questions

1. **Which travel expos and events should agencies participate in?**
2. **How do we capture and qualify leads at events?**
3. **What post-event follow-up converts leads to bookings?**
4. **How do we measure event ROI?**

---

## Research Areas

### Travel Event Calendar

```typescript
interface TravelEventCalendar {
  // Major Indian travel expos and events
  events: {
    TTF_MUMBAI: {
      name: "Travel & Tourism Fair — Mumbai";
      frequency: "Annual (Feb)";
      type: "Consumer + Trade";
      footfall: "25,000+ visitors";
      booth_cost: "₹1.5-3L for 9 sqm";
      audience: "Mumbai/Pune families planning travel";
      lead_potential: "200-400 inquiries per event";
      conversion_rate: "8-12% of inquiries convert to bookings within 90 days";
    };

    OTM_MUMBAI: {
      name: "Outbound Travel Mart — Mumbai";
      frequency: "Annual (Jan)";
      type: "Trade-focused";
      footfall: "15,000+ trade visitors";
      booth_cost: "₹2-4L for 9 sqm";
      audience: "Travel agents, tour operators, destination reps";
      lead_potential: "B2B partnerships, supplier connections";
    };

    SATTE_DELHI: {
      name: "South Asia Travel & Tourism Exchange — Delhi";
      frequency: "Annual (Mar)";
      type: "Trade + Consumer";
      footfall: "30,000+ visitors";
      booth_cost: "₹2-5L";
      audience: "Delhi NCR families, travel trade";
      lead_potential: "300-500 inquiries";
    };

    WEDDING_EXPO: {
      name: "Wedding exhibitions (multiple cities)";
      frequency: "Seasonal (Oct-Feb wedding season)";
      type: "Consumer";
      footfall: "5,000-15,000 per event";
      booth_cost: "₹50K-1.5L";
      audience: "Couples planning weddings — honeymoon leads";
      lead_potential: "50-150 honeymoon inquiries";
      conversion_rate: "15-20% (high intent — already spending on wedding)";
    };

    CORPORATE_FAIR: {
      name: "Corporate offsite/HR fairs";
      frequency: "Quarterly";
      type: "Corporate";
      footfall: "200-500 HR/admin decision makers";
      booth_cost: "₹25K-50K (often free as travel vendor)";
      audience: "Corporate HR planning team outings";
      lead_potential: "10-30 corporate trip inquiries";
      conversion_rate: "25% (bulk bookings, high value)";
    };

    HOUSING_SOCIETY_EVENT: {
      name: "RWA/society cultural events";
      frequency: "Festival/annual events";
      type: "Hyper-local";
      footfall: "200-500 residents";
      booth_cost: "₹5K-10K or free (sponsorship)";
      audience: "Families in the society";
      lead_potential: "5-15 inquiries";
      conversion_rate: "20-30% (trust from neighbor recommendation)";
    };
  };
}

// ── Event calendar ──
// ┌─────────────────────────────────────────────────────┐
// │  Event Calendar — 2026                                    │
// │                                                       │
// │  Upcoming events:                                     │
// │  🗓️ May 15: Sunshine Apartments Annual Day                │
// │     Type: Housing society · Cost: ₹5K · Expected: 10 leads│
// │     Status: Confirmed · Agent: Priya                      │
// │     [Prepare Materials] [Assign Team]                      │
// │                                                       │
// │  🗓️ Jun 8: Delhi Wedding Expo                             │
// │     Type: Consumer · Cost: ₹80K · Expected: 80 leads      │
// │     Status: Booth booked (4 sqm) · Materials needed       │
// │     [Design Standee] [Print Brochures] [Staff Plan]       │
// │                                                       │
// │  🗓️ Sep 20: TTF Mumbai                                    │
// │     Type: Consumer+Trade · Cost: ₹2.5L · Expected: 300 leads│
// │     Status: Early bird pricing until Jun 30               │
// │     [Register] [Plan Booth Design]                         │
// │                                                       │
// │  Past events ROI:                                     │
// │  ✅ Feb TTF Mumbai: 280 leads → 24 bookings · ₹6.8L rev   │
// │     Cost: ₹2.2L · ROI: 3.1x                               │
// │  ✅ Jan Wedding Expo: 65 leads → 11 bookings · ₹3.2L rev  │
// │     Cost: ₹75K · ROI: 4.3x                                │
// │                                                       │
// │  [Add Event] [Event Templates] [Budget Planner]           │
// └─────────────────────────────────────────────────────┐
```

### Event Lead Capture

```typescript
interface EventLeadCapture {
  // Capture and qualify leads at events
  capture: {
    METHODS: {
      QR_CODE_SCANNER: {
        description: "Visitor scans QR code at booth → opens inquiry form on phone";
        form_fields: ["Name", "Phone (required)", "Destination interest", "Budget range", "Travel timeline"];
        advantage: "Visitor enters own data → no typos, no paper";
        conversion_to_inquiry: "60% of scans complete the form";
      };

      AGENT_TABLET: {
        description: "Agent enters visitor details on tablet during conversation";
        form_fields: ["Name", "Phone", "Destination", "Travelers", "Notes from conversation"];
        advantage: "Richer data — agent adds conversation context";
        conversion_to_inquiry: "85% of conversations result in entry";
      };

      LUCKY_DRAW: {
        description: "Business card drop / form fill for lucky draw prize";
        prize: "Free weekend getaway for 2 (worth ₹25K, actual cost ₹8K)";
        advantage: "Captures visitors who wouldn't stop otherwise";
        data_quality: "LOW — many just want the prize, not travel";
        conversion_to_inquiry: "15% of entries are genuine leads";
      };

      INSTANT_QUOTE: {
        description: "Give instant mini-quote at booth for their destination";
        mechanism: "Agent selects destination template → enters dates → shows ballpark price on tablet";
        advantage: "Demonstrates value immediately, high engagement";
        conversion_to_inquiry: "40% want detailed follow-up quote";
      };
    };

    // Lead qualification at event
    qualification: {
      HOT: "Wants to travel in next 3 months + has budget + knows destination";
      WARM: "Planning to travel in 3-6 months + exploring options";
      COLD: "No immediate plans + just browsing + entered for lucky draw";
      NOT_QUALIFIED: "Student doing research + competition + not in target segment";
    };
  };
}

// ── Event lead capture ──
// ┌─────────────────────────────────────────────────────┐
// │  Lead Capture — Delhi Wedding Expo · Live                 │
// │  Day 1 of 2 · Leads captured: 45 · Hot: 12 · Warm: 22   │
// │                                                       │
// │  Recent captures:                                     │
// │  🔥 HOT — Mehta couple · Honeymoon · Bali/Others · Jun  │
// │     Budget: ₹1.5-2L · Source: Agent conversation        │
// │     → Auto-send Bali honeymoon guide + WhatsApp link     │
// │     [Assign Agent] [Send Material]                        │
// │                                                       │
// │  🟡 WARM — Gupta family · Europe · Oct-Nov               │
// │     Budget: ₹5-7L · Source: QR scan                      │
// │     → Add to Europe nurture sequence                     │
// │     [Add to Sequence]                                     │
// │                                                       │
// │  Capture method breakdown:                            │
// │  Agent tablet:  22 (49%) · Rich data, warm leads         │
// │  QR code:      15 (33%) · Good data, mixed quality        │
// │  Lucky draw:    8 (18%) · Low quality, follow-up needed   │
// │                                                       │
// │  [Real-time Dashboard] [Export Leads] [Staff Schedule]    │
// └─────────────────────────────────────────────────────┘
```

### Post-Event Follow-Up & Conversion

```typescript
interface PostEventFollowUp {
  // Convert event leads to bookings
  follow_up_sequence: {
    DAY_0: {
      trigger: "Same evening after event";
      action: "WhatsApp message: 'Great meeting you at {event}! Here's the {destination} info we discussed'";
      hot_leads: "Personal call from assigned agent within 2 hours";
    };

    DAY_1: {
      trigger: "Next morning";
      action: "Send personalized destination guide via WhatsApp based on their interest";
      include: "Package pricing + testimonial from similar customer";
    };

    DAY_3: {
      trigger: "3 days after event";
      action: "Agent follow-up call: 'Did you get a chance to look at the guide? Any questions?'";
      goal: "Move from casual interest to active discussion";
    };

    DAY_7: {
      trigger: "1 week after event";
      action: "If no response: 'Prices for {destination} are trending up — shall I lock current rates for you?'";
      urgency: "Create gentle FOMO based on real pricing data";
    };

    DAY_14: {
      trigger: "2 weeks after event";
      action: "If still no response: move to monthly newsletter (don't over-contact)";
    };
  };

  // Event ROI tracking
  roi_tracking: {
    costs: {
      booth_rental: number;
      materials: number;                    // standee, brochures, tablets
      travel_staff: number;                 // travel + accommodation for team
      lucky_draw_prize: number;
      total: number;
    };

    returns: {
      leads_captured: number;
      inquiries_converted: number;           // lead became active inquiry
      proposals_sent: number;
      bookings_confirmed: number;
      revenue_generated: number;
    };

    roi_formula: "(Revenue from event bookings - Total event cost) / Total event cost";
    good_roi: "3x+ for consumer events, 5x+ for corporate/wedding events";
    tracking_window: "90 days post-event (most bookings happen within 90 days)";
  };
}

// ── Event ROI tracker ──
// ┌─────────────────────────────────────────────────────┐
// │  Event ROI — TTF Mumbai Feb 2026                          │
// │                                                       │
// │  Costs:                                               │
// │  Booth: ₹1.8L · Materials: ₹25K · Staff: ₹15K            │
// │  Lucky draw: ₹8K · Total: ₹2.28L                         │
// │                                                       │
// │  Returns (90-day window):                              │
// │  Leads: 280 → Inquiries: 85 → Proposals: 42              │
// │  → Bookings: 24 · Revenue: ₹6.84L                        │
// │                                                       │
// │  ROI: (6.84L - 2.28L) / 2.28L = 2.0x                    │
// │  Cost per booking: ₹9,500                                │
// │  Avg booking value: ₹28,500                              │
// │                                                       │
// │  ROI by lead source:                                  │
// │  Agent conversation: 35% conversion · 3.8x ROI            │
// │  QR code scan:       22% conversion · 2.4x ROI            │
// │  Lucky draw:          5% conversion · 0.5x ROI             │
// │                                                       │
// │  Lesson: Invest in more agent conversations,              │
// │  fewer lucky draws. Quality over quantity.                │
// │                                                       │
// │  [Full Report] [Compare Events] [Plan Next Event]         │
// └─────────────────────────────────────────────────────┘
```

---

## Open Problems

1. **Lead quality vs. quantity** — Events generate lots of leads but many are low-quality (browsers, students, competitors). Need instant qualification at capture point to prioritize follow-up.

2. **Event fatigue** — Same visitors at every expo. Need fresh angles each time (new destinations, exclusive offers) rather than repeating the same pitch.

3. **Long attribution window** — Event leads may book 3-6 months later after seeing the agency elsewhere. Hard to attribute to the event alone. Need multi-touch tracking.

4. **Staff cost** — Pulling agents off sales for 2 days to staff a booth has opportunity cost. Need to calculate that into event ROI.

---

## Next Steps

- [ ] Build event calendar with Indian travel expo schedule
- [ ] Create event lead capture system with QR code and tablet entry
- [ ] Implement post-event follow-up sequences with qualification-based paths
- [ ] Design event ROI tracker with 90-day attribution window
