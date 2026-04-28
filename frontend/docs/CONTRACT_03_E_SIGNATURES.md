# E-Signatures — Digital Signing & Verification

> Research document for electronic signature integration, verification, and legal validity.

---

## Key Questions

1. **Which e-signature providers are viable for a travel agency serving Indian and international clients?**
2. **What constitutes a legally valid e-signature in India (IT Act 2000), EU (eIDAS), US (ESIGN), and other key markets?**
3. **How do we handle signers who are not digitally native (e.g., elderly travelers, small suppliers)?**
4. **What's the right balance between security (multi-factor, biometric) and conversion friction?**
5. **How do we verify signer identity without adding excessive overhead?**
6. **What are the storage and archival requirements for signed documents?**

---

## Provider Landscape

### Tier 1: Full-Service Platforms

| Provider | Strengths | Weaknesses | Pricing Model |
|----------|-----------|------------|---------------|
| **DocuSign** | Market leader, broad integrations, court-tested | Expensive at scale, complex API | Per-envelope |
| **Adobe Sign** | Adobe ecosystem, strong enterprise features | Heavier integration effort | Per-user |
| **HelloSign (Dropbox)** | Simple API, good UX, affordable | Fewer advanced features | Per-user |
| **PandaDoc** | Good for sales workflows, document builder | Less established for legal | Per-user |

### Tier 2: India-Focused

| Provider | Strengths | Weaknesses |
|----------|-----------|------------|
| **Digio** | Aadhaar-based eSign, DSC support, Indian legal compliance | Limited international recognition |
| **eMudhra** | Licensed Certifying Authority, DSC issuance | More traditional, less API-friendly |
| **NTT Data Sign** | Japan/India corridors, enterprise focus | Niche market |

### Tier 3: Embedded / API-First

| Provider | Strengths | Weaknesses |
|----------|-----------|------------|
| **SignWell** | Modern API, fair pricing, good UX | Newer, less case law |
| **GoCanvas** | Mobile-first, field-service oriented | Not travel-specific |
| **Anvil** | PDF filling + e-sign, developer-friendly | Early stage |

### Open Questions for Provider Selection

- Which providers support Aadhaar-based eSign for Indian customers?
- Can we use one provider domestically and another internationally?
- What's the cost structure for high-volume seasonal traffic (peak travel seasons)?
- Do any providers offer white-label signing experiences?

---

## Research Areas

### Legal Validity by Jurisdiction

```typescript
interface SignatureRequirement {
  jurisdiction: string;
  standard: string;
  minimumRequirements: string[];
  acceptedMethods: SignatureMethod[];
  specialCases?: string;
}

type SignatureMethod =
  | 'simple_electronic'    // Click-to-sign, typed name
  | 'advanced_electronic'  // Uniquely linked to signer, tamper-evident
  | 'qualified_electronic' // Certificate-based, equal to handwritten
  | 'digital_signature'    // PKI-based with certifying authority
  | 'aadhaar_esign'        // India-specific, Aadhaar-linked
  | 'wet_ink'              // Physical signature (fallback)
```

**India (IT Act 2000, amended 2008):**
- Electronic signatures recognized via IT Act Section 5
- Aadhaar eSign is valid and widely adopted
- Digital Signature Certificates (DSC) for companies
- Some documents still require notarization (property, specific agreements)

**EU (eIDAS Regulation):**
- Three tiers: Simple, Advanced, Qualified
- Qualified Electronic Signatures (QES) have presumption of legal equivalence
- Cross-border recognition within EU

**US (ESIGN Act + UETA):**
- Broad recognition of electronic signatures
- Some exceptions (wills, family law, certain notices)
- No tiered system like EU

**Research needed:**
- Full list of jurisdictions where the agency operates or plans to operate
- Which contract types require elevated signature levels?
- What are the record-keeping requirements per jurisdiction?

### Signing Workflow

**Questions:**
- Should we use sequential signing (ordered), parallel, or mixed?
- How do we handle in-person signing (agent meets customer)?
- What's the signing experience for mobile vs. desktop?

**Data model sketch:**

```typescript
interface SigningSession {
  sessionId: string;
  contractId: string;
  status: SigningStatus;
  signers: SigningParty[];
  createdAt: Date;
  expiresAt: Date;
  reminderSchedule: ReminderConfig;
}

type SigningStatus =
  | 'created'
  | 'in_progress'
  | 'completed'
  | 'declined'
  | 'expired'
  | 'voided';

interface SigningParty {
  partyId: string;
  email: string;
  name: string;
  role: 'signer' | 'cc' | 'witness';
  signingOrder: number;          // 0 = parallel
  authMethod: AuthMethod;
  status: 'pending' | 'viewed' | 'signed' | 'declined';
  signedDocumentHash?: string;
  auditTrail: AuditEvent[];
}

type AuthMethod =
  | 'email_link'         // Simple email verification
  | 'sms_otp'            // SMS one-time password
  | 'aadhaar_otp'        // Aadhaar-based OTP (India)
  | 'knowledge_based'    // Security questions
  | 'digital_certificate' // PKI certificate
  | 'biometric'          // Fingerprint, face ID
```

### Document Integrity & Audit Trail

**Critical for legal enforceability:**

```typescript
interface DocumentAuditTrail {
  documentId: string;
  events: AuditEvent[];
  finalHash: string;           // SHA-256 of signed document
  certificateChain?: string;   // PKI certificate chain
  timestampAuthority?: string; // TSA proof of signing time
}

interface AuditEvent {
  eventType: 'created' | 'viewed' | 'signed' | 'declined' | 'voided';
  timestamp: Date;
  actor: string;
  ipAddress: string;
  userAgent?: string;
  geolocation?: GeoLocation;
}
```

### Storage & Archival

**Questions:**
- How long must signed contracts be retained?
- What format ensures long-term readability (PDF/A)?
- Where should documents be stored (cloud, on-premise, distributed)?

**Research needed:**
- Retention periods by jurisdiction and contract type
- PDF/A compliance requirements
- Disaster recovery for legal documents
- Right-to-erasure (GDPR) vs. retention obligations conflict resolution

---

## Open Problems

1. **Aadhaar eSign for non-resident customers** — NRIs and foreign customers don't have Aadhaar. Need alternative paths that are equally frictionless.

2. **Offline signing** — Travel agents may need to get signatures in areas with poor connectivity. Queue-and-sync patterns needed.

3. **Multi-document signing ceremonies** — A single booking may require signing a terms sheet, insurance waiver, visa authorization, and privacy notice together. Bundle signing UX is unexplored.

4. **Signature tampering detection** — If a signed PDF is modified post-signing, how is this detected and flagged? What's the remediation workflow?

5. **Cost optimization** — E-signature platforms charge per envelope or per user. For a travel agency processing thousands of bookings monthly, costs can escalate. Need to identify which contracts truly need platform e-signatures vs. simple acknowledgment.

6. **Regulatory divergence** — Simultaneously satisfying IT Act, eIDAS, and ESIGN requirements for a single international contract is complex. May need jurisdiction-aware signing flows.

---

## Next Steps

- [ ] Compare DocuSign vs. Adobe Sign vs. HelloSign API capabilities
- [ ] Research Aadhaar eSign API integration requirements
- [ ] Map jurisdiction requirements for top 10 customer/supplier markets
- [ ] Prototype signing cost model based on projected booking volumes
- [ ] Investigate PDF/A and long-term archival best practices
- [ ] Design multi-document signing ceremony UX
