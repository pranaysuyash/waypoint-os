# Travel Health & Vaccination Intelligence — Advisory Engine

> Research document for automated health advisory generation, pre-trip health briefings, destination health scoring, and India-specific health regulations.

---

## Key Questions

1. **How do we auto-generate health advisories per trip?**
2. **What pre-trip health briefings do travelers need?**
3. **How do we score destinations for health safety?**
4. **What India-specific health regulations affect travel agencies?**

---

## Research Areas

### Automated Health Advisory Engine

```typescript
interface HealthAdvisoryEngine {
  // Generate trip-specific health advisory
  generateTripAdvisory(trip: Trip): TripHealthAdvisory;

  // Continuous monitoring for booked trips
  monitorActiveTrips(): HealthAlert[];

  // Pre-trip health checklist
  generateChecklist(trip: Trip, travelers: Traveler[]): HealthChecklist;
}

interface TripHealthAdvisory {
  trip_id: string;
  generated_at: string;

  destination_summaries: {
    destination: string;
    overall_health_risk: "LOW" | "MODERATE" | "HIGH" | "VERY_HIGH";
    risk_score: number;                  // 1-100

    vaccine_requirements: {
      status: "ALL_CLEAR" | "VACCINES_NEEDED" | "CERTIFICATES_EXPIRED";
      items: {
        vaccine: string;
        status: "COMPLETED" | "NEEDED" | "EXPIRED" | "NOT_APPLICABLE";
        urgency: "IMMEDIATE" | "WITHIN_2_WEEKS" | "RECOMMENDED";
        action: string;
      }[];
    };

    active_alerts: {
      alert_type: string;
      severity: string;
      summary: string;
      impact_on_trip: string;
    }[];

    health_precautions: string[];
    packing_list_additions: string[];    // "insect repellent", "water purification tablets"
  }[];

  traveler_specific_notes: {
    traveler: string;
    notes: string[];
    extra_precautions: string[];
  }[];
}

// ── Auto-generated trip health advisory ──
// ┌─────────────────────────────────────────────────────┐
// │  Trip Health Advisory — Auto-Generated                │
// │  Trip: WP-442 Singapore Family Trip (Jun 1-6)        │
// │  Generated: Apr 29, 2026                              │
// │                                                       │
// │  🇸🇬 Singapore — Risk: LOW (Score: 22/100)           │
// │                                                       │
// │  Vaccines: ✅ ALL CLEAR                              │
// │  • COVID-19: All travelers vaccinated ✅              │
// │  • No additional vaccines required for Singapore     │
// │                                                       │
// │  Active Alerts:                                       │
// │  ⚠️ Dengue outbreak (2,400+ cases in Apr)            │
// │     Impact: Use mosquito repellent, wear long sleeves│
// │     for evening outdoor activities                    │
// │                                                       │
// │  Precautions:                                         │
// │  • Stay hydrated (32°C expected)                     │
// │  • Sunscreen SPF 50+ (UV index: 8-10)               │
// │  • Use insect repellent (DEET-based)                 │
// │  • Tap water is safe to drink                        │
// │                                                       │
// │  Traveler Notes:                                      │
// │  • Rajesh (62): Carry diabetes medication, avoid     │
// │    extreme heat, insurance with pre-existing cover   │
// │  • Anaya (8): Children's mosquito repellent needed, │
// │    paediatric dosage for any medication              │
// │                                                       │
// │  Add to Packing List:                                 │
// │  • Insect repellent (DEET 30%+)                      │
// │  • Sunscreen SPF 50                                  │
// │  • Hand sanitizer                                    │
// │  • Rajesh: Prescription copy for Metformin           │
// └─────────────────────────────────────────────────────┘
```

### Pre-Trip Health Briefing

```typescript
interface PreTripHealthBriefing {
  trip_id: string;
  format: "WHATSAPP" | "EMAIL" | "PORTAL" | "PDF";

  sections: {
    title: string;
    content: string;
    importance: "MANDATORY" | "IMPORTANT" | "INFORMATIONAL";
  }[];

  checklist: {
    item: string;
    deadline: string;                    // "2 weeks before travel"
    status: "PENDING" | "COMPLETED" | "N/A";
    assigned_to: string;
  }[];
}

// ── Pre-trip health briefing (email/WhatsApp format) ──
// ┌─────────────────────────────────────────────────────┐
// │  🏥 Pre-Trip Health Briefing                          │
// │  Singapore Family Trip — Jun 1-6, 2026                │
// │                                                       │
// │  Hello Rajesh! Here's your health checklist:          │
// │                                                       │
// │  ⏰ Time-Sensitive Actions:                           │
// │  ☐ Get Yellow Fever certificate renewed (Rajesh)     │
// │    Deadline: May 15 (2 weeks before travel)           │
// │  ☐ Get Typhoid vaccine (Priya, Aarav)                │
// │    Deadline: May 18 (10 days before travel)           │
// │                                                       │
// │  📋 Before You Leave:                                 │
// │  ☐ Pack prescription medications in carry-on         │
// │  ☐ Carry doctor's prescription (English)             │
// │  ☐ Travel insurance card (digital + print)           │
// │  ☐ Emergency contacts saved in phone                 │
// │  ☐ Download offline medical translation app          │
// │                                                       │
// │  🌡️ During Your Trip:                                │
// │  • Drink bottled or tap water (safe in Singapore)    │
// │  • Use mosquito repellent (dengue risk)              │
// │  • Apply sunscreen (UV index very high)              │
// │  • Set medication alarms (SGT is +2.5h from IST)     │
// │                                                       │
// │  🆘 In Case of Emergency:                             │
// │  • App SOS button → immediate assistance             │
// │  • Insurance hotline: +91-124-XXXX (24x7)            │
// │  • Nearest hospital: Mt Elizabeth (Orchard)          │
// │  • Singapore emergency: 995                          │
// └─────────────────────────────────────────────────────┘
```

### Destination Health Scoring

```typescript
interface DestinationHealthScore {
  destination: string;
  overall_score: number;                // 1-100 (higher = safer)
  last_updated: string;

  dimensions: {
    healthcare_quality: number;         // hospital quality, doctor availability
    infectious_disease_risk: number;    // endemic diseases, outbreak risk
    food_water_safety: number;          // food hygiene, water quality
    environmental_hazards: number;      // air quality, UV, natural disasters
    emergency_response: number;         // ambulance speed, emergency services
    vaccination_burden: number;         // how many vaccines needed
    medical_access_for_foreigners: number; // English-speaking, cashless
  };

  trends: {
    score_3_months_ago: number;
    score_change: number;
    improving: boolean;
    alerts_increasing: boolean;
  };
}

// ── Destination health scores ──
// ┌─────────────────────────────────────────────────────┐
// │  Destination Health Safety Scores                     │
// │                                                       │
// │  Destination    | Score | Trend | Key Risk           │
// │  ─────────────────────────────────────────────────── │
// │  Singapore      | 88/100| →  0% | Dengue (seasonal) │
// │  Dubai          | 85/100| ↑ +2% | Heat (summer)     │
// │  Thailand       | 72/100| ↓ -5% | Dengue outbreak   │
// │  Kerala         | 68/100| →  0% | Monsoon diseases  │
// │  Bali           | 62/100| ↓ -3% | Rabies risk       │
// │  Rajasthan      | 58/100| ↑ +1% | Heat (summer)     │
// │  Sri Lanka      | 55/100| ↓ -8% | Dengue + economic │
// │  Nepal          | 48/100| →  0% | Altitude, limited  │
// │  Goa            | 65/100| →  0% | Water safety       │
// │  Kashmir        | 60/100| ↑ +3% | Improving          │
// │                                                       │
// │  Score breakdown: Singapore (88)                      │
// │  Healthcare:    95 ████████████████████              │
// │  Disease risk:  85 ████████████████                 │
// │  Food/water:    90 █████████████████                 │
// │  Environmental: 82 ████████████████                 │
// │  Emergency:     92 ███████████████████              │
// │  Vaccine burden: 95 ████████████████████            │
// │  Foreign access: 88 █████████████████               │
// └─────────────────────────────────────────────────────┘
```

### India-Specific Health Regulations

```typescript
// ── India health regulations for travel agencies ──
// ┌─────────────────────────────────────────────────────┐
// │  India Health Regulations Affecting Agencies           │
// │                                                       │
// │  1. International Health Regulations (IHR):           │
// │     • Must inform travelers of health requirements    │
// │     • Liability if traveler denied entry due to       │
// │       missing health documents                        │
// │                                                       │
// │  2. Vaccination Requirements:                         │
// │     • Outbound: Must inform re: destination vaccines  │
// │     • Inbound: Yellow Fever cert for endemic areas    │
// │     • COVID: No longer required but may change       │
// │                                                       │
// │  3. Medical Tourism (Inbound):                        │
// │     • M-Visa facilitation required                    │
// │     • Hospital letter mandatory                       │
// │     • Medical visa extension assistance               │
// │     • Must work with NABH/JCI accredited hospitals   │
// │                                                       │
// │  4. Travel Insurance Advisory:                        │
// │     • IRDAI mandated disclosure of coverage           │
// │     • Must offer insurance for international trips    │
// │     • Cannot sell insurance without license           │
// │     • Must disclose exclusions clearly                │
// │                                                       │
// │  5. Food Safety (Domestic Tours):                     │
// │     • FSSAI compliance for packaged tour meals        │
// │     • Liability for food poisoning on group tours     │
// │     • Must verify hotel FSSAI licenses                │
// │                                                       │
// │  6. COVID/Endemic Disease Protocols:                  │
// │     • Follow MoHFW guidelines (can change rapidly)    │
// │     • Must have cancellation policy for health bans   │
// │     • Refund obligations if travel banned by govt     │
// └─────────────────────────────────────────────────────┘
```

---

## Open Problems

1. **Advisory accuracy vs liability** — If the agency provides incorrect health advice, who is liable? Must clearly state advisories are "informational, consult your doctor."

2. **Real-time outbreak data** — WHO and CDC data has 1-2 week lag. Social media and news report outbreaks faster but are unreliable. Need to balance speed vs accuracy.

3. **Regulatory compliance burden** — Health regulations differ by country and change frequently. Maintaining compliance across all destinations is operationally expensive.

4. **Traveler non-compliance** — Travelers may ignore vaccination advice. Need clear liability disclaimers and insurance implications when travelers skip recommended vaccines.

---

## Next Steps

- [ ] Build automated health advisory engine with trip-specific generation
- [ ] Create pre-trip health briefing delivery (WhatsApp/email)
- [ ] Implement destination health scoring system
- [ ] Design India health regulation compliance tracker
- [ ] Integrate with IATA Timatic for real-time health requirements
