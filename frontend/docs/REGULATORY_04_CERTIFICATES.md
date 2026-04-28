# Regulatory & Licensing — Certificate Management & Renewals

> Research document for certificate lifecycle management, expiry tracking, renewal automation, and document vault.

---

## Key Questions

1. **How do we manage the lifecycle of all agency certificates and licenses?**
2. **What expiry tracking and renewal alerts are needed?**
3. **How do we automate renewal workflows?**
4. **What's the document vault architecture for regulatory documents?**
5. **How do we handle audits and compliance checks?**

---

## Research Areas

### Certificate Lifecycle Management

```typescript
interface CertificateLifecycle {
  certificateId: string;
  type: CertificateType;
  holder: CertificateHolder;
  status: CertificateStatus;
  timeline: CertificateTimeline;
  renewal: RenewalConfig;
  documents: CertificateDocument[];
}

type CertificateType =
  // Business registrations
  | 'gst_registration'
  | 'pan_card'
  | 'tan_registration'
  | 'msme_udyam'
  | 'shop_establishment'
  | 'trade_license'
  | 'fssai_license'
  // Professional certifications
  | 'iata_accreditation'
  | 'iata_ufataa_diploma'
  | 'amadeus_certification'
  | 'sabre_certification'
  // Travel-specific
  | 'ministry_tourism_recognition'
  | 'state_tourism_license'
  | 'adventure_tourism_license'
  // Staff certifications
  | 'iata_agent_exam'
  | 'first_aid_certification'
  | 'guide_license'
  // Insurance & financial
  | 'professional_indemnity_insurance'
  | 'bank_guarantee'
  | 'cash_deposit_receipt'
  // Compliance
  | 'epf_registration'
  | 'esi_registration'
  | 'labor_law_compliance'
  | 'fire_safety_certificate'
  | 'consumer_complaint_registration';

interface CertificateTimeline {
  issuedDate: Date;
  effectiveDate: Date;
  expiryDate: Date;
  renewalStartDate: Date;             // When renewal process can begin
  renewalDeadline: Date;              // Must be renewed by this date
  lastRenewedDate?: Date;
  renewalCount: number;
}

// Certificate lifecycle states:
// active → renewal_pending → renewal_submitted → renewed → active
//    ↓                              ↓
//  expired ← ← ← ← ← ← ← ←  rejected
//    ↓
//  grace_period → reinstated (if renewed late)
//    ↓
//  cancelled (if not renewed within grace period)

// Renewal timeline example (IATA Accreditation):
// Accredited: Jan 2024
// Valid until: Dec 31, 2024 (annual review)
// Renewal window opens: Nov 1, 2024 (60 days before)
// Documents due: Nov 15, 2024
// Financial review: Dec 1, 2024
// Renewal confirmed: Dec 15, 2024
// New accreditation period: Jan 2025 - Dec 2025

interface RenewalConfig {
  autoRenewable: boolean;
  renewalLeadTime: number;            // Days before expiry to start
  documentsRequired: string[];
  fees: RenewalFee[];
  processingTime: string;             // "15-30 business days"
  authority: RenewalAuthority;
  steps: RenewalStep[];
}

interface RenewalStep {
  step: number;
  action: string;
  responsibleParty: 'platform' | 'agency_admin' | 'consultant' | 'authority';
  estimatedDuration: string;
  dependencies: number[];             // Step numbers that must complete first
  autoAction?: string;                // Platform can do this automatically
}

// Automated renewal steps:
// Step 1: Download renewal form (platform auto-downloads if available)
// Step 2: Pre-fill form with current data (platform auto-fills)
// Step 3: Upload required documents (agency admin action)
// Step 4: Review and verify (agency admin review)
// Step 5: Pay renewal fee (platform generates payment link)
// Step 6: Submit to authority (platform submits online, or prints form)
// Step 7: Track status (platform monitors authority portal)
// Step 8: Upload renewed certificate (agency admin or platform auto-detects)
// Step 9: Update compliance score (platform auto-updates)
```

### Document Vault

```typescript
interface DocumentVault {
  agencyId: string;
  documents: VaultDocument[];
  access: VaultAccess;
  retention: VaultRetention;
  audit: VaultAudit;
}

interface VaultDocument {
  documentId: string;
  category: DocumentCategory;
  type: string;
  title: string;
  fileUrl: string;
  fileSize: string;
  uploadedBy: string;
  uploadedAt: Date;
  expiryDate?: Date;
  status: 'active' | 'expired' | 'archived';
  tags: string[];
  linkedEntity?: string;              // License ID, staff ID, etc.
}

type DocumentCategory =
  | 'registration'                    // PAN, GST, TAN, etc.
  | 'license'                         // IATA, Shop & Establishment, etc.
  | 'insurance'                       // Professional indemnity, etc.
  | 'financial'                       // Bank guarantee, audit reports
  | 'compliance'                      // Fire safety, labor law, etc.
  | 'staff'                           // Staff certifications, training
  | 'contracts'                       // Supplier contracts, partnership agreements
  | 'tax'                             // GST returns, TDS certificates, ITR
  | 'correspondence';                 // Government letters, notices

// Document vault features:
// - Categorized storage with metadata
// - Full-text search (OCR for scanned documents)
// - Version control (new version replaces old, old archived)
// - Access control (admin, accountant, agent — different access levels)
// - Expiry tracking (documents with expiry auto-monitored)
// - Bulk upload (drag-and-drop multiple documents)
// - Mobile upload (camera → scan → upload)
// - Integration with compliance dashboard
// - Audit trail (who accessed, downloaded, modified)
// - Encryption at rest (AES-256)
// - Backup (daily automated backup)
//
// Storage estimates:
// Per agency: ~200-500 documents over 5 years
// Average document: 2-5 MB (PDF, scanned image)
// Total storage per agency: 1-2 GB
// Platform total (100 agencies): 100-200 GB

interface VaultAccess {
  roles: Record<string, VaultPermission[]>;
  sharing: DocumentSharing;
  watermarking: boolean;
  downloadControl: DownloadControl;
}

// Access control matrix:
// Agency Owner: Full access (all documents, all actions)
// Agency Admin: Full access except ownership transfer
// Accountant: Tax, financial, compliance categories only
// Agent: Staff-related documents only (own certifications)
// Auditor: Read-only, time-limited access (granted per audit)
// Platform Support: Read-only, with agency admin approval
//
// Security:
// - Documents watermarked with viewer's name and timestamp
// - Download tracking (who downloaded what, when)
// - No bulk download (prevent mass data extraction)
// - Time-limited sharing links (expire after 7 days)
// - Two-factor authentication for sensitive documents
```

### Compliance Dashboard

```typescript
interface ComplianceDashboard {
  agencyId: string;
  overallScore: number;               // 0-100
  riskLevel: 'low' | 'medium' | 'high' | 'critical';
  categories: ComplianceCategory[];
  upcomingDeadlines: ComplianceDeadline[];
  alerts: ComplianceAlert[];
  auditReadiness: AuditReadiness;
}

interface ComplianceCategory {
  name: string;                       // "Tax", "Licensing", "Insurance"
  score: number;
  status: 'compliant' | 'warning' | 'non_compliant';
  items: ComplianceItem[];
}

// Compliance scoring:
// Score = (Compliant items / Total items) × 100
// Each category weighted:
// Tax compliance: 30% (GST, TDS, TCS, Income Tax)
// Licensing: 25% (IATA, Shop & Est., Trade License, Tourism)
// Insurance: 15% (Professional indemnity, bank guarantee)
// Staff certifications: 15% (IATA training, first aid)
// Operational: 15% (Fire safety, consumer complaints, labor law)
//
// Status thresholds:
// Score 90-100: ✅ Fully Compliant (green)
// Score 70-89: ⚠️ Minor Issues (yellow)
// Score 50-69: ⚠️ Significant Gaps (orange)
// Score 0-49: 🔴 Non-Compliant (red) — action required

interface ComplianceDeadline {
  deadlineId: string;
  description: string;
  category: string;
  dueDate: Date;
  daysRemaining: number;
  status: 'on_track' | 'at_risk' | 'overdue';
  actionRequired: string;
  autoPrepareable: boolean;
}

// Upcoming deadlines view:
// ┌──────────────────────────────────────────────┐
// │  Compliance Deadlines                         │
// │                                              │
// │  🔴 OVERDUE                                  │
// │  GST Return (GSTR-3B) — Due Apr 20          │
// │  Penalty: ₹100/day                          │
// │  [File Now]                                  │
// │                                              │
// │  ⚠️ THIS WEEK                                │
// │  TCS Deposit — Due May 7 (3 days)           │
// │  Amount: ₹45,000                            │
// │  [Prepare Payment]                           │
// │                                              │
// │  📋 THIS MONTH                               │
// │  Shop & Est. Renewal — Due May 30 (26 days) │
// │  Documents needed: 3 of 4 uploaded           │
// │  [Complete Application]                      │
// │                                              │
// │  ✅ UPCOMING                                  │
// │  GST Return (GSTR-1) — Due Jun 11 (38 days) │
// │  Auto-preparation: Available Jun 8           │
// │  [Schedule Auto-Prepare]                     │
// └──────────────────────────────────────────────┘

interface AuditReadiness {
  score: number;                      // 0-100
  missingDocuments: string[];
  lastAuditDate?: Date;
  nextAuditDue?: Date;
  preparationChecklist: AuditChecklistItem[];
}

// Audit readiness checklist:
// [ ] All GST returns filed for audit period
// [ ] Bank statements collected for audit period
// [ ] Booking revenue reconciliation completed
// [ ] TDS/TCS certificates collected
// [ ] Expense documentation organized
// [ ] Staff salary records (PF, ESI if applicable)
// [ ] Fixed asset register updated
// [ ] Supplier invoices and contracts filed
// [ ] Board minutes (if company) up to date
// [ ] Previous year's audit report available
//
// Audit readiness automation:
// - Platform tracks which documents are available
// - Flags missing documents for agency to provide
// - Auto-generates reconciliation reports
// - Prepares trial balance and financial summaries
// - Creates audit-ready export (Excel + PDF bundle)
```

---

## Open Problems

1. **Document verification** — Uploaded documents may be forged or expired. Need verification against issuing authority databases where available.

2. **Regulatory change management** — Government rules change frequently (budget announcements, CBDT circulars, state-level amendments). Need real-time regulatory intelligence.

3. **Multi-state compliance** — Agencies with branches in multiple states need separate compliance per state. Each state has unique Shop & Establishment rules.

4. **Audit stress** — Agencies often scramble during audit season. Proactive compliance management throughout the year reduces audit stress.

5. **Consultant dependency** — Most small agencies rely on CAs and tax consultants for compliance. Platform can automate routine filings but can't replace professional judgment.

---

## Next Steps

- [ ] Build certificate lifecycle management with auto-renewal workflows
- [ ] Create encrypted document vault with categorized storage and OCR search
- [ ] Design compliance dashboard with scoring and deadline tracking
- [ ] Build audit readiness toolkit with reconciliation reports
- [ ] Study compliance management platforms (V-Comply, ComplianceQuest, Zoho Compliance)
