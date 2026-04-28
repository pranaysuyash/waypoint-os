# Customer Identity & Verification — Passport & Travel Documents

> Research document for passport management, document expiry tracking, and travel document intelligence.

---

## Key Questions

1. **How do we manage passport data across the trip lifecycle?**
2. **What's the passport validity checking model?**
3. **How do we track document expiry and renewal reminders?**
4. **What's the multi-passport handling for families and groups?**
5. **How do we integrate document data with visa and booking systems?**

---

## Research Areas

### Passport Management

```typescript
interface PassportProfile {
  profileId: string;
  travelerId: string;
  passport: PassportData;
  otherDocuments: TravelDocument[];
  verificationStatus: VerificationStatus;
  expiryTracking: ExpiryTracking;
}

interface PassportData {
  passportNumber: string;            // Encrypted at rest
  fullName: string;                  // Exactly as in passport
  nationality: string;
  dateOfBirth: Date;
  placeOfBirth: string;
  gender: 'M' | 'F' | 'X';
  issueDate: Date;
  expiryDate: Date;
  issuingCountry: string;
  placeOfIssue: string;
  passportType: 'regular' | 'diplomatic' | 'official' | 'emergency';
  machineReadableZone?: string;      // MRZ data from OCR
  photoReference?: string;           // Stored passport photo
}

interface TravelDocument {
  documentType: 'visa' | 'oci_card' | 'greencard' | 'residence_permit' | 'travel_insurance' | 'vaccination_cert' | 'international_driving_permit';
  documentId: string;
  issuingCountry: string;
  issueDate: Date;
  expiryDate: Date;
  applicableCountries: string[];
  notes: string;
}

// Passport management features:
// 1. One-time capture: Scan passport once, reuse across trips
// 2. Expiry tracking: Alert when passport expiring within 6 months
// 3. Validity check: Auto-check 6-month validity rule for destination
// 4. Name format: Store name exactly as in passport for airline bookings
// 5. Family linking: Group family passports for family trips
// 6. Renewal reminders: Notify when renewal is due
```

### Validity Checking

```typescript
interface PassportValidityCheck {
  passportId: string;
  destination: string;
  travelDates: DateRange;
  isValid: boolean;
  issues: ValidityIssue[];
  rules: ValidityRule[];
}

interface ValidityIssue {
  issue: string;
  severity: 'blocking' | 'warning';
  resolution: string;
}

// Common validity rules:
// 1. Six-month rule: Most countries require passport validity 6 months beyond departure date
//    - Exception: Some countries accept 3 months (UK, some EU countries)
//    - India-specific: Indian passports must be valid 6 months beyond return date
//
// 2. Blank pages: Some countries require 1-2 blank pages for visa stamps
//    - South Africa: 2 blank facing pages
//    - Most Schengen: 1 blank page
//
// 3. Damage check: Damaged passports may be rejected
//    - Only visual check by agent (not automated)
//
// 4. Name consistency: Booking name must match passport name exactly
//    - Airlines are strict about name matching
//    - MRZ (machine-readable zone) name is authoritative
//
// 5. Second passport: Some travelers hold dual passports
//    - Enter and exit a country on the same passport
//    - Some destinations require specific passport for visa-free entry

// Validity check flow during booking:
// 1. Agent enters travel destination and dates
// 2. System checks all travelers' passport profiles
// 3. For each traveler:
//    a. Is passport valid for travel dates?
//    b. Does it meet 6-month rule for destination?
//    c. Are there enough blank pages?
//    d. Is visa required? Is visa obtained?
// 4. Flag any issues before booking confirmation
// 5. Prevent booking if blocking issues found
//    "Cannot proceed: Traveler Rajesh Sharma's passport expires on Aug 15,
//     but Singapore requires 6-month validity (need Feb 2027).
//     Resolution: Renew passport before booking."
```

### Expiry & Renewal Tracking

```typescript
interface ExpiryTracking {
  documentId: string;
  expiryDate: Date;
  reminderSchedule: ReminderSchedule[];
  renewalStatus: RenewalStatus;
}

interface ReminderSchedule {
  daysBeforeExpiry: number;
  channel: 'in_app' | 'email' | 'whatsapp' | 'sms';
  message: string;
  audience: 'agent' | 'customer' | 'both';
}

// Reminder schedule for passport expiry:
// 365 days before: Annual check reminder (in-app to agent)
// 180 days before: "Passport expires in 6 months" (email to customer)
// 90 days before: "Renew passport now — upcoming travel may be affected" (WhatsApp to customer)
// 30 days before: "URGENT: Passport expiring. Cannot book international travel." (email + SMS)
// On expiry: "Passport expired. Update passport details to enable international bookings."

// Renewal workflow:
// 1. Customer initiates passport renewal
// 2. Agent updates traveler profile: "Passport pending renewal"
// 3. Customer provides new passport details after renewal
// 4. Agent verifies and updates profile
// 5. System re-validates all pending/upcoming trips against new passport
// 6. Passport number history maintained for audit

// Document renewal in India:
// Passport renewal via Passport Seva Kendra (PSK) or online
// Tatkal: 1-3 weeks (₹3,500-5,000 additional)
// Normal: 4-6 weeks
// Required: Old passport, address proof, photographs
// Agent can assist with appointment booking and documentation
```

### Multi-Traveler Document Management

```typescript
interface TravelerDocumentManager {
  tripId: string;
  travelers: TravelerDocuments[];
  completionStatus: DocumentCompletionStatus;
  bulkActions: BulkDocumentAction[];
}

interface TravelerDocuments {
  travelerId: string;
  name: string;
  role: 'primary' | 'spouse' | 'child' | 'parent' | 'friend';
  documents: RequiredDocuments;
  completionPercent: number;
}

interface DocumentCompletionStatus {
  totalTravelers: number;
  completedTravelers: number;
  pendingDocuments: string[];        // What's still needed
  blockingIssues: string[];          // Prevents booking
}

// Family document management:
// Trip: Singapore (2 adults, 2 children)
// Father: Passport ✓, Visa ✓ → Complete
// Mother: Passport ✓, Visa pending → 80% complete
// Child 1 (8 yrs): Passport ✓, Visa pending → 80% complete
// Child 2 (3 yrs): Passport pending, Visa pending → 20% complete
//
// Bulk actions:
// "Send reminder to all travelers with pending documents"
// "Download all passports as ZIP"
// "Upload documents for all travelers"
// "Check validity for all travelers"

// Child-specific considerations:
// Children's passports in India: Valid for 5 years (vs. 10 for adults)
// Both parents' consent required for child passport application
// Child traveling with one parent: May need NOC from other parent
// Some countries require birth certificate for minors
```

---

## Open Problems

1. **Passport photo quality** — Customers send passport scans via WhatsApp. The quality is often too poor for visa applications. Need quality standards and resubmission workflow.

2. **Dual passport handling** — An NRI with Indian and US passports. Which passport to use for booking? Depends on entry/exit requirements. Complex routing logic needed.

3. **Real-time validity** — A passport is valid when checked at booking but expires before travel. Need re-validation as travel date approaches.

4. **Privacy of passport data** — Passport numbers and personal details are highly sensitive. Data breach is catastrophic. Need maximum security measures.

5. **Group document management** — A school trip with 40 students. Managing 40 passports, 40 visas, 40 consent forms is a logistical challenge. Need bulk processing tools.

---

## Next Steps

- [ ] Design passport profile with expiry tracking and renewal workflow
- [ ] Build validity checking engine with country-specific rules
- [ ] Create multi-traveler document management dashboard
- [ ] Design passport OCR extraction with quality validation
- [ ] Study passport management (VFS Global, Passport Seva, travel document platforms)
