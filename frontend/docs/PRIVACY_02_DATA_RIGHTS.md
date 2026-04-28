# Data Privacy & Consent Management — Data Subject Rights

> Research document for data access, correction, erasure, and portability rights under DPDP Act, GDPR, and global privacy regulations.

---

## Key Questions

1. **How do we implement data subject rights at scale?**
2. **What's the automated pipeline for data access and export?**
3. **How does data erasure work with legal retention requirements?**
4. **What verification is needed before fulfilling data requests?**
5. **How do we handle cross-border data rights requests?**

---

## Research Areas

### Data Subject Rights Framework

```typescript
interface DataSubjectRights {
  access: DataAccessRight;
  correction: DataCorrectionRight;
  erasure: DataErasureRight;
  portability: DataPortabilityRight;
  objection: DataObjectionRight;
  nomination: DataNominationRight;
}

interface DataAccessRight {
  // DPDP Act Section 10: Right to access
  // Customer can request: What data we have, how it's used, who it's shared with
  request: DataRequest;
  verification: IdentityVerification;
  compilation: DataCompilation;
  delivery: DataDelivery;
}

interface DataRequest {
  id: string;
  type: DataRequestType;
  requesterId: string;                 // Data principal ID
  submittedAt: Date;
  status: RequestStatus;
  assignedTo?: string;                 // DPO or privacy team
  dueDate: Date;                       // 30 days from submission
  completedAt?: Date;
}

type DataRequestType =
  | 'access'                           // "What data do you have about me?"
  | 'correction'                       // "Fix this data about me"
  | 'erasure'                         // "Delete my data"
  | 'portability'                      // "Give me my data in a file"
  | 'objection'                        // "Stop using my data for X purpose"
  | 'nomination';                      // "Let [person] act on my behalf"

// Data access request fulfillment:
// 1. Request received (web form, email, WhatsApp)
// 2. Identity verification required
//    - Option A: Log in to account (strongest — already authenticated)
//    - Option B: Email verification link + OTP to registered phone
//    - Option C: Government ID verification (for non-account holders)
// 3. Request logged in privacy management system
// 4. Data compilation begins (automated)
// 5. Data review by DPO (verify nothing exempt)
// 6. Delivery to requester (secure download link, 48-hour expiry)
//
// Data compilation output (JSON structure):
// {
//   "request_id": "DSR-2026-00142",
//   "requested_at": "2026-04-28",
//   "data_principal": {
//     "profile": { "name": "...", "email": "...", "phone": "..." },
//     "addresses": [...],
//     "government_ids": [
//       { "type": "passport", "partial": "P******1234" }  // Masked
//     ]
//   },
//   "trips": [
//     {
//       "id": "TRV-45678",
//       "destination": "Kerala",
//       "dates": "2026-03-15 to 2026-03-20",
//       "status": "completed",
//       "travelers": [...],
//       "bookings": [
//         { "type": "hotel", "name": "Taj Residency", "amount": 45000 }
//       ]
//     }
//   ],
//   "payments": [...],
//   "communications": [
//     { "channel": "whatsapp", "count": 47, "first": "...", "last": "..." }
//   ],
//   "consents": [
//     { "purpose": "booking_fulfillment", "status": "given", "date": "..." }
//   ],
//   "documents_generated": [
//     { "type": "itinerary", "trip": "TRV-45678", "date": "..." }
//   ],
//   "data_shared_with": [
//     { "entity": "Taj Hotels", "purpose": "hotel_booking", "data": ["name", "dates"] }
//   ]
// }
//
// Exemptions (data that can be withheld):
// - Legal privilege (communications with legal counsel)
// - Trade secrets (pricing algorithms, supplier contracts)
// - Third-party data that would reveal others' identities
// - Data subject to ongoing investigation (fraud, security)
// - Data required for legal compliance (cannot erase tax records)

interface DataCorrectionRight {
  // DPDP Act Section 11: Right to correction
  // Customer can request: Fix inaccurate or incomplete data
  correctionRequest: CorrectionRequest;
  verification: CorrectionVerification;
  propagation: CorrectionPropagation;
}

// Data correction flow:
// 1. Customer identifies incorrect data in their profile/trips
// 2. Submits correction request with:
//    - Field to correct
//    - Current value
//    - Corrected value
//    - Supporting evidence (optional — e.g., updated passport scan)
// 3. System auto-corrects if simple (name typo, phone number)
// 4. Manual review if complex (identity change, government ID correction)
// 5. Propagate correction to all systems:
//    - Primary database
//    - Search index
//    - Analytics warehouse (if PII present)
//    - Third-party processors (airlines, hotels already shared with)
//    - Cached data (invalidate CDN, Redis caches)
// 6. Confirmation to customer with updated data view
//
// Correction propagation challenges:
// - Airline already has old passport number → Request PNR update
// - Hotel booking under old name → Request name change with hotel
// - Invoice already generated with old GST → Credit note + new invoice
// - Timeline: Propagation to third parties within 15 days

interface DataErasureRight {
  // DPDP Act Section 12: Right to erasure
  // Customer can request: Delete my personal data
  erasureRequest: ErasureRequest;
  assessment: ErasureAssessment;
  execution: ErasureExecution;
  confirmation: ErasureConfirmation;
}

interface ErasureAssessment {
  fullyErasable: DataCategory[];
  partiallyErasable: ErasureWithRetention[];
  exempt: ErasureExemption[];
}

// Erasure assessment for travel platform:
//
// FULLY ERASABLE (delete immediately):
// - Marketing preferences and history
// - Search and browsing history
// - Location tracking data (post-trip)
// - Behavioral analytics data
// - AI recommendation profiles
// - Non-essential communications metadata
//
// PARTIALLY ERASABLE (anonymize or retain partial):
// - Trip history: Retain destination, dates, amounts (anonymized)
//   Reason: Required for financial reporting (aggregate)
// - Communication logs: Retain fact of communication, delete content
//   Reason: Dispute resolution reference
//
// EXEMPT (cannot erase — legal retention requirements):
// - GST invoices and tax records: 8 years (CGST Act)
// - TCS collection records: 7 years (Income Tax Act)
// - KYC documents (Aadhaar, PAN): 5 years post-relationship (PMLA)
// - Payment transaction records: 8 years (RBI guidelines)
// - Insurance records: Duration of policy + 3 years (IRDAI)
// - Contract records: Duration of contract + 3 years
//
// Erasure execution pipeline:
// Phase 1 (Immediate — 24 hours):
// - Deactivate account
// - Remove from search indexes
// - Delete from caches
// - Revoke all active sessions and tokens
// - Stop all communications
//
// Phase 2 (Short-term — 7 days):
// - Delete from primary databases (non-exempt data)
// - Delete from analytics warehouse
// - Delete from backup systems (next backup cycle)
// - Anonymize in aggregate datasets
// - Notify third-party processors to delete shared data
//
// Phase 3 (Long-term — 30 days):
// - Delete from archival storage
// - Delete from log systems
// - Confirm third-party deletion completed
// - Generate erasure certificate
//
// Erasure certificate:
// "This certifies that personal data for [identifier] has been erased
//  from [Agency Name] systems on [date], with the following exceptions
//  retained for legal compliance: [list]. Erasure confirmation from
//  third-party processors: [list]. Certificate ID: ERS-2026-00142"

// Data portability right:
interface DataPortabilityRight {
  // DPDP Act: Right to receive data in machine-readable format
  formats: ExportFormat[];
  scope: ExportScope;
  delivery: PortabilityDelivery;
}

type ExportFormat = 'json' | 'csv' | 'xml' | 'pdf';

// Portability export scope:
// Everything the platform holds about the data principal:
// - Profile data
// - Trip history with full details
// - Payment history
// - Communication history
// - Documents generated
// - Consent history
// - Preferences and settings
//
// Not included in portability:
// - Inferred data (AI recommendations, risk scores)
// - Data about other people
// - Platform-internal data (logs, debug traces)
// - Third-party proprietary data (supplier rates, etc.)
//
// Portability delivery:
// - Encrypted ZIP file (AES-256)
// - Password sent separately via SMS
// - Download link expires in 48 hours
// - File size estimate: 5-50 MB per customer (depending on history)
// - Can also be sent on physical media (USB) upon request
//
// Rate limiting:
// One portability request per 30 days
// Prevent abuse: Automated requests detected and throttled
```

---

## Open Problems

1. **Erasure vs. legal retention conflicts** — Customers request "delete everything" but tax, KYC, and regulatory laws require retaining significant data for 5-8 years. Explaining why some data cannot be erased without undermining trust is a communication challenge.

2. **Third-party deletion verification** — After sharing data with 10+ suppliers (airline, hotel, car rental, insurance), verifying that all have actually deleted the data requires follow-up coordination that is operationally expensive.

3. **Identity verification for non-account holders** — Someone who inquired via WhatsApp but never created an account can still exercise data rights. Verifying identity without an account system requires alternative verification (phone number OTP + email confirmation).

4. **Bulk data rights requests** — A corporate client may request data access/erasure for all 500 employees who traveled. Fulfilling bulk requests requires batch processing while maintaining individual per-person audit trails.

5. **Real-time systems erasure** — Data in search indexes, caches, and streaming systems cannot always be immediately deleted. Eventual consistency means data may briefly remain visible after erasure is confirmed.

---

## Next Steps

- [ ] Build data subject rights request management system with verification
- [ ] Create automated data compilation pipeline for access/portability requests
- [ ] Implement erasure execution pipeline with legal retention exemption engine
- [ ] Design correction propagation system across primary and third-party systems
- [ ] Study privacy rights platforms (OneTrust Data Subject Rights, DataGrail, Transcend)
