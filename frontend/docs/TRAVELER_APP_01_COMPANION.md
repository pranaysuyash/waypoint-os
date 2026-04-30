# Traveler Companion App — Mobile Experience During Trip

> Research document for the customer-facing traveler companion mobile app, providing itinerary access, real-time maps, budget tracking, emergency contacts, in-trip chat with agent, and on-destination assistance for the Waypoint OS platform.

---

## Key Questions

1. **What does the traveler companion app provide during a trip?**
2. **How does real-time itinerary with maps work?**
3. **What in-trip communication features connect travelers with agents?**
4. **What offline capabilities are essential for traveling?**

---

## Research Areas

### Traveler Companion App Architecture

```typescript
interface TravelerCompanionApp {
  // Customer-facing mobile experience during travel
  app_model: {
    form_factor: "Progressive Web App (PWA) — no app store download required";
    access: "Link via WhatsApp or SMS; works in mobile browser; installable to home screen";
    auth: "Phone number OTP (no password to remember while traveling)";
    data_mode: "Online-first with offline fallback for essential features";
  };

  core_features: {
    TRIP_DASHBOARD: {
      description: "At-a-glance trip status on app launch";
      display: {
        current_day: "Day 3 of 5 · Singapore";
        today_schedule: "Morning: Gardens by the Bay · Afternoon: Sentosa · Evening: Free";
        next_upcoming: "Transfer to airport tomorrow at 10 AM";
        weather: "32°C · Partly cloudy · 20% rain chance";
        budget_status: "₹42K of ₹1.2L spent (35%)";
        emergency_card: "24/7 agent contact · Insurance helpline · Embassy number";
      };
    };

    DAY_BY_DAY_ITINERARY: {
      description: "Interactive day-by-day trip schedule";
      features: {
        timeline_view: "Vertical timeline with activities, meals, transfers, free time";
        detail_tap: "Tap activity → see address, time, confirmation number, notes";
        countdown: "Next activity in 45 minutes · Sentosa Express at 2:00 PM";
        mark_done: "Swipe to mark activities as completed";
        photos: "Attach photos to each activity → auto-compiled trip journal";
      };
    };

    INTERACTIVE_MAP: {
      description: "Map showing today's activities, hotel, and nearby points of interest";
      features: {
        activity_pins: "All today's activities pinned on map with walking/transit directions";
        hotel_pin: "Current hotel location with address and phone";
        nearby: "Restaurants, ATMs, pharmacies, hospitals within 1km";
        navigation: "Walking/transit directions from current location to next activity";
        offline_map: "Downloaded city map for offline use (no data needed)";
      };
    };

    BUDGET_TRACKER: {
      description: "Real-time spending tracker during trip";
      features: {
        quick_entry: "Tap + → enter amount → select category (meals, transport, shopping)";
        snap_receipt: "Camera to photo receipt → OCR extracts amount";
        daily_view: "Today: ₹3,200 of ₹5,000 daily budget";
        alerts: "Warning when daily or category budget exceeded";
        multi_currency: "Auto-convert SGD/THB/USD to INR using live rate";
      };
    };

    DOCUMENTS_WALLET: {
      description: "All travel documents accessible offline";
      contents: {
        hotel_vouchers: "QR code voucher for each hotel check-in";
        flight_tickets: "E-ticket with PNR and barcode for boarding";
        activity_confirmations: "Booking reference for each booked activity";
        insurance_certificate: "Policy number + emergency contact + claim process";
        passport_copy: "Encrypted copy of passport (accessible with biometric unlock)";
        visa_copy: "E-visa document for immigration";
      };
      offline: "All documents cached for offline access — no internet needed at check-in";
    };

    AGENT_CHAT: {
      description: "Direct WhatsApp-like chat with assigned travel agent";
      features: {
        quick_actions: ["My itinerary", "Payment status", "Weather today", "Emergency help"];
        photo_sharing: "Send photos of issues (wrong room, damaged item)";
        response_sla: "Premium: <30 min · Standard: <2 hours · Emergency: immediate";
        chat_history: "Full conversation history accessible during trip";
      };
    };

    EMERGENCY_CARD: {
      description: "Always-visible emergency information";
      contents: {
        agent_24_7: "Agency emergency number (tappable to call)";
        insurance_helpline: "Insurance company emergency line";
        nearest_hospital: "Google Maps link to nearest hospital";
        embassy: "Indian embassy/consulate contact for the destination";
        police: "Local emergency number (911 equivalent)";
        phrase_card: "Essential phrases in local language ('I need help', 'Hospital', 'Police')";
      };
      access: "Accessible from every screen via emergency button; works offline";
    };
  };
}

// ── Traveler companion app — home screen ──
// ┌─────────────────────────────────────────────────────┐
// │  🌏 Waypoint Travel · Singapore                            │
// │  Day 3 of 5 · Tuesday, Jun 17                              │
// │                                                       │
// │  ┌──────────────────────────────────────────────────┐ │
// │  │  🌤️ 32°C Partly Cloudy · 20% rain                   │ │
// │  │  Next: Lunch at Lau Pa Sat · 12:30 PM (in 45 min)    │ │
// │  └──────────────────────────────────────────────────┘ │
// │                                                       │
// │  Today's Schedule:                                    │
// │  ☑ Morning: Gardens by the Bay (completed)              │
// │  🔵 Now: Walking to Lau Pa Sat (12:30 PM lunch)        │
// │  ○ Afternoon: Sentosa Island (2:00 PM - 6:00 PM)       │
// │  ○ Evening: Free time / Rest                             │
// │  [View Full Itinerary] [Map View]                          │
// │                                                       │
// │  Quick Actions:                                       │
// │  💰 Budget: ₹3.2K / ₹5K today                            │
// │  📄 Documents: All cached offline ✅                      │
// │  💬 Chat with Priya (agent) · Last: 2h ago               │
// │                                                       │
// │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐       │
// │  │ 📋   │ │ 🗺️   │ │ 💰   │ │ 📄   │ │ 🚨   │       │
// │  │Trip  │ │Map   │ │Budget│ │Docs  │ │SOS   │       │
// │  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘       │
// └─────────────────────────────────────────────────────┘
```

### Offline Capabilities

```typescript
interface OfflineCapabilities {
  // Essential features that work without internet
  offline_priority: {
    CRITICAL_OFFLINE: {
      documents: "All vouchers, tickets, passport copy cached locally";
      emergency_card: "All emergency numbers + embassy info + hospital location";
      itinerary: "Full day-by-day itinerary with addresses and times";
      hotel_address: "Hotel address in local language (show to taxi driver)";
    };

    PARTIAL_OFFLINE: {
      map: "Pre-downloaded city map with activity pins (no live transit)";
      budget: "Log expenses offline → sync when connected";
      chat: "Queue messages → send when connected";
    };

    ONLINE_ONLY: {
      live_flight_tracking: "Real-time flight status requires internet";
      agent_chat_realtime: "Messages delivered when both online";
      weather_update: "Latest weather requires API call";
      nearby_search: "Restaurant/pharmacy search needs internet";
    };
  };

  sync_strategy: {
    on_reconnect: "When internet detected → sync queued expenses, send queued messages, refresh itinerary";
    conflict_resolution: "Offline changes (expense edits) take priority; server provides authoritative itinerary updates";
    bandwidth_aware: "On slow connections → text-only mode; skip image downloads; compress sync data";
  };
}

// ── Offline mode indicator ──
// ┌─────────────────────────────────────────────────────┐
// │  📵 Offline Mode · Limited features                      │
// │                                                       │
// │  ✅ Available:                                         │
// │  Itinerary · Documents · Emergency card · Budget log     │
// │  Hotel address · Cached city map                          │
// │                                                       │
// │  ⏳ Queued (sending when online):                       │
// │  3 expense entries · 1 chat message to agent              │
// │                                                       │
// │  ❌ Unavailable until online:                           │
// │  Live weather · Nearby search · Flight status             │
// │                                                       │
// │  [Try Reconnect]                                          │
// └─────────────────────────────────────────────────────┘
```

### In-Trip Photo Journal

```typescript
interface TripPhotoJournal {
  // Auto-compiled trip journal from photos and activities
  journal_features: {
    AUTO_COMPILE: {
      description: "Photos attached to activities automatically create a day-by-day journal";
      structure: {
        day_header: "Day 3 — Sentosa Island · June 17";
        activity_photos: "Gardens by the Bay (8 photos) → Sentosa (12 photos)";
        captions: "Auto-generated from activity names + dates";
      };
    };

    TRIP_SUMMARY: {
      description: "End-of-trip auto-generated summary";
      contents: {
        stats: "5 days · 3 cities · 15 activities · 87 photos";
        map_trace: "Route map showing all places visited";
        budget_summary: "Total spent: ₹1.18L of ₹1.2L budget";
        highlights: "Top 3 photos from each day";
      };
      share_options: ["Share with agent (for testimonial)", "Share on social media", "Download PDF"];
      agency_benefit: "Customer-shared trip journal = social proof marketing with agency branding";
    };
  };
}
```

---

## Open Problems

1. **App adoption without app store** — PWA avoids app store friction but many travelers don't know they can "install" a PWA. Need clear WhatsApp-based onboarding: "Tap this link → tap 'Add to Home Screen' → done."

2. **Offline map quality** — Downloaded offline maps are large (50-200MB per city). Travelers may have limited storage. Need to offer city-level selection and warn about storage before download.

3. **Battery drain** — Map features, GPS, and photo uploads drain battery during travel days when charging access is limited. Need aggressive battery optimization and offline-first defaults.

4. **Data roaming costs** — Indian travelers on international SIMs face ₹50-200/MB roaming charges. The app must be usable with minimal data: sync only on WiFi, compress all transfers, provide offline-first experience.

---

## Next Steps

- [ ] Build PWA shell with offline-first service worker architecture
- [ ] Create interactive day-by-day itinerary with map integration
- [ ] Implement documents wallet with encrypted offline storage
- [ ] Design in-trip chat interface with queued offline messages
- [ ] Build trip photo journal with auto-compilation
