# Crisis Communication Protocol — Agency Emergency Broadcast System

> Research document for crisis communication protocols, mass notification systems, traveler safety tracking, emergency coordination, and post-crisis recovery for the Waypoint OS platform.

---

## Key Questions

1. **How does the agency communicate with all active travelers during a crisis?**
2. **What crisis types require agency-initiated communication?**
3. **How are travelers tracked and verified safe during emergencies?**
4. **What is the post-crisis recovery protocol?**

---

## Research Areas

### Crisis Communication Architecture

```typescript
interface CrisisCommunicationProtocol {
  // Agency emergency broadcast and coordination system
  crisis_types: {
    NATURAL_DISASTER: {
      examples: ["Earthquake", "Tsunami warning", "Typhoon/cyclone", "Volcanic eruption", "Flooding"];
      severity_levels: {
        ADVISORY: "Information only — no immediate danger to travelers";
        WARNING: "Potential danger — advise caution and monitor";
        CRITICAL: "Active danger — initiate safety check and potential evacuation";
      };
      response_time: "Advisory: <2 hours · Warning: <30 minutes · Critical: immediate";
    };

    POLITICAL_UNREST: {
      examples: ["Civil unrest", "Government coup", "Terrorist incident", "Border closure", "Curfew"];
      severity_levels: {
        MONITOR: "Unrest in area not frequented by travelers";
        ALERT: "Unrest near traveler locations — advise shelter in place";
        EVACUATE: "Direct threat — coordinate immediate relocation or evacuation";
      };
      response_time: "Monitor: <4 hours · Alert: <1 hour · Evacuate: immediate";
    };

    HEALTH_EMERGENCY: {
      examples: ["Pandemic outbreak", "Disease epidemic", "Food/water contamination", "Medical emergency of traveler"];
      severity_levels: {
        INFORMATION: "Health advisory for destination (e.g., dengue outbreak)";
        PRECAUTION: "Specific health risk — advise preventive measures";
        EMERGENCY: "Traveler medical emergency — coordinate hospital and insurance";
      };
    };

    TRANSPORT_DISRUPTION: {
      examples: ["Flight cancellations (mass)", "Airport closure", "Strike (airline/rail)", "Severe weather delay"];
      severity_levels: {
        DELAY: "Individual flight delay — rebook and notify";
        DISRUPTION: "Multiple flights affected — mass rebooking required";
        SHUTDOWN: "Airport/airline shutdown — alternative arrangements for all affected travelers";
      };
    };

    SUPPLIER_FAILURE: {
      examples: ["Hotel bankruptcy/closure", "Airline ceases operations", "Tour operator insolvency"];
      response: "Immediate alternative booking for all affected travelers; legal and insurance coordination";
    };
  };

  // ── Crisis command center ──
  // ┌─────────────────────────────────────────────────────┐
  // │  🚨 Crisis Command Center · Typhoon Signal 3 · Hong Kong  │
  // │                                                       │
  // │  Active Travelers in Region: 12 families (34 pax)     │
  // │  Safety Status:                                       │
  // │  ✅ Confirmed Safe: 8 families (22 pax)                  │
  // │  ⏳ Awaiting Response: 3 families (9 pax)                │
  // │  ❌ Unreachable: 1 family (3 pax) — last: Hotel retry   │
  // │                                                       │
  // │  Actions Taken:                                       │
  // │  10:30 AM  Mass WhatsApp sent to all 12 families      │
  // │  10:45 AM  Hotel concierge contacted for 3 families    │
  // │  11:00 AM  Embassy helpline activated for unreachable  │
  // │  11:15 AM  Alternate departure flights researched      │
  // │                                                       │
  // │  Broadcast Queue:                                     │
  // │  [Send Safety Instructions]                              │
  // │  [Send Hotel Shelter Advisory]                           │
  // │  [Send Evacuation Instructions — if escalated]           │
  // │  [Send Rebooking Options]                                │
  // │                                                       │
  // │  Communication Log:                                   │
  // │  10:30  WhatsApp broadcast → 12 families                │
  // │  10:32  Patel family replied "Safe in hotel"             │
  // │  10:35  Sharma family replied "At airport, what do?"     │
  // │  10:40  Gupta family — no response · calling hotel       │
  // │                                                       │
  // │  [Escalate] [Contact Embassy] [Insurance Alert] [Log]    │
  // └─────────────────────────────────────────────────────────┘
}

### Emergency Broadcast System

```typescript
interface EmergencyBroadcastSystem {
  // Mass communication with active travelers
  broadcast_channels: {
    WHATSAPP_BROADCAST: {
      primary: "Main channel — highest open rate (95%+ within 5 minutes)";
      capabilities: {
        mass_message: "Same message to all travelers in affected region";
        personalized: "Per-traveler message with their specific hotel, flight, and instructions";
        rich_media: "Map with shelter locations, emergency contacts, QR code for helpline";
        two_way: "Travelers reply 'SAFE' or 'NEED HELP' — system tracks responses";
      };
    };

    SMS_FALLBACK: {
      backup: "If WhatsApp not delivered within 15 minutes, send SMS";
      use_case: "Travelers with no data/internet connection";
      format: "Short text with critical info and callback number";
    };

    PHONE_CALL: {
      escalation: "If no digital response within 30 minutes, call directly";
      priority: "Unreachable travelers called first; voicemail left with callback number";
    };

    APP_NOTIFICATION: {
      supplementary: "Push notification to companion app users";
      content: "Same message as WhatsApp, displayed prominently in emergency banner";
    };
  };

  message_templates: {
    SAFETY_CHECK: {
      trigger: "First message after crisis detected";
      template: `
        🚨 IMPORTANT — {crisis_type} in {destination}

        Your safety is our priority.

        Please reply:
        ✅ SAFE — if you're safe
        🆘 HELP — if you need assistance
        📍 LOCATION — your current location

        Emergency contacts:
        Agency: {emergency_number}
        Embassy: {embassy_number}
        Insurance: {insurance_helpline}

        Stay tuned for updates.
      `;
    };

    SHELTER_ADVISORY: {
      trigger: "Traveler needs to shelter or relocate";
      template: `
        🏠 SHELTER ADVISORY — {destination}

        Please move to your hotel and stay indoors.
        Do not travel to the airport until further notice.

        Your hotel {hotel_name} is aware of the situation.
        Address: {hotel_address} (show to taxi driver)

        If you need to leave your current location:
        Nearest shelter: {nearest_shelter} ({distance} away)

        We are monitoring the situation and will update you.
      `;
    };

    EVACUATION: {
      trigger: "Active evacuation required";
      template: `
        ⚠️ EVACUATION NOTICE — {destination}

        Please proceed to {evacuation_point} immediately.

        Transportation arranged:
        {pickup_time} — {vehicle_type} from {pickup_location}

        What to bring:
        Passport · Phone + charger · Medication · Cash

        What to leave: Luggage (will be collected later)

        Call {emergency_number} if you need help getting to pickup.
      `;
    };
  };
}
```

### Traveler Safety Tracking

```typescript
interface TravelerSafetyTracking {
  // Track and verify safety of all active travelers
  tracking_workflow: {
    STEP_1_DETECT: {
      description: "Detect crisis and identify affected travelers";
      sources: [
        "Government travel advisories (MEA India, destination government)",
        "News monitoring (Google Alerts, Reuters API)",
        "Weather services (typhoon, earthquake, tsunami alerts)",
        "Airline/airport disruption feeds",
        "Traveler incoming messages (customer reports issue first)",
      ];
      auto_detect: "System cross-references active trips with crisis location — immediate alert";
    };

    STEP_2_NOTIFY: {
      description: "Send safety check to all affected travelers";
      method: "WhatsApp broadcast → SMS fallback → phone call escalation";
      tracking: "Dashboard shows delivered/read/replied status per traveler";
    };

    STEP_3_TRACK: {
      description: "Track response status for each traveler";
      statuses: {
        CONFIRMED_SAFE: "Traveler replied SAFE or confirmed via hotel/airline";
        PENDING_RESPONSE: "Message delivered but no reply yet";
        MESSAGE_UNDELIVERED: "WhatsApp + SMS undelivered — trying phone call";
        NEEDS_HELP: "Traveler requested assistance — agent assigned";
        UNREACHABLE: "All channels attempted, no response — escalate to embassy";
      };
    };

    STEP_4_ASSIST: {
      description: "Provide assistance to travelers who need help";
      actions: [
        "Rebook flights for affected travelers",
        "Arrange hotel extensions or alternative accommodation",
        "Coordinate with insurance for medical or evacuation claims",
        "Contact embassy for unreachable travelers",
        "Arrange ground transportation from danger zone",
      ];
    };

    STEP_5_RECOVER: {
      description: "Post-crisis recovery and follow-up";
      actions: [
        "Verify all travelers are safe and accounted for",
        "Arrange modified itineraries or early returns",
        "Process insurance claims for affected travelers",
        "Post-crisis communication: summary + next steps",
        "Internal debrief: what worked, what didn't, process improvements",
      ];
    };
  };

  // ── Safety tracking status board ──
  // ┌─────────────────────────────────────────────────────┐
  // │  Safety Status · Hong Kong Typhoon · 34 travelers        │
  // │                                                       │
  // │  ✅ SAFE (22)            ⏳ PENDING (9)                  │
  // │  Patel · Grand Hyatt     Gupta · Kowloon Hotel          │
  // │  Mehta · Langham         Singh · Regal Airport          │
  // │  [20 more...]            [7 more...]                    │
  // │                                                       │
  // │  🆘 NEEDS HELP (0)       ❌ UNREACHABLE (3)              │
  // │  None                    Joshi family · last: Day 2     │
  // │                          → Hotel calling...              │
  // │                          → Embassy alerted               │
  // │                                                       │
  // │  Last update: 11:45 AM · Next check: 12:00 PM           │
  // │  [Refresh Status] [Call Unreachable] [Escalate All]       │
  // └─────────────────────────────────────────────────────────┘
}
```

### Post-Crisis Recovery

```typescript
interface PostCrisisRecovery {
  // Recovery operations after crisis resolves
  recovery_operations: {
    IMMEDIATE_RECOVERY: {
      timeframe: "0-48 hours after crisis";
      actions: [
        "Confirm 100% of travelers accounted for and safe",
        "Arrange modified itineraries for continuing travelers",
        "Process early returns for travelers wanting to cut trip short",
        "Handle insurance claims initiation",
        "Supplier negotiations for cancellations and refunds",
      ];
    };

    CUSTOMER_COMMUNICATION: {
      description: "Transparent communication about recovery options";
      options_presented: [
        "Continue trip with modified itinerary (no extra cost)",
        "Return early with partial refund + rebooking credit",
        "Postpone remaining trip to later date (credit for unused portion)",
        "Full cancellation if trip was severely impacted",
      ];
      tone: "Empathetic, transparent, no sales pressure — this is about trust, not revenue";
    };

    FINANCIAL_RECOVERY: {
      description: "Recoup costs through insurance and supplier negotiations";
      channels: [
        "Agency insurance (business interruption, professional indemnity)",
        "Customer travel insurance claims",
        "Supplier refunds and credits (airlines, hotels, activity providers)",
        "Force majeure clause invocation for cancellation waivers",
      ];
    };

    PROCESS_IMPROVEMENT: {
      description: "Post-crisis debrief and process improvement";
      review: [
        "How fast was crisis detected?",
        "How quickly were all travelers notified?",
        "Did the tracking system work reliably?",
        "Were message templates effective?",
        "What traveler needed help that we couldn't provide?",
        "What would we do differently next time?",
      ];
      output: "Updated crisis protocol with lessons learned";
    };
  };
}
```

---

## Open Problems

1. **False alarm fatigue** — Over-alerting on minor incidents causes agents and travelers to ignore warnings. Need calibrated severity assessment that only escalates genuine threats while monitoring low-risk situations passively.

2. **Data connectivity during crisis** — The travelers who most need help are often the ones with no internet. WhatsApp and app-based communication fails when cell towers are down. SMS and phone calls are essential fallbacks, but international SMS delivery is unreliable.

3. **Traveler self-reporting accuracy** — Travelers may not know their exact location, may say "SAFE" prematurely, or may panic and provide unclear information. GPS-based location sharing (with consent) provides more reliable data than self-reporting.

4. **Multi-agency coordination** — During major crises, the agency must coordinate with embassies, airlines, hotels, insurance companies, and local authorities. No single system manages all these touchpoints — the protocol needs clear escalation paths for each entity.

5. **Legal liability** — If the agency fails to warn travelers of a known risk, or gives incorrect shelter/evacuation advice, liability falls on the agency. Crisis communication must be factual, sourced from official channels, and avoid speculative advice.

---

## Next Steps

- [ ] Build crisis detection engine with travel advisory and news monitoring
- [ ] Create emergency broadcast system with WhatsApp/SMS/call escalation
- [ ] Implement traveler safety tracking dashboard with status management
- [ ] Design message templates for each crisis type and severity level
- [ ] Build post-crisis recovery workflow with insurance claim coordination
