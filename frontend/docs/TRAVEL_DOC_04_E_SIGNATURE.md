# Travel Document Lifecycle — E-Signatures & Digital Verification

> Research document for e-signature integration, India-specific digital signing (Aadhaar eSign), contract workflows, and document verification.

---

## Key Questions

1. **How do we integrate e-signatures for travel contracts and agreements?**
2. **What India-specific signing methods are legally valid?**
3. **How do we verify document authenticity and detect tampering?**
4. **What contract signing workflows are needed?**

---

## Research Areas

### E-Signature Integration

```typescript
interface ESignatureRequest {
  id: string;
  document_id: string;
  type: SignatureType;
  status: SignatureStatus;

  // Signers
  signers: Signer[];
  signing_order: "SEQUENTIAL" | "PARALLEL" | "ANY";

  // Document
  document_url: string;
  signature_positions: SignaturePosition[];

  // Workflow
  expires_at: string;
  reminders: ReminderSchedule;
  completion_callback: string;
}

type SignatureType =
  | "ELECTRONIC"        // click-to-sign
  | "DIGITAL"           // certificate-based
  | "AADHAAR_ESIGN"     // India: Aadhaar-based
  | "DSC"               // India: Digital Signature Certificate
  | "BIO_METRIC";       // fingerprint/face

type SignatureStatus =
  | "DRAFT" | "SENT" | "VIEWED" | "SIGNED" | "DECLINED"
  | "EXPIRED" | "CANCELLED";

interface Signer {
  name: string;
  email: string;
  phone: string;
  role: "CUSTOMER" | "AGENT" | "AGENCY_OWNER" | "VENDOR";
  signing_method: SignatureType;
  status: "PENDING" | "NOTIFIED" | "VIEWED" | "SIGNED" | "DECLINED";
  signed_at: string | null;
  ip_address: string | null;
  geolocation: GeoLocation | null;
}

// ── India-specific signing methods ──
// ┌─────────────────────────────────────────────────────┐
// │  Method          | Legal Validity | Use Case         │
// │  ─────────────────────────────────────────────────── │
// │  Aadhaar eSign   | IT Act §35     | Customer contracts│
// │  (UIDAI OTP)     |                |                   │
// │  DSC Class 3     | IT Act §35     | Agency filings   │
// │  (USB token)     | Highest trust  | GST, tax returns │
// │  Electronic      | IT Act §10     | Internal docs    │
// │  (click-to-sign) |                | Vouchers         │
// │  Biometric       | Emerging       | Future use       │
// │  (fingerprint)   |                |                   │
// └─────────────────────────────────────────────────────┘
```

### Contract Signing Workflow

```typescript
// ── Travel booking contract workflow ──
// ┌─────────────────────────────────────────────────────┐
// │  1. Agent prepares booking contract                    │
// │     → Auto-populated with trip details                │
// │     → Includes terms, cancellation policy, pricing    │
// │                                                       │
// │  2. Contract sent to customer (WhatsApp + email)      │
// │     → Customer reviews on phone/web                  │
// │     → Customer signs via Aadhaar eSign (OTP)         │
// │                                                       │
// │  3. Counter-signature by agency                       │
// │     → Agency owner signs with DSC                    │
// │     → Contract becomes legally binding               │
// │                                                       │
// │  4. Executed contract delivered                       │
// │     → PDF with both signatures sent to customer      │
// │     → Stored in document library                     │
// │     → Booking status → CONFIRMED                    │
// │                                                       │
// │  ── Timeline:                                         │
// │  Day 0: Contract sent                                │
// │  Day 1: Reminder if not signed                       │
// │  Day 3: Urgent reminder                              │
// │  Day 7: Contract expires if not signed               │
// └─────────────────────────────────────────────────────┘

interface ContractTemplate {
  id: string;
  name: string;
  type: "BOOKING_AGREEMENT" | "VENDOR_CONTRACT" | "EMPLOYMENT" | "NDA" | "PARTNERSHIP";
  clauses: ContractClause[];
  signature_fields: SignaturePosition[];
  applicable_law: string;              // "Indian Contract Act, 1872"
  jurisdiction: string;                // "Mumbai, India"
}

interface ContractClause {
  id: string;
  title: string;
  content: string;
  mandatory: boolean;
  variables: string[];                 // {{customer_name}}, {{trip_value}}
}
```

### Document Verification & QR Codes

```typescript
interface DocumentVerification {
  document_id: string;
  verification_method: "QR_CODE" | "HASH" | "DIGITAL_SIGNATURE" | "WATERMARK";
  verification_data: string;           // URL or hash
  is_valid: boolean;
  last_verified_at: string;
}

// ── QR code verification ──
// ┌─────────────────────────────────────────────────────┐
// │  Every generated document includes a QR code:        │
// │                                                       │
// │  [QR] → https://verify.waypointos.com/doc/abc123     │
// │                                                       │
// │  Scanning shows:                                      │
// │  ✅ Document verified                                 │
// │  Type: Hotel Voucher                                  │
// │  Issued by: [Agency Name]                             │
// │  Issued on: 29-Apr-2026                              │
// │  Trip: Singapore 5N/6D                               │
// │  Status: Valid                                        │
// │                                                       │
// │  Vendor can scan at check-in to verify authenticity  │
// └─────────────────────────────────────────────────────┘

// Tamper detection:
// - Content hash embedded in QR code
// - Any PDF modification changes the hash
// - Scanning modified PDF shows "⚠️ Document modified"
```

---

## Open Problems

1. **Aadhaar eSign adoption** — Not all customers have Aadhaar linked to phones. Need fallback to electronic signature for customers without Aadhaar access.

2. **DSC token requirement** — Agency owners need USB-based DSC tokens for Class 3 signing, which is hardware-dependent and not always convenient.

3. **Legal validity across borders** — Indian e-signatures may not be recognized in all countries for travel contracts involving international vendors.

4. **Mobile signing UX** — Signing a multi-page contract on a phone is awkward. Need mobile-optimized review and signing interfaces.

---

## Next Steps

- [ ] Integrate e-signature provider (Aadhaar eSign + DocuSign for international)
- [ ] Build contract template engine with variable substitution
- [ ] Implement QR code document verification
- [ ] Design counter-signature workflow for agency owners
- [ ] Study Indian IT Act 2000 compliance requirements for e-signatures
