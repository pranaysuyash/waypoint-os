# Regulatory & Licensing — Agency Licensing & Registration

> Research document for travel agency licensing, government registration, and regulatory compliance in India.

---

## Key Questions

1. **What licenses and registrations does a travel agency need in India?**
2. **How do we track license status, renewals, and expiry?**
3. **What are the compliance requirements for different agency types?**
4. **How do regulatory requirements vary by state?**
5. **What's the penalty for non-compliance?**

---

## Research Areas

### Licensing Model

```typescript
interface AgencyLicense {
  agencyId: string;
  licenses: AgencyLicenseEntry[];
  registrations: GovernmentRegistration[];
  accreditations: Accreditation[];
  complianceStatus: ComplianceStatus;
}

interface AgencyLicenseEntry {
  licenseType: LicenseType;
  licenseNumber: string;
  issuingAuthority: string;
  issuedDate: Date;
  expiryDate: Date;
  status: LicenseStatus;
  renewalDue: Date;
  documents: LicenseDocument[];
}

type LicenseStatus =
  | 'active'
  | 'pending_renewal'
  | 'expired'
  | 'suspended'
  | 'cancelled';

// Required licenses for Indian travel agencies:
//
// 1. GST Registration (Mandatory)
//    - GST number required if annual turnover > ₹20 lakh (₹10 lakh for NE states)
//    - Most travel agencies exceed this threshold
//    - GST rates: 5% on air travel, 5% on tour packages (with input tax credit)
//    - Filing: Monthly GSTR-1, GSTR-3B; Quarterly GSTR-9
//    - Penalty for non-filing: ₹50/day (₹100/day if tax unpaid)
//
// 2. Shop & Establishment License (State-level)
//    - Required for any commercial establishment
//    - Issued by local municipal corporation / labor department
//    - State-specific requirements and fees
//    - Renewal: Annual or multi-year (state-dependent)
//
// 3. Ministry of Tourism Recognition (Recommended)
//    - Not mandatory but highly valuable
//    - Classified as: Approved / Recognized travel agency
//    - Requirements: Min 3 years experience, financial standing
//    - Benefits: Government contract eligibility, credibility
//    - Renewal: Every 5 years
//
// 4. IATA Accreditation (For flight ticketing)
//    - Required for direct airline ticketing (BSP billing)
//    - Categories: Accredited Agent, Cargo Agent, General Sales Agent
//    - Financial guarantee: Bank guarantee or cash deposit
//    - Annual turnover requirements apply
//    - Renewal: Annual review
//
// 5. Trade License (Municipal)
//    - Required by local municipal body
//    - Specific to business type (travel agency)
//    - Fees vary by city and area
//    - Renewal: Annual

interface GovernmentRegistration {
  registrationType: RegistrationType;
  registrationNumber: string;
  issuingAuthority: string;
  registeredDate: Date;
  status: 'active' | 'inactive';
}

type RegistrationType =
  | 'gst'                             // Goods and Services Tax
  | 'pan'                             // Permanent Account Number (income tax)
  | 'tan'                             // Tax Deduction Account Number (TDS)
  | 'msme'                            // Udyam Registration (MSME)
  | 'fssai'                           // Food license (if selling meal packages)
  | 'shop_establishment'              // Shop & Establishment Act
  | 'profession_tax'                  // Professional tax registration
  | 'epf'                             // Employee Provident Fund (if 20+ employees)
  | 'esi'                             // Employee State Insurance (if applicable)
  | 'tds';                            // TDS compliance for commission payments

// Registration hierarchy:
// Must have:
//   - PAN (income tax) — Foundation for everything
//   - GST — If turnover > ₹20 lakh
//   - Shop & Establishment — State requirement
//   - Trade License — Municipal requirement
//
// Recommended:
//   - MSME/Udyam — Benefits: Priority lending, subsidy eligibility
//   - Ministry of Tourism recognition — Credibility, government contracts
//   - TAN — If deducting TDS on commissions
//
// Optional (business-dependent):
//   - IATA — If issuing airline tickets directly
//   - FSSAI — If providing meal packages
//   - EPF/ESI — Based on employee count
```

### License Tracking & Renewal

```typescript
interface LicenseTracker {
  agencyId: string;
  dashboard: LicenseDashboard;
  alerts: LicenseAlert[];
  renewals: RenewalPipeline;
  documents: LicenseDocumentVault;
}

interface LicenseDashboard {
  totalLicenses: number;
  activeCount: number;
  expiringCount: number;               // Within 90 days
  expiredCount: number;
  complianceScore: number;             // 0-100
  riskLevel: 'low' | 'medium' | 'high';
}

// License dashboard:
// ┌──────────────────────────────────────────┐
// │  License Compliance Dashboard             │
// │                                          │
// │  Compliance Score: 85/100                │
// │  ████████████████████░░░░ 85%            │
// │                                          │
// │  Active: 8  Expiring: 2  Expired: 0     │
// │                                          │
// │  ⚠ GST Registration                     │
// │    Expires: Aug 15, 2026 (62 days)       │
// │    Status: Renewal application pending   │
// │    [Start Renewal Process]               │
// │                                          │
// │  ⚠ Shop & Establishment License          │
// │    Expires: Sep 30, 2026 (108 days)      │
// │    Status: Documents ready for submission │
// │    [Upload Documents]                    │
// │                                          │
// │  ✅ IATA Accreditation — Active          │
// │  ✅ PAN Registration — Active            │
// │  ✅ MSME Registration — Active           │
// │  ✅ TAN Registration — Active            │
// │  ✅ Trade License — Active               │
// │  ✅ Profession Tax — Active              │
// │  ✅ EPF Registration — Active            │
// └──────────────────────────────────────────┘

interface LicenseAlert {
  licenseType: string;
  alertType: AlertType;
  message: string;
  actionRequired: string;
  deadline: Date;
}

type AlertType =
  | 'expiring_90_days'
  | 'expiring_60_days'
  | 'expiring_30_days'
  | 'expiring_7_days'
  | 'expired'
  | 'renewal_reminder'
  | 'document_required'
  | 'payment_due';

// Alert escalation timeline:
// -90 days: Dashboard warning, email notification
// -60 days: Email + in-app notification, renewal checklist
// -30 days: WhatsApp alert to agency admin, urgency badge
// -7 days: Phone call, daily dashboard reminder, agency admin alert
// Day 0: License marked expired, compliance score drops
// +7 days: If not renewed, features restricted (e.g., can't issue GST invoices)
// +30 days: If not renewed, flagged for legal compliance review

interface RenewalPipeline {
  pendingRenewals: RenewalEntry[];
  renewalChecklist: RenewalChecklist[];
  autoRenewable: string[];            // Licenses with auto-renewal enabled
}

interface RenewalEntry {
  licenseType: string;
  currentExpiry: Date;
  renewalStatus: 'not_started' | 'in_progress' | 'submitted' | 'approved';
  assignedTo: string;
  documentsUploaded: boolean;
  feesPaid: boolean;
  submittedDate?: Date;
  expectedApprovalDate?: Date;
}

// Renewal checklist example (Shop & Establishment):
// [ ] Download renewal form from state labor department website
// [ ] Fill form with current business details
// [ ] Attach copy of previous year's license
// [ ] Attach address proof (utility bill, rental agreement)
// [ ] Attach passport-size photographs of proprietor
// [ ] Pay renewal fee (₹500-2,000, state-dependent)
// [ ] Submit online (if state supports) or visit labor office
// [ ] Receive renewed license within 15-30 days
// [ ] Upload renewed license to platform
// [ ] Compliance score updated
```

### Compliance Requirements by Agency Type

```typescript
interface ComplianceByType {
  agencyType: AgencyType;
  mandatoryLicenses: string[];
  recommendedLicenses: string[];
  filingRequirements: FilingRequirement[];
  auditRequirements: AuditRequirement[];
  penaltyForNonCompliance: string;
}

type AgencyType =
  | 'sole_proprietorship'
  | 'partnership'
  | 'llp'                             // Limited Liability Partnership
  | 'private_limited'
  | 'one_person_company';

// Compliance matrix by agency type:
//
// Sole Proprietorship:
// Mandatory: PAN, GST, Shop & Establishment, Trade License
// Filing: GST monthly, Income Tax annually (ITR-3/4)
// Audit: Not required (unless turnover > ₹1 crore)
//
// Partnership:
// Mandatory: PAN, GST, Shop & Establishment, Trade License, Partnership Deed
// Filing: GST monthly, Income Tax annually (ITR-5), Partnership return
// Audit: Required if turnover > ₹1 crore
//
// Private Limited:
// Mandatory: PAN, GST, Shop & Establishment, Trade License, ROC compliance
// Filing: GST monthly, Income Tax annually, ROC annual returns (AOC-4, MGT-7)
// Audit: Always required (Companies Act mandate)
// Additional: Board meetings (min 4/year), statutory audit, DIR-3 KYC

interface FilingRequirement {
  filingType: string;
  frequency: string;
  dueDate: string;                    // e.g., "11th of following month"
  penalty: string;
  autoGenerated: boolean;             // Can platform auto-generate this filing?
}

// GST filing calendar:
// GSTR-1 (Outward supplies): 11th of following month
// GSTR-3B (Summary return): 20th of following month
// GSTR-9 (Annual return): December 31 of following financial year
// TDS return (if applicable): Quarterly (July 31, Oct 31, Jan 31, May 31)
// Income Tax return: July 31 (for non-audit cases), October 31 (audit cases)
//
// TCS on overseas tour packages (Section 206C(1G)):
// - TCS @ 5% on overseas tour packages > ₹7 lakh (if PAN available)
// - TCS @ 10% if PAN not available
// - No TCS for packages ≤ ₹7 lakh (up to March 2025 threshold)
// - TCS collected from customer, deposited by 7th of following month
// - Quarterly TCS return filing required
```

---

## Open Problems

1. **State-level variation** — Shop & Establishment rules, trade license fees, and compliance timelines vary across 28 states and 8 UTs. Need state-specific compliance playbooks.

2. **Renewal unpredictability** — Government processing times vary. Some renewals take 15 days, others take 3 months. Hard to predict exact compliance status.

3. **Regulatory changes** — GST rates, TCS thresholds, and filing deadlines change with Union Budget and CBDT notifications. Need real-time regulatory update tracking.

4. **Small agency burden** — A 2-person agency has the same compliance requirements as a 50-person firm. Compliance cost is regressive for small agencies.

5. **Digital readiness** — Many state government portals are unreliable or offline. Online renewal isn't always available. Physical submission may be required.

---

## Next Steps

- [ ] Build license tracking dashboard with expiry alerts
- [ ] Create renewal pipeline with checklists per license type
- [ ] Design compliance matrix for all agency types
- [ ] Integrate GST filing reminders and TCS tracking
- [ ] Study compliance platforms (ClearTax, Zoho Books, IndiaFilings, Vakilsearch)
