# Travel Compliance Automation — Data Privacy & Traveler Protection

> Research document for India DPDP Act compliance, traveler data protection, consent management, and data subject rights automation for travel agencies.

---

## Key Questions

1. **How does the India DPDP Act apply to travel agencies?**
2. **What traveler data requires special handling?**
3. **How do we automate consent management?**
4. **What data subject rights must be supported?**

---

## Research Areas

### DPDP Act Compliance Framework

```typescript
interface DPDPCompliance {
  // Digital Personal Data Protection Act 2023 compliance
  data_categories: {
    // Sensitive personal data ( heightened protection)
    SENSITIVE: {
      types: [
        "Passport number",
        "Visa application data",
        "Financial information (bank statements for visa)",
        "Health data (vaccination records, medical conditions)",
        "Biometric data (fingerprints for visa)",
        "Children's data (under 18)",
      ];
      requirements: {
        explicit_consent: true;           // must be specific and informed
        purpose_limitation: true;         // can only use for stated purpose
        data_minimization: true;          // collect only what's needed
        storage_limitation: true;         // delete when purpose is served
        breach_notification: "72 hours";
      };
    };

    // General personal data
    GENERAL: {
      types: [
        "Name, address, contact information",
        "Travel preferences",
        "Trip history",
        "Communication records",
        "Payment information",
      ];
      requirements: {
        consent: true;                    // can be bundled
        purpose_limitation: true;
        retention_period: "7 years";      // tax compliance requirement
      };
    };

    // Derived/anonymized data
    DERIVED: {
      types: [
        "Travel analytics (anonymized)",
        "Destination popularity trends",
        "Customer segmentation (no PII)",
      ];
      requirements: {
        consent: false;                   // if properly anonymized
        anonymization_standard: "k-anonymity (k≥5)";
      };
    };
  };
}

// ── DPDP compliance dashboard ──
// ┌─────────────────────────────────────────────────────┐
// │  Data Privacy Compliance — DPDP Act                     │
// │                                                       │
// │  Overall compliance score: 87/100                      │
// │                                                       │
// │  ┌───────────────────────────────────────────────┐   │
// │  │ Category        │ Status     │ Score │ Action │   │
// │  │ ────────────────────────────────────────────  │   │
// │  │ Consent Mgmt    │ ✅ Active   │ 95/100│ None   │   │
// │  │ Data Inventory  │ ✅ Complete │ 92/100│ None   │   │
// │  │ Subject Rights  │ ⚠️ Partial  │ 78/100│ 2 gaps │   │
// │  │ Breach Response │ ✅ Ready    │ 90/100│ Test   │   │
// │  │ Vendor DPA      │ ⚠️ Pending  │ 72/100│ 4 DPA  │   │
// │  │ Retention       │ ⚠️ Partial  │ 80/100│ 3 pol. │   │
// │  │ Grievance Officer│ ✅ Active  │ 100   │ None   │   │
// │  └───────────────────────────────────────────────┘   │
// │                                                       │
// │  Actions needed:                                      │
// │  1. Data portability feature not yet implemented       │
// │  2. 4 vendor DPAs need renewal                        │
// │  3. Children's data consent flow needs update          │
// │                                                       │
// │  [Fix Issues] [Download Audit Report] [Schedule Review]│
// └─────────────────────────────────────────────────────┘
```

### Consent Management System

```typescript
interface ConsentManager {
  // Granular consent tracking
  consents: {
    traveler_id: string;
    consent_records: {
      purpose: string;                    // "Trip booking and management"
      data_types: string[];               // what data is collected
      consent_given: boolean;
      consent_date: string | null;
      consent_method: "WHATSAPP" | "APP" | "WEB_FORM" | "VERBAL";
      consent_version: string;            // version of consent text
      withdrawable: boolean;
      withdrawal_date: string | null;
      expiry_date: string | null;
    }[];

    // Purpose-specific consents
    purposes: {
      TRIP_MANAGEMENT: {
        description: "Process and manage your trip booking";
        data: ["Name", "Contact", "Passport", "Travel preferences", "Payment info"];
        required: true;
        consent_given: boolean;
      };

      VISA_PROCESSING: {
        description: "Submit visa application on your behalf";
        data: ["Passport", "Financial documents", "Employment details", "Photos"];
        required: true;
        consent_given: boolean;
      };

      MARKETING: {
        description: "Send travel deals and destination updates";
        data: ["Contact info", "Travel preferences"];
        required: false;
        consent_given: boolean;
      };

      PHOTO_MEMORY: {
        description: "Create memory products from trip photos";
        data: ["Trip photos", "AI-generated captions"];
        required: false;
        consent_given: boolean;
      };

      ANALYTICS: {
        description: "Use anonymized data for service improvement";
        data: ["Anonymized travel patterns"];
        required: false;
        consent_given: boolean;
      };

      THIRD_PARTY_SHARING: {
        description: "Share data with hotels, airlines for booking";
        data: ["Name", "Contact", "Travel dates"];
        required: true;                   // necessary for trip execution
        consent_given: boolean;
        recipients: string[];             // list of third parties
      };
    };
  };
}

// ── Consent collection flow ──
// ┌─────────────────────────────────────────────────────┐
// │  Consent Collection — WhatsApp Flow                     │
// │                                                       │
// │  Booking confirmation message:                         │
// │  ┌───────────────────────────────────────────────┐   │
// │  │  🎉 Your Singapore trip is confirmed!           │   │
// │  │                                               │   │
// │  │  Before we proceed, we need your consent        │   │
// │  │  for the following:                             │   │
// │  │                                               │   │
// │  │  ✅ Trip management (required)                  │   │
// │  │     Process booking, share with hotel/airline   │   │
// │  │                                               │   │
// │  │  ✅ Visa processing (required)                  │   │
// │  │     Submit application on your behalf           │   │
// │  │                                               │   │
// │  │  ☐ Travel deals & offers (optional)             │   │
// │  │     Receive promotions and destination updates  │   │
// │  │                                               │   │
// │  │  ☐ Trip memory products (optional)              │   │
// │  │     Create photo books and videos               │   │
// │  │                                               │   │
// │  │  Reply "ALL" to accept all, or "1,2" for        │   │
// │  │  required only.                                │   │
// │  │                                               │   │
// │  │  Privacy policy: [Link]                        │   │
// │  │  Grievance officer: privacy@waypointos.com      │   │
// │  └───────────────────────────────────────────────┘   │
// │                                                       │
// │  Customer replies: "ALL"                               │
// │  System: Consent recorded ✅ (timestamped, versioned)  │
// └─────────────────────────────────────────────────────┘
```

### Data Subject Rights Automation

```typescript
interface DataSubjectRights {
  // Automated handling of data subject requests
  request_types: {
    RIGHT_TO_ACCESS: {
      description: "Customer requests all their data";
      auto_action: [
        "Compile all data across systems (CRM, trips, documents, photos)",
        "Generate data export in machine-readable format",
        "Send via secure link with 7-day expiry",
      ];
      sla: "30 days";
    };

    RIGHT_TO_CORRECTION: {
      description: "Customer requests data correction";
      auto_action: [
        "Update data across all systems",
        "Notify downstream systems (hotels, airlines) if already shared",
        "Log correction for audit trail",
      ];
      sla: "7 days";
    };

    RIGHT_TO_ERASURE: {
      description: "Customer requests data deletion";
      complexity: "HIGH";
      checks_before_deletion: [
        "Are there active bookings? → Cannot delete",
        "Are there pending payments/refunds? → Cannot delete",
        "Tax/legal retention requirements? → Partial delete only",
        "Are there photos in shared albums? → Remove from individual, flag for group",
      ];
      deletion_scope: {
        delete_immediately: ["Marketing preferences", "Travel preferences", "Photos (individual)"];
        retain_until_legal_expiry: ["Booking records", "Financial records", "Tax invoices"];
        anonymize: ["Trip analytics", "Destination statistics"];
      };
      sla: "30 days";
    };

    RIGHT_TO_DATA_PORTABILITY: {
      description: "Customer requests data transfer to another service";
      auto_action: [
        "Export in standard format (JSON + CSV)",
        "Include: profile, trip history, preferences, documents",
        "Secure transfer link",
      ];
      sla: "15 days";
    };
  };
}

// ── Data subject request handling ──
// ┌─────────────────────────────────────────────────────┐
// │  Data Subject Request — #DSR-2026-042                   │
// │                                                       │
// │  Request: RIGHT_TO_ERASURE                             │
// │  Customer: Mehta family (TRV-2847)                     │
// │  Received: Apr 28, 2026 · SLA: May 28, 2026           │
// │                                                       │
// │  Deletion feasibility check:                           │
// │  ┌───────────────────────────────────────────────┐   │
// │  │ Data type          │ Can delete? │ Reason      │   │
// │  │ ────────────────────────────────────────────  │   │
// │  │ Profile & contacts │ ✅ Yes     │ No active trips│   │
// │  │ Travel preferences  │ ✅ Yes     │ No dependency │   │
// │  │ Marketing consent   │ ✅ Yes     │ Already opt-out│   │
// │  │ Trip photos (42)    │ ✅ Yes     │ Individual only│   │
// │  │ Trip history (3)    │ ⚠️ Anonymize│ Legal hold 2yr│   │
// │  │ Financial records   │ ❌ No      │ Tax retention │   │
// │  │ Booking records     │ ⚠️ Anonymize│ Tax retention │   │
// │  │ GST invoices (3)    │ ❌ No      │ Regulatory    │   │
// │  └───────────────────────────────────────────────┘   │
// │                                                       │
// │  Action plan:                                         │
// │  1. Delete profile, contacts, preferences (immediate) │
// │  2. Delete all 42 trip photos (24 hours)              │
// │  3. Anonymize trip history (remove name, keep stats)  │
// │  4. Retain financial/tax records until legal expiry    │
// │  5. Confirm deletion to customer                      │
// │                                                       │
// │  [Execute Deletion] [Review Plan] [Escalate to Legal]  │
// └─────────────────────────────────────────────────────┘
```

### Vendor Data Processing Agreements

```typescript
interface VendorDPA {
  // Track data processing agreements with vendors
  vendors: {
    vendor_name: string;
    vendor_type: "HOTEL" | "AIRLINE" | "DMC" | "PAYMENT_GATEWAY" | "INSURANCE" | "VISA_SERVICE" | "CLOUD_PROVIDER";
    data_shared: string[];
    dpa_status: "ACTIVE" | "EXPIRED" | "PENDING" | "NOT_NEEDED";
    dpa_expiry: string | null;
    data_residency: "INDIA" | "INTERNATIONAL";
    last_audit: string | null;
    breach_notification_sla: string;
  }[];
}

// ── Vendor DPA tracker ──
// ┌─────────────────────────────────────────────────────┐
// │  Vendor Data Processing Agreements                      │
// │                                                       │
// │  Active: 12 · Expiring: 2 · Missing: 1               │
// │                                                       │
// │  ┌───────────────────────────────────────────────┐   │
// │  │ Razorpay (Payment)        ✅ Active until Dec26│   │
// │  │ Data: Name, email, payment info                │   │
// │  │ Residency: India · Last audit: Jan 2026        │   │
// │  │                                               │   │
// │  │ Singapore DMC             ⚠️ Expires Jun 2026 │   │
// │  │ Data: Name, travel dates, hotel preferences    │   │
// │  │ Residency: Singapore · Last audit: Nov 2025    │   │
// │  │ [Renew DPA] [Contact Vendor]                    │   │
// │  │                                               │   │
// │  │ Cloud Storage (AWS)      ✅ Active until Mar27 │   │
// │  │ Data: All customer data (encrypted)            │   │
// │  │ Residency: India (ap-south-1) · DPA current    │   │
// │  │                                               │   │
// │  │ Thai Activity Provider   🔴 NO DPA ON FILE     │   │
// │  │ Data: Name, travel dates                       │   │
// │  │ Action: DPA must be signed before sharing data  │   │
// │  │ [Send DPA Template] [Block Data Sharing]        │   │
// │  └───────────────────────────────────────────────┘   │
// │                                                       │
// │  [Add Vendor] [Bulk Renew] [Audit Report]              │
// └─────────────────────────────────────────────────────┘
```

---

## Open Problems

1. **Cross-border data transfer** — Sharing traveler data with international hotels/DMCs may trigger cross-border data transfer restrictions under DPDP. Need standard contractual clauses.

2. **Consent withdrawal cascade** — Withdrawing consent for trip management mid-trip is impractical. Need tiered consent that distinguishes "ongoing trip" from "future marketing."

3. **Deletion vs. legal retention** — Tax laws require 7-year financial record retention. DPDP requires deletion on request. These conflict and need legal guidance on scope.

4. **Children's data** — Travel bookings for minors require parental consent. Age verification and parental consent flows add complexity.

---

## Next Steps

- [ ] Build consent management system with WhatsApp collection
- [ ] Create data subject rights automation (access, correction, erasure)
- [ ] Implement vendor DPA tracker with expiry alerts
- [ ] Design DPDP compliance dashboard with scoring
