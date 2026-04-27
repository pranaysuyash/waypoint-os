# Airport Services 03: Access & Delivery

> Confirmations, passes, and accessing airport services

---

## Document Overview

**Focus:** How customers access booked airport services
**Status:** Research Exploration
**Last Updated:** 2026-04-27

---

## Key Questions to Answer

### 1. Confirmation Formats
- How are confirmations delivered? (QR, barcode, name-on-list?)
- What information must be included?
- How do customers access confirmations offline?
- What about wallet passes?

### 2. Access Methods
- How do customers enter lounges?
- How do fast track lanes work?
- How does meet & greet connection happen?
- What if access is denied?

### 3. Timing & Validity
- When are services valid? (Time windows?)
- What about early/late arrivals?
- How long is lounge access valid for?
- What happens if flight is delayed?

### 4. Support Issues
- What if customer can't access service?
- What if QR code doesn't work?
- What if lounge is full?
- How do we handle disputes?

---

## Research Areas

### A. Confirmation Delivery

**Delivery Methods:**

| Method | Used For | How It Works |
|--------|----------|--------------|
| **QR code** | Most services | Scan at entrance |
| **Barcode** | Some services | Scan at entrance |
| **Name on list** | Some lounges | Check against list |
| **Physical pass** | Rare | Collected or mailed |

**Delivery Channels:**

| Channel | Timing | Offline Access |
|----------|--------|----------------|
| **App** | Instant | Yes |
| **Email** | Immediate | Yes (saved) |
| **SMS** | Immediate | No |
| **Wallet pass** | Instant | Yes |

**Research:**
- Which methods are most reliable?
- How do we support offline access?
| What about wallet passes (Apple/Google Wallet)?

### B. Access by Service Type

**Lounge Access:**

| Step | Process |
|------|----------|
| 1. **Locate lounge** | Terminal, floor, signage |
| 2. **Present confirmation** | QR, barcode, or name |
| 3. **Verify eligibility** | Staff checks |
| 4. **Enter lounge** | Granted access |

**Fast Track Access:**

| Step | Process |
|------|----------|
| 1. **Locate lane** | Signage for fast track |
| 2. **Present confirmation** | QR, barcode, or name |
| 3. **Verify** | Staff or automated |
| 4. **Proceed** | Skip line |

**Meet & Greet:**

| Step | Process |
|------|----------|
| 1. **Agent location** | Meeting point specified |
| 2. **Identification** | Sign with customer name |
| 3. **Verification** | Match booking details |
| 4. **Service begins** | Assistance provided |

### C. Validity & Timing

**Lounge Access Validity:**

| Rule | Typical | Research Needed |
|------|---------|-----------------|
| **Duration** | 2-4 hours | ? |
| **Same-day re-entry** | Sometimes | ? |
| **Flight delay** | Usually accommodated | ? |
| **Early arrival** | Depends on availability | ? |

**Fast Track Validity:**

| Rule | Typical |
|------|---------|
| **Time window** | Usually flight time ± few hours |
| **Flight delay** | Usually still valid |
| **Missed flight** | Depends on policy |

**Research:**
- What are the exact validity rules?
- How do we handle flight changes?
- What if customer arrives very early/late?

### D. Access Problems

| Problem | Cause | Resolution |
|---------|-------|------------|
| **QR won't scan** | Screen brightness, damage | Manual check, name verification |
| **Not on list** | Booking not synced | Contact provider, manual verification |
| **Wrong terminal** | Flight changed | Rebook, or deny access |
| **Lounge full** | Capacity reached | Wait list, alternative, compensation? |
| **Name mismatch** | Booking name vs. ID | Manual verification |

---

## Confirmation Data Model

```typescript
interface AirportServiceConfirmation {
  bookingId: string;

  // Service details
  service: AirportService;
  provider: string;
  airport: string;
  terminal?: string;

  // Validity
  validFrom: DateTime;
  validUntil: DateTime;
  flightDetails?: FlightInfo;

  // Access
  accessMethod: AccessMethod;
  accessCode?: string;  // QR, barcode, reference
  nameOnList?: boolean;

  // Delivery
  delivery: {
    method: DeliveryMethod[];
    sentAt: Date;
    url?: string;
    pass?: WalletPass;
  };

  // Instructions
  instructions: {
    howToFind: string;
    howToAccess: string;
    whatToBring: string[];
    whatNotToBring: string[];
  };

  // Support
  emergencyContact: {
    phone: string;
    email: string;
  };
}

interface WalletPass {
  type: 'apple_wallet' | 'google_wallet';
  url: string;
  expiresAt: Date;
}
```

---

## Access Experience

**Pre-Arrival:**

| Timing | Communication |
|--------|----------------|
| **At booking** | Confirmation with instructions |
| **24 hours before** | Reminder with location details |
| **Day of travel** | Last-minute reminder (optional) |

**On Arrival:**

| Step | Guidance Needed |
|------|-----------------|
| **Finding service** | Terminal, floor, landmarks |
| **Accessing service** | Scan here, show to staff |
| **Using service** | What's included, duration |

---

## Open Problems

### 1. Offline Access
**Challenge:** Customer has no data at airport

**Options:**
- Wallet pass
- Screenshot
- Print-at-home
- SMS with backup code

**Research:** What works best?

### 2. Flight Disruptions
**Challenge:** Flight delayed, missed, or cancelled

**Options:**
- Automatic rebooking
- Credit for future
- Case-by-case handling

**Research:** How do providers handle this?

### 3. Group Bookings
**Challenge:** 5 people booked, only 4 show up

**Options:**
- All or nothing
- Partial refund for no-show
| Pay for who shows

### 4. Staff Training
**Challenge:** Lounge staff doesn't recognize our confirmation

**Options:**
- Provider education
| Backup verification process
| Customer support hotline

---

## Competitor Research Needed

| Competitor | Access UX | Notable Patterns |
|------------|-----------|------------------|
| **Priority Pass** | ? | ? |
| **Airline apps** | ? | ? |

---

## Experiments to Run

1. **Access success rate test:** What % access without issues?
2. **QR code readability test:** Which formats work best?
3. **Offline access test:** How do customers access without data?
4. **Disruption handling test:** How are delays handled?

---

## References

- [Activities - Booking](./ACTIVITIES_03_BOOKING.md) — Voucher patterns
| [Ground Transportation - Booking](./GROUND_TRANSPORTATION_03_BOOKING.md) — Confirmation patterns

---

## Next Steps

1. Design confirmation format
2. Build QR/barcode generation
3. Create wallet passes
4. Write access instructions
5. Test access flow

---

**Status:** Research Phase — Access patterns unknown

**Last Updated:** 2026-04-27
