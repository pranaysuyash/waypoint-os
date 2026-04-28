# Data Privacy & Consent Management — Privacy by Design

> Research document for privacy-by-design architecture, data minimization, anonymization techniques, and privacy impact assessments.

---

## Key Questions

1. **How do we embed privacy into system design from the start?**
2. **What data minimization strategies reduce privacy risk?**
3. **What anonymization and pseudonymization techniques apply to travel data?**
4. **How do we conduct privacy impact assessments (PIAs)?**
5. **What's the data architecture for privacy compliance?**

---

## Research Areas

### Privacy-by-Design Principles

```typescript
interface PrivacyByDesign {
  principles: PbDPrinciple[];
  architecture: PrivacyArchitecture;
  minimization: DataMinimization;
  anonymization: AnonymizationFramework;
  impactAssessment: PrivacyImpactAssessment;
}

// Seven principles of Privacy by Design (Cavoukian):
//
// 1. PROACTIVE NOT REACTIVE — Privacy built in, not bolted on
//    - Design systems with privacy as default setting
//    - Don't collect data "just in case" — collect only what's needed
//    - Encrypt data at rest and in transit by default
//
// 2. PRIVACY AS DEFAULT — Maximum privacy automatically
//    - All optional data sharing: OFF by default
//    - Data retention: Minimum required by law
//    - Access controls: Least privilege by default
//    - Marketing: Opt-in, not opt-out
//
// 3. PRIVACY EMBEDDED IN DESIGN — Integral, not add-on
//    - Privacy requirements in every feature spec
//    - Privacy review in code review checklist
//    - Privacy test cases in test suite
//    - Privacy metrics in sprint reviews
//
// 4. FULL FUNCTIONALITY — Privacy AND utility, not trade-off
//    - Analytics on anonymized data instead of raw data
//    - Recommendations without individual tracking
//    - Fraud detection with pseudonymized identifiers
//
// 5. END-TO-END SECURITY — Full lifecycle protection
//    - Data encrypted from collection to deletion
//    - Access logged at every stage
//    - Secure deletion (crypto-shredding for backups)
//
// 6. VISIBILITY AND TRANSPARENCY — Open about data practices
//    - Public privacy policy in plain language
//    - Data inventory published and accessible
//    - Audit results shared with data principals
//
// 7. RESPECT FOR USER PRIVACY — User-centric design
//    - Granular consent controls
//    - Easy data access and export
//    - Simple withdrawal process
//    - Responsive to privacy inquiries

interface PrivacyArchitecture {
  dataClassification: DataClassification;
  dataFlow: DataFlowMapping;
  storage: PrivacyStorage;
  access: PrivacyAccessControl;
}

interface DataClassification {
  levels: ClassificationLevel[];
  rules: ClassificationRule[];
  inventory: DataInventory;
}

interface ClassificationLevel {
  level: number;
  name: string;
  description: string;
  examples: string[];
  protections: ProtectionRequirement[];
}

// Data classification levels:
//
// Level 4 — RESTRICTED (highest sensitivity):
//   Government IDs: Aadhaar, PAN, passport, visa
//   Financial: Credit card numbers, bank account details
//   Biometric: Fingerprints, facial recognition data
//   Medical: Health conditions, vaccination records
//   Protections:
//     - Encrypted at rest (AES-256)
//     - Encrypted in transit (TLS 1.3)
//     - Access: Named individuals only, MFA required
//     - Logging: Every access recorded
//     - Retention: Minimum required by law
//     - Masking: Display as "XXXX-XXXX-1234" in UI
//     - Export: Requires DPO approval
//
// Level 3 — CONFIDENTIAL:
//   PII: Full name + contact details + address
//   Travel plans: Full itinerary with dates, destinations
//   Payment data: Transaction history, refund records
//   Communications: Message content, call recordings
//   Corporate: Employee ID, department, cost center
//   Protections:
//     - Encrypted at rest (AES-256)
//     - Access: Role-based, justified access only
//     - Logging: Access recorded
//     - Retention: As per consent + legal requirements
//     - Sharing: Consent required for third parties
//
// Level 2 — INTERNAL:
//   Aggregated analytics: Destination popularity, booking trends
//   Operational data: Agent performance, response times
//   System data: Logs, metrics, error reports
//   Protections:
//     - Encrypted at rest (AES-256)
//     - Access: Role-based
//     - Retention: 1 year standard
//     - Anonymization: No individual-level data
//
// Level 1 — PUBLIC:
//   Destination guides, public content
//   Agency listings, public storefront data
//   Protections: Integrity controls only

// Data inventory for travel platform:
// Each data store mapped with classification level and purpose:
//
// PostgreSQL (Supabase):
//   customers table → Level 3 (PII, contact)
//   passports table → Level 4 (government ID)
//   trips table → Level 3 (travel plans)
//   payments table → Level 3 (financial)
//   consents table → Level 3 (privacy records)
//   destinations table → Level 1 (public)
//   analytics_aggregate → Level 2 (anonymized)
//
// Redis Cache:
//   Session tokens → Level 3 (auto-expire 24h)
//   Search results → Level 2 (no PII in cache)
//   Rate limit counters → Level 1
//
// Meilisearch:
//   Destination index → Level 1 (public)
//   Trip search → Level 3 (contains customer names)
//
// S3 / Object Storage:
//   Passport scans → Level 4 (encrypted, access-controlled)
//   Invoice PDFs → Level 3 (contains financial data)
//   Destination photos → Level 1 (public)
//
// Data flow mapping:
// Every data flow documented with:
// - Source system → Destination system
// - Data categories transferred
// - Classification level
// - Legal basis (consent, contract, legal obligation)
// - Encryption in transit
// - Purpose limitation
```

### Data Minimization & Anonymization

```typescript
interface DataMinimization {
  collection: CollectionMinimization;
  storage: StorageMinimization;
  processing: ProcessingMinimization;
  sharing: SharingMinimization;
}

// Collection minimization rules:
// 1. Only collect data required for the specific purpose
//    Booking: Need name, contact, destination, dates
//    Don't need: Social media profiles, employer name (unless corporate)
//
// 2. Use the least sensitive identifier possible
//    For trip tracking: Use trip ID, not customer Aadhaar
//    For analytics: Use anonymous session ID, not email
//
// 3. Prefer aggregated data over individual data
//    Revenue report: Aggregate by destination, not per-customer
//    Popular packages: Count bookings, not list travelers
//
// 4. Delete data when purpose is fulfilled
//    Price monitoring data: Delete after booking confirmed
//    Search history: Anonymize after 30 days
//    Location tracking: Delete 30 days after trip completion
//
// Storage minimization:
// - Auto-delete drafts older than 90 days
// - Auto-anonymize completed trips after 3 years (retain financials only)
// - Auto-delete search history older than 90 days
// - Auto-delete communication content after 1 year (retain metadata)
// - Crypto-shredding: Encrypt with per-customer key, delete key = "delete" data

interface AnonymizationFramework {
  techniques: AnonymizationTechnique[];
  assessment: ReidentificationRisk;
  testing: AnonymizationTest;
}

type AnonymizationTechnique =
  | 'suppression'                      // Remove identifying fields
  | 'generalization'                   // Replace precise with general (age → age range)
  | 'pseudonymization'                 // Replace identifiers with tokens
  | 'aggregation'                      // Replace individual records with aggregates
  | 'noise_addition'                   // Add statistical noise
  | 'data_masking'                     // Partially hide data ("XXX-XXX-1234")
  | 'synthetic_data';                  // Generate artificial data with same distribution

// Anonymization applications for travel platform:
//
// ANALYTICS:
// Raw: "Rajesh Sharma (rajesh@email.com) booked Kerala trip for ₹48,000"
// Anonymized: "Customer #CUST-78542 booked Kerala trip for ₹48,000"
// Aggregated: "127 customers booked Kerala trips averaging ₹45,200"
//
// RECOMMENDATIONS:
// Raw: Show trips booked by customer's friends
// Anonymized: Show trips popular with similar travelers (no individual data)
//
// FRAUD DETECTION:
// Raw: Check if Aadhaar number was used in previous bookings
// Pseudonymized: Check if tokenized ID matches previous (token from Aadhaar hash)
//
// REPORTING:
// Raw: List of all customers with their booking amounts
// Aggregated: Booking amounts by destination, by month, by package type
//
// Re-identification risk assessment:
// For each anonymized dataset, assess:
// 1. K-anonymity: Each record is indistinguishable from at least K-1 others
//    Target: K ≥ 5 (each person's data matches at least 4 others)
// 2. L-diversity: Sensitive attributes have at least L distinct values per group
//    Target: L ≥ 3 (diverse destinations/prices in each group)
// 3. T-closeness: Distribution of sensitive attribute close to overall distribution
//    Target: Earth mover distance < 0.15
//
// Re-identification risk factors:
// - Small destinations (Lakshadweep → very few travelers → easy to identify)
// - Unique trip combinations (honeymoon + luxury + specific dates)
// - High-value bookings (₹5+ lakh → very few in dataset)
// - Temporal correlation (trip date + known travel from social media)
//
// Mitigation:
// - Minimum group size: Suppress results if group < 5 people
// - Noise: Add ±5% noise to booking amounts
// - Date generalization: Store month, not exact date for analytics
// - Destination grouping: Use region (South India) not specific city
```

### Privacy Impact Assessment

```typescript
interface PrivacyImpactAssessment {
  trigger: PIATrigger;
  process: PIAProcess;
  mitigation: PIAMitigation;
  approval: PIAApproval;
  review: PIAReview;
}

type PIATrigger =
  | 'new_feature'                      // Feature that collects/uses personal data
  | 'new_data_source'                  // Integrating new data source
  | 'new_processor'                    // New third-party data processor
  | 'new_purpose'                      // Using existing data for new purpose
  | 'cross_border'                     // Transferring data internationally
  | 'high_risk_data'                   // Processing children's, biometric, health data
  | 'automated_decision'              // AI-driven decisions about individuals
  | 'large_scale'                      // Processing data at significant scale
  | 'public_profile';                  // Making personal data publicly visible

// PIA process:
//
// Step 1: IDENTIFY (Screening)
// Does this feature/process involve personal data?
//   If no → PIA not needed, document decision
//   If yes → Continue to Step 2
//
// Step 2: DESCRIBE (Data Flow Mapping)
// What data is collected? From whom? For what purpose?
// Where is it stored? Who has access? How long retained?
// Is it shared? With whom? Under what legal basis?
//
// Step 3: ASSESS (Risk Analysis)
// What could go wrong?
// - Unauthorized access (data breach)
// - Purpose creep (using data beyond original purpose)
// - Re-identification (anonymized data deanonymized)
// - Excessive retention (keeping data too long)
// - Cross-border risks (data in jurisdictions with weak protection)
// - Discrimination (AI bias in recommendations)
//
// Step 4: MITIGATE (Controls)
// What controls reduce each risk?
// - Encryption, access controls, audit logging
// - Data minimization, anonymization, purpose limitation
// - Consent management, retention policies, deletion workflows
// - DPIA for high-risk processing
//
// Step 5: APPROVE (Sign-off)
// DPO reviews assessment, approves or requests changes
// High-risk: Requires senior management approval
// Very high-risk: Requires Data Protection Board consultation
//
// Step 6: REVIEW (Ongoing)
// Annual review of approved processing
// Trigger-based review if circumstances change
// Audit findings incorporated into reassessment

// PIA template for travel feature:
// Feature: Customer Location Tracking (Duty of Care)
//
// 1. DESCRIPTION:
// Track traveler GPS location during active trips for safety
// and emergency response capability.
//
// 2. DATA INVOLVED:
// - Location coordinates (GPS, lat/lng)
// - Timestamp
// - Device identifier (pseudonymized)
// - Trip ID
//
// 3. LEGAL BASIS:
// Consent (explicit opt-in) + Contractual necessity (duty of care)
//
// 4. DATA FLOW:
// Mobile app (GPS) → API (TLS 1.3) → Database (encrypted)
// → Redis cache (auto-expire 1 hour) → Emergency response system
//
// 5. RISKS:
// - Location data breach: Reveals where someone is/isn't
// - Mission creep: Using tracking for productivity monitoring
// - Re-identification: Location + trip dates = identity
// - Retention: Keeping data after trip completion
//
// 6. MITIGATIONS:
// - Explicit opt-in with clear purpose explanation
// - Auto-delete 30 days after trip completion
// - Access restricted to emergency response team (3 named individuals)
// - All access logged and audited
// - GPS disabled when traveler disables tracking (immediate)
// - Location data never shared with third parties
// - Annual privacy review of this feature
//
// 7. RESIDUAL RISK: LOW
// With mitigations in place, risk is acceptable.
// Approved by DPO on [date].
```

---

## Open Problems

1. **Anonymization vs. analytics quality** — Stronger anonymization reduces data utility. Finding the right balance between privacy protection and analytics usefulness requires ongoing calibration.

2. **Crypto-shredding complexity** — Encrypting each customer's data with a unique key and deleting the key to "erase" data sounds elegant but adds significant complexity to database operations, backups, and search.

3. **AI training data privacy** — Using customer data to train AI models (recommendations, chatbots) creates derived data that is hard to erase. The "right to be forgotten" becomes complex when data is embedded in model weights.

4. **Third-party processor audits** — The platform shares data with airlines, hotels, payment processors. Each is a separate data fiduciary/processor. Auditing their privacy practices at scale is resource-intensive.

5. **Privacy impact assessment scalability** — Every feature that touches personal data needs a PIA. With 50+ features in development, the DPO becomes a bottleneck. Self-service PIA tools with automated risk scoring can help.

---

## Next Steps

- [ ] Implement data classification system with automated tagging
- [ ] Build anonymization pipeline for analytics and reporting
- [ ] Create PIA self-service tool with risk scoring
- [ ] Design crypto-shredding architecture for backup erasure
- [ ] Study privacy engineering frameworks (Google Privacy Sandbox, Apple Privacy, NIST Privacy Framework)
