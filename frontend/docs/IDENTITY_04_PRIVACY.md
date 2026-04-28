# Customer Identity & Verification — Privacy & Consent

> Research document for data privacy management, consent workflows, and regulatory compliance for identity data.

---

## Key Questions

1. **How do we manage customer consent for identity data collection?**
2. **What's the data retention and deletion model for sensitive documents?**
3. **How do we comply with India's DPDP Act for identity data?**
4. **What's the cross-border data transfer model?**
5. **How do we handle customer data requests (access, deletion, portability)?**

---

## Research Areas

### Consent Management

```typescript
interface ConsentManagement {
  consents: ConsentRecord[];
  preferences: ConsentPreferences;
  auditTrail: ConsentAuditEntry[];
}

interface ConsentRecord {
  consentId: string;
  customerId: string;
  purpose: ConsentPurpose;
  dataTypes: DataType[];
  grantedAt: Date;
  expiresAt?: Date;
  withdrawalMechanism: string;
  status: 'active' | 'withdrawn' | 'expired';
}

type ConsentPurpose =
  | 'booking_processing'             // Process bookings (legitimate interest)
  | 'identity_verification'          // Verify identity for travel
  | 'visa_application'               // Submit visa application on behalf
  | 'communication'                  // Send booking updates and offers
  | 'document_storage'               // Store documents for future trips
  | 'analytics'                      // Use data for service improvement
  | 'third_party_sharing'            // Share with suppliers for booking
  | 'marketing'                      // Marketing communications
  | 'profiling';                     // Build customer profile for personalization

type DataType =
  | 'personal_identity'              // Name, DOB, nationality
  | 'government_id'                  // Passport, Aadhaar, PAN
  | 'contact_info'                   // Phone, email, address
  | 'financial_info'                 // Payment methods, bank details
  | 'travel_history'                 // Past trips, preferences
  | 'biometric'                      // Passport photo, selfie
  | 'location_data';                 // Travel destinations, tracking

// Consent flow:
// At booking: "To process your booking, we need to collect and store:
//   - Personal identity (name, DOB) — Required
//   - Government ID (passport) — Required for international travel
//   - Contact info (phone, email) — Required
//   - Travel history — Optional (helps us serve you better)
//
//   [ ] I consent to document storage for future trips
//   [ ] I consent to marketing communications
//
//   [Agree & Continue]"
//
// Consent withdrawal:
// Customer can withdraw consent at any time:
// "I want to delete my stored documents"
// → System checks: Are there active bookings requiring these documents?
//   If yes: "These documents are needed for your upcoming trip.
//           They will be deleted after trip completion."
//   If no: "Documents will be deleted within 30 days per our policy."

// DPDP Act compliance:
// 1. Notice: Clear notice before collecting personal data
// 2. Consent: Free, specific, informed, unambiguous consent
// 3. Purpose limitation: Data used only for stated purpose
// 4. Data minimization: Collect only what's necessary
// 5. Storage limitation: Retain only as long as needed
// 6. Right to access: Customer can see all data held
// 7. Right to correction: Customer can correct inaccurate data
// 8. Right to erasure: Customer can request deletion
// 9. Right to data portability: Customer can export their data
// 10. Right to nominate: Customer can nominate someone to exercise rights
//     in case of death or incapacity
```

### Data Retention & Deletion

```typescript
interface DataRetentionPolicy {
  dataType: DataType;
  retentionPeriod: string;
  justification: string;
  deletionMethod: DeletionMethod;
  legalBasis: string;
}

// Retention periods:
// Active booking documents: Until trip completion + 90 days
// Completed trip documents: 7 years (Income Tax Act, GST Act requirement)
// Cancelled trip documents: 1 year from cancellation
// Marketing consent data: Until consent withdrawn + 30 days
// KYC documents (forex): 5 years (PMLA requirement)
// Audit trail: 8 years (Companies Act requirement)
// Customer profile: Until account deletion + 30 days

// Deletion methods:
// 'soft_delete': Mark as deleted, retain in encrypted backup for 30 days
// 'hard_delete': Permanently remove from all storage
// 'anonymize': Remove PII, retain aggregate data
// 'archive': Move to cold storage (legal hold only)

// Customer data deletion workflow:
// 1. Customer requests deletion ("Delete my account and all data")
// 2. System checks for:
//    a. Active bookings → Cannot delete, explain why
//    b. Pending refunds → Cannot delete until resolved
//    c. Legal holds → Cannot delete until hold released
//    d. Tax/legal retention requirements → Partial deletion
// 3. Deletion plan presented to customer:
//    "The following will be deleted within 30 days:
//     - Profile and login credentials: Immediately
//     - Documents: Within 7 days
//     - Communication history: Within 14 days
//     - Booking details: Anonymized (retained 7 years for tax purposes)
//     - Payment records: Anonymized (retained 7 years for audit)"
// 4. Customer confirms
// 5. Deletion processed in phases
// 6. Confirmation email sent when complete

interface DataDeletionJob {
  jobId: string;
  customerId: string;
  requestedAt: Date;
  phases: DeletionPhase[];
  status: 'scheduled' | 'in_progress' | 'completed';
  completedAt?: Date;
}

interface DeletionPhase {
  dataType: string;
  scheduledAt: Date;
  completedAt?: Date;
  status: 'pending' | 'in_progress' | 'completed';
  recordsAffected: number;
}
```

### Cross-Border Data Transfer

```typescript
interface CrossBorderTransfer {
  transferId: string;
  dataType: DataType;
  sourceCountry: string;
  destinationCountry: string;
  recipient: string;
  purpose: string;
  legalBasis: string;
  safeguards: string[];
}

// Cross-border scenarios:
// 1. Booking data to international airlines (India → US/EU/Singapore)
// 2. Passport data to visa processing centers (India → destination country)
// 3. Payment data to international payment gateways
// 4. Cloud storage (India → AWS/Azure regions)
// 5. Customer support data (India → support team in different region)

// Data localization requirements:
// RBI: Payment data must be stored in India (can be processed abroad, but stored locally)
// DPDP Act: Data can be transferred to countries notified by government
// GST: Financial records must be available in India for audit
// IT Act: Reasonable security practices for sensitive data

// Safeguards for cross-border transfer:
// 1. Encryption in transit (TLS 1.3)
// 2. Data processing agreements with recipients
// 3. Standard contractual clauses
// 4. Purpose limitation (data used only for stated purpose)
// 5. Breach notification (recipient must notify within 72 hours)
// 6. Right to audit (agency can audit recipient's data practices)
```

### Customer Data Rights

```typescript
interface CustomerDataRights {
  accessRequest: DataAccessRequest;
  correctionRequest: DataCorrectionRequest;
  deletionRequest: DataDeletionRequest;
  portabilityRequest: DataPortabilityRequest;
  nominationRequest: NominationRequest;
}

interface DataAccessRequest {
  requestId: string;
  customerId: string;
  requestDate: Date;
  responseDeadline: Date;            // 30 days per DPDP Act
  dataPackage: CustomerDataPackage;
  status: 'pending' | 'processing' | 'completed';
}

interface CustomerDataPackage {
  profile: CustomerProfile;
  documents: DocumentMetadata[];     // List of stored documents (not actual files)
  bookings: BookingSummary[];
  payments: PaymentSummary[];
  communications: CommunicationLog[];
  consentHistory: ConsentRecord[];
  auditTrail: AuditLogSummary[];
}

// Data portability:
// Customer requests data export:
// → Generate JSON/CSV package with all customer data
// → Include: profile, bookings, payments, preferences
// → Exclude: documents (too sensitive for portable format)
// → Available formats: JSON, CSV
// → Download link (expires in 48 hours)
// → Purpose: Customer can take data to another travel agency

// Grievance redressal (DPDP Act requirement):
// Data Principal (customer) → Grievance Officer (agency)
// Response time: 30 days
// If unsatisfied → Data Protection Board of India
// Agency must have a designated Grievance Officer
// Contact details must be published on website
```

---

## Open Problems

1. **Consent fatigue** — Asking for consent at every step frustrates customers. Need layered consent (one-time with granular controls, not repeated prompts).

2. **Deletion conflicts** — Customer wants data deleted, but tax law requires 7-year retention. The overlap between privacy rights and legal obligations is complex.

3. **Cross-border complexity** — Travel data inherently crosses borders (booking a Singapore hotel from India). Data localization requirements may conflict with service needs.

4. **Consent for minors** — Children's data requires parental consent. Verifying parental relationship adds complexity to family trip bookings.

5. **Third-party data sharing** — Booking requires sharing customer data with airlines and hotels. Each third party has their own privacy policy. Tracking the data chain is hard.

---

## Next Steps

- [ ] Design consent management system with granular controls
- [ ] Build data retention and deletion automation
- [ ] Create customer data rights portal (access, correction, deletion, portability)
- [ ] Design cross-border data transfer safeguards
- [ ] Study privacy compliance (DPDP Act implementation, GDPR patterns)
