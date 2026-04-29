# Travel Health & Vaccination Intelligence — Health Requirements

> Research document for destination health requirements, vaccination tracking, travel health advisories, medical clearance workflows, and health certificate management.

---

## Key Questions

1. **What health requirements must travelers meet per destination?**
2. **How do we track and verify vaccination status?**
3. **What health advisories affect travel decisions?**
4. **How do we manage medical clearance workflows?**

---

## Research Areas

### Destination Health Requirements

```typescript
interface DestinationHealthProfile {
  destination: string;
  country: string;

  // Required vaccinations
  required_vaccines: {
    vaccine: string;                    // "Yellow Fever", "COVID-19"
    required_for_entry: boolean;
    required_from_countries: string[];  // only if arriving from certain countries
    minimum_days_before_travel: number;
    certificate_required: boolean;
    certificate_format: "WHO_ICVP" | "DIGITAL_CERT" | "OTHER";
    validity_period_months: number;
  }[];

  // Recommended vaccinations
  recommended_vaccines: {
    vaccine: string;
    risk_level: "HIGH" | "MODERATE" | "LOW";
    reason: string;
  }[];

  // Health risks
  health_risks: {
    risk: string;                       // "Malaria", "Dengue", "Altitude sickness"
    risk_level: "ENDEMIC" | "SEASONAL" | "OUTBREAK" | "LOW";
    affected_regions: string[];
    prevention: string[];
    peak_months: number[];
  }[];

  // Health infrastructure
  health_infrastructure: {
    healthcare_quality: "EXCELLENT" | "GOOD" | "ADEQUATE" | "POOR";
    emergency_services: boolean;
    english_speaking_doctors: boolean;
    travel_clinics: string[];
    hospital_count: number;
    ambulance_number: string;
  }[];

  // Food & water safety
  food_water_safety: {
    tap_water_safe: boolean;
    food_safety_rating: "SAFE" | "CAUTION" | "AVOID_STREET_FOOD";
    common_issues: string[];
    precautions: string[];
  };

  last_updated: string;
}

// ── Destination health card ──
// ┌─────────────────────────────────────────────────────┐
// │  Health Profile: Thailand                              │
// │                                                       │
// │  Required Vaccines:                                   │
// │  • Yellow Fever: Only if arriving from endemic areas  │
// │  • COVID-19: Proof of vaccination OR negative test   │
// │                                                       │
// │  Recommended Vaccines:                                │
// │  • Hepatitis A  — HIGH risk                          │
// │  • Typhoid       — HIGH risk                         │
// │  • Japanese Enc. — MODERATE (rural areas)            │
// │  • Rabies        — MODERATE (animal contact)         │
// │                                                       │
// │  Health Risks:                                        │
// │  • Dengue: ENDEMIC, peak May-Oct                     │
// │  • Malaria: Low risk, border regions only            │
// │  • Traveler's diarrhea: COMMON                       │
// │                                                       │
// │  Healthcare: GOOD | English-speaking doctors ✅       │
// │  Emergency: 1669 | Water: NOT safe to drink          │
// │  Food: CAUTION (street food hygiene varies)          │
// └─────────────────────────────────────────────────────┘
```

### Vaccination Tracking System

```typescript
interface TravelerVaccinationRecord {
  traveler_id: string;
  vaccines: {
    vaccine: string;
    date_administered: string;
    booster_due: string | null;
    certificate_number: string | null;
    certificate_url: string | null;
    administering_facility: string;
    lot_number: string | null;
    valid_until: string | null;
    verified: boolean;
    verified_by: string | null;          // system or manual
  }[];

  // Computed
  missing_vaccines_for_destination: {
    destination: string;
    missing: string[];
    action_required: string;
    deadline_days: number;
  }[];
}

// ── Vaccination tracking dashboard ──
// ┌─────────────────────────────────────────────────────┐
// │  Vaccination Tracker — Family: Sharma (4 travelers)   │
// │                                                       │
// │  Traveler   | Vaccine      | Status   | Valid Until  │
// │  ─────────────────────────────────────────────────── │
// │  Rajesh     | COVID-19     | ✅ Done  | Aug 2026    │
// │  (Adult)    | Hepatitis A  | ✅ Done  | Lifetime    │
// │             | Typhoid      | ✅ Done  | Jul 2028    │
// │             | Yellow Fever | ⚠️ Exp. | Jan 2025 ❌ │
// │                                                       │
// │  Priya      | COVID-19     | ✅ Done  | Sep 2026    │
// │  (Adult)    | Hepatitis A  | ✅ Done  | Lifetime    │
// │             | Typhoid      | ❌ Missing             │
// │                                                       │
// │  Aarav      | COVID-19     | ✅ Done  | Oct 2026    │
// │  (Child,12) | Hepatitis A  | ✅ Done  | Lifetime    │
// │             | Typhoid      | ❌ Missing             │
// │                                                       │
// │  Anaya      | COVID-19     | ❌ Underage (8)        │
// │  (Child, 8) | Hepatitis A  | ✅ Done  | Lifetime    │
// │             | Typhoid      | ❌ Missing             │
// │                                                       │
// │  Trip: Thailand (Jun 2026)                            │
// │  Actions needed:                                      │
// │  🔴 Rajesh: Yellow Fever booster (expired)           │
// │  🟡 Priya, Aarav: Typhoid vaccine needed             │
// │  ℹ️ Anaya: COVID exemption (under 12)                │
// │                                                       │
// │  Recommended clinic: Travel Health Centre, Andheri    │
// │  Appointment: May 15, 2026 (3 weeks before travel)   │
// └─────────────────────────────────────────────────────┘
```

### Travel Health Advisory Feed

```typescript
interface HealthAdvisory {
  id: string;
  source: "WHO" | "CDC" | "MOH_INDIA" | "ECDC" | "LOCAL";
  severity: "INFO" | "ADVISORY" | "WARNING" | "ALERT";
  type: "DISEASE_OUTBREAK" | "EPIDEMIC" | "PANDEMIC" | "FOOD_SAFETY" | "AIR_QUALITY" | "WATER_CONTAMINATION" | "NATURAL_DISASTER_HEALTH";

  title: string;
  description: string;
  affected_destinations: string[];
  affected_regions: string[];

  issued_at: string;
  expires_at: string | null;

  affected_trips: string[];             // trips in system that are impacted
  recommended_actions: string[];
  travel_impact: "NO_IMPACT" | "CAUTION" | "CONSIDER_POSTPONING" | "AVOID_TRAVEL";
}

// ── Health advisory dashboard ──
// ┌─────────────────────────────────────────────────────┐
// │  Health Advisory Feed — Active Alerts (3)             │
// │                                                       │
// │  🔴 ALERT — Dengue Outbreak: Singapore               │
// │     Source: MOH Singapore | Issued: Apr 25, 2026     │
// │     Cases: 2,400+ in Apr (3x normal)                 │
// │     Affected trips: 8 (WP-442, WP-448, ...)         │
// │     Impact: CAUTION — use mosquito prevention        │
// │     Action: Send advisory to all SG-bound travelers  │
// │                                                       │
// │  🟡 WARNING — Air Quality: Delhi NCR                 │
// │     Source: CPCB India | AQI: 280 (Poor)             │
// │     Affected: Travelers with respiratory issues      │
// │     Impact: CAUTION — carry masks, limit outdoor     │
// │     Affected trips: 3                                │
// │                                                       │
// │  ℹ️ INFO — New COVID variant: Southeast Asia         │
// │     Source: WHO | Low severity, high transmissibility │
// │     Impact: No travel restrictions currently         │
// │     Action: Monitor, no client action needed         │
// └─────────────────────────────────────────────────────┘
```

### Medical Clearance Workflow

```typescript
interface MedicalClearance {
  trip_id: string;
  traveler_id: string;

  // Trigger conditions
  triggers: {
    pre_existing_conditions: string[];
    high_risk_destination: boolean;
    extreme_activities: string[];       // "scuba diving", "trekking >4000m"
    age_over_65: boolean;
    pregnant: boolean;
  };

  // Clearance workflow
  status: "NOT_NEEDED" | "PENDING" | "FORM_REQUESTED" | "COMPLETED" | "CLEARED" | "NOT_CLEARED" | "CONDITIONAL";
  medical_form: {
    sent_at: string | null;
    completed_at: string | null;
    doctor_name: string | null;
    doctor_license: string | null;
    conditions_declared: string[];
    medications_list: string[];
    fitness_for_travel: boolean | null;
    restrictions: string[];
  };

  // Insurance implications
  insurance_impact: {
    standard_coverage: boolean;
    premium_required: boolean;
    exclusions: string[];
    additional_premium: Money | null;
  };
}

// ── Medical clearance flow ──
// ┌─────────────────────────────────────────────────────┐
// │  Medical Clearance Workflow                            │
// │                                                       │
// │  Trip: WP-442 Singapore Family Trip                   │
// │  Traveler: Rajesh Sharma (62, diabetic)               │
// │                                                       │
// │  Triggers:                                            │
// │  • Age > 60 ✅                                        │
// │  • Pre-existing condition: Diabetes ✅                │
// │  • Extreme activity: None ❌                          │
// │                                                       │
// │  Status: CONDITIONAL CLEARANCE ✅                     │
// │  Doctor: Dr. Mehta, License: MCI-12345               │
// │  Completed: Apr 20, 2026                              │
// │                                                       │
// │  Conditions:                                          │
// │  • Carry medication (Metformin) with prescription    │
// │  • Travel insurance with pre-existing cover required │
// │  • Avoid extreme heat activities (>35°C)             │
// │                                                       │
// │  Insurance: Premium plan required (+₹2,500)          │
// │  Standard policy excludes diabetes complications     │
// └─────────────────────────────────────────────────────┘
```

---

## Open Problems

1. **Vaccine data accuracy** — Requirements change frequently (especially post-COVID). Need automated feeds from WHO/IATA Timatic, not manual updates.

2. **Medical data privacy** — Vaccination records and health conditions are sensitive. Must comply with India DPDP Act and medical data regulations. Access strictly limited.

3. **Pediatric vaccination complexity** — Children have different vaccine schedules, age-based requirements, and exemption rules. One-size-fits-all doesn't work.

4. **International certificate verification** — Fake vaccination certificates exist. Digital verification (like India's CoWIN API for COVID) is ideal but not available for all vaccines.

---

## Next Steps

- [ ] Build destination health requirements database with auto-update
- [ ] Create traveler vaccination tracking with trip-specific gap analysis
- [ ] Implement health advisory feed with trip matching
- [ ] Design medical clearance workflow for high-risk travelers
- [ ] Integrate with travel insurance for health-based premium adjustment
