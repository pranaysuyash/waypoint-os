# Travel Risk Assessment — Destination Risk Scoring

> Research document for pre-trip destination risk assessment, safety scoring, health risk evaluation, political stability monitoring, natural disaster exposure, and comprehensive travel risk intelligence for the Waypoint OS platform.

---

## Key Questions

1. **How do we assess and score destination risk before and during trips?**
2. **What risk dimensions matter for travel safety?**
3. **How does risk assessment integrate with booking and trip planning?**
4. **When should risk assessment trigger trip modifications or cancellations?**

---

## Research Areas

### Travel Risk Assessment System

```typescript
interface TravelRiskAssessment {
  // Pre-trip and during-trip destination risk evaluation
  risk_dimensions: {
    SAFETY_AND_SECURITY: {
      weight: 30%;
      factors: {
        crime_rate: "Violent crime, petty theft, tourist-targeted scams";
        terrorism_risk: "Recent incidents, government travel advisories, high-risk zones";
        political_stability: "Civil unrest, protests, government instability, elections";
        personal_safety: "Harassment, women's safety, LGBTQ+ safety, racial discrimination risk";
      };
      data_sources: [
        "Indian MEA travel advisories (primary)",
        "US State Department travel advisories",
        "UK FCDO travel advice",
        "Australia DFAT travel advice",
        "Global Peace Index",
        "OSAC (Overseas Security Advisory Council) reports",
      ];
    };

    HEALTH_AND_MEDICAL: {
      weight: 25%;
      factors: {
        disease_risk: "Malaria, dengue, Zika, COVID, yellow fever endemic areas";
        air_quality: "AQI levels (critical for Indian travelers with respiratory conditions)";
        food_and_water: "Water safety, food hygiene standards, street food risk";
        healthcare_quality: "Hospital quality, English-speaking doctors, emergency response time";
        vaccination_required: "Mandatory vaccinations for entry (yellow fever, etc.)";
        medical_evacuation: "Feasibility and cost of emergency medical evacuation";
      };
      data_sources: [
        "WHO travel health advisories",
        "CDC travel health notices",
        "Indian Ministry of Health advisories",
        "IAMAT (International Association for Medical Assistance to Travellers)",
      ];
    };

    NATURAL_DISASTER: {
      weight: 20%;
      factors: {
        seismic_risk: "Earthquake zones, tsunami risk for coastal destinations";
        weather_extremes: "Hurricane/typhoon season, monsoon severity, extreme heat/cold";
        volcanic_activity: "Active volcanoes near destination";
        flooding: "Flood-prone areas, seasonal flooding patterns";
        wildfire: "Wildfire risk during dry seasons",
      };
      data_sources: [
        "NDMA (National Disaster Management Authority) for domestic",
        "Global Disaster Alert and Coordination System (GDACS)",
        "Historical weather and disaster data",
        "Seasonal weather patterns by destination",
      ];
    };

    TRANSPORT_INFRASTRUCTURE: {
      weight: 15%;
      factors: {
        road_safety: "Road quality, traffic fatality rate, driving standards";
        aviation_safety: "Airline safety ratings, airport security standards";
        maritime_safety: "Ferry safety records, boat tour regulations";
        public_transport: "Metro safety, taxi reliability, rideshare availability",
      };
    };

    REGULATORY_AND_LEGAL: {
      weight: 10%;
      factors: {
        entry_requirements: "Visa on arrival availability, entry restrictions, customs regulations";
        legal_risks: "Strict drug laws, alcohol restrictions, dress code requirements";
        consular_access: "Indian embassy/consulate presence at destination";
        currency_restrictions: "Cash limits, forex restrictions, payment infrastructure",
      };
    };
  };

  // ── Risk assessment — agent view ──
  // ┌─────────────────────────────────────────────────────┐
  // │  🛡️ Risk Assessment · Bangkok · Dec 15-22, 2026            │
  // │                                                       │
  // │  Overall Risk Score: 72/100 (MODERATE)                │
  // │  ████████████████░░░░░░░░                               │
  // │                                                       │
  // │  Dimension Scores:                                    │
  // │  🔒 Safety:        78/100 · LOW RISK                     │
  // │  🏥 Health:        70/100 · MODERATE                     │
  // │  🌊 Natural:       85/100 · LOW RISK (no typhoon season) │
  // │  🚗 Transport:     55/100 · ELEVATED (road safety)       │
  // │  ⚖️ Regulatory:    80/100 · LOW RISK                      │
  // │                                                       │
  // │  ⚠️ Specific Alerts:                                      │
  // │  · Air quality: AQI 135 (unhealthy for sensitive)     │
  // │    → Advise: Carry N95 mask, limit outdoor morning     │
  // │  · Transport: Taxi scams near Grand Palace              │
  // │    → Advise: Use Grab app, avoid street taxis           │
  // │  · Health: Dengue cases elevated this month             │
  // │    → Advise: Mosquito repellent, long sleeves evening   │
  // │                                                       │
  // │  Recommendations:                                     │
  // │  · Add travel insurance (recommended): ₹3,200           │
  // │  · Include mosquito repellent in packing list            │
  // │  · Share safety briefing with customer                   │
  // │                                                       │
  // │  [Generate Safety Briefing] [Send to Customer]           │
  // │  [Add Insurance] [Override Assessment]                    │
  // └─────────────────────────────────────────────────────────┘
}
```

### Risk-Based Decision Framework

```typescript
interface RiskDecisionFramework {
  // How risk scores drive booking and trip decisions
  risk_levels: {
    LOW_RISK: {
      score: "80-100";
      color: "GREEN";
      action: "Proceed with booking — standard safety briefing";
      customer_communication: "Optional safety info card in trip documents";
    };

    MODERATE_RISK: {
      score: "60-79";
      color: "YELLOW";
      action: "Proceed with enhanced safety briefing";
      customer_communication: "Mandatory safety briefing document with specific precautions";
      examples: [
        "Bangkok during air quality season — advise masks",
        "Dubai in summer — heat precautions, hydration guidance",
        "Goa during monsoon — water activity restrictions",
      ];
    };

    ELEVATED_RISK: {
      score: "40-59";
      color: "ORANGE";
      action: "Proceed with documented risk acknowledgment from customer";
      customer_communication: "Detailed risk disclosure; customer signs acknowledgment";
      insurance: "Comprehensive travel insurance mandatory (not optional)";
      agent_authority: "Agent must inform customer of specific risks; cannot hide risks";
      examples: [
        "Egypt during political tension — avoid certain areas",
        "Bali during volcanic activity — travel insurance required",
        "Thailand during political protests — avoid protest areas",
      ];
    };

    HIGH_RISK: {
      score: "20-39";
      color: "RED";
      action: "Booking requires manager approval; strong recommendation to reconsider";
      customer_communication: "Formal risk advisory; alternative destination suggested";
      alternatives: "Agent should propose safer alternative with similar experience";
      examples: [
        "Active conflict zone",
        "Severe natural disaster recovery",
        "Disease outbreak (epidemic level)",
      ];
    };

    EXTREME_RISK: {
      score: "0-19";
      color: "BLACK";
      action: "Booking blocked — agency will not sell travel to this destination";
      override: "Only owner-level override with written justification";
      examples: [
        "Active war zone",
        "Government travel ban in effect",
        "ME-Advisory Level 4 (Do Not Travel)",
      ];
    };
  };

  dynamic_reassessment: {
    description: "Risk is reassessed continuously, not just at booking time";
    triggers: [
      "Government travel advisory change (MEA updates)",
      "Natural disaster at destination",
      "Health advisory (disease outbreak, air quality spike)",
      "Political event (election, protest, coup)",
      "Terrorist incident at or near destination",
      "Supplier failure (hotel closure, airline bankruptcy)",
    ];
    reassessment_action: "If risk level increases during active trip → agent contacts customer with updated guidance";
    downgrade: "If risk decreases → notify customer that situation has improved";
  };

  customer_safety_briefing: {
    description: "Auto-generated safety briefing for each destination";
    content: {
      general_safety: "Area-specific do's and don'ts, common scams, safe/unsafe areas";
      health: "Required vaccinations, food/wwater precautions, mosquito protection, nearest hospital";
      emergency: "Local emergency numbers, Indian embassy contact, agency 24/7 hotline";
      cultural: "Dress codes, behavior expectations, religious site etiquette";
      transport: "Recommended transport modes, fair prices, what to avoid";
    };
    delivery: "Sent via WhatsApp + included in trip documents PDF + available in companion app";
    timing: "3-5 days before departure, after final payment";
  };
}
```

---

## Open Problems

1. **Data freshness** — Risk data from government advisories may be days or weeks old. Real-time risk assessment requires aggregating multiple sources and applying timeliness weighting.

2. **Risk perception vs. reality** — Some destinations are perceived as dangerous but are safe (Israel for tourists), while others are perceived as safe but have risks (pickpocketing in Paris). Balanced, factual assessment without fear-mongering is essential.

3. **Liability of risk disclosure** — Providing risk assessment creates a legal responsibility. If the agency assesses a destination as "moderate risk" and a customer is injured, does the assessment protect or expose the agency legally?

4. **Customer pushback** — Some customers may insist on traveling to high-risk destinations despite warnings. The agency needs clear policies on whether to facilitate or refuse such travel.

5. **Cultural sensitivity** — Risk descriptions of destinations must be factual and not perpetuate stereotypes. "Avoid walking alone at night" is universal safety advice; "This city is dangerous" is unhelpful and potentially biased.

---

## Next Steps

- [ ] Build multi-dimensional risk scoring engine with 5 risk categories
- [ ] Create data aggregation from government advisories, WHO, and travel intelligence sources
- [ ] Implement risk-level booking gates (green/yellow/orange/red/black)
- [ ] Design auto-generated customer safety briefing per destination
- [ ] Build dynamic reassessment system with real-time trigger monitoring
- [ ] Create risk dashboard for agents with active trip risk monitoring
- [ ] Implement manager approval workflow for elevated and high-risk bookings
