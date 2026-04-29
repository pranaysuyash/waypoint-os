# Travel Health & Vaccination Intelligence — Medical Travel & Assistance

> Research document for travel medical insurance integration, emergency medical assistance, medical tourism coordination, and traveler health support during trips.

---

## Key Questions

1. **How do we integrate medical assistance with travel insurance?**
2. **What emergency medical support do travelers need abroad?**
3. **How do we handle medical tourism trips specifically?**
4. **What health support is needed during active trips?**

---

## Research Areas

### Travel Medical Insurance Integration

```typescript
interface TravelMedicalInsurance {
  trip_id: string;
  policy: {
    provider: string;
    policy_number: string;
    type: "STANDARD" | "COMPREHENSIVE" | "PREMIUM" | "GROUP";
    coverage: {
      medical_emergencies: Money;
      hospitalization: Money;
      emergency_evacuation: Money;
      repatriation: Money;
      dental_emergency: Money;
      trip_cancellation_medical: Money;
      pre_existing_conditions: boolean;
      adventure_sports: boolean;
      pregnancy_complications: boolean;
      covid19: boolean;
    };
    deductible: Money;
    premium: Money;
    excess: Money;
    valid_from: string;
    valid_to: string;
    destination_scope: "WORLDWIDE" | "ASIA" | "SCHENGEN" | "SPECIFIC";
  };

  // Emergency contacts
  emergency: {
    24x7_hotline: string;
    whatsapp: string | null;
    email: string;
    claims_portal: string;
    cashless_hospitals: string[];        // network hospitals
  };
}

// ── Insurance card for traveler ──
// ┌─────────────────────────────────────────────────────┐
// │  Travel Insurance — Policy Card                       │
// │                                                       │
// │  Provider: ICICI Lombard                              │
// │  Policy: TRV-2026-XXXXXX                              │
// │  Type: Comprehensive                                  │
// │                                                       │
// │  Coverage:                                            │
// │  Medical Emergency: $500,000                          │
// │  Hospitalization: $500,000                            │
// │  Emergency Evacuation: $250,000                       │
// │  Repatriation: $100,000                               │
// │  Dental: $2,000                                       │
// │  Trip Cancellation: ₹3,00,000                        │
// │                                                       │
// │  Premium: ₹4,500 | Deductible: $100                  │
// │  Valid: May 1 - May 8, 2026                          │
// │  Scope: Asia Pacific                                  │
// │  Pre-existing: Covered (declared)                     │
// │                                                       │
// │  📞 Emergency: +91-124-XXXXXX (24x7)                 │
// │  📱 WhatsApp: +91-98765-XXXXX                        │
// │  🌐 Claims: ilclaims.icicilombard.com                │
// │                                                       │
// │  Cashless hospitals in Singapore: 15                  │
// │  Nearest: Mount Elizabeth Hospital (2.3km)           │
// └─────────────────────────────────────────────────────┘
```

### Emergency Medical Assistance

```typescript
interface MedicalEmergencyResponse {
  incident_id: string;
  trip_id: string;
  traveler_id: string;

  // Incident details
  incident_type: "ILLNESS" | "INJURY" | "ALLERGIC_REACTION" | "CHRONIC_CONDITION" | "ACCIDENT" | "FOOD_POISONING" | "OTHER";
  severity: "MINOR" | "MODERATE" | "SERIOUS" | "CRITICAL";
  description: string;
  location: GeoLocation;
  reported_at: string;

  // Response coordination
  response: {
    nearby_hospitals: {
      name: string;
      distance_km: number;
      rating: number;
      english_support: boolean;
      cashless_network: boolean;
      phone: string;
    }[];
    recommended_hospital: string;

    insurance_notification: {
      notified: boolean;
      pre_approval: "NOT_NEEDED" | "PENDING" | "APPROVED" | "DENIED";
      claim_started: boolean;
      claim_number: string | null;
    };

    agent_notification: boolean;
    family_notification: boolean;
    guide_notification: boolean;

    local_ambulance: {
      called: boolean;
        provider: string | null;
        eta_minutes: number | null;
    };

    translation_needed: boolean;
    translator_arranged: boolean;
  };
}

// ── Emergency medical flow ──
// ┌─────────────────────────────────────────────────────┐
// │  Medical Emergency Response — Trip WP-442              │
// │                                                       │
// │  Traveler: Rajesh Sharma                              │
// │  Incident: Chest pain, suspected cardiac issue        │
// │  Severity: CRITICAL                                   │
// │  Location: Orchard Road, Singapore                    │
// │  Reported: 14:32 SGT                                  │
// │                                                       │
// │  Response Timeline:                                    │
// │  14:32 — SOS triggered, GPS shared                   │
// │  14:33 — Insurance hotline notified                  │
// │  14:33 — Agent Priya notified                        │
// │  14:34 — Ambulance called (Singapore 995)            │
// │  14:35 — Nearest hospital: Mt Elizabeth (1.2km)     │
// │  14:36 — Pre-approval: APPROVED (cashless)           │
// │  14:38 — Family notified (Priya Sharma, +91-XXXXX)  │
// │  14:40 — Ambulance ETA: 4 min                        │
// │  14:44 — Ambulance arrived                           │
// │  14:52 — Arrived at Mt Elizabeth A&E                │
// │  15:00 — Doctor assessment in progress               │
// │  15:30 — Stable, observation for 24 hours            │
// │                                                       │
// │  Insurance: ICICI Lombard, Cashless ✅                │
// │  Claim: TRV-CLM-2026-XXXX (auto-started)             │
// │  Coverage: Up to $500K medical emergency             │
// │                                                       │
// │  Agent actions:                                       │
// │  ✅ Family informed                                   │
// │  ✅ Hotel informed (extend stay if needed)            │
// │  ✅ Return flight rebooking standby                   │
// │  ✅ Trip documents updated                            │
// └─────────────────────────────────────────────────────┘
```

### Medical Tourism Coordination

```typescript
interface MedicalTourismTrip {
  trip_id: string;
  type: "MEDICAL_TOURISM";

  medical_details: {
    procedure: string;
    hospital: string;
    doctor: string;
    estimated_duration_days: number;
    recovery_days: number;
    pre_op_requirements: string[];
    post_op_care: string[];
    follow_up_required: boolean;
  };

  logistics: {
    hospital_transfer: TransportBooking;
    accommodation: {
      type: "HOSPITAL" | "RECOVERY_HOTEL" | "SERVICED_APARTMENT";
      accessible_room: boolean;
      nursing_support: boolean;
      wheelchair_accessible: boolean;
    };
    companion_stay: {
      hotel: string;
      distance_to_hospital_km: number;
    };
    medical_visa: {
      required: boolean;
      type: string;                     // "M-Visa" for India
      letter_from_hospital: boolean;
    };
    post_op_transport: "AMBULANCE" | "WHEELCHAIR_CAR" | "STANDARD";
  };

  cost_breakdown: {
    procedure_cost: Money;
    hospital_stay: Money;
    medication: Money;
    accommodation: Money;
    travel: Money;
    total: Money;
    savings_vs_home_country: Money;     // what they save vs getting it at home
  };
}

// ── Medical tourism trip ──
// ┌─────────────────────────────────────────────────────┐
// │  Medical Tourism Trip — Knee Replacement               │
// │  Patient: Ahmed (58, from Dubai)                      │
// │  Destination: Chennai, India                          │
// │                                                       │
// │  Hospital: Apollo Hospitals, Greams Road              │
// │  Surgeon: Dr. Rajasekar (Orthopedic, 25yr exp)       │
// │  Procedure: Total Knee Replacement (bilateral)       │
// │                                                       │
// │  Timeline:                                            │
// │  Day 1:  Arrival, hospital admission, pre-op tests   │
// │  Day 2:  Surgery (morning), ICU recovery             │
// │  Day 3:  Room transfer, physio begins                │
// │  Day 4-7: Hospital stay, daily physio                │
// │  Day 8:  Discharge → recovery hotel                  │
// │  Day 9-14: Recovery, daily physio sessions           │
// │  Day 15: Follow-up check, clearance to fly           │
// │  Day 16: Return to Dubai                             │
// │                                                       │
// │  Cost:                                                │
// │  Procedure: ₹5,50,000 ($6,600)                      │
// │  Hospital (7 days): ₹1,40,000 ($1,700)              │
// │  Recovery hotel (8 days): ₹48,000 ($575)            │
// │  Flights: ₹32,000 ($385)                            │
// │  Medication: ₹15,000 ($180)                         │
// │  Total: ₹7,85,000 (~$9,400)                        │
// │                                                       │
// │  Same procedure in Dubai: ~$35,000                   │
// │  Savings: ~$25,600 (73% less)                        │
// │                                                       │
// │  Visa: M-Visa (medical), hospital letter provided ✅ │
// │  Insurance: N/A (self-pay, medical tourism)          │
// └─────────────────────────────────────────────────────┘
```

### Active Trip Health Support

```typescript
interface ActiveTripHealthSupport {
  trip_id: string;
  travelers: {
    traveler_id: string;
    health_notes: string[];             // agent-visible notes
    medication_reminders: {
      medication: string;
      schedule: string;                 // "8am, 8pm daily"
      timezone: string;
    }[];
    allergies: string[];
    dietary_restrictions: string[];
    blood_group: string;
    emergency_contact: string;
  }[];

  // Daily health briefing
  daily_health_briefing: {
    destination: string;
    uv_index: number;
    air_quality_index: number;
    temperature_range: { high: number; low: number };
    heat_advisory: boolean;
    mosquito_risk: "NONE" | "LOW" | "MODERATE" | "HIGH";
    water_safety: boolean;
    food_safety_alerts: string[];
    health_tips: string[];
  };

  // Nearby medical facilities
  nearby_medical: {
    hospitals: { name: string; distance_km: number; phone: string }[];
    pharmacies: { name: string; distance_km: number; open_24h: boolean }[];
    travel_clinic: { name: string; distance_km: number } | null;
  };
}

// ── Daily health briefing (WhatsApp) ──
// ┌─────────────────────────────────────────────────────┐
// │  🏥 Daily Health Briefing — Singapore                  │
// │  Trip: WP-442 | Day 3 of 5                            │
// │                                                       │
// │  Weather: 32°C / 27°C | UV: 8 (Very High) 🌞        │
// │  AQI: 45 (Good) ✅ | Humidity: 82%                  │
// │                                                       │
// │  Health Alerts:                                       │
// │  ⚠️ Dengue risk: HIGH — use mosquito repellent       │
// │  ⚠️ UV: Very high — sunscreen SPF 50+               │
// │  ℹ️ Hydration reminder: drink 3L+ water daily        │
// │                                                       │
// │  Rajesh's Medications:                                │
// │  • Metformin 500mg — 8am, 8pm SGT ✅                 │
// │  • Blood sugar check — before meals                  │
// │                                                       │
// │  Nearby Help:                                         │
// │  🏥 Mt Elizabeth: 1.2km | +65-XXXX                  │
// │  💊 Guardian Pharmacy: 200m | Open 24h               │
// │                                                       │
// │  Food tips: Hawker centres are safe, avoid raw seafood│
// │  Water: Tap water safe in Singapore ✅                │
// │                                                       │
// │  Emergency: SOS button → immediate assistance        │
// └─────────────────────────────────────────────────────┘
```

---

## Open Problems

1. **Cashless vs reimbursement** — Many Indian travelers expect cashless hospital admission abroad, but networks are limited. Need clear communication about reimbursement processes.

2. **Medical record portability** — Indian medical records (ABHA health ID) aren't universally recognized abroad. Need standardized medical summary formats.

3. **Post-trip medical follow-up** — Travelers who get sick abroad may need follow-up care at home. Coordinating between foreign hospitals and home doctors is complex.

4. **Language barriers in medical emergencies** — Medical terminology translation is specialized. Standard translation services may miss critical nuances.

---

## Next Steps

- [ ] Build travel medical insurance comparison and purchase flow
- [ ] Create emergency medical response coordination system
- [ ] Implement medical tourism trip coordination module
- [ ] Design daily health briefing for active trips
- [ ] Build nearby medical facility finder
