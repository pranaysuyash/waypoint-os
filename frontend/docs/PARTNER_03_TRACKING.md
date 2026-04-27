# Partner & Affiliate Management 03: Tracking

> Referral tracking, attribution, and conversion measurement

---

## Document Overview

**Focus:** Partner referral tracking
**Status:** Research Exploration
**Last Updated:** 2026-04-27

---

## Key Questions

### Attribution Methods
- How do we track referrals?
- What attribution model do we use?
- How do we handle multiple touchpoints?
- What is the attribution window?

### Tracking Technology
- How do we implement tracking?
- What about cross-device tracking?
- How do we handle privacy?
- What about ad blockers?

### Fraud Prevention
- How do we detect fraud?
- What are common fraud patterns?
- How do we prevent self-referrals?
- What about cookie stuffing?

### Reporting & Visibility
- What data do partners see?
- How real-time is tracking?
- What about pending conversions?
- How do we handle discrepancies?

---

## Research Areas

### A. Attribution Models

**Last-Click Attribution:**

| Characteristic | Description | Research Needed |
|---------------|-------------|-----------------|
| **Rule** | Last partner gets credit | ? |
| **Pros** | Simple, clear | ? |
| **Cons** | Undervalues awareness | ? |
| **Best for** | Standard affiliate | ? |

**First-Click Attribution:**

| Characteristic | Description | Research Needed |
|---------------|-------------|-----------------|
| **Rule** | First partner gets credit | ? |
| **Pros** | Values discovery | ? |
| **Cons** | May credit stale click | ? |
| **Best for** | Awareness partners | ? |

**Multi-Touch Attribution:**

| Characteristic | Description | Research Needed |
|---------------|-------------|-----------------|
| **Rule** | Split credit across partners | ? |
| **Pros** | Fair, complex | ? |
| **Cons** | Expensive to implement | ? |
| **Best for** | Strategic partners | ? |

**Time-Based Attribution:**

| Characteristic | Description | Research Needed |
|---------------|-------------|-----------------|
| **Rule** | Most recent within window | ? |
| **Pros** | Balances recency and value | ? |
| **Cons** | More complex | ? |
| **Best for** | Mixed channels | ? |

### B. Tracking Implementation

**Tracking Methods:**

| Method | How It Works | Research Needed |
|--------|--------------|-----------------|
| **Tracking link** | URL with partner ID | ? |
| **Tracking pixel** | Image pixel on page | ? |
| **Postback URL** | Server-to-server | ? |
| **Cookie** | Browser storage | ? |
| **Fingerprinting** | Device ID | ? |

**Cookie Tracking:**

| Aspect | Consideration | Research Needed |
|--------|---------------|-----------------|
| **Duration** | 30-90 days typical | ? |
| **First vs. last** | Which cookie wins | ? |
| **Cross-domain** | Third-party cookie issues | ? |
| **Privacy** | Consent requirements | ? |

**Cross-Device Tracking:**

| Challenge | Solution | Research Needed |
|-----------|----------|-----------------|
| **Mobile to desktop** | User login | ? |
| **Desktop to app** | Device linking | ? |
| **Multiple devices** | Probabilistic matching | ? |
| **Privacy** | Limited tracking | ? |

### C. Attribution Windows

**Window by Product:**

| Product | Window | Rationale | Research Needed |
|---------|--------|-----------|-----------------|
| **Flights** | 30 days | Short consideration | ? |
| **Hotels** | 30 days | Short consideration | ? |
| **Packages** | 60 days | Longer consideration | ? |
| **Insurance** | 90 days | Long consideration | ? |

**Window Logic:**

| Scenario | Attribution | Research Needed |
|----------|-------------|-----------------|
| **Click and book same day** | Credit | ? |
| **Click, return direct, book** | Depends on cookie | ? |
| **Multiple partners, different days** | Last or split | ? |
| **Click after window expires** | No credit | ? |

### D. Fraud Detection

**Fraud Patterns:**

| Pattern | Detection | Research Needed |
|---------|-----------|-----------------|
| **Self-referral** | Partner books own travel | ? |
| **Cookie stuffing** | Forced cookies | ? |
| **Fake bookings** | High cancellation | ? |
| **Bot traffic** | Unusual patterns | ? |
| **Incentivized clicks** | Low conversion | ? |

**Detection Methods:**

| Method | Description | Research Needed |
|--------|-------------|-----------------|
| **IP analysis** | Detect same IP | ? |
| **Conversion rate** | Unusually low/high | ? |
| **Pattern analysis** | Repeated behavior | ? |
| **Manual review** | Flagged accounts | ? |

**Penalties:**

| Violation | Penalty | Research Needed |
|-----------|----------|-----------------|
| **Minor** | Warning | ? |
| **Moderate** | Reversal + warning | ? |
| **Severe** | Termination | ? |
| **Fraudulent** | Termination + legal | ? |

### E. Partner Visibility

**Dashboard Metrics:**

| Metric | Description | Research Needed |
|--------|-------------|-----------------|
| **Clicks** | Total clicks | ? |
| **Conversions** | Total bookings | ? |
| **Conversion rate** | % conversion | ? |
| **Revenue** | Total booking value | ? |
| **Commission** | Earned commission | ? |
| **Pending** | Not yet payable | ? |

**Real-Time vs. Batch:**

| Data Type | Update Frequency | Research Needed |
|-----------|------------------|-----------------|
| **Clicks** | Real-time | ? |
| **Conversions** | Near real-time | ? |
| **Commission** | After booking | ? |
| **Payments** | Per payout | ? |

**Conversion Details:**

| Field | Shown | Research Needed |
|-------|-------|-----------------|
| **Booking ID** | Yes | ? |
| **Customer** | Masked | ? |
| **Amount** | Yes | ? |
| **Commission** | Yes | ? |
| **Status** | Yes | ? |
| **Date** | Yes | ? |

---

## Data Model Sketch

```typescript
interface ReferralTracking {
  trackingId: string;
  partnerId: string;

  // Source
  source: ReferralSource;
  trackingCode: string;

  // Click data
  clickId: string;
  clickedAt: Date;
  clickUrl: string;

  // User (anonymized)
  sessionId?: string;
  deviceId?: string;
  fingerprint?: string;

  // Conversion
  converted: boolean;
  conversionId?: string;
  convertedAt?: Date;
  bookingValue?: number;
  commission?: number;

  // Attribution
  attributedTo: string; // partnerId
  attributionModel: AttributionModel;
  attributionScore?: number; // For multi-touch

  // Fraud
  fraudFlags: FraudFlag[];
  fraudScore: number; // 0-100
}

interface ReferralSource {
  type: ReferralType;
  url?: string;
  campaign?: string;
  creative?: string;

  // Context
  userAgent?: string;
  ip?: string;
  referrer?: string;
}

type ReferralType =
  | 'tracking_link'
  | 'widget'
  | 'api'
  | 'qr_code'
  | 'social';

interface ConversionAttribution {
  conversionId: string;
  bookingId: string;

  // All touchpoints
  touchpoints: ReferralTracking[];

  // Attribution
  model: AttributionModel;
  attributedPartners: AttributedPartner[];

  // Value
  totalValue: number;
  totalCommission: number;

  // Timing
  convertedAt: Date;
}

interface AttributedPartner {
  partnerId: string;
  commissionShare: number; // % of total commission
  commissionAmount: number;
  reason: string; // Why this share
}

type AttributionModel =
  | 'last_click'
  | 'first_click'
  | 'linear' // Equal split
  | 'time_decay' // More recent = more
  | 'position_based' // First + last get more
  | 'custom';

interface FraudDetection {
  detectionId: string;
  partnerId: string;

  // Analysis
  period: DateRange;
  totalClicks: number;
  totalConversions: number;
  conversionRate: number;

  // Flags
  flags: FraudFlag[];
  score: number; // 0-100

  // Status
  status: FraudStatus;
  reviewedAt?: Date;
  reviewedBy?: string;
  action?: FraudAction;
}

type FraudFlag =
  | 'high_click_low_conversion'
  | 'same_ip_pattern'
  | 'suspicious_timing'
  | 'self_referral'
  | 'bot_pattern'
  | 'cookie_stuffing';

type FraudStatus =
  | 'clean'
  | 'suspicious'
  | 'confirmed_fraud';

type FraudAction =
  | 'none'
  | 'warning'
  | 'reverse_commission'
  | 'suspend'
  | 'terminate';
```

---

## Open Problems

### 1. Cross-Device
**Challenge:** Users switch devices

**Options:** Login-based tracking, probabilistic matching, accept lower accuracy

### 2. Privacy Regulations
**Challenge:** GDPR, consent requirements

**Options:** Consent management, minimal tracking, server-side

### 3. Ad Blockers
**Challenge:** Tracking blocked

**Options:** Server-to-server, direct links, alternative methods

### 4. Attribution Disputes
**Challenge:** Partners claim missing credit

**Options:** Clear policies, transparency, audit logs

### 5. Mobile Apps
**Challenge:** Deep linking complexity

**Options:** Universal links, app tracking, deferred deep linking

---

## Next Steps

1. Define attribution model
2. Build tracking infrastructure
3. Implement fraud detection
4. Create partner dashboard

---

**Status:** Research Phase — Tracking patterns unknown

**Last Updated:** 2026-04-27
