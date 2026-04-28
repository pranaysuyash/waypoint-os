# Travel Fraud Detection & Prevention — Detection Signals & Risk Scoring

> Research document for fraud signal detection, risk scoring models, anomaly detection, and fraud taxonomy for travel.

---

## Key Questions

1. **What types of fraud occur in travel bookings?**
2. **How do we detect suspicious booking patterns?**
3. **What risk scoring model do we apply to bookings?**
4. **How do we balance fraud prevention with customer experience?**
5. **What data points feed into fraud detection?**

---

## Research Areas

### Travel Fraud Taxonomy

```typescript
interface FraudTaxonomy {
  categories: FraudCategory[];
  signals: FraudSignal[];
  impact: FraudImpact[];
}

type FraudCategory =
  // Payment fraud
  | 'stolen_card'                      // Booking with stolen credit card
  | 'card_testing'                    // Testing stolen card numbers
  | 'chargeback_fraud'                // Booking then claiming non-receipt
  | 'payment_reversal'                // Cancel after service consumed
  // Identity fraud
  | 'fake_identity'                   // False name/ID for booking
  | 'identity_theft'                  // Using someone else's identity
  | 'synthetic_identity'              // Fabricated identity from real/fake data
  // Booking fraud
  | 'phantom_booking'                 // Booking with no intent to travel
  | 'price_manipulation'              // Exploiting pricing errors or loopholes
  | 'duplicate_claim'                 // Claiming refund multiple times
  | 'inventory_hoarding'              // Blocking inventory with no intent
  // Agent/internal fraud
  | 'commission_inflation'            // Inflating booking value for higher commission
  | 'phantom_supplier'                // Creating fake supplier invoices
  | 'customer_poaching'               // Diverting customers to personal bookings
  | 'data_theft';                     // Stealing customer data

interface FraudSignal {
  signalId: string;
  category: FraudCategory;
  name: string;
  description: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  dataPoints: string[];
  detectionMethod: 'rule' | 'ml_model' | 'manual';
}

// Fraud signals library:
//
// PAYMENT FRAUD SIGNALS:
// - Multiple booking attempts with different cards (card testing)
// - Card billing address doesn't match travel origin
// - Payment from high-risk country for domestic travel
// - Rapid successive bookings with same card
// - Payment amount just below card limit threshold
// - Multiple partial payments from different cards for one booking
// - Card flagged in global fraud databases
//
// IDENTITY FRAUD SIGNALS:
// - Name on booking doesn't match cardholder name
// - Phone number from different country than traveler
// - Email domain is disposable/temporary (guerrillamail, etc.)
// - IP geolocation doesn't match booking origin
// - Multiple bookings with slight name variations (Rajesh/Rajeesh/Rajesh K)
// - Traveler age doesn't match profile signals
//
// BOOKING PATTERN SIGNALS:
// - Same customer booking same route multiple times
// - Cancel-and-rebook pattern (price manipulation)
// - Booking high-value international trip as first booking
// - Multiple bookings for same dates from different accounts
// - Booking with immediate cancellation request
// - Unusually large group booking from new customer
// - Booking exotic destinations with domestic payment patterns
//
// INTERNAL FRAUD SIGNALS:
// - Agent booking under family/friend names
// - Commission rate higher than authorized
// - Supplier invoice without corresponding booking
// - Agent accessing customer data without active booking
// - Unusual booking patterns by specific agent
// - Agent modifying prices after confirmation

interface FraudImpact {
  category: FraudCategory;
  averageLoss: Money;
  frequency: 'rare' | 'occasional' | 'frequent';
  detectionDifficulty: 'easy' | 'moderate' | 'hard';
}

// Fraud impact assessment:
// Stolen card: ₹10,000-5,00,000 loss, occasional, moderate detection
// Chargeback: ₹5,000-2,00,000 loss, frequent, hard detection
// Phantom booking: ₹5,000-50,000 (opportunity cost), rare, easy detection
// Commission inflation: ₹1,000-50,000 per incident, occasional, hard detection
// Phantom supplier: ₹50,000-10,00,000, rare, moderate detection
```

### Risk Scoring Model

```typescript
interface RiskScoring {
  bookingId: string;
  score: number;                      // 0-100 (higher = riskier)
  level: RiskLevel;
  factors: RiskFactor[];
  recommendation: RiskRecommendation;
}

type RiskLevel =
  | 'low'                             // 0-30: Proceed normally
  | 'medium'                          // 31-60: Enhanced verification
  | 'high'                            // 61-80: Manual review required
  | 'critical';                       // 81-100: Block and investigate

interface RiskFactor {
  factor: string;
  contribution: number;               // Points added to score
  reason: string;
  dataUsed: string;
}

// Risk scoring algorithm:
// Base score: 0
//
// Customer factors (0-30 points):
// +10: New customer (no booking history)
// +5: Customer has 1-2 previous bookings
// +0: Customer has 3+ bookings (trusted)
// +10: Customer had previous cancellation/dispute
// +15: Customer flagged in internal fraud database
//
// Payment factors (0-30 points):
// +15: International card for domestic travel
// +10: Card country doesn't match traveler nationality
// +10: Multiple payment attempts with different cards
// +5: Payment amount exceeds customer's typical booking value
// +20: Card on global fraud watchlist
//
// Booking factors (0-20 points):
// +10: High-value booking (₹2L+) as first transaction
// +5: Booking made outside business hours (2-6 AM IST)
// +5: One-way international flight booking
// +10: Same-day travel booking (rush booking)
// +5: Group booking (>6 travelers)
//
// Identity factors (0-20 points):
// +10: Disposable email domain
// +5: Phone number country doesn't match traveler
// +10: Name mismatch between booking and payment
// +5: Incomplete identity information
// +10: IP geolocation anomaly
//
// Score thresholds and actions:
// 0-30 (Low): Auto-approve, normal processing
// 31-60 (Medium): Require OTP verification on payment
//                  Send confirmation link to email
//                  Flag for post-booking review
// 61-80 (High): Manual review by agency admin
//               Require additional ID verification
//               Hold booking until verified
// 81-100 (Critical): Block booking
//                    Notify fraud team
//                    Log for investigation

interface RiskRecommendation {
  action: RecommendedAction;
  reason: string;
  additionalSteps: string[];
}

type RecommendedAction =
  | 'approve'                         // Proceed with booking
  | 'approve_with_otp'                // Approve after OTP verification
  | 'manual_review'                   // Hold for human review
  | 'request_documents'               // Request ID/payment proof
  | 'block';                          // Block the booking
```

### Anomaly Detection

```typescript
interface AnomalyDetection {
  baseline: BehavioralBaseline;
  anomalies: DetectedAnomaly[];
  models: AnomalyModel[];
}

interface BehavioralBaseline {
  metric: string;
  normalRange: { min: number; max: number };
  updatedFrom: string;                // "last_90_days_bookings"
  confidence: number;
}

// Behavioral baselines (computed per agency):
// Average booking value: ₹25,000-75,000
// Average travelers per booking: 2-4
// Average advance payment: 30-40%
// Cancellation rate: 8-15%
// Peak booking hours: 10 AM - 8 PM IST
// Popular destinations: Goa, Kerala, Rajasthan, Thailand, Dubai
// Payment method distribution: UPI 45%, Card 25%, Net banking 15%
//
// Anomaly triggers:
// Booking value > 3x average → Flag
// Booking at 3 AM IST → Flag
// Customer making 5th booking in one month → Flag
// Same card used across 3 different customer accounts → Flag
// Cancellation rate > 30% for specific customer → Flag
// Agent with commission rate exceeding norms → Flag
// Supplier invoice without matching booking → Flag
//
// ML model types for fraud detection:
// 1. Rule-based: If-then rules for known fraud patterns
//    Pros: Explainable, fast, no training data needed
//    Cons: Can't detect novel fraud patterns
//
// 2. Statistical anomaly: Z-score, isolation forest
//    Pros: Detects statistical outliers
//    Cons: High false positive rate for legitimate unusual bookings
//
// 3. Supervised ML: Train on labeled fraud/non-fraud data
//    Pros: Learns from actual fraud cases
//    Cons: Needs labeled data (fraud is rare, limited training examples)
//
// Recommended approach: Start with rules, add statistical anomaly,
// graduate to ML as labeled data accumulates.
```

---

## Open Problems

1. **False positive cost** — Blocking a legitimate ₹2L international booking angers a genuine customer. False positives have real revenue cost.

2. **Limited training data** — Fraud is rare (<1% of bookings). ML models trained on small fraud datasets have low accuracy. Need extensive rule-based system first.

3. **Evolving tactics** — Fraudsters adapt quickly. Rules that catch today's patterns miss tomorrow's. Need adaptive detection.

4. **Agent experience impact** — Fraud checks add friction to the booking process. Agents want speed, not security delays. Need invisible verification where possible.

5. **Privacy vs. security** — Extensive fraud monitoring collects significant customer data. Must comply with DPDP Act for data collection and usage.

---

## Next Steps

- [ ] Build fraud signal detection engine with rule-based system
- [ ] Create risk scoring model with threshold-based actions
- [ ] Design anomaly detection with behavioral baselines
- [ ] Build fraud case management dashboard
- [ ] Study fraud detection platforms (Razorpay Risk, Signifyd, Riskified, Sardine)
