# Travel Fraud Detection & Prevention — Payment Fraud Prevention

> Research document for payment fraud prevention, chargeback management, PCI compliance, and secure payment flows.

---

## Key Questions

1. **How do we prevent payment fraud in travel bookings?**
2. **What's the chargeback management process?**
3. **How do we comply with PCI-DSS requirements?**
4. **What payment security measures are needed?**
5. **How do we handle disputed payments?**

---

## Research Areas

### Payment Fraud Prevention

```typescript
interface PaymentFraudPrevention {
  prePayment: PrePaymentChecks;
  duringPayment: DuringPaymentChecks;
  postPayment: PostPaymentChecks;
  chargebacks: ChargebackManagement;
}

interface PrePaymentChecks {
  cardChecks: CardValidation[];
  customerChecks: CustomerValidation[];
  velocityChecks: VelocityCheck[];
}

// Pre-payment fraud checks:
//
// Card validation:
// - BIN (Bank Identification Number) check: First 6 digits identify bank, card type, country
// - AVS (Address Verification System): Match billing address to card address
// - Card velocity: How many times this card has been used in last 24 hours
// - Card blacklist: Known fraudulent cards (internal + third-party databases)
// - Card age: Recently issued cards have higher fraud risk
//
// Customer validation:
// - Email age: Newly created email addresses have higher fraud risk
// - Phone verification: OTP to registered mobile number
// - Device fingerprint: Has this device been used for fraud before?
// - IP geolocation: Does IP match billing address country?
// - Account age: How long since customer created account?
//
// Velocity checks (rate limiting):
// - Max 3 booking attempts per hour per customer
// - Max 5 payment attempts per hour per card
// - Max 2 different cards per booking
// - Max ₹10L total bookings per day per new customer
// - Flag if customer has 3+ failed payment attempts

interface DuringPaymentChecks {
  threeDS: ThreeDSConfig;
  otp: OTPConfig;
  riskEngine: PaymentRiskEngine;
}

// 3D Secure 2.0 (mandatory in India per RBI):
// - All online card transactions require 3DS authentication
// - Customer receives OTP from issuing bank
// - Risk-based authentication: Low-risk transactions may be frictionless
// - Challenge flow: High-risk transactions require OTP + PIN
//
// UPI fraud prevention:
// - UPI has built-in 2FA (UPI PIN)
// - Risk: SIM swap attacks (fraudster ports victim's SIM)
// - Mitigation: Verify device binding, monitor for SIM change
// - UPI Mandate fraud: Verify mandate amount and frequency
//
// International payment risk:
// - Higher fraud risk for international cards
// - Additional checks: AVS, CVV mandatory, billing address verification
// - Currency mismatch: Card currency different from booking currency → Flag
// - Country risk: Certain countries have higher fraud rates

// Payment risk engine:
// ┌──────────────────────────────────────────┐
// │  Payment Risk Assessment                  │
// │                                          │
// │  Booking: ₹2,50,000 (International)     │
// │  Customer: New (no history)              │
// │  Card: International (USA)               │
// │  IP Location: Nigeria                    │
// │                                          │
// │  Risk Score: 78/100 (HIGH)               │
// │                                          │
// │  Factors:                                │
// │  +25: International card, domestic IP    │
// │  +20: High-value first booking           │
// │  +15: Card country ≠ booking destination│
// │  +10: IP country ≠ card country         │
// │  +8: New customer                        │
// │                                          │
// │  Recommendation: BLOCK                   │
// │  Require: Manual review + ID verification│
// │                                          │
// │  [Block] [Request ID Proof] [Override]   │
// └──────────────────────────────────────────┘
```

### Chargeback Management

```typescript
interface ChargebackManagement {
  chargebacks: Chargeback[];
  representment: RepresentmentWorkflow;
  prevention: ChargebackPrevention;
  analytics: ChargebackAnalytics;
}

interface Chargeback {
  chargebackId: string;
  bookingId: string;
  paymentId: string;
  reason: ChargebackReason;
  amount: Money;
  cardNetwork: string;                // Visa, Mastercard, RuPay
  initiatedDate: Date;
  responseDeadline: Date;
  status: ChargebackStatus;
  evidence: ChargebackEvidence[];
}

type ChargebackReason =
  | 'fraudulent'                      // "I didn't authorize this transaction"
  | 'service_not_received'            // "I paid but didn't get the service"
  | 'service_not_as_described'        // "The trip wasn't what was promised"
  | 'duplicate_charge'                // "I was charged twice"
  | 'canceled_subscription'           // "I canceled but was still charged"
  | 'credit_not_processed'            // "Refund was promised but not received"
  | 'processing_error';               // "Incorrect amount charged"

type ChargebackStatus =
  | 'received'                        // Chargeback initiated by cardholder
  | 'evidence_gathering'             // Agency collecting evidence
  | 'representment_submitted'        // Agency submitted defense
  | 'won'                             // Agency won the dispute
  | 'lost'                            // Agency lost, refund issued
  | 'second_chargeback'              // Cardholder disputed again (arbitration)
  | 'pre_arbitration';               // Final stage before arbitration

// Chargeback lifecycle:
// Day 0: Cardholder disputes transaction with their bank
// Day 1-3: Platform notified by payment gateway (Razorpay)
// Day 1-7: Agency gathers evidence
// Day 7-14: Representment submitted (defense to cardholder's bank)
// Day 14-45: Cardholder's bank reviews evidence
// Day 30-60: Decision: Chargeback won or lost
//
// If won: Money returned to agency
// If lost: Money stays with cardholder + chargeback fee ($15-25)
// Chargeback fee: ₹500-1,500 per chargeback (gateway fee)
//
// Chargeback defense evidence:
// For "fraudulent" claims:
// - IP address and geolocation at time of booking
// - Device fingerprint
// - 3DS authentication proof (OTP verified)
// - Communication with customer (WhatsApp, email)
// - Delivery of service proof (hotel check-in, boarding pass)
// - Customer's booking history (repeat customer = less likely fraud)
//
// For "service not received" claims:
// - Booking confirmation sent (email + WhatsApp proof)
// - Itinerary delivered (PDF download log)
// - Hotel voucher (confirmed by hotel)
// - Flight ticket (PNR confirmation)
// - Customer's acknowledgment (WhatsApp "thank you" message)
//
// For "service not as described" claims:
// - Original quote with inclusions/exclusions
// - Customer's signed acceptance of terms
// - Communication about any changes
// - Supplier confirmation of service delivered

// Chargeback prevention:
// 1. Clear cancellation and refund policies (documented and accepted)
// 2. Prompt refund processing (< 5 days from cancellation)
// 3. Booking confirmation via WhatsApp + email + SMS (proof of delivery)
// 4. Clear itinerary and pricing disclosure before payment
// 5. Post-trip follow-up (satisfied customers don't chargeback)
// 6. Address customer complaints within 24 hours
// 7. Maintain communication trail for every booking
```

### PCI-DSS Compliance

```typescript
interface PCICompliance {
  level: PCILevel;
  requirements: PCIRequirement[];
  controls: SecurityControl[];
  audit: PCIAudit;
}

type PCILevel =
  | 'level_1'                         // > 6M transactions/year
  | 'level_2'                         // 1-6M transactions/year
  | 'level_3'                         // 20K-1M transactions/year
  | 'level_4';                        // < 20K transactions/year

// PCI-DSS compliance for travel platform:
// Most important: NEVER handle raw card data on our servers
//
// Recommended: Use Razorpay's hosted checkout
// - Card data enters Razorpay's iframe directly
// - Platform never sees or stores card numbers
// - Razorpay handles PCI compliance
// - Platform receives tokenized payment reference only
//
// PCI-DSS requirements (what platform must do):
// 1. Network security: Firewalls, no default passwords
// 2. Cardholder data protection: Encryption, no storage of full card numbers
// 3. Vulnerability management: Antivirus, security patches
// 4. Access control: Need-to-know basis, unique IDs, MFA
// 5. Monitoring: Log access, track activities, regular testing
// 6. Security policy: Maintain information security policy
//
// India-specific requirements (RBI):
// - Card tokenization mandatory (no card-on-file with raw numbers)
// - AFA (Additional Factor of Authentication) for all online transactions
// - Card data cannot be stored by merchants (tokenization only)
// - CoFT (Card-on-File Tokenization) for recurring payments
//
// What platform stores:
// ✅ Tokenized card reference (last 4 digits + token)
// ✅ Payment status and amount
// ✅ Transaction reference from gateway
// ❌ Full card number (NEVER)
// ❌ CVV/CVC (NEVER)
// ❌ Card expiry date (store tokenized reference only)
```

---

## Open Problems

1. **Friendly fraud** — Customer books a trip, enjoys it, then claims "unauthorized transaction." Hard to distinguish from real fraud. Need strong service delivery evidence.

2. **Chargeback ratio** — Payment gateways monitor chargeback ratios. If >1%, they may increase fees or suspend the account. Every chargeback matters.

3. **International card acceptance** — Accepting international cards increases fraud risk but also increases international booking revenue. Need balanced approach.

4. **Refund vs. chargeback** — Customer requests refund through platform (cost: ₹0) vs. files chargeback (cost: ₹500-1,500 + dispute effort). Need to encourage refund channel.

5. **EMI fraud** — Customer books on EMI, travels, then disputes the charge. EMI transactions are harder to chargeback but not impossible.

---

## Next Steps

- [ ] Build payment fraud prevention with pre/during/post checks
- [ ] Create chargeback management with evidence collection and representment
- [ ] Design PCI-DSS compliant payment flow with Razorpay tokenization
- [ ] Build chargeback analytics with ratio monitoring and prevention scoring
- [ ] Study payment fraud platforms (Razorpay Risk, Signifyd, Riskified, Bolt)
