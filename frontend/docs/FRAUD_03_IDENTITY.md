# Travel Fraud Detection & Prevention — Identity Verification

> Research document for identity verification, document fraud detection, KYC automation, and customer authentication.

---

## Key Questions

1. **How do we verify customer identity during booking?**
2. **What document fraud detection capabilities are needed?**
3. **How do we automate KYC for travel bookings?**
4. **What's the authentication model for returning customers?**
5. **How do we balance security with booking experience?**

---

## Research Areas

### Customer Identity Verification

```typescript
interface IdentityVerification {
  bookingId: string;
  level: VerificationLevel;
  methods: VerificationMethod[];
  result: VerificationResult;
}

type VerificationLevel =
  | 'basic'                           // Name + phone + email
  | 'standard'                        // + OTP verification + ID proof
  | 'enhanced'                        // + Document upload + selfie match
  | 'premium';                        // + Video KYC + address proof

// Verification level triggers:
// Basic (< ₹25,000 domestic):
//   - Name, phone, email
//   - OTP verification on phone
//   - No document upload required
//
// Standard (₹25,000-1,00,000 or international):
//   - Basic + government ID proof (Aadhaar, PAN, passport)
//   - ID number verified against issuing authority database
//   - OTP on registered mobile
//
// Enhanced (> ₹1,00,000 or high-risk):
//   - Standard + document photo upload
//   - Selfie photo match against ID photo
//   - Address verification
//
// Premium (> ₹5,00,000 or flagged):
//   - Enhanced + video KYC call
//   - Live agent verifies identity on video
//   - Full document upload (ID + address + income proof)

interface VerificationMethod {
  method: string;
  provider: string;
  result: 'pass' | 'fail' | 'inconclusive';
  confidence: number;
  timestamp: Date;
  data?: VerificationData;
}

// Identity verification providers (India):
// 1. Aadhaar eKYC (UIDAI):
//    - OTP-based: Aadhaar number + OTP → Instant verification
//    - Biometric: Fingerprint/iris at Aadhaar center
//    - Offline: Aadhaar XML download + biometric unlock
//    - Coverage: 95%+ of Indian adults have Aadhaar
//    - Cost: ₹0.50-1.50 per verification
//    - Privacy: Must comply with Aadhaar Act (consent required)
//
// 2. DigiLocker:
//    - Government document storage platform
//    - Access to: PAN, Aadhaar, driving license, vehicle registration
//    - API integration: Pull verified documents with consent
//    - Free to use (government platform)
//
// 3. PAN Verification (NSDL/UTIITSL):
//    - Verify PAN against Income Tax database
//    - Name + PAN number match
//    - Essential for TCS collection (₹7L threshold tracking)
//    - Cost: ₹1-2 per verification
//
// 4. Passport Verification:
//    - Verify passport number against MEA database
//    - Required for international travel bookings
//    - Check validity, expiry date
//    - Cost: Limited public API, manual verification common

// Verification flow for high-value international booking:
// 1. Customer starts booking (₹3,50,000 Europe tour)
// 2. System detects: High value + international → Enhanced verification
// 3. Step 1: Aadhaar OTP verification
//    → Customer enters Aadhaar number → Receives OTP → Verified ✅
// 4. Step 2: PAN verification (for TCS tracking)
//    → Customer enters PAN → Verified against NSDL ✅
// 5. Step 3: Selfie + ID photo match
//    → Customer uploads Aadhaar/PAN card photo + selfie
//    → AI face matching: Confidence 94% ✅
// 6. Step 4: Address proof (optional, for delivery)
//    → Customer uploads utility bill or bank statement
// 7. Verification complete → Booking proceeds
// 8. All verification data stored securely (encrypted)
//
// Total verification time: 2-3 minutes
// Cost per verification: ₹5-15 (Aadhaar + PAN + face match)
```

### Document Fraud Detection

```typescript
interface DocumentFraudDetection {
  documentId: string;
  documentType: DocumentType;
  checks: DocumentCheck[];
  score: FraudDetectionScore;
}

type DocumentType =
  | 'aadhaar_card'
  | 'pan_card'
  | 'passport'
  | 'driving_license'
  | 'voter_id'
  | 'bank_statement'
  | 'utility_bill';

interface DocumentCheck {
  check: string;
  result: 'pass' | 'fail' | 'warning';
  confidence: number;
  details: string;
}

// Document fraud checks:
//
// AADHAAR CARD:
// 1. Format validation: 12-digit number, proper checksum
// 2. QR code verification: Scan QR code → match data
// 3. Photo quality: Check if photo is printed (physical) vs. digital
// 4. Hologram detection: Security hologram presence
// 5. Database verification: Match name + DOB against UIDAI
// 6. Masked Aadhaar: Accept masked version (only last 4 digits visible)
//
// PAN CARD:
// 1. Format validation: 10-character (5 letters + 4 digits + 1 letter)
// 2. Name match: Verify name matches PAN database
// 3. Card type: Individual (P), Company (C), HUF (H), etc.
// 4. Database verification: NSDL/UTIITSL API
// 5. Photo match: Compare card photo to selfie (if uploaded)
//
// PASSPORT:
// 1. MRZ (Machine Readable Zone) parsing and validation
// 2. Passport number format check (India: 1 letter + 7 digits)
// 3. Expiry date check (must be 6+ months from travel date)
// 4. Photo page integrity: Check for tampering signs
// 5. Font consistency: Government-printed fonts are uniform
// 6. Watermark detection: Security watermark presence
//
// Common document fraud types:
// - Altered numbers: Changed DOB or expiry date on scanned copy
// - Photo substitution: Different person's photo pasted
// - Completely fake: Fabricated document (usually poor quality)
// - Stolen identity: Genuine document of another person
// - Screen capture: Photo of screen instead of original (lower quality)
//
// Detection accuracy targets:
// Completely fake: >99% detection (usually obvious)
// Altered document: >90% detection (requires pixel-level analysis)
// Stolen identity: >70% detection (harder without biometric match)
// Screen capture: >95% detection (moiré pattern detection)

interface FraudDetectionScore {
  overall: number;                    // 0-100 (higher = more likely fraud)
  recommendation: 'accept' | 'review' | 'reject';
  flags: string[];
}
```

### Customer Authentication

```typescript
interface CustomerAuthentication {
  customerId: string;
  methods: AuthMethod[];
  session: SessionConfig;
  mfa: MFAConfig;
}

type AuthMethod =
  | 'phone_otp'                       // OTP to registered mobile
  | 'email_link'                      // Magic link to email
  | 'whatsapp_otp'                    // OTP via WhatsApp
  | 'password'                        // Password-based (not recommended for customers)
  | 'biometric';                      // Phone fingerprint/face ID

// Authentication strategy for customers:
//
// First-time customer:
// 1. Phone number + OTP (primary authentication)
// 2. Email verification (secondary)
// 3. No password required (OTP is sufficient)
//
// Returning customer:
// 1. Phone number + OTP (standard)
// 2. Or: Biometric (if enabled on device)
// 3. Or: WhatsApp OTP (faster, no SMS cost)
//
// High-risk actions (require re-authentication):
// - Making payment > ₹50,000
// - Canceling a booking
// - Changing traveler details
// - Requesting refund
// - Updating phone number or email
//
// Session management:
// - Session duration: 7 days (remember me) or 30 minutes (no activity)
// - Concurrent sessions: Max 2 devices
// - Session invalidation: On password change, phone number change
// - Suspicious activity: Invalidate all sessions, require re-auth
```

---

## Open Problems

1. **Verification friction** — Each verification step adds 30-60 seconds. Too much friction causes booking abandonment. Need to minimize steps while maintaining security.

2. **Aadhaar privacy** — Supreme Court restricted mandatory Aadhaar usage. Can't force Aadhaar for private services. Must offer alternatives (PAN, passport).

3. **International customer identity** — Foreign customers don't have Aadhaar/PAN. Different verification flow needed per nationality. Passport verification APIs vary by country.

4. **Family bookings** — One person books for 5 family members. Only booker's identity is verified. How to verify all travelers without excessive friction?

5. **Document quality** — Mobile photos of documents are often blurry, poorly lit, or partially cut off. OCR and fraud detection accuracy drops with poor image quality.

---

## Next Steps

- [ ] Build identity verification flow with Aadhaar/PAN/passport integration
- [ ] Create document fraud detection with AI-based image analysis
- [ ] Design tiered authentication model (basic/standard/enhanced)
- [ ] Build document quality scoring with re-upload prompts
- [ ] Study identity verification platforms (DigiLocker, Aadhaar eKYC, Onfido, Jumio)
