# Customer Identity & Verification — KYC & Verification

> Research document for customer identity verification, KYC processes, and regulatory compliance.

---

## Key Questions

1. **What identity verification is required for travel services?**
2. **How do we implement KYC without creating friction?**
3. **What India-specific regulations govern customer identity?**
4. **How do we handle verification for different traveler nationalities?**
5. **What's the data security model for identity documents?**

---

## Research Areas

### Verification Requirements

```typescript
interface VerificationRequirement {
  serviceType: ServiceType;
  nationality: string;
  requiredDocuments: DocumentRequirement[];
  verificationLevel: VerificationLevel;
}

type VerificationLevel =
  | 'basic'                   // Name + phone (domestic hotel)
  | 'standard'                // Name + ID (domestic flight)
  | 'enhanced'                // Name + ID + address (international flight)
  | 'full_kyc';               // Full KYC (forex, high-value transactions)

// Verification requirements by service:
//
// Domestic flights (India):
//   - Any government-issued photo ID
//   - PAN card, Aadhaar, passport, voter ID, driving license
//   - Name must match booking name exactly
//
// International flights:
//   - Valid passport (6+ months validity beyond travel dates)
//   - Visa (if required for destination)
//   - Some countries require additional docs (e.g., Saudi Arabia: vaccination cert)
//
// Hotels (domestic):
//   - Government photo ID at check-in
//   - Booking name should match ID
//   - Foreign nationals: Passport + visa copy
//
// Forex purchase:
//   - PAN card (mandatory)
//   - Passport copy
//   - Visa copy (for destination country)
//   - Ticket copy (confirmed onward/return journey)
//   - Purpose declaration (LRS compliance)
//   - Full KYC with address proof
//
// Travel insurance:
//   - Name, date of birth, passport number
//   - Nominee details
//
// Visa application:
//   - Full passport scan
//   - Photographs (specific dimensions per country)
//   - Financial documents (bank statements, ITR)
//   - Employment/education proof
//   - Travel itinerary
//   - Hotel and flight confirmations
```

### KYC Process

```typescript
interface CustomerKYC {
  customerId: string;
  kycStatus: KYCStatus;
  verifiedDocuments: VerifiedDocument[];
  verificationHistory: VerificationEvent[];
  riskLevel: 'low' | 'medium' | 'high';
  lastVerifiedAt: Date;
  nextRenewalAt?: Date;
}

type KYCStatus =
  | 'not_started'
  | 'pending'
  | 'in_review'
  | 'verified'
  | 'rejected'
  | 'expired';

interface VerifiedDocument {
  documentType: DocumentType;
  documentNumber: string;            // Masked for display: "XXXXX1234X"
  documentExpiry: Date;
  verifiedAt: Date;
  verifiedBy: 'agent' | 'automated' | 'third_party';
  verificationReference: string;
  storageReference: string;          // Encrypted storage location
}

type DocumentType =
  | 'passport'
  | 'aadhaar'
  | 'pan_card'
  | 'voter_id'
  | 'driving_license'
  | 'bank_statement'
  | 'utility_bill'
  | 'photograph'
  | 'visa'
  | 'birth_certificate'
  | 'marriage_certificate'
  | 'itr_acknowledgement';

// KYC verification flow:
// 1. Agent collects documents (in-person, WhatsApp, email, upload)
// 2. System performs automated checks:
//    a. Document type validation (is this a valid passport?)
//    b. Name matching (does the name match the booking?)
//    c. Expiry check (is the document valid for travel dates?)
//    d. Format validation (correct dimensions, readable quality)
// 3. For enhanced verification:
//    a. Aadhaar eKYC (UIDAI API for Aadhaar verification)
//    b. DigiLocker integration (pull documents from government locker)
//    c. OCR extraction (auto-fill from document scan)
// 4. Agent reviews automated results, confirms or flags issues
// 5. Customer verified → Documents stored encrypted

// India-specific regulations:
// Aadhaar Act 2016: Aadhaar can be used for identity verification
//   BUT: Cannot make Aadhaar mandatory (Supreme Court ruling)
//   Must offer alternative ID options
//
// DPDP Act 2023: Data protection requirements
//   - Explicit consent for document collection
//   - Purpose limitation (documents only for stated purpose)
//   - Right to erasure (delete documents when no longer needed)
//   - Data minimization (only collect what's needed)
//
// PMLA (Prevention of Money Laundering Act):
//   - KYC required for forex transactions
//   - PAN mandatory for transactions > ₹50,000
//   - Enhanced due diligence for high-value transactions
//
// RBI Master Direction on KYC:
//   - Customer identification procedures
//   - Risk-based approach (low/medium/high risk customers)
//   - Ongoing monitoring (periodic re-verification)
```

### Document Security

```typescript
interface DocumentSecurity {
  encryption: EncryptionConfig;
  access: DocumentAccessControl;
  retention: RetentionPolicy;
  audit: DocumentAuditLog;
}

// Security measures:
// 1. AES-256 encryption at rest
// 2. Encrypted in transit (TLS 1.3)
// 3. Access logging (who viewed/downloaded what and when)
// 4. Time-limited access links (expire after 30 minutes)
// 5. No downloads to agent devices (view only)
// 6. Automatic redaction of sensitive numbers in display
// 7. Secure deletion after retention period
// 8. Separate storage from application database
// 9. Tokenized references (no document numbers in logs)
// 10. Breach notification per DPDP Act requirements

// Access control:
// Agent: View documents for assigned trips only
// Specialist: View relevant documents (visa agent sees passport, not bank statements)
// Admin: View all documents, manage retention
// Customer: View their own documents, download for personal records
// Auditor: View audit trail, not actual documents

// Retention policy:
// Active booking: Until trip completion + 30 days
// Completed trip: 7 years (tax/legal requirement)
// Cancelled trip: 1 year after cancellation
// Customer request to delete: Within 30 days (DPDP Act)
// Exception: Documents under legal hold → Retain until hold released
```

---

## Open Problems

1. **Document quality** — Customers send photos of passports via WhatsApp (blurry, cropped, poor lighting). OCR fails on low-quality images. Need quality checks at upload.

2. **Name mismatch** — Passport says "RAJESH KUMAR SHARMA", booking says "Rajesh Sharma", Aadhaar says "Rajesh K Sharma". Airlines reject mismatched names. Need fuzzy name matching and normalization.

3. **Consent management** — Collecting documents requires explicit consent under DPDP Act. Consent must be granular (which documents, for what purpose, how long). Consent UX is complex.

4. **Multi-traveler verification** — A family of 5 needs 5 passports, potentially 5 visas. Bulk document management with per-person verification status.

5. **International document formats** — A Nepali passport, a UK driving license, a US visa — each has different format and verification requirements. Need multi-format support.

---

## Next Steps

- [ ] Design KYC workflow with progressive verification levels
- [ ] Build document security model with encryption and access control
- [ ] Create OCR-powered document extraction pipeline
- [ ] Design consent management per DPDP Act requirements
- [ ] Study KYC systems (DigiLocker, Aadhaar eKYC, Jumio, Onfido)
