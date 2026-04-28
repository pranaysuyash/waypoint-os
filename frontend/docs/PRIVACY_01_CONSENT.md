# Data Privacy & Consent Management — Consent Lifecycle

> Research document for consent collection, management, withdrawal, and audit trails under India's DPDP Act and global privacy regulations.

---

## Key Questions

1. **How do we collect and manage consent across multiple touchpoints?**
2. **What consent models are required by the DPDP Act (India)?**
3. **How do we handle consent withdrawal and data deletion?**
4. **What's the consent audit trail for regulatory compliance?**
5. **How do parental consent and minor protection work?**

---

## Research Areas

### Consent Data Model

```typescript
interface ConsentManagement {
  collection: ConsentCollection;
  storage: ConsentStore;
  lifecycle: ConsentLifecycle;
  audit: ConsentAudit;
}

interface ConsentRecord {
  id: string;
  dataPrincipal: string;               // Customer / traveler ID
  dataFiduciary: string;               // Agency ID (who collects)
  processor?: string;                  // Third-party processor ID
  purposes: ConsentPurpose[];
  status: ConsentStatus;
  collectedAt: Date;
  collectedVia: ConsentChannel;
  expiresAt?: Date;
  withdrawnAt?: Date;
  version: string;                     // Consent version for audit
}

type ConsentStatus =
  | 'pending'                          // Consent requested, not yet given
  | 'given'                            // Explicitly consented
  | 'implicit'                         // Implied by action (account creation)
  | 'withdrawn'                        // Explicitly withdrawn
  | 'expired'                          // Time-based expiry
  | 'revoked';                         // Revoked by platform (regulatory)

// DPDP Act (Digital Personal Data Protection Act, 2023) — India:
// Key requirements:
// 1. Data Fiduciary: Agency that determines purpose of data processing
// 2. Data Principal: Individual whose data is collected (customer, traveler)
// 3. Data Processor: Third party that processes data on behalf of fiduciary
// 4. Consent must be: Free, specific, informed, unconditional, unambiguous
// 5. Clear affirmative action required (no pre-ticked boxes)
// 6. Purpose limitation: Data used only for stated purposes
// 7. Right to withdraw consent at any time
// 8. Right to access, correct, erase personal data
// 9. Right to nominate another person to exercise rights
// 10. Cross-border transfer: Only to countries whitelisted by government
//
// Significant Data Fiduciary (SDF):
// - Based on volume and sensitivity of data processed
// - Travel platforms processing 10L+ customers likely qualify
// - Additional obligations: Data Protection Impact Assessment (DPIA)
// - Appoint Data Protection Officer (DPO)
// - Periodic audits by independent auditor
//
// Penalties:
// - Up to ₹250 crore per instance
// - Up to ₹50 crore for data breach notification failures
// - No criminal penalties (civil only)
// - Adjudicated by Data Protection Board of India

interface ConsentPurpose {
  purpose: DataPurpose;
  description: string;                 // Plain-language explanation
  categories: DataCategory[];
  retention: RetentionPolicy;
  required: boolean;                   // True = service won't work without it
  withdrawalImpact: string;            // What happens if consent withdrawn
}

type DataPurpose =
  | 'booking_fulfillment'              // Processing trip bookings
  | 'communication'                    // Sending trip updates, messages
  | 'payment_processing'               // Processing payments, refunds
  | 'document_generation'              // Creating itineraries, invoices
  | 'customer_support'                 // Handling support requests
  | 'marketing'                        // Promotional communications
  | 'analytics'                        // Usage analytics, reporting
  | 'personalization'                  // Recommendations, preferences
  | 'fraud_prevention'                 // Risk scoring, identity verification
  | 'regulatory_compliance'            // GST, TCS, KYC requirements
  | 'traveler_safety'                  // Duty of care, emergency contact
  | 'third_party_sharing'              // Sharing with airlines, hotels
  | 'research'                         // Aggregated research purposes
  | 'ai_training';                     // Training ML models

type DataCategory =
  | 'identity'                         // Name, DOB, gender
  | 'contact'                          // Email, phone, address
  | 'government_id'                    // Passport, Aadhaar, PAN
  | 'financial'                        // Payment methods, transaction history
  | 'travel_history'                   // Past trips, preferences
  | 'location'                         // Travel destinations, tracking data
  | 'communication'                    // Messages, call logs
  | 'behavioral'                       // Search history, browsing patterns
  | 'biometric'                        // Photos, fingerprints (visa processing)
  | 'health'                           // Medical conditions, vaccination records
  | 'family'                           // Family member details, emergency contacts
  | 'corporate'                        // Company, employee ID, cost center
  | 'children';                        // Data about minors (<18 years)

// Consent purposes for travel platform:
//
// REQUIRED (service won't work without):
// booking_fulfillment: Process and manage trip bookings
//   Categories: identity, contact, travel_history, government_id
//   Retention: 7 years (tax/legal requirement)
//   Withdrawal impact: "Cannot process bookings without this data"
//
// payment_processing: Handle payments and refunds
//   Categories: identity, financial, government_id (GST)
//   Retention: 8 years (Income Tax Act requirement)
//   Withdrawal impact: "Cannot process payments without this data"
//
// regulatory_compliance: Meet legal obligations (GST, TCS, KYC)
//   Categories: identity, government_id, financial
//   Retention: 8 years (statutory requirement)
//   Withdrawal impact: "Cannot operate without regulatory compliance"
//
// traveler_safety: Emergency contact and duty of care
//   Categories: contact, family, location
//   Retention: Duration of trip + 1 year
//   Withdrawal impact: "Cannot provide emergency assistance"
//
// OPTIONAL (enhances experience):
// communication: Send trip updates via WhatsApp/Email
//   Categories: contact, travel_history
//   Retention: Until consent withdrawn
//   Withdrawal impact: "Won't receive trip updates via messaging"
//
// marketing: Send deals, offers, travel inspiration
//   Categories: contact, behavioral, travel_history
//   Retention: Until consent withdrawn
//   Withdrawal impact: "Won't receive promotional offers"
//
// personalization: Tailor recommendations to preferences
//   Categories: behavioral, travel_history
//   Retention: Until consent withdrawn
//   Withdrawal impact: "Generic recommendations instead of personalized"
//
// analytics: Understand usage patterns for improvement
//   Categories: behavioral (aggregated, anonymized)
//   Retention: Until consent withdrawn
//   Withdrawal impact: "Platform may not be optimized for your needs"
//
// third_party_sharing: Share booking details with suppliers
//   Categories: identity, contact, government_id, travel_history
//   Retention: Duration of booking relationship
//   Withdrawal impact: "Suppliers cannot prepare for your arrival"

// Consent collection touchpoints:
//
// 1. Account Registration:
//    "Create your account to book trips"
//    Required: booking_fulfillment, payment_processing, regulatory_compliance
//    Optional: ☐ Send me deals and offers (marketing)
//              ☐ Personalize my experience (personalization)
//
// 2. First Booking:
//    "To complete your booking, we need your travel documents"
//    Required: traveler_safety, third_party_sharing
//    Consent: "I agree to share my details with [Airline/Hotel] for this booking"
//
// 3. WhatsApp Communication:
//    "Get trip updates on WhatsApp?"
//    Send via WhatsApp Business API opt-in flow
//    "Reply YES to receive trip updates from [Agency Name]"
//
// 4. Marketing Email:
//    Footer in every email: "Manage preferences | Unsubscribe"
//    One-click unsubscribe required (DPDP Act)
//
// 5. Location Tracking (duty of care):
//    "Enable location sharing for your safety during travel?"
//    Purpose: traveler_safety
//    Duration: Only during active trip dates
//    "Your location is shared only with [Company Name] for safety purposes"
//    Explicit opt-in required (not pre-checked)
```

### Consent Lifecycle Management

```typescript
interface ConsentLifecycle {
  collection: ConsentCollectionFlow;
  modification: ConsentModification;
  withdrawal: ConsentWithdrawal;
  expiry: ConsentExpiry;
}

interface ConsentCollectionFlow {
  touchpoint: ConsentTouchpoint;
  presentation: ConsentPresentation;
  validation: ConsentValidation;
  recording: ConsentRecording;
}

interface ConsentPresentation {
  format: 'banner' | 'modal' | 'inline' | 'settings_page';
  granularity: 'granular' | 'bundled' | 'layered';
  language: string;                    // "en-IN", "hi-IN"
}

// Consent presentation patterns:
//
// GRANULAR (DPDP Act recommended):
// Show each purpose separately with clear toggle:
// ┌─────────────────────────────────────────────────────┐
// │  How we use your data                               │
// │                                                      │
// │  ✅ Trip bookings (required)                        │
// │     Process and manage your travel bookings          │
// │                                                      │
// │  ✅ Payments (required)                             │
// │     Handle payments, refunds, and invoices           │
// │                                                      │
// │  ✅ Safety (required)                               │
// │     Emergency contact and traveler safety            │
// │                                                      │
// │  ☐ WhatsApp updates (optional)                      │
// │     Get real-time trip updates on WhatsApp           │
// │     [Learn more]                                     │
// │                                                      │
// │  ☐ Deals & offers (optional)                        │
// │     Receive personalized travel deals                │
// │     [Learn more]                                     │
// │                                                      │
// │  ☐ Recommendations (optional)                       │
// │     Personalized destination and hotel suggestions   │
// │     [Learn more]                                     │
// │                                                      │
// │  [Save Preferences]                                  │
// └─────────────────────────────────────────────────────┘
//
// Each "Learn more" expands to show:
// - What data is collected
// - Who it's shared with
// - How long it's retained
// - How to withdraw consent
//
// CONSENT VALIDATION:
// - Cannot submit without all required consents checked
// - Optional consents must not be pre-checked
// - Clear "Accept All" / "Reject All" / "Customize" options
// - Language must be plain and understandable (8th grade level)
// - Must be available in Hindi + English (minimum)
// - Version stamp recorded with each consent

// Consent withdrawal flow:
// User navigates to: Settings → Privacy → Manage Consent
//
// Sees all current consents with status and withdrawal option
// Clicks "Withdraw" on a purpose:
//   1. Show impact: "Withdrawing consent for [purpose] means:
//      - [Specific consequences]"
//   2. Confirm: "Are you sure? [Withdraw] [Keep]"
//   3. Process:
//      a. Update consent record status → 'withdrawn'
//      b. Stop all processing for that purpose
//      c. Schedule data deletion (if no other purpose requires it)
//      d. Notify data processors to stop processing
//      e. Record in audit trail
//   4. Confirmation: "Consent withdrawn. [Data deletion scheduled: 30 days]"
//
// Data deletion on consent withdrawal:
// - Immediate: Stop processing, remove from active systems
// - 30 days: Delete from backups, analytics databases
// - Retained: Data required for legal/regulatory purposes
//   (e.g., GST records retained for 8 years regardless of consent)
// - Communication: "Your data for [purpose] will be deleted within 30 days.
//   Some data may be retained for legal compliance.
//   [View retained data] [Download my data]"
//
// Right to data portability (DPDP Act):
// - User can request all their data in machine-readable format
// - Format: JSON or CSV
// - Delivery: Download link (encrypted) or email
// - Timeline: Within 30 days of request
// - Frequency: Once per 30 days (prevent abuse)
//
// Data export contents:
// - Profile data (name, email, phone, addresses)
// - Trip history (all trips with full details)
// - Payment history (transactions, invoices)
// - Communication history (messages, emails)
// - Documents (itineraries, vouchers generated)
// - Consent records (all consent history)
// - Preferences and settings
```

---

## Open Problems

1. **Consent fatigue** — Asking for consent at every touchpoint overwhelms users. Many click "Accept All" without reading, which undermines informed consent. Layered notices (summary + detail) help but don't fully solve this.

2. **Cross-border data transfers** — Travel inherently involves cross-border data (booking a Singapore hotel from India). DPDP Act restricts transfers to whitelisted countries. The whitelist hasn't been fully published yet, creating uncertainty.

3. **Supplier data sharing** — Airlines and hotels require customer data for bookings. If a customer withdraws consent for third-party sharing, existing bookings may be affected. Balancing withdrawal rights with contractual obligations is complex.

4. **Consent for minors** — Travel bookings often include children. DPDP Act requires verifiable parental consent for processing children's data. Age verification and parental consent collection add friction to the booking flow.

5. **Legacy data migration** — Existing customer data collected before DPDP Act enforcement may not have proper consent records. Re-consenting existing users is operationally expensive and risks user churn.

---

## Next Steps

- [ ] Build consent record database with versioned audit trail
- [ ] Create consent collection UI components (banner, modal, settings)
- [ ] Implement consent withdrawal with automated data deletion pipeline
- [ ] Design data subject rights portal (access, correction, erasure, portability)
- [ ] Study consent management platforms (OneTrust, TrustArc, Cookiebot, Osano)
