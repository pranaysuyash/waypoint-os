# Airport Experience Services — Lounge, Meet & Greet, FASTtrack

> Research document for airport experience services, lounge access booking, meet-and-greet services, FASTtrack/express security, airport transfers, and transit assistance for the Waypoint OS platform.

---

## Key Questions

1. **What premium airport services can the agency offer travelers?**
2. **How does meet-and-greet service work for families and first-timers?**
3. **What lounge access options are available for Indian airports?**
4. **How are airport experience services booked and delivered?**

---

## Research Areas

### Airport Experience Services

```typescript
interface AirportExperienceServices {
  // Premium airport services for travelers
  services: {
    MEET_AND_GREET: {
      description: "Personal airport assistant from curb to gate (departure) or gate to curb (arrival)";
      departure_service: {
        steps: [
          "Agent meets customer at terminal entrance (curbside)",
          "Assist with luggage trolley and check-in (queue bypass where available)",
          "Escort through security (FASTtrack lane where available)",
          "Guide to departure gate or lounge",
          "Provide boarding pass and gate information",
        ];
        ideal_for: "First-time international travelers, families with children, elderly travelers, VIPs";
        duration: "45-90 minutes from curb to gate";
      };
      arrival_service: {
        steps: [
          "Agent meets customer at arrival gate with name board",
          "Assist through immigration (dedicated counter where available)",
          "Help with baggage claim",
          "Escort to pre-arranged transfer vehicle",
          "Hand over welcome kit (SIM card, local currency, city map, emergency card)",
        ];
        welcome_kit: {
          contents: ["Local SIM card (pre-activated)", "City map with hotel marked", "Emergency contact card", "Local currency (₹2K-5K equivalent)", "Companion app QR code"];
          value: "Traveler has everything they need within 5 minutes of landing";
        };
        ideal_for: "All international travelers, especially first-timers and families";
      };
      pricing: {
        domestic: "₹500-1,500 per service (departure or arrival)";
        international: "₹1,500-4,000 per service";
        premium: "₹5,000-10,000 (VIP treatment, luxury transfer, personal concierge)";
      };
    };

    LOUNGE_ACCESS: {
      description: "Airport lounge booking for comfortable pre-flight wait";
      indian_airports: {
        tier_1: {
          airports: ["Delhi T3", "Mumbai T2", "Bangalore", "Hyderabad"];
          lounges: ["Priority Pass lounges", "Airline lounges (Air India, Vistara)", "Card-access lounges (HDFC, ICICI)"];
          price: "₹800-2,500 per visit (3-hour access)";
        };
        international: {
          airports: ["Singapore Changi", "Dubai International", "Bangkok Suvarnabhumi", "KL International"];
          lounges: ["Priority Pass network", "LoungeKey", "Airline business class lounges"];
          price: "₹1,500-5,000 per visit";
        };
      };
      inclusions: ["Comfortable seating", "Wi-Fi", "Food and beverages (complimentary)", "Shower facilities (select lounges)", "Quiet workspace"];
      booking: "Add to trip package during booking; or standalone booking via companion app";
      complimentary: "Premium/Elite tier customers get lounge access included in package";
    };

    FASTTRACK_SECURITY: {
      description: "Express lane through security and immigration";
      availability: {
        india: "Available at Delhi T3, Mumbai T2, Bangalore, Hyderabad (₹500-1,500)";
        international: "Available at most major international airports (₹1,000-3,000)";
      };
      benefit: "Skip 30-90 minute general queue → 5-15 minute FASTtrack lane";
      ideal_for: "Business travelers, families with children, elderly, tight connections";
    };

    AIRPORT_TRANSFER: {
      description: "Pre-arranged ground transport from airport to hotel and back";
      options: {
        shared_shuttle: "Shared vehicle, multiple stops, budget-friendly (₹500-1,500)";
        private_sedan: "Private car (Toyota Camry equivalent), direct to hotel (₹1,500-4,000)";
        private_van: "Toyota Innova/Commuter for families/groups (₹2,500-6,000)";
        luxury: "Mercedes/BMW, complimentary water and WiFi (₹5,000-15,000)";
      };
      features: {
        driver_details: "Driver name, phone, vehicle number shared 24 hours before via WhatsApp";
        tracking: "Live vehicle tracking on companion app from pickup to drop-off";
        waiting: "60-minute free waiting after landing (flight delays happen); ₹200/15 min after";
        child_seat: "Available on request (mandatory in some countries); pre-booked",
      };
    };

    TRANSIT_ASSISTANCE: {
      description: "Help during connecting flights and layovers";
      services: {
        connection escort: "Agent meets at arrival gate → escorts to departure gate";
        layover_tour: "4-8 hour layover → city tour with return to airport (available in Dubai, Singapore, Doha)";
        hotel_day_use: "Day-use hotel room during long layover (6+ hours)";
        lounge_access: "Lounge during layover for shower and rest",
      };
    };
  };

  // ── Airport experience — booking card ──
  // ┌─────────────────────────────────────────────────────┐
  // │  ✈️ Airport Experience · Singapore Trip                    │
  // │                                                       │
  // │  Departure (Delhi → Singapore):                       │
  // │  ☐ Meet & Greet at DEL T3 · ₹1,800                       │
  // │  ☐ FASTtrack Security · ₹1,200                           │
  // │  ☐ Lounge Access (3 hours) · ₹2,000                      │
  // │                                                       │
  // │  Arrival (Singapore Changi):                          │
  // │  ☑ Meet & Greet at Changi · ₹2,500 ✅                     │
  // │     → Welcome kit with SIM, map, emergency card           │
  // │  ☑ Private transfer to hotel · ₹3,200 ✅                  │
  // │     → Toyota Commuter (family of 3 + luggage)             │
  // │     → Driver details sent June 14 evening                 │
  // │                                                       │
  // │  Return (Singapore → Delhi):                          │
  // │  ☑ Hotel pickup · ₹3,200 ✅                                │
  // │  ☐ Changi Lounge · ₹2,500                                 │
  // │  ☐ FASTtrack Immigration · ₹1,500                        │
  // │                                                       │
  // │  Total airport services: ₹11,900                          │
  // │  [Add Services] [Modify] [Confirm]                         │
  // └─────────────────────────────────────────────────────────┘
}
```

### Booking & Delivery Integration

```typescript
interface AirportBookingDelivery {
  // How airport services are booked and delivered
  booking_integration: {
    TRIP_BOOKING_FLOW: {
      timing: "Offered as add-ons during trip booking process";
      presentation: "'Customize your airport experience' card after flight + hotel selection";
      bundling: "Premium packages include meet-and-greet + lounge + transfer as standard";
    };

    POST_BOOKING_ADDON: {
      timing: "Available to add anytime before departure via companion app or WhatsApp";
      trigger: "Companion app shows airport services section 14 days before departure";
    };

    COMPANION_APP: {
      features: [
        "View all booked airport services with times and locations",
        "Driver details and live tracking for transfers",
        "Lounge access QR code for scan-at-entry",
        "Meet-and-greet agent photo and contact number",
        "Airport map with meeting point highlighted",
      ];
    };
  };

  delivery_coordination: {
    SUPPLIER_NETWORK: {
      providers: ["Airport concierge companies", "Transfer companies (local at each destination)", "Lounge networks (Priority Pass, LoungeKey)"];
      management: "Agency maintains supplier relationships; booking confirmed 48 hours before departure";
    };

    REAL_TIME_UPDATES: {
      flight_delay: "System detects flight delay → auto-notifies transfer driver and meet-and-greet agent with new arrival time";
      gate_change: "Companion app pushes gate change notification with walking time to new gate";
    };
  };
}
```

---

## Open Problems

1. **Airport-specific availability** — Services vary significantly by airport. Not all Indian airports have FASTtrack, and lounge quality varies widely. Need accurate, airport-specific service catalogs.

2. **Third-party coordination** — Meet-and-greet requires local airport staff (not agency employees). Managing quality across 50+ airports with local partners is operationally complex.

3. **Price sensitivity** — Indian leisure travelers may see airport services as unnecessary expenses. Bundling into premium packages (where the cost is absorbed) works better than standalone upsell.

4. **Flight delay cascades** — A 3-hour flight delay cascades through all airport services (driver waits, lounge booking expires, meet-and-greet reschedules). Real-time flight tracking with automatic re-coordination is essential.

5. **Lounge access card fragmentation** — Some lounges accept Priority Pass, others only credit card access, others require airline status. Helping customers navigate which lounges they can access is complicated.

---

## Next Steps

- [ ] Build airport services catalog with airport-specific offerings
- [ ] Create airport experience booking flow integrated with trip booking
- [ ] Implement meet-and-greet coordination with local supplier network
- [ ] Design lounge access booking with Priority Pass and card-based access
- [ ] Build real-time flight tracking with automatic service re-coordination
