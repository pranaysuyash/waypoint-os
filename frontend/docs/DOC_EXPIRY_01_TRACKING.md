# Travel Document Expiry Tracking — Passport, Visa & ID Monitor

> Research document for passport expiry tracking, visa validity monitoring, travel document expiry alerts, renewal reminders, and document readiness assessment for the Waypoint OS platform.

---

## Key Questions

1. **How do we track and alert on expiring travel documents?**
2. **What documents need monitoring for travel eligibility?**
3. **How do document expiry dates affect booking and trip planning?**
4. **What renewal workflows should the platform support?**

---

## Research Areas

### Document Expiry Tracking System

```typescript
interface DocumentExpiryTracking {
  // Monitoring travel document validity and triggering renewal actions
  tracked_documents: {
    PASSPORT: {
      fields: {
        passport_number: "e.g., J1234567";
        issuing_country: "India";
        issue_date: "2020-03-15";
        expiry_date: "2030-03-14";
        name_as_on_passport: "Must match booking name exactly";
        pages_remaining: "Estimated blank pages (visa stamps consume pages)";
      };
      validity_rules: {
        most_countries: "Passport must be valid for 6 months beyond travel dates";
        strict_countries: "Schengen zone requires 3 months beyond return date (effectively 6+ months)";
        some_countries: "Nepal, Bhutan — just valid passport, no minimum validity";
      };
      renewal_timeline: "Apply for renewal 1 year before expiry (Indian passport renewal takes 2-6 weeks)";
      alert_schedule: [
        "12 months before expiry: 'Consider renewing your passport this year'",
        "6 months before expiry: 'Passport validity running low — renewal recommended'",
        "3 months before expiry: 'URGENT: Renew passport before booking international travel'",
        "1 month before any trip where passport doesn't meet validity: 'This trip requires passport renewal first'",
      ];
    };

    VISA: {
      fields: {
        visa_type: "Tourist, Business, Transit, Student, Work";
        destination_country: "Country that issued the visa";
        visa_number: "Visa reference number";
        issue_date: "Date visa was granted";
        expiry_date: "Last date of validity";
        entries: "Single, Double, Multiple";
        entries_used: "How many entries consumed";
        duration_of_stay: "Maximum days per entry (e.g., 90 days for Schengen)";
      };
      validity_rules: {
        single_entry: "Used after one entry; needs new visa for next trip";
        multiple_entry: "Valid until expiry date or entries exhausted";
        evisa: "Many countries now offer e-visas — check if reusable or per-entry",
      };
      tracking_complexity: {
        schengen: "180-day rolling window — max 90 days in any 180-day period across all Schengen countries";
        us_visa: "10-year multiple entry but each stay max 6 months";
        uk_visa: "6-month or 2-year or 5-year tourist visa with max 180 days/year";
      };
      alert_schedule: [
        "30 days before visa expiry: 'Your UAE visa expires soon — renew if planning another trip'",
        "When booking trip requiring visa: Check if existing visa covers dates and entries",
        "Schengen day-count approaching 90: 'You've used 78 of 90 Schengen days'",
      ];
    };

    DRIVING_LICENSE: {
      relevance: "Needed for international self-drive trips (car rental requires International Driving Permit)";
      fields: {
        license_number: "Indian driving license number";
        expiry_date: "Indian DL expiry";
        idp_expiry: "International Driving Permit expiry (1 year validity)";
      };
      alert: "Alert if booking includes car rental and DL/IDP is expired or insufficient";
    };

    OTHER_DOCUMENTS: {
      documents: [
        "Aadhaar card (for domestic travel verification at some airports)",
        "Vaccination certificates (Yellow Fever for Africa, COVID for some destinations)",
        "Travel insurance policy (validity for trip dates)",
        "OCI/PIO cards (for NRI family members)",
        "Emigration clearance (ECNR/ECR status for certain countries and job categories)",
      ];
    };
  };

  // ── Document tracker — customer view ──
  // ┌─────────────────────────────────────────────────────┐
  // │  📋 My Travel Documents · Rahul Sharma                    │
  // │                                                       │
  // │  🛂 Passport:                                            │
  // │  · J1234567 · Valid until Mar 14, 2030                   │
  // │  · ✅ Valid for all upcoming trips                        │
  // │  · Pages remaining: ~30 (plenty)                         │
  // │                                                       │
  // │  🛫 Visas:                                                │
  // │  · 🇸🇬 Singapore Tourist · Multiple Entry                  │
  // │    Valid: Jan 2024 - Dec 2026 · ✅ Covers Oct trip       │
  // │  · 🇹🇭 Thailand Tourist · Single Entry                      │
  // │    ⚠️ USED · Need new visa for Feb trip                   │
  // │  · 🇦🇪 UAE Tourist · Multiple Entry                         │
  // │    Valid: Jun 2025 - Jun 2026 · ✅ Covers Dec trip       │
  // │                                                       │
  // │  🚗 Driving:                                              │
  // │  · Indian DL: Valid until 2028                           │
  // │  · IDP: Not issued · [Apply for IDP]                      │
  // │                                                       │
  // │  💉 Vaccinations:                                         │
  // │  · Yellow Fever: Not required for upcoming trips         │
  // │  · COVID: Booster due in Aug 2026                        │
  // │                                                       │
  // │  ⚠️ Action Items:                                         │
  // │  1. Thailand visa needed for Feb trip (apply by Jan)     │
  // │  2. IDP needed for Bali scooter rental                   │
  // │                                                       │
  // │  [Add Document] [Upload Passport Scan] [Set Reminders]    │
  // └─────────────────────────────────────────────────────────┘
}
```

### Booking & Document Integration

```typescript
interface BookingDocumentIntegration {
  // Checking document readiness at every stage of the booking lifecycle
  pre_booking_check: {
    AT_SEARCH: {
      description: "When customer searches for a destination, check document readiness";
      checks: [
        "Does passport have 6+ months validity for travel dates?",
        "Does customer have valid visa for destination (or visa-on-arrival eligible)?",
        "Is any vaccination required that customer doesn't have?",
      ];
      action_if_incomplete: "Show warning: 'Your passport expires before this trip — renew first' or 'You'll need a Thailand visa — we can help'";
    };

    AT_BOOKING: {
      description: "Block or warn at booking if documents are insufficient";
      rules: [
        "Passport validity insufficient → BLOCK booking (cannot travel)";
        "Visa not obtained → WARN (can apply after booking but before travel)";
        "Vaccination missing → WARN (can obtain but needs lead time)",
      ];
      override: "Agent can override warning with documented acknowledgment (customer aware of requirement)";
    };

    AT_TRIP_APPROACHING: {
      description: "Pre-trip document readiness check";
      timing: "30 days, 14 days, and 7 days before departure";
      checks: "All required documents valid and present?";
      escalation: "7 days before: If documents incomplete → urgent agent intervention";
    };
  };

  renewal_assistance: {
    PASSPORT_RENEWAL: {
      description: "Help customer renew passport in time for travel";
      services: [
        "Link to Passport Seva portal for online application",
        "Provide document checklist for renewal",
        "Suggest Tatkaal (expedited) option if time is short",
        "Update passport details in profile after renewal",
      ];
    };

    VISA_APPLICATION: {
      description: "Assist with visa application for upcoming trip";
      services: [
        "Determine visa type and requirements for destination",
        "Checklist of documents needed for visa application",
        "Link to embassy/consulate or visa processing partner",
        "Track application status (manual update by customer or agent)",
        "Update visa details in profile after approval",
      ];
    };
  };
}
```

---

## Open Problems

1. **OCR for document scanning** — Automatically extracting passport number and expiry date from a photo of the passport would reduce manual data entry. OCR accuracy for Indian passports (with varied fonts and layouts) is a technical challenge.

2. **Privacy of sensitive documents** — Passport numbers, visa details, and IDs are highly sensitive. Secure storage, encryption, and access controls are mandatory. Compliance with Indian data protection laws (DPDP Act) is required.

3. **Visa rule complexity** — Different countries have different validity rules, entry counts, rolling windows (Schengen 90/180 rule). Accurately determining visa eligibility for a specific trip date requires a comprehensive visa rules database.

4. **Family document management** — A family of 4 may have 4 passports, 8+ visas, 4 driving licenses. Managing and tracking expiry for all family members' documents is complex.

5. **Integration with government systems** — Checking real-time visa validity or passport status requires integration with government systems that may not have public APIs. Manual verification may be necessary.

---

## Next Steps

- [ ] Build document tracking system with passport, visa, DL, and vaccination monitoring
- [ ] Create expiry alert engine with configurable notification schedule
- [ ] Implement booking-document integration (pre-booking check, booking gate, pre-trip verification)
- [ ] Design document upload and OCR for automatic data extraction
- [ ] Build visa rules database for country-specific validity requirements
- [ ] Create renewal assistance workflow with links and checklists
- [ ] Implement family document management for multi-traveler profiles
