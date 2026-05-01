# Visa & Documentation 05: Visa on Arrival (VOA) & e-VOA for Indian Passport Holders

> Research document for Visa on Arrival and electronic Visa on Arrival facilities available to Indian passport holders, destination countries, process workflows, eligibility criteria, and platform integration for VOA trip planning.

---

## Key Questions

1. **Which countries offer Visa on Arrival to Indian passport holders?**
2. **What is the VOA process at each destination?**
3. **How do e-VOA (electronic VOA) systems work?**
4. **What documents must travelers carry for VOA?**
5. **How should the platform handle VOA trips vs pre-approved visa trips?**

---

## Research Areas

### VOA Countries for Indian Passport Holders

```typescript
interface VOACountries {
  // Countries offering Visa on Arrival to Indian citizens (2026):
  // Note: Entry requirements change frequently — always verify before booking

  asia: [
    {
      country: "Thailand",
      type: "VOA + e-VOA",
      cost: "THB 2,000 (≈₹4,600)",
      duration: "15 days (VOA) / 60 days (e-VOA)",
      extension: "Yes, 30 days at immigration office",
      process: {
        voa: "Queue at airport counter → Fill form → Pay fee → Stamp in passport",
        e_voa: "Apply online before travel → Approval email → Express lane at airport"
      },
      documents: ["Passport (6+ months validity)", "Return ticket", "Hotel booking", "1 photo"],
      popular_with: ["Gujarati families", "honeymooners", "budget travelers"],
      advisory: "VOA queues at BKK can be 1-2 hours. e-VOA recommended."
    },
    {
      country: "Maldives",
      type: "Free VOA",
      cost: "Free (30 days)",
      duration: "30 days (free) / 60 days (extended, USD 50)",
      extension: "Yes, up to 90 days total",
      process: "Automatic at arrival — no application needed",
      documents: ["Passport (6+ months)", "Return ticket", "Hotel booking confirmation"],
      popular_with: ["honeymooners", "luxury travelers", "divers"],
      advisory: "Most accessible international destination for Indians"
    },
    {
      country: "Indonesia (Bali)",
      type: "VOA",
      cost: "IDR 500,000 (≈₹2,600)",
      duration: "30 days",
      extension: "Yes, 30 more days at immigration office",
      process: "Counter at airport or e-VOA online",
      documents: ["Passport (6+ months)", "Return ticket", "sufficient funds"],
      popular_with: ["honeymooners", "backpackers", "digital nomads"],
      advisory: "Bali is #1 Indian honeymoon destination post-2024"
    },
    {
      country: "Sri Lanka",
      type: "e-VOA (ETA)",
      cost: "USD 50 (tourist) / USD 35 (SAARC)",
      duration: "30 days (double entry)",
      extension: "Yes, up to 90 days",
      process: "Apply online at eta.gov.lk → Approval in 24h",
      documents: ["Passport", "Return ticket", "Hotel booking"],
      popular_with: ["temple tourism", "beach holidays", "Ayurveda"],
      advisory: "SAARC rate (USD 35) available for Indian passport holders"
    },
    {
      country: "Nepal",
      type: "No visa needed (Indian citizens)",
      cost: "Free",
      duration: "Unlimited stay",
      documents: ["Any government ID (passport, voter ID, Aadhaar)"],
      advisory: "No passport required — any valid Indian ID works"
    },
    {
      country: "Bhutan",
      type: "Entry Permit on Arrival",
      cost: "SDF USD 100/night (Sustainable Development Fee)",
      duration: "As per permit",
      documents: ["Passport or Voter ID", "Hotel booking", "SDF payment"],
      advisory: "Indian nationals don't need visa but must pay SDF"
    },
    {
      country: "Cambodia",
      type: "VOA + e-VOA",
      cost: "USD 30",
      duration: "30 days",
      process: "Airport counter or e-visa online",
      popular_with: ["temple tourism (Angkor Wat)", "backpackers"]
    },
    {
      country: "Laos",
      type: "VOA",
      cost: "USD 30-42",
      duration: "30 days",
      process: "Airport counter only"
    },
    {
      country: "Myanmar",
      type: "e-VOA",
      cost: "USD 50",
      duration: "28 days",
      process: "Online only — no VOA at airport"
    }
  ];

  africa: [
    {
      country: "Mauritius",
      type: "Free VOA",
      cost: "Free",
      duration: "60 days",
      documents: ["Passport (6+ months)", "Return ticket", "Hotel booking", "Sufficient funds"],
      popular_with: ["honeymooners", "family vacations"],
      advisory: "Extremely popular Indian honeymoon destination"
    },
    {
      country: "Seychelles",
      type: "Free VOA (Visitor's Permit)",
      cost: "Free",
      duration: "90 days",
      documents: ["Passport", "Return ticket", "Hotel booking", "Sufficient funds"],
      popular_with: ["luxury honeymooners"]
    },
    {
      country: "Kenya",
      type: "e-VOA (eTA)",
      cost: "USD 51",
      duration: "90 days",
      process: "Apply online at etakenya.go.ke",
      popular_with: ["safari tourism", "adventure travelers"]
    },
    {
      country: "Ethiopia",
      type: "e-VOA",
      cost: "USD 52",
      duration: "30-90 days",
      process: "Apply online or at Bole Airport"
    },
    {
      country: "Tanzania",
      type: "VOA",
      cost: "USD 50",
      duration: "90 days",
      popular_with: ["safari tourism (Serengeti)", "Zanzibar beach"]
    },
    {
      country: "Madagascar",
      type: "VOA",
      cost: "USD 37 (tourist)",
      duration: "90 days"
    }
  ];

  americas: [
    {
      country: "Jamaica",
      type: "Free VOA",
      cost: "Free",
      duration: "30 days (extendable to 6 months)",
      popular_with: ["honeymooners"]
    }
  ];

  oceania: [
    {
      country: "Fiji",
      type: "VOA",
      cost: "Free (4 months)",
      duration: "120 days",
      popular_with: ["honeymooners", "divers"]
    },
    {
      country: "Vanuatu",
      type: "VOA",
      cost: "Free (30 days)",
      duration: "30 days (extendable)"
    }
  ];
}
```

### VOA Process Workflow

```typescript
interface VOAProcess {
  // Platform workflow for VOA trips:

  // Phase 1: Trip Planning
  planning: {
    step: "destination_selection",
    check: "Is destination VOA-eligible for Indian passport?",
    action: "Show VOA badge on destination card",
    info_shown: ["VOA cost", "Duration", "Documents needed", "Process time"]
  };

  // Phase 2: Booking
  booking: {
    step: "booking_confirmation",
    check: "Does customer have valid passport (6+ months)?",
    action: "Collect passport details, validate expiry",
    generate: "VOA document checklist (per destination)",
    advisory: "Carry printed copies of all documents + return ticket + hotel booking"
  };

  // Phase 3: Pre-Departure
  pre_departure: {
    step: "departure_briefing",
    check: "Has customer prepared VOA documents?",
    action: "Send document checklist via WhatsApp/email",
    tips: [
      "Keep USD cash for VOA fee (many airports don't accept cards)",
      "Carry 2 passport photos (some counters require)",
      "Print hotel booking + return ticket (immigration may ask)",
      "Download offline maps for airport VOA counter location"
    ]
  };

  // Phase 4: At Destination
  arrival: {
    step: "arrival_assistance",
    action: "Send WhatsApp message with VOA counter location",
    fallback: "Emergency contact if denied entry (rare but possible)",
    tracking: "Customer confirms successful entry via app/WhatsApp"
  };
}
```

### e-VOA Integration

```typescript
interface eVOAIntegration {
  // Countries with electronic VOA systems:
  // Thailand (thaievisa.go.th), Sri Lanka (eta.gov.lk), Cambodia (evisa.gov.kh),
  // Kenya (etakenya.go.ke), Myanmar (evisa.moip.gov.mm)

  // Platform can offer concierge service:
  concierge: {
    service: "Apply for e-VOA on behalf of customer",
    input_from_customer: ["Passport scan", "Photo", "Flight booking", "Hotel booking"],
    platform_action: "Submit e-VOA application, monitor status, notify approval",
    fee: "₹500-1,000 service fee per application",
    value_prop: "Customer doesn't need to navigate foreign government websites"
  };

  // Status tracking:
  tracking: {
    states: ["SUBMITTED", "UNDER_REVIEW", "APPROVED", "REJECTED"],
    notifications: "Push + WhatsApp + email for each state change",
    timeline: "24-72 hours for most countries"
  };
}
```

---

## Open Problems

### 1. Requirement Volatility
VOA rules change frequently. Thailand suspended VOA during COVID and reintroduced it with different terms. The platform needs a real-time requirement feed.

### 2. VOA Queue Experience
At popular destinations (Bangkok, Bali), VOA queues can be 1-2 hours. e-VOA is much faster. Platform should actively upsell e-VOA and guide customers to express lanes.

### 3. Indian Immigration at Departure
Some Indian immigration officers question travelers heading to VOA countries without return tickets or sufficient funds. Platform should generate a "VOA travel letter" that customers can show.

---

## Next Steps

- [ ] Build VOA country database with real-time requirement feed
- [ ] Design VOA badge system for destination cards
- [ ] Create e-VOA concierge service flow
- [ ] Generate VOA document checklists per destination
- [ ] Build VOA arrival counter location database for major airports
- [ ] Add VOA cost to trip budget calculator

---

**Created:** 2026-05-01
**Series:** Visa & Documentation (VISA_05)
