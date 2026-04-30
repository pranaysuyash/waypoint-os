# Legal & Compliance Templates — Indian Travel Law

> Research document for Indian travel agency legal requirements, booking terms and conditions, cancellation policies, liability frameworks, consumer protection compliance, and legal document templates for the Waypoint OS platform.

---

## Key Questions

1. **What legal documents does an Indian travel agency need?**
2. **What are the mandatory booking terms and cancellation policies?**
3. **What liability does a travel agency carry?**
4. **How do consumer protection laws affect travel agencies?**

---

## Research Areas

### Legal Document Requirements

```typescript
interface LegalDocumentRequirements {
  // Legal documents every Indian travel agency needs
  required_documents: {
    BUSINESS_REGISTRATION: {
      types: {
        proprietorship: "GST registration + Shop & Establishment license";
        partnership: "Partnership deed + GST + PAN of firm";
        private_limited: "MOA + AOA + GST + PAN + TAN + ROC filing";
      };
      travel_specific: {
        iata_accreditation: "Optional but needed for direct airline ticketing";
        taai_membership: "Travel Agents Association of India — voluntary but adds credibility";
        state_tourism_registration: "Some states require registration with tourism department";
      };
    };

    CUSTOMER_FACING_DOCUMENTS: {
      BOOKING_TERMS_CONDITIONS: {
        required: "Must be shared with customer at booking time";
        contents: ["Services included and excluded", "Payment terms and schedule", "Cancellation and refund policy", "Liability limitations", "Dispute resolution mechanism", "Governing law jurisdiction"];
        format: "PDF + link in booking confirmation email/WhatsApp";
        update_frequency: "Annual review or when regulations change";
      };

      INVOICE_RECEIPT: {
        required: "Mandatory for every transaction under GST law";
        contents: ["Agency GSTIN", "Customer name and GSTIN (if applicable)", "Invoice number (sequential)", "Service description", "HSN/SAC codes", "Tax breakup (CGST + SGST/IGST)", "TCS collection (if international package)"];
        format: "PDF generated from system";
        storage: "Retain for 6 years per GST law";
      };

      TRAVEL_VOUCHER: {
        required: "Confirmation document for each booked service";
        types: ["Hotel voucher (confirmation number, dates, room type)", "Flight ticket (PNR, e-ticket number)", "Activity voucher (booking reference, date, time)", "Transfer voucher (pickup details, driver contact)"];
        format: "PDF with QR code for supplier verification";
      };

      INSURANCE_CERTIFICATE: {
        required: "If insurance sold, must provide policy certificate";
        contents: ["Policy number", "Coverage details", "Emergency contact", "Claim process"];
        provider: "Insurance company issues; agency delivers to customer";
      };
    };

    INTERNAL_DOCUMENTS: {
      SUPPLIER_CONTRACT: {
        required: "Written agreement with every supplier";
        contents: ["Rate agreement and validity", "Cancellation terms", "Payment terms", "Service quality standards", "Liability and indemnification"];
      };

      EMPLOYEE_AGREEMENT: {
        required: "Employment contract for all agents";
        contents: ["Role and responsibilities", "Compensation structure", "Non-compete clause", "Data confidentiality", "Customer data handling policy"];
      };

      PRIVACY_POLICY: {
        required: "Mandatory under DPDP Act for collecting personal data";
        contents: ["Data collected and purpose", "Data storage and security", "Third-party sharing", "Data subject rights", "Contact for privacy queries"];
        format: "Website page + link in all customer communications";
      };
    };
  };
}

// ── Legal compliance checklist ──
// ┌─────────────────────────────────────────────────────┐
// │  Legal Compliance — Document Checklist                     │
// │                                                       │
// │  Business Registration:                               │
// │  ✅ GST Registration (27AABCU9603R1ZM)                    │
// │  ✅ Shop & Establishment License (MH-2024-12345)          │
// │  ✅ PAN Card (AABCU9603R)                                 │
// │  ☐ IATA Accreditation (not yet applied)                  │
// │  ✅ TAAI Membership (active until Dec 2026)               │
// │                                                       │
// │  Customer Documents:                                  │
// │  ✅ Booking T&C (v3.2 · Last updated: Jan 2026)          │
// │  ✅ Invoice template (GST-compliant)                      │
// │  ✅ Travel voucher template                               │
// │  ✅ Cancellation policy (v2.1 · Updated: Mar 2026)        │
// │  ⚠️ Privacy policy (needs DPDP Act 2023 update)          │
// │  ☐ Refund policy (draft stage)                           │
// │                                                       │
// │  Internal Documents:                                  │
// │  ✅ Supplier contracts (12 of 15 signed)                  │
// │  ✅ Employee agreements (4 of 4 signed)                   │
// │  ⚠️ Data handling policy (needs DPDP update)              │
// │  ☐ Incident response plan (not created)                  │
// │                                                       │
// │  Compliance Deadlines:                                │
// │  🔴 GST return: Due May 11 (11 days)                      │
// │  🟡 TCS return: Due Jun 7 (38 days)                       │
// │  🟢 Annual ROC filing: Due Sep 30 (153 days)              │
// │                                                       │
// │  [Update Document] [Compliance Report] [Legal Review]     │
// └─────────────────────────────────────────────────────┘
```

### Booking Terms & Cancellation Framework

```typescript
interface BookingTermsCancellation {
  // Standard booking terms and cancellation policies
  cancellation_tiers: {
    INTERNATIONAL_PACKAGES: {
      more_than_45_days: "Full refund minus ₹2,000 processing fee";
      days_30_to_45: "75% refund (25% cancellation charge)";
      days_15_to_29: "50% refund (50% cancellation charge)";
      days_7_to_14: "25% refund (75% cancellation charge)";
      less_than_7_days: "No refund (100% cancellation charge)";
      airline_tickets: "Subject to airline cancellation policy (varies by fare type)";
      hotel_only: "Depends on hotel cancellation terms (free cancellation usually 48-72h before)";
    };

    DOMESTIC_PACKAGES: {
      more_than_30_days: "Full refund minus ₹1,000 processing fee";
      days_15_to_30: "75% refund";
      days_7_to_14: "50% refund";
      less_than_7_days: "No refund";
    };

    FORCE_MAJEURE: {
      definition: "Natural disaster, pandemic, government travel ban, war, civil unrest";
      policy: "Full refund minus non-recoverable costs (airline cancellation fees, visa fees)";
      documentation: "Customer must submit cancellation request within 7 days of force majeure event";
      insurance: "Travel insurance covers force majeure — claim through insurance, not agency";
    };

    SUPPLIER_CANCEL: {
      policy: "If supplier cancels (hotel overbooked, airline cancels flight):";
      options: [
        "Full refund of affected component",
        "Alternative arrangement of equal or higher standard at no extra cost",
        "Customer choice: refund or alternative",
      ];
      compensation: "₹500-2,000 inconvenience credit for future booking (discretionary)";
    };
  };

  // Liability framework
  liability: {
    AGENCY_LIABILITY: {
      responsible_for: [
        "Accuracy of booking details (dates, hotel names, activities)",
        "Timely communication of booking confirmations",
        "Payment handling and invoicing accuracy",
        "Visa application assistance quality",
      ];

      not_responsible_for: [
        "Airline delays, cancellations, or schedule changes",
        "Hotel service quality beyond booking confirmation",
        "Weather conditions affecting trip experience",
        "Customer health issues during travel",
        "Supplier bankruptcy or business failure",
        "Government regulation changes (visa rules, travel bans)",
      ];
    };

    LIABILITY_LIMITATION: {
      maximum: "Agency liability limited to amount paid by customer for the specific booking";
      exclusion: "Consequential losses (missed events, business losses, emotional distress) not covered";
      insurance: "Agency recommends travel insurance for comprehensive protection";
      indemnification: "Customer indemnifies agency for issues arising from incorrect information provided by customer";
    };
  };
}

// ── Cancellation calculator ──
// ┌─────────────────────────────────────────────────────┐
// │  Cancellation Calculator                                   │
// │                                                       │
// │  Booking: Sharma Family Singapore · ₹2,80,000            │
// │  Travel dates: Jun 15-20, 2026                            │
// │  Cancellation date: May 20, 2026 (26 days before travel) │
// │                                                       │
// │  Package cancellation tier:                            │
// │  26 days before = 30-45 day window → 75% refund          │
// │                                                       │
// │  Breakdown:                                           │
// │  Package cost: ₹2,80,000                                  │
// │  Cancellation charge (25%): ₹70,000                       │
// │  Refund amount: ₹2,10,000                                 │
// │                                                       │
// │  Component exceptions:                                │
// │  ✅ Hotel: Free cancellation until Jun 12 → Full refund   │
// │  ⚠️ Flight: IndiGo Saver fare → ₹3,500 per person (₹7,000)│
// │  ✅ Activities: Free cancellation until Jun 13            │
// │                                                       │
// │  Adjusted calculation:                                │
// │  Flight non-refundable: ₹7,000                            │
// │  Package cancellation: ₹63,000 (₹70K - ₹7K flight)      │
// │  Total refund: ₹2,10,000 (₹2.8L - ₹63K - ₹7K)          │
// │                                                       │
// │  [Process Cancellation] [Offer Credit Note] [Escalate]    │
// └─────────────────────────────────────────────────────┘
```

### Consumer Protection Compliance

```typescript
interface ConsumerProtection {
  // Indian consumer protection laws affecting travel agencies
  applicable_laws: {
    CONSUMER_PROTECTION_ACT_2019: {
      relevance: "Travel services classified as 'services' under the Act";
      key_provisions: {
        unfair_trade: "Misleading claims about destinations, hotels, or inclusions";
        deficiency: "Service not matching what was promised (hotel downgrade, missing activities)";
        overcharging: "Charging more than quoted without customer consent";
        refund_delay: "Must process refunds within time promised (typically 7-14 days)";
      };

      consumer_rights: {
        right_to_information: "Full disclosure of inclusions, exclusions, terms before booking";
        right_to_choose: "Not forcing specific suppliers or packages";
        right_to_redressal: "Customer can approach Consumer Disputes Redressal Commission";
        right_to_compensation: "For deficiency in service, overcharging, or unfair trade";
      };

      penalties: {
        district_commission: "Claims up to ₹1Cr — local consumer court";
        state_commission: "Claims ₹1Cr-10Cr — state consumer court";
        national_commission: "Claims >₹10Cr — national consumer court";
        typical_case_duration: "12-36 months";
        common_outcomes: "Refund + compensation (₹5K-2L) + legal costs";
      };
    };

    GST_APPLICABILITY: {
      travel_services: {
        package_tour: "5% GST on 25% of package value (effective 1.25%) or 18% on margin";
        hotel_booking: "GST included in hotel rate (varies by hotel star rating)";
        airline_ticket: "GST on commission earned, not on ticket value";
        visa_service: "18% GST on service fee";
        insurance: "GST included in premium by insurance company";
      };

      TCS_COLLECTION: {
        description: "Tax Collected at Source on international tour packages";
        rate: "5% if package >₹7L per person; 20% if no PAN/Aadhaar";
        mechanism: "Agency collects TCS from customer → deposits to government → customer claims credit";
        due_date: "Monthly deposit by 7th of following month";
        quarterly_return: "Form 27EQ filed quarterly";
      };
    };
  };
}
```

---

## Open Problems

1. **Template maintenance** — Legal templates need annual review by a lawyer, but most agencies never update them. Need a reminder system and template version management.

2. **Consumer disputes** — Even with good terms, consumer court cases happen. Need a dispute resolution process that resolves most issues before they reach formal complaints.

3. **TCS compliance complexity** — TCS rules on international packages are complex and frequently updated. Many agencies collect incorrectly or fail to deposit on time.

4. **Cross-border legal issues** — When Indian customers travel internationally, multiple jurisdictions apply. Liability limitations under Indian law may not hold for incidents abroad.

---

## Next Steps

- [ ] Create standardized booking T&C template for Indian travel agencies
- [ ] Build cancellation calculator with component-level policy application
- [ ] Implement GST invoice generator with TCS collection tracking
- [ ] Design legal document versioning system with annual review reminders
