# Trip Control Room — Real-Time Trip Monitoring

> Research document for the real-time trip monitoring dashboard, active trip health scoring, traveler tracking, and disruption detection for travel agencies.

---

## Key Questions

1. **How do we monitor all active trips in real-time?**
2. **What health scoring signals indicate trip problems?**
3. **How do we detect disruptions before they impact travelers?**
4. **What does the operations team see on the control room dashboard?**

---

## Research Areas

### Trip Control Room Dashboard

```typescript
interface TripControlRoom {
  // Real-time overview of all active trips
  overview: {
    active_trips: number;                // trips currently in progress
    travelers_in_transit: number;
    trips_healthy: number;
    trips_with_warnings: number;
    trips_with_issues: number;
    unresolved_alerts: number;
  };

  // Trip health cards
  active_trips: {
    trip_id: string;
    destination: string;
    agent: string;
    travelers: number;

    // Status indicators
    status: "ON_TRACK" | "MINOR_ISSUE" | "MAJOR_ISSUE" | "EMERGENCY";
    health_score: number;                // 0-100

    // Current position in itinerary
    current_day: number;
    current_activity: string;
    next_milestone: string;

    // Live signals
    flight_status: "ON_TIME" | "DELAYED" | "CANCELLED" | "LANDED" | null;
    hotel_check_in: "CONFIRMED" | "PENDING" | "ISSUE" | null;
    last_traveler_contact: string;       // "2 hours ago"
    unresolved_issues: number;
  }[];
}

// ── Control room dashboard ──
// ┌─────────────────────────────────────────────────────┐
// │  Trip Control Room — Live Operations                    │
// │  April 29, 2026 · 3:45 PM IST                          │
// │                                                       │
// │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐               │
// │  │  14  │ │  52  │ │  12  │ │   2  │               │
// │  │Active│ │Travel│ │On    │ │Issues│               │
// │  │Trips │  │ers  │ │Track │ │     │               │
// │  │      │ │     │ │     │ │     │               │
// │  └──────┘ └──────┘ └──────┘ └──────┘               │
// │                                                       │
// │  🔴 EMERGENCY (0)  🟡 WARNINGS (2)  ✅ HEALTHY (12)  │
// │                                                       │
// │  ┌─ Trips Needing Attention ──────────────────────┐  │
// │  │                                                 │  │
// │  │  🟡 WP-442 Sharma · Singapore · Day 3/5        │  │
// │  │  Agent: Priya · 4 travelers                     │  │
// │  │  ⚠️ Universal Studios: OVERCROWDED (wait 90min) │  │
// │  │  Activity ends 5 PM, backup: Night Safari       │  │
// │  │  [Contact Agent] [View Itinerary] [Suggest Alt]  │  │
// │  │                                                 │  │
// │  │  🟡 WP-455 Patel · Dubai · Day 1/4              │  │
// │  │  Agent: Rahul · 2 travelers                     │  │
// │  │  ⚠️ Flight DELAYED by 2 hours (IndiGo 6E-87)    │  │
// │  │  New arrival: 11:30 PM · Hotel notified         │  │
// │  │  [Contact Traveler] [Track Flight] [Update Plan] │  │
// │  └─────────────────────────────────────────────────┘  │
// │                                                       │
// │  [View All Trips] [Map View] [Filter by Alert Level]   │
// └─────────────────────────────────────────────────────┘
```

### Trip Health Scoring

```typescript
interface TripHealthScore {
  trip_id: string;
  score: number;                          // 0-100
  grade: "A" | "B" | "C" | "D" | "F";

  // Score components
  components: {
    itinerary_adherence: {
      weight: 25;
      score: number;
      signals: {
        activities_completed_on_time: boolean;
        meals_as_planned: boolean;
        transfers_on_schedule: boolean;
        skipped_activities: number;
      };
    };

    traveler_satisfaction: {
      weight: 25;
      score: number;
      signals: {
        last_checkin_sentiment: "POSITIVE" | "NEUTRAL" | "NEGATIVE" | null;
        complaints_received: number;
        messages_to_agent: number;        // high volume may indicate issues
        nps_if_collected: number | null;
      };
    };

    supplier_reliability: {
      weight: 20;
      score: number;
      signals: {
        hotel_issues: number;
        transport_issues: number;
        activity_issues: number;
        supplier_cancellations: number;
      };
    };

    logistics_health: {
      weight: 20;
      score: number;
      signals: {
        flights_on_time: boolean;
        weather_conditions: "FAVORABLE" | "MODERATE" | "ADVERSE";
        visa_documents_valid: boolean;
        payment_status: "PAID" | "PARTIAL" | "PENDING";
      };
    };

    communication_health: {
      weight: 10;
      score: number;
      signals: {
        agent_response_time_hours: number;
        traveler_response_rate: number;   // % of check-ins responded to
        last_contact_hours_ago: number;
        escalation_count: number;
      };
    };
  };

  // Trend
  trend: "IMPROVING" | "STABLE" | "DECLINING";
  previous_score: number;
}

// ── Trip health score detail ──
// ┌─────────────────────────────────────────────────────┐
// │  Trip Health — WP-442 Sharma Singapore                  │
// │  Day 3 of 5 · Score: 78/100 (B) · Trend: ↓ Declining  │
// │                                                       │
// │  Itinerary Adherence:   ████████████████░░░ 82/100    │
// │  • Day 1: ✅ All activities completed                 │
// │  • Day 2: ✅ All activities completed                 │
// │  • Day 3: ⚠️ Universal Studios overcrowded (skipped)  │
// │  • Skipped 1 of 8 planned activities                  │
// │                                                       │
// │  Traveler Satisfaction: ██████████████░░░░ 72/100      │
// │  • Check-in sentiment: Neutral                        │
// │  • Complaints: 1 (restaurant quality)                  │
// │  • Messages to agent: 4 (above normal for day 3)      │
// │  • Suggested action: Proactive outreach               │
// │                                                       │
// │  Supplier Reliability:  ████████████████████ 90/100    │
// │  • Hotel: No issues                                    │
// │  • Transport: No issues                                │
// │  • Activities: 1 overcrowding issue                    │
// │                                                       │
// │  Logistics Health:     ████████████████████ 95/100     │
// │  • Flights: Landed on time                             │
// │  • Weather: Moderate (afternoon showers)               │
// │  • Documents: All valid                                │
// │  • Payment: Fully paid                                 │
// │                                                       │
// │  Communication Health: ██████████░░░░░░░░░ 60/100      │
// │  • Agent response: 4 hours (SLA: 2 hours)             │
// │  • Traveler response: 50% check-ins answered           │
// │  • Last contact: 4 hours ago                           │
// │                                                       │
// │  Score dropped from 85 → 78 due to:                    │
// │  1. Activity skipped (itinerary adherence -3)          │
// │  2. Agent response time (communication -4)             │
// │                                                       │
// │  [Contact Agent] [Auto-Alert Agent] [View Full Log]     │
// └─────────────────────────────────────────────────────┘
```

### Disruption Detection Engine

```typescript
interface DisruptionDetector {
  // Proactive disruption detection
  sources: {
    FLIGHT_TRACKING: {
      provider: "FlightAware | FlightStats | Cirium";
      events: ["DELAY_30MIN", "DELAY_2HOUR", "CANCELLED", "DIVERTED", "GATE_CHANGE"];
      check_frequency: "POLLING_15MIN";
      affected_trips: "Trips with flights in next 24h or currently in transit";
    };

    WEATHER: {
      provider: "OpenWeather | WeatherAPI";
      events: ["RAIN", "STORM", "EXTREME_HEAT", "EXTREME_COLD", "CYCLONE_WARNING"];
      thresholds: {
        rain_mm_per_hour: 10;
        temperature_high: 40;             // Celsius
        temperature_low: 5;
        wind_speed_kmh: 50;
      };
      check_frequency: "POLLING_1HOUR";
    };

    TRAVEL_ADVISORY: {
      provider: "MEA India | WHO | State Department";
      events: ["HEALTH_ADVISORY", "SECURITY_ALERT", "NATURAL_DISASTER", "CIVIL_UNREST"];
      check_frequency: "PUSH_BASED";
    };

    SUPPLIER_ALERTS: {
      provider: "Direct API or email parsing";
      events: ["OVERBOOKED", "CLOSED", "SERVICE_DISRUPTION", "STRIKE"];
      check_frequency: "PUSH_BASED";
    };
  };

  // Disruption response protocols
  response_protocols: {
    severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
    auto_actions: string[];
    agent_notification: string;
    escalation_path: string[];
    customer_communication_template: string;
    sla_minutes: number;
  }[];
}

// ── Disruption detection alert ──
// ┌─────────────────────────────────────────────────────┐
// │  🔴 DISRUPTION DETECTED — Flight Delay                 │
// │                                                       │
// │  Trip: WP-455 Patel · Dubai                           │
// │  Flight: IndiGo 6E-87 · DEL → DXB                    │
// │  Scheduled: 8:30 PM · Now: 10:30 PM (+2h)            │
// │  Reason: Late arriving aircraft                       │
// │                                                       │
// │  Impact:                                              │
// │  • Arrival delayed to 11:30 PM IST                    │
// │  • Hotel check-in: JW Marriott (notified ✅)          │
// │  • Transfer driver: Al Fazal (needs update ⚠️)        │
// │  • Tomorrow's activity: Burj Khalifa 10 AM (no impact)│
// │                                                       │
// │  Auto-actions taken:                                  │
// │  ✅ Hotel notified of late check-in                   │
// │  ✅ Agent Priya alerted via WhatsApp                  │
// │                                                       │
// │  Pending agent actions:                               │
// │  ⬜ Update transfer driver timing                     │
// │  ⬜ Send update to Patel family                       │
// │  ⬜ Adjust tomorrow's wake-up time if needed          │
// │                                                       │
// │  [Contact Traveler] [Auto-Notify Transfer]              │
// │  [View Updated Timeline] [Acknowledge]                  │
// └─────────────────────────────────────────────────────┘
```

### Traveler Check-In System

```typescript
interface TravelerCheckIn {
  trip_id: string;

  // Automated check-in schedule
  schedule: {
    trigger: string;                     // "Daily at 8 PM local time"
    method: "WHATSAPP" | "APP_PUSH" | "SMS";
    message_template: string;            // "How was your day in {city}? 😊"
    response_timeout_hours: number;      // 12 hours before escalation
  };

  // Check-in response analysis
  responses: {
    date: string;
    traveler_response: string;
    sentiment: "POSITIVE" | "NEUTRAL" | "NEGATIVE";
    issues_detected: string[];
    agent_action: string | null;
  }[];
}

// ── Automated daily check-in ──
// ┌─────────────────────────────────────────────────────┐
// │  Daily Check-In — Sharma Singapore (Day 3)              │
// │                                                       │
// │  Sent: 8:00 PM SGT · Auto-generated                   │
// │                                                       │
// │  To: Rajesh Sharma (WhatsApp)                          │
// │  ┌───────────────────────────────────────────────┐   │
// │  │ "Good evening, Sharma ji! 🌙                   │   │
// │  │  How was Day 3 in Singapore?                   │   │
// │  │                                               │   │
// │  │  Quick check-in:                              │   │
// │  │  😊 Great  😐 Okay  😞 Had issues             │   │
// │  │                                               │   │
// │  │  Need anything for tomorrow's plans?"          │   │
// │  └───────────────────────────────────────────────┘   │
// │                                                       │
// │  Response: 😐 Okay                                    │
// │  Follow-up: "Universal Studios was too crowded,       │
// │  couldn't do most rides. Kids were disappointed."      │
// │                                                       │
// │  Sentiment: NEUTRAL with negative undertone            │
// │  Issues detected: Activity overcrowding                │
// │  Impact on health score: -7 points                    │
// │                                                       │
// │  Suggested agent response:                             │
// │  "Sorry to hear that, Sharma ji! Let me arrange       │
// │   VIP access for Universal tomorrow OR switch to       │
// │   Adventure Cove Waterpark instead. What do you        │
// │   prefer?"                                             │
// │                                                       │
// │  [Send Suggested] [Custom Response] [Escalate]          │
// └─────────────────────────────────────────────────────┘
```

---

## Open Problems

1. **Traveler privacy in tracking** — Real-time location tracking raises privacy concerns. Need opt-in consent with clear disclosure about what's tracked and why.

2. **Alert fatigue for agents** — Too many low-severity alerts desensitize agents. Need intelligent filtering that only surfaces actionable alerts.

3. **Check-in response fatigue** — Daily check-ins may annoy travelers. Need adaptive frequency (more during issues, less when healthy) and opt-out options.

4. **Data source reliability** — Flight tracking, weather, and supplier APIs have varying reliability. Need fallback sources and confidence scoring on disruption data.

---

## Next Steps

- [ ] Build trip control room dashboard with real-time health scoring
- [ ] Create disruption detection engine with multi-source monitoring
- [ ] Implement automated traveler check-in with sentiment analysis
- [ ] Design alert routing with severity-based escalation
