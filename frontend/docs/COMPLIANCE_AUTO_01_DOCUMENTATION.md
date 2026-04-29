# Travel Compliance Automation — Document & Visa Compliance

> Research document for automated document verification, visa compliance checking, travel document management, and regulatory tracking for travel agencies.

---

## Key Questions

1. **How do we automate travel document compliance checking?**
2. **What visa rules engine handles multi-destination compliance?**
3. **How do we manage document collection and verification?**
4. **What regulatory changes need automated monitoring?**

---

## Research Areas

### Travel Document Compliance Engine

```typescript
interface DocumentComplianceEngine {
  // Check all documents needed for a trip
  checkCompliance(params: {
    travelers: {
      nationality: string;               // "Indian"
      passport_number: string;
      passport_expiry: string;
      visa_status: Record<string, string>; // country → visa status
      age: number;
      occupation: string | null;
    }[];
    destinations: {
      country: string;
      entry_date: string;
      exit_date: string;
      purpose: "TOURISM" | "BUSINESS" | "TRANSIT";
    }[];
  }): ComplianceReport;
}

interface ComplianceReport {
  trip_id: string;
  overall_status: "COMPLIANT" | "ACTION_NEEDED" | "NON_COMPLIANT";

  // Per-traveler checks
  travelers: {
    name: string;
    status: "COMPLIANT" | "WARNING" | "BLOCKING";

    checks: {
      rule: string;                      // "Passport validity 6 months"
      status: "PASS" | "FAIL" | "WARNING" | "NOT_APPLICABLE";
      details: string;
      action_required: string | null;
      deadline: string | null;
      blocking: boolean;                 // prevents travel if FAIL
    }[];
  }[];

  // Destination-specific requirements
  destination_requirements: {
    country: string;
    documents_needed: {
      type: "PASSPORT" | "VISA" | "VACCINATION" | "INSURANCE" | "INVITATION" | "FINANCIAL_PROOF" | "RETURN_TICKET" | "HOTEL_BOOKING";
      description: string;
      specific_requirements: string;     // "Passport must have 2 blank pages"
      status: "COLLECTED" | "PENDING" | "NOT_NEEDED";
      collected_date: string | null;
    }[];
  }[];
}

// ── Compliance check result ──
// ┌─────────────────────────────────────────────────────┐
// │  Document Compliance — Sharma Singapore Trip            │
// │  4 travelers · Jun 1-6, 2026                          │
// │                                                       │
// │  Overall: ⚠️ ACTION NEEDED (2 issues)                 │
// │                                                       │
// │  Travelers:                                           │
// │  ┌───────────────────────────────────────────────┐   │
// │  │ Rajesh Sharma (Adult, Indian)        ✅ PASS   │   │
// │  │  ✅ Passport valid until Dec 2027              │   │
// │  │  ✅ Singapore e-visa approved (May 15)          │   │
// │  │  ✅ Travel insurance active                     │   │
// │  │                                               │   │
// │  │ Priya Sharma (Adult, Indian)         ✅ PASS   │   │
// │  │  ✅ Passport valid until Mar 2028              │   │
// │  │  ✅ Singapore e-visa approved (May 15)          │   │
// │  │  ✅ Travel insurance active                     │   │
// │  │                                               │   │
// │  │ Aarav Sharma (Child, 12, Indian)     ⚠️ WARN  │   │
// │  │  ✅ Passport valid until Sep 2027              │   │
// │  │  ⚠️ Singapore visa: APPLIED, pending approval  │   │
// │  │  ✅ Travel insurance active                     │   │
// │  │  Action: Follow up with visa agent by May 25    │   │
// │  │                                               │   │
// │  │ Anaya Sharma (Child, 8, Indian)      🔴 FAIL  │   │
// │  │  ✅ Singapore visa: approved                    │   │
// │  │  🔴 Passport expires Jul 15, 2026              │   │
// │  │     RULE: Need 6 months validity → expires      │   │
// │  │     within 6 months of travel date!             │   │
// │  │  ✅ Travel insurance active                     │   │
// │  │  Action: URGENT — Apply for passport renewal    │   │
// │  │  Tatkaal service: 1-3 weeks                     │   │
// │  │  Blocking: YES — cannot travel without renewal  │   │
// │  └───────────────────────────────────────────────┘   │
// │                                                       │
// │  [Send Reminders] [Generate Document Checklist]         │
// │  [Start Visa Applications] [Flag to Agent]             │
// └─────────────────────────────────────────────────────┘
```

### Visa Rules Engine

```typescript
interface VisaRulesEngine {
  // Multi-destination visa requirements
  checkVisaRequirements(params: {
    nationality: string;
    destinations: {
      country: string;
      stay_days: number;
      purpose: string;
      prev_visits: number;
    }[];
    travel_dates: { start: string; end: string };
  }): VisaRequirement[];
}

interface VisaRequirement {
  destination: string;
  visa_type: string;                     // "e-Visa", "Visa on Arrival", "Prior Visa"
  eligibility: "ELIGIBLE" | "CONDITIONAL" | "NOT_ELIGIBLE";

  // Application details
  application: {
    method: "ONLINE" | "EMBASSY" | "ON_ARRIVAL" | "NOT_REQUIRED";
    processing_time: string;             // "3-5 business days"
    cost: number;
    validity: string;                    // "30 days from issue"
    multiple_entry: boolean;
    documents_required: string[];
  };

  // Timeline
  timeline: {
    earliest_application: string;        // "30 days before travel"
    latest_application: string;          // "4 days before travel"
    recommended_apply_date: string;
    current_status: "NOT_STARTED" | "APPLIED" | "APPROVED" | "REJECTED";
  };

  // Warnings
  warnings: string[];                    // "Transit visa needed for layover in Bangkok"
}

// ── Visa requirements for multi-destination trip ──
// ┌─────────────────────────────────────────────────────┐
// │  Visa Requirements — Europe Trip (Schengen)             │
// │  Indian nationals · 12-day trip · Jul 1-12, 2026       │
// │  Destinations: France, Italy, Switzerland              │
// │                                                       │
// │  📋 Schengen Visa (covers all 3 countries)             │
// │  ┌───────────────────────────────────────────────┐   │
// │  │ Type: Schengen Tourist Visa (Category C)       │   │
// │  │ Validity: 90 days · Multiple entry             │   │
// │  │ Cost: ₹7,200 per applicant                    │   │
// │  │ Processing: 15-30 calendar days                │   │
// │  │                                               │   │
// │  │ Documents needed:                              │   │
// │  │  ✅ Passport (6 months + validity)             │   │
// │  │  ✅ 2 passport photos (35x45mm)                │   │
// │  │  ✅ Flight itinerary (round trip)               │   │
// │  │  ✅ Hotel bookings for all nights               │   │
// │  │  ✅ Travel insurance (€30K coverage min)        │   │
// │  │  ✅ Bank statements (3 months, min ₹3L balance)│   │
// │  │  ✅ Income tax returns (2 years)                │   │
// │  │  ✅ Employment letter / NOC from employer       │   │
// │  │  ☐ Cover letter (template provided)             │   │
// │  │  ☐ VFS appointment (book by Jun 1)              │   │
// │  │                                               │   │
// │  │ Application timeline:                          │   │
// │  │ Earliest apply: Jun 1 (30 days before)         │   │
// │  │ Latest apply: Jun 17 (15 days before)          │   │
// │  │ Recommended: Apply Jun 1-5 (safe buffer)       │   │
// │  │                                               │   │
// │  │ ⚠️ Warnings:                                   │   │
// │  │ • Switzerland is Schengen but NOT EU —          │   │
// │  │   confirm insurance covers non-EU Schengen      │   │
// │  │ • Fingerprints required at VFS (in person)      │   │
// │  │ • Minors need additional: birth certificate,    │   │
// │  │   parent consent letter (notarized)             │   │
// │  └───────────────────────────────────────────────┘   │
// │                                                       │
// │  Per-person cost: ₹7,200 × 4 = ₹28,800               │
// │  Application deadline: Jun 1, 2026                     │
// │                                                       │
// │  [Generate Document Checklist] [Book VFS Appointment]   │
// │  [Send Checklist to Customer] [Track Application]       │
// └─────────────────────────────────────────────────────┘
```

### Document Collection Workflow

```typescript
interface DocumentCollection {
  trip_id: string;

  // Collection tracking
  documents: {
    traveler_name: string;
    doc_type: string;
    status: "REQUESTED" | "UPLOADED" | "VERIFIED" | "REJECTED" | "EXPIRED";
    uploaded_at: string | null;
    verified_by: string | null;
    verified_at: string | null;
    rejection_reason: string | null;
    expiry_date: string | null;
    file_url: string | null;
  }[];

  // Automated reminders
  reminders: {
    pending_documents: string[];
    next_reminder_date: string;
    reminder_count: number;
    escalation: boolean;                  // escalate to agent after 3 reminders
  };
}

// ── Document collection tracker ──
// ┌─────────────────────────────────────────────────────┐
// │  Document Collection — Sharma Singapore                  │
// │  Deadline: May 15 (16 days remaining)                   │
// │                                                       │
// │  Overall: 8/12 documents collected (67%)               │
// │                                                       │
// │  Rajesh Sharma:                                       │
// │  ✅ Passport copy (verified)                           │
// │  ✅ Photo (verified)                                   │
// │  ✅ Bank statement (verified)                          │
// │                                                       │
// │  Priya Sharma:                                        │
// │  ✅ Passport copy (verified)                           │
// │  ✅ Photo (verified)                                   │
// │  ⚠️ Bank statement — uploaded but PENDING verification │
// │                                                       │
// │  Aarav Sharma (12):                                   │
// │  ✅ Passport copy (verified)                           │
// │  ✅ Photo (verified)                                   │
// │  ☐ Birth certificate — REQUESTED (reminder sent 2x)    │
// │  ☐ Parent consent letter — NOT YET REQUESTED           │
// │                                                       │
// │  Anaya Sharma (8):                                    │
// │  🔴 Passport — RENEWAL IN PROGRESS ( Tatkaal)          │
// │  ✅ Photo (verified)                                   │
// │  ☐ Birth certificate — REQUESTED (reminder sent 1x)    │
// │                                                       │
// │  Automated actions:                                   │
// │  • Send birth cert reminder to Aarav (3rd notice)      │
// │  • Request parent consent letter for both children      │
// │  • Track Anaya's passport renewal status                │
// │  • Flag trip if documents not ready by May 25           │
// │                                                       │
// │  [Send All Reminders] [Verify Pending] [Escalate]       │
// └─────────────────────────────────────────────────────┘
```

### Regulatory Change Monitor

```typescript
interface RegulatoryMonitor {
  // Track regulation changes that affect active trips
  monitors: {
    type: "VISA_RULE_CHANGE" | "HEALTH_REQUIREMENT" | "ENTRY_RULE" | "TAX_CHANGE" | "TRAVEL_ADVISORY";
    country: string;
    change: string;
    effective_date: string;
    source: string;
    affected_trips: string[];
    action_required: string;
  }[];
}

// ── Regulatory alerts ──
// ┌─────────────────────────────────────────────────────┐
// │  Regulatory Change Monitor — Active Alerts              │
// │                                                       │
// │  🔴 URGENT — Thailand Entry Rule Change                 │
// │  Effective: May 1, 2026                                │
// │  Change: Indian nationals now require e-Visa           │
// │          (previously visa on arrival)                   │
// │  Affected trips: 3 (WP-455, WP-461, WP-468)           │
// │  Action: Apply e-Visa for all 3 trips                  │
// │  [Apply for All] [Review Each] [Dismiss]                │
// │                                                       │
// │  ⚠️ INFO — Singapore GST Increase                      │
// │  Effective: Jul 1, 2026                                │
// │  Change: GST increasing from 8% to 9%                 │
// │  Affected trips: 2 (Jul-Aug travel)                    │
// │  Action: Update pricing for quoted trips               │
// │  [Update Pricing] [Dismiss]                             │
// │                                                       │
// │  ℹ️ INFO — EU ETIAS Launch                             │
// │  Effective: Q4 2026 (tentative)                        │
// │  Change: Electronic travel authorization required      │
// │          for Schengen visa-exempt nationals            │
// │  Affected trips: 0 currently (monitor for Q4 bookings) │
// │  Action: Add to compliance checks when active          │
// │  [Add to Rules Engine] [Dismiss]                        │
// └─────────────────────────────────────────────────────┘
```

---

## Open Problems

1. **Rule accuracy and timeliness** — Visa rules change frequently and vary by nationality. Maintaining an accurate, current rules database requires continuous monitoring of embassy/consulate updates.

2. **Document verification fraud** — Uploaded documents could be forged. Need verification against official databases where available (passport verification via Indian government API).

3. **Multi-nationality groups** — Group trips with travelers of different nationalities need per-person compliance checks. Rules engines must handle nationality × destination combinations.

4. **Regulatory change detection** — No single authoritative source for travel regulation changes. Need multiple source monitoring (embassy websites, IATA, travel advisories).

---

## Next Steps

- [ ] Build document compliance engine with per-traveler checks
- [ ] Create visa rules database for top 20 destinations from India
- [ ] Implement document collection workflow with automated reminders
- [ ] Design regulatory change monitor with trip impact analysis
