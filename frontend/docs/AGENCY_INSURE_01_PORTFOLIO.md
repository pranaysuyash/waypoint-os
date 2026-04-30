# Agency Insurance & Risk Transfer — Portfolio & Claims

> Research document for travel agency insurance portfolio, professional indemnity, errors & omissions, business interruption, cyber insurance, and claims management for the Waypoint OS platform.

---

## Key Questions

1. **What insurance does a travel agency need for its own protection?**
2. **How do professional indemnity and E&O insurance work for travel agencies?**
3. **What does business interruption insurance cover?**
4. **How does cyber insurance protect against data breaches?**

---

## Research Areas

### Agency Insurance Portfolio

```typescript
interface AgencyInsurancePortfolio {
  // Insurance products protecting the agency (not customer travel insurance)
  insurance_types: {
    PROFESSIONAL_INDEMNITY: {
      description: "Covers claims of professional negligence or errors in service";
      why_needed: "Customer sues agency for booking error, wrong destination, missed flight";
      coverage: {
        legal_defense: "Legal costs for defending against claims";
        compensation: "Damages awarded to customer (up to policy limit)";
        examples: [
          "Agent books wrong dates → customer misses trip → sues for damages",
          "Visa application error → customer denied boarding → agency liable",
          "Wrong hotel booked (different city) → customer stranded → claim",
        ];
      };
      policy_details: {
        coverage_amount: "₹25L-1Cr (recommended: 2x annual revenue)";
        premium: "₹15K-50K/year depending on revenue and claims history";
        deductible: "₹10K-50K per claim";
        exclusions: ["Intentional fraud", "Criminal acts", "Known issues not disclosed"];
      };

      providers_india: {
        new_india_assurance: "Public sector, competitive rates, wide network";
        icici_lombard: "Private sector, faster claims, online management";
        bajaj_allianz: "Good for small agencies, flexible coverage options";
        hdfc_ergo: "Comprehensive coverage, digital claims process";
      };
    };

    ERRORS_AND_OMISSIONS: {
      description: "Covers mistakes and failures in booking/services that cause customer loss";
      relation_to_pi: "Often bundled with professional indemnity as PI+E&O package";
      covered_scenarios: [
        "Forgot to book airport transfer → customer pays ₹5K taxi → agency reimburses",
        "Incorrect visa advice → customer denied entry → trip cancelled → agency pays",
        "Hotel booking not confirmed (technical error) → customer arrives with no room → agency covers emergency hotel",
        "Missed payment deadline to supplier → booking cancelled → agency covers rebooking cost",
      ];
      coverage_amount: "₹10L-50L";
      premium: "₹10K-30K/year";
    };

    BUSINESS_INTERRUPTION: {
      description: "Covers lost revenue when agency can't operate due to insured event";
      trigger_events: [
        "Office fire/flood → can't operate for weeks",
        "Pandemic lockdown → travel banned → revenue drops 80%+",
        "Key supplier bankruptcy → committed bookings can't be fulfilled",
        "Government regulation change → license suspended",
      ];
      coverage: {
        lost_revenue: "Average monthly revenue for period of interruption (up to 12 months)";
        fixed_costs: "Rent, salaries, loan payments during interruption";
        relocation: "Temporary office setup costs";
        extra_expenses: "Costs to minimize interruption (overtime, temporary systems)";
      };
      pandemic_lessons: {
        covid_impact: "Most Indian agencies lost 80-90% revenue during 2020-2021";
        insurance_gap: "Standard BI policies excluded pandemic — most agencies got nothing";
        post_covid: "Newer policies offer pandemic add-on at 20-30% premium increase";
      };
    };

    CYBER_INSURANCE: {
      description: "Covers costs of data breaches, cyber attacks, and privacy incidents";
      why_critical: "Agency stores passport numbers, Aadhaar, payment data — high-value PII";
      coverage: {
        breach_notification: "Cost of notifying affected customers (DPDP Act requires 72h notification)";
        forensic_investigation: "Cost of investigating breach scope and cause";
        legal_defense: "Legal costs for privacy lawsuits and regulatory fines";
        credit_monitoring: "Credit monitoring for affected customers";
        business_interruption: "Revenue lost during system downtime from attack";
        extortion: "Ransom payment (if legal) in ransomware attack";
      };
      typical_costs: {
        data_breach_india: "₹8L-2Cr average cost per breach (IBM 2024 study)";
        premium: "₹20K-1L/year depending on data volume and security posture";
        coverage: "₹50L-5Cr";
      };
    };

    GENERAL_LIABILITY: {
      description: "Covers third-party bodily injury and property damage at agency premises";
      scenarios: [
        "Customer slips in agency office → injury claim",
        "Agency-organized event → participant injury",
        "Property damage to rented office space",
      ];
      premium: "₹5K-15K/year";
      coverage: "₹10L-50L";
    };
  };
}

// ── Agency insurance dashboard ──
// ┌─────────────────────────────────────────────────────┐
// │  Agency Insurance — Portfolio Overview                     │
// │                                                       │
// │  Active Policies:                                     │
// │  🛡️ Professional Indemnity · ₹50L coverage               │
// │     ICICI Lombard · Premium: ₹28K/yr · Renews: Dec 2026  │
// │     Claims: 1 (₹12K — booking error, settled)            │
// │                                                       │
// │  📋 E&O · ₹25L coverage (bundled with PI)                 │
// │     Covered under same policy                             │
// │                                                       │
// │  🏢 Business Interruption · ₹30L coverage                 │
// │     New India Assurance · Premium: ₹22K/yr                │
// │     Pandemic add-on: Yes (+₹8K)                          │
// │     Claims: 0                                              │
// │                                                       │
// │  🔒 Cyber Insurance · ₹1Cr coverage                       │
// │     Bajaj Allianz · Premium: ₹45K/yr                      │
// │     Last security audit: Feb 2026 ✅                       │
// │     Claims: 0                                              │
// │                                                       │
// │  🏥 General Liability · ₹25L coverage                     │
// │     HDFC Ergo · Premium: ₹8K/yr                           │
// │     Claims: 0                                              │
// │                                                       │
// │  Total annual premium: ₹1.11L                              │
// │  Coverage value: ₹2.3Cr                                   │
// │  Cost as % of revenue: 0.5%                               │
// │                                                       │
// │  [File Claim] [Compare Policies] [Renewal Calendar]        │
// └─────────────────────────────────────────────────────┘
```

### Claims Management & Prevention

```typescript
interface ClaimsManagement {
  // Filing and managing insurance claims
  claims_process: {
    FILING: {
      step_1: "Document the incident (photos, emails, customer complaint)";
      step_2: "Notify insurer within 48-72 hours of incident";
      step_3: "Fill claim form with incident details and supporting documents";
      step_4: "Insurer assigns surveyor/adjuster";
      step_5: "Assessment and investigation (2-4 weeks)";
      step_6: "Settlement or rejection with reasons";
    };

    common_claims: {
      BOOKING_ERROR: {
        frequency: "Most common claim type (60% of PI claims)";
        example: "Agent books June 15 instead of July 15; customer arrives to no booking";
        claim_amount: "₹5K-50K (rebooking cost + inconvenience)";
        prevention: "System-enforced date confirmation + customer verification before booking";
      };

      SUPPLIER_FAILURE: {
        frequency: "15% of claims";
        example: "Hotel goes bankrupt after agency collected customer payment";
        claim_amount: "₹20K-2L (full trip value)";
        prevention: "Verify supplier financial health + use escrow for large payments";
      };

      DATA_BREACH: {
        frequency: "5% of claims (but highest cost per claim)";
        example: "Customer passport data leaked due to unsecured system";
        claim_amount: "₹5L-50L (notification + legal + compensation)";
        prevention: "PII encryption + access controls + security audits";
      };
    };
  };

  // Risk prevention through system design
  risk_prevention: {
    BOOKING_ACCURACY: {
      description: "Prevent errors that lead to claims";
      measures: [
        "Mandatory customer confirmation of dates, travelers, destination before booking",
        "System-level validation (no past dates, valid hotel codes, price sanity checks)",
        "Double-entry verification for critical fields (passport numbers, flight dates)",
        "Automated booking confirmation sent to customer within 1 hour of creation",
      ];
    };

    FINANCIAL_PROTECTION: {
      description: "Prevent financial losses that lead to claims";
      measures: [
        "Separate customer funds from operating funds (escrow account)",
        "Supplier payments only after customer payment received",
        "Payment milestone tracking with automated alerts",
        "Credit limit management for supplier payments",
      ];
    };

    DATA_PROTECTION: {
      description: "Prevent data breaches that lead to claims";
      measures: [
        "PII field-level encryption (PII_DETECT_* series)",
        "Access logging for all PII access",
        "Regular security audits",
        "Employee data handling training",
      ];
    };
  };
}
```

---

## Open Problems

1. **Claims documentation** — Most agencies don't document incidents properly, making claims harder to prove. Need system-level incident logging that captures relevant details at the time of occurrence.

2. **Pandemic coverage gaps** — Standard business interruption policies don't cover pandemic-related losses (as agencies learned in 2020). Pandemic add-ons exist but are expensive and have coverage limits.

3. **Cyber insurance requirements** — Insurers increasingly require proof of security measures (encryption, access controls, audits) before issuing cyber policies. Agencies without proper PII protection may not qualify.

4. **Premium vs. risk calculation** — Small agencies (₹1Cr revenue) may find ₹1L+ annual insurance premium burdensome. But a single uninsured claim (₹2-5L) costs more than a decade of premiums.

---

## Next Steps

- [ ] Build insurance portfolio management dashboard
- [ ] Implement claims filing workflow with document collection
- [ ] Create risk prevention checklist integrated into booking process
- [ ] Design insurance renewal calendar with comparison shopping
