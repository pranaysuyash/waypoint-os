# Trip Control Room — Traveler Communication & Real-Time Tools

> Research document for real-time traveler communication, the trip companion app, location sharing, and in-trip support tools for the Waypoint OS platform.

---

## Key Questions

1. **How do travelers receive real-time trip updates?**
2. **What tools help travelers during the trip?**
3. **How does location sharing work with privacy?**
4. **What in-trip support is available to travelers?**

---

## Research Areas

### Traveler Trip Companion

```typescript
interface TripCompanion {
  // Mobile-first trip companion (PWA / WhatsApp)
  trip_id: string;
  traveler_id: string;

  // Today's plan
  today: {
    date: string;
    day_number: number;
    city: string;
    weather: { temp: number; condition: string; high: number; low: number };

    schedule: {
      time: string;
      activity: string;
      location: string;
      status: "UPCOMING" | "IN_PROGRESS" | "COMPLETED" | "CHANGED";
      notes: string | null;
      map_link: string | null;
    }[];

    reminders: string[];
  };

  // Quick actions
  quick_actions: {
    contact_agent: string;               // WhatsApp link
    emergency_help: string;              // direct line
    share_location: boolean;
    view_documents: string;
    report_issue: string;
  };
}

// ── Traveler companion (WhatsApp-based) ──
// ┌─────────────────────────────────────────────────────┐
// │  Waypoint OS — Sharma Singapore Trip                     │
// │  Day 3 of 5 · Tuesday, June 3                           │
// │  Singapore · 🌤️ 31°C (Afternoon showers expected)       │
// │                                                       │
// │  Today's Schedule:                                    │
// │  ┌───────────────────────────────────────────────┐   │
// │  │ ✅ 8:00 AM  Breakfast at hotel                  │   │
// │  │ ✅ 9:30 AM  Universal Studios Singapore          │   │
// │  │         ⚠️ Changed → Night Safari (crowding)     │   │
// │  │ ⬜ 1:00 PM  Lunch at Newton Food Centre           │   │
// │  │ ⬜ 3:00 PM  Gardens by the Bay                   │   │
// │  │ ⬜ 5:30 PM  Supertree Grove light show            │   │
// │  │ ⬜ 7:00 PM  Dinner at Clarke Quay                 │   │
// │  │ ⬜ 8:30 PM  Night Safari (rescheduled)            │   │
// │  └───────────────────────────────────────────────┘   │
// │                                                       │
// │  Reminders:                                           │
// │  • Umbrella recommended (showers after 2 PM)           │
// │  • Comfortable shoes for Gardens walking               │
// │  • Camera for Supertree light show 📸                  │
// │                                                       │
// │  Quick Actions:                                       │
// │  [💬 Agent Chat] [📍 Share Location] [🆘 Emergency]    │
// │  [📄 Documents] [🌧️ Weather] [🍽️ Food Near Me]       │
// │                                                       │
// │  Need help? Reply anytime — your agent Priya is        │
// │  available until 6 PM IST. Night support: Rahul.       │
// └─────────────────────────────────────────────────────┘
```

### Real-Time Trip Updates

```typescript
interface TripUpdateSystem {
  // Proactive updates pushed to travelers
  updates: {
    // Pre-activity briefing
    PRE_ACTIVITY: {
      trigger: "30 minutes before next activity";
      content: {
        activity_name: string;
        location: string;
        map_link: string;
        duration: string;
        what_to_bring: string[];
        weather_note: string | null;
        dress_code: string | null;
        pickup_time: string | null;
        pickup_location: string | null;
      };
    };

    // Day briefing
    DAY_BRIEFING: {
      trigger: "8:00 AM local time";
      content: {
        day_number: number;
        weather: string;
        schedule_summary: string;
        important_reminders: string[];
        local_tip: string;               // "MRT is fastest to Gardens today"
        exchange_rate: string | null;
      };
    };

    // Disruption alert
    DISRUPTION_ALERT: {
      trigger: "Disruption detected affecting this trip";
      content: {
        what_happened: string;
        impact: string;
        new_plan: string;
        action_needed: string | null;     // "Head to Gate B3"
        agent_contact: string;
      };
    };
  };
}

// ── Day briefing (WhatsApp) ──
// ┌─────────────────────────────────────────────────────┐
// │  ☀️ Good Morning, Sharma Family!                         │
// │  Day 3 in Singapore · Tuesday, June 3                    │
// │                                                       │
// │  Weather: 🌤️ 31°C, afternoon showers                   │
// │  Bring umbrella! ☂️                                    │
// │                                                       │
// │  Today's highlights:                                  │
// │  🎢 Universal Studios (9:30 AM - 2 PM)                │
// │  🌳 Gardens by the Bay (3:00 PM - 6 PM)               │
// │  🍽️ Dinner at Clarke Quay (7 PM)                       │
// │  🦇 Night Safari (8:30 PM)                             │
// │                                                       │
// │  💡 Local tip: Take MRT to Bayfront station for        │
// │  Gardens — faster than taxi during rush hour.          │
// │                                                       │
// │  💱 SGD/INR rate today: ₹62.4                          │
// │  (Better than when you booked! 💰)                     │
// │                                                       │
// │  Need anything? Just reply to this message.             │
// │  Your agent Priya is online until 6 PM IST.             │
// └─────────────────────────────────────────────────────┘
```

### Location Sharing & Traveler Tracking

```typescript
interface TravelerTracking {
  // Opt-in location sharing
  consent: {
    location_sharing_enabled: boolean;
    consent_date: string | null;
    scope: "AGENCY_ONLY" | "AGENT_ONLY" | "FAMILY_TOO";
    frequency: "CONTINUOUS" | "CHECK_IN_BASED" | "MANUAL";
    expires: string;                      // trip end date
  };

  // Location data
  location: {
    last_known: {
      latitude: number;
      longitude: number;
      accuracy_meters: number;
      timestamp: string;
      battery_level: number | null;
    };

    // Inferred state
    inferred_state: "AT_HOTEL" | "AT_ACTIVITY" | "IN_TRANSIT" | "AT_RESTAURANT" | "UNKNOWN";
    confidence: number;
  };

  // Geo-fence alerts
  geo_fences: {
    name: string;                         // "Hotel", "Airport"
    type: "ARRIVAL" | "DEPARTURE";
    triggered: boolean;
    triggered_at: string | null;
  }[];
}

// ── Location tracking dashboard (agent view) ──
// ┌─────────────────────────────────────────────────────┐
// │  Traveler Location — Sharma Family (opt-in)             │
// │  Singapore · Day 3                                      │
// │                                                       │
// │  ┌───── Singapore Map ─────────────────────────────┐ │
// │  │                                                 │ │
// │  │     🏨 Taj Vivanta (hotel)                      │ │
// │  │         ↑ 2.3 km                                │ │
// │  │     📍 Sharma family                            │ │
// │  │         (Newton Food Centre area)                │ │
// │  │         Updated: 12:45 PM SGT                   │ │
// │  │         Battery: 62% 🔋                         │ │
// │  │         State: AT_RESTAURANT (90% confidence)    │ │
// │  │                                                 │ │
// │  │     🌳 Gardens by the Bay (next: 3 PM)          │ │
// │  │                                                 │ │
// │  │  Geo-fences:                                    │ │
// │  │  ✅ Hotel arrival: Jun 1, 4:30 PM               │ │
// │  │  ✅ Airport departure: Jun 1, 11:00 AM           │ │
// │  │  ⬜ Airport arrival (return): Jun 6 (expected)   │ │
// │  └─────────────────────────────────────────────────┘ │
// │                                                       │
// │  Privacy: Location shared with agent only              │
// │  Expires: Jun 6, 2026 (trip end)                       │
// │  Last update: 12:45 PM (auto, every 30 min)            │
// │                                                       │
// │  [Contact Traveler] [Send Directions] [Pause Tracking]  │
// └─────────────────────────────────────────────────────┘
```

### In-Trip Support Tools

```typescript
interface InTripSupport {
  // Traveler self-service tools
  self_service: {
    // Emergency assistance
    emergency: {
      nearest_hospital: { name: string; distance_km: number; phone: string };
      police: { phone: string; nearest: string };
      embassy: { name: string; phone: string; address: string };
      insurance_helpline: string;
      agent_emergency_line: string;
    };

    // Quick reference
    reference: {
      hotel_address: string;
      hotel_phone: string;
      agent_phone: string;
      wifi_password: string | null;
      local_emergency_number: string;     // "911", "999", "112"
      nearest_pharmacy: string;
      nearest_atm: string;
    };

    // Translation help
    translation: {
      common_phrases: { english: string; local: string }[];
      language: string;
    };

    // Currency converter
    currency: {
      from: string;
      to: string;
      rate: number;
      last_updated: string;
      offline_rates: boolean;
    };
  };
}

// ── Emergency quick-access (WhatsApp) ──
// ┌─────────────────────────────────────────────────────┐
// │  🆘 Emergency Help — Singapore                          │
// │                                                       │
// │  Quick contacts:                                      │
// │  🚑 Emergency: 995 (ambulance)                         │
// │  🚔 Police: 999                                        │
// │  🏥 Nearest hospital: Raffles Hospital (2.3 km)        │
// │  🇮🇳 Indian Embassy: +65-6737-6767                     │
// │  🛡️ Insurance: Star Health 1800-425-2255                │
// │  💬 Your agent Priya: +91-98XXX-XXXXX                   │
// │                                                       │
// │  Hotel address:                                       │
// │  Taj Vivanta, 1 Maju Lane, Singapore 667688            │
// │                                                       │
// │  Common phrases:                                      │
// │  "Help!" → "Tolong!"                                  │
// │  "Hospital" → "Hospital"                              │
// │  "Where is..." → "Di mana..."                         │
// │  "How much?" → "Berapa?"                              │
// │                                                       │
// │  💱 SGD 100 = ₹6,240                                  │
// │                                                       │
// │  Reply "AGENT" to connect with Priya now               │
// │  Reply "SOS" for immediate agent callback              │
// └─────────────────────────────────────────────────────┘
```

---

## Open Problems

1. **PWA vs. WhatsApp-first** — Building a full PWA companion is expensive. WhatsApp-based companion (message + quick-reply buttons) may be more practical for India market.

2. **Location sharing battery drain** — Continuous GPS tracking drains battery. Check-in-based sharing (manual ping) or coarse location (city-level) is more battery-friendly.

3. **Offline access** — Travelers may not have data abroad. Critical info (hotel address, emergency numbers) must be available offline.

4. **Information overload** — Too many updates and reminders can annoy travelers. Need adaptive frequency based on trip phase (more during travel days, less during relaxation).

---

## Next Steps

- [ ] Build WhatsApp-first traveler companion with daily briefings
- [ ] Create real-time trip update system with pre-activity alerts
- [ ] Implement opt-in location sharing with privacy controls
- [ ] Design in-trip support tools with emergency quick-access
