# Reviews & Ratings 02: Verification

> Ensuring review authenticity and preventing fraud

---

## Document Overview

**Focus:** Review verification systems
**Status:** Research Exploration
**Last Updated:** 2026-04-27

---

## Key Questions

### Verification Methods
- How do we verify reviews?
- What constitutes proof of travel?
- How do we handle different booking types?
- What about third-party bookings?

### Fraud Prevention
- What are common fraud patterns?
- How do we detect fake reviews?
- What are the penalties?
- How do we handle disputes?

### Verified Status
- What does "verified" mean?
- How do we display it?
- What value does it add?
- How do we maintain it?

---

## Research Areas

### A. Verification Methods

**Proof Requirements:**

| Method | Proof | Research Needed |
|--------|-------|-----------------|
| **Booking ID** | Valid booking number | ? |
| **Travel dates** | Past travel only | ? |
| **Email confirmation** | Forwarded confirmation | ? |
| **Photo evidence** | Optional, for claims | ? |

**Verification by Source:**

| Source | Verification | Research Needed |
|--------|-------------|-----------------|
| **Direct booking** | Automatic | ? |
| **Partner booking** | Via partner | ? |
| **External booking** | Manual verification | ? |

### B. Fraud Detection

**Red Flags:**

| Flag | Description | Research Needed |
|------|-------------|-----------------|
| **Multiple reviews, same IP** | Suspicious pattern | ? |
| **Extreme ratings only** | Always 1 or 5 stars | ? |
| **Generic content** | Template-like | ? |
| **Competitor attacks** | Negative reviews of competitors | ? |
| **Self-promotion** | Positive reviews of own business | ? |

**Detection Methods:**

| Method | Description | Research Needed |
|--------|-------------|-----------------|
| **IP analysis** | Detect patterns | ? |
| **Content analysis** | Natural language | ? |
| **Timing patterns** | Burst of reviews | ? |
| **Cross-reference** | With bookings | ? |

### C. Verified Badge

**Badge Criteria:**

| Criteria | Requirement | Research Needed |
|----------|-------------|-----------------|
| **Confirmed booking** | Verified through system | ? |
| **Actual travel** | Trip completed | ? |
| **Genuine customer** | Verified identity | ? |

**Display:**

| Location | Display | Research Needed |
|----------|---------|-----------------|
| **Next to rating** | Badge icon | ? |
| **Review list** | Filter option | ? |
| **Provider page** | % verified | ? |

---

## Data Model Sketch

```typescript
interface ReviewVerification {
  reviewId: string;
  verified: boolean;
  method: VerificationMethod;

  // Evidence
  bookingVerified: boolean;
  travelVerified: boolean;
  identityVerified: boolean;

  // Fraud check
  fraudScore: number; // 0-100
  flags: FraudFlag[];

  // Verification details
  verifiedAt: Date;
  verifiedBy: 'system' | 'manual';
}

type VerificationMethod =
  | 'automatic_booking'
  | 'manual_document'
  | 'partner_api';

type FraudFlag =
  | 'multiple_same_ip'
  | 'extreme_only'
  | 'generic_content'
  | 'suspicious_timing'
  | 'competitor_pattern';
```

---

## Open Problems

### 1. Privacy vs. Verification
**Challenge:** Need data but must protect privacy

**Options:** Minimal data, anonymization, consent

### 2. False Positives
**Challenge:** Legitimate reviews flagged

**Options:** Appeals, manual review, transparency

### 3. International Bookings
**Challenge:** Verifying external bookings

**Options:** Partner integrations, manual checks

### 4. Gaming the System
**Challenge:** People trying to bypass verification

**Options:** Continuous monitoring, penalties

---

## Next Steps

1. Define verification criteria
2. Build fraud detection
3. Create badge system
4. Implement appeals process

---

**Status:** Research Phase — Verification patterns unknown

**Last Updated:** 2026-04-27
